"""
Review commands for the CLI.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional
import uuid
from datetime import datetime

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...core.git.differ import GitDiffer
from ...core.git.parser import DiffParser
from ...core.ai import OllamaClient, OpenAIClient, AnthropicClient, GeminiClient
from ...core.ai.prompts import PromptEngine
from ...core.config.manager import ConfigManager
from ...core.output.console import ReviewConsole
from ...models import ReviewRequest, ReviewResult, ReviewFocus
from ...models.diff import GitDiff
from ...models.review import ReviewMetrics, IssueSeverity
from ...models.issue import Issue, IssueLocation, IssueCategory
from ...models.review import ReviewStatus

logger = logging.getLogger(__name__)
console = Console()

app = typer.Typer()


@app.command("run-review")
def run_review(
    target: str = typer.Option("main", "--target", "-t", help="Target branch/commit"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Source branch/commit"),
    focus: List[str] = typer.Option([], "--focus", "-f", help="Focus areas (security, performance, etc.)"),
    include: List[str] = typer.Option([], "--include", "-i", help="File patterns to include"),
    exclude: List[str] = typer.Option([], "--exclude", "-e", help="File patterns to exclude"),
    output: str = typer.Option("rich", "--output", "-o", help="Output format (rich, json, markdown)"),
    max_files: int = typer.Option(100, "--max-files", help="Maximum files to review"),
    save: Optional[str] = typer.Option(None, "--save", help="Save output to file"),
    config_path: Optional[str] = typer.Option(None, "--config", help="Path to config file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Run AI code review on git diff."""
    
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Run the async review
    asyncio.run(_run_review_async(
        target=target,
        source=source,
        focus=focus,
        include=include,
        exclude=exclude,
        output=output,
        max_files=max_files,
        save=save,
        config_path=config_path,
        verbose=verbose
    ))


async def _run_review_async(
    target: str,
    source: Optional[str],
    focus: List[str],
    include: List[str],
    exclude: List[str],
    output: str,
    max_files: int,
    save: Optional[str],
    config_path: Optional[str],
    verbose: bool
):
    """Async implementation of the review command."""
    
    try:
        # Load configuration
        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()
        print(f"DEBUG: Loaded config - provider: {config.ai.provider}, model: {config.ai.model}")
        print(f"DEBUG: Config file: {config_manager.config_path}")
        
        # Determine focus area - use first focus or default to general
        focus_area = ReviewFocus.GENERAL
        if focus:
            try:
                focus_area = ReviewFocus(focus[0].lower())
            except ValueError:
                console.print(f"[yellow]Warning: Invalid focus '{focus[0]}', using 'general'[/yellow]")
        
        # Create review request
        request = ReviewRequest(
            source_branch=source or "HEAD",
            target_branch=target,
            focus=focus_area,
            include_patterns=include,
            exclude_patterns=exclude,
            max_files=max_files
        )
        
        console.print(f"Starting code review...")
        console.print(f"Target branch: {target}")
        console.print(f"Source branch: {request.source_branch}")
        console.print(f"Focus area: {focus_area.value}")
        console.print()
        
        # Get git diff
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Getting git diff...", total=None)
            
            git_differ = GitDiffer()
            
            # Get the structured diff (GitDiffer already returns a GitDiff object)
            diff = git_differ.get_diff_between_branches(
                target_branch=request.target_branch,
                source_branch=request.source_branch
            )
            
            print(f"DEBUG: diff type: {type(diff)}")
            print(f"DEBUG: diff files count: {len(diff.files)}")
            
            progress.update(task, description="Filtering files...")
            
            # Filter files based on patterns
            filtered_files = []
            for file in diff.files:
                if len(filtered_files) >= max_files:
                    break
                    
                # Check include patterns (CLI args)
                if include and not any(file.path.endswith(pattern.lstrip('*')) for pattern in include):
                    continue
                    
                # Check exclude patterns (CLI args)
                if exclude and any(file.path.endswith(pattern.lstrip('*')) for pattern in exclude):
                    continue
                
                # Check git config exclude patterns
                git_exclude_patterns = config.git.exclude_patterns
                if git_exclude_patterns:
                    import fnmatch
                    if any(fnmatch.fnmatch(file.path, pattern) for pattern in git_exclude_patterns):
                        print(f"DEBUG: Excluding file due to git config pattern: {file.path}")
                        continue
                    
                filtered_files.append(file)
            
            diff.files = filtered_files
            print(f"DEBUG: Files being sent to AI ({len(filtered_files)}): {[f.path for f in filtered_files]}")
            
            if not filtered_files:
                console.print("[yellow]⚠️ No files to review after filtering. Use --include-all to include more files.[/yellow]")
                return
            
            progress.update(task, description="Initializing AI client...")
            
            # Initialize AI client based on config
            print(f"DEBUG: AI provider from config: {config.ai.provider}")
            print(f"DEBUG: AI model from config: {config.ai.model}")
            ai_client = _create_ai_client(config)
            
            # Test connection
            async with ai_client:
                if not await ai_client.test_connection():
                    console.print("[red]❌ Failed to connect to AI service[/red]")
                    console.print(f"Please check your {config.ai.provider} configuration.")
                    return
                
                progress.update(task, description="Loading prompts...")
                
                # Load system prompt
                prompt_engine = PromptEngine()
                system_prompt = prompt_engine.get_prompt(focus_area)
                
                # Prepare diff context for logging
                diff_context = ai_client.prepare_diff_context(diff)
                
                # Log prompts to files for debugging
                try:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Save system prompt
                    with open(f"system_prompt_{timestamp}.txt", "w", encoding="utf-8") as f:
                        f.write("=== SYSTEM PROMPT ===\n")
                        f.write(system_prompt)
                        f.write("\n\n=== END SYSTEM PROMPT ===\n")
                    
                    # Save diff context
                    with open(f"diff_context_{timestamp}.txt", "w", encoding="utf-8") as f:
                        f.write("=== DIFF CONTEXT ===\n")
                        f.write(diff_context)
                        f.write("\n\n=== END DIFF CONTEXT ===\n")
                    
                    # Save combined prompt (how it will appear to AI)
                    with open(f"full_prompt_{timestamp}.txt", "w", encoding="utf-8") as f:
                        f.write("=== FULL PROMPT SENT TO AI ===\n")
                        f.write("System Prompt:\n")
                        f.write(system_prompt)
                        f.write("\n\n" + "="*50 + "\n\n")
                        f.write("User Message (Diff Context):\n")
                        f.write(f"Please analyze the following code changes:\n\n{diff_context}")
                        if request.context:
                            f.write(f"\n\nAdditional context: {request.context}")
                        f.write("\n\n=== END FULL PROMPT ===\n")
                    
                    console.print(f"[green]✓[/green] Prompts saved to files with timestamp: {timestamp}")
                    
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not save prompt files: {e}[/yellow]")
                
                progress.update(task, description="Analyzing code...")
                
                # Perform the review
                ai_response = await ai_client.analyze_code(request, diff, system_prompt)
                
                # Parse the AI response into issues
                issues = _parse_ai_response(ai_response.content, diff)
                
                # Create review result
                result = ReviewResult(
                    id=str(uuid.uuid4()),
                    status=ReviewStatus.COMPLETED,
                    request=request,
                    diff=diff,
                    issues=issues,
                    summary=_generate_summary(issues),
                    metrics=ReviewMetrics(
                        critical_issues=len([i for i in issues if i.severity == IssueSeverity.CRITICAL]),
                        high_issues=len([i for i in issues if i.severity == IssueSeverity.HIGH]),
                        medium_issues=len([i for i in issues if i.severity == IssueSeverity.MEDIUM]),
                        low_issues=len([i for i in issues if i.severity == IssueSeverity.LOW]),
                        info_issues=len([i for i in issues if i.severity == IssueSeverity.INFO]),
                        files_reviewed=len(diff.files) if diff else 0,
                        lines_added=sum(f.stats.additions for f in diff.files) if diff else 0,
                        lines_deleted=sum(f.stats.deletions for f in diff.files) if diff else 0,
                    ),
                    created_at=datetime.utcnow(),
                    ai_provider_used=config.ai.provider,
                    ai_model_used=config.ai.model,
                )
                
                progress.update(task, description="Formatting results...")
        
        # Display results
        review_console = ReviewConsole(config.output)
        
        if output == "rich":
            review_console.print_full_review(result)
        elif output == "json":
            console.print(result.model_dump_json(indent=2))
        elif output == "markdown":
            # TODO: Implement markdown output
            console.print("Markdown output not yet implemented")
        else:
            console.print(f"Unknown output format: {output}")
        
        # Save to file if requested
        if save:
            # TODO: Implement file saving
            console.print(f"Save to file not yet implemented: {save}")
        
        console.print("\n[green]✓ Review completed![/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Review failed: {e}[/red]")
        if verbose:
            logger.exception("Review failed")
        raise typer.Exit(1)


def _create_ai_client(config):
    """Create AI client based on configuration."""
    
    if config.ai.provider == "ollama":
        return OllamaClient(config.ai)
    elif config.ai.provider == "openai":
        return OpenAIClient(config.ai)
    elif config.ai.provider == "anthropic":
        return AnthropicClient(config.ai)
    elif config.ai.provider == "gemini":
        return GeminiClient(config.ai)
    else:
        raise ValueError(f"Unsupported AI provider: {config.ai.provider}")


@app.command("list")
def list_reviews(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of reviews to show"),
    format: str = typer.Option("table", "--format", "-f", help="Output format (table, json)")
):
    """List recent reviews."""
    
    console.print("📋 Recent Reviews")
    console.print("=" * 50)
    
    # TODO: Implement review history
    console.print("Review history not yet implemented.")
    console.print("This will show recent reviews from the cache.")


@app.command("show")
def show_review(
    review_id: str = typer.Argument(..., help="Review ID to show")
):
    """Show detailed review by ID."""
    
    console.print(f"🔍 Review Details: {review_id}")
    console.print("=" * 50)
    
    # TODO: Implement review details
    console.print("Review details not yet implemented.")
    console.print("This will show detailed information about a specific review.")


@app.command("clear")
def clear_history():
    """Clear review history."""
    
    console.print("🗑️  Clearing review history...")
    
    # TODO: Implement history clearing
    console.print("Review history not yet implemented.")
    console.print("This will clear cached review data.")


def _parse_ai_response(response_text: str, diff: GitDiff) -> List[Issue]:
    """Parse AI response into structured issues."""
    import json
    import uuid
    from code_review_cli.models.issue import Issue, IssueLocation, IssueSeverity, IssueCategory
    
    issues = []
    
    try:
        # Try to extract JSON from the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            
            for issue_data in data.get("issues", []):
                try:
                    # Handle both old and new field formats
                    file_path = issue_data.get("file_path") or issue_data.get("file", "")
                    line_start = issue_data.get("line_start") or issue_data.get("line", 0)
                    
                    # Create proper IssueLocation
                    location = IssueLocation(
                        file_path=file_path,
                        line_start=line_start,
                        line_end=issue_data.get("line_end"),
                        column_start=issue_data.get("column_start"),
                        column_end=issue_data.get("column_end")
                    )
                    
                    issue = Issue(
                        id=str(uuid.uuid4()),
                        title=issue_data.get("title", "Code review issue"),
                        description=issue_data.get("description", ""),
                        severity=IssueSeverity(issue_data.get("severity", "MEDIUM")),
                        category=IssueCategory(issue_data.get("category", "MAINTAINABILITY")),
                        location=location,
                        code_snippet=issue_data.get("code_snippet"),
                        suggested_fix=issue_data.get("suggested_fix") or issue_data.get("suggestion", ""),
                        confidence=issue_data.get("confidence", 1.0),
                        tags=issue_data.get("tags", []),
                        references=issue_data.get("references", [])
                    )
                    issues.append(issue)
                except Exception as e:
                    logger.warning(f"Failed to parse issue: {e}")
        
    except Exception as e:
        logger.error(f"Failed to parse AI response: {e}")
        # Fallback: create a generic issue
        issues.append(Issue(
            id=str(uuid.uuid4()),
            title="AI Response Parse Error",
            description=f"Could not parse AI response: {response_text[:200]}...",
            severity=IssueSeverity.MEDIUM,
            category=IssueCategory.MAINTAINABILITY,
            location=IssueLocation(file_path="", line_start=0),
            suggested_fix="Check the AI response format"
        ))
    
    return issues


def _generate_summary(issues: List[Issue]) -> str:
    """Generate a summary from the issues."""
    if not issues:
        return "No issues found. Code looks good!"
    
    critical = len([i for i in issues if i.severity == IssueSeverity.CRITICAL])
    high = len([i for i in issues if i.severity == IssueSeverity.HIGH])
    medium = len([i for i in issues if i.severity == IssueSeverity.MEDIUM])
    low = len([i for i in issues if i.severity == IssueSeverity.LOW])
    
    summary = f"Found {len(issues)} issues: "
    if critical > 0:
        summary += f"{critical} critical, "
    if high > 0:
        summary += f"{high} high, "
    if medium > 0:
        summary += f"{medium} medium, "
    if low > 0:
        summary += f"{low} low priority"
    
    return summary.rstrip(", ") 
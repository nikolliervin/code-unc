"""Rich console output for beautiful terminal display."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.syntax import Syntax
from rich.tree import Tree
from rich.text import Text
from rich.columns import Columns
from rich.align import Align

from ...models.review import ReviewResult
from ...models.issue import Issue, IssueSeverity
from ...models.config import OutputConfig


logger = logging.getLogger(__name__)


class ReviewConsole:
    """Rich-based console output for code review results."""
    
    # Severity color mapping
    SEVERITY_COLORS = {
        IssueSeverity.CRITICAL: "red",
        IssueSeverity.HIGH: "orange3", 
        IssueSeverity.MEDIUM: "yellow",
        IssueSeverity.LOW: "green",
        IssueSeverity.INFO: "blue",
    }
    
    # Severity icons
    SEVERITY_ICONS = {
        IssueSeverity.CRITICAL: "🚨",
        IssueSeverity.HIGH: "⚠️ ",
        IssueSeverity.MEDIUM: "⚡",
        IssueSeverity.LOW: "💡",
        IssueSeverity.INFO: "ℹ️ ",
    }
    
    def __init__(self, config: OutputConfig):
        """
        Initialize review console.
        
        Args:
            config: Output configuration
        """
        self.config = config
        self.console = Console(
            width=config.console_width,
            color_system="auto" if config.color_enabled else None,
        )
    
    def print_review_header(self, review_result: ReviewResult) -> None:
        """Print review header with basic info."""
        # Create header panel
        header_content = []
        header_content.append(f"[bold blue]Review ID:[/bold blue] {review_result.id}")
        header_content.append(f"[bold blue]Status:[/bold blue] {review_result.status.value}")
        header_content.append(f"[bold blue]Created:[/bold blue] {review_result.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if review_result.diff:
            header_content.append(f"[bold blue]Repository:[/bold blue] {review_result.diff.repository or 'Unknown'}")
            header_content.append(f"[bold blue]Branch:[/bold blue] {review_result.diff.source_branch} → {review_result.diff.target_branch}")
        
        header_text = "\n".join(header_content)
        header_panel = Panel(
            header_text,
            title="[bold cyan]Code Review Report[/bold cyan]",
            border_style="cyan",
        )
        
        self.console.print(header_panel)
        self.console.print()
    
    def print_summary(self, review_result: ReviewResult) -> None:
        """Print review summary."""
        if review_result.summary:
            summary_panel = Panel(
                review_result.summary,
                title="[bold green]Summary[/bold green]",
                border_style="green",
            )
            self.console.print(summary_panel)
            self.console.print()
    
    def print_metrics(self, review_result: ReviewResult) -> None:
        """Print review metrics in a nice layout."""
        metrics = review_result.metrics
        
        # Create metrics cards
        cards = []
        
        # Files card
        files_card = Panel(
            f"[bold]{metrics.files_reviewed}[/bold]\nFiles Reviewed",
            title="📁 Files",
            width=15,
        )
        cards.append(files_card)
        
        # Changes card
        changes_card = Panel(
            f"[green]+{metrics.lines_added}[/green] [red]-{metrics.lines_deleted}[/red]\nLine Changes",
            title="📝 Changes",
            width=15,
        )
        cards.append(changes_card)
        
        # Issues card
        total_issues = metrics.total_issues
        issues_color = "red" if metrics.critical_issues > 0 else "orange3" if metrics.high_issues > 0 else "green"
        issues_card = Panel(
            f"[{issues_color}]{total_issues}[/{issues_color}]\nTotal Issues",
            title="🐛 Issues",
            width=15,
        )
        cards.append(issues_card)
        
        # Quality score card
        score = metrics.calculate_score()
        score_color = "red" if score < 60 else "yellow" if score < 80 else "green"
        score_card = Panel(
            f"[{score_color}]{score:.1f}/100[/{score_color}]\nQuality Score",
            title="⭐ Score",
            width=15,
        )
        cards.append(score_card)
        
        # Print cards in columns
        self.console.print(Columns(cards, equal=True, expand=False))
        self.console.print()
        
        # Detailed breakdown if there are issues
        if total_issues > 0:
            breakdown_table = Table(title="Issue Breakdown", show_header=True, header_style="bold magenta")
            breakdown_table.add_column("Severity", style="bold")
            breakdown_table.add_column("Count", justify="center")
            breakdown_table.add_column("Percentage", justify="center")
            
            issue_counts = [
                ("Critical", metrics.critical_issues, "red"),
                ("High", metrics.high_issues, "orange3"),
                ("Medium", metrics.medium_issues, "yellow"),
                ("Low", metrics.low_issues, "green"),
                ("Info", metrics.info_issues, "blue"),
            ]
            
            for severity, count, color in issue_counts:
                if count > 0:
                    percentage = (count / total_issues) * 100
                    breakdown_table.add_row(
                        f"[{color}]{severity}[/{color}]",
                        f"[{color}]{count}[/{color}]",
                        f"[{color}]{percentage:.1f}%[/{color}]"
                    )
            
            self.console.print(breakdown_table)
            self.console.print()
    
    def print_issues(self, issues: List[Issue], max_issues: Optional[int] = None) -> None:
        """Print issues grouped by severity."""
        if not issues:
            self.console.print("[green]✅ No issues found![/green]")
            return
        
        # Group issues by severity
        severity_groups = {}
        for issue in issues:
            severity = issue.severity
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(issue)
        
        # Print each severity group
        shown_count = 0
        for severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM, IssueSeverity.LOW, IssueSeverity.INFO]:
            if severity in severity_groups:
                group_issues = severity_groups[severity]
                if max_issues and shown_count >= max_issues:
                    remaining = len(issues) - shown_count
                    self.console.print(f"[dim]... and {remaining} more issues (use --verbose to see all)[/dim]")
                    break
                
                self._print_severity_group(severity, group_issues, max_issues - shown_count if max_issues else None)
                shown_count += len(group_issues)
    
    def _print_severity_group(self, severity: IssueSeverity, issues: List[Issue], max_show: Optional[int]) -> None:
        """Print a group of issues with the same severity."""
        color = self.SEVERITY_COLORS[severity]
        icon = self.SEVERITY_ICONS[severity]
        
        # Header
        header = f"{icon} [bold {color}]{severity.value.title()} Issues ({len(issues)})[/bold {color}]"
        self.console.print(header)
        self.console.print()
        
        # Show issues
        issues_to_show = issues[:max_show] if max_show else issues
        
        for i, issue in enumerate(issues_to_show, 1):
            self._print_single_issue(issue, severity, i)
        
        if max_show and len(issues) > max_show:
            remaining = len(issues) - max_show
            self.console.print(f"[dim]... and {remaining} more {severity.value} issues[/dim]")
        
        self.console.print()
    
    def _print_single_issue(self, issue: Issue, severity: IssueSeverity, index: int) -> None:
        """Print a single issue with formatting."""
        color = self.SEVERITY_COLORS[severity]
        
        # Issue header
        location = f"{issue.location.file_path}:{issue.location.line_range}"
        header = f"[bold]{index}. {issue.title}[/bold]"
        subheader = f"[dim]{location} | {issue.category.value} | {issue.confidence:.1%} confidence[/dim]"
        
        self.console.print(f"[{color}]▸[/{color}] {header}")
        self.console.print(f"   {subheader}")
        
        # Description
        description_lines = issue.description.split('\n')
        for line in description_lines:
            if line.strip():
                self.console.print(f"   {line}")
        
        # Code snippet
        if issue.code_snippet:
            self.console.print("   [dim]Code:[/dim]")
            # Try to detect language for syntax highlighting
            file_ext = issue.location.file_path.split('.')[-1] if '.' in issue.location.file_path else "text"
            syntax = Syntax(
                issue.code_snippet,
                file_ext,
                theme="monokai",
                line_numbers=True,
                padding=(0, 1),
            )
            self.console.print(syntax, style="dim")
        
        # Suggested fix
        if issue.suggested_fix:
            self.console.print("   [dim]Suggested Fix:[/dim]")
            file_ext = issue.location.file_path.split('.')[-1] if '.' in issue.location.file_path else "text"
            syntax = Syntax(
                issue.suggested_fix,
                file_ext,
                theme="monokai",
                line_numbers=True,
                padding=(0, 1),
            )
            self.console.print(syntax, style="dim")
        
        # References
        if issue.references:
            self.console.print("   [dim]References:[/dim]")
            for ref in issue.references:
                self.console.print(f"   [link={ref}]{ref}[/link]")
        
        self.console.print()
    
    def print_recommendations(self, recommendations: List[str]) -> None:
        """Print general recommendations."""
        if not recommendations:
            return
        
        rec_panel = Panel(
            "\n".join(f"• {rec}" for rec in recommendations),
            title="[bold yellow]Recommendations[/bold yellow]",
            border_style="yellow",
        )
        self.console.print(rec_panel)
        self.console.print()
    
    def print_file_tree(self, review_result: ReviewResult) -> None:
        """Print a tree view of reviewed files."""
        if not review_result.diff or not review_result.diff.files:
            return
        
        tree = Tree("📁 [bold blue]Files Reviewed[/bold blue]")
        
        for diff_file in review_result.diff.files:
            # File status icon
            if diff_file.is_new_file:
                icon = "[green]➕[/green]"
            elif diff_file.is_deleted_file:
                icon = "[red]➖[/red]"
            elif diff_file.is_renamed:
                icon = "[yellow]📝[/yellow]"
            else:
                icon = "[blue]📝[/blue]"
            
            # File info
            stats = f"+{diff_file.stats.additions} -{diff_file.stats.deletions}"
            file_node = tree.add(f"{icon} {diff_file.path} [dim]({stats})[/dim]")
            
            # Add language info if available
            if diff_file.language:
                file_node.add(f"[dim]Language: {diff_file.language}[/dim]")
        
        self.console.print(tree)
        self.console.print()
    
    def print_approval_status(self, review_result: ReviewResult) -> None:
        """Print approval status with prominent display."""
        is_approved = review_result.is_approved()
        blocking_issues = review_result.get_blocking_issues()
        
        if is_approved:
            status_panel = Panel(
                "[bold green]✅ APPROVED[/bold green]\n[green]No blocking issues found. Ready to merge![/green]",
                border_style="green",
                padding=(1, 2),
            )
        else:
            blocking_count = len(blocking_issues)
            status_panel = Panel(
                f"[bold red]❌ NEEDS ATTENTION[/bold red]\n[red]{blocking_count} blocking issue(s) found. Review required before merging.[/red]",
                border_style="red",
                padding=(1, 2),
            )
        
        self.console.print(Align.center(status_panel))
        self.console.print()
    
    def create_progress_bar(self, description: str) -> Progress:
        """Create a Rich progress bar."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
            disable=not self.config.show_progress,
        )
    
    def print_error(self, message: str, title: str = "Error") -> None:
        """Print an error message."""
        error_panel = Panel(
            f"[red]{message}[/red]",
            title=f"[bold red]{title}[/bold red]",
            border_style="red",
        )
        self.console.print(error_panel)
    
    def print_warning(self, message: str, title: str = "Warning") -> None:
        """Print a warning message."""
        warning_panel = Panel(
            f"[yellow]{message}[/yellow]",
            title=f"[bold yellow]{title}[/bold yellow]",
            border_style="yellow",
        )
        self.console.print(warning_panel)
    
    def print_success(self, message: str, title: str = "Success") -> None:
        """Print a success message."""
        success_panel = Panel(
            f"[green]{message}[/green]",
            title=f"[bold green]{title}[/bold green]",
            border_style="green",
        )
        self.console.print(success_panel)
    
    def print_full_review(self, review_result: ReviewResult, verbose: bool = False) -> None:
        """Print complete review output."""
        # Header
        self.print_review_header(review_result)
        
        # Summary
        self.print_summary(review_result)
        
        # Metrics
        self.print_metrics(review_result)
        
        # File tree (if verbose)
        if verbose:
            self.print_file_tree(review_result)
        
        # Issues
        max_issues = None if verbose else 20
        self.print_issues(review_result.issues, max_issues)
        
        # Recommendations
        self.print_recommendations(review_result.recommendations)
        
        # Approval status
        self.print_approval_status(review_result) 
"""Prompt management and template engine."""

import logging
from pathlib import Path
from typing import Dict, Optional
from jinja2 import Environment, FileSystemLoader, Template

from ...models.review import ReviewFocus
from ...models.diff import GitDiff


logger = logging.getLogger(__name__)


class PromptEngine:
    """Manages prompts and templates for AI code review."""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize prompt engine.
        
        Args:
            prompts_dir: Directory containing prompt templates
        """
        if prompts_dir is None:
            # Use default prompts directory
            prompts_dir = Path(__file__).parent.parent.parent.parent / "configs" / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self.templates = {}
        self.jinja_env = None
        
        # Initialize Jinja2 environment if prompts directory exists
        if self.prompts_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.prompts_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        
        # Load default prompts
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load prompt templates from files."""
        try:
            # Load main review prompt
            review_file = self.prompts_dir / "review.txt"
            if review_file.exists():
                self.templates["review"] = review_file.read_text(encoding="utf-8")
            
            # Load security-focused prompt
            security_file = self.prompts_dir / "security.txt"
            if security_file.exists():
                self.templates["security"] = security_file.read_text(encoding="utf-8")
            
            # Load performance-focused prompt
            performance_file = self.prompts_dir / "performance.txt"
            if performance_file.exists():
                self.templates["performance"] = performance_file.read_text(encoding="utf-8")
            
            logger.info(f"Loaded {len(self.templates)} prompt templates")
            
        except Exception as e:
            logger.warning(f"Failed to load some prompts: {e}")
    
    def get_prompt(
        self,
        focus: ReviewFocus,
        custom_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Get prompt for specific review focus.
        
        Args:
            focus: Review focus area
            custom_prompt: Custom prompt to use instead
            **kwargs: Additional template variables
            
        Returns:
            Formatted prompt string
        """
        if custom_prompt:
            return self._render_template_string(custom_prompt, **kwargs)
        
        # Map focus to template name
        template_name = self._get_template_name(focus)
        
        if template_name in self.templates:
            return self._render_template_string(self.templates[template_name], **kwargs)
        
        # Fallback to general review prompt
        if "review" in self.templates:
            logger.warning(f"No specific prompt for {focus}, using general review prompt")
            return self._render_template_string(self.templates["review"], **kwargs)
        
        # Ultimate fallback
        return self._get_fallback_prompt()
    
    def _get_template_name(self, focus: ReviewFocus) -> str:
        """Map review focus to template name."""
        mapping = {
            ReviewFocus.SECURITY: "security",
            ReviewFocus.PERFORMANCE: "performance",
            ReviewFocus.STYLE: "review",
            ReviewFocus.BUGS: "review",
            ReviewFocus.MAINTAINABILITY: "review",
            ReviewFocus.TESTING: "review",
            ReviewFocus.GENERAL: "review",
        }
        return mapping.get(focus, "review")
    
    def _render_template_string(self, template_str: str, **kwargs) -> str:
        """
        Render a template string with variables.
        
        Args:
            template_str: Template string
            **kwargs: Template variables
            
        Returns:
            Rendered string
        """
        try:
            if self.jinja_env:
                template = self.jinja_env.from_string(template_str)
                return template.render(**kwargs)
            else:
                # Simple string formatting fallback
                return template_str.format(**kwargs)
        except Exception as e:
            logger.warning(f"Template rendering failed: {e}")
            return template_str
    
    def _get_fallback_prompt(self) -> str:
        """Get fallback prompt if no templates are available."""
        return """You are an expert AI code reviewer. Analyze the provided code changes and respond with valid JSON containing:

{
  "summary": "Brief overview of code quality and main findings",
  "issues": [
    {
      "id": "unique_issue_id",
      "title": "Brief issue title",
      "description": "Detailed explanation",
      "severity": "critical|high|medium|low|info",
      "category": "security|performance|maintainability|readability|style|bugs|design|testing|documentation|complexity",
      "location": {
        "file_path": "path/to/file",
        "line_start": 42,
        "line_end": 45
      },
      "code_snippet": "problematic code",
      "suggested_fix": "corrected code",
      "confidence": 0.95
    }
  ],
  "recommendations": ["General recommendation 1", "General recommendation 2"],
  "metrics": {
    "files_reviewed": 1,
    "critical_issues": 0,
    "high_issues": 1,
    "medium_issues": 2,
    "low_issues": 1,
    "info_issues": 1
  }
}

Focus on finding genuine issues and providing actionable fixes. Respond with valid JSON only."""
    
    def add_custom_prompt(self, name: str, prompt: str) -> None:
        """
        Add a custom prompt template.
        
        Args:
            name: Template name
            prompt: Prompt content
        """
        self.templates[name] = prompt
        logger.info(f"Added custom prompt: {name}")
    
    def list_available_prompts(self) -> Dict[str, str]:
        """
        List all available prompt templates.
        
        Returns:
            Dictionary mapping template names to descriptions
        """
        descriptions = {
            "review": "General code review prompt with comprehensive analysis",
            "security": "Security-focused prompt emphasizing OWASP Top 10 and vulnerabilities",
            "performance": "Performance-focused prompt for optimization and efficiency",
        }
        
        available = {}
        for name in self.templates.keys():
            available[name] = descriptions.get(name, "Custom prompt template")
        
        return available
    
    def validate_prompt_output(self, output: str) -> bool:
        """
        Validate that prompt output is valid JSON with required fields.
        
        Args:
            output: AI response to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            import json
            data = json.loads(output)
            
            # Check required top-level fields
            required_fields = ["summary", "issues", "recommendations", "metrics"]
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # Validate issues structure
            if not isinstance(data["issues"], list):
                logger.warning("Issues field must be a list")
                return False
            
            for issue in data["issues"]:
                required_issue_fields = ["id", "title", "description", "severity", "category", "location"]
                for field in required_issue_fields:
                    if field not in issue:
                        logger.warning(f"Missing required issue field: {field}")
                        return False
            
            # Validate metrics structure
            metrics = data["metrics"]
            required_metrics = ["files_reviewed", "critical_issues", "high_issues", "medium_issues", "low_issues", "info_issues"]
            for field in required_metrics:
                if field not in metrics:
                    logger.warning(f"Missing required metric field: {field}")
                    return False
            
            return True
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON output: {e}")
            return False
        except Exception as e:
            logger.warning(f"Prompt validation error: {e}")
            return False
    
    def get_prompt_with_context(
        self,
        focus: ReviewFocus,
        diff: GitDiff,
        file_languages: Optional[Dict[str, str]] = None,
        custom_prompt: Optional[str] = None,
    ) -> str:
        """
        Get prompt with additional context about the diff.
        
        Args:
            focus: Review focus area
            diff: Git diff being reviewed
            file_languages: Mapping of file paths to detected languages
            custom_prompt: Custom prompt to use
            
        Returns:
            Contextualized prompt
        """
        # Gather context information
        context_vars = {
            "total_files": diff.total_files,
            "total_additions": diff.total_additions,
            "total_deletions": diff.total_deletions,
            "source_branch": diff.source_branch,
            "target_branch": diff.target_branch,
            "repository": diff.repository,
        }
        
        # Add language information
        if file_languages:
            unique_languages = set(file_languages.values())
            context_vars["languages"] = list(unique_languages)
            context_vars["primary_language"] = max(file_languages.values(), key=list(file_languages.values()).count) if file_languages else None
        
        # Get base prompt
        prompt = self.get_prompt(focus, custom_prompt, **context_vars)
        
        # Add context-specific instructions
        if diff.total_files > 10:
            prompt += "\n\nNote: This is a large changeset with many files. Focus on the most critical issues."
        
        if context_vars.get("primary_language"):
            prompt += f"\n\nPrimary language: {context_vars['primary_language']}. Consider language-specific best practices."
        
        return prompt 
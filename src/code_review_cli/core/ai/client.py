"""Abstract AI client interface for code review analysis."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ...models.review import ReviewResult, ReviewRequest
from ...models.diff import GitDiff
from ...models.config import AIConfig


@dataclass
class AIResponse:
    """Response from AI API call."""
    
    content: str
    usage: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    request_id: Optional[str] = None
    cost_estimate: Optional[float] = None


class AIClient(ABC):
    """Abstract base class for AI clients."""
    
    def __init__(self, config: AIConfig):
        """
        Initialize AI client.
        
        Args:
            config: AI configuration settings
        """
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate the AI configuration."""
        pass
    
    @abstractmethod
    async def analyze_code(
        self,
        request: ReviewRequest,
        diff: GitDiff,
        prompt: str,
    ) -> AIResponse:
        """
        Analyze code using AI.
        
        Args:
            request: Review request parameters
            diff: Git diff to analyze
            prompt: System prompt for analysis
            
        Returns:
            AI response with analysis
        """
        pass
    
    @abstractmethod
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Estimate the cost of an AI request.
        
        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """
        Get token count for text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass
    
    def prepare_diff_context(
        self,
        diff: GitDiff,
        max_context_size: int = 8000,
    ) -> str:
        """
        Prepare diff context for AI analysis.
        
        Args:
            diff: Git diff to analyze
            max_context_size: Maximum context size in tokens
            
        Returns:
            Formatted diff context
        """
        context_parts = [
            f"Repository: {diff.repository or 'unknown'}",
            f"Source Branch: {diff.source_branch or 'unknown'}",
            f"Target Branch: {diff.target_branch}",
            f"Files Changed: {diff.total_files}",
            f"Lines Added: {diff.total_additions}",
            f"Lines Deleted: {diff.total_deletions}",
            "",
            "=== FILE CHANGES ===",
        ]
        
        current_tokens = self.get_token_count("\n".join(context_parts))
        
        for diff_file in diff.files:
            # Format file header
            file_header = f"\n--- {diff_file.path} ---"
            if diff_file.change_type.value != "modified":
                file_header += f" ({diff_file.change_type.value})"
            
            # Add language information
            if diff_file.language:
                file_header += f" [Language: {diff_file.language}]"
            
            file_header += f"\nStats: +{diff_file.stats.additions} -{diff_file.stats.deletions}"
            
            # Check if we can fit this file
            file_tokens = self.get_token_count(file_header)
            if current_tokens + file_tokens > max_context_size:
                context_parts.append(f"\n... (remaining {len(diff.files) - len([f for f in diff.files if f == diff_file])} files truncated due to size)")
                break
            
            context_parts.append(file_header)
            current_tokens += file_tokens
            
            # Add hunks if we have space
            if not diff_file.binary and diff_file.hunks:
                for hunk in diff_file.hunks:
                    hunk_content = self._format_hunk(hunk)
                    hunk_tokens = self.get_token_count(hunk_content)
                    
                    if current_tokens + hunk_tokens > max_context_size:
                        context_parts.append("... (hunk truncated due to size)")
                        break
                    
                    context_parts.append(hunk_content)
                    current_tokens += hunk_tokens
        
        return "\n".join(context_parts)
    
    def _format_hunk(self, hunk) -> str:
        """Format a diff hunk for AI context."""
        lines = [hunk.header]
        
        for line in hunk.lines:
            lines.append(f"{line.line_type}{line.content}")
        
        return "\n".join(lines)
    
    def prepare_file_context(
        self,
        file_content: str,
        file_path: str,
        language: Optional[str] = None,
        max_lines: int = 500,
    ) -> str:
        """
        Prepare individual file context for analysis.
        
        Args:
            file_content: Content of the file
            file_path: Path to the file
            language: Programming language
            max_lines: Maximum lines to include
            
        Returns:
            Formatted file context
        """
        lines = file_content.split('\n')
        
        context_parts = [
            f"=== {file_path} ===",
        ]
        
        if language:
            context_parts.append(f"Language: {language}")
        
        context_parts.extend([
            f"Total Lines: {len(lines)}",
            "",
        ])
        
        # Include file content (truncated if necessary)
        if len(lines) > max_lines:
            context_parts.append(f"```{language or ''}")
            context_parts.extend(lines[:max_lines])
            context_parts.extend([
                "...",
                f"(File truncated after {max_lines} lines)",
                "```",
            ])
        else:
            context_parts.append(f"```{language or ''}")
            context_parts.extend(lines)
            context_parts.append("```")
        
        return "\n".join(context_parts)
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get rate limit information.
        
        Returns:
            Rate limit information
        """
        return {
            "max_requests_per_minute": self.config.max_requests_per_minute,
            "retry_attempts": self.config.retry_attempts,
            "timeout": self.config.timeout,
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information.
        
        Returns:
            Model information
        """
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        } 
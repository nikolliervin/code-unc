"""
Ollama AI client implementation for local model inference.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import aiohttp
import asyncio
import uuid

from .client import AIClient, AIResponse
from ...models import ReviewRequest, ReviewResult, Issue, IssueSeverity, IssueCategory
from ...models.diff import GitDiff
from ...models.review import ReviewMetrics
from ...models.config import AIConfig

logger = logging.getLogger(__name__)


class OllamaClient(AIClient):
    """Ollama client for local model inference."""
    
    def __init__(self, config: AIConfig):
        """Initialize Ollama client with configuration."""
        super().__init__(config)
        self.base_url = config.ollama_base_url.rstrip('/')
        self.model = config.ollama_model
        self.session: Optional[aiohttp.ClientSession] = None
    
    def _validate_config(self) -> None:
        """Validate Ollama configuration."""
        if not self.config.ollama_base_url:
            raise ValueError("Ollama base URL is required")
        if not self.config.ollama_model:
            raise ValueError("Ollama model is required")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, prompt: str, system_prompt: str = "") -> str:
        """Make request to Ollama API."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "top_p": 0.9,
                "num_predict": self.config.max_tokens
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                result = await response.json()
                return result.get("response", "")
        
        except Exception as e:
            logger.error(f"Ollama API request failed: {e}")
            raise
    
    async def analyze_code(
        self,
        request: ReviewRequest,
        diff: GitDiff,
        prompt: str,
    ) -> AIResponse:
        """Analyze code using Ollama - updated to match base class signature."""
        
        # Prepare the prompt with diff context
        full_prompt = self._prepare_diff_context(diff, request) + "\n\n" + prompt
        
        # Get AI response
        response_text = await self._make_request(full_prompt)
        
        return AIResponse(
            content=response_text,
            model=self.model,
            cost_estimate=0.0  # Free for local models
        )
    
    def _prepare_diff_context(self, diff: GitDiff, request: ReviewRequest) -> str:
        """Prepare the diff context for AI analysis."""
        
        context = f"""
Please review the following code changes and provide feedback in JSON format.

Focus areas: {request.focus.value if request.focus else 'General code review'}

Files changed: {len(diff.files)} files

"""
        
        for file in diff.files:
            context += f"\n--- File: {file.path} ---\n"
            context += f"Change type: {file.change_type.value}\n"
            
            for hunk in file.hunks:
                context += f"\n@@ Line {hunk.start_line} @@\n"
                for line in hunk.lines:
                    context += f"{line.line_number}: {line.content}\n"
        
        context += """

Please analyze this code and provide feedback in the following JSON format:
{
  "issues": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "category": "SECURITY|PERFORMANCE|BUG|CODE_STYLE|ARCHITECTURE",
      "title": "Brief issue title",
      "description": "Detailed description of the issue",
      "file": "path/to/file",
      "line": 123,
      "suggestion": "How to fix this issue"
    }
  ],
  "summary": "Overall assessment of the changes"
}
"""
        
        return context
    
    def _parse_ai_response(self, response_text: str, diff: GitDiff) -> List[Issue]:
        """Parse AI response into structured issues."""
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
                        issue = Issue(
                            severity=IssueSeverity(issue_data.get("severity", "MEDIUM")),
                            category=IssueCategory(issue_data.get("category", "CODE_STYLE")),
                            title=issue_data.get("title", "Code review issue"),
                            description=issue_data.get("description", ""),
                            location={
                                "file": issue_data.get("file", ""),
                                "line": issue_data.get("line", 0)
                            },
                            suggestion=issue_data.get("suggestion", "")
                        )
                        issues.append(issue)
                    except Exception as e:
                        logger.warning(f"Failed to parse issue: {e}")
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            # Fallback: create a generic issue
            issues.append(Issue(
                severity=IssueSeverity.MEDIUM,
                category=IssueCategory.CODE_STYLE,
                title="AI Response Parse Error",
                description=f"Could not parse AI response: {response_text[:200]}...",
                location={"file": "", "line": 0},
                suggestion="Check the AI response format"
            ))
        
        return issues
    
    def _generate_summary(self, issues: List[Issue]) -> str:
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
    
    async def estimate_cost(self, diff: GitDiff) -> float:
        """Estimate cost for Ollama (always 0 for local)."""
        return 0.0
    
    def get_token_count(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count
        """
        # Simple estimation: roughly 4 characters per token
        return len(text) // 4
    
    async def test_connection(self) -> bool:
        """Test connection to Ollama."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False 
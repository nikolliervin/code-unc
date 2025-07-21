"""OpenAI client implementation for code review analysis."""

import logging
import asyncio
import json
from typing import Dict, Any, Optional

import openai
from openai import AsyncOpenAI

from .client import AIClient, AIResponse
from ...models.review import ReviewRequest
from ...models.diff import GitDiff
from ...models.config import AIConfig


logger = logging.getLogger(__name__)


class OpenAIClient(AIClient):
    """OpenAI client for code review analysis."""
    
    # Pricing per 1K tokens (as of 2024) - update as needed
    PRICING = {
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
        "gpt-4-0125-preview": {"input": 0.01, "output": 0.03},
    }
    
    def __init__(self, config: AIConfig):
        """Initialize OpenAI client."""
        super().__init__(config)
        
        # Initialize async OpenAI client
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.api_base,
            timeout=config.timeout,
        )
    
    def _validate_config(self) -> None:
        """Validate OpenAI configuration."""
        if not self.config.api_key:
            raise ValueError("OpenAI API key is required")
        
        if not self.config.api_key.startswith("sk-"):
            raise ValueError("OpenAI API key should start with 'sk-'")
        
        if self.config.model not in self.PRICING:
            logger.warning(f"Unknown model {self.config.model}, cost estimation may be inaccurate")
    
    async def analyze_code(
        self,
        request: ReviewRequest,
        diff: GitDiff,
        prompt: str,
    ) -> AIResponse:
        """
        Analyze code using OpenAI API.
        
        Args:
            request: Review request parameters
            diff: Git diff to analyze
            prompt: System prompt for analysis
            
        Returns:
            AI response with analysis
        """
        try:
            # Prepare context
            diff_context = self.prepare_diff_context(diff)
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": f"Please analyze the following code changes:\n\n{diff_context}"
                }
            ]
            
            # Add additional context if provided
            if request.context:
                messages.append({
                    "role": "user",
                    "content": f"Additional context: {request.context}"
                })
            
            # Prepare API parameters
            api_params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": request.temperature or self.config.temperature,
                "response_format": {"type": "json_object"},
            }
            
            # Add max_tokens if specified
            if self.config.max_tokens:
                api_params["max_tokens"] = self.config.max_tokens
            
            logger.info(f"Making OpenAI API call with model {self.config.model}")
            
            # Make API call with retries
            response = await self._make_api_call_with_retry(api_params)
            
            # Extract response data
            content = response.choices[0].message.content
            usage = response.usage._asdict() if response.usage else None
            
            # Calculate cost estimate
            cost_estimate = None
            if usage:
                cost_estimate = self.estimate_cost(
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0)
                )
            
            return AIResponse(
                content=content,
                usage=usage,
                model=response.model,
                finish_reason=response.choices[0].finish_reason,
                request_id=getattr(response, 'id', None),
                cost_estimate=cost_estimate,
            )
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise RuntimeError(f"OpenAI API error: {e}")
    
    async def _make_api_call_with_retry(self, api_params: Dict[str, Any]) -> Any:
        """Make API call with retry logic."""
        for attempt in range(self.config.retry_attempts + 1):
            try:
                response = await self.client.chat.completions.create(**api_params)
                return response
                
            except openai.RateLimitError as e:
                if attempt < self.config.retry_attempts:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except openai.APITimeoutError as e:
                if attempt < self.config.retry_attempts:
                    wait_time = 2 ** attempt
                    logger.warning(f"Timeout, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except openai.APIError as e:
                if attempt < self.config.retry_attempts and e.status_code >= 500:
                    wait_time = 2 ** attempt
                    logger.warning(f"Server error {e.status_code}, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                raise
    
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Estimate cost for OpenAI API call.
        
        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        if self.config.model not in self.PRICING:
            return 0.0
        
        pricing = self.PRICING[self.config.model]
        
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def get_token_count(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Note: This is a rough estimation. For exact counts, use tiktoken library.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated number of tokens
        """
        # Rough estimation: ~4 characters per token for English text
        # This is an approximation and may not be perfectly accurate
        return len(text) // 4
    
    def get_precise_token_count(self, text: str) -> int:
        """
        Get precise token count using tiktoken (if available).
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Precise number of tokens
        """
        try:
            import tiktoken
            
            # Get encoding for the model
            if self.config.model.startswith("gpt-4"):
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif self.config.model.startswith("gpt-3.5"):
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                # Fallback to cl100k_base encoding
                encoding = tiktoken.get_encoding("cl100k_base")
            
            return len(encoding.encode(text))
            
        except ImportError:
            logger.debug("tiktoken not available, using rough estimation")
            return self.get_token_count(text)
        except Exception as e:
            logger.warning(f"Error calculating precise token count: {e}")
            return self.get_token_count(text)
    
    def validate_response_format(self, response_content: str) -> bool:
        """
        Validate that the response is valid JSON.
        
        Args:
            response_content: Response content to validate
            
        Returns:
            True if valid JSON, False otherwise
        """
        try:
            json.loads(response_content)
            return True
        except json.JSONDecodeError:
            return False
    
    async def test_connection(self) -> bool:
        """
        Test connection to OpenAI API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Make a simple API call to test connectivity
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
                temperature=0,
            )
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close the client connection."""
        await self.client.close() 
"""Mistral client implementation for code review analysis."""

import logging
import asyncio
import json
from typing import Dict, Any, Optional

from mistralai import Mistral as MistralSDK
from mistralai import SDKError

from .client import AIClient, AIResponse
from ...models.review import ReviewRequest
from ...models.diff import GitDiff
from ...models.config import AIConfig


logger = logging.getLogger(__name__)


class MistralClient(AIClient):
    """Mistral client for code review analysis."""
    
    # Pricing per 1M tokens (as of 2024) - update as needed
    PRICING = {
        "mistral-large-latest": {"input": 3.0, "output": 9.0},
        "mistral-medium-latest": {"input": 2.7, "output": 8.1},
        "mistral-small-latest": {"input": 0.2, "output": 0.6},
        "codestral-latest": {"input": 0.2, "output": 0.6},
        "mistral-moderation-latest": {"input": 0.1, "output": 0.1},
        "mistral-embed": {"input": 0.1, "output": 0.0},  # Embedding model
    }
    
    def __init__(self, config: AIConfig):
        """Initialize Mistral client."""
        super().__init__(config)
        
        # Initialize Mistral client
        self.client = MistralSDK(
            api_key=config.api_key,
            server_url=config.api_base or "https://api.mistral.ai",
            timeout_ms=int(config.timeout * 1000) if config.timeout else None,
        )
    
    def _validate_config(self) -> None:
        """Validate Mistral configuration."""
        if not self.config.api_key:
            raise ValueError("Mistral API key is required")
        
        if self.config.model not in self.PRICING:
            logger.warning(f"Unknown model {self.config.model}, cost estimation may be inaccurate")
    
    async def analyze_code(
        self,
        request: ReviewRequest,
        diff: GitDiff,
        prompt: str,
    ) -> AIResponse:
        """
        Analyze code using Mistral API.
        
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
            
            # Prepare user message content
            user_content = f"Please analyze the following code changes and respond with valid JSON:\n\n{diff_context}"
            
            # Add additional context if provided
            if request.context:
                user_content += f"\n\nAdditional context: {request.context}"
            
            # Prepare messages
            messages = [
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user", 
                    "content": user_content
                }
            ]
            
            # Prepare API parameters
            api_params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": request.temperature or self.config.temperature,
                "stream": False,
            }
            
            # Add max_tokens if specified
            if self.config.max_tokens:
                api_params["max_tokens"] = self.config.max_tokens
            
            logger.info(f"Making Mistral API call with model {self.config.model}")
            
            # Make API call with retries
            response = await self._make_api_call_with_retry(api_params)
            
            # Extract response data
            content = response.choices[0].message.content if response.choices else ""
            
            # Prepare usage info
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": (response.usage.prompt_tokens + response.usage.completion_tokens) if response.usage else 0,
            }
            
            # Calculate cost estimate
            cost_estimate = self.estimate_cost(
                usage["prompt_tokens"],
                usage["completion_tokens"]
            )
            
            return AIResponse(
                content=content,
                usage=usage,
                model=response.model,
                finish_reason=response.choices[0].finish_reason if response.choices else None,
                request_id=response.id,
                cost_estimate=cost_estimate,
            )
            
        except Exception as e:
            logger.error(f"Mistral API call failed: {e}")
            raise RuntimeError(f"Mistral API error: {e}")
    
    async def _make_api_call_with_retry(self, api_params: Dict[str, Any]) -> Any:
        """Make API call with retry logic."""
        for attempt in range(self.config.retry_attempts + 1):
            try:
                response = await self.client.chat.complete_async(**api_params)
                return response
                
            except SDKError as e:
                # Handle rate limiting and retryable errors
                if hasattr(e, 'status_code'):
                    if e.status_code == 429:  # Rate limit error
                        if attempt < self.config.retry_attempts:
                            wait_time = 2 ** attempt  # Exponential backoff
                            logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1})")
                            await asyncio.sleep(wait_time)
                            continue
                    elif e.status_code >= 500:  # Server error
                        if attempt < self.config.retry_attempts:
                            wait_time = 2 ** attempt
                            logger.warning(f"Server error, retrying in {wait_time}s (attempt {attempt + 1})")
                            await asyncio.sleep(wait_time)
                            continue
                raise
    
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Estimate cost for Mistral API call.
        
        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        if self.config.model not in self.PRICING:
            return 0.0
        
        pricing = self.PRICING[self.config.model]
        
        # Pricing is per 1M tokens
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def get_token_count(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Note: This is a rough estimation for Mistral models.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated number of tokens
        """
        # Rough estimation: ~4 characters per token for Mistral models
        # This is an approximation and may not be perfectly accurate
        return int(len(text) / 4)
    
    def get_precise_token_count(self, text: str) -> int:
        """
        Get token count using Mistral's tokenizer (if available).
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Token count
        """
        try:
            # Mistral doesn't provide a public tokenizer yet
            # Fall back to rough estimation
            return self.get_token_count(text)
            
        except Exception as e:
            logger.warning(f"Error calculating token count: {e}")
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
        Test connection to Mistral API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Make a simple API call to test connectivity
            response = await self.client.chat.complete_async(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
                temperature=0,
            )
            return True
        except Exception as e:
            logger.error(f"Mistral connection test failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close the client connection."""
        # The Mistral SDK doesn't require explicit closing
        pass 
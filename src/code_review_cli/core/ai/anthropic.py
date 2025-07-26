"""Anthropic client implementation for code review analysis."""

import logging
import asyncio
import json
from typing import Dict, Any, Optional

import anthropic
from anthropic import AsyncAnthropic

from .client import AIClient, AIResponse
from ...models.review import ReviewRequest
from ...models.diff import GitDiff
from ...models.config import AIConfig


logger = logging.getLogger(__name__)


class AnthropicClient(AIClient):
    """Anthropic client for code review analysis."""
    
    # Pricing per 1M tokens (as of 2024) - update as needed
    PRICING = {
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-2.1": {"input": 8.0, "output": 24.0},
        "claude-2.0": {"input": 8.0, "output": 24.0},
    }
    
    def __init__(self, config: AIConfig):
        """Initialize Anthropic client."""
        super().__init__(config)
        
        # Initialize async Anthropic client
        self.client = AsyncAnthropic(
            api_key=config.anthropic_api_key,
            timeout=config.timeout,
        )
    
    def _validate_config(self) -> None:
        """Validate Anthropic configuration."""
        if not self.config.anthropic_api_key:
            raise ValueError("Anthropic API key is required")
        
        if self.config.model not in self.PRICING:
            logger.warning(f"Unknown model {self.config.model}, cost estimation may be inaccurate")
    
    async def __aenter__(self):
        """Enter async context manager."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        await self.close()
    
    async def analyze_code(
        self,
        request: ReviewRequest,
        diff: GitDiff,
        prompt: str,
    ) -> AIResponse:
        """
        Analyze code using Anthropic API.
        
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
            
            # Prepare API parameters
            api_params = {
                "model": self.config.model,
                "system": prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_content
                    }
                ],
                "temperature": request.temperature or self.config.temperature,
            }
            
            # Add max_tokens if specified
            if self.config.max_tokens:
                api_params["max_tokens"] = self.config.max_tokens
            else:
                # Anthropic requires max_tokens to be specified
                api_params["max_tokens"] = 4096
            
            logger.info(f"Making Anthropic API call with model {self.config.model}")
            
            # Make API call with retries
            response = await self._make_api_call_with_retry(api_params)
            
            # Extract response data
            content = response.content[0].text if response.content else ""
            
            # Prepare usage info
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
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
                finish_reason=response.stop_reason,
                request_id=response.id,
                cost_estimate=cost_estimate,
            )
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise RuntimeError(f"Anthropic API error: {e}")
    
    async def _make_api_call_with_retry(self, api_params: Dict[str, Any]) -> Any:
        """Make API call with retry logic."""
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self.client.messages.create(**api_params)
                return response
                
            except anthropic.RateLimitError as e:
                if attempt < self.config.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except anthropic.APITimeoutError as e:
                if attempt < self.config.max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"Timeout, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except anthropic.APIError as e:
                if attempt < self.config.max_retries and hasattr(e, 'status_code') and e.status_code >= 500:
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
        Estimate cost for Anthropic API call.
        
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
        
        Note: This is a rough estimation for Anthropic models.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated number of tokens
        """
        # Rough estimation: ~3.5 characters per token for Claude models
        # This is an approximation and may not be perfectly accurate
        return int(len(text) / 3.5)
    
    def get_precise_token_count(self, text: str) -> int:
        """
        Get token count using Anthropic's tokenizer (if available).
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Token count
        """
        try:
            # Anthropic doesn't provide a public tokenizer yet
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
        Test connection to Anthropic API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Make a simple API call to test connectivity
            response = await self.client.messages.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
                temperature=0,
            )
            return True
        except Exception as e:
            logger.error(f"Anthropic connection test failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close the client connection."""
        await self.client.close() 
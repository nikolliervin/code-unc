"""Google Gemini client implementation for code review analysis."""

import logging
import asyncio
import json
from typing import Dict, Any, Optional

import aiohttp
from .client import AIClient, AIResponse
from ...models.review import ReviewRequest
from ...models.diff import GitDiff
from ...models.config import AIConfig


logger = logging.getLogger(__name__)


class GeminiClient(AIClient):
    """Google Gemini client for code review analysis."""
    
    # Pricing per 1M tokens (updated January 2025) - from Google AI API pricing
    PRICING = {
        # Gemini 2.5 models (Latest)
        "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
        "gemini-2.5-pro": {"input": 1.25, "output": 10.00},  # <200k tokens
        "gemini-2.5-flash-reasoning": {"input": 0.15, "output": 3.50},  # thinking tokens
        
        # Gemini 2.0 models 
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        "gemini-2.0-flash-lite": {"input": 0.075, "output": 0.30},
        "gemini-2.0-pro": {"input": 1.25, "output": 10.00},
        
        # Gemini 1.5 models (Legacy)
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},  # <128k tokens
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},  # <128k tokens  
        "gemini-1.5-flash-8b": {"input": 0.0375, "output": 0.15},  # <128k tokens
        "gemini-1.0-pro": {"input": 0.50, "output": 1.50},
    }
    
    def __init__(self, config: AIConfig):
        """Initialize Gemini client."""
        super().__init__(config)
        
        self.api_key = config.gemini_api_key
        self.base_url = config.gemini_base_url or "https://generativelanguage.googleapis.com/v1beta"
        self.session: Optional[aiohttp.ClientSession] = None
    
    def _validate_config(self) -> None:
        """Validate Gemini configuration."""
        if not self.config.gemini_api_key:
            raise ValueError("Gemini API key is required")
        
        if self.config.model not in self.PRICING:
            logger.warning(f"Unknown model {self.config.model}, cost estimation may be inaccurate")
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_code(
        self,
        request: ReviewRequest,
        diff: GitDiff,
        prompt: str,
    ) -> AIResponse:
        """
        Analyze code using Google Gemini API.
        
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
            
            # Prepare the request content
            user_content = f"Please analyze the following code changes and respond with valid JSON:\n\n{diff_context}"
            
            # Add additional context if provided
            if request.context:
                user_content += f"\n\nAdditional context: {request.context}"
            
            # Combine system prompt with user content for Gemini
            full_content = f"{prompt}\n\n{user_content}"
            
            # Prepare API parameters
            api_params = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": full_content
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": request.temperature or self.config.temperature,
                    "candidateCount": 1,
                    "topP": 0.95,
                    "topK": 40,
                }
            }
            
            # Add max_tokens if specified
            if self.config.max_tokens:
                api_params["generationConfig"]["maxOutputTokens"] = self.config.max_tokens
            
            logger.info(f"Making Gemini API call with model {self.config.model}")
            
            # Make API call with retries
            response_data = await self._make_api_call_with_retry(api_params)
            
            # Extract response data
            content = ""
            if response_data.get("candidates") and len(response_data["candidates"]) > 0:
                candidate = response_data["candidates"][0]
                if candidate.get("content") and candidate["content"].get("parts"):
                    content = candidate["content"]["parts"][0].get("text", "")
            
            # Extract usage information
            usage = response_data.get("usageMetadata", {})
            
            # Calculate cost estimate
            cost_estimate = None
            if usage:
                cost_estimate = self.estimate_cost(
                    usage.get("promptTokenCount", 0),
                    usage.get("candidatesTokenCount", 0)
                )
            
            return AIResponse(
                content=content,
                usage=usage,
                model=self.config.model,
                finish_reason=response_data.get("candidates", [{}])[0].get("finishReason"),
                request_id=None,  # Gemini doesn't provide request ID in response
                cost_estimate=cost_estimate,
            )
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise RuntimeError(f"Gemini API error: {e}")
    
    async def _make_api_call_with_retry(self, api_params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call with retry logic."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/models/{self.config.model}:generateContent"
        
        for attempt in range(self.config.max_retries + 1):
            try:
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key
                }
                
                async with self.session.post(
                    url,
                    json=api_params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        return response_data
                    elif response.status == 429:  # Rate limit
                        if attempt < self.config.retry_attempts:
                            wait_time = 2 ** attempt  # Exponential backoff
                            logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1})")
                            await asyncio.sleep(wait_time)
                            continue
                        raise Exception(f"Rate limit exceeded after {self.config.retry_attempts} retries")
                    elif response.status >= 500:  # Server error
                        if attempt < self.config.retry_attempts:
                            wait_time = 2 ** attempt
                            logger.warning(f"Server error {response.status}, retrying in {wait_time}s (attempt {attempt + 1})")
                            await asyncio.sleep(wait_time)
                            continue
                        raise Exception(f"Server error: {response.status}")
                    else:
                        error_msg = response_data.get("error", {}).get("message", f"HTTP {response.status}")
                        raise Exception(f"API error: {error_msg}")
                        
            except asyncio.TimeoutError:
                if attempt < self.config.retry_attempts:
                    wait_time = 2 ** attempt
                    logger.warning(f"Timeout, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                raise Exception("Request timeout")
            except aiohttp.ClientError as e:
                if attempt < self.config.retry_attempts:
                    wait_time = 2 ** attempt
                    logger.warning(f"Client error {e}, retrying in {wait_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                raise Exception(f"Client error: {e}")
    
    def estimate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """
        Estimate the cost of a Gemini request.
        
        Args:
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        if self.config.model not in self.PRICING:
            return 0.0
        
        pricing = self.PRICING[self.config.model]
        
        # Convert to millions for pricing calculation
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def get_token_count(self, text: str) -> int:
        """
        Get rough token count for text (Gemini-specific estimation).
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated number of tokens
        """
        # Rough estimation: ~4 characters per token for English text
        # This is an approximation; for precise counting, use Gemini's token counting API
        return len(text) // 4
    
    async def get_precise_token_count(self, text: str) -> int:
        """
        Get precise token count using Gemini's token counting API.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Precise number of tokens
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/models/{self.config.model}:countTokens"
        
        try:
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": text
                            }
                        ]
                    }
                ]
            }
            
            async with self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("totalTokens", 0)
                else:
                    # Fall back to estimation
                    return self.get_token_count(text)
        
        except Exception as e:
            logger.warning(f"Failed to get precise token count: {e}")
            return self.get_token_count(text)
    
    async def test_connection(self) -> bool:
        """Test connection to Gemini API."""
        try:
            # Make a simple test request
            test_params = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": "Hello, respond with 'OK' if you can hear me."
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": 10,
                    "temperature": 0.1,
                }
            }
            
            response = await self._make_api_call_with_retry(test_params)
            return bool(response.get("candidates"))
            
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None 
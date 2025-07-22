"""
Configuration models for the code review CLI.
"""

from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class AIConfig(BaseModel):
    """AI provider configuration."""
    
    provider: str = Field(default="openai", description="AI provider: openai, anthropic, ollama, gemini")
    model: str = Field(default="gpt-4", description="Model name")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int = Field(default=4000, ge=1, le=32000, description="Maximum tokens to generate")
    
    # OpenAI specific
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_base_url: Optional[str] = Field(default=None, description="OpenAI base URL")
    
    # Anthropic specific
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    
    # Gemini specific
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    gemini_base_url: Optional[str] = Field(default=None, description="Gemini base URL")
    
    # Ollama specific
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    ollama_model: str = Field(default="codellama:7b", description="Ollama model name")
    
    # Retry settings
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    timeout: float = Field(default=60.0, description="Request timeout in seconds")
    
    @validator('provider')
    def validate_provider(cls, v):
        if v not in ['openai', 'anthropic', 'ollama', 'gemini']:
            raise ValueError('Provider must be one of: openai, anthropic, ollama, gemini')
        return v


class GitConfig(BaseModel):
    """Git configuration."""
    
    default_source: str = Field(default="HEAD", description="Default source branch/commit")
    default_target: str = Field(default="main", description="Default target branch")
    max_diff_size: int = Field(default=100000, description="Maximum diff size in bytes")
    include_patterns: List[str] = Field(default=[], description="File patterns to include")
    exclude_patterns: List[str] = Field(default=[], description="File patterns to exclude")
    binary_files: bool = Field(default=False, description="Include binary files in review")


class OutputConfig(BaseModel):
    """Output configuration."""
    
    format: str = Field(default="rich", description="Output format: rich, json, markdown, html")
    show_progress: bool = Field(default=True, description="Show progress bars")
    show_metrics: bool = Field(default=True, description="Show review metrics")
    show_suggestions: bool = Field(default=True, description="Show improvement suggestions")
    max_issues_display: int = Field(default=50, description="Maximum issues to display")
    
    # Console-specific settings
    console_width: Optional[int] = Field(default=None, description="Console width (auto-detect if None)")
    color_enabled: bool = Field(default=True, description="Enable colored output")
    
    @validator('format')
    def validate_format(cls, v):
        if v not in ['rich', 'json', 'markdown', 'html']:
            raise ValueError('Format must be one of: rich, json, markdown, html')
        return v


class CacheConfig(BaseModel):
    """Cache configuration."""
    
    enabled: bool = Field(default=True, description="Enable caching")
    ttl_hours: int = Field(default=24, description="Cache TTL in hours")
    max_size_mb: int = Field(default=100, description="Maximum cache size in MB")
    cleanup_interval_hours: int = Field(default=168, description="Cache cleanup interval in hours")


class ReviewConfig(BaseModel):
    """Review configuration."""
    
    default_focus: List[str] = Field(default=[], description="Default focus areas")
    severity_threshold: str = Field(default="LOW", description="Minimum severity to report")
    max_files_per_review: int = Field(default=100, description="Maximum files per review")
    timeout_seconds: int = Field(default=300, description="Review timeout in seconds")
    
    @validator('severity_threshold')
    def validate_severity(cls, v):
        if v not in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            raise ValueError('Severity must be one of: CRITICAL, HIGH, MEDIUM, LOW')
        return v


class Config(BaseModel):
    """Main configuration model."""
    
    ai: AIConfig = Field(default_factory=AIConfig, description="AI configuration")
    git: GitConfig = Field(default_factory=GitConfig, description="Git configuration")
    output: OutputConfig = Field(default_factory=OutputConfig, description="Output configuration")
    cache: CacheConfig = Field(default_factory=CacheConfig, description="Cache configuration")
    review: ReviewConfig = Field(default_factory=ReviewConfig, description="Review configuration")
    
    # Metadata
    version: str = Field(default="1.0.0", description="Configuration version")
    created_at: Optional[str] = Field(default=None, description="Configuration creation timestamp")
    
    class Config:
        extra = "forbid"
        validate_assignment = True 
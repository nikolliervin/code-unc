"""Configuration data models for the application."""

from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class AIConfig(BaseModel):
    """Configuration for AI providers."""
    
    # Provider settings
    provider: str = Field("openai", description="AI provider (openai, anthropic)")
    model: str = Field("gpt-4-turbo", description="AI model to use")
    api_key: Optional[str] = Field(None, description="API key for the provider")
    api_base: Optional[str] = Field(None, description="Custom API base URL")
    
    # Generation parameters
    temperature: float = Field(0.2, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")
    timeout: int = Field(60, ge=1, description="Request timeout in seconds")
    
    # Rate limiting
    max_requests_per_minute: int = Field(50, ge=1, description="Rate limit for API calls")
    retry_attempts: int = Field(3, ge=0, description="Number of retry attempts")
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['openai', 'anthropic']
        if v not in allowed:
            raise ValueError(f'Provider must be one of: {", ".join(allowed)}')
        return v
    
    @validator('model')
    def validate_model(cls, v, values):
        provider = values.get('provider')
        if provider == 'openai':
            allowed_models = [
                'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo',
                'gpt-4-1106-preview', 'gpt-4-0125-preview'
            ]
        elif provider == 'anthropic':
            allowed_models = [
                'claude-3-opus-20240229', 'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307', 'claude-2.1', 'claude-2.0'
            ]
        else:
            return v  # Skip validation for unknown providers
        
        if v not in allowed_models:
            raise ValueError(f'Model {v} not supported for provider {provider}')
        return v


class GitConfig(BaseModel):
    """Configuration for Git operations."""
    
    # Default branches
    default_target_branch: str = Field("main", description="Default target branch")
    default_source_branch: Optional[str] = Field(None, description="Default source branch")
    
    # File filtering
    include_patterns: List[str] = Field(
        default_factory=lambda: ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.c", "*.cpp", "*.h", "*.cs", "*.rb", "*.go", "*.rs", "*.php"],
        description="Default file patterns to include"
    )
    exclude_patterns: List[str] = Field(
        default_factory=lambda: ["*.min.js", "*.min.css", "node_modules/*", "__pycache__/*", ".git/*", "*.pyc", "*.class"],
        description="Default file patterns to exclude"
    )
    
    # Limits
    max_files_per_review: int = Field(50, ge=1, description="Maximum files to review")
    max_file_size_kb: int = Field(500, ge=1, description="Maximum file size in KB")
    max_diff_lines: int = Field(1000, ge=1, description="Maximum diff lines per file")
    
    # Git settings
    ignore_whitespace: bool = Field(True, description="Ignore whitespace changes")
    ignore_binary_files: bool = Field(True, description="Ignore binary files")


class OutputConfig(BaseModel):
    """Configuration for output formatting."""
    
    # Format settings
    default_format: str = Field("rich", description="Default output format")
    color_enabled: bool = Field(True, description="Enable colored output")
    verbose: bool = Field(False, description="Enable verbose output")
    
    # Rich console settings
    console_width: Optional[int] = Field(None, ge=40, description="Console width (auto-detect if None)")
    show_progress: bool = Field(True, description="Show progress indicators")
    
    # File output
    save_to_file: bool = Field(False, description="Save output to file")
    output_directory: str = Field("./reviews", description="Directory for saved reviews")
    
    @validator('default_format')
    def validate_format(cls, v):
        allowed = ['rich', 'json', 'markdown', 'html']
        if v not in allowed:
            raise ValueError(f'Format must be one of: {", ".join(allowed)}')
        return v


class CacheConfig(BaseModel):
    """Configuration for caching."""
    
    # Cache settings
    enabled: bool = Field(True, description="Enable caching")
    cache_directory: str = Field("~/.cache/code-review-cli", description="Cache directory")
    
    # TTL settings (in seconds)
    git_diff_ttl: int = Field(3600, ge=0, description="Git diff cache TTL")
    ai_response_ttl: int = Field(86400, ge=0, description="AI response cache TTL")
    
    # Size limits
    max_cache_size_mb: int = Field(100, ge=1, description="Maximum cache size in MB")
    cleanup_interval_hours: int = Field(24, ge=1, description="Cache cleanup interval")


class ReviewConfig(BaseModel):
    """Configuration for review behavior."""
    
    # Default settings
    default_focus: str = Field("general", description="Default review focus")
    auto_fix_suggestions: bool = Field(True, description="Generate auto-fix suggestions")
    include_explanations: bool = Field(True, description="Include detailed explanations")
    
    # Filtering
    min_confidence: float = Field(0.7, ge=0.0, le=1.0, description="Minimum confidence for issues")
    exclude_info_issues: bool = Field(False, description="Exclude info-level issues")
    
    # Custom prompts
    custom_prompts: Dict[str, str] = Field(default_factory=dict, description="Custom prompts by focus area")


class Config(BaseSettings):
    """Main application configuration."""
    
    # Sub-configurations
    ai: AIConfig = Field(default_factory=AIConfig, description="AI provider configuration")
    git: GitConfig = Field(default_factory=GitConfig, description="Git operation configuration")
    output: OutputConfig = Field(default_factory=OutputConfig, description="Output formatting configuration")
    cache: CacheConfig = Field(default_factory=CacheConfig, description="Caching configuration")
    review: ReviewConfig = Field(default_factory=ReviewConfig, description="Review behavior configuration")
    
    # Global settings
    debug: bool = Field(False, description="Enable debug mode")
    log_level: str = Field("INFO", description="Logging level")
    config_version: str = Field("1.0", description="Configuration version")
    
    class Config:
        """Pydantic configuration."""
        env_prefix = "CODE_REVIEW_"
        env_nested_delimiter = "__"
        case_sensitive = False
        
    @validator('log_level')
    def validate_log_level(cls, v):
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f'Log level must be one of: {", ".join(allowed)}')
        return v.upper()
    
    def get_config_path(self) -> Path:
        """Get the configuration file path."""
        config_dir = Path.home() / ".config" / "code-review-cli"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.yaml"
    
    def get_cache_path(self) -> Path:
        """Get the cache directory path."""
        cache_path = Path(self.cache.cache_directory).expanduser()
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path
    
    def validate_ai_config(self) -> List[str]:
        """Validate AI configuration and return any issues."""
        issues = []
        
        if not self.ai.api_key:
            issues.append(f"No API key provided for {self.ai.provider}")
        
        if self.ai.provider == "openai" and self.ai.api_key and not self.ai.api_key.startswith("sk-"):
            issues.append("OpenAI API key should start with 'sk-'")
        
        if self.ai.max_tokens and self.ai.max_tokens < 100:
            issues.append("max_tokens should be at least 100 for meaningful responses")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.dict()
    
    def get_effective_include_patterns(self, request_patterns: List[str]) -> List[str]:
        """Get effective include patterns combining config and request."""
        if request_patterns:
            return request_patterns
        return self.git.include_patterns
    
    def get_effective_exclude_patterns(self, request_patterns: List[str]) -> List[str]:
        """Get effective exclude patterns combining config and request."""
        base_patterns = self.git.exclude_patterns.copy()
        if request_patterns:
            base_patterns.extend(request_patterns)
        return base_patterns
    
    def should_cache_response(self, operation: str) -> bool:
        """Check if a response should be cached."""
        if not self.cache.enabled:
            return False
        
        ttl_map = {
            "git_diff": self.cache.git_diff_ttl,
            "ai_response": self.cache.ai_response_ttl,
        }
        
        return ttl_map.get(operation, 0) > 0 
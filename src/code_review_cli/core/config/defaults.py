"""Default configuration factory."""

from typing import Dict, Any, Optional
from pathlib import Path

from ...models.config import Config, AIConfig


def get_default_config() -> Config:
    """
    Get default configuration with sensible defaults.
    
    Returns:
        Default configuration object
    """
    return Config()  # Uses all Pydantic defaults from the model


def get_minimal_config() -> Config:
    """
    Get minimal configuration for testing or CI environments.
    
    Returns:
        Minimal configuration object
    """
    return Config(
        output={"default_format": "json", "color_enabled": False, "show_progress": False},
        cache={"enabled": False},
        debug=False,
    )


def get_development_config() -> Config:
    """
    Get development configuration with debugging enabled.
    
    Returns:
        Development configuration object
    """
    return Config(
        debug=True,
        log_level="DEBUG",
        output={"verbose": True, "show_progress": True},
        cache={"enabled": True, "git_diff_ttl": 60, "ai_response_ttl": 300},  # Short TTL for dev
        ai=AIConfig(
            provider="openai",  # Default to OpenAI
            model="gpt-4",
            temperature=0.1,
            max_tokens=4000,
            
            # OpenAI settings
            openai_api_key=None,  # Set via environment or config
            openai_base_url=None,
            
            # Anthropic settings  
            anthropic_api_key=None,
            
            # Mistral settings
            mistral_api_key=None,
            
            # Gemini settings
            gemini_api_key=None,
            gemini_base_url=None,
            
            # Ollama settings
            ollama_base_url="http://localhost:11434",
            ollama_model="codellama:7b",
        ),
    ) 
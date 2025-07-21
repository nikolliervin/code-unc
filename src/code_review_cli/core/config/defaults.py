"""Default configuration factory."""

from ...models.config import Config


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
    ) 
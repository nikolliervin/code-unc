"""Configuration management package."""

from .manager import ConfigManager
from .defaults import get_default_config

__all__ = [
    "ConfigManager",
    "get_default_config",
] 
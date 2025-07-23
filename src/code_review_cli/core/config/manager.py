"""Configuration manager for loading and saving settings."""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

import yaml
from pydantic import ValidationError

from ...models.config import Config


logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading, saving, and validation."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        if config_path is None:
            config_path = self._get_default_config_path()
        
        self.config_path = Path(config_path)
        self._config: Optional[Config] = None
    
    def _get_default_config_path(self) -> Path:
        """Get default configuration file path."""
        # Follow XDG Base Directory Specification
        config_dir = Path.home() / ".config" / "unc"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.yaml"
    
    def load_config(self, create_if_missing: bool = True) -> Config:
        """
        Load configuration from file.
        
        Args:
            create_if_missing: Create default config if file doesn't exist
            
        Returns:
            Loaded configuration
        """
        try:
            if not self.config_path.exists():
                if create_if_missing:
                    logger.info(f"Config file not found, creating default: {self.config_path}")
                    self._create_default_config()
                else:
                    logger.info("Config file not found, using defaults")
                    return self._load_from_env()
            
            logger.info(f"Loading config from: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            
            # Merge with environment variables
            config_data = self._merge_with_env(config_data)
            
            self._config = Config(**config_data)
            return self._config
            
        except ValidationError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Invalid configuration: {e}")
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing failed: {e}")
            raise ValueError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise RuntimeError(f"Configuration loading error: {e}")
    
    def save_config(self, config: Config) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save
        """
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dictionary and filter out None values
            config_dict = self._config_to_dict(config)
            
            # Write to file
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    config_dict,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    indent=2,
                    allow_unicode=True,
                )
            
            logger.info(f"Configuration saved to: {self.config_path}")
            self._config = config
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise RuntimeError(f"Configuration saving error: {e}")
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        from .defaults import get_default_config
        
        default_config = get_default_config()
        self.save_config(default_config)
    
    def _load_from_env(self) -> Config:
        """Load configuration from environment variables only."""
        try:
            # This will use pydantic-settings to load from environment
            return Config()
        except ValidationError as e:
            logger.error(f"Environment variable validation failed: {e}")
            raise ValueError(f"Invalid environment configuration: {e}")
    
    def _merge_with_env(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge configuration data with environment variables.
        
        Args:
            config_data: Configuration data from file
            
        Returns:
            Merged configuration data
        """
        # Environment variables take precedence
        env_vars = {}
        
        # Check for CODE_REVIEW_ prefixed environment variables
        for key, value in os.environ.items():
            if key.startswith('CODE_REVIEW_'):
                # Convert CODE_REVIEW_AI__API_KEY to nested dict structure
                config_key = key[12:]  # Remove CODE_REVIEW_ prefix
                
                # Handle nested keys (e.g., AI__API_KEY -> ai.api_key)
                if '__' in config_key:
                    parts = config_key.lower().split('__')
                    current = env_vars
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = self._convert_env_value(value)
                else:
                    env_vars[config_key.lower()] = self._convert_env_value(value)
        
        # Merge environment variables into config data
        return self._deep_merge(config_data, env_vars)
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Handle boolean values
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Handle numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Handle None/null
        if value.lower() in ('null', 'none', ''):
            return None
        
        # Return as string
        return value
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _config_to_dict(self, config: Config) -> Dict[str, Any]:
        """Convert Config object to dictionary for YAML serialization."""
        config_dict = config.dict(exclude_none=True)
        
        # Remove sensitive data from saved config
        if 'ai' in config_dict and 'api_key' in config_dict['ai']:
            if config_dict['ai']['api_key']:
                # Mask the API key in saved config
                config_dict['ai']['api_key'] = "***MASKED***"
        
        return config_dict
    
    def get_config(self) -> Config:
        """
        Get current configuration, loading if not already loaded.
        
        Returns:
            Current configuration
        """
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def update_config(self, **kwargs) -> Config:
        """
        Update configuration with new values.
        
        Args:
            **kwargs: Configuration values to update
            
        Returns:
            Updated configuration
        """
        current_config = self.get_config()
        current_dict = current_config.dict()
        
        # Deep merge the updates
        updated_dict = self._deep_merge(current_dict, kwargs)
        
        # Create new config object
        new_config = Config(**updated_dict)
        
        # Save and return
        self.save_config(new_config)
        return new_config
    
    def set_value(self, key_path: str, value: Any) -> Config:
        """
        Set a specific configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., "ai.api_key")
            value: Value to set
            
        Returns:
            Updated configuration
        """
        current_config = self.get_config()
        current_dict = current_config.dict()
        
        # Navigate to the target location
        keys = key_path.split('.')
        target = current_dict
        
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # Set the value
        target[keys[-1]] = value
        
        # Create new config object
        new_config = Config(**current_dict)
        
        # Save and return
        self.save_config(new_config)
        return new_config
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a specific configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path (e.g., "ai.api_key")
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        config = self.get_config()
        config_dict = config.dict()
        
        # Navigate to the target value
        keys = key_path.split('.')
        current = config_dict
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def validate_config(self) -> List[str]:
        """
        Validate current configuration and return any issues.
        
        Returns:
            List of validation issues
        """
        try:
            config = self.get_config()
            issues = []
            
            # Validate AI configuration
            ai_issues = config.validate_ai_config()
            issues.extend(ai_issues)
            
            # Check file paths exist
            cache_path = config.get_cache_path()
            if not cache_path.parent.exists():
                try:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create cache directory: {e}")
            
            # Validate output directory
            if config.output.save_to_file:
                output_path = Path(config.output.output_directory)
                if not output_path.exists():
                    try:
                        output_path.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        issues.append(f"Cannot create output directory: {e}")
            
            return issues
            
        except Exception as e:
            return [f"Configuration validation error: {e}"]
    
    def backup_config(self) -> Path:
        """
        Create a backup of the current configuration.
        
        Returns:
            Path to backup file
        """
        import datetime
        
        if not self.config_path.exists():
            raise FileNotFoundError("No configuration file to backup")
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.config_path.with_suffix(f".backup_{timestamp}.yaml")
        
        backup_path.write_text(self.config_path.read_text(encoding='utf-8'), encoding='utf-8')
        logger.info(f"Configuration backed up to: {backup_path}")
        
        return backup_path
    
    def reset_to_defaults(self) -> Config:
        """
        Reset configuration to defaults.
        
        Returns:
            Default configuration
        """
        # Backup current config if it exists
        if self.config_path.exists():
            self.backup_config()
        
        # Create default config
        self._create_default_config()
        
        # Reload and return
        return self.load_config(create_if_missing=False) 
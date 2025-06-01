import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import copy

class ConfigSource(ABC):
    """Abstract base class for configuration sources."""
    
    @abstractmethod
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: The configuration key to retrieve.
            default: Default value if key is not found.
            
        Returns:
            The configuration value or default if not found.
        """
        pass

class DictConfigSource(ConfigSource):
    """Configuration source that uses a dictionary."""
    
    def __init__(self, values: Dict[str, str]):
        """Initialize with a dictionary of values."""
        self.values = values or {}
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the dictionary."""
        # If the key exists but has a None value, return None
        if key in self.values and self.values[key] is None:
            return None
        # Otherwise return the value or default
        return self.values.get(key, default)

    def get_config(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        neo4j_config = {}
        for k, v in self.values.items():
            if k.startswith('NEO4J_'):
                # Map env var names to config keys
                key_map = {
                    'NEO4J_URI': 'uri',
                    'NEO4J_USER': 'user',
                    'NEO4J_PASSWORD': 'password',
                    'NEO4J_MAX_CONNECTION_LIFETIME': 'max_connection_lifetime',
                    'NEO4J_MAX_CONNECTION_POOL_SIZE': 'max_connection_pool_size',
                    'NEO4J_CONNECTION_TIMEOUT': 'connection_timeout',
                }
                config_key = key_map.get(k, k)
                neo4j_config[config_key] = v
        return {'neo4j': neo4j_config} if neo4j_config else {}

class EnvConfigSource(ConfigSource):
    """Configuration source that reads from environment variables."""
    
    def __init__(self, env: Optional[Dict[str, str]] = None):
        """Initialize the environment configuration source.
        
        Args:
            env: Dictionary of environment variables.
                 If not provided, uses os.environ.
        """
        self.env = env if env is not None else os.environ
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the environment.
        
        Args:
            key: The environment variable name.
            default: Default value if variable is not set.
            
        Returns:
            The environment variable value or default if not set.
        """
        return self.env.get(key, default)

    def get_config(self) -> Dict[str, Any]:
        # Only include relevant Neo4j keys
        neo4j_keys = [
            'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD',
            'NEO4J_MAX_CONNECTION_LIFETIME', 'NEO4J_MAX_CONNECTION_POOL_SIZE', 'NEO4J_CONNECTION_TIMEOUT'
        ]
        neo4j_config = {}
        for k in neo4j_keys:
            val = self.env.get(k)
            if val is not None:
                # Map env var names to config keys
                key_map = {
                    'NEO4J_URI': 'uri',
                    'NEO4J_USER': 'user',
                    'NEO4J_PASSWORD': 'password',
                    'NEO4J_MAX_CONNECTION_LIFETIME': 'max_connection_lifetime',
                    'NEO4J_MAX_CONNECTION_POOL_SIZE': 'max_connection_pool_size',
                    'NEO4J_CONNECTION_TIMEOUT': 'connection_timeout',
                }
                config_key = key_map.get(k, k)
                neo4j_config[config_key] = val
        return {'neo4j': neo4j_config} if neo4j_config else {}

class FileConfigSource(ConfigSource):
    """Configuration source that reads from YAML files."""
    
    def __init__(self, config_path: str):
        """Initialize the file configuration source.
        
        Args:
            config_path: Path to the configuration file.
        """
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Dictionary containing the configuration.
            
        Raises:
            ValueError: If the file is invalid YAML.
        """
        if not os.path.exists(self.config_path):
            return {}
            
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Error loading config file: {e}")
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the configuration file.
        
        Args:
            key: The configuration key to retrieve.
            default: Default value if key is not found.
            
        Returns:
            The configuration value or default if not found.
        """
        keys = key.split('.')
        value = self._config
        for k in keys:
            if not isinstance(value, dict):
                return default
            value = value.get(k, default)
            if value is None:
                return default
        return value

    def get_config(self) -> Dict[str, Any]:
        return self._config or {}

class Config:
    """Configuration manager for the genealogy mapper application."""
    
    # Make DEFAULT_CONFIG immutable by using a frozen dict
    _DEFAULT_CONFIG = {
        'neo4j': {
            'uri': 'bolt://localhost:7687',
            'user': 'neo4j',
            'max_connection_lifetime': 3600,
            'max_connection_pool_size': 50,
            'connection_timeout': 30
        }
    }
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get a deep copy of the default configuration."""
        return copy.deepcopy(cls._DEFAULT_CONFIG)
    
    def __init__(self, config_path: Optional[str] = None, config_source: Optional[ConfigSource] = None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Optional path to the configuration file.
                        If not provided, uses default location.
            config_source: Optional configuration source.
                          If not provided, uses environment variables.
        """
        self.config_path = config_path or str(Path(__file__).parent.parent.parent / 'config.yaml')
        self.config_source = config_source or EnvConfigSource()
        self.file_source = FileConfigSource(self.config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from all sources."""
        # Start with default configuration
        config = self.get_default_config()
        
        # Load from file sources
        if self.file_source:
            file_config = self.file_source._load_config()
            if file_config:
                # Merge file config into default config
                if 'neo4j' in file_config:
                    config['neo4j'].update(file_config['neo4j'])
        
        # Override with environment variables if set
        env_config = self.config_source.get_config()
        if env_config and 'neo4j' in env_config:
            config['neo4j'].update(env_config['neo4j'])
        
        # Ensure Neo4j password is set
        if not config.get("neo4j", {}).get("password"):
            raise ValueError("Neo4j password must be set in config file or NEO4J_PASSWORD environment variable")
        
        return config
    
    def get_neo4j_config(self) -> Dict[str, Any]:
        """Get Neo4j configuration.
        
        Returns:
            Dict containing Neo4j connection settings.
        """
        return self.config.get('neo4j', {})
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    @classmethod
    def create_default_config(cls, config_path: str) -> None:
        """Create a default configuration file.
        
        Args:
            config_path: Path where the config file should be created.
        """
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(cls.get_default_config(), f, default_flow_style=False) 
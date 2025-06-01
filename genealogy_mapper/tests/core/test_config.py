import os
import pytest
import yaml
from pathlib import Path
from typing import Dict, Any

from genealogy_mapper.core.config import Config, ConfigSource, EnvConfigSource, FileConfigSource, DictConfigSource

@pytest.fixture
def dict_config_source():
    """Create a dictionary-based configuration source."""
    def _create(values: Dict[str, str] = None):
        # Always return a new instance with a copy of the values
        return DictConfigSource(dict(values) if values else {})
    return _create

@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary directory for config files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return str(config_dir)

@pytest.fixture
def unique_config_path(temp_config_dir, request):
    """Create a unique config path for each test."""
    test_name = request.node.name
    return os.path.join(temp_config_dir, f"{test_name}.yaml")

@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        'neo4j': {
            'uri': 'bolt://custom:7687',
            'user': 'custom_user',
            'password': 'custom_password',
            'max_connection_lifetime': 1800,
            'max_connection_pool_size': 25,
            'connection_timeout': 15
        }
    }

class TestConfig:
    """Test suite for Config class."""

    def test_init_with_default_path(self, dict_config_source):
        """Test initialization with default config path."""
        config_source = dict_config_source({
            'NEO4J_URI': 'bolt://test:7687',
            'NEO4J_USER': 'test_user',
            'NEO4J_PASSWORD': 'test_password'
        })
        
        config = Config(config_source=config_source)
        assert config.config_path.endswith('config.yaml')
        assert config.config['neo4j']['uri'] == 'bolt://test:7687'
        assert config.config['neo4j']['user'] == 'test_user'

    def test_init_with_custom_path(self, unique_config_path, dict_config_source):
        """Test initialization with custom config path."""
        config_source = dict_config_source({
            'NEO4J_URI': 'bolt://test:7687',
            'NEO4J_USER': 'test_user',
            'NEO4J_PASSWORD': 'test_password'
        })
        
        config = Config(unique_config_path, config_source=config_source)
        assert config.config_path == unique_config_path

    def test_load_config_from_file(self, unique_config_path, sample_config, dict_config_source):
        """Test loading configuration from file."""
        config_source = dict_config_source({'NEO4J_PASSWORD': 'test_password'})
        
        with open(unique_config_path, 'w') as f:
            yaml.dump(sample_config, f)
            
        config = Config(unique_config_path, config_source=config_source)
        assert config.config['neo4j']['uri'] == 'bolt://custom:7687'
        assert config.config['neo4j']['user'] == 'custom_user'
        assert config.config['neo4j']['password'] == 'test_password'
        assert config.config['neo4j']['max_connection_lifetime'] == 1800

    def test_environment_variables_override_file(self, unique_config_path, sample_config, dict_config_source):
        """Test that environment variables override file settings."""
        config_source = dict_config_source({
            'NEO4J_URI': 'bolt://test:7687',
            'NEO4J_USER': 'test_user',
            'NEO4J_PASSWORD': 'test_password'
        })
        
        with open(unique_config_path, 'w') as f:
            yaml.dump(sample_config, f)
            
        config = Config(unique_config_path, config_source=config_source)
        assert config.config['neo4j']['uri'] == 'bolt://test:7687'
        assert config.config['neo4j']['user'] == 'test_user'
        assert config.config['neo4j']['password'] == 'test_password'

    def test_missing_password(self, unique_config_path, dict_config_source):
        """Test that missing password raises ValueError."""
        # Ensure no config file exists
        if os.path.exists(unique_config_path):
            os.remove(unique_config_path)
            
        config_source = dict_config_source({})  # Empty config source
        with pytest.raises(ValueError, match="Neo4j password must be set"):
            Config(unique_config_path, config_source=config_source)

    def test_get_neo4j_config(self, unique_config_path, dict_config_source):
        """Test getting Neo4j configuration."""
        # Ensure no config file exists
        if os.path.exists(unique_config_path):
            os.remove(unique_config_path)
            
        config_source = dict_config_source({'NEO4J_PASSWORD': 'test_password'})
        config = Config(unique_config_path, config_source=config_source)
        neo4j_config = config.get_neo4j_config()
        
        assert neo4j_config['uri'] == 'bolt://localhost:7687'
        assert neo4j_config['user'] == 'neo4j'
        assert neo4j_config['password'] == 'test_password'
        assert neo4j_config['max_connection_lifetime'] == 3600
        assert neo4j_config['max_connection_pool_size'] == 50
        assert neo4j_config['connection_timeout'] == 30

    def test_save_config(self, unique_config_path, dict_config_source):
        """Test saving configuration to file."""
        config_source = dict_config_source({
            'NEO4J_URI': 'bolt://test:7687',
            'NEO4J_USER': 'test_user',
            'NEO4J_PASSWORD': 'test_password'
        })
        
        config = Config(unique_config_path, config_source=config_source)
        config.save_config()
        
        assert os.path.exists(unique_config_path)
        with open(unique_config_path, 'r') as f:
            saved_config = yaml.safe_load(f)
            assert saved_config['neo4j']['uri'] == 'bolt://test:7687'
            assert saved_config['neo4j']['user'] == 'test_user'

    def test_create_default_config(self, unique_config_path):
        """Test creating default configuration file."""
        # Ensure no config file exists
        if os.path.exists(unique_config_path):
            os.remove(unique_config_path)
            
        Config.create_default_config(unique_config_path)
        assert os.path.exists(unique_config_path)
        with open(unique_config_path, 'r') as f:
            saved_config = yaml.safe_load(f)
            assert 'neo4j' in saved_config
            assert saved_config['neo4j']['uri'] == 'bolt://localhost:7687'
            assert saved_config['neo4j']['user'] == 'neo4j'

    def test_invalid_yaml_file(self, unique_config_path, dict_config_source):
        """Test handling of invalid YAML file."""
        config_source = dict_config_source({'NEO4J_PASSWORD': 'test_password'})
        
        with open(unique_config_path, 'w') as f:
            f.write('invalid: yaml: content:')
            
        with pytest.raises(ValueError, match="Error loading config file"):
            Config(unique_config_path, config_source=config_source)

    def test_missing_config_file(self, unique_config_path, dict_config_source):
        """Test handling of missing config file."""
        config_source = dict_config_source({
            'NEO4J_URI': 'bolt://test:7687',
            'NEO4J_USER': 'test_user',
            'NEO4J_PASSWORD': 'test_password'
        })
        
        # Ensure no config file exists
        if os.path.exists(unique_config_path):
            os.remove(unique_config_path)
            
        config = Config(unique_config_path, config_source=config_source)
        assert config.config['neo4j']['uri'] == 'bolt://test:7687'
        assert config.config['neo4j']['user'] == 'test_user'

    def test_partial_config_file(self, unique_config_path, dict_config_source):
        """Test handling of partial configuration in file."""
        # Ensure no config file exists
        if os.path.exists(unique_config_path):
            os.remove(unique_config_path)
            
        config_source = dict_config_source({'NEO4J_PASSWORD': 'test_password'})
        
        partial_config = {
            'neo4j': {
                'uri': 'bolt://partial:7687',
                'password': 'test_password'
            }
        }
        with open(unique_config_path, 'w') as f:
            yaml.dump(partial_config, f)
            
        config = Config(unique_config_path, config_source=config_source)
        assert config.config['neo4j']['uri'] == 'bolt://partial:7687'
        assert config.config['neo4j']['user'] == 'neo4j'  # Default value
        assert config.config['neo4j']['max_connection_lifetime'] == 3600  # Default value 
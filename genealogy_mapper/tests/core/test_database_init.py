import pytest
from genealogy_mapper.core.config import Config
from genealogy_mapper.core.db_init import init_db

def test_database_initialization(temp_config_file):
    """Test that the database can be initialized using a temporary config file."""
    config = Config(config_path=temp_config_file)
    assert init_db(config_path=temp_config_file) is True, "Database initialization failed" 
import pytest
from unittest.mock import patch, MagicMock
from genealogy_mapper.core.config import Config
from genealogy_mapper.core.db_init import init_db

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver and session."""
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    return mock_driver, mock_session

@patch('neo4j.GraphDatabase.driver')
def test_database_initialization(mock_driver, temp_config_file, mock_neo4j_driver):
    """Test that the database can be initialized using a temporary config file."""
    mock_driver.return_value = mock_neo4j_driver[0]
    mock_neo4j_driver[1].run.return_value.single.return_value = {"n": 1}
    
    config = Config(config_path=temp_config_file)
    assert init_db(config_path=temp_config_file) is True, "Database initialization failed" 
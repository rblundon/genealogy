import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from genealogy_mapper.core.db_init import DatabaseInitializer, init_db
from genealogy_mapper.core.config import DictConfigSource

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver and session."""
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    return mock_driver, mock_session

@pytest.fixture
def temp_db_dir(tmp_path):
    """Create a temporary database directory."""
    db_dir = tmp_path / "neo4j"
    db_dir.mkdir()
    return str(db_dir)

@pytest.fixture
def mock_config_source():
    """Create a mock configuration source."""
    return DictConfigSource({
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USER': 'neo4j',
        'NEO4J_PASSWORD': 'test_password'
    })

@pytest.fixture
def env_vars(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "test_password")
    yield
    # Cleanup is handled automatically by monkeypatch

class TestDatabaseInitializer:
    """Test suite for DatabaseInitializer class."""

    def test_init_with_default_directory(self, mock_config_source):
        """Test initialization with default directory."""
        initializer = DatabaseInitializer(config_source=mock_config_source)
        assert initializer.uri == 'bolt://localhost:7687'
        assert initializer.user == 'neo4j'
        assert initializer.password == 'test_password'
        assert 'data/neo4j' in initializer.db_directory

    def test_init_with_custom_directory(self, mock_config_source, temp_db_dir):
        """Test initialization with custom directory."""
        initializer = DatabaseInitializer(temp_db_dir, config_source=mock_config_source)
        assert initializer.db_directory == temp_db_dir

    def test_init_without_password(self, monkeypatch):
        """Test initialization without password environment variable."""
        # Ensure no environment variables are set
        monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
        config_source = DictConfigSource({})  # Empty config source
        with pytest.raises(ValueError, match="Neo4j password must be set in config file or NEO4J_PASSWORD environment variable"):
            DatabaseInitializer(config_source=config_source)

    @patch('neo4j.GraphDatabase.driver')
    def test_initialize_database_success(self, mock_driver, mock_config_source, mock_neo4j_driver):
        """Test successful database initialization."""
        mock_driver.return_value = mock_neo4j_driver[0]
        initializer = DatabaseInitializer(config_source=mock_config_source)
        assert initializer.initialize_database() is True

    @patch('neo4j.GraphDatabase.driver')
    def test_initialize_database_connection_error(self, mock_driver, mock_config_source):
        """Test database initialization with connection error."""
        mock_driver.side_effect = Exception("Connection failed")
        initializer = DatabaseInitializer(config_source=mock_config_source)
        assert initializer.initialize_database() is False

    @patch('neo4j.GraphDatabase.driver')
    def test_create_constraints(self, mock_driver, mock_config_source, mock_neo4j_driver):
        """Test constraint creation."""
        mock_driver.return_value = mock_neo4j_driver[0]
        initializer = DatabaseInitializer(config_source=mock_config_source)
        initializer._create_constraints(mock_neo4j_driver[1])
        
        # Verify that all constraints were created
        assert mock_neo4j_driver[1].run.call_count > 0
        calls = [call[0][0] for call in mock_neo4j_driver[1].run.call_args_list]
        assert any("CREATE CONSTRAINT indi_id" in call for call in calls)
        assert any("CREATE CONSTRAINT fam_id" in call for call in calls)
        assert any("CREATE CONSTRAINT sour_id" in call for call in calls)

    @patch('neo4j.GraphDatabase.driver')
    def test_create_indexes(self, mock_driver, mock_config_source, mock_neo4j_driver):
        """Test index creation."""
        mock_driver.return_value = mock_neo4j_driver[0]
        initializer = DatabaseInitializer(config_source=mock_config_source)
        initializer._create_indexes(mock_neo4j_driver[1])
        
        # Verify that all indexes were created
        assert mock_neo4j_driver[1].run.call_count > 0
        calls = [call[0][0] for call in mock_neo4j_driver[1].run.call_args_list]
        assert any("CREATE INDEX indi_name" in call for call in calls)
        assert any("CREATE INDEX fam_marriage_date" in call for call in calls)
        assert any("CREATE INDEX sour_author" in call for call in calls)

    @patch('neo4j.GraphDatabase.driver')
    def test_create_metadata(self, mock_driver, mock_config_source, mock_neo4j_driver):
        """Test metadata node creation."""
        mock_driver.return_value = mock_neo4j_driver[0]
        initializer = DatabaseInitializer(config_source=mock_config_source)
        initializer._create_metadata(mock_neo4j_driver[1])
        
        # Verify metadata node creation
        mock_neo4j_driver[1].run.assert_called_once()
        call_args = mock_neo4j_driver[1].run.call_args[1]
        assert call_args['metadata']['gedcom_version'] == '7.0'
        assert 'created_at' in call_args['metadata']
        assert 'last_updated' in call_args['metadata']

@patch('neo4j.GraphDatabase.driver')
def test_init_db_success(mock_driver, mock_config_source, temp_db_dir, mock_neo4j_driver):
    """Test successful init_db function call."""
    mock_driver.return_value = mock_neo4j_driver[0]
    result = init_db(temp_db_dir, config_source=mock_config_source)
    assert result is True

@patch('neo4j.GraphDatabase.driver')
def test_init_db_failure(mock_driver, mock_config_source):
    """Test failed init_db function call."""
    mock_driver.side_effect = Exception("Connection failed")
    result = init_db(config_source=mock_config_source)
    assert result is False

@patch('neo4j.GraphDatabase.driver')
def test_init_with_env_vars(mock_driver, env_vars, mock_neo4j_driver):
    """Test initialization with environment variables."""
    mock_driver.return_value = mock_neo4j_driver[0]
    # Initialize with environment variables
    initializer = DatabaseInitializer()
    
    # Verify configuration
    config = initializer.config.get_neo4j_config()
    assert config["uri"] == "bolt://localhost:7687"
    assert config["user"] == "neo4j"
    assert config["password"] == "test_password"

def test_init_without_password(monkeypatch):
    """Test initialization without password environment variable."""
    # Ensure no environment variables are set
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
    with pytest.raises(ValueError, match="Neo4j password must be set in config file or NEO4J_PASSWORD environment variable"):
        DatabaseInitializer() 
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import yaml

from genealogy_mapper.core.db_init import init_db
from genealogy_mapper.core.config import DictConfigSource

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver and session."""
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    return mock_driver, mock_session

@pytest.fixture
def mock_config_source():
    """Create a mock configuration source."""
    return DictConfigSource({
        'NEO4J_URI': 'bolt://localhost:7687',
        'NEO4J_USER': 'neo4j',
        'NEO4J_PASSWORD': 'test_password'
    })

@pytest.fixture
def temp_config_file():
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            'neo4j': {
                'uri': 'bolt://localhost:7687',
                'user': 'neo4j',
                'password': 'test_password'
            }
        }, f)
    yield f.name
    Path(f.name).unlink(missing_ok=True)

@patch('neo4j.GraphDatabase.driver')
def test_constraints_exist(mock_driver, mock_neo4j_driver, temp_config_file):
    """Test that all required constraints exist."""
    mock_driver.return_value = mock_neo4j_driver[0]
    assert init_db(config_path=temp_config_file) is True
    
    # Verify that all constraints were created
    calls = [call[0][0] for call in mock_neo4j_driver[1].run.call_args_list]
    assert any("CREATE CONSTRAINT indi_id" in call for call in calls)
    assert any("CREATE CONSTRAINT fam_id" in call for call in calls)
    assert any("CREATE CONSTRAINT sour_id" in call for call in calls)
    assert any("CREATE CONSTRAINT repo_id" in call for call in calls)
    assert any("CREATE CONSTRAINT note_id" in call for call in calls)
    assert any("CREATE CONSTRAINT media_id" in call for call in calls)
    assert any("CREATE CONSTRAINT subn_id" in call for call in calls)

@patch('neo4j.GraphDatabase.driver')
def test_indexes_exist(mock_driver, mock_neo4j_driver, temp_config_file):
    """Test that all required indexes exist."""
    mock_driver.return_value = mock_neo4j_driver[0]
    assert init_db(config_path=temp_config_file) is True
    
    # Verify that all indexes were created
    calls = [call[0][0] for call in mock_neo4j_driver[1].run.call_args_list]
    assert any("CREATE INDEX indi_name" in call for call in calls)
    assert any("CREATE INDEX indi_birth_date" in call for call in calls)
    assert any("CREATE INDEX indi_death_date" in call for call in calls)
    assert any("CREATE INDEX fam_marriage_date" in call for call in calls)
    assert any("CREATE INDEX sour_author" in call for call in calls)
    assert any("CREATE INDEX sour_publication" in call for call in calls) 
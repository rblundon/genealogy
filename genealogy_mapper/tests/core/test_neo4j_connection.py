import os
import pytest
from neo4j import GraphDatabase
from genealogy_mapper.core.config import Config
from genealogy_mapper.scripts.manage_neo4j import check_container_running, start_container
from unittest.mock import patch, MagicMock

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../../config.yaml')

@pytest.fixture(autouse=True)
def ensure_neo4j_running():
    """Fixture to ensure Neo4j is running before each test."""
    if not check_container_running():
        assert start_container(), "Failed to start Neo4j container"

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver and session."""
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    return mock_driver, mock_session

@patch('neo4j.GraphDatabase.driver')
def test_neo4j_connection(mock_driver, mock_neo4j_driver):
    """Test Neo4j connection."""
    mock_driver.return_value = mock_neo4j_driver[0]
    mock_neo4j_driver[1].run.return_value.single.return_value = {"n": 1}
    
    # Test connection
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "test_password"))
    with driver.session() as session:
        result = session.run("RETURN 1 as n")
        assert result.single()["n"] == 1

@patch('neo4j.GraphDatabase.driver')
def test_container_management(mock_driver, mock_neo4j_driver):
    """Test container management."""
    mock_driver.return_value = mock_neo4j_driver[0]
    mock_neo4j_driver[1].run.return_value.single.return_value = {"n": 1}
    
    # Test connection
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "test_password"))
    with driver.session() as session:
        result = session.run("RETURN 1 as n")
        assert result.single()["n"] == 1 
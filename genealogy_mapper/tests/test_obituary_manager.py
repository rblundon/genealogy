import pytest
from unittest.mock import Mock, patch
from genealogy_mapper.core.obituary_manager import ObituaryManager
from neo4j import GraphDatabase

@pytest.fixture
def mock_neo4j_driver():
    with patch('genealogy_mapper.core.obituary_manager.GraphDatabase') as mock_db:
        mock_session = Mock()
        mock_db.driver.return_value.session.return_value.__enter__.return_value = mock_session
        yield mock_db

@pytest.fixture
def mock_requests_session():
    with patch('genealogy_mapper.core.obituary_manager.requests.Session') as mock_session:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_session.return_value.get.return_value = mock_response
        yield mock_session

@pytest.fixture
def obituary_manager(mock_neo4j_driver, mock_requests_session):
    return ObituaryManager()

def test_add_obituary_url_success(obituary_manager, mock_neo4j_driver, mock_requests_session):
    """Test successful addition of a new obituary URL."""
    url = "https://www.legacy.com/us/obituaries/jsonline/name/test-obituary"
    source = "legacy.com"
    
    # Mock Neo4j response
    mock_session = mock_neo4j_driver.driver.return_value.session.return_value.__enter__.return_value
    mock_session.run.return_value.single.return_value = {"o": {"url": url}}
    
    # Test adding new obituary
    result = obituary_manager.add_obituary_url(url, source)
    assert result is True
    
    # Verify Neo4j query was called with correct parameters
    mock_session.run.assert_called()
    call_args = mock_session.run.call_args[1]
    assert call_args['url'] == url
    assert call_args['source'] == source
    assert 'id' in call_args
    assert call_args['newspaper'] == "Jsonline"
    assert call_args['location'] == "Name"

def test_add_obituary_url_exists(obituary_manager, mock_neo4j_driver, mock_requests_session):
    """Test adding an existing obituary URL without force flag."""
    url = "https://www.legacy.com/us/obituaries/jsonline/name/test-obituary"
    source = "legacy.com"
    
    # Mock Neo4j response to simulate existing URL
    mock_session = mock_neo4j_driver.driver.return_value.session.return_value.__enter__.return_value
    mock_session.run.return_value.single.return_value = {"o": {"url": url}}
    
    # Test adding existing obituary without force
    result = obituary_manager.add_obituary_url(url, source, force_rescrape=False)
    assert result is False

def test_add_obituary_url_force_rescrape(obituary_manager, mock_neo4j_driver, mock_requests_session):
    """Test force rescraping an existing obituary URL."""
    url = "https://www.legacy.com/us/obituaries/jsonline/name/test-obituary"
    source = "legacy.com"
    
    # Mock Neo4j response
    mock_session = mock_neo4j_driver.driver.return_value.session.return_value.__enter__.return_value
    mock_session.run.return_value.single.return_value = {"o": {"url": url}}
    
    # Test force rescraping
    result = obituary_manager.add_obituary_url(url, source, force_rescrape=True)
    assert result is True
    
    # Verify Neo4j query was called with correct parameters
    mock_session.run.assert_called()
    call_args = mock_session.run.call_args[1]
    assert call_args['url'] == url
    assert call_args['source'] == source

def test_add_obituary_url_dry_run(obituary_manager, mock_neo4j_driver, mock_requests_session):
    """Test dry run mode for adding obituary URL."""
    url = "https://www.legacy.com/us/obituaries/jsonline/name/test-obituary"
    source = "legacy.com"
    
    # Test dry run
    result = obituary_manager.add_obituary_url(url, source, dry_run=True)
    assert result is True
    
    # Verify Neo4j was not called
    mock_session = mock_neo4j_driver.driver.return_value.session.return_value.__enter__.return_value
    mock_session.run.assert_not_called()

def test_add_obituary_url_invalid(obituary_manager, mock_neo4j_driver, mock_requests_session):
    """Test adding an invalid URL."""
    url = "invalid-url"
    source = "legacy.com"
    
    # Test invalid URL
    result = obituary_manager.add_obituary_url(url, source)
    assert result is False
    
    # Verify Neo4j was not called
    mock_session = mock_neo4j_driver.driver.return_value.session.return_value.__enter__.return_value
    mock_session.run.assert_not_called()

def test_add_obituary_url_404(obituary_manager, mock_neo4j_driver, mock_requests_session):
    """Test adding a URL that returns 404."""
    url = "https://www.legacy.com/us/obituaries/jsonline/name/test-obituary"
    source = "legacy.com"
    
    # Mock 404 response
    mock_response = Mock()
    mock_response.status_code = 404
    mock_requests_session.return_value.get.return_value = mock_response
    
    # Test 404 URL
    result = obituary_manager.add_obituary_url(url, source)
    assert result is False
    
    # Verify Neo4j was not called
    mock_session = mock_neo4j_driver.driver.return_value.session.return_value.__enter__.return_value
    mock_session.run.assert_not_called()

def test_add_obituary_url_network_error(obituary_manager, mock_neo4j_driver, mock_requests_session):
    """Test adding a URL with network error."""
    url = "https://www.legacy.com/us/obituaries/jsonline/name/test-obituary"
    source = "legacy.com"
    
    # Mock network error
    mock_requests_session.return_value.get.side_effect = Exception("Network error")
    
    # Test network error
    result = obituary_manager.add_obituary_url(url, source)
    assert result is False
    
    # Verify Neo4j was not called
    mock_session = mock_neo4j_driver.driver.return_value.session.return_value.__enter__.return_value
    mock_session.run.assert_not_called()

def test_add_obituary_url_neo4j_error(obituary_manager, mock_neo4j_driver, mock_requests_session):
    """Test Neo4j error when adding obituary URL."""
    url = "https://www.legacy.com/us/obituaries/jsonline/name/test-obituary"
    source = "legacy.com"
    
    # Mock Neo4j error
    mock_session = mock_neo4j_driver.driver.return_value.session.return_value.__enter__.return_value
    mock_session.run.side_effect = Exception("Neo4j error")
    
    # Test Neo4j error
    result = obituary_manager.add_obituary_url(url, source)
    assert result is False 
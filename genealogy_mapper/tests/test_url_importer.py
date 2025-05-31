import json
import os
import pytest
from datetime import datetime
from unittest.mock import patch, Mock, MagicMock
from genealogy_mapper.core.url_importer import URLImporter
from genealogy_mapper.core.scrapers.factory import ScraperFactory
from genealogy_mapper.core.scrapers.legacy_scraper import LegacyScraper

@pytest.fixture
def temp_json_file(tmp_path):
    """Create a temporary JSON file for testing."""
    json_file = tmp_path / "test_obituary_urls.json"
    initial_data = {
        "urls": [],
        "last_updated": datetime.now().isoformat()
    }
    with open(json_file, 'w') as f:
        json.dump(initial_data, f)
    return str(json_file)

@pytest.fixture
def importer(temp_json_file):
    """Create a URLImporter instance with a temporary JSON file."""
    return URLImporter(json_path=temp_json_file)

def test_validate_url(importer):
    """Test URL validation."""
    # Test valid URL
    valid_url = "https://www.legacy.com/us/obituaries/jsonline/name/maxine-kaczmarowski-obituary?id=3326788"
    assert importer.validate_url(valid_url) is True
    
    # Test invalid URL
    invalid_url = "not-a-url"
    assert importer.validate_url(invalid_url) is False
    
    # Test non-existent URL
    non_existent_url = "https://www.legacy.com/us/obituaries/nonexistent"
    assert importer.validate_url(non_existent_url) is False

def test_import_url(importer):
    """Test URL importing."""
    url = "https://www.legacy.com/us/obituaries/jsonline/name/maxine-kaczmarowski-obituary?id=3326788"
    
    # Test importing new URL
    assert importer.import_url(url) is True
    
    # Test importing duplicate URL
    assert importer.import_url(url) is True
    
    # Verify URL was added to JSON file
    with open(importer.json_path, 'r') as f:
        data = json.load(f)
        assert len(data["urls"]) == 1
        assert data["urls"][0]["url"] == url
        assert data["urls"][0]["status"] == "pending"

def test_get_unprocessed_urls(importer):
    """Test getting unprocessed URLs."""
    # Add a completed URL
    url = "https://www.legacy.com/us/obituaries/jsonline/name/maxine-kaczmarowski-obituary?id=3326788"
    importer.import_url(url)
    importer.update_url_status(url, "completed")
    
    # Test without force_rescrape
    assert len(importer.get_unprocessed_urls()) == 0
    
    # Test with force_rescrape
    importer.force_rescrape = True
    assert len(importer.get_unprocessed_urls()) == 1

def test_update_url_status(importer):
    """Test updating URL status."""
    url = "https://www.legacy.com/us/obituaries/jsonline/name/maxine-kaczmarowski-obituary?id=3326788"
    importer.import_url(url)
    
    # Test updating status
    assert importer.update_url_status(url, "completed") is True
    
    # Test updating with text and metadata
    text = "Test obituary text"
    metadata = {"name": "Test Name", "location": "Test Location"}
    assert importer.update_url_status(url, "completed", text, metadata) is True
    
    # Verify updates in JSON file
    with open(importer.json_path, 'r') as f:
        data = json.load(f)
        assert data["urls"][0]["status"] == "completed"
        assert data["urls"][0]["extracted_text"] == text
        assert data["urls"][0]["metadata"] == metadata

def test_process_pending_urls(tmp_path):
    """Test processing pending URLs."""
    # Create test URLs file
    urls_file = tmp_path / "obituary_urls.json"
    test_data = {
        "urls": [
            {
                "url": "https://www.legacy.com/us/obituaries/jsonline/name/maxine-kaczmarowski-obituary?id=3326788",
                "status": "pending",
                "metadata": {}
            }
        ]
    }
    urls_file.write_text(json.dumps(test_data))

    # Initialize importer with test file
    importer = URLImporter(json_path=urls_file)

    # Mock the scraper factory and LegacyScraper
    with patch('genealogy_mapper.core.url_importer.ScraperFactory.create_scraper') as mock_create_scraper:
        mock_scraper = MagicMock()
        mock_scraper.extract.return_value = {
            "text": "Sample obituary text",
            "metadata": {
                "name": "Maxine Kaczmarowski",
                "birth_date": "1940-01-01",
                "death_date": "2020-01-01",
                "location": "Milwaukee, WI"
            }
        }
        mock_create_scraper.return_value = mock_scraper

        # Process URLs
        results = importer.process_pending_urls()

        # Verify results
        assert len(results) > 0
        assert results[0]["url"] == test_data["urls"][0]["url"]
        assert results[0]["text"] == "Sample obituary text"
        assert results[0]["metadata"]["name"] == "Maxine Kaczmarowski"

        # Verify file was updated
        updated_data = json.loads(urls_file.read_text())
        assert updated_data["urls"][0]["status"] == "completed"
        assert updated_data["urls"][0]["extracted_text"] == "Sample obituary text"
        assert updated_data["urls"][0]["metadata"]["name"] == "Maxine Kaczmarowski" 
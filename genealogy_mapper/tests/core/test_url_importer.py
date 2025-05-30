import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from genealogy_mapper.core.url_importer import URLImporter

@pytest.fixture
def temp_json_path(tmp_path):
    """Create a temporary JSON file path."""
    return tmp_path / "test_obituaries.json"

@pytest.fixture
def sample_url():
    """Return a sample valid URL."""
    return "https://www.legacy.com/us/obituaries/example"

@pytest.fixture
def sample_data():
    """Return sample JSON data."""
    return {
        "version": "2.0",
        "last_updated": "2024-03-19",
        "obituaries": []
    }

class TestURLImporter:
    def test_init_creates_file_if_not_exists(self, temp_json_path):
        """Test that initialization creates a new file if it doesn't exist."""
        importer = URLImporter(str(temp_json_path))
        assert temp_json_path.exists()
        
        with open(temp_json_path, 'r') as f:
            data = json.load(f)
            assert "version" in data
            assert "urls" in data
            assert data["version"] == "1.0"
            assert data["urls"] == []

    def test_validate_url_valid(self, sample_url):
        """Test URL validation with a valid URL."""
        with patch('requests.Session.get') as mock_get:
            mock_response = mock_get.return_value
            mock_response.status_code = 200
            mock_response.text = "This is an obituary page"
            
            importer = URLImporter()
            assert importer.validate_url(sample_url) is True

    def test_validate_url_invalid_format(self):
        """Test URL validation with an invalid URL format."""
        importer = URLImporter()
        assert importer.validate_url("not-a-url") is False

    def test_validate_url_inaccessible(self, sample_url):
        """Test URL validation with an inaccessible URL."""
        with patch('requests.Session.get') as mock_get:
            mock_response = mock_get.return_value
            mock_response.status_code = 404
            
            importer = URLImporter()
            assert importer.validate_url(sample_url) is False

    def test_validate_url_connection_error(self, sample_url):
        """Test URL validation with a connection error."""
        with patch('requests.Session.get') as mock_get:
            mock_get.side_effect = Exception("Connection error")
            
            importer = URLImporter()
            assert importer.validate_url(sample_url) is False

    def test_import_url_success(self, temp_json_path, sample_url):
        """Test successful URL import."""
        # Create initial empty file
        with open(temp_json_path, 'w') as f:
            json.dump({"urls": [], "version": "1.0"}, f)
        
        with patch('requests.Session.get') as mock_get:
            mock_response = mock_get.return_value
            mock_response.status_code = 200
            mock_response.text = "This is an obituary page"
            
            importer = URLImporter(str(temp_json_path))
            
            # Test the import
            assert importer.import_url(sample_url) is True
            
            # Verify the file contents
            with open(temp_json_path, 'r') as f:
                data = json.load(f)
                assert len(data["urls"]) == 1
                assert data["urls"][0]["url"] == sample_url
                assert "imported_at" in data["urls"][0]

    def test_import_url_invalid(self, temp_json_path):
        """Test importing an invalid URL."""
        importer = URLImporter(str(temp_json_path))
        assert importer.import_url("not-a-url") is False

    def test_json_file_corruption(self, temp_json_path):
        """Test handling of corrupted JSON file."""
        # Create a corrupted JSON file
        with open(temp_json_path, 'w') as f:
            f.write("invalid json content")
        
        importer = URLImporter(str(temp_json_path))
        urls = importer._load_urls()
        assert urls == []  # Should return empty list for corrupted file

    def test_import_url_duplicate(self, tmp_path):
        """Test importing a URL that already exists."""
        # Create initial JSON file with one URL
        json_path = tmp_path / "obituaries.json"
        initial_data = {
            "urls": [{
                "url": "https://example.com/obituary/1",
                "imported_at": "2024-03-19T00:00:00"
            }],
            "version": "1.0"
        }
        
        with open(json_path, 'w') as f:
            json.dump(initial_data, f)
        
        importer = URLImporter(str(json_path))
        
        # Try to import the same URL again
        result = importer.import_url("https://example.com/obituary/1")
        
        # Should return True for duplicate (matching CLI logic)
        assert result is True
        
        # Verify no new URL was added
        with open(json_path, 'r') as f:
            data = json.load(f)
            assert len(data["urls"]) == 1 
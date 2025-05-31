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
        "urls": [],
        "last_updated": "2024-03-19T00:00:00"
    }

class TestURLImporter:
    def test_init_creates_file_if_not_exists(self, temp_json_path):
        """Test that initialization creates a new file if it doesn't exist."""
        importer = URLImporter(str(temp_json_path))
        assert temp_json_path.exists()
        
        with open(temp_json_path, 'r') as f:
            data = json.load(f)
            assert "urls" in data
            assert "last_updated" in data
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
            json.dump({"urls": [], "last_updated": "2024-03-19T00:00:00"}, f)
        
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
                assert data["urls"][0]["status"] == "pending"
                assert data["urls"][0]["extracted_text"] is None
                assert data["urls"][0]["metadata"] is None

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
        data = importer._load_json()
        assert data["urls"] == []  # Should return empty list for corrupted file

    def test_import_url_duplicate(self, tmp_path):
        """Test importing a URL that already exists."""
        # Create initial JSON file with one URL
        json_path = tmp_path / "obituaries.json"
        initial_data = {
            "urls": [{
                "url": "https://example.com/obituary/1",
                "imported_at": "2024-03-19T00:00:00",
                "status": "pending",
                "extracted_text": None,
                "metadata": None
            }],
            "last_updated": "2024-03-19T00:00:00"
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

    def test_get_pending_urls(self, temp_json_path):
        """Test getting pending URLs."""
        # Create initial data with mixed status URLs
        initial_data = {
            "urls": [
                {
                    "url": "https://example.com/obituary/1",
                    "imported_at": "2024-03-19T00:00:00",
                    "status": "pending",
                    "extracted_text": None,
                    "metadata": None
                },
                {
                    "url": "https://example.com/obituary/2",
                    "imported_at": "2024-03-19T00:00:00",
                    "status": "completed",
                    "extracted_text": "Some text",
                    "metadata": {"name": "John Doe"}
                }
            ],
            "last_updated": "2024-03-19T00:00:00"
        }
        
        with open(temp_json_path, 'w') as f:
            json.dump(initial_data, f)
        
        importer = URLImporter(str(temp_json_path))
        pending_urls = importer.get_pending_urls()
        
        assert len(pending_urls) == 1
        assert pending_urls[0]["url"] == "https://example.com/obituary/1"
        assert pending_urls[0]["status"] == "pending"

    def test_update_url_status(self, temp_json_path):
        """Test updating URL status and data."""
        # Create initial data
        initial_data = {
            "urls": [{
                "url": "https://example.com/obituary/1",
                "imported_at": "2024-03-19T00:00:00",
                "status": "pending",
                "extracted_text": None,
                "metadata": None
            }],
            "last_updated": "2024-03-19T00:00:00"
        }
        
        with open(temp_json_path, 'w') as f:
            json.dump(initial_data, f)
        
        importer = URLImporter(str(temp_json_path))
        
        # Update status and data
        result = importer.update_url_status(
            url="https://example.com/obituary/1",
            status="completed",
            extracted_text="Obituary text",
            metadata={"name": "John Doe"}
        )
        
        assert result is True
        
        # Verify the update
        with open(temp_json_path, 'r') as f:
            data = json.load(f)
            assert data["urls"][0]["status"] == "completed"
            assert data["urls"][0]["extracted_text"] == "Obituary text"
            assert data["urls"][0]["metadata"] == {"name": "John Doe"}

    def test_process_pending_urls(self, temp_json_path):
        """Test processing pending URLs."""
        # Create initial data with pending URL
        initial_data = {
            "urls": [{
                "url": "https://example.com/obituary/1",
                "imported_at": "2024-03-19T00:00:00",
                "status": "pending",
                "extracted_text": None,
                "metadata": None
            }],
            "last_updated": "2024-03-19T00:00:00"
        }
        
        with open(temp_json_path, 'w') as f:
            json.dump(initial_data, f)
        
        importer = URLImporter(str(temp_json_path))
        
        # Mock the scraper's extract_legacy_com method
        with patch('genealogy_mapper.core.obituary_scraper.ObituaryScraper.extract_legacy_com') as mock_extract:
            mock_extract.return_value = {
                "text": "Obituary text",
                "metadata": {"name": "John Doe"}
            }
            
            processed = importer.process_pending_urls()
            
            assert len(processed) == 1
            assert processed[0]["url"] == "https://example.com/obituary/1"
            assert processed[0]["text"] == "Obituary text"
            assert processed[0]["metadata"] == {"name": "John Doe"}
            
            # Verify the update in the file
            with open(temp_json_path, 'r') as f:
                data = json.load(f)
                assert data["urls"][0]["status"] == "completed"
                assert data["urls"][0]["extracted_text"] == "Obituary text"
                assert data["urls"][0]["metadata"] == {"name": "John Doe"} 
import pytest
from unittest.mock import patch, Mock
from bs4 import BeautifulSoup
from genealogy_mapper.core.obituary_scraper import ObituaryScraper

@pytest.fixture
def sample_html():
    """Return a sample HTML page for testing."""
    return """
    <html>
        <body>
            <h1 class="obit-name">John Doe</h1>
            <div class="obit-dates">January 1, 1950 - December 31, 2023</div>
            <div class="obit-source">Milwaukee Journal Sentinel - Milwaukee, WI</div>
            <div class="obit-date">Published on January 2, 2024</div>
            <article>
                <p>John Doe, age 73, passed away peacefully on December 31, 2023.</p>
                <p>He was born in Milwaukee, Wisconsin to Jane and James Doe.</p>
                <p>John is survived by his loving wife Mary and their children.</p>
            </article>
        </body>
    </html>
    """

@pytest.fixture
def scraper():
    """Return a new ObituaryScraper instance."""
    return ObituaryScraper()

class TestObituaryScraper:
    def test_extract_legacy_com_success(self, scraper, sample_html):
        """Test successful extraction from Legacy.com."""
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.text = sample_html
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = scraper.extract_legacy_com("https://www.legacy.com/obituary/123")
            
            assert result is not None
            assert "text" in result
            assert "metadata" in result
            
            # Check text content
            assert "John Doe" in result["text"]
            assert "passed away peacefully" in result["text"]
            
            # Check metadata
            metadata = result["metadata"]
            assert metadata["name"] == "John Doe"
            assert metadata["birth_date"] == "January 1, 1950"
            assert metadata["death_date"] == "December 31, 2023"
            assert metadata["newspaper"] == "Milwaukee Journal Sentinel"
            assert metadata["location"] == "Milwaukee, WI"
            assert metadata["publication_date"] == "Published on January 2, 2024"
    
    def test_extract_legacy_com_connection_error(self, scraper):
        """Test handling of connection errors."""
        with patch('requests.Session.get') as mock_get:
            mock_get.side_effect = Exception("Connection error")
            
            result = scraper.extract_legacy_com("https://www.legacy.com/obituary/123")
            assert result is None
    
    def test_extract_legacy_com_missing_text(self, scraper):
        """Test handling of pages with missing obituary text."""
        html = "<html><body><h1>No obituary here</h1></body></html>"
        
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.text = html
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = scraper.extract_legacy_com("https://www.legacy.com/obituary/123")
            assert result is None
    
    def test_extract_legacy_metadata_partial(self, scraper):
        """Test extraction with partial metadata."""
        html = """
        <html>
            <body>
                <h1 class="obit-name">Jane Smith</h1>
                <article>
                    <p>Some obituary text here.</p>
                </article>
            </body>
        </html>
        """
        
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.text = html
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = scraper.extract_legacy_com("https://www.legacy.com/obituary/123")
            
            assert result is not None
            metadata = result["metadata"]
            assert metadata["name"] == "Jane Smith"
            assert metadata["newspaper"] == "Unknown"
            assert metadata["location"] == "Unknown"
            assert metadata["birth_date"] == "Unknown"
            assert metadata["death_date"] == "Unknown" 
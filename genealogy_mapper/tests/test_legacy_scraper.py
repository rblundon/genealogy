import pytest
from bs4 import BeautifulSoup
from genealogy_mapper.core.scrapers.legacy_scraper import LegacyScraper

@pytest.fixture
def sample_html():
    """Return a sample HTML page with JSON-LD data."""
    return """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "description": "Test obituary text for Maxine Kaczmarowski",
                "name": "Maxine Kaczmarowski",
                "datePublished": "2018-05-27T00:00:00.000Z",
                "publisher": {
                    "name": "Legacy"
                }
            }
            </script>
        </head>
        <body>
            <article class="obituary">
                <h1>Maxine Kaczmarowski</h1>
                <div class="obituary-text">
                    Test obituary text for Maxine Kaczmarowski
                </div>
            </article>
        </body>
    </html>
    """

@pytest.fixture
def scraper():
    """Create a LegacyScraper instance."""
    return LegacyScraper()

def test_extract_text_from_json_ld(scraper, sample_html):
    """Test extracting text from JSON-LD data."""
    soup = BeautifulSoup(sample_html, 'html.parser')
    text = scraper._extract_text(soup)
    assert text == "Test obituary text for Maxine Kaczmarowski"

def test_extract_metadata_from_json_ld(scraper, sample_html):
    """Test extracting metadata from JSON-LD data."""
    soup = BeautifulSoup(sample_html, 'html.parser')
    metadata = scraper._extract_metadata(soup)
    assert metadata["name"] == "Maxine Kaczmarowski"
    assert metadata["newspaper"] == "Legacy"
    assert metadata["publication_date"] == "2018-05-27T00:00:00.000Z"

def test_extract_text_from_html(scraper, sample_html):
    """Test extracting text from HTML when JSON-LD is not available."""
    # Remove JSON-LD data
    soup = BeautifulSoup(sample_html, 'html.parser')
    soup.find('script').decompose()
    
    text = scraper._extract_text(soup)
    assert text == "Test obituary text for Maxine Kaczmarowski"

def test_extract_metadata_from_html(scraper, sample_html):
    """Test extracting metadata from HTML when JSON-LD is not available."""
    # Remove JSON-LD data
    soup = BeautifulSoup(sample_html, 'html.parser')
    soup.find('script').decompose()
    
    metadata = scraper._extract_metadata(soup)
    assert metadata["name"] == "Maxine Kaczmarowski"
    assert metadata["newspaper"] == "Unknown"
    assert metadata["location"] == "Unknown"

def test_extract_with_invalid_html(scraper):
    """Test handling of invalid HTML."""
    soup = BeautifulSoup("<html><body>Invalid content</body></html>", 'html.parser')
    text = scraper._extract_text(soup)
    metadata = scraper._extract_metadata(soup)
    
    assert text is None
    assert metadata["name"] == "Unknown"
    assert metadata["newspaper"] == "Unknown"
    assert metadata["location"] == "Unknown" 
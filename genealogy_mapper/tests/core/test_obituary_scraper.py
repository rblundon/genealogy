import pytest
from genealogy_mapper.core.scrapers.legacy_scraper import LegacyScraper
from genealogy_mapper.core.scrapers.factory import ScraperFactory
from unittest.mock import patch

class TestLegacyScraper:
    """Test the Legacy.com scraper."""
    
    @pytest.fixture
    def scraper(self):
        """Create a LegacyScraper instance."""
        return LegacyScraper()
    
    def test_extract_legacy_com_success(self):
        """Test successful extraction from Legacy.com."""
        url = "https://www.legacy.com/us/obituaries/jsonline/name/maxine-kaczmarowski-obituary?id=3326788"
        
        # Mock the Selenium WebDriver
        with patch('selenium.webdriver.Chrome') as mock_driver:
            # Set up the mock driver
            mock_driver.return_value.page_source = """
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
            
            # Create the scraper and extract
            scraper = LegacyScraper()
            result = scraper.extract(url)
            
            # Verify the result
            assert result is not None
            assert result["text"] == "Test obituary text for Maxine Kaczmarowski"
            assert result["metadata"]["name"] == "Maxine Kaczmarowski"
            assert result["metadata"]["newspaper"] == "Legacy"

class TestScraperFactory:
    """Test the scraper factory."""
    
    def test_create_legacy_scraper(self):
        """Test creating a Legacy.com scraper."""
        url = "https://www.legacy.com/us/obituaries/jsonline/name/maxine-kaczmarowski-obituary?id=3326788"
        scraper = ScraperFactory.create_scraper(url)
        assert isinstance(scraper, LegacyScraper)
    
    def test_create_unknown_scraper(self):
        """Test creating a scraper for an unknown URL."""
        url = "https://unknown-site.com/obituary/123"
        scraper = ScraperFactory.create_scraper(url)
        assert scraper is None 
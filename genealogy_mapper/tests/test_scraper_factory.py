import pytest
from genealogy_mapper.core.scrapers.factory import ScraperFactory
from genealogy_mapper.core.scrapers.legacy_scraper import LegacyScraper

def test_create_legacy_scraper():
    """Test creating a Legacy.com scraper."""
    url = "https://www.legacy.com/us/obituaries/jsonline/name/maxine-kaczmarowski-obituary?id=3326788"
    scraper = ScraperFactory.create_scraper(url)
    assert isinstance(scraper, LegacyScraper)

def test_create_unknown_scraper():
    """Test creating a scraper for an unknown URL."""
    url = "https://unknown-site.com/obituary/123"
    scraper = ScraperFactory.create_scraper(url)
    assert scraper is None

def test_create_scraper_with_timeout():
    """Test creating a scraper with a custom timeout."""
    url = "https://www.legacy.com/us/obituaries/jsonline/name/maxine-kaczmarowski-obituary?id=3326788"
    timeout = 30
    scraper = ScraperFactory.create_scraper(url, timeout=timeout)
    assert isinstance(scraper, LegacyScraper)
    assert scraper.driver.timeouts.page_load == timeout  # Check in seconds 
from typing import Optional
from urllib.parse import urlparse
from .base_scraper import BaseScraper
from .legacy_scraper import LegacyScraper

class ScraperFactory:
    """Factory for creating appropriate scrapers based on URL."""
    
    @staticmethod
    def create_scraper(url: str, timeout: int = 3) -> Optional[BaseScraper]:
        """
        Create a scraper instance based on the URL.
        
        Args:
            url (str): The URL to scrape
            timeout (int): Maximum time to wait for elements to load, in seconds
            
        Returns:
            Optional[BaseScraper]: An instance of the appropriate scraper, or None if no suitable scraper is found
        """
        domain = urlparse(url).netloc.lower()
        
        if "legacy.com" in domain:
            return LegacyScraper(timeout=timeout)
        
        return None 
import logging
import time
import os
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger("genealogy_mapper")

class BaseScraper(ABC):
    """Base class for all obituary scrapers."""
    
    def __init__(self, timeout: int = 3):
        """
        Initialize the scraper with Selenium WebDriver.
        
        Args:
            timeout (int): Maximum time to wait for elements to load, in seconds
        """
        # Initialize Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.wait = WebDriverWait(self.driver, timeout)
        
        # Create debug directory if it doesn't exist
        self.debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'debug')
        os.makedirs(self.debug_dir, exist_ok=True)
    
    def __del__(self):
        """Clean up the WebDriver when the object is destroyed."""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    @abstractmethod
    def extract(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract obituary text and metadata from a URL.
        
        Args:
            url (str): The URL to extract from
            
        Returns:
            Optional[Dict[str, Any]]: Dictionary containing text and metadata, or None if extraction fails
        """
        pass
    
    def _save_debug_html(self, url: str) -> None:
        """Save the full HTML page source for debugging."""
        page_source = self.driver.page_source
        debug_file = os.path.join(self.debug_dir, f'{self.__class__.__name__.lower()}_page.html')
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(page_source)
        logger.info(f"Saved full HTML page source to: {debug_file}") 
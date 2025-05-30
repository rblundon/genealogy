import json
import logging
import os
from typing import List, Optional
import requests
import validators
from datetime import datetime

logger = logging.getLogger("genealogy_mapper")

class URLImporter:
    """Class for importing and managing obituary URLs."""
    
    def __init__(self, data_file: str = "obituaries.json"):
        """
        Initialize the URL importer.
        
        Args:
            data_file (str): Path to the JSON file storing URLs
        """
        self.data_file = data_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
        self._initialize_data_file()
    
    def _initialize_data_file(self) -> None:
        """Initialize the data file if it doesn't exist."""
        if not os.path.exists(self.data_file):
            logger.info(f"Creating new data file: {self.data_file}")
            with open(self.data_file, 'w') as f:
                json.dump({
                    "urls": [],
                    "version": "1.0"
                }, f, indent=2)
    
    def _load_urls(self) -> List[dict]:
        """Load URLs from the data file."""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                return data.get("urls", [])
        except json.JSONDecodeError:
            logger.error(f"Error reading {self.data_file}: Invalid JSON format")
            return []
        except Exception as e:
            logger.error(f"Error reading {self.data_file}: {str(e)}")
            return []
    
    def _save_urls(self, urls: List[dict]) -> bool:
        """Save URLs to the data file."""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            data["urls"] = urls
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving to {self.data_file}: {str(e)}")
            return False
    
    def validate_url(self, url: str) -> bool:
        """
        Validate a URL.
        
        Args:
            url (str): The URL to validate
            
        Returns:
            bool: True if the URL is valid and accessible, False otherwise
        """
        if not validators.url(url):
            logger.error(f"Invalid URL format: {url}")
            return False
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 404:
                logger.error(f"URL not found: {url}")
                return False
            response.raise_for_status()
            logger.info(f"URL validation successful: {url}")
            return True
        except requests.RequestException as e:
            logger.error(f"URL not accessible: {url} - {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error accessing URL: {url} - {str(e)}")
            return False
    
    def import_url(self, url: str) -> bool:
        """
        Import a new URL.
        
        Args:
            url (str): The URL to import
            
        Returns:
            bool: True if the URL was imported successfully, False otherwise
        """
        logger.info(f"Attempting to import URL: {url}")

        urls = self._load_urls()

        # Check for duplicates first
        if any(u["url"] == url for u in urls):
            logger.info(f"URL already exists in database: {url}")
            return True

        # Only validate if not a duplicate
        if not self.validate_url(url):
            return False
        
        # Add new URL
        new_url = {
            "url": url,
            "imported_at": datetime.now().isoformat()
        }
        urls.append(new_url)
        
        if self._save_urls(urls):
            logger.info(f"Successfully imported URL: {url}")
            return True
        else:
            logger.error(f"Failed to save URL: {url}")
            return False
    
    def get_urls(self) -> List[dict]:
        """
        Get all imported URLs.
        
        Returns:
            List[dict]: List of URL dictionaries
        """
        return self._load_urls() 
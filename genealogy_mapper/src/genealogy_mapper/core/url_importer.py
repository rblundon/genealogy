import json
import logging
import os
from typing import Dict, List, Optional
import requests
import validators
from datetime import datetime
from .scrapers.factory import ScraperFactory

logger = logging.getLogger(__name__)

def get_project_root() -> str:
    """Get the project root directory."""
    # Start from the current file's directory and go up until we find the project root
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    return current_dir

class URLImporter:
    """Class for importing and managing obituary URLs."""
    
    def __init__(self, json_path: Optional[str] = None, timeout: int = 3, force_rescrape: bool = False):
        """
        Initialize the URL importer.
        
        Args:
            json_path (Optional[str]): Path to the JSON file for storing URLs. If None, uses default in project root.
            timeout (int): Maximum time to wait for elements to load, in seconds
            force_rescrape (bool): If True, process all URLs even if they have "completed" status
        """
        if json_path is None:
            json_path = os.path.join(get_project_root(), "obituary_urls.json")
        self.json_path = json_path
        self.timeout = timeout
        self.force_rescrape = force_rescrape
        self._ensure_json_file()
        self._migrate_old_data()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
    
    def _ensure_json_file(self) -> None:
        """Ensure the JSON file exists with proper structure."""
        if not os.path.exists(self.json_path):
            initial_data = {
                "urls": [],
                "last_updated": datetime.now().isoformat()
            }
            with open(self.json_path, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def _migrate_old_data(self) -> None:
        """Migrate old data format to new format."""
        # Implementation of _migrate_old_data method
        pass
    
    def _load_json(self) -> Dict:
        """Load and validate JSON data."""
        try:
            with open(self.json_path, 'r') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Invalid JSON structure")
                if "urls" not in data:
                    data["urls"] = []
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(f"Could not read {self.json_path}, creating new file")
            return {"urls": [], "last_updated": datetime.now().isoformat()}
    
    def _save_json(self, data: Dict) -> None:
        """Save data to JSON file."""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=2)
    
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
        Import a URL into the database.
        
        Args:
            url: The URL to import
            
        Returns:
            bool: True if URL was imported or already exists, False if import failed
        """
        if not validators.url(url):
            logger.error(f"Invalid URL format: {url}")
            return False

        data = self._load_json()
        
        # Check for duplicates
        if any(entry["url"] == url for entry in data["urls"]):
            logger.info(f"URL already exists in database: {url}")
            return True

        # Add new URL with pending status
        new_entry = {
            "url": url,
            "date_added": datetime.now().strftime("%Y-%m-%d"),
            "source": "legacy.com" if "legacy.com" in url else "unknown",
            "status": "pending",
            "extracted_text": None,
            "metadata": {
                "newspaper": "Unknown",
                "location": "Unknown"
            }
        }
        
        data["urls"].append(new_entry)
        self._save_json(data)
        logger.info(f"Successfully imported URL: {url}")
        return True

    def get_unprocessed_urls(self) -> List[Dict]:
        """
        Get all URLs that need to be processed.
        
        Returns:
            List[Dict]: List of URLs that need processing
        """
        try:
            with open(self.json_path, 'r') as f:
                data = json.load(f)
                
            if self.force_rescrape:
                # Return all URLs if force_rescrape is True
                return data.get("urls", [])
            else:
                # Return only URLs that haven't been successfully processed
                return [url for url in data.get("urls", []) if url.get("status") != "completed"]
                
        except Exception as e:
            logger.error(f"Error reading URLs: {str(e)}")
            return []

    def update_url_status(self, url: str, status: str, extracted_text: Optional[str] = None, metadata: Optional[Dict] = None) -> bool:
        """Update the status and data for a URL."""
        data = self._load_json()
        for entry in data["urls"]:
            if entry["url"] == url:
                entry["status"] = status
                if extracted_text is not None:
                    entry["extracted_text"] = extracted_text
                if metadata is not None:
                    entry["metadata"] = metadata
                self._save_json(data)
                return True
        return False

    def process_pending_urls(self) -> List[Dict]:
        """
        Process all unprocessed URLs and extract their text.
        
        Returns:
            List[Dict]: List of processed URLs with their extracted text and metadata
        """
        unprocessed_urls = self.get_unprocessed_urls()
        if not unprocessed_urls:
            logger.info("No unprocessed URLs to process")
            return []

        processed = []

        for entry in unprocessed_urls:
            url = entry["url"]
            logger.info(f"Processing URL: {url}")
            
            # Create appropriate scraper for the URL
            scraper = ScraperFactory.create_scraper(url, timeout=self.timeout)
            if not scraper:
                logger.error(f"No suitable scraper found for URL: {url}")
                self.update_url_status(url=url, status="failed")
                continue
            
            result = scraper.extract(url)
            if result:
                self.update_url_status(
                    url=url,
                    status="completed",
                    extracted_text=result["text"],
                    metadata=result["metadata"]
                )
                processed.append({
                    "url": url,
                    "text": result["text"],
                    "metadata": result["metadata"]
                })
            else:
                self.update_url_status(url=url, status="failed")
                logger.error(f"Failed to extract text from URL: {url}")

        return processed 
import json
import logging
import os
from typing import Dict, List, Optional
import requests
import validators
from datetime import datetime
from .obituary_scraper import ObituaryScraper

logger = logging.getLogger(__name__)

class URLImporter:
    """Class for importing and managing obituary URLs."""
    
    def __init__(self, json_file: str = None, timeout: int = 3):
        """
        Initialize the URL importer.
        
        Args:
            json_file (str): Path to the JSON file storing URLs
            timeout (int): Maximum time to wait for elements to load, in seconds
        """
        # Default to project root if not specified
        if json_file is None:
            # This file: .../genealogy_mapper/src/genealogy_mapper/core/url_importer.py
            # Project root: .../genealogy/
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
            json_file = os.path.join(project_root, 'obituary_urls.json')
        self.json_file = json_file
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
        self._ensure_json_file_exists()
    
    def _ensure_json_file_exists(self) -> None:
        """Ensure the JSON file exists with proper structure."""
        if not os.path.exists(self.json_file):
            initial_data = {
                "urls": [],
                "last_updated": datetime.now().isoformat()
            }
            with open(self.json_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def _load_json(self) -> Dict:
        """Load and validate JSON data."""
        try:
            with open(self.json_file, 'r') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Invalid JSON structure")
                if "urls" not in data:
                    data["urls"] = []
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(f"Could not read {self.json_file}, creating new file")
            return {"urls": [], "last_updated": datetime.now().isoformat()}
    
    def _save_json(self, data: Dict) -> None:
        """Save data to JSON file."""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.json_file, 'w') as f:
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
        """Get all URLs that haven't been successfully processed."""
        data = self._load_json()
        return data["urls"]  # Return all URLs regardless of status

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

        scraper = ObituaryScraper(timeout=self.timeout)
        processed = []

        for entry in unprocessed_urls:
            url = entry["url"]
            logger.info(f"Processing URL: {url}")
            
            result = scraper.extract_legacy_com(url)
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
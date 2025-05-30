import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import validators
import requests

logger = logging.getLogger("genealogy_mapper")

class URLImporter:
    def __init__(self, json_path: str = "obituaries.json"):
        self.json_path = Path(json_path)
        self._ensure_json_exists()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _ensure_json_exists(self) -> None:
        """Ensure the JSON file exists with proper structure."""
        if not self.json_path.exists():
            logger.info(f"Creating new obituaries file at {self.json_path}")
            initial_data = {
                "version": "2.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "obituaries": []
            }
            self._write_json(initial_data)
    
    def _read_json(self) -> Dict[str, Any]:
        """Read the JSON file."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error reading JSON file: {e}")
            raise
    
    def _write_json(self, data: Dict[str, Any]) -> None:
        """Write data to the JSON file."""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error writing to JSON file: {e}")
            raise
    
    def validate_url(self, url: str) -> bool:
        """
        Validate the URL format and check if it's accessible.
        
        Args:
            url (str): The URL to validate
            
        Returns:
            bool: True if valid and accessible, False otherwise
        """
        logger.debug(f"Validating URL: {url}")
        
        # Check URL format
        if not validators.url(url):
            logger.error(f"Invalid URL format: {url}")
            return False
        
        # Check if URL is accessible
        try:
            # Add a small delay to be respectful to the server
            time.sleep(1)
            
            # Use GET instead of HEAD and add proper headers
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"URL not accessible: {url} (Status: {response.status_code})")
                return False
                
            # Check if the page contains expected content
            if "obituary" not in response.text.lower():
                logger.error(f"URL does not appear to be an obituary page: {url}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error accessing URL: {url} - {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error accessing URL: {url} - {str(e)}")
            return False
        
        logger.info(f"URL validation successful: {url}")
        return True
    
    def import_url(self, url: str) -> bool:
        """
        Import a new URL into the obituaries JSON file.
        
        Args:
            url (str): The URL to import
            
        Returns:
            bool: True if import was successful, False otherwise
        """
        logger.info(f"Attempting to import URL: {url}")
        
        if not self.validate_url(url):
            return False
        
        # Read current data
        data = self._read_json()
        
        # Check for duplicate URL
        for obit in data["obituaries"]:
            if obit["url"] == url:
                logger.info(f"URL already exists in database: {url}")
                return False
        
        # Generate unique ID
        url_id = f"legacy-{url.split('id=')[-1]}" if 'id=' in url else f"url-{len(data['obituaries'])}"
        
        # Create new entry
        new_entry = {
            "id": url_id,
            "url": url,
            "source": "legacy.com" if "legacy.com" in url else "unknown",
            "date_added": datetime.now().strftime("%Y-%m-%d"),
            "status": "pending",
            "metadata": {
                "newspaper": "Unknown",
                "location": "Unknown"
            }
        }
        
        # Add to obituaries list
        data["obituaries"].append(new_entry)
        data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        
        # Write back to file
        self._write_json(data)
        
        logger.info(f"Successfully imported URL: {url}")
        return True 
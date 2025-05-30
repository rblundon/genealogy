import logging
import time
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger("genealogy_mapper")

class ObituaryScraper:
    """Class for scraping obituary text and metadata from various sources."""
    
    def __init__(self):
        """Initialize the scraper with a session for making requests."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
    
    def extract_legacy_com(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract obituary text and metadata from a Legacy.com URL.
        
        Args:
            url (str): The URL to extract from
            
        Returns:
            Optional[Dict[str, Any]]: Dictionary containing text and metadata, or None if extraction fails
        """
        logger.info(f"Extracting obituary from Legacy.com: {url}")
        
        try:
            # Add a small delay to be respectful to the server
            time.sleep(2)
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the main obituary text
            text = self._extract_legacy_text(soup)
            if not text:
                logger.error("Could not find obituary text")
                return None
            
            # Extract metadata
            metadata = self._extract_legacy_metadata(soup)
            
            return {
                "text": text,
                "metadata": metadata
            }
            
        except requests.RequestException as e:
            logger.error(f"Error accessing URL: {url} - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error extracting obituary: {str(e)}")
            return None
    
    def _extract_legacy_text(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the main obituary text from the parsed HTML."""
        try:
            # Try different possible selectors for the obituary text
            selectors = [
                'div.obit-text',
                'div.obituary-text',
                'div.obit-content',
                'div.obituary-content',
                'div.obit-body',
                'div.obituary-body'
            ]
            
            for selector in selectors:
                text_div = soup.select_one(selector)
                if text_div:
                    # Clean up the text
                    text = text_div.get_text(separator='\n', strip=True)
                    return text
            
            # If no specific selector worked, try to find the main content area
            main_content = soup.find('main') or soup.find('article')
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
                return text
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return None
    
    def _extract_legacy_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from the parsed HTML."""
        metadata = {
            "name": "Unknown",
            "birth_date": "Unknown",
            "death_date": "Unknown",
            "newspaper": "Unknown",
            "location": "Unknown",
            "publication_date": "Unknown"
        }
        
        try:
            # Try to extract name
            name_elem = soup.select_one('h1.obit-name') or soup.select_one('h1.obituary-name')
            if name_elem:
                metadata["name"] = name_elem.get_text(strip=True)
            
            # Try to extract dates
            date_elem = soup.select_one('div.obit-dates') or soup.select_one('div.obituary-dates')
            if date_elem:
                dates = date_elem.get_text(strip=True)
                if " - " in dates:
                    birth, death = dates.split(" - ", 1)
                    metadata["birth_date"] = birth.strip()
                    metadata["death_date"] = death.strip()
            
            # Try to extract newspaper and location
            source_elem = soup.select_one('div.obit-source') or soup.select_one('div.obituary-source')
            if source_elem:
                source_text = source_elem.get_text(strip=True)
                if " - " in source_text:
                    paper, location = source_text.split(" - ", 1)
                    metadata["newspaper"] = paper.strip()
                    metadata["location"] = location.strip()
            
            # Try to extract publication date
            pub_date = soup.select_one('div.obit-date') or soup.select_one('div.obituary-date')
            if pub_date:
                metadata["publication_date"] = pub_date.get_text(strip=True)
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
        
        return metadata 
import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Optional, Dict, List
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        """
        Initialize the web scraper with a base URL and optional headers.
        
        Args:
            base_url (str): The base URL to scrape
            headers (Dict[str, str], optional): HTTP headers to use in requests
        """
        self.base_url = base_url
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()

    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return its BeautifulSoup object.
        
        Args:
            url (str): The URL to fetch
            
        Returns:
            Optional[BeautifulSoup]: BeautifulSoup object if successful, None if failed
        """
        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'lxml')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def save_to_json(self, data: List[Dict], filename: str) -> None:
        """
        Save scraped data to a JSON file.
        
        Args:
            data (List[Dict]): The data to save
            filename (str): The output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved to {filename}")
        except IOError as e:
            logger.error(f"Error saving data to {filename}: {str(e)}")

    def scrape(self) -> List[Dict]:
        """
        Main scraping method to be implemented by subclasses.
        
        Returns:
            List[Dict]: List of scraped data
        """
        raise NotImplementedError("Subclasses must implement scrape()")

def main():
    # Example usage
    class ExampleScraper(WebScraper):
        def scrape(self) -> List[Dict]:
            soup = self.get_page(self.base_url)
            if not soup:
                return []
            
            # Example: scraping all paragraph texts
            data = []
            for p in soup.find_all('p'):
                data.append({
                    'text': p.get_text(strip=True)
                })
            return data

    # Example usage
    scraper = ExampleScraper('https://example.com')
    data = scraper.scrape()
    scraper.save_to_json(data, 'scraped_data.json')

if __name__ == '__main__':
    main() 
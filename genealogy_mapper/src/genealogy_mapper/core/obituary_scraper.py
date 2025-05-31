import logging
import time
import os
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger("genealogy_mapper")

class ObituaryScraper:
    """Class for scraping obituary text and metadata from Legacy.com."""
    
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
            
            # Load the page
            self.driver.get(url)
            
            # Wait for the page to load and JavaScript to execute
            try:
                # First wait for the body to be present
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # Then wait for any of the common obituary text containers
                text_selectors = [
                    "div.obit-text",
                    "div.obituary-text",
                    "div.obit-content",
                    "div.obituary-content",
                    "div.obit-body",
                    "div.obituary-body",
                    "div.obit-detail",
                    "div.obituary-detail",
                    "div.obit-main",
                    "div.obituary-main"
                ]
                
                # Try each selector
                for selector in text_selectors:
                    try:
                        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        logger.debug(f"Found text container with selector: {selector}")
                        break
                    except TimeoutException:
                        continue
                
                # Additional wait for dynamic content
                time.sleep(5)  # Increased wait time
                
                # Save the full HTML page source for debugging
                page_source = self.driver.page_source
                debug_file = os.path.join(self.debug_dir, 'legacy_page.html')
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                logger.info(f"Saved full HTML page source to: {debug_file}")
                
                # Get the page source and parse with BeautifulSoup
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Extract metadata first
                metadata = self._extract_metadata(soup)
                
                # Extract the main obituary text
                text = self._extract_text(soup)
                if not text:
                    logger.error("Could not find obituary text")
                    return None
                
                return {
                    "text": text,
                    "metadata": metadata
                }
                
            except TimeoutException as e:
                logger.error(f"Timeout waiting for page to load: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Error extracting obituary: {str(e)}")
            return None
    
    def _extract_text(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the main obituary text from the parsed HTML."""
        try:
            # First try to extract from JSON-LD data
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    import json
                    data = json.loads(script.string)
                    if "articleBody" in data:
                        text = data["articleBody"]
                        if text and len(text) > 100:  # Ensure we have substantial content
                            logger.debug("Found obituary text in JSON-LD data")
                            return text
                except Exception as e:
                    logger.debug(f"Error parsing JSON-LD: {str(e)}")
                    continue
            
            # If JSON-LD extraction fails, try the existing selectors
            selectors = [
                'div.obit-text',
                'div.obituary-text',
                'div.obit-content',
                'div.obituary-content',
                'div.obit-body',
                'div.obituary-body',
                'div.obit-detail',
                'div.obituary-detail',
                'div.obit-main',
                'div.obituary-main',
                'div[class*="obit"]',
                'div[class*="obituary"]'
            ]
            
            for selector in selectors:
                text_div = soup.select_one(selector)
                if text_div:
                    # Clean up the text
                    text = text_div.get_text(separator='\n', strip=True)
                    if text and len(text) > 100:  # Ensure we have substantial content
                        return text
            
            # If no specific selector worked, try to find the main content area
            main_content = soup.find('main') or soup.find('article')
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
                if text and len(text) > 100:  # Ensure we have substantial content
                    return text
            
            # Log the HTML structure for debugging
            logger.debug("HTML structure:")
            logger.debug(soup.prettify()[:1000])  # Log first 1000 chars for debugging
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return None
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
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
            # First try to extract from JSON-LD data
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    import json
                    data = json.loads(script.string)
                    
                    # Extract name from headline or name field
                    if "headline" in data:
                        metadata["name"] = data["headline"].split(" Obituary")[0]
                    elif "name" in data:
                        metadata["name"] = data["name"]
                    
                    # Extract location
                    if "deathPlace" in data and "address" in data["deathPlace"]:
                        addr = data["deathPlace"]["address"]
                        location_parts = []
                        if "addressLocality" in addr:
                            location_parts.append(addr["addressLocality"])
                        if "addressRegion" in addr:
                            location_parts.append(addr["addressRegion"])
                        if location_parts:
                            metadata["location"] = ", ".join(location_parts)
                    
                    # Extract publication date
                    if "datePublished" in data:
                        metadata["publication_date"] = data["datePublished"]
                    
                    # Extract newspaper from publisher
                    if "publisher" in data and "name" in data["publisher"]:
                        metadata["newspaper"] = data["publisher"]["name"]
                    
                    # If we found any metadata, return it
                    if any(v != "Unknown" for v in metadata.values()):
                        return metadata
                        
                except Exception as e:
                    logger.debug(f"Error parsing JSON-LD metadata: {str(e)}")
                    continue
            
            # If JSON-LD extraction fails, try the existing selectors
            # Try to extract name
            name_selectors = [
                'h1.obit-name',
                'h1.obituary-name',
                'h1[class*="obit"]',
                'h1[class*="obituary"]',
                'h1.obit-title',
                'h1.obituary-title'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    metadata["name"] = name_elem.get_text(strip=True)
                    break
            
            # Try to extract location
            location_selectors = [
                'div.obit-location',
                'div.obituary-location',
                'div[class*="location"]',
                'span[class*="location"]'
            ]
            
            for selector in location_selectors:
                location_elem = soup.select_one(selector)
                if location_elem:
                    metadata["location"] = location_elem.get_text(strip=True)
                    break
            
            # Try to extract newspaper
            newspaper_selectors = [
                'div.obit-source',
                'div.obituary-source',
                'div[class*="source"]',
                'span[class*="source"]'
            ]
            
            for selector in newspaper_selectors:
                newspaper_elem = soup.select_one(selector)
                if newspaper_elem:
                    metadata["newspaper"] = newspaper_elem.get_text(strip=True)
                    break
            
            # Try to extract dates
            date_selectors = [
                'div.obit-dates',
                'div.obituary-dates',
                'div[class*="dates"]',
                'span[class*="dates"]'
            ]
            
            for selector in date_selectors:
                dates_elem = soup.select_one(selector)
                if dates_elem:
                    dates_text = dates_elem.get_text(strip=True)
                    # Try to parse birth and death dates
                    if " - " in dates_text:
                        birth, death = dates_text.split(" - ", 1)
                        metadata["birth_date"] = birth.strip()
                        metadata["death_date"] = death.strip()
                    break
            
            # Try to extract publication date
            pub_date_selectors = [
                'div.obit-date',
                'div.obituary-date',
                'div[class*="publication-date"]',
                'span[class*="publication-date"]'
            ]
            
            for selector in pub_date_selectors:
                pub_date_elem = soup.select_one(selector)
                if pub_date_elem:
                    metadata["publication_date"] = pub_date_elem.get_text(strip=True)
                    break
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return metadata 
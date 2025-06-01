import requests
from bs4 import BeautifulSoup
from genealogy_mapper.core.ner_processor import ObituaryNERProcessor
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_obituary(url):
    """Fetch obituary content from Legacy.com."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch obituary: {e}")
        return None

def extract_obituary_text(html_content):
    """Extract obituary text from HTML content."""
    if not html_content:
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Try to find the obituary text
    # Look for common obituary text containers
    obit_text = None
    for class_name in ['obituary-text', 'obit-text', 'obituary-content']:
        element = soup.find('div', class_=class_name)
        if element:
            obit_text = element.get_text(strip=True)
            break
    
    if not obit_text:
        # Try to find text that looks like an obituary
        # Look for text containing common obituary phrases
        text = soup.get_text(strip=True)
        obit_start = text.find("Kaczmarowski, Maxine V.")
        if obit_start != -1:
            obit_end = text.find("Published by", obit_start)
            if obit_end != -1:
                obit_text = text[obit_start:obit_end].strip()
    
    return obit_text

def main():
    # URL from the JSON file
    url = "https://www.legacy.com/us/obituaries/jsonline/name/maxine-kaczmarowski-obituary?id=3326788"
    
    # Fetch the obituary
    html_content = fetch_obituary(url)
    if not html_content:
        logger.error("Failed to fetch obituary content")
        return
    
    # Extract text
    obit_text = extract_obituary_text(html_content)
    if not obit_text:
        logger.error("Failed to extract obituary text")
        return
    
    # Process with NER
    processor = ObituaryNERProcessor()
    person_info = processor.extract_person_info(obit_text)
    
    # Print results
    print("\nExtracted Information:")
    print(f"Full Name: {person_info.full_name}")
    print(f"Maiden Name: {person_info.maiden_name}")
    print(f"Gender: {person_info.gender}")
    print(f"Age: {person_info.age}")
    print(f"Birth Date: {person_info.birth_date}")
    print(f"Death Date: {person_info.death_date}")
    print(f"Birth Place: {person_info.birth_place}")
    print(f"Death Place: {person_info.death_place}")
    print(f"Occupation: {person_info.occupation}")
    print(f"Education: {person_info.education}")
    print(f"Military Service: {person_info.military_service}")
    print(f"Organizations: {person_info.organizations}")
    print("\nRaw Text:")
    print(obit_text)

if __name__ == "__main__":
    main() 
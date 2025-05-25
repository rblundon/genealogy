import json
import re
from scraper import WebScraper
from bs4 import BeautifulSoup
import logging
import argparse
from datetime import datetime
from common_classes import DateNormalizer
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def is_valid_url(url):
    if not url:
        logger.debug("URL is None or empty")
        return False
    parsed = urlparse(url)
    is_valid = all([parsed.scheme, parsed.netloc])
    if not is_valid:
        logger.debug(f"Invalid URL format: {url}")
    return is_valid

def is_invalid_obituary_text(text):
    if not text or not isinstance(text, str):
        logger.debug("Obituary text is None or not a string")
        return True
    # Consider text invalid if it's too short or contains placeholder text
    if len(text.strip()) < 20:
        logger.debug(f"Obituary text too short ({len(text.strip())} chars): {text}")
        return True
    if text.strip().lower() in {"n/a", "none", "unknown", "obituary not available"}:
        logger.debug(f"Obituary text contains placeholder: {text}")
        return True
    return False

class ObituaryReader(WebScraper):
    def __init__(self):
        super().__init__(base_url="https://www.legacy.com")
        logger.info("Initialized ObituaryReader with base URL: https://www.legacy.com")

    def extract_fields(self, soup: BeautifulSoup, url: str) -> dict:
        logger.info(f"Extracting fields from URL: {url}")
        
        # Extract name from <title>
        title_tag = soup.find('title')
        name = None
        location = None
        if title_tag:
            title_text = title_tag.get_text()
            name_match = re.match(r'^(.*?) Obituary', title_text)
            if name_match:
                name = name_match.group(1).strip()
                logger.info(f"Found name in title: {name}")
            loc_match = re.search(r'- ([^-]+) - [^-]+Funeral Home', title_text)
            if loc_match:
                location = loc_match.group(1).strip()
                logger.info(f"Found location in title: {location}")
            else:
                dash_parts = title_text.split('-')
                if len(dash_parts) > 1:
                    location = dash_parts[-2].strip()
                    logger.info(f"Found location in title (alternative format): {location}")

        # Extract summary and dates from <meta name="description">
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        birth_date = None
        death_date = None
        obituary_text = None
        if meta_desc:
            desc = meta_desc.get('content', '')
            obituary_text = desc
            logger.info("Found meta description")
            # Try to extract dates from description
            birth_date = DateNormalizer.find_birth_date(desc)
            if birth_date:
                logger.info(f"Found birth date in meta: {birth_date}")
            death_date = DateNormalizer.find_death_date(desc)
            if death_date:
                logger.info(f"Found death date in meta: {death_date}")

        # Try to extract the main obituary text from a visible element
        main_obit = ''
        obit_div = soup.find('div', class_=re.compile(r'ObituaryText|obituary-text|obituary__text'))
        if obit_div:
            main_obit = obit_div.get_text(separator=' ', strip=True)
            logger.info("Found obituary text in main content div")
        elif obituary_text:
            main_obit = obituary_text
            logger.info("Using meta description as obituary text")

        # Try to find dates in the main obituary text if not found in meta
        if not birth_date or not death_date:
            logger.info("Searching for dates in main obituary text")
            # Look for age
            age = DateNormalizer.find_age(main_obit)
            if age:
                logger.info(f"Found age: {age}")

            # Look for death date if not found
            if not death_date:
                death_date = DateNormalizer.find_death_date(main_obit)
                if death_date:
                    logger.info(f"Found death date in main text: {death_date}")

            # Calculate birth date from death date and age if we have both
            if death_date and age and not birth_date:
                birth_date = DateNormalizer.calculate_birth_date(death_date, age)
                if birth_date:
                    logger.info(f"Calculated birth date from death date and age: {birth_date}")

            # Look for birth date if still not found
            if not birth_date:
                birth_date = DateNormalizer.find_birth_date(main_obit)
                if birth_date:
                    logger.info(f"Found birth date in main text: {birth_date}")

        return {
            'name': name,
            'birth_date': birth_date,
            'death_date': death_date,
            'location': location,
            'obituary_text': main_obit,
            'url': url
        }

    def read_obituaries(self, people_file: str, refresh_all: bool = False):
        logger.info(f"Reading obituaries from file: {people_file}")
        with open(people_file, 'r') as f:
            people = json.load(f)
        logger.info(f"Loaded {len(people)} people from {people_file}")

        # Normalize any existing dates before scraping
        logger.info("Normalizing existing dates...")
        people = DateNormalizer.normalize_existing_dates(people)

        updated_people = []
        for i, person in enumerate(people, 1):
            current_name = person.get('name', 'Unknown')
            person_id = person.get('id', 'No ID')
            url = person.get('url')
            obituary_text = person.get('obituary_text')

            logger.info(f"\nProcessing person {i}/{len(people)}: {current_name} (ID: {person_id})")

            # Skip if URL is invalid
            if not is_valid_url(url):
                logger.info(f"Skipping {current_name} (ID: {person_id}) - invalid or missing URL")
                updated_people.append(person)
                continue

            # Skip if obituary text is valid and we're not refreshing all
            if not refresh_all and not is_invalid_obituary_text(obituary_text):
                logger.info(f"Skipping {current_name} (ID: {person_id}) - already has valid obituary text")
                updated_people.append(person)
                continue

            if refresh_all:
                logger.info(f"Refreshing obituary for {current_name} (ID: {person_id}) (--refresh-obits flag set)")

            logger.info(f"Fetching obituary for {current_name} (ID: {person_id}) at {url}")
            soup = self.get_page(url)
            if not soup:
                logger.warning(f"Failed to fetch page for {current_name} (ID: {person_id})")
                updated_people.append(person)
                continue

            fields = self.extract_fields(soup, url)
            # Update the person's data with new fields
            person.update({
                'name': fields['name'] or current_name,  # Use extracted name if available
                'birth_date': fields['birth_date'] or person.get('birth_date'),
                'death_date': fields['death_date'] or person.get('death_date'),
                'location': fields['location'] or person.get('location'),
                'obituary_text': fields['obituary_text'] or person.get('obituary_text')
            })
            
            # Log the name update if it changed
            if fields['name'] and fields['name'] != current_name:
                logger.info(f"Updated name from '{current_name}' to '{fields['name']}' for ID: {person_id}")
            
            logger.info(f"Updated data for {person['name']} (ID: {person_id})")
            updated_people.append(person)

        # Save updated people data back to input file
        logger.info(f"\nSaving updated data to {people_file}")
        with open(people_file, 'w') as f:
            json.dump(updated_people, f, indent=2)
        logger.info(f"Successfully updated {people_file} with new data.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read obituary details from URLs in a JSON file.")
    parser.add_argument("input_file", help="Path to the input JSON file containing people data")
    parser.add_argument("--refresh-obits", action="store_true", 
                       help="Force re-reading of all obituaries with valid URLs")
    args = parser.parse_args()
    reader = ObituaryReader()
    reader.read_obituaries(args.input_file, args.refresh_obits) 
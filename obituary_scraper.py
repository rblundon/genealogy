import json
import re
from scraper import WebScraper
from bs4 import BeautifulSoup
import logging
import argparse
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DateNormalizer:
    @staticmethod
    def parse_date(date_str):
        """Convert various date formats to dd mmm yyyy format."""
        if not date_str:
            return None
        
        # Common date formats to try
        formats = [
            '%B %d, %Y',  # May 24, 2018
            '%B %d %Y',   # May 24 2018
            '%d %B %Y',   # 24 May 2018
            '%d %b %Y',   # 24 May 2018
            '%b %d %Y',   # May 24 2018
            '%Y-%m-%d',   # 2018-05-24
            '%m/%d/%Y',   # 05/24/2018
            '%d/%m/%Y',   # 24/05/2018
            '%d %b %Y',   # 24 May 2018
            '%d %B %Y',   # 24 May 2018
            '%B %dth, %Y', # May 24th, 2018
            '%B %dst, %Y', # May 1st, 2018
            '%B %dnd, %Y', # May 2nd, 2018
            '%B %drd, %Y', # May 3rd, 2018
            '%d %B %Y',   # 24 May 2018
            '%d %b %Y',   # 24 May 2018
            '%d %B, %Y',  # 24 May, 2018
            '%d %b, %Y',  # 24 May, 2018
        ]
        
        # Clean up the date string
        date_str = date_str.strip()
        # Remove ordinal indicators (st, nd, rd, th)
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%d %b %Y')
            except ValueError:
                continue
        
        return None

    @classmethod
    def normalize_existing_dates(cls, people):
        """Normalize any existing birth_date or death_date fields in the people list."""
        for person in people:
            for field in ["birth_date", "death_date"]:
                val = person.get(field)
                if val:
                    normalized = cls.parse_date(val)
                    if normalized:
                        person[field] = normalized
        return people

class ObituaryScraper(WebScraper):
    def __init__(self):
        super().__init__(base_url="https://www.legacy.com")

    def extract_fields(self, soup: BeautifulSoup, url: str) -> dict:
        # Extract name from <title>
        title_tag = soup.find('title')
        name = None
        location = None
        if title_tag:
            title_text = title_tag.get_text()
            name_match = re.match(r'^(.*?) Obituary', title_text)
            if name_match:
                name = name_match.group(1).strip()
            loc_match = re.search(r'- ([^-]+) - [^-]+Funeral Home', title_text)
            if loc_match:
                location = loc_match.group(1).strip()
            else:
                dash_parts = title_text.split('-')
                if len(dash_parts) > 1:
                    location = dash_parts[-2].strip()

        # Extract summary and dates from <meta name="description">
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        birth_date = None
        death_date = None
        obituary_text = None
        if meta_desc:
            desc = meta_desc.get('content', '')
            obituary_text = desc
            # Try to extract dates from description
            birth_match = re.search(r'Born (\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})', desc)
            if birth_match:
                birth_date = DateNormalizer.parse_date(birth_match.group(1))
            death_match = re.search(r'Died (\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})', desc)
            if death_match:
                death_date = DateNormalizer.parse_date(death_match.group(1))

        # Try to extract the main obituary text from a visible element
        main_obit = ''
        obit_div = soup.find('div', class_=re.compile(r'ObituaryText|obituary-text|obituary__text'))
        if obit_div:
            main_obit = obit_div.get_text(separator=' ', strip=True)
        elif obituary_text:
            main_obit = obituary_text

        # Try to find dates in the main obituary text if not found in meta
        if not birth_date or not death_date:
            # Look for patterns like "age 87 years" or "age 80"
            age_match = re.search(r'age (\d+)(?:\s+years)?', main_obit, re.IGNORECASE)
            if age_match and death_date:
                try:
                    age = int(age_match.group(1))
                    death_year = int(re.search(r'\d{4}', death_date).group())
                    birth_year = death_year - age
                    birth_date = f"01 Jan {birth_year}"
                except (ValueError, IndexError):
                    pass

            # Look for patterns like "Born in 1941" or "Born 1941"
            if not birth_date:
                birth_year_match = re.search(r'born(?:\s+in)?\s+(\d{4})', main_obit, re.IGNORECASE)
                if birth_year_match:
                    birth_year = birth_year_match.group(1)
                    birth_date = f"01 Jan {birth_year}"

            # Look for death date patterns
            if not death_date:
                death_patterns = [
                    r'passed away on (\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})',
                    r'died on (\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})',
                    r'passed on (\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})',
                    r'(\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4}) at the age of',
                ]
                for pattern in death_patterns:
                    death_match = re.search(pattern, main_obit, re.IGNORECASE)
                    if death_match:
                        death_date = DateNormalizer.parse_date(death_match.group(1))
                        break

        return {
            'name': name,
            'birth_date': birth_date,
            'death_date': death_date,
            'location': location,
            'obituary_text': main_obit,
            'url': url
        }

    def scrape_people(self, people_file: str, output_file: str):
        with open(people_file, 'r') as f:
            people = json.load(f)
        logger.info(f"Loaded {len(people)} people from {people_file}")

        # Normalize any existing dates before scraping
        people = DateNormalizer.normalize_existing_dates(people)

        results = []
        updated_people = []
        
        for person in people:
            name = person.get('name', 'Unknown')
            url = person.get('url')
            if not url:
                logger.info(f"Skipping {name} (no URL)")
                updated_people.append(person)
                continue
            
            logger.info(f"Processing {name} at {url}")
            soup = self.get_page(url)
            if not soup:
                updated_people.append(person)
                continue
            
            fields = self.extract_fields(soup, url)
            results.append(fields)
            
            # Update the person's data with new fields
            person.update({
                'birth_date': fields['birth_date'] or person.get('birth_date'),
                'death_date': fields['death_date'] or person.get('death_date'),
                'location': fields['location'] or person.get('location'),
                'obituary_text': fields['obituary_text'] or person.get('obituary_text')
            })
            updated_people.append(person)
        
        # Save scraped results
        self.save_to_json(results, output_file)
        logger.info(f"Scraped {len(results)} obituaries.")
        
        # Save updated people data back to input file
        with open(people_file, 'w') as f:
            json.dump(updated_people, f, indent=2)
        logger.info(f"Updated {people_file} with new data.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape obituary details from URLs in a JSON file.")
    parser.add_argument("input_file", help="Path to the input JSON file (e.g., people.json)")
    parser.add_argument("--output", default="scraped_obituaries.json", help="Path to the output JSON file (default: scraped_obituaries.json)")
    args = parser.parse_args()
    scraper = ObituaryScraper()
    scraper.scrape_people(args.input_file, args.output) 
"""
ObituaryProcessor: A class for processing obituary URLs and extracting key information.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from genealogy.core.patterns import DEATH_PATTERNS, BIRTH_PATTERNS, AGE_PATTERNS, LOCATION_PATTERNS
from .name_extractor import NameExtractor
from .obituary_utils import read_obituary, get_next_individual_id, initialize_individual_id_counter
from .date_normalizer import DateNormalizer

class ObituaryProcessor:
    def __init__(self, input_file: str):
        """Initialize the ObituaryProcessor with input file path."""
        self.input_file = input_file
        self.name_extractor = NameExtractor()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.current_person = None  # Track the current person being processed

    def process_url(self, url: str, force_refresh: bool = False) -> Dict:
        """
        Process a single obituary URL.
        
        Args:
            url: The URL to process
            force_refresh: Whether to force a refresh of the data
            
        Returns:
            Dictionary containing the processed data
        """
        try:
            # Check if we need to process this obituary
            if not force_refresh and self.current_person:
                # Check if we have all required fields
                text = self.current_person.get('obituary_text', '')
                death_date = self.current_person.get('death_date')
                name = self.current_person.get('full_name')
                logging.info(f"Skip check: obituary_text present: {bool(text)}, death_date: {death_date}, name: {name}")
                # Skip if we have valid obituary text, death date, and name
                if (text and len(text) > 100 and 
                    any(indicator in text.lower() for indicator in [
                        'died', 'passed away', 'obituary', 'funeral',
                        'survived by', 'born', 'age'
                    ]) and
                    death_date and name):
                    logging.info(f"Skipping URL {url} - already has valid obituary text, death date, and name")
                    return self.current_person

            # Read the obituary text and extract name and location
            main_text, extracted_name, extracted_location = read_obituary(url, self.headers)
            if not main_text:
                raise Exception("Failed to extract main text from obituary")
                
            # Extract birth and death dates using DateNormalizer
            birth_date = DateNormalizer.find_birth_date(main_text)
            death_date = DateNormalizer.find_death_date(main_text)
            age = DateNormalizer.find_age(main_text)
            # If age and death_date are present but not birth_date, calculate birth_date
            if age and death_date and not birth_date:
                birth_date = DateNormalizer.calculate_birth_date(death_date, age)

            logging.info(f"Extracted birth_date: {birth_date}")
            logging.info(f"Extracted death_date: {death_date}")
            logging.info(f"Extracted age: {age}")
            
            location = extracted_location or self.extract_location(main_text)
            
            # Create the person dictionary
            person = {
                'url': url,
                'full_name': extracted_name or '',
                'location': location or '',
                'obituary_text': main_text,
                'id': get_next_individual_id(),
                'birth_date': birth_date,
                'death_date': death_date,
                'age': age
            }
            
            return person
            
        except Exception as e:
            logging.error(f"Error processing URL {url}: {str(e)}")
            return {
                'url': url,
                'full_name': '',
                'location': '',
                'obituary_text': '',
                'id': get_next_individual_id(),
                'birth_date': None,
                'death_date': None,
                'age': None
            }

    def extract_location(self, text: str) -> Optional[str]:
        """
        Extract location from the text.
        
        Args:
            text: The text to extract location from
            
        Returns:
            The extracted location or None if not found
        """
        # Look for location patterns
        location_match = re.search(r'(?:in|at)\s+([A-Z][a-zA-Z\s]+(?:,\s+[A-Z]{2})?)', text)
        if location_match:
            return location_match.group(1).strip()
        return None
        
    def process_file(self, force_refresh: bool = False) -> List[Dict]:
        """
        Process all URLs in the input file.
        
        Args:
            force_refresh: Whether to force a refresh of the data
            
        Returns:
            List of dictionaries containing the processed data
        """
        try:
            # Initialize the ID counter based on existing IDs in the file
            initialize_individual_id_counter(self.input_file)
            with open(self.input_file, 'r') as f:
                data = json.load(f)
                
            results = []
            for item in data:
                if 'url' in item:
                    self.current_person = item  # Set current person before processing
                    result = self.process_url(item['url'], force_refresh)
                    results.append(result)
                    
                    # If force_refresh is True, exit after processing the first URL
                    if force_refresh:
                        logging.info("Force refresh complete - exiting after processing one URL")
                        break
                    
            # Write results back to the input file
            with open(self.input_file, 'w') as f:
                json.dump(results, f, indent=2)
                
            return results
            
        except Exception as e:
            logging.error(f"Error processing file {self.input_file}: {str(e)}")
            return [] 
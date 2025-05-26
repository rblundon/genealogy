"""
ObituaryReader: A module for reading and processing obituaries from various sources.

This module provides functionality to read obituaries from URLs, extract relevant information,
and update person records with the extracted data.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from .date_normalizer import DateNormalizer
from .name_extractor import NameExtractor
from .obituary_utils import read_obituary
from genealogy.core.patterns import NAME_PATTERNS

class ObituaryReader:
    def __init__(self, input_file: str, output_file: str, refresh_obits: bool = False):
        """Initialize the ObituaryReader with input and output file paths."""
        self.input_file = input_file
        self.output_file = output_file
        self.refresh_obits = refresh_obits
        self.people = []
        self.processed_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.name_extractor = NameExtractor()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid and accessible."""
        if not url:
            return False
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def is_valid_obituary_text(self, text: str) -> bool:
        """Check if obituary text is valid and contains useful information."""
        if not text:
            return False
        # Check for minimum length and common obituary indicators
        return (
            len(text) > 100 and  # Minimum length
            any(indicator in text.lower() for indicator in [
                'died', 'passed away', 'obituary', 'funeral',
                'survived by', 'born', 'age'
            ])
        )

    def extract_fields(self, text: str, soup: Optional[BeautifulSoup] = None) -> Dict[str, Any]:
        """Extract relevant fields from obituary text."""
        fields = {}
        
        # Extract name and location using NameExtractor if soup is provided
        if soup:
            name, location = self.name_extractor.extract_from_title(soup)
            if name:
                fields['name'] = name
            if location:
                fields['location'] = location
            elif not name:
                name = self.name_extractor.extract_full_name(soup, text)
                if name:
                    fields['name'] = name
        
        # Extract death date
        death_date = DateNormalizer.find_death_date(text)
        if death_date:
            fields['death_date'] = death_date
            
        # Extract birth date
        birth_date = DateNormalizer.find_birth_date(text)
        if birth_date:
            fields['birth_date'] = birth_date
            
        # Extract age and calculate birth date if possible
        age = DateNormalizer.find_age(text)
        if age and death_date and not birth_date:
            birth_date = DateNormalizer.calculate_birth_date(death_date, age)
            if birth_date:
                fields['birth_date'] = birth_date
        
        return fields

    def process_person(self, person: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single person's obituary."""
        url = person.get('url')
        if not url:
            logging.info(f"Skipping {person.get('name', 'Unknown')} (ID: {person.get('id', 'N/A')}): No URL")
            self.skipped_count += 1
            return person

        # Check if we need to process this obituary
        if not self.refresh_obits and person.get('obituary_text'):
            if self.is_valid_obituary_text(person['obituary_text']):
                logging.info(f"Skipping {person.get('name', 'Unknown')} (ID: {person.get('id', 'N/A')}): Already processed")
                self.skipped_count += 1
                return person

        # Read and process obituary
        text = read_obituary(url, self.headers)
        if not text:
            logging.error(f"Failed to read obituary for {person.get('name', 'Unknown')} (ID: {person.get('id', 'N/A')})")
            self.error_count += 1
            return person

        # Get BeautifulSoup object for name extraction
        soup = BeautifulSoup(text, 'html.parser')

        # Update person with new information
        person['obituary_text'] = text
        fields = self.extract_fields(text, soup)
        person.update(fields)
        
        # Generate ID if not present
        if not person.get('id'):
            person['id'] = f"P{len(self.people) + 1:04d}"
        
        logging.info(f"Processed {person.get('name', 'Unknown')} (ID: {person.get('id', 'N/A')})")
        self.processed_count += 1
        return person

    def read_obituaries(self) -> None:
        """Read obituaries for all people in the input file."""
        try:
            # Read input file
            with open(self.input_file, 'r') as f:
                self.people = json.load(f)
                
            # Process each person
            self.people = [self.process_person(person) for person in self.people]
            
            # Save results to the output file
            with open(self.output_file, 'w') as f:
                json.dump(self.people, f, indent=2)
                
            # Log summary
            logging.info(f"\nProcessing complete:")
            logging.info(f"Total people: {len(self.people)}")
            logging.info(f"Processed: {self.processed_count}")
            logging.info(f"Skipped: {self.skipped_count}")
            logging.info(f"Errors: {self.error_count}")
            
        except Exception as e:
            logging.error(f"Error processing obituaries: {str(e)}")
            raise 
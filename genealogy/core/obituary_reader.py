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
from ..patterns import NAME_PATTERNS

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

    def read_obituary(self, url: str) -> Optional[str]:
        """Read obituary content from a URL."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text
            text = re.sub(r'\s+', ' ', text)
            return text
        except Exception as e:
            logging.error(f"Error reading obituary from {url}: {str(e)}")
            return None

    def extract_name_from_text(self, text: str) -> Optional[str]:
        """Extract name from obituary text."""
        # Try to find name from title pattern
        title_match = re.search(NAME_PATTERNS['title'], text)
        if title_match:
            return title_match.group(1)
        
        # If no title match, try to find name at the start of the text
        first_line = text.split('\n')[0]
        name_match = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', first_line)
        if name_match:
            return name_match.group(1)
        
        return None

    def extract_location_from_text(self, text: str) -> Optional[str]:
        """Extract location from obituary text."""
        location_match = re.search(NAME_PATTERNS['location'], text)
        if location_match:
            return location_match.group(1).strip()
        return None

    def extract_fields(self, text: str) -> Dict[str, Any]:
        """Extract relevant fields from obituary text."""
        fields = {}
        
        # Extract name
        name = self.extract_name_from_text(text)
        if name:
            fields['name'] = name
        
        # Extract location
        location = self.extract_location_from_text(text)
        if location:
            fields['location'] = location
        
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
        text = self.read_obituary(url)
        if not text:
            logging.error(f"Failed to read obituary for {person.get('name', 'Unknown')} (ID: {person.get('id', 'N/A')})")
            self.error_count += 1
            return person

        # Update person with new information
        person['obituary_text'] = text
        fields = self.extract_fields(text)
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
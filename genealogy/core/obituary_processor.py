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
from genealogy.core.patterns import (
    DEATH_PATTERNS, BIRTH_PATTERNS, AGE_PATTERNS, 
    LOCATION_PATTERNS, NAME_PATTERNS, GENDER_PATTERNS, SPOUSE_PATTERNS
)
from .name_extractor import NameExtractor
from .obituary_utils import read_obituary, get_next_individual_id, initialize_individual_id_counter, add_to_input_file
from .date_normalizer import DateNormalizer
from .name_parser import NameParser
from .relationship_extraction import extract_spouses_and_companions  # <-- Import from core module now
from .name_normalizer import NameNormalizer

class ObituaryProcessor:
    def __init__(self, input_file: Optional[str] = None):
        """Initialize the ObituaryProcessor with optional input file path."""
        self.input_file = input_file
        self.name_extractor = NameExtractor()
        self.name_parser = NameParser()  # Initialize name_parser
        self.name_normalizer = NameNormalizer()  # Initialize name_normalizer
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.current_person = None  # Track the current person being processed

    def determine_gender(self, text: str) -> Optional[str]:
        """
        Determine gender based on pronouns and relationship terms in the text.
        
        Args:
            text: The text to analyze
            
        Returns:
            'F' for female, 'M' for male, or None if cannot determine
        """
        text = text.lower()
        female_score = 0
        male_score = 0

        # If any maiden name pattern is found, boost female score
        maiden_name_found = False
        for maiden_pattern in NAME_PATTERNS['maiden_name']:
            if re.search(maiden_pattern, text, re.IGNORECASE):
                maiden_name_found = True
                female_score += 5  # Strong weight for maiden name
                break

        # Check strong indicators (weight: 3)
        for term in GENDER_PATTERNS['strong_female']:
            if term in text and term not in ['sister', 'sisters']:
                female_score += 3
        for term in GENDER_PATTERNS['strong_male']:
            if term in text and term not in ['brother', 'brothers']:
                male_score += 3

        # Check regular terms (weight: 1)
        for term in GENDER_PATTERNS['female_terms']:
            if not any(term in strong_term for strong_term in GENDER_PATTERNS['strong_female'] + GENDER_PATTERNS['strong_male']):
                count = text.count(term)
                female_score += count
        for term in GENDER_PATTERNS['male_terms']:
            if not any(term in strong_term for strong_term in GENDER_PATTERNS['strong_female'] + GENDER_PATTERNS['strong_male']):
                count = text.count(term)
                male_score += count

        # If scores are equal, use maiden name as tiebreaker
        if female_score == male_score:
            if maiden_name_found:
                return 'F'
            return None

        return 'F' if female_score > male_score else 'M'

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
            logging.info(f"read_obituary returned: extracted_name='{extracted_name}', extracted_location='{extracted_location}'")
            if not main_text:
                raise Exception("Failed to extract main text from obituary")
                
            # Determine gender
            gender = self.determine_gender(main_text)
            logging.info(f"Determined gender: {gender}")
                
            # Extract maiden name only if gender is female
            maiden_name = None
            if gender == 'F':
                # Only assign maiden name if the matched name is a substring of the extracted name or vice versa
                for maiden_pattern in NAME_PATTERNS['maiden_name']:
                    maiden_match = re.search(maiden_pattern, main_text)
                    if maiden_match:
                        logging.debug(f"Trying maiden pattern: {maiden_pattern}")
                        logging.debug(f"Matched groups: {maiden_match.groups()} (type: {type(maiden_match.groups())}), lastindex: {maiden_match.lastindex} (type: {type(maiden_match.lastindex)})")
                        try:
                            matched_name = maiden_match.group(1).strip().lower()
                            extracted_name_clean = (extracted_name or '').strip().lower()
                            logging.debug(f"matched_name: {matched_name}, extracted_name_clean: {extracted_name_clean}")
                            if matched_name and extracted_name_clean and (matched_name in extracted_name_clean or extracted_name_clean in matched_name):
                                # Only assign maiden_name if the group exists and is not None
                                if maiden_match.lastindex and maiden_match.lastindex <= len(maiden_match.groups()) and maiden_match.group(maiden_match.lastindex):
                                    maiden_name = maiden_match.group(maiden_match.lastindex)
                                    logging.debug(f"Extracted maiden_name (by lastindex): {maiden_name}")
                                else:
                                    maiden_name = None
                                break
                        except Exception as e:
                            logging.error(f"Error extracting maiden name group: {e}")
                            maiden_name = None
                            break
            
            # Find spouse and companion relationships using extract_spouses_and_companions
            spouse_name = None
            companion_name = None
            current_last_name = (extracted_name.split()[-1] if extracted_name and ' ' in extracted_name else None)
            relationships = extract_spouses_and_companions(main_text, current_last_name)
            for name, rel, _ in relationships:
                if rel == 'spouse' and not spouse_name:
                    spouse_name = name
                elif rel == 'companion' and not companion_name:
                    companion_name = name
            
            # Extract birth and death dates using DateNormalizer
            birth_date = DateNormalizer.find_birth_date(main_text)
            death_date = DateNormalizer.find_death_date(main_text)
            age = DateNormalizer.find_age(main_text)
            # If age and death_date are present but not birth_date, calculate birth_date
            if age and death_date and not birth_date:
                birth_date = DateNormalizer.calculate_birth_date(death_date, age)
            # If birth_date and death_date are present but age is null, calculate age
            if birth_date and death_date and not age:
                age = DateNormalizer.calculate_age(birth_date, death_date)

            logging.info(f"Extracted birth_date: {birth_date}")
            logging.info(f"Extracted death_date: {death_date}")
            logging.info(f"Extracted age: {age}")
            
            location = extracted_location or self.extract_location(main_text)
            logging.info(f"Final location used: '{location}'")
            
            # Parse the extracted name to handle variations
            logging.debug(f"About to parse extracted_name: {extracted_name!r} (type: {type(extracted_name)})")
            if not extracted_name or not isinstance(extracted_name, str):
                logging.error(f"Invalid extracted_name: {extracted_name!r} (type: {type(extracted_name)})")
                raise ValueError("extracted_name must be a non-empty string")
            parsed_name = self.name_parser.parse_name(extracted_name)
            logging.debug(f"Parsed name result: {parsed_name!r} (type: {type(parsed_name)})")
            first_name = parsed_name.first_name
            last_name = parsed_name.last_name
            middle_name = parsed_name.middle_name
            middle_names_str = middle_name if middle_name else ''
            suffix = parsed_name.suffix
            nickname = parsed_name.nickname
            maiden_name = parsed_name.maiden_name if hasattr(parsed_name, 'maiden_name') else None

            # Normalize first and last names
            canonical_first, canonical_last = self.name_normalizer.normalize_name(first_name, last_name)

            # Debug log the values and types before constructing the person dictionary
            logging.debug(f"canonical_first: {canonical_first!r} (type: {type(canonical_first)})")
            logging.debug(f"canonical_last: {canonical_last!r} (type: {type(canonical_last)})")
            logging.debug(f"middle_names_str: {middle_names_str!r} (type: {type(middle_names_str)})")
            logging.debug(f"suffix: {suffix!r} (type: {type(suffix)})")
            logging.debug(f"nickname: {nickname!r} (type: {type(nickname)})")
            logging.debug(f"maiden_name: {maiden_name!r} (type: {type(maiden_name)})")

            # Create the person dictionary
            try:
                person = {
                    'url': url,
                    'full_name': extracted_name or '',
                    'location': location or '',
                    'obituary_text': main_text,
                    'id': get_next_individual_id(),
                    'birth_date': birth_date,
                    'death_date': death_date,
                    'age': age,
                    'gender': gender,
                    'spouse': spouse_name,
                    'companion': companion_name,
                    'first_name': canonical_first,
                    'last_name': canonical_last,
                    'middle_names': middle_names_str,
                    'suffix': suffix,
                    'nickname': nickname,
                    'maiden_name': maiden_name
                }
            except Exception as e:
                logging.error(f"Exception constructing person dictionary: {e}")
                logging.error(f"url: {url!r} (type: {type(url)})")
                logging.error(f"extracted_name: {extracted_name!r} (type: {type(extracted_name)})")
                logging.error(f"location: {location!r} (type: {type(location)})")
                logging.error(f"main_text: {main_text!r} (type: {type(main_text)})")
                logging.error(f"birth_date: {birth_date!r} (type: {type(birth_date)})")
                logging.error(f"death_date: {death_date!r} (type: {type(death_date)})")
                logging.error(f"age: {age!r} (type: {type(age)})")
                logging.error(f"gender: {gender!r} (type: {type(gender)})")
                logging.error(f"spouse_name: {spouse_name!r} (type: {type(spouse_name)})")
                logging.error(f"companion_name: {companion_name!r} (type: {type(companion_name)})")
                logging.error(f"canonical_first: {canonical_first!r} (type: {type(canonical_first)})")
                logging.error(f"canonical_last: {canonical_last!r} (type: {type(canonical_last)})")
                logging.error(f"middle_names_str: {middle_names_str!r} (type: {type(middle_names_str)})")
                logging.error(f"suffix: {suffix!r} (type: {type(suffix)})")
                logging.error(f"nickname: {nickname!r} (type: {type(nickname)})")
                logging.error(f"maiden_name: {maiden_name!r} (type: {type(maiden_name)})")
                raise
            
            # If force_refresh is True, update only the fields instead of creating a new person
            if force_refresh and self.current_person:
                self.current_person.update({
                    'obituary_text': main_text,
                    'birth_date': birth_date,
                    'death_date': death_date,
                    'age': age,
                    'gender': gender,
                    'spouse': spouse_name,
                    'companion': companion_name
                })
                if maiden_name:
                    self.current_person['maiden_name'] = maiden_name
                return self.current_person
            
            return person
            
        except Exception as e:
            import sys
            import traceback
            logging.error(f"Exception in process_url: {e}")
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
            logging.error(f"Traceback:\\n{tb_str}")
            # Log all local variables
            for var_name, var_val in locals().items():
                logging.error(f"{var_name}: {var_val!r} (type: {type(var_val)})")
            raise

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
        if not self.input_file:
            logging.error("No input file specified")
            return []
            
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
                    # Preserve the original ID if force_refresh is True
                    if force_refresh and 'id' in item:
                        result['id'] = item['id']
                    results.append(result)
                else:
                    # If the item does not have a URL, keep it unchanged
                    results.append(item)
                    
            # Write results back to the input file
            with open(self.input_file, 'w') as f:
                json.dump(results, f, indent=2)
                
            return results
            
        except Exception as e:
            logging.error(f"Error processing file {self.input_file}: {str(e)}")
            return [] 
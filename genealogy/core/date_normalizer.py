"""
DateNormalizer: A class for normalizing dates in obituary text.
"""

import re
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
from .patterns import DEATH_PATTERNS, BIRTH_PATTERNS, AGE_PATTERNS

class DateNormalizer:
    # List of common date formats to try
    DATE_FORMATS = [
        '%d %B %Y',  # 15 January 2020
        '%B %d %Y',  # January 15 2020
        '%d %B, %Y',  # 15 January, 2020
        '%B %d, %Y',  # January 15, 2020
        '%d %b %Y',   # 15 Jan 2020
        '%d %b, %Y',  # 15 Jan, 2020
        '%Y-%m-%d',  # 2020-01-15
        '%m/%d/%Y',  # 01/15/2020
        '%d/%m/%Y',  # 15/01/2020
        '%Y'  # 2020
    ]

    @staticmethod
    def parse_date(date_str: str) -> Optional[str]:
        """Parse a date string into a standard format."""
        if not date_str:
            print("parse_date: input is None or empty")
            return None
        # Remove ordinal suffixes (st, nd, rd, th) from day numbers
        date_str = re.sub(r'(\d{1,2})(st|nd|rd|th)', r'\1', date_str)
        # Remove extra whitespace and commas
        date_str = date_str.replace(',', '').strip()
        print(f"parse_date: trying to parse '{date_str}'")
        # Try each date format
        for fmt in DateNormalizer.DATE_FORMATS:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                print(f"parse_date: matched format '{fmt}'")
                return date_obj.strftime('%d %b %Y')
            except ValueError:
                continue
        print(f"parse_date: no format matched for '{date_str}'")
        return None

    @staticmethod
    def normalize_existing_dates(people: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize existing birth and death date fields in a list of people."""
        for person in people:
            if 'birth_date' in person:
                person['birth_date'] = DateNormalizer.parse_date(person['birth_date'])
            if 'death_date' in person:
                person['death_date'] = DateNormalizer.parse_date(person['death_date'])
        return people

    @staticmethod
    def extract_death_date_and_age(text: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract death date and age from text."""
        if not text:
            return None, None
            
        death_date = None
        age = None
        
        # Try each death date pattern
        for pattern in DEATH_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract the date part
                date_str = match.group(1)
                death_date = DateNormalizer.parse_date(date_str)
                if death_date:
                    break
                    
        # Try each age pattern
        for pattern in AGE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    age = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
                    
        return death_date, age

    @staticmethod
    def find_death_date(text: str) -> Optional[str]:
        """Find death date in text."""
        if not text:
            print("find_death_date: input is None or empty")
            return None
        for pattern in DEATH_PATTERNS:
            print(f"find_death_date: trying pattern '{pattern}'")
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                print(f"find_death_date: matched '{date_str}'")
                return DateNormalizer.parse_date(date_str)
        print("find_death_date: no pattern matched")
        return None

    @staticmethod
    def find_birth_date(text: str) -> Optional[str]:
        """Find birth date in text."""
        if not text:
            print("find_birth_date: input is None or empty")
            return None
        for pattern in BIRTH_PATTERNS:
            print(f"find_birth_date: trying pattern '{pattern}'")
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                print(f"find_birth_date: matched '{date_str}'")
                return DateNormalizer.parse_date(date_str)
        print("find_birth_date: no pattern matched")
        return None

    @staticmethod
    def find_age(text: str) -> Optional[int]:
        """Find age in text."""
        if not text:
            return None
            
        # Try each age pattern
        for pattern in AGE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
                    
        return None

    @staticmethod
    def calculate_birth_date(death_date: str, age: int) -> Optional[str]:
        """Calculate birth date from death date and age."""
        if not death_date or not age:
            return None
            
        try:
            death = datetime.strptime(death_date, '%d %b %Y')
            birth = death.replace(year=death.year - age)
            return birth.strftime('%d %b %Y')
        except (ValueError, TypeError):
            return None

    @staticmethod
    def calculate_age(birth_date: str, death_date: str) -> Optional[int]:
        """Calculate age from birth and death dates."""
        if not birth_date or not death_date:
            return None
            
        try:
            birth = datetime.strptime(birth_date, '%d %b %Y')
            death = datetime.strptime(death_date, '%d %b %Y')
            age = death.year - birth.year
            if (death.month, death.day) < (birth.month, birth.day):
                age -= 1
            return age
        except (ValueError, TypeError):
            return None 
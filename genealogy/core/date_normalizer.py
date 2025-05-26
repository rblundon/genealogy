"""
DateNormalizer: A module for normalizing and parsing dates in various formats.

This module provides functionality to parse dates from strings, normalize them to a standard format,
and calculate dates based on age and death dates.
"""

from datetime import datetime
import re
from typing import Optional, List, Dict, Any
from genealogy.core.patterns import DEATH_PATTERNS, BIRTH_PATTERNS, AGE_PATTERNS
import logging

class DateNormalizer:
    @staticmethod
    def parse_date(date_str: str) -> Optional[str]:
        """Convert various date formats to a standardized format (dd mmm yyyy)."""
        if not date_str:
            return None
        
        # Remove ordinal indicators (st, nd, rd, th)
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        # Remove commas
        date_str = date_str.replace(',', '')
        # Normalize whitespace
        date_str = ' '.join(date_str.split())
        print(f"Trying to parse date string: '{date_str}'")
        
        # List of common date formats to try
        formats = [
            '%d %b %Y',  # 15 Jan 2020
            '%b %d %Y',  # Jan 15 2020
            '%B %d %Y',  # January 15 2020
            '%Y-%m-%d',  # 2020-01-15
            '%m/%d/%Y',  # 01/15/2020
            '%d/%m/%Y',  # 15/01/2020
            '%Y',        # 2020
        ]
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str.strip(), fmt)
                return date_obj.strftime('%d %b %Y')
            except ValueError:
                continue
        return None

    @classmethod
    def normalize_existing_dates(cls, people: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize existing birth_date and death_date fields in a list of people."""
        for person in people:
            if 'birth_date' in person:
                person['birth_date'] = cls.parse_date(person['birth_date'])
            if 'death_date' in person:
                person['death_date'] = cls.parse_date(person['death_date'])
        return people

    @staticmethod
    def extract_death_date_and_age(text: str) -> (Optional[str], Optional[int]):
        """Extract both death date and age from text using patterns from patterns.py."""
        from genealogy.core.patterns import DEATH_PATTERNS  # Ensure up-to-date import
        print(f"DEATH_PATTERNS at runtime: {DEATH_PATTERNS}")
        text = ' '.join(text.split())
        print(f"extract_death_date_and_age input text: {repr(text)}")
        for pattern in DEATH_PATTERNS:
            print(f"Trying death date pattern: {pattern}")
            # Print all matches for this pattern
            all_matches = list(re.finditer(pattern, text, re.IGNORECASE | re.DOTALL))
            if all_matches:
                print(f"All matches for pattern: {[m.group(0) for m in all_matches]}")
            else:
                print("No matches found for this pattern.")
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                groups = match.groups()
                print(f"Matched groups for death date and age: {groups}")
                if len(groups) == 2:
                    date_str, age_str = groups
                    print(f"Matched date substring: '{date_str}', age substring: '{age_str}'")
                    date = DateNormalizer.parse_date(date_str)
                    try:
                        age = int(age_str)
                    except (ValueError, TypeError):
                        age = None
                    return date, age
                elif len(groups) == 1:
                    print(f"Matched date substring: '{groups[0]}'")
                    date = DateNormalizer.parse_date(groups[0])
                    return date, None
        return None, None

    @staticmethod
    def find_death_date(text: str) -> Optional[str]:
        date, _ = DateNormalizer.extract_death_date_and_age(text)
        return date

    @staticmethod
    def find_birth_date(text: str) -> Optional[str]:
        """
        Find birth date in the text.
        
        Args:
            text: The text to search
            
        Returns:
            The birth date if found, None otherwise
        """
        for pattern in BIRTH_PATTERNS:
            print(f"Trying birth date pattern: {pattern}")
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                print(f"Matched birth date pattern: {pattern} with group: {match.group(1)}")
                try:
                    date_str = match.group(1)
                    # If it's just a year, convert to January 1st of that year
                    if re.match(r'^\d{4}$', date_str):
                        date_str = f"01 Jan {date_str}"
                    return DateNormalizer.parse_date(date_str)
                except (ValueError, IndexError):
                    continue
        print("No birth date pattern matched.")
        return None

    @staticmethod
    def calculate_age_from_dates(birth_date: str, death_date: str) -> Optional[int]:
        """
        Calculate age from birth and death dates.
        
        Args:
            birth_date: Birth date in format 'DD MMM YYYY'
            death_date: Death date in format 'DD MMM YYYY'
            
        Returns:
            Calculated age or None if dates are invalid
        """
        try:
            birth = datetime.strptime(birth_date, '%d %b %Y')
            death = datetime.strptime(death_date, '%d %b %Y')
            age = death.year - birth.year
            # Adjust age if birthday hasn't occurred in death year
            if (death.month, death.day) < (birth.month, birth.day):
                age -= 1
            return age
        except (ValueError, TypeError):
            return None

    @staticmethod
    def find_age(text: str) -> Optional[int]:
        """
        Find age in the text.
        
        Args:
            text: The text to search
            
        Returns:
            The age if found, None otherwise
        """
        # First try to find age from death date pattern
        death_date, age = DateNormalizer.extract_death_date_and_age(text)
        if age:
            return int(age)
        
        # Then try age patterns
        for pattern in AGE_PATTERNS:
            print(f"Trying age pattern: {pattern}")
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                print(f"Matched age pattern: {pattern} with group: {match.group(1)}")
                try:
                    age_str = match.group(1)
                    return int(age_str)
                except (ValueError, IndexError):
                    continue
        print("No age pattern matched.")
        # If no age found, try to calculate from birth and death dates
        birth_date = DateNormalizer.find_birth_date(text)
        death_date = DateNormalizer.find_death_date(text)
        if birth_date and death_date:
            calculated_age = DateNormalizer.calculate_age_from_dates(birth_date, death_date)
            if calculated_age is not None:
                logging.info(f"Calculated age {calculated_age} from birth date {birth_date} and death date {death_date}")
                return calculated_age
        return None

    @staticmethod
    def calculate_birth_date(death_date: str, age: int) -> Optional[str]:
        """Calculate birth date from death date and age. Returns only the year if calculated."""
        try:
            death = datetime.strptime(death_date, '%d %b %Y')
            # Subtract age from death date
            birth = death.replace(year=death.year - age)
            # Return only the year since this is a calculated date
            return str(birth.year)
        except (ValueError, TypeError):
            return None 
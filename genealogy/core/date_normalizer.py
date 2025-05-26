"""
DateNormalizer: A module for normalizing and parsing dates in various formats.

This module provides functionality to parse dates from strings, normalize them to a standard format,
and calculate dates based on age and death dates.
"""

from datetime import datetime
import re
from typing import Optional, List, Dict, Any
from genealogy.patterns import DEATH_PATTERNS, BIRTH_PATTERNS, AGE_PATTERNS

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
        
        # List of common date formats to try
        formats = [
            '%d %b %Y',  # 15 Jan 2020
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
    def find_death_date(text: str) -> Optional[str]:
        """Find death date in text using patterns from patterns.py."""
        for pattern in DEATH_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Try to find the first group that looks like a date
                for group in match.groups():
                    parsed = DateNormalizer.parse_date(group)
                    if parsed:
                        return parsed
        return None

    @staticmethod
    def find_birth_date(text: str) -> Optional[str]:
        """Find birth date in text using patterns from patterns.py."""
        for pattern in BIRTH_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                for group in match.groups():
                    parsed = DateNormalizer.parse_date(group)
                    if parsed:
                        return parsed
        return None

    @staticmethod
    def find_age(text: str) -> Optional[int]:
        """Find age in text using patterns from patterns.py."""
        for pattern in AGE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None

    @staticmethod
    def calculate_birth_date(death_date: str, age: int) -> Optional[str]:
        """Calculate birth date from death date and age."""
        try:
            death = datetime.strptime(death_date, '%d %b %Y')
            # Subtract age from death date
            birth = death.replace(year=death.year - age)
            return birth.strftime('%d %b %Y')
        except (ValueError, TypeError):
            return None 
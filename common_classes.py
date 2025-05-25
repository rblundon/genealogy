import logging
import re
from datetime import datetime
from patterns import DEATH_PATTERNS, BIRTH_PATTERNS, AGE_PATTERNS

logger = logging.getLogger(__name__)

class NameWeighting:
    def __init__(self, people):
        self.people = people
        self.last_name_counts = self._count_last_names()

    def _count_last_names(self):
        last_name_counts = {}
        for person in self.people.values():
            last_name_counts[person['last_name'].lower()] = last_name_counts.get(person['last_name'].lower(), 0) + 1
        return last_name_counts

    def correct_last_name(self, last_name, obituary_text=None):
        if obituary_text and last_name.lower() in obituary_text.lower():
            return last_name  # Use the last name as is if it's in the obituary
        if last_name.lower() in self.last_name_counts:
            most_frequent_last_name = max(self.last_name_counts.items(), key=lambda x: x[1])[0]
            # Only correct if the frequency difference is significant
            if self.last_name_counts[most_frequent_last_name] > self.last_name_counts[last_name.lower()] * 2:
                logger.info(f"Corrected last name '{last_name}' to '{most_frequent_last_name}' based on frequency.")
                return most_frequent_last_name
        return last_name 

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
    def find_death_date(cls, text: str) -> str:
        """Find death date in text using predefined patterns."""
        if not text:
            return None
            
        for pattern in DEATH_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                death_date = cls.parse_date(match.group(1))
                if death_date:
                    return death_date
        return None

    @classmethod
    def find_birth_date(cls, text: str) -> str:
        """Find birth date in text using predefined patterns."""
        if not text:
            return None
            
        for pattern in BIRTH_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Handle year-only dates
                if re.match(r'^\d{4}$', date_str):
                    return f"01 Jan {date_str}"
                birth_date = cls.parse_date(date_str)
                if birth_date:
                    return birth_date
        return None

    @classmethod
    def find_age(cls, text: str) -> int:
        """Find age in text using predefined patterns."""
        if not text:
            return None
            
        for pattern in AGE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None

    @classmethod
    def calculate_birth_date(cls, death_date: str, age: int) -> str:
        """Calculate birth date from death date and age."""
        if not death_date or not age:
            return None
            
        try:
            death_year = int(re.search(r'\d{4}', death_date).group())
            birth_year = death_year - age
            return f"01 Jan {birth_year}"
        except (ValueError, IndexError):
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
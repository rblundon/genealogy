from datetime import datetime
import re
from typing import Optional, Tuple

def extract_death_date(text: str) -> Optional[Tuple[datetime, int]]:
    """
    Extract death date and age from obituary text.
    Returns a tuple of (death_date, age) if found, None otherwise.
    
    Args:
        text (str): The obituary text to parse
        
    Returns:
        Optional[Tuple[datetime, int]]: Tuple of (death_date, age) if found, None otherwise
    """
    # Pattern to match "on [Month] [Day], [Year] at the age of [age] years"
    pattern = r"on\s+(\w+)\s+(\d{1,2}),\s+(\d{4})\s+at\s+the\s+age\s+of\s+(\d+)\s+years"
    
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        month, day, year, age = match.groups()
        try:
            # Convert month name to number
            month_num = datetime.strptime(month, "%B").month
            death_date = datetime(int(year), month_num, int(day))
            return death_date, int(age)
        except ValueError:
            return None
    
    return None

def parse_date_string(date_str: str) -> Optional[datetime]:
    """
    Parse a date string into a datetime object.
    Handles various date formats commonly found in obituaries.
    
    Args:
        date_str (str): The date string to parse
        
    Returns:
        Optional[datetime]: Parsed datetime object if successful, None otherwise
    """
    # Common date formats in obituaries
    formats = [
        "%B %d, %Y",  # May 24, 2018
        "%b %d, %Y",  # May 24, 2018
        "%m/%d/%Y",   # 05/24/2018
        "%Y-%m-%d",   # 2018-05-24
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None 
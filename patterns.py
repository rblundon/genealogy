"""
Regex patterns used across the application for extracting information from text.
"""

# Death date patterns
DEATH_PATTERNS = [
    r'passed away unexpectedly while mowing grass on (\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})',
    r'passed away on (\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})',
    r'died on (\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})',
    r'passed on (\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})',
    r'(\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4}) at the age of',
    r'(\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4}), age \d+',
    r'(\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})',
]

# Birth date patterns
BIRTH_PATTERNS = [
    r'born on (\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})',
    r'born (\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})',
    r'birth date: (\w+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})',
    r'born(?:\s+in)?\s+(\d{4})',  # Just the year
    r'born in (\d{4})',  # Alternative format for year-only
]

# Age patterns
AGE_PATTERNS = [
    r'age (\d+)(?:\s+years)?',
    r'aged (\d+)(?:\s+years)?',
    r'(\d+)(?:\s+years)? old',
]

# Name patterns
NAME_PATTERNS = {
    'title': r'^(.*?) Obituary',
    'location': r'- ([^-]+) - [^-]+Funeral Home',
    'maiden_name': r'(?:née|nee|maiden name|born)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    'nickname': r'(?:known as|nickname|called|")([^"]+)"',
}

# Relationship patterns
RELATIONSHIP_PATTERNS = {
    'spouse': [
        r'(?:married to|spouse|husband|wife)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:married)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
    'parent': [
        r'(?:son|daughter) of ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:father|mother) was ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
    'sibling': [
        r'(?:brother|sister) ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:siblings include|survived by siblings) ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
    'child': [
        r'(?:children include|survived by children) ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:son|daughter) ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
} 
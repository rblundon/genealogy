"""
Regex patterns used across the application for extracting information from text.
"""

# Death date patterns
DEATH_PATTERNS = [
    r'(\w+\s+\d{1,2},?\s*\d{4})\s+at\s+the\s+age\s+of\s+(\d+)\s+years',
    r'on\s+(\w+\s+\d{1,2},?\s*\d{4})\s+at\s+the\s+age\s+of\s+(\d+)\s+years',
    r'passed away on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'passed away.*on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'died on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'passed on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\s+at\s+the\s+age\s+of',
]

# Birth date patterns
BIRTH_PATTERNS = [
    r'born on (\d{1,2} [A-Za-z]+,? \d{4})',
    r'born on ([A-Za-z]+ \d{1,2},? \d{4})',
    r'born (\d{1,2} [A-Za-z]+,? \d{4})',
    r'born ([A-Za-z]+ \d{1,2},? \d{4})',
    r'Born ([A-Za-z]+ \d{1,2}(?:st|nd|rd|th)?,? \d{4})',
    r'birth date: (\d{1,2} [A-Za-z]+,? \d{4})',
    r'birth date: ([A-Za-z]+ \d{1,2},? \d{4})',
    r'(\d{1,2} [A-Za-z]+,? \d{4}) - Birth',
    r'([A-Za-z]+ \d{1,2},? \d{4}) - Birth',
]

# Age patterns
AGE_PATTERNS = [
    r'age (\d+)',
    r'aged (\d+)',
    r'(\d+) years old',
    r'(\d+) years of age',
]

# Name patterns
NAME_PATTERNS = {
    'title': r"^(?:In Memory of|In Loving Memory of|Obituary for|Remembering|Memorial for|Tribute to|Celebration of Life for)?\s*([A-Z][a-zA-Z\s\"\'\(\)\-]+?)(?:'s Obituary|'s Memorial|'s Tribute|'s Celebration of Life)?$",
    'location': r'- ([^-]+) - [^-]+Funeral Home',
    'maiden_name': r'(?:née|nee|maiden name|born|formerly)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)|\(née\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\)',
    'nickname': r'(?:known as|nickname|called)\s+"([^"]+)"|"([^"]+)"',
}

# Relationship patterns
RELATIONSHIP_PATTERNS = {
    'spouse': [
        r'(?:married to|spouse|husband|wife|partner)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*(?:\([^)]*\))?\s*(?:"[^"]*")?)',
        r'(?:married)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*(?:\([^)]*\))?\s*(?:"[^"]*")?)',
        r'(?:survived by|predeceased by)\s+(?:his|her)\s+(?:beloved\s+)?(?:husband|wife|spouse|partner)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
    'parent': [
        r'(?:son|daughter) of ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:father|mother) was ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:survived by|predeceased by)\s+(?:his|her)\s+(?:parents|father|mother)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:born to|raised by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
    'sibling': [
        r'(?:brother|sister)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:siblings include|survived by siblings)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:survived by|predeceased by)\s+(?:his|her)\s+(?:brothers|sisters|siblings)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:brother|sister)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:and|,)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
    'child': [
        r'(?:children include|survived by children)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:son|daughter)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:survived by|predeceased by)\s+(?:his|her)\s+(?:children|sons|daughters)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:children|sons|daughters)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:and|,)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
}

# Add location patterns
LOCATION_PATTERNS = [
    r'(?:of|from|in)\s+([A-Z][a-zA-Z\s,]+(?:County|City|State|Province|Country)?)',
    r'(?:resided|lived|passed away)\s+(?:in|at)\s+([A-Z][a-zA-Z\s,]+)',
    r'(?:location|place):\s+([A-Z][a-zA-Z\s,]+)',
    r'(?:funeral home|memorial service|service).*?([A-Z][a-zA-Z\s,]+(?:County|City|State|Province|Country)?)',
    r'(?:church|chapel).*?([A-Z][a-zA-Z\s,]+(?:County|City|State|Province|Country)?)'
] 
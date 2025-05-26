# Death date patterns
DEATH_PATTERNS = [
    r'died on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\s+at\s+the\s+age\s+of\s+(\d+)\s+years',
    r'passed away on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\s+at\s+the\s+age\s+of\s+(\d+)\s+years',
    r'passed away.*on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'passed away on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'died on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'passed on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\s+at\s+the\s+age\s+of',
    r'on\s+(\w+\s+\d{1,2},?\s*\d{4})\s+at\s+the\s+age\s+of\s+(\d+)\s+years',
]

# Age patterns
AGE_PATTERNS = [
    r'age of (\d+) years',
    r'Age of (\d+) years',
    r'at\s+the\s+age\s+of\s+(\d+)\s+years',
    r'age\s+(\d+)\s+years',
    r'age\s+(\d+)',
    r'age\s+of\s+(\d+)\s+years',
    r'aged\s+(\d+)',
    r'Age\s+(\d+)\s+at\s+time\s+of\s+death',
]

# Birth date patterns
BIRTH_PATTERNS = [
    r'Born in (\d{4})',
    r'born\s+in\s+(\d{4})',
    r'born\s+on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'born\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'birth\s+date:\s*(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
]

# Location patterns
LOCATION_PATTERNS = [
    r'(?:in|at)\s+([A-Z][a-zA-Z\s]+(?:,\s+[A-Z]{2})?)',
    r'(?:resided|lived|passed away|died)\s+(?:in|at)\s+([A-Z][a-zA-Z\s]+(?:,\s+[A-Z]{2})?)',
    r'(?:of|from)\s+([A-Z][a-zA-Z\s]+(?:,\s+[A-Z]{2})?)',
]

# Name patterns
NAME_PATTERNS = {
    'title': r'^(.*?)\s+Obituary',
    'maiden_name': r'\(NEE ([^)]+)\)|NEE ([A-Z][a-zA-Z\-]+)',
    'nickname': r'"([^"]+)"|\'([^\']+)\'',
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
        r'(?:his|her)?\s*brother\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?=\s+(?:and|,|who|that|which|also|$))\s+(?:and|,)?\s+(?:sister\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?=\s+(?:who|that|which|also|survive|$|\.|,))',
        r'(?:his|her)?\s*sister\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?=\s+(?:and|,|who|that|which|also|$))\s+(?:and|,)?\s+(?:brother\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?=\s+(?:who|that|which|also|survive|$|\.|,))',
        r'(?:his|her)?\s*brother\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?=\s+(?:and|,|who|that|which|also|survive|$|\.|,))',
        r'(?:his|her)?\s*sister\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?=\s+(?:and|,|who|that|which|also|survive|$|\.|,))',
        r'(?:siblings include|survived by siblings)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:survived by|predeceased by)\s+(?:his|her)\s+(?:brothers|sisters|siblings)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
    'child': [
        r'(?:children include|survived by children)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:son|daughter)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:survived by|predeceased by)\s+(?:his|her)\s+(?:children|sons|daughters)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:children|sons|daughters)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:and|,)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
} 
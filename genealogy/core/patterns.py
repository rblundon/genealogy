# Death date patterns
DEATH_PATTERNS = [
    r'passed away on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'died on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'passed on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\s+at\s+the\s+age\s+of',
    r'on\s+(\w+\s+\d{1,2},?\s*\d{4})\s+at\s+the\s+age\s+of\s+(\d+)\s+years',
]

# Age patterns
AGE_PATTERNS = [
    r'at\s+the\s+age\s+of\s+(\d+)\s+years',
    r'age\s+(\d+)\s+years',
    r'age\s+(\d+)',
]

# Birth date patterns
BIRTH_PATTERNS = [
    r'born\s+on\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'born\s+(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'birth\s+date:\s*(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})',
    r'born\s+in\s+(\d{4})',
] 
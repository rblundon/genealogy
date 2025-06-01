"""Regex patterns for obituary text processing."""

# Name patterns
NAME_PATTERNS = [
    # Pattern for "LastName, FirstName MiddleInitial. (NEE MaidenName)"
    r'([A-Za-z]+),\s+([A-Za-z\s]+\.?)\s+\(NEE\s+([A-Za-z]+)\)',
    # Pattern for "FirstName MiddleInitial. LastName (NEE MaidenName)"
    r'([A-Za-z\s]+\.?)\s+([A-Za-z]+)\s+\(NEE\s+([A-Za-z]+)\)',
    # Pattern for "LastName, FirstName MiddleInitial."
    r'([A-Za-z]+),\s+([A-Za-z\s]+\.?)',
    # Pattern for "FirstName MiddleInitial. LastName"
    r'([A-Za-z\s]+\.?)\s+([A-Za-z]+)',
]

# Gender patterns
GENDER_PATTERNS = {
    'female': [
        r'\b(she|her|hers)\b',
        r'\b(Mrs\.|Ms\.|Miss)\b',
        r'\b(daughter|sister|mother|grandmother|aunt)\b',
        r'\b(NEE|nee)\b'  # Maiden name indicator
    ],
    'male': [
        r'\b(he|him|his)\b',
        r'\b(Mr\.|Sir)\b',
        r'\b(son|brother|father|grandfather|uncle)\b'
    ]
}

# Age patterns
AGE_PATTERNS = [
    r'at the age of (\d+) years?',
    r'aged (\d+)',
    r'(\d+) years? old',
    r'(\d+), of'  # Common pattern: "John Smith, 85, of..."
]

# Death date patterns (prioritized)
DEATH_DATE_PATTERNS = [
    # Format: died on January 1, 2020
    (r'died\s+on\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})', 1, True),
    # Format: passed away on January 1, 2020
    (r'passed\s+away\s+on\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})', 1, True),
    # Format: died January 1, 2020
    (r'died\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})', 1, True),
    # Format: passed away January 1, 2020
    (r'passed\s+away\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})', 1, True),
    # Format: died on 01/01/2020
    (r'died\s+on\s+(\d{1,2}/\d{1,2}/\d{4})', 1, True),
    # Format: passed away on 01/01/2020
    (r'passed\s+away\s+on\s+(\d{1,2}/\d{1,2}/\d{4})', 1, True),
    # Format: died 01/01/2020
    (r'died\s+(\d{1,2}/\d{1,2}/\d{4})', 1, True),
    # Format: passed away 01/01/2020
    (r'passed\s+away\s+(\d{1,2}/\d{1,2}/\d{4})', 1, True),
    # Format: died on 01-01-2020
    (r'died\s+on\s+(\d{1,2}-\d{1,2}-\d{4})', 1, True),
    # Format: passed away on 01-01-2020
    (r'passed\s+away\s+on\s+(\d{1,2}-\d{1,2}-\d{4})', 1, True),
    # Format: died 01-01-2020
    (r'died\s+(\d{1,2}-\d{1,2}-\d{4})', 1, True),
    # Format: passed away 01-01-2020
    (r'passed\s+away\s+(\d{1,2}-\d{1,2}-\d{4})', 1, True),
    # Format: died in 2020
    (r'died\s+in\s+(\d{4})', 1, False),
    # Format: passed away in 2020
    (r'passed\s+away\s+in\s+(\d{4})', 1, False),
]

# Date range patterns
DATE_RANGE_PATTERNS = [
    # Format: (01 Jan 1920 - 01 Jan 2020)
    (r'\((\d{2}\s+[A-Za-z]{3}\s+\d{4})\s*-\s*(\d{2}\s+[A-Za-z]{3}\s+\d{4})\)', 2, True),
    # Format: (01/01/1920 - 01/01/2020)
    (r'\((\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})\)', 2, True),
    # Format: (01-01-1920 - 01-01-2020)
    (r'\((\d{1,2}-\d{1,2}-\d{4})\s*-\s*(\d{1,2}-\d{1,2}-\d{4})\)', 2, True),
    # Format: (01 Jan 1920)
    (r'\((\d{2}\s+[A-Za-z]{3}\s+\d{4})\)', 1, True),
    # Format: (01/01/1920)
    (r'\((\d{1,2}/\d{1,2}/\d{4})\)', 1, True),
    # Format: (01-01-1920)
    (r'\((\d{1,2}-\d{1,2}-\d{4})\)', 1, True),
]

# Address patterns
ADDRESS_PATTERNS = [
    r'\b(street|st\.|avenue|ave\.|road|rd\.|boulevard|blvd\.|drive|dr\.|lane|ln\.|place|pl\.|court|ct\.|terrace|ter\.|circle|cir\.|way)\b',
    r'\b(north|south|east|west|n\.|s\.|e\.|w\.)\b',
    r'\b(apartment|apt\.|suite|ste\.|unit|floor|fl\.)\b',
    r'\b(zip|zipcode|postal code)\b',
    r'\b(po box|p\.o\. box)\b',
]

# Service patterns
SERVICE_PATTERNS = [
    r'\b(visitation|viewing|wake|funeral|service|mass|burial|interment|memorial)\b',
    r'\b(church|chapel|cemetery|funeral home)\b',
    r'\b(am|pm|morning|afternoon|evening)\b',
]

# Address date patterns
ADDRESS_DATE_PATTERNS = [
    r'\d+\s+[A-Za-z\s]+' + r'\d{4}',  # "123 Main Street 2020"
    r'\d{4}' + r'\s+[A-Za-z\s]+',     # "2020 Main Street"
] 
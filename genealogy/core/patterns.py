"""
Patterns for extracting information from obituary text.
"""

# Death date patterns
DEATH_PATTERNS = [
    r'died on\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})\s+at\s+the\s+age\s+of\s+(\d+)\s+years',
    r'died on\s+(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})',
    r'passed away on\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})\s+at\s+the\s+age\s+of\s+(\d+)\s+years',
    r'passed away on\s+(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})',
    r'passed away.*on\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})',
    r'passed away.*on\s+(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})',
    r'passed away on\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})',
    r'passed away on\s+(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})',
    r'died on\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})',
    r'died on\s+(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})',
    r'passed on\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})',
    r'passed on\s+(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})',
    r'death on\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})',
    r'death on\s+(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})',
    r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})\s+at\s+the\s+age\s+of',
    r'(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})\s+at\s+the\s+age\s+of',
    r'on\s+([A-Za-z]+\s+\d{1,2},?\s*\d{4})\s+at\s+the\s+age\s+of\s+(\d+)\s+years',
    r'on\s+(\d{1,2}\s+[A-Za-z]+,?\s*\d{4})\s+at\s+the\s+age\s+of\s+(\d+)\s+years',
    r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})\s*-\s*Death',
    r'(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})\s*-\s*Death',
    r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})\s*-\s*Died',
    r'(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})\s*-\s*Died',
    r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})\s*-\s*Passed',
    r'(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})\s*-\s*Passed',
    r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})\s*-\s*Passed Away',
    r'(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})\s*-\s*Passed Away'
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
    r'(\d+)\s+years\s+old',
    r'(\d+)\s+years\s+of\s+age',
    r'(\d+)\s+years\s+at\s+death',
    r'(\d+)\s+years\s+at\s+time\s+of\s+death'
]

# Birth date patterns
BIRTH_PATTERNS = [
    r'Born in (\d{4})',
    r'born\s+in\s+(\d{4})',
    r'born\s+on\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})',
    r'born\s+on\s+(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})',
    r'born\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})',
    r'born\s+(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})',
    r'birth\s+date:\s*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})',
    r'birth\s+date:\s*(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})',
    r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})\s*-\s*Birth',
    r'(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})\s*-\s*Birth',
    r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})\s*-\s*Born',
    r'(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})\s*-\s*Born',
    r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s*\d{4})\s*-\s*Birth Date',
    r'(\d{1,2}\s+[A-Za-z]+[,]?\s*\d{4})\s*-\s*Birth Date'
]

# Location patterns
LOCATION_PATTERNS = [
    r'of\s+([^,]+?)(?:,|\.|$)',
    r'from\s+([^,]+?)(?:,|\.|$)',
    r'in\s+([^,]+?)(?:,|\.|$)',
    r'resided\s+in\s+([^,]+?)(?:,|\.|$)',
    r'lived\s+in\s+([^,]+?)(?:,|\.|$)',
    r'resident\s+of\s+([^,]+?)(?:,|\.|$)'
]

# Name extraction patterns
NAME_PATTERNS = {
    'title': [
        r'^(.*?)\s+Obituary\s*-\s*([^-]+?)(?:\s*-\s*[^-]+)?$',
        r'^(.*?)\s+Memorial\s*-\s*([^-]+?)(?:\s*-\s*[^-]+)?$',
        r'^(.*?)\s*-\s*([^-]+?)(?:\s*-\s*[^-]+)?$',
        r'^(.*?)\s+(?:Obituary|Memorial)\s*-\s*([^-]+?)\s*-\s*[^-]+$',
        r'^([^-]+?)\s*-\s*(.*?)\s+(?:Obituary|Memorial)$',
        r'^(.*?)\s+(?:Obituary|Memorial)$',
        r'^(.*?)\s*-\s*([^-]+?)$'
    ],
    'maiden_name': [
        r'(?:^|\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\(nee\s+([^)]+)\)',  # Name (nee Maiden)
        r'(?:^|\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\(née\s+([^)]+)\)',  # Name (née Maiden)
        r'(?:^|\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\(born\s+([^)]+)\)',  # Name (born Maiden)
        r'(?:^|\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\(formerly\s+([^)]+)\)',  # Name (formerly Maiden)
        r'(?:^|\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\(maiden\s+name\s+([^)]+)\)'  # Name (maiden name Maiden)
    ],
    'nickname': [
        r'"([^"]+)"',
        r"'([^']+)'",
        r'\(([^)]+)\)',
        r'known as ([^,\.]+)',
        r'called ([^,\.]+)'
    ],
    'full_name': [
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)\s+(?:passed away|died|was born|passed on|left us)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)\'s\s+(?:obituary|memorial|tribute)',
        r'(?:In Memory of|In Loving Memory of|Remembering)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:,|\.|$)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)\s+(?:passed|died|was born)',
        r'(?:The family of|The family announces the passing of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:,|\.|$)',
        r'(?:We announce the passing of|We are sad to announce the passing of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:,|\.|$)',
        r'(?:It is with great sadness that we announce the passing of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:,|\.|$)',
        r'(?:With heavy hearts, we announce the passing of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:,|\.|$)',
        r'(?:We are heartbroken to announce the passing of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:,|\.|$)',
        r'(?:It is with deep sorrow that we announce the passing of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:,|\.|$)'
    ],
    'location': [
        r'(?:at|in) ([A-Z][a-zA-Z .\'-]+,? [A-Z]{2,})',  # at/in City, State
        r'(?:at|in) ([A-Z][a-zA-Z .\'-]+)',             # at/in City or Place
        r'of ([A-Z][a-zA-Z .\'-]+,? [A-Z]{2,})',        # of City, State
        r'of ([A-Z][a-zA-Z .\'-]+)',                    # of City or Place
        r'([A-Z][a-zA-Z .\'-]+, [A-Z]{2,})'             # City, State
    ]
}

# Gender determination patterns
GENDER_PATTERNS = {
    'male': [
        r'\b(he|him|his)\b',
        r'\b(son|brother|father|husband|uncle|nephew|grandfather|grandson)\b',
        r'\b(Mr\.|Sir|Dr\.)\b',
        r'\b(man|gentleman|male)\b'
    ],
    'female': [
        r'\b(she|her|hers)\b',
        r'\b(daughter|sister|mother|wife|aunt|niece|grandmother|granddaughter)\b',
        r'\b(Mrs\.|Ms\.|Miss|Lady|Dr\.)\b',
        r'\b(woman|lady|female)\b'
    ],
    'strong_female': [
        'beloved wife', 'devoted mother', 'loving daughter', 'matriarch', 'grandmother', 'sister', 'aunt', 'niece', 'Ms.', 'Mrs.', 'Miss', 'Lady', 'matron'
    ],
    'strong_male': [
        'beloved husband', 'devoted father', 'loving son', 'patriarch', 'grandfather', 'brother', 'uncle', 'nephew', 'Mr.', 'Sir', 'gentleman'
    ],
    'female_terms': [
        'she', 'her', 'hers', 'woman', 'female', 'mother', 'daughter', 'wife', 'sister', 'aunt', 'niece', 'grandmother', 'granddaughter', 'Ms.', 'Mrs.', 'Miss', 'Lady'
    ],
    'male_terms': [
        'he', 'him', 'his', 'man', 'male', 'father', 'son', 'husband', 'brother', 'uncle', 'nephew', 'grandfather', 'grandson', 'Mr.', 'Sir'
    ]
}

# Relationship patterns
RELATIONSHIP_PATTERNS = {
    'spouse': [
        r'(?:wife|husband|spouse)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+and|\s*,|\s*\.|\s*$)',
        r'(?:married to|married)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+and|\s*,|\s*\.|\s*$)',
        r'reunited with\s+(?:her|his)\s+(?:husband|wife)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+and|\s*,|\s*\.|\s*$)',
        r'(?:preceded in death by|survived by)\s+(?:his|her)\s+(?:beloved )?(?:wife|husband|spouse)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+and|\s*,|\s*\.|\s*$)'
    ],
    'parent': [
        r'(?:father|mother)\s+of\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s+and|\s*,|\s*\.|\s*$)',
        r'(?:preceded in death by|survived by)\s+(?:his|her)\s+(?:beloved )?(?:father|mother)\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s+and|\s*,|\s*\.|\s*$)',
        r'(?:the late )?(?:father|mother)\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s+and|\s*,|\s*\.|\s*$)'
    ],
    'sibling': [
        # Pattern for "brother/sister First (Spouse) Last and brother/sister First (Spouse) Last"
        r'(?:his|her)?\s*(?:brother|sister)\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s+and\s+(?:brother|sister)\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?)?',
        
        # Pattern for "brothers/sisters First (Spouse) Last and First (Spouse) Last"
        r'(?:his|her)?\s*(?:brothers|sisters)\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s+and\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?)?',
        
        # Pattern for "survived by brother/sister First (Spouse) Last"
        r'survived by (?:his|her)?\s*(?:brother|sister)\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?',
        
        # Pattern for "survived by brothers/sisters First (Spouse) Last and First (Spouse) Last"
        r'survived by (?:his|her)?\s*(?:brothers|sisters)\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s+and\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?)?',
        
        # Pattern for "brother/sister of First (Spouse) Last"
        r'(?:brother|sister)\s+of\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?',
        
        # Pattern for "siblings include First (Spouse) Last and First (Spouse) Last"
        r'siblings include\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s+and\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?)?',
        
        # Pattern for "survived by siblings First (Spouse) Last and First (Spouse) Last"
        r'survived by siblings\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s+and\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?)?',
        
        # Pattern for complex listings with commas
        r'(?:survived by|preceded by)\s+(?:his|her)?\s*(?:brothers|sisters)\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s*,\s*(?:and\s+)?([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?)*',
        
        # Pattern for "survived by brothers First (Spouse) Last and First (Spouse) Last"
        r'survived by brothers\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s+and\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?)?'
    ],
    'child': [
        r'(?:son|daughter)\s+of\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s+and|\s*,|\s*\.|\s*$)',
        r'(?:preceded in death by|survived by)\s+(?:his|her)\s+(?:beloved )?(?:son|daughter)\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s+and|\s*,|\s*\.|\s*$)',
        r'(?:the late )?(?:son|daughter)\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:\s+and|\s*,|\s*\.|\s*$)',
        r'reunited with\s+(?:her|his)\s+(?:husband|wife)\s+[A-Z][a-z]+(?:\s+and|\s*,)\s+(?:son|daughter)\s+([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?(?:[^\w]|$)',
        r'(?:loving|beloved)\s+(?:father|mother)\s+of\s+(?:the late )?([A-Z][a-z]+)(?:\s+\(([^)]+)\))?(?:\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))?'
    ]
}

# Add spouse_patterns to the patterns.py file
SPOUSE_PATTERNS = [
    # Suffix pattern for names
    r'(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))',
    # Middle name/initial pattern
    r'(?: [A-Z](?:\.|[a-z]+)?)?',
    # Pattern for NEE format in parentheses
    r'([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))? \(NEE ([^)]+)\)',
    r'([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))? \(nee ([^)]+)\)',
    # Original patterns
    r'beloved (?:wife|husband|spouse) of ([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: \(nee ([^)]+)\))?',
    r'(?:wife|husband|spouse) ([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: \(nee ([^)]+)\))?',
    r'(?:married to|married) ([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: \(nee ([^)]+)\))?',
    r'(?:companion of|companion|partner of|partner) ([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: \(nee ([^)]+)\))?',
    r'([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))? \(companion\)(?: \(nee ([^)]+)\))?',
    r'Survived by ([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?, (?:his|her|their) constant companion(?: \(nee ([^)]+)\))?',
    # New patterns for better spouse detection
    r'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) ([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: \(nee ([^)]+)\))?',
    r'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) of ([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: \(nee ([^)]+)\))?',
    r'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) ([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))? and (?:their|his|her) children(?: \(nee ([^)]+)\))?',
    r'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) ([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))? and family(?: \(nee ([^)]+)\))?',
    # Pattern for single name spouses (will use current_last_name)
    r'(?:wife|husband|spouse) ([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)?)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: and|$)(?: \(nee ([^)]+)\))?',
    r'(?:married to|married) ([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)?)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: and|$)(?: \(nee ([^)]+)\))?',
    r'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) ([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)?)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: and|$)(?: \(nee ([^)]+)\))?',
    # Add pattern for "reunited with her/his husband/wife"
    r'reunited with (?:her|his) (?:husband|wife) ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+(?:and|,))',
    # Add pattern for first name only
    r'reunited with (?:her|his) (?:husband|wife) ([A-Z][a-z]+)',
    # Enhanced companion patterns
    r'(?:companion of|companion|partner of|partner)\s+([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?',
    r'([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))? \(companion\)',
    r'Survived by\s+([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?,\s+(?:his|her|their)\s+constant companion',
    r'(?:survived by|predeceased by)\s+([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?,\s+(?:his|her|their)\s+(?:constant|longtime|long-time)\s+companion',
    r'(?:survived by|predeceased by)\s+([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?,\s+(?:his|her|their)\s+companion\s+(?:and|,)',
    r'(?:survived by|predeceased by)\s+([A-Z][a-z]+(?: [A-Z](?:\.|[a-z]+)?)? [A-Z][a-z]+)(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?,\s+(?:his|her|their)\s+companion\s+(?:of|for)',
    r"reunited with (?:her|his) (?:husband|wife) ([A-Z][a-z]+)(?:\s+(?:and|,))"
]

# Context patterns for determining the living/deceased context of a sentence
CONTEXT_PATTERNS = {
    'deceased': [
        r'preceded by',
        r'reunited with',
    ],
    'alive': [
        r'survived by',
        r'married to',
    ]
} 
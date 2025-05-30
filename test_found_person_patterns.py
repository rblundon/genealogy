import re
from genealogy.core.patterns import RELATIONSHIP_PATTERNS

RELATION_LABELS = {
    'brother': 'siblings',
    'sister': 'siblings',
    'father': 'parents',
    'mother': 'parents',
    'son': 'children',
    'daughter': 'children'
}

def extract_all_relation_spouse_pairs(text):
    """Extract all relation-spouse pairs from text."""
    pairs = []
    deceased = set()
    deceased_context = False
    # Check for deceased context
    if 'reunited with' in text.lower():
        deceased_context = True
    # Check for deceased indicators
    deceased_indicators = ['the late', 'late', 'deceased', 'predeceased by']
    for indicator in deceased_indicators:
        if indicator in text.lower():
            # Find the next word after the indicator
            match = re.search(f'{indicator}\\s+([A-Z][a-z]+)', text, re.IGNORECASE)
            if match:
                deceased.add(match.group(1))
    # Always extract spouse in 'reunited with her/his husband/wife [Name]' pattern
    spouse_match = re.search(r'reunited with (?:her|his) (?:husband|wife) ([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*)', text, re.IGNORECASE)
    if spouse_match:
        spouse_name = spouse_match.group(1)
        pairs.append(('spouse', spouse_name, None, None, True))
    # Try each relationship type
    for rel_type, patterns in RELATIONSHIP_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                groups = match.groups()
                if not groups:
                    continue
                # Sibling/parent/child logic
                if rel_type in ('sibling', 'parent', 'child'):
                    # Try to extract all possible people from the groups
                    # (first, spouse, last, second_first, second_spouse, second_last)
                    # Accept single-name (first only) or first+last
                    def add_person(first, last, spouse, is_deceased):
                        if first and last:
                            pairs.append((rel_type, first, last, spouse, is_deceased))
                        elif first:
                            pairs.append((rel_type, first, None, spouse, is_deceased))
                    # First person
                    first = groups[0] if len(groups) > 0 else None
                    spouse = groups[1] if len(groups) > 1 else None
                    last = groups[2] if len(groups) > 2 else None
                    is_deceased = deceased_context or (first in deceased)
                    add_person(first, last, spouse, is_deceased)
                    # Second person (for patterns with multiple people)
                    if len(groups) > 3 and groups[3]:
                        second_first = groups[3]
                        second_spouse = groups[4] if len(groups) > 4 else None
                        second_last = groups[5] if len(groups) > 5 else last
                        is_deceased2 = deceased_context or (second_first in deceased)
                        add_person(second_first, second_last, second_spouse, is_deceased2)
    # Handle multiple children/relations in a single phrase (e.g. 'sons David and John')
    # Simple pattern for 'sons David and John' or 'daughters Alice and Mary'
    multi_child_pattern = r'(?:sons|daughters) ([A-Z][a-z]+)(?: and ([A-Z][a-z]+))?(?: and ([A-Z][a-z]+))?'
    if deceased_context:
        for match in re.finditer(multi_child_pattern, text):
            for i in range(1, 4):
                name = match.group(i)
                if name:
                    pairs.append(('child', name, None, None, True))
    # Handle "reunited with" context for multiple people/relationships
    reunited_general_pattern = r'reunited with ([^\n\.;]+)'
    match = re.search(reunited_general_pattern, text, re.IGNORECASE)
    if match:
        after_reunited = match.group(1)
        # Split by 'and' and commas
        parts = re.split(r'\s+and\s+|,', after_reunited)
        for part in parts:
            part = part.strip()
            # Match relationship and name(s)
            rel_name_match = re.match(r'(husband|wife|son|daughter|sons|daughters) ([A-Z][a-z]+(?: and [A-Z][a-z]+)*)', part)
            if rel_name_match:
                rel = rel_name_match.group(1)
                names = rel_name_match.group(2)
                # Handle multiple names (e.g., 'David and John')
                for name in re.split(r' and ', names):
                    name = name.strip()
                    if rel in ['son', 'daughter']:
                        pairs.append(('child', name, None, None, True))
                    elif rel in ['sons', 'daughters']:
                        pairs.append(('child', name, None, None, True))
                    elif rel in ['husband', 'wife']:
                        pairs.append(('spouse', name, None, None, True))
            else:
                # If no relationship, just add as deceased
                name_match = re.match(r'([A-Z][a-z]+)', part)
                if name_match:
                    name = name_match.group(1)
                    pairs.append(('unknown', name, None, None, True))
    return pairs

def extract_relationships(text):
    """Extract and structure relationships from text."""
    relationships = {
        'siblings': set(),
        'parents': set(),
        'children': set(),
        'spouses': set(),
        'deceased': set()
    }
    pairs = extract_all_relation_spouse_pairs(text)
    for rel_type, first, last, spouse, is_deceased in pairs:
        person = f"{first} {last}" if last else first
        # Add to appropriate relationship set
        if rel_type == 'sibling':
            relationships['siblings'].add(person)
        elif rel_type == 'parent':
            relationships['parents'].add(person)
        elif rel_type == 'child':
            relationships['children'].add(person)
        elif rel_type == 'spouse':
            relationships['spouses'].add(person)
        if is_deceased:
            relationships['deceased'].add(person)
        # Add spouse relationship if present
        if spouse:
            spouse_name = f"{spouse} {last}" if last else spouse
            relationships['spouses'].add(f"{person} is married to {spouse_name}")
            if is_deceased:
                relationships['deceased'].add(spouse_name)
    return relationships

def test_relation_patterns():
    test_cases = [
        # Sibling test cases
        "survived by brothers Reginald (Donna) Paradowski and Joseph (Rosemary) Paradowski",
        "survived by sister Jane (Bob) Johnson and brother Michael (Lisa) Williams",
        "sister Megan (Ross Wurz) Smith",
        # Parent test cases
        "father of John (Mary) Smith and mother of Alice (Robert) Smith",
        "survived by his beloved father William (Elizabeth) Brown and mother Alice (Robert) Smith",
        "preceded in death by his father John (Mary) Smith",
        # Child test cases
        "son of David (Emily) Brown and daughter of Sarah (Tom) Brown",
        "survived by his beloved son John (Mary) Smith",
        "preceded in death by his daughter Jane (Bob) Johnson",
        # Deceased context test cases
        "Reunited with her husband Terrence and daughter Patricia on May 24, 2018",
        "Reunited with her husband Terrence, sons David and John, and daughter Patricia",
        "Reunited with her daughter Megan (Ross) Wurz",
        # Deceased test cases
        "the late brother John (Mary) Smith",
        "predeceased by sister Jane (Bob) Johnson",
        "survived by the late father William (Elizabeth) Brown and mother Alice (Robert) Smith"
    ]
    for text in test_cases:
        print(f"\nTest case: {text}")
        relationships = extract_relationships(text)
        print("\nExtracted Relationships:")
        print(f"Siblings: {', '.join(relationships['siblings']) if relationships['siblings'] else 'None'}")
        print(f"Parents: {', '.join(relationships['parents']) if relationships['parents'] else 'None'}")
        print(f"Children: {', '.join(relationships['children']) if relationships['children'] else 'None'}")
        print("\nSpouse Relationships:")
        for spouse in relationships['spouses']:
            print(f"- {spouse}")
        if relationships['deceased']:
            print("\nDeceased Individuals:")
            for person in relationships['deceased']:
                print(f"- {person}")

if __name__ == "__main__":
    print("Testing generalized relation extraction (with deceased status):\n")
    test_relation_patterns() 
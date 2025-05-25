import json
import re
import argparse
from common_classes import NameWeighting
from name_normalizer import NameNormalizer
import gender_guesser.detector as gender
from typing import List, Tuple, Optional, Dict, Any

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_spouses_and_companions(obituary_text, current_last_name=None):
    """
    Extract spouse and companion names from obituary text.
    Returns a list of (name, relationship, maiden_name) tuples.
    """
    results = set()
    # Suffix pattern for names
    suffix_regex = r'(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))'
    # Middle name/initial pattern
    middle_regex = r'(?: [A-Z](?:\.|[a-z]+)?)?'

    # First, check for maiden name in the format "Last, First M. (NEE Maiden)"
    maiden_pattern = re.compile(r'([A-Z][a-z]+),\s+([A-Z][a-z]+)' + middle_regex + r'(?:{suffix_regex})?\s*\(NEE\s+([^)]+)\)', re.IGNORECASE)
    maiden_match = maiden_pattern.search(obituary_text)
    if maiden_match:
        last_name = maiden_match.group(1)
        first_name = maiden_match.group(2)
        # Try to get middle name/initial
        middle_name = None
        m = re.match(r'([A-Z][a-z]+),\s+([A-Z][a-z]+)(?: ([A-Z](?:\.|[a-z]+)?))?', maiden_match.group(0))
        if m and m.group(3):
            middle_name = m.group(3).strip()
        maiden_name = maiden_match.group(3)
        suffix = maiden_match.group(4) if len(maiden_match.groups()) > 3 else None
        full_name = f"{first_name}"
        if middle_name:
            full_name += f" {middle_name}"
        full_name += f" {last_name}"
        if suffix:
            full_name = f"{full_name} {suffix}"
        results.add((full_name, 'self', maiden_name))
        current_last_name = last_name

    # Spouse/companion patterns (now with optional middle name/initial)
    spouse_patterns = [
        # Pattern for NEE format in parentheses
        (rf'([A-Z][a-z]+{middle_regex} [A-Z][a-z]+)(?:{suffix_regex})? \(NEE ([^)]+)\)', 'spouse'),
        (rf'([A-Z][a-z]+{middle_regex} [A-Z][a-z]+)(?:{suffix_regex})? \(nee ([^)]+)\)', 'spouse'),
        # Original patterns
        (rf'beloved (?:wife|husband|spouse) of ([A-Z][a-z]+{middle_regex} [A-Z][a-z]+)(?:{suffix_regex})?(?: \(nee ([^)]+)\))?', 'spouse'),
        (rf'(?:wife|husband|spouse) ([A-Z][a-z]+{middle_regex} [A-Z][a-z]+)(?:{suffix_regex})?(?: \(nee ([^)]+)\))?', 'spouse'),
        (rf'(?:married to|married) ([A-Z][a-z]+{middle_regex} [A-Z][a-z]+)(?:{suffix_regex})?(?: \(nee ([^)]+)\))?', 'spouse'),
        (rf'(?:companion of|companion|partner of|partner) ([A-Z][a-z]+{middle_regex} [A-Z][a-z]+)(?:{suffix_regex})?(?: \(nee ([^)]+)\))?', 'companion'),
        (rf'([A-Z][a-z]+{middle_regex} [A-Z][a-z]+)(?:{suffix_regex})? \(companion\)(?: \(nee ([^)]+)\))?', 'companion'),
        (rf'Survived by ([A-Z][a-z]+{middle_regex} [A-Z][a-z]+)(?:{suffix_regex})?, (?:his|her|their) constant companion(?: \(nee ([^)]+)\))?', 'companion'),
        # New patterns for better spouse detection
        (rf'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) ([A-Z][a-z]+{middle_regex} [A-Z][a-z]+)(?:{suffix_regex})?(?: \(nee ([^)]+)\))?', 'spouse'),
        (rf'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) of ([A-Z][a-z]+{middle_regex} [A-Z][a-z]+)(?:{suffix_regex})?(?: \(nee ([^)]+)\))?', 'spouse'),
        (rf'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) ([A-Z][a-z]+{middle_regex} [A-Z][a-z]+)(?:{suffix_regex})? and (?:their|his|her) children(?: \(nee ([^)]+)\))?', 'spouse'),
        (rf'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) ([A-Z][a-z]+{middle_regex} [A-Z][a-z]+)(?:{suffix_regex})? and family(?: \(nee ([^)]+)\))?', 'spouse'),
        # Pattern for single name spouses (will use current_last_name)
        (rf'(?:wife|husband|spouse) ([A-Z][a-z]+{middle_regex})(?:{suffix_regex})?(?: and|$)(?: \(nee ([^)]+)\))?', 'spouse'),
        (rf'(?:married to|married) ([A-Z][a-z]+{middle_regex})(?:{suffix_regex})?(?: and|$)(?: \(nee ([^)]+)\))?', 'spouse'),
        (rf'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) ([A-Z][a-z]+{middle_regex})(?:{suffix_regex})?(?: and|$)(?: \(nee ([^)]+)\))?', 'spouse'),
    ]
    
    for pattern, relationship in spouse_patterns:
        for match in re.finditer(pattern, obituary_text, re.IGNORECASE):
            logger.debug(f"[SPOUSE] Pattern: {pattern}")
            logger.debug(f"[SPOUSE] Raw match: {match.group(0)} | Groups: {match.groups()} | Relationship: {relationship}")
            name = match.group(1)
            suffix = match.group(2) if len(match.groups()) > 1 else None
            maiden_name = match.group(3) if len(match.groups()) > 2 else None
            
            # Skip if name contains 'and' or other conjunctions
            if re.search(r'\b(and|or|but|with)\b', name, re.IGNORECASE):
                continue
                
            if suffix:
                name = f"{name} {suffix}"
            # Remove parenthetical content and extra whitespace
            clean = re.sub(r'\([^)]*\)', '', name).strip()
            # Handle 'nee' cases
            clean = re.sub(r'nee\s+[^,]+', '', clean).strip()
            # Handle titles
            clean = re.sub(r'^(?:Dr\.|Mr\.|Mrs\.|Ms\.|Rev\.|Fr\.)\s+', '', clean).strip()
            # Remove any trailing conjunctions
            clean = re.sub(r'\s+(?:and|or|but|with|,)$', '', clean, flags=re.IGNORECASE).strip()
            
            # If the name is just a first name and we have a current_last_name, use it
            if ' ' not in clean and current_last_name:
                clean = f"{clean} {current_last_name}"
            
            # Only consider if at least two words (likely a name)
            if len(clean.split()) >= 2:
                results.add((clean, relationship, maiden_name))
    return list(results)

def is_name_variation(name1: str, name2: str) -> bool:
    """Check if two names are variations of each other (e.g., with/without Jr.)"""
    # Remove common suffixes and normalize
    suffixes = ['jr', 'sr', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x']
    name1_norm = name1.lower()
    name2_norm = name2.lower()
    
    # Remove suffixes from both names
    for suffix in suffixes:
        name1_norm = name1_norm.replace(f', {suffix}', '').replace(f' {suffix}', '')
        name2_norm = name2_norm.replace(f', {suffix}', '').replace(f' {suffix}', '')
    
    # Compare normalized names
    return name1_norm == name2_norm

def get_more_complete_name(name1: str, name2: str) -> str:
    """Return the more complete version of two name variations."""
    # Check which name has more suffixes
    suffixes = ['jr', 'sr', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x']
    name1_suffixes = sum(1 for suffix in suffixes if f', {suffix}' in name1.lower() or f' {suffix}' in name1.lower())
    name2_suffixes = sum(1 for suffix in suffixes if f', {suffix}' in name2.lower() or f' {suffix}' in name2.lower())
    
    return name1 if name1_suffixes >= name2_suffixes else name2

def extract_family_names(obituary_text: str, current_last_name: str) -> List[Tuple[str, str]]:
    """Extract family names from obituary text."""
    results = set()
    relationships = {}  # Track relationships between people
    
    def add_name(name: str, rel: str):
        # Check if this name is a variation of an existing name
        for existing_name, existing_rel in list(results):
            if is_name_variation(name, existing_name):
                # If it's a variation, keep the more complete version
                more_complete = get_more_complete_name(name, existing_name)
                if more_complete != existing_name:
                    results.remove((existing_name, existing_rel))
                    results.add((more_complete, existing_rel))
                    # Update relationships if needed
                    if existing_name in relationships:
                        relationships[more_complete] = relationships.pop(existing_name)
                return
        # If no variation found, add the new name
        results.add((name, rel))
        # Initialize relationships for this person
        if name not in relationships:
            relationships[name] = set()
    
    def add_relationship(person1: str, person2: str, rel_type: str):
        """Add a bidirectional relationship between two people."""
        if person1 not in relationships:
            relationships[person1] = set()
        if person2 not in relationships:
            relationships[person2] = set()
        relationships[person1].add((person2, rel_type))
        # Add inverse relationship
        if rel_type == 'spouse':
            relationships[person2].add((person1, 'spouse'))
        elif rel_type == 'parent':
            relationships[person2].add((person1, 'child'))
        elif rel_type == 'child':
            relationships[person2].add((person1, 'parent'))
        elif rel_type == 'sibling':
            relationships[person2].add((person1, 'sibling'))
    
    # Extract spouses and companions
    for name, rel, maiden_name in extract_spouses_and_companions(obituary_text, current_last_name):
        logger.debug(f"[SPOUSE][MODULAR] Adding: {name} ({rel})")
        add_name(name, rel)
        if rel == 'spouse':
            add_relationship(name, current_last_name, 'spouse')
    
    # Extract parents
    for name, rel in extract_parents(obituary_text, current_last_name):
        logger.debug(f"[PARENT][MODULAR] Adding: {name} ({rel})")
        add_name(name, rel)
        if isinstance(rel, tuple) and rel[0] == 'spouse':
            # Handle parent's spouse
            add_relationship(name, rel[1], 'spouse')
        else:
            # Handle parent-child relationship
            add_relationship(name, current_last_name, 'parent')
    
    # Extract siblings
    siblings = []
    for name, rel in extract_siblings(obituary_text, current_last_name):
        logger.debug(f"[SIBLING][MODULAR] Adding: {name} ({rel})")
        add_name(name, rel)
        if isinstance(rel, tuple) and rel[0] == 'spouse':
            # Handle sibling's spouse
            add_relationship(name, rel[1], 'spouse')
        else:
            # Handle sibling relationship
            siblings.append(name)
            add_relationship(name, current_last_name, 'sibling')
    
    # Connect all siblings to each other
    for i, sibling1 in enumerate(siblings):
        for sibling2 in siblings[i+1:]:
            add_relationship(sibling1, sibling2, 'sibling')
    
    # Extract nieces and nephews
    for name, rel in extract_nieces_and_nephews(obituary_text, current_last_name):
        logger.debug(f"[NIECE/NEPHEW][MODULAR] Adding: {name} ({rel})")
        add_name(name, rel)
        if isinstance(rel, tuple) and rel[0] == 'spouse':
            add_relationship(name, rel[1], 'spouse')
    
    # Extract great nieces and nephews
    for name, rel in extract_great_nieces_and_nephews(obituary_text, current_last_name):
        logger.debug(f"[GREAT NIECE/NEPHEW][MODULAR] Adding: {name} ({rel})")
        add_name(name, rel)
        if isinstance(rel, tuple) and rel[0] == 'spouse':
            add_relationship(name, rel[1], 'spouse')
    
    # Extract children
    for child_name, rel, mother, father in extract_children_of_couples(obituary_text, current_last_name):
        logger.debug(f"[CHILD][MODULAR] Adding: {child_name} (child), mother: {mother}, father: {father}")
        add_name(child_name, 'child')
        if mother:
            add_name(mother, ('parent', child_name))
            add_relationship(mother, child_name, 'parent')
        if father:
            add_name(father, ('parent', child_name))
            add_relationship(father, child_name, 'parent')
    
    # Convert relationships to the final format
    final_results = list(results)
    for name, rels in relationships.items():
        for related_name, rel_type in rels:
            if (name, rel_type) not in final_results:
                final_results.append((name, rel_type))
    
    return final_results

def parse_name(full_name: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Parse a full name into its components."""
    # Remove any trailing conjunctions
    full_name = re.sub(r'\s+(?:and|&)\s*$', '', full_name)
    
    # Skip if name contains 'and' or other conjunctions in the middle
    if re.search(r'\b(and|or|but|with)\b', full_name, re.IGNORECASE):
        return None, None, None, None, None
    
    # Extract nickname if present
    nickname = None
    if '"' in full_name:
        match = re.search(r'"([^"]+)"', full_name)
        if match:
            nickname = match.group(1)
            full_name = full_name.replace(f'"{nickname}"', '').strip()
    elif '(' in full_name:
        match = re.search(r'\(([^)]+)\)', full_name)
        if match:
            nickname = match.group(1)
            full_name = full_name.replace(f'({nickname})', '').strip()
    elif ' aka ' in full_name.lower():
        parts = full_name.split(' aka ', 1)
        full_name = parts[0].strip()
        nickname = parts[1].strip()
    
    # Split on spaces and handle suffixes
    parts = full_name.split()
    if not parts:
        return None, None, None, None, None
        
    # Handle suffixes
    suffix = None
    if parts[-1].upper() in ['JR', 'SR', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']:
        suffix = parts[-1].upper()
        parts = parts[:-1]
    elif parts[-1].lower() in ['jr.', 'sr.']:
        suffix = parts[-1].lower()
        parts = parts[:-1]
    
    # Handle middle names/initials
    middle = None
    if len(parts) > 2:
        # Check if the middle part is an initial
        if len(parts[1]) == 1 or (len(parts[1]) == 2 and parts[1][1] == '.'):
            middle = parts[1]
            first = parts[0]
            last = ' '.join(parts[2:])
        else:
            # Assume it's a middle name
            first = parts[0]
            middle = parts[1]
            last = ' '.join(parts[2:])
    elif len(parts) == 2:
        first, last = parts
    else:
        return None, None, None, None, None
    
    # Clean up the names
    first = first.strip('.,')
    if middle:
        middle = middle.strip('.,')
    last = last.strip('.,')
    
    # Validate names
    if not first or not last or first.lower() in ['and', '&'] or last.lower() in ['and', '&']:
        return None, None, None, None, None
    
    # Skip if any part contains conjunctions
    invalid_words = ['and', 'or', 'but', 'with', 'the', 'a', 'an']
    if any(word.lower() in invalid_words for word in [first, middle, last] if word):
        return None, None, None, None, None
    
    return first, middle, last, suffix, nickname

def is_valid_name(first_name: str, last_name: str) -> bool:
    """Check if a name is valid."""
    if not first_name or not last_name:
        return False
    if len(first_name) < 2 or len(last_name) < 2:
        return False
    # Remove any trailing commas
    last_name = last_name.rstrip(',')
    if not last_name:
        return False
    # Check for invalid last names (conjunctions, etc.)
    invalid_last_names = ['and', 'or', 'but', 'with', 'the', 'a', 'an']
    if last_name.lower() in invalid_last_names:
        return False
    # Check for invalid first names (conjunctions, etc.)
    invalid_first_names = ['and', 'or', 'but', 'with', 'the', 'a', 'an']
    if first_name.lower() in invalid_first_names:
        return False
    return True

def extract_nieces_and_nephews(obituary_text, current_last_name=None):
    """
    Extract niece/nephew names (and their spouses) from obituary text.
    Returns a list of (name, relationship) tuples.
    """
    results = set()
    # Pattern: niece/nephew First (Spouse) Last
    pattern1 = re.compile(r'(?:niece|nephew) ([A-Z][a-z]+)(?: \(([^)]+)\))? ([A-Z][a-z]+)', re.IGNORECASE)
    for match in pattern1.finditer(obituary_text):
        niece_first = match.group(1)
        spouse_first = match.group(2)
        last = match.group(3)
        niece_full = f"{niece_first} {last}"
        if not any(niece_full in n for n, _ in results):
            results.add((niece_full, 'niece_nephew'))
        if spouse_first:
            spouse_full = f"{spouse_first} {last}"
            if not any(spouse_full in n for n, _ in results):
                results.add((spouse_full, ('spouse', niece_full)))
    # Fallback: niece/nephew FullName (with optional suffix)
    pattern2 = re.compile(r'(?:niece|nephew) ([A-Z][a-z]+(?: [A-Z][a-z]+)+(?:,? (?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?)', re.IGNORECASE)
    for match in pattern2.finditer(obituary_text):
        full_name = match.group(1).strip()
        # Only add if not already matched by the more specific pattern
        if not any(full_name in n for n, _ in results):
            results.add((full_name, 'niece_nephew'))
    return list(results)

def extract_parents(obituary_text, current_last_name=None):
    """
    Extract parent names (father, mother, or both) from obituary text.
    Returns a list of (name, relationship) tuples.
    """
    results = set()
    # Pattern: parents Father and Mother (nee Maiden)
    pattern1 = re.compile(r'(?:preceded in death by|survived by) (?:his|her|their) parents ([A-Z][a-z]+)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))? and ([A-Z][a-z]+)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: \(nee ([^)]+)\))?', re.IGNORECASE)
    for match in pattern1.finditer(obituary_text):
        father = match.group(1)
        mother = match.group(2)
        maiden = match.group(3)
        if father:
            father_full = f"{father} {current_last_name}"
            results.add((father_full, 'father'))
        if mother:
            if maiden:
                mother_full = f"{mother} {maiden}"
            else:
                mother_full = f"{mother} {current_last_name}"
            results.add((mother_full, 'mother'))
            # Add spouse relationship between parents
            if father:
                results.add((father_full, ('spouse', mother_full)))
                results.add((mother_full, ('spouse', father_full)))
    
    # Pattern: father Father
    pattern2 = re.compile(r'(?:preceded in death by|survived by) (?:his|her|their) father ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?', re.IGNORECASE)
    for match in pattern2.finditer(obituary_text):
        father = match.group(1)
        results.add((f"{father} {current_last_name}", 'father'))
    
    # Pattern: mother Mother (nee Maiden)
    pattern3 = re.compile(r'(?:preceded in death by|survived by) (?:his|her|their) mother ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: \(nee ([^)]+)\))?', re.IGNORECASE)
    for match in pattern3.finditer(obituary_text):
        mother = match.group(1)
        maiden = match.group(2)
        if maiden:
            results.add((f"{mother} {maiden}", 'mother'))
        else:
            results.add((f"{mother} {current_last_name}", 'mother'))
    
    # New patterns for better parent detection
    # Pattern: parents Father and Mother (nee Maiden) and their children
    pattern4 = re.compile(r'(?:preceded in death by|survived by) (?:his|her|their) parents ([A-Z][a-z]+)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))? and ([A-Z][a-z]+)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: \(nee ([^)]+)\))? and their children', re.IGNORECASE)
    for match in pattern4.finditer(obituary_text):
        father = match.group(1)
        mother = match.group(2)
        maiden = match.group(3)
        if father:
            father_full = f"{father} {current_last_name}"
            results.add((father_full, 'father'))
        if mother:
            if maiden:
                mother_full = f"{mother} {maiden}"
            else:
                mother_full = f"{mother} {current_last_name}"
            results.add((mother_full, 'mother'))
            # Add spouse relationship between parents
            if father:
                results.add((father_full, ('spouse', mother_full)))
                results.add((mother_full, ('spouse', father_full)))
    
    # Pattern: father Father and mother Mother (nee Maiden)
    pattern5 = re.compile(r'(?:preceded in death by|survived by) (?:his|her|their) father ([A-Z][a-z]+)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))? and mother ([A-Z][a-z]+)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: \(nee ([^)]+)\))?', re.IGNORECASE)
    for match in pattern5.finditer(obituary_text):
        father = match.group(1)
        mother = match.group(2)
        maiden = match.group(3)
        if father:
            father_full = f"{father} {current_last_name}"
            results.add((father_full, 'father'))
        if mother:
            if maiden:
                mother_full = f"{mother} {maiden}"
            else:
                mother_full = f"{mother} {current_last_name}"
            results.add((mother_full, 'mother'))
            # Add spouse relationship between parents
            if father:
                results.add((father_full, ('spouse', mother_full)))
                results.add((mother_full, ('spouse', father_full)))
    
    # Pattern: mother Mother (nee Maiden) and father Father
    pattern6 = re.compile(r'(?:preceded in death by|survived by) (?:his|her|their) mother ([A-Z][a-z]+)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?(?: \(nee ([^)]+)\))? and father ([A-Z][a-z]+)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?', re.IGNORECASE)
    for match in pattern6.finditer(obituary_text):
        mother = match.group(1)
        maiden = match.group(2)
        father = match.group(3)
        if mother:
            if maiden:
                mother_full = f"{mother} {maiden}"
            else:
                mother_full = f"{mother} {current_last_name}"
            results.add((mother_full, 'mother'))
        if father:
            father_full = f"{father} {current_last_name}"
            results.add((father_full, 'father'))
            # Add spouse relationship between parents
            if mother:
                results.add((father_full, ('spouse', mother_full)))
                results.add((mother_full, ('spouse', father_full)))
    
    return list(results)

def extract_siblings(obituary_text, current_last_name=None):
    """
    Extract sibling names (and their spouses) from obituary text.
    Returns a list of (name, relationship) tuples.
    """
    results = set()
    import logging
    logger = logging.getLogger(__name__)

    # Enhanced sibling patterns to catch more variations
    sibling_patterns = [
        # Pattern 1: his/her/their brother/sister First (Spouse) Last
        r'(?:his|her|their)\s+(brother|sister)\s+([A-Z][a-z]+)'  # relationship and first name
        r'(?:\s+\(([^)]+)\))?'  # optional spouse in parentheses
        r'(?:\s+([A-Z][a-z]+))?'  # optional last name
        r'(?:\s+([A-Z][a-z]+))?'  # optional second last name
        r'(?:\s+\(nee ([^)]+)\))?',  # optional maiden name
        
        # Pattern 2: brother/sister First (Spouse) Last
        r'(?:brother|sister)\s+([A-Z][a-z]+)'  # first name
        r'(?:\s+\(([^)]+)\))?'  # optional spouse in parentheses
        r'(?:\s+([A-Z][a-z]+))?'  # optional last name
        r'(?:\s+([A-Z][a-z]+))?'  # optional second last name
        r'(?:\s+\(nee ([^)]+)\))?',  # optional maiden name
        
        # Pattern 3: survived by brother/sister First (Spouse) Last
        r'survived by (?:his|her|their)?\s+(?:brother|sister)\s+([A-Z][a-z]+)'  # first name
        r'(?:\s+\(([^)]+)\))?'  # optional spouse in parentheses
        r'(?:\s+([A-Z][a-z]+))?'  # optional last name
        r'(?:\s+([A-Z][a-z]+))?'  # optional second last name
        r'(?:\s+\(nee ([^)]+)\))?',  # optional maiden name
    ]

    def clean_last(last):
        if last:
            # Remove trailing conjunctions like 'and', 'or', etc.
            return re.sub(r'\b(and|or|but|with|,)$', '', last, flags=re.IGNORECASE).strip()
        return last

    for pattern in sibling_patterns:
        for match in re.finditer(pattern, obituary_text, re.IGNORECASE | re.MULTILINE):
            groups = match.groups()
            logger.debug(f"[SIBLINGS] Pattern match: {match.group(0)} | groups: {groups}")
            
            # Extract components based on pattern
            if len(groups) == 6:  # Pattern 1
                rel, first, spouse, last1, last2, maiden = groups
            else:  # Pattern 2 or 3
                first, spouse, last1, last2, maiden = groups
                rel = None
            
            # Determine last name
            if maiden:
                last = maiden.strip()
            elif last2:
                last = f"{last1} {last2}".strip()
            elif last1:
                last = last1
            else:
                last = current_last_name
            last = clean_last(last)
            
            # Add sibling
            sibling_full = f"{first} {last}".strip()
            logger.debug(f"[SIBLINGS] Adding sibling: {sibling_full}")
            results.add((sibling_full, 'sibling'))
            
            # Add spouse if present
            if spouse:
                spouse_full = f"{spouse} {last}".strip()
                logger.debug(f"[SIBLINGS] Adding spouse: {spouse_full} (of {sibling_full})")
                results.add((spouse_full, ('spouse', sibling_full)))

    # Also look for sibling lists
    sibling_list_pattern = r'(?:brothers|sisters|siblings):\s*([^.]*?)(?:\.|$)'
    for match in re.finditer(sibling_list_pattern, obituary_text, re.IGNORECASE):
        siblings_text = match.group(1).strip()
        # Split on common separators
        sibling_names = re.split(r',\s*|\s+and\s+|\s*&\s*', siblings_text)
        for name in sibling_names:
            name = name.strip()
            if name:
                # Try to parse first and last name
                parts = name.split()
                if len(parts) >= 2:
                    first = parts[0]
                    last = parts[-1] if len(parts) > 1 else current_last_name
                    sibling_full = f"{first} {last}".strip()
                    logger.debug(f"[SIBLINGS] Adding sibling from list: {sibling_full}")
                    results.add((sibling_full, 'sibling'))

    logger.debug(f"[SIBLINGS] Final extracted siblings: {results}")
    return list(results)

def extract_great_nieces_and_nephews(obituary_text, current_last_name=None):
    """
    Extract great niece/nephew names (and their spouses) from obituary text.
    Returns a list of (name, relationship) tuples.
    """
    results = set()
    # Pattern: great niece/nephew First (Spouse) Last and family, and their father/mother Parent (Spouse) Last
    pattern1 = re.compile(r'(great niece|great nephew) ([A-Z][a-z]+)(?: \(([^)]+)\))? ([A-Z][a-z]+) and family, and their (father|mother) ([A-Z][a-z]+)(?: \(([^)]+)\))? ([A-Z][a-z]+)', re.IGNORECASE)
    for match in pattern1.finditer(obituary_text):
        rel_type = match.group(1).lower()
        great_niece_first = match.group(2)
        spouse_first = match.group(3)
        last = match.group(4)
        parent_type = match.group(5).lower()
        parent_first = match.group(6)
        parent_spouse_first = match.group(7)
        parent_last = match.group(8)
        
        # Add the great niece/nephew and their spouse
        great_niece_full = f"{great_niece_first} {last}"
        results.add((great_niece_full, 'great_niece_nephew'))
        if spouse_first:
            spouse_full = f"{spouse_first} {last}"
            results.add((spouse_full, ('spouse', great_niece_full)))
        
        # Add the parent and their spouse
        parent_full = f"{parent_first} {parent_last}"
        results.add((parent_full, ('parent', great_niece_full)))  # Include child reference
        if parent_spouse_first:
            parent_spouse_full = f"{parent_spouse_first} {parent_last}"
            results.add((parent_spouse_full, ('spouse', parent_full)))
    
    # Pattern: great niece/nephew First (Spouse) Last
    pattern2 = re.compile(r'(?:great niece|great nephew) ([A-Z][a-z]+)(?: \(([^)]+)\))? ([A-Z][a-z]+)', re.IGNORECASE)
    for match in pattern2.finditer(obituary_text):
        great_niece_first = match.group(1)
        spouse_first = match.group(2)
        last = match.group(3)
        great_niece_full = f"{great_niece_first} {last}"
        results.add((great_niece_full, 'great_niece_nephew'))
        if spouse_first:
            spouse_full = f"{spouse_first} {last}"
            results.add((spouse_full, ('spouse', great_niece_full)))
    
    # Fallback: great niece/nephew FullName (with optional suffix)
    pattern3 = re.compile(r'(?:great niece|great nephew) ([A-Z][a-z]+(?: [A-Z][a-z]+)*(?:,? (?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?)', re.IGNORECASE)
    for match in pattern3.finditer(obituary_text):
        full_name = match.group(1).strip()
        # Only add if not already matched by the more specific pattern
        if not any(full_name in n for n, _ in results):
            results.add((full_name, 'great_niece_nephew'))
    return list(results)

def extract_children_of_couples(obituary_text, current_last_name=None):
    """
    Extract children from patterns like 'great niece/nephew [First] ([Spouse]) [Last] and son/daughter [Child]'.
    Returns a list of (child_name, 'child', mother_name, father_name) tuples.
    """
    results = set()
    d = gender.Detector()
    
    # Example: great niece Megan (Ross) Wurz and son Finley
    pattern1 = re.compile(r'(great niece|great nephew) ([A-Z][a-z]+)(?: \(([^)]+)\))? ([A-Z][a-z]+) and (son|daughter) ([A-Z][a-z]+)', re.IGNORECASE)
    for match in pattern1.finditer(obituary_text):
        rel_type = match.group(1).lower()
        parent_first = match.group(2)
        spouse_first = match.group(3)
        last = match.group(4)
        child_gender = match.group(5).lower()
        child_first = match.group(6)
        # Determine mother/father
        parent_gender = d.get_gender(parent_first)
        spouse_gender = d.get_gender(spouse_first) if spouse_first else None
        if rel_type == 'great niece' or parent_gender in ['female', 'mostly_female']:
            mother = f"{parent_first} {last}"
            father = f"{spouse_first} {last}" if spouse_first else None
        else:
            father = f"{parent_first} {last}"
            mother = f"{spouse_first} {last}" if spouse_first else None
        child_name = f"{child_first} {last}"
        results.add((child_name, 'child', mother, father))
    
    # Pattern: son/daughter First (Spouse) Last
    pattern2 = re.compile(r'(?:preceded in death by|survived by) (?:his|her|their) (son|daughter) ([A-Z][a-z]+)(?: \(([^)]+)\))? ([A-Z][a-z]+)', re.IGNORECASE)
    for match in pattern2.finditer(obituary_text):
        child_gender = match.group(1).lower()
        child_first = match.group(2)
        spouse_first = match.group(3)
        last = match.group(4)
        child_name = f"{child_first} {last}"
        # Try to find parents in the text
        parent_pattern = re.compile(r'(?:preceded in death by|survived by) (?:his|her|their) (father|mother) ([A-Z][a-z]+)(?: \(([^)]+)\))? ([A-Z][a-z]+)', re.IGNORECASE)
        parent_matches = list(parent_pattern.finditer(obituary_text))
        mother = None
        father = None
        for parent_match in parent_matches:
            parent_type = parent_match.group(1).lower()
            parent_first = parent_match.group(2)
            maiden = parent_match.group(3)
            parent_last = parent_match.group(4)
            if parent_type == 'mother':
                if maiden:
                    mother = f"{parent_first} {maiden}"
                else:
                    mother = f"{parent_first} {parent_last}"
            else:  # father
                father = f"{parent_first} {parent_last}"
        results.add((child_name, 'child', mother, father))
    
    # Pattern: children First (Spouse) Last and First (Spouse) Last
    pattern3 = re.compile(r'(?:preceded in death by|survived by) (?:his|her|their) children ([A-Z][a-z]+)(?: \(([^)]+)\))? ([A-Z][a-z]+)(?: and ([A-Z][a-z]+)(?: \(([^)]+)\))? ([A-Z][a-z]+))?', re.IGNORECASE)
    for match in pattern3.finditer(obituary_text):
        # First child
        child1_first = match.group(1)
        spouse1_first = match.group(2)
        last1 = match.group(3)
        child1_name = f"{child1_first} {last1}"
        # Try to find parents in the text
        parent_pattern = re.compile(r'(?:preceded in death by|survived by) (?:his|her|their) (father|mother) ([A-Z][a-z]+)(?: \(([^)]+)\))? ([A-Z][a-z]+)', re.IGNORECASE)
        parent_matches = list(parent_pattern.finditer(obituary_text))
        mother = None
        father = None
        for parent_match in parent_matches:
            parent_type = parent_match.group(1).lower()
            parent_first = parent_match.group(2)
            maiden = parent_match.group(3)
            parent_last = parent_match.group(4)
            if parent_type == 'mother':
                if maiden:
                    mother = f"{parent_first} {maiden}"
                else:
                    mother = f"{parent_first} {parent_last}"
            else:  # father
                father = f"{parent_first} {parent_last}"
        results.add((child1_name, 'child', mother, father))
        
        # Second child if present
        child2_first = match.group(4)
        spouse2_first = match.group(5)
        last2 = match.group(6)
        if child2_first and last2:
            child2_name = f"{child2_first} {last2}"
            results.add((child2_name, 'child', mother, father))
    
    # Pattern: great niece/nephew First (Spouse) Last and son/daughter Child
    pattern4 = re.compile(r'great (?:niece|nephew) ([A-Z][a-z]+)(?: \(([^)]+)\))? ([A-Z][a-z]+) and (son|daughter) ([A-Z][a-z]+)', re.IGNORECASE)
    for match in pattern4.finditer(obituary_text):
        parent_first = match.group(1)
        spouse_first = match.group(2)
        last = match.group(3)
        child_gender = match.group(4).lower()
        child_first = match.group(5)
        # Determine mother/father based on gender
        parent_gender = d.get_gender(parent_first)
        spouse_gender = d.get_gender(spouse_first) if spouse_first else None
        if parent_gender in ['female', 'mostly_female']:
            mother = f"{parent_first} {last}"
            father = f"{spouse_first} {last}" if spouse_first else None
        else:
            father = f"{parent_first} {last}"
            mother = f"{spouse_first} {last}" if spouse_first else None
        child_name = f"{child_first} {last}"
        results.add((child_name, 'child', mother, father))
    
    return list(results)

def extract_preceded_in_death_names(obituary_text: str, current_last_name: str) -> List[str]:
    """Extract names from 'preceded in death by' sections."""
    preceded_patterns = [
        r'preceded in death by (?:his|her|their)?\s*([^.;]+)',
        r'reunited with (?:his|her|their)?\s*([^.;]+)',
        r'the late ([^.;]+)',
        r'late ([^.;]+)'
    ]
    
    found_names = []
    for pattern in preceded_patterns:
        matches = re.finditer(pattern, obituary_text, re.IGNORECASE)
        for match in matches:
            names_text = match.group(1)
            # Split on common conjunctions
            names = re.split(r',\s*|\s+and\s+|\s*&\s*', names_text)
            for name in names:
                name = name.strip()
                if name:
                    # If it's just a first name, append the current last name
                    if ' ' not in name:
                        name = f"{name} {current_last_name}"
                    found_names.append(name)
    
    return found_names

def extract_obituary_owner(obituary_text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Extract the name of the person the obituary is about."""
    # Use the first non-empty line as the primary source
    lines = [line.strip() for line in obituary_text.split('\n') if line.strip()]
    if lines:
        first_line = lines[0]
        # Try "Last, First M. (NEE Maiden)" or "Last, First M." headline
        headline_pattern = re.compile(r'^([A-Z][a-z]+),\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:\s*\(NEE\s+([^)]+)\))?', re.IGNORECASE)
        m = headline_pattern.match(first_line)
        if m:
            last_name = m.group(1)
            first_part = m.group(2)
            maiden_name = m.group(3)
            first_parts = first_part.split()
            first_name = first_parts[0]
            middle_name = ' '.join(first_parts[1:]) if len(first_parts) > 1 else None
            return first_name, middle_name, last_name, None, maiden_name, None
        # Try "First M. Last (NEE Maiden)" or "First M. Last" headline
        headline_pattern2 = re.compile(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([A-Z][a-z]+)(?:\s*\(NEE\s+([^)]+)\))?', re.IGNORECASE)
        m2 = headline_pattern2.match(first_line)
        if m2:
            first_part = m2.group(1)
            last_name = m2.group(2)
            maiden_name = m2.group(3)
            first_parts = first_part.split()
            first_name = first_parts[0]
            middle_name = ' '.join(first_parts[1:]) if len(first_parts) > 1 else None
            return first_name, middle_name, last_name, None, maiden_name, None
    # Fallback: scan the first paragraph for a likely full name
    paragraphs = obituary_text.split('\n\n')
    if paragraphs:
        first_para = paragraphs[0]
        # Look for the first occurrence of two or more capitalized words (likely a full name)
        name_pattern = re.compile(r'([A-Z][a-z]+(?: [A-Z][a-z]+)+)')
        name_match = name_pattern.search(first_para)
        if name_match:
            full_name = name_match.group(1)
            # Try to parse out first, middle, last
            parts = full_name.split()
            if len(parts) == 2:
                first_name, last_name = parts
                return first_name, None, last_name, None, None, None
            elif len(parts) > 2:
                first_name = parts[0]
                middle_name = ' '.join(parts[1:-1])
                last_name = parts[-1]
                return first_name, middle_name, last_name, None, None, None
    # Fallback: scan the entire obituary for the first likely full name (with optional middle initial and suffix)
    # Pattern: First [Middle/Initial] Last [Suffix]
    name_pattern = re.compile(r'([A-Z][a-z]+)(?: ([A-Z]\.|[A-Z][a-z]+))? ([A-Z][a-z]+)(?:,? (Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?')
    for match in name_pattern.finditer(obituary_text):
        first_name = match.group(1)
        middle_name = match.group(2)
        last_name = match.group(3)
        suffix = match.group(4)
        # Heuristic: skip if first_name is a common word (e.g., Born, Passed, Survived, etc.)
        if first_name.lower() in ['born', 'passed', 'survived', 'died', 'was', 'and', 'the', 'in', 'on', 'by', 'for', 'with', 'to', 'from', 'at', 'of', 'his', 'her', 'their', 'he', 'she', 'it', 'a', 'an']:
            continue
        # Heuristic: skip if last_name is a common word
        if last_name.lower() in ['born', 'passed', 'survived', 'died', 'was', 'and', 'the', 'in', 'on', 'by', 'for', 'with', 'to', 'from', 'at', 'of', 'his', 'her', 'their', 'he', 'she', 'it', 'a', 'an']:
            continue
        return first_name, middle_name, last_name, suffix, None, None
    # Fallback to previous regexes on the whole text
    # Pattern for "Last, First M. (NEE Maiden)"
    maiden_pattern = re.compile(r'([A-Z][a-z]+),\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?\s*\(NEE\s+([^)]+)\)', re.IGNORECASE)
    maiden_match = maiden_pattern.search(obituary_text)
    if maiden_match:
        last_name = maiden_match.group(1)
        first_name = maiden_match.group(2)
        maiden_name = maiden_match.group(3)
        # Try to get middle name/initial
        middle_name = None
        m = re.match(r'([A-Z][a-z]+),\s+([A-Z][a-z]+)(?: ([A-Z](?:\.|[a-z]+)?))?', maiden_match.group(0))
        if m and m.group(3):
            middle_name = m.group(3).strip()
        return first_name, middle_name, last_name, None, maiden_name, None
    # Pattern for "First M. Last (NEE Maiden)"
    pattern = re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+([A-Z][a-z]+)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?\s*\(NEE\s+([^)]+)\)', re.IGNORECASE)
    match = pattern.search(obituary_text)
    if match:
        first_part = match.group(1)
        last_name = match.group(2)
        maiden_name = match.group(3)
        # Split first part into first and middle names
        first_parts = first_part.split()
        first_name = first_parts[0]
        middle_name = ' '.join(first_parts[1:]) if len(first_parts) > 1 else None
        return first_name, middle_name, last_name, None, maiden_name, None
    # Pattern for "First M. Last"
    pattern = re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+([A-Z][a-z]+)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?', re.IGNORECASE)
    match = pattern.search(obituary_text)
    if match:
        first_part = match.group(1)
        last_name = match.group(2)
        # Split first part into first and middle names
        first_parts = first_part.split()
        first_name = first_parts[0]
        middle_name = ' '.join(first_parts[1:]) if len(first_parts) > 1 else None
        return first_name, middle_name, last_name, None, None, None
    # Pattern for "Last, First M."
    pattern = re.compile(r'([A-Z][a-z]+),\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?', re.IGNORECASE)
    match = pattern.search(obituary_text)
    if match:
        last_name = match.group(1)
        first_part = match.group(2)
        # Split first part into first and middle names
        first_parts = first_part.split()
        first_name = first_parts[0]
        middle_name = ' '.join(first_parts[1:]) if len(first_parts) > 1 else None
        return first_name, middle_name, last_name, None, None, None
    # Pattern for "Born [date]... Passed away..."
    pattern = re.compile(r'Born [^.]*\. Passed away', re.IGNORECASE)
    if pattern.search(obituary_text):
        # Look for the first name in the text
        name_pattern = re.compile(r'([A-Z][a-z]+) was (?:always|a|an)', re.IGNORECASE)
        name_match = name_pattern.search(obituary_text)
        if name_match:
            first_name = name_match.group(1)
            # Look for the last name in the text
            last_name_pattern = re.compile(r'([A-Z][a-z]+) was a \d+-year employee', re.IGNORECASE)
            last_name_match = last_name_pattern.search(obituary_text)
            if last_name_match:
                last_name = last_name_match.group(1)
                return first_name, None, last_name, None, None, None
    return None, None, None, None, None, None

def extract_names(obituary_text: str, name_normalizer: NameNormalizer) -> List[Dict[str, Any]]:
    """Extract names and relationships from obituary text."""
    names = []
    
    # Define suffix pattern
    suffix_pattern = r'(?:,?\s+(?:Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?'
    
    # First try to extract the deceased's name from the title or first line
    deceased_name = None
    if obituary_text.startswith("Obituary for "):
        deceased_name = obituary_text.split("\n")[0].replace("Obituary for ", "").strip()
    else:
        # Try to find the deceased's name in the first paragraph
        first_para = obituary_text.split('\n\n')[0] if '\n\n' in obituary_text else obituary_text
        name_match = re.search(r'([A-Z][a-z]+(?: [A-Z][a-z]+)+' + suffix_pattern + r')(?:\s+passed away|\s+died|\s+was born)', first_para)
        if name_match:
            deceased_name = name_match.group(1).strip()
    
    # Extract names using various patterns
    name_patterns = [
        # Spouse patterns with maiden names, nicknames, and suffixes
        (r'(?:wife|husband) of the late\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'spouse'),
        (r'(?:wife|husband) of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'spouse'),
        (r'(?:wife|husband)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'spouse'),
        (r'(?:married to|married)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'spouse'),
        
        # Parent patterns with maiden names, nicknames, and suffixes
        (r'(?:son|daughter) of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'parent'),
        (r'(?:son|daughter) of the late\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'parent'),
        (r'(?:son|daughter)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'parent'),
        
        # Sibling patterns with maiden names, nicknames, and suffixes
        (r'(?:brother|sister) of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'sibling'),
        (r'(?:brother|sister) of the late\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'sibling'),
        (r'(?:brother|sister)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'sibling'),
        
        # Child patterns with maiden names, nicknames, and suffixes
        (r'(?:father|mother) of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'child'),
        (r'(?:father|mother) of the late\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'child'),
        (r'(?:father|mother)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'child'),
        
        # General name patterns with maiden names, nicknames, and suffixes
        (r'(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'unknown'),
        (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*' + suffix_pattern + r')(?:\s+\(nee\s+([^)]+)\))?(?:\s+\(([^)]+)\))?', 'unknown')
    ]
    
    # First add the deceased if we found them
    if deceased_name:
        normalized = name_normalizer.normalize_name(deceased_name)
        if normalized:
            # Check for maiden name in the deceased's name
            maiden_match = re.search(r'\(nee\s+([^)]+)\)', deceased_name, re.IGNORECASE)
            maiden_name = maiden_match.group(1).strip() if maiden_match else None
            
            # Check for nickname in the deceased's name
            nickname_match = re.search(r'\(([^)]+)\)', deceased_name)
            nickname = nickname_match.group(1).strip() if nickname_match and not maiden_match else None
            
            # Extract suffix
            suffix_match = re.search(r',?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X)$', deceased_name)
            suffix = suffix_match.group(1) if suffix_match else None
            
            name_dict = {
                'name': normalized,
                'relationship': 'deceased',
                'original': deceased_name
            }
            if maiden_name:
                name_dict['maiden_name'] = maiden_name
            if nickname:
                name_dict['nickname'] = nickname
            if suffix:
                name_dict['suffix'] = suffix
            names.append(name_dict)
    
    # Then process the rest of the text
    for pattern, relationship in name_patterns:
        matches = re.finditer(pattern, obituary_text, re.IGNORECASE)
        for match in matches:
            name = match.group(1).strip()
            maiden_name = match.group(2) if len(match.groups()) > 1 and match.group(2) else None
            nickname = match.group(3) if len(match.groups()) > 2 and match.group(3) else None
            
            # Skip if this is the deceased's name
            if deceased_name and name_normalizer.normalize_name(name) == name_normalizer.normalize_name(deceased_name):
                continue
            
            # Skip if name contains 'and' or other conjunctions
            if re.search(r'\b(and|or|but|with)\b', name, re.IGNORECASE):
                continue
                
            normalized = name_normalizer.normalize_name(name)
            if normalized:
                # Extract suffix
                suffix_match = re.search(r',?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X)$', name)
                suffix = suffix_match.group(1) if suffix_match else None
                
                name_dict = {
                    'name': normalized,
                    'relationship': relationship,
                    'original': name
                }
                if maiden_name:
                    name_dict['maiden_name'] = maiden_name.strip()
                if nickname:
                    name_dict['nickname'] = nickname.strip()
                if suffix:
                    name_dict['suffix'] = suffix
                names.append(name_dict)
    
    return names

def process_obituary(obituary: Dict[str, Any], name_normalizer: NameNormalizer) -> Dict[str, Any]:
    """Process a single obituary and extract names and relationships."""
    result = {
        'name': obituary.get('name', ''),
        'birth_date': obituary.get('birth_date', ''),
        'death_date': obituary.get('death_date', ''),
        'location': obituary.get('location', ''),
        'url': obituary.get('url', ''),
        'people': []
    }
    
    # Get the obituary text, preferring the full text if available
    obituary_text = obituary.get('obituary_text', '')
    if not obituary_text:
        obituary_text = obituary.get('text', '')
    
    if not obituary_text:
        return result
    
    # Extract names from the text
    names = extract_names(obituary_text, name_normalizer)
    
    # Add the deceased if not already in the list
    if result['name'] and not any(n['name'] == name_normalizer.normalize_name(result['name']) for n in names):
        names.append({
            'name': name_normalizer.normalize_name(result['name']),
            'relationship': 'deceased',
            'original': result['name']
        })
    
    # Add all found names to the result
    result['people'] = names
    
    # Add any maiden names found in the text
    maiden_pattern = re.compile(r'\(nee\s+([^)]+)\)', re.IGNORECASE)
    maiden_matches = maiden_pattern.finditer(obituary_text)
    for match in maiden_matches:
        maiden_name = match.group(1).strip()
        # Try to find the corresponding person
        for person in result['people']:
            if 'maiden_name' not in person:
                person['maiden_name'] = maiden_name
                break
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Process obituaries to identify the deceased person.")
    parser.add_argument("input_file", help="Path to the input JSON file containing people data")
    parser.add_argument("--debug", action="store_true", help="Print results to STDOUT instead of writing to file")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    with open(args.input_file, 'r') as f:
        people = json.load(f)

    # Filter out people without obituary text early
    people_with_obituaries = [p for p in people if p.get('obituary_text')]
    logger.info(f"Processing {len(people_with_obituaries)} people with obituaries out of {len(people)} total people")

    # Process each person with an obituary
    for person in people_with_obituaries:
        obituary_text = person['obituary_text']
        first, middle, last, suffix, maiden_name, nickname = extract_obituary_owner(obituary_text)
        
        if first and last:
            logger.info(f"Found obituary owner: {first} {middle or ''} {last}")
            # Update person's information
            person['first_name'] = first
            person['middle_name'] = middle
            person['last_name'] = last
            person['suffix'] = suffix
            person['maiden_name'] = maiden_name
            person['nickname'] = nickname
            person['deceased'] = True
        else:
            logger.warning(f"Could not determine obituary owner for person with ID {person.get('id', 'unknown')}")

    if args.debug:
        print(json.dumps(people, indent=2))
    else:
        # Write back to the original file
        with open(args.input_file, 'w') as f:
            json.dump(people, f, indent=2)
        logger.info(f"Updated {args.input_file} with {len(people)} people")

if __name__ == "__main__":
    main() 
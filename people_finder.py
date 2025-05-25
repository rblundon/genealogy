import json
import re
import argparse
from common_classes import NameWeighting
import gender_guesser.detector as gender
from typing import List, Tuple

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_spouses_and_companions(obituary_text, current_last_name=None):
    """
    Extract spouse and companion names from obituary text.
    Returns a list of (name, relationship) tuples.
    """
    results = set()
    # Suffix pattern for names
    suffix_regex = r'(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))'

    # Spouse/companion patterns
    spouse_patterns = [
        (rf'beloved (?:wife|husband|spouse) of ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:{suffix_regex})?(?: \(nee [^)]+\))?', 'spouse'),
        (rf'(?:wife|husband|spouse) ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:{suffix_regex})?(?: \(nee [^)]+\))?', 'spouse'),
        (rf'(?:married to|married) ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:{suffix_regex})?(?: \(nee [^)]+\))?', 'spouse'),
        (rf'(?:companion of|companion|partner of|partner) ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:{suffix_regex})?(?: \(nee [^)]+\))?', 'companion'),
        (rf'([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:{suffix_regex})? \(companion\)', 'companion'),
        (rf'Survived by ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:{suffix_regex})?, (?:his|her|their) constant companion', 'companion'),
        # New patterns for better spouse detection
        (rf'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:{suffix_regex})?(?: \(nee [^)]+\))?', 'spouse'),
        (rf'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) of ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:{suffix_regex})?(?: \(nee [^)]+\))?', 'spouse'),
        (rf'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:{suffix_regex})? and (?:their|his|her) children', 'spouse'),
        (rf'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:wife|husband|spouse) ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:{suffix_regex})? and family', 'spouse'),
        # Patterns for companion detection
        (rf'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:companion|partner) ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:{suffix_regex})?(?: \(nee [^)]+\))?', 'companion'),
        (rf'(?:preceded in death by|survived by) (?:his|her|their) (?:beloved )?(?:companion|partner) of ([A-Z][a-z]+(?: [A-Z][a-z]+)?)(?:{suffix_regex})?(?: \(nee [^)]+\))?', 'companion'),
    ]
    for pattern, relationship in spouse_patterns:
        for match in re.finditer(pattern, obituary_text, re.IGNORECASE):
            logger.debug(f"[SPOUSE] Pattern: {pattern}")
            logger.debug(f"[SPOUSE] Raw match: {match.group(0)} | Groups: {match.groups()} | Relationship: {relationship}")
            name = match.group(1)
            suffix = match.group(2) if len(match.groups()) > 1 else None
            if suffix:
                name = f"{name} {suffix}"
            # Remove parenthetical content and extra whitespace
            clean = re.sub(r'\([^)]*\)', '', name).strip()
            # Handle 'nee' cases
            clean = re.sub(r'nee\s+[^,]+', '', clean).strip()
            # Handle titles
            clean = re.sub(r'^(?:Dr\.|Mr\.|Mrs\.|Ms\.|Rev\.|Fr\.)\s+', '', clean).strip()
            # Only consider if at least two words (likely a name)
            if len(clean.split()) >= 2:
                results.add((clean, relationship))
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
    for name, rel in extract_spouses_and_companions(obituary_text, current_last_name):
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

def parse_name(full_name: str) -> Tuple[str, str]:
    """Parse a full name into first and last name components."""
    # Remove any suffixes
    suffixes = ['jr', 'sr', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x']
    name_parts = full_name.split()
    if len(name_parts) >= 2:
        # Check if the last part is a suffix
        last_part = name_parts[-1].lower().replace('.', '')
        if last_part in suffixes:
            # Remove the suffix
            name_parts = name_parts[:-1]
            # If there's a comma before the suffix, remove it too
            if name_parts[-1].endswith(','):
                name_parts[-1] = name_parts[-1][:-1]
    
    if len(name_parts) >= 2:
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:])
        return first_name, last_name
    return full_name, ''

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

def main():
    parser = argparse.ArgumentParser(description="Find all family people in obituaries.")
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

    # Add IDs to people if they don't have them
    for i, person in enumerate(people):
        if 'id' not in person:
            person['id'] = f"P{i+1:04d}"
        # Initialize relationship fields if they don't exist
        for rel in ['spouse', 'companion', 'father', 'mother']:
            if rel not in person:
                person[rel] = None
        if 'children' not in person:
            person['children'] = []
        if 'siblings' not in person:
            person['siblings'] = []
        # Remove maiden_name field if it exists
        if 'maiden_name' in person:
            del person['maiden_name']

    # Build set of known (first, last) names and create a lookup dictionary
    known_names = set((p.get('first_name', '').lower(), p.get('last_name', '').lower()) for p in people)
    name_lookup = {(p.get('first_name', '').lower(), p.get('last_name', '').lower()): p for p in people if 'id' in p}
    name_weighting = NameWeighting({str(i): p for i, p in enumerate(people)})

    new_people = []
    spouse_relationships = []  # Store spouse relationships to process after all people are created
    parent_child_relationships = []  # Store parent-child relationships to process after all people are created
    child_parent_links = []  # Store child-parent relationships to process after all people are created
    
    # Only process people with obituaries
    for person in people_with_obituaries:
        obituary_text = person['obituary_text']  # We know this exists from the filter
        current_last_name = person.get('last_name', '')
        found_names = extract_family_names(obituary_text, current_last_name)
        # --- NEW: process children of couples for parent links ---
        for child_name, rel, mother, father in extract_children_of_couples(obituary_text, current_last_name):
            if rel == 'child':
                child_parent_links.append((child_name, mother, father))
        # --- END NEW ---
        for full_name, relationship in found_names:
            logger.info(f"Found name: '{full_name}' with relationship: {relationship}")
            first, last = parse_name(full_name)
            if not first or not last:
                logger.info(f"Skipping '{full_name}' (could not parse first/last name)")
                continue
            if not is_valid_name(first, last):
                logger.info(f"Filtered out as invalid: '{first} {last}' (from '{full_name}')")
                continue
            # Normalize last name using name checker
            last = name_weighting.correct_last_name(last, obituary_text)
            key = (first.lower(), last.lower())
            if key not in known_names:
                logger.info(f"Adding new person: {first} {last} ({relationship}) from '{full_name}'")
                new_person = {
                    'id': f"P{len(people) + len(new_people) + 1:04d}",
                    'first_name': first,
                    'last_name': last,
                    'birth_date': None,
                    'death_date': None,
                    'url': None,
                    'spouse': None,
                    'companion': None,
                    'father': None,
                    'mother': None,
                    'children': [],
                    'siblings': []
                }
                # Set the appropriate relationship field
                if isinstance(relationship, tuple):
                    if relationship[0] == 'spouse':
                        spouse_relationships.append((new_person, relationship[1]))
                    elif relationship[0] == 'parent':
                        parent_child_relationships.append((new_person, relationship[1]))
                elif relationship in ['spouse', 'companion']:
                    new_person[relationship] = person.get('id')
                    person[relationship] = new_person['id']
                elif relationship in ['father', 'mother']:
                    person[relationship] = new_person['id']
                    new_person['children'] = [person['id']]
                elif relationship == 'sibling':
                    # Add bidirectional sibling relationship
                    new_person['siblings'].append(person['id'])
                    person['siblings'].append(new_person['id'])
                    # Also add this new sibling to all other siblings of the person
                    for sib_id in person['siblings']:
                        if sib_id == new_person['id']:
                            continue
                        sib = name_lookup.get((next((p['first_name'].lower(), p['last_name'].lower()) for p in people + new_people if p['id'] == sib_id), None))
                        if sib and new_person['id'] not in sib['siblings']:
                            sib['siblings'].append(new_person['id'])
                        if sib and sib['id'] not in new_person['siblings']:
                            new_person['siblings'].append(sib['id'])
                new_people.append(new_person)
                known_names.add(key)
                name_lookup[key] = new_person
            else:
                logger.info(f"Already known: {first} {last} (from '{full_name}')")
                if relationship in ['father', 'mother']:
                    parent = name_lookup[key]
                    if 'children' not in parent:
                        parent['children'] = []
                    if person['id'] not in parent['children']:
                        parent['children'].append(person['id'])
                    person[relationship] = parent['id']
                elif relationship == 'sibling':
                    sibling = name_lookup[key]
                    if 'siblings' not in sibling:
                        sibling['siblings'] = []
                    if person['id'] not in sibling['siblings']:
                        sibling['siblings'].append(person['id'])
                    if 'siblings' not in person:
                        person['siblings'] = []
                    if sibling['id'] not in person['siblings']:
                        person['siblings'].append(sibling['id'])
                    # Also add this sibling to all other siblings of the person
                    for sib_id in person['siblings']:
                        if sib_id == sibling['id']:
                            continue
                        sib = name_lookup.get((next((p['first_name'].lower(), p['last_name'].lower()) for p in people + new_people if p['id'] == sib_id), None))
                        if sib and sibling['id'] not in sib['siblings']:
                            sib['siblings'].append(sibling['id'])
                        if sib and sib['id'] not in sibling['siblings']:
                            sibling['siblings'].append(sib['id'])

    # Second pass: link children to parents
    for child_full, mother_full, father_full in child_parent_links:
        c_first, c_last = parse_name(child_full)
        c_key = (c_first.lower(), c_last.lower())
        child = name_lookup.get(c_key)
        if not child:
            for k, v in name_lookup.items():
                if c_first.lower() in k[0] and c_last.lower() in k[1]:
                    child = v
                    break
            if not child:
                continue
        # Find mother
        if mother_full:
            m_first, m_last = parse_name(mother_full)
            m_key = (m_first.lower(), m_last.lower())
            mother = name_lookup.get(m_key)
            if not mother:
                for k, v in name_lookup.items():
                    if m_first.lower() in k[0] and m_last.lower() in k[1]:
                        mother = v
                        break
            if mother:
                child['mother'] = mother['id']
                if child['id'] not in mother['children']:
                    mother['children'].append(child['id'])

    # Additional pass: link children to parents based on spouse relationships
    for person in people + new_people:
        if person.get('spouse'):
            spouse = name_lookup.get((person['spouse'].lower(), person['last_name'].lower()))
            if spouse and spouse.get('children'):
                for child_id in spouse['children']:
                    child = next((p for p in people + new_people if p['id'] == child_id), None)
                    if child:
                        # If child has one parent but not the other, add the missing parent
                        if child.get('mother') == spouse['id'] and not child.get('father'):
                            child['father'] = person['id']
                            if child['id'] not in person['children']:
                                person['children'].append(child['id'])
                        elif child.get('father') == spouse['id'] and not child.get('mother'):
                            child['mother'] = person['id']
                            if child['id'] not in person['children']:
                                person['children'].append(child['id'])

    # Process spouse relationships after all people are created
    for spouse, sibling_name in spouse_relationships:
        # Add the last name to the sibling name if it's not already there
        if ' ' not in sibling_name:
            sibling_name = f"{sibling_name} {current_last_name}"
        sibling_first, sibling_last = parse_name(sibling_name)
        if sibling_first and sibling_last:
            sibling_key = (sibling_first.lower(), sibling_last.lower())
            if sibling_key in name_lookup:
                sibling = name_lookup[sibling_key]
                # Link the spouse to the sibling
                spouse['spouse'] = sibling['id']
                sibling['spouse'] = spouse['id']
                # If one is marked as companion, update both to be companions
                if spouse.get('companion') or sibling.get('companion'):
                    spouse['companion'] = sibling['id']
                    sibling['companion'] = spouse['id']
                    spouse['spouse'] = None
                    sibling['spouse'] = None

    # Process parent-child relationships after all people are created
    for parent, child_name in parent_child_relationships:
        child_first, child_last = parse_name(child_name)
        if child_first and child_last:
            child_key = (child_first.lower(), child_last.lower())
            if child_key in name_lookup:
                child = name_lookup[child_key]
                # Link the parent to the child
                child['father'] = parent['id']
                # Add the child to the parent's children array
                if 'children' not in parent:
                    parent['children'] = []
                if child['id'] not in parent['children']:
                    parent['children'].append(child['id'])

    # Clean up any incorrect sibling relationships
    for person in people + new_people:
        if 'siblings' in person:
            # Remove any siblings that are actually parents or children
            person['siblings'] = [s for s in person['siblings'] if not (
                s == person.get('father') or 
                s == person.get('mother') or 
                s in person.get('children', [])
            )]

    # Combine original and new people
    all_people = people + new_people

    # Ensure all siblings are mutually connected
    id_map = {p['id']: p for p in all_people}
    
    # First pass: collect all sibling groups
    sibling_groups = []
    processed_ids = set()
    
    for person in all_people:
        if person['id'] in processed_ids:
            continue
            
        sibs = person.get('siblings', [])
        if sibs:
            # Start a new sibling group
            group = {person['id']}
            group.update(sibs)
            
            # Add all siblings of siblings to the group
            to_process = list(group)
            while to_process:
                current_id = to_process.pop()
                current = id_map.get(current_id)
                if current and 'siblings' in current:
                    for sib_id in current['siblings']:
                        if sib_id not in group:
                            group.add(sib_id)
                            to_process.append(sib_id)
            
            sibling_groups.append(group)
            processed_ids.update(group)
    
    # Second pass: ensure all members of each group are connected to each other
    for group in sibling_groups:
        for person_id in group:
            person = id_map.get(person_id)
            if person:
                if 'siblings' not in person:
                    person['siblings'] = []
                # Add all other group members as siblings
                for other_id in group:
                    if other_id != person_id and other_id not in person['siblings']:
                        person['siblings'].append(other_id)

    if args.debug:
        print(json.dumps(all_people, indent=2))
    else:
        # Write back to the original file
        with open(args.input_file, 'w') as f:
            json.dump(all_people, f, indent=2)
        logger.info(f"Updated {args.input_file} with {len(all_people)} people")

if __name__ == "__main__":
    main() 
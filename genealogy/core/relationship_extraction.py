import re
from typing import List, Optional, Tuple
from .patterns import SPOUSE_PATTERNS
import logging

def extract_spouses_and_companions(text: str, current_last_name: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """
    Extract spouse and companion relationships from the text.
    
    Args:
        text: The text to analyze
        current_last_name: The last name of the current person (to avoid self-matching)
        
    Returns:
        List of tuples (name, relationship_type, confidence)
    """
    relationships = []
    companion_found = False
    
    # Extract spouse and companion relationships
    for pattern in SPOUSE_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if match.groups():
                name = match.group(1).strip()
                # Skip if the name matches the current_last_name or contains specific phrases
                if current_last_name and name.endswith(current_last_name) or re.search(r'\b(husband|wife) of\b', name, re.IGNORECASE):
                    continue
                # Handle conjunctions by splitting the name
                names = re.split(r'\s+(?:and|or|but|with)\s+', name, flags=re.IGNORECASE)
                for single_name in names:
                    single_name = single_name.strip()
                    if single_name:
                        # Infer last name if only a first name is present
                        if ' ' not in single_name and current_last_name:
                            single_name = f"{single_name} {current_last_name}"
                        # Skip if the inferred name matches the current_last_name or contains specific phrases
                        if current_last_name and single_name.endswith(current_last_name) or re.search(r'\b(husband|wife) of\b', single_name, re.IGNORECASE):
                            continue
                        # Determine relationship type based on pattern content
                        if 'companion' in pattern.lower():
                            relationships.append((single_name, 'companion', 'high'))
                            companion_found = True
                        else:
                            relationships.append((single_name, 'spouse', 'high'))
    
    # If a companion is found, remove any spouse relationships
    if companion_found:
        relationships = [rel for rel in relationships if rel[1] != 'spouse']
    
    return relationships

def extract_spouses_and_companions_old(obituary_text: str, current_last_name: Optional[str] = None) -> List[Tuple[str, str, Optional[str]]]:
    """
    Extract spouse and companion names from obituary text.
    Returns a list of (name, relationship, maiden_name) tuples.
    """
    results = set()
    # First, check for maiden name in the format "Last, First M. (NEE Maiden)"
    maiden_pattern = re.compile(r'([A-Z][a-z]+),\s+([A-Z][a-z]+)(?: [A-Z](?:\.|[a-z]+)?)?(?:,?\s+(Jr\.|Sr\.|I{2,}|IV|V|VI|VII|VIII|IX|X))?\s*\(NEE\s+([^)]+)\)', re.IGNORECASE)
    maiden_match = maiden_pattern.search(obituary_text)
    if maiden_match:
        last_name = maiden_match.group(1)
        first_name = maiden_match.group(2)
        # Try to get middle name/initial
        middle_name = None
        m = re.match(r'([A-Z][a-z]+),\s+([A-Z][a-z]+)(?: ([A-Z](?:\.|[a-z]+)?))?', maiden_match.group(0))
        if m and m.group(3):
            middle_name = m.group(3).strip()
        suffix = maiden_match.group(3) if len(maiden_match.groups()) > 3 else None
        maiden_name = maiden_match.group(4) if len(maiden_match.groups()) > 3 else None
        full_name = f"{first_name}"
        if middle_name:
            full_name += f" {middle_name}"
        full_name += f" {last_name}"
        if suffix:
            full_name = f"{full_name} {suffix}"
        results.add((full_name, 'self', maiden_name))
        current_last_name = last_name

    # Use the patterns from patterns.py
    for pattern in SPOUSE_PATTERNS:
        for match in re.finditer(pattern, obituary_text, re.IGNORECASE):
            groups = match.groups()
            # Debug log for match groups
            logging.debug(f"Pattern: {pattern} | Match groups: {groups}")
            name = match.group(1) if len(groups) >= 1 else None
            suffix = match.group(2) if len(groups) >= 2 else None
            maiden_name = match.group(3) if len(groups) >= 3 else None
            # Skip if name is None or contains 'and' or other conjunctions
            if not name or re.search(r'\b(and|or|but|with)\b', name, re.IGNORECASE):
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
                # Determine relationship type based on pattern
                if 'companion' in pattern.lower():
                    relationship = 'companion'
                else:
                    relationship = 'spouse'
                results.add((clean, relationship, maiden_name))
    return list(results) 
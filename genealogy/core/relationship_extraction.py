import re
from typing import List, Optional, Tuple, Dict
from .patterns import SPOUSE_PATTERNS
from .text_processor import TextProcessor
import logging

def extract_spouses_and_companions(text: str, current_last_name: str, people: List[Dict], current_person_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract spouse and companion names from text.
    
    Args:
        text: The text to process
        current_last_name: The last name of the current person
        people: List of all people dictionaries
        current_person_id: ID of the current person being processed
        
    Returns:
        Tuple of (spouse_name, companion_name)
    """
    processor = TextProcessor(people, current_person_id)
    processed_sentences = processor.process_text(text)
    
    spouse_name = None
    companion_name = None
    
    for sentence in processed_sentences:
        for relationship in sentence.relationships:
            if relationship['type'] == 'spouse':
                spouse_name = relationship['name']
            elif relationship['type'] == 'companion':
                companion_name = relationship['name']
                
    return spouse_name, companion_name

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
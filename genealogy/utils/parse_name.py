"""
Parse a person's name into its components (first, last, middle names, suffix, nickname, and maiden name).
"""

import re
from typing import Dict, Any
from genealogy.patterns import NAME_PATTERNS

def parse_name(name: str) -> Dict[str, Any]:
    """
    Parse a person's name into its components.
    
    Args:
        name (str): The full name of the person.
    
    Returns:
        Dict[str, Any]: A dictionary containing the parsed name components:
            - first_name: The first name.
            - last_name: The last name.
            - middle_names: A list of middle names (if any).
            - suffix: The suffix (e.g., Jr., Sr., III, IV, V).
            - nickname: The nickname (if any).
            - maiden_name: The maiden name (if any).
    """
    if not name:
        return {
            'first_name': '',
            'last_name': '',
            'middle_names': [],
            'suffix': '',
            'nickname': '',
            'maiden_name': ''
        }
    
    # Extract nickname if present using NAME_PATTERNS['nickname']
    nickname = None
    nickname_match = re.search(NAME_PATTERNS['nickname'], name)
    if nickname_match:
        nickname = nickname_match.group(1)
        name = re.sub(NAME_PATTERNS['nickname'], '', name).strip()
    
    # Extract suffix if present (e.g., "John Smith Jr.")
    suffix = None
    suffix_match = re.search(r'\b(Jr\.|Sr\.|III|IV|V)\b', name)
    if suffix_match:
        suffix = suffix_match.group(1)
        name = re.sub(r'\b(Jr\.|Sr\.|III|IV|V)\b', '', name).strip()
    
    # Extract maiden name if present using NAME_PATTERNS['maiden_name']
    maiden_name = None
    maiden_match = re.search(NAME_PATTERNS['maiden_name'], name, re.IGNORECASE)
    if maiden_match:
        maiden_name = maiden_match.group(1)
        name = re.sub(NAME_PATTERNS['maiden_name'], '', name, flags=re.IGNORECASE).strip()
    
    # Split the name into parts
    parts = name.split()
    if not parts:
        return {
            'first_name': '',
            'last_name': '',
            'middle_names': [],
            'suffix': suffix or '',
            'nickname': nickname or '',
            'maiden_name': maiden_name or ''
        }
    
    first_name = parts[0]
    last_name = parts[-1] if len(parts) > 1 else ''
    middle_names = parts[1:-1] if len(parts) > 2 else []
    
    return {
        'first_name': first_name,
        'last_name': last_name,
        'middle_names': middle_names,
        'suffix': suffix or '',
        'nickname': nickname or '',
        'maiden_name': maiden_name or ''
    } 
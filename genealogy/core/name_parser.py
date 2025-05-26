"""
Name parsing functionality for genealogy data.
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class ParsedName:
    """Class to hold parsed name components."""
    first_name: str
    middle_name: Optional[str]
    last_name: str
    nickname: Optional[str]
    suffix: Optional[str]

class NameParser:
    """Class to parse full names into components."""
    
    # Common name suffixes
    SUFFIXES = {
        'Jr', 'Jr.', 'Sr', 'Sr.', 'II', 'III', 'IV', 'V',
        'Junior', 'Senior', 'Esq', 'Esq.', 'PhD', 'MD', 'DDS'
    }
    
    def __init__(self):
        # Pattern to match nicknames in quotes or parentheses
        self.nickname_pattern = r'["\']([^"\']+)["\']|\(([^)]+)\)'
        
    def parse_name(self, full_name: str) -> ParsedName:
        """
        Parse a full name into its components.
        
        Args:
            full_name: The full name to parse
            
        Returns:
            ParsedName object containing the parsed components
        """
        # Extract nickname if present
        nickname = None
        nickname_match = re.search(self.nickname_pattern, full_name)
        if nickname_match:
            nickname = nickname_match.group(1) or nickname_match.group(2)
            # Remove the nickname from the full name
            full_name = re.sub(self.nickname_pattern, '', full_name).strip()
        
        # Split the remaining name into parts
        parts = full_name.split()
        
        # Check for suffix
        suffix = None
        if parts and parts[-1] in self.SUFFIXES:
            suffix = parts.pop()
        
        # Handle remaining parts
        if not parts:
            raise ValueError("No name parts found after processing")
            
        first_name = parts[0]
        last_name = parts[-1]
        middle_name = ' '.join(parts[1:-1]) if len(parts) > 2 else None
        
        return ParsedName(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            nickname=nickname,
            suffix=suffix
        ) 
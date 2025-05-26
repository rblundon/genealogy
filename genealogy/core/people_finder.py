"""
PeopleFinder: A module for finding and extracting people's information from obituaries.

This module provides functionality to extract names, relationships, and other relevant information
from obituary text.
"""

import re
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from genealogy.core.patterns import NAME_PATTERNS, RELATIONSHIP_PATTERNS
from .name_extractor import NameExtractor
import logging

# PATCH: Add a local RELATIONSHIP_PATTERNS with improved sibling pattern
RELATIONSHIP_PATTERNS = {
    'spouse': [
        r'(?:married to|spouse|husband|wife|partner)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*(?:\([^)]*\))?\s*(?:"[^"]*")?)',
        r'(?:married)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*(?:\([^)]*\))?\s*(?:"[^"]*")?)',
        r'(?:survived by|predeceased by)\s+(?:his|her)\s+(?:beloved\s+)?(?:husband|wife|spouse|partner)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
    'parent': [
        r'(?:son|daughter) of ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:father|mother) was ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:survived by|predeceased by)\s+(?:his|her)\s+(?:parents|father|mother)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:born to|raised by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
    'sibling': [
        # Capture names up to 'and', ',', or sentence end, but not trailing text
        r'(?:his|her)?\s*brother\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?=\s+(?:and|,|who|that|which|also|$))\s+(?:and|,)\s+(?:sister\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?=\s+(?:who|that|which|also|survive|$|\.|,))',
        r'(?:his|her)?\s*sister\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?=\s+(?:and|,|who|that|which|also|$))\s+(?:and|,)\s+(?:brother\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?=\s+(?:who|that|which|also|survive|$|\.|,))',
        r'(?:his|her)?\s*brother\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?=\s+(?:and|,|who|that|which|also|survive|$|\.|,))',
        r'(?:his|her)?\s*sister\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?=\s+(?:and|,|who|that|which|also|survive|$|\.|,))',
        r'(?:siblings include|survived by siblings)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:survived by|predeceased by)\s+(?:his|her)\s+(?:brothers|sisters|siblings)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
    'child': [
        r'(?:children include|survived by children)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:son|daughter)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:survived by|predeceased by)\s+(?:his|her)\s+(?:children|sons|daughters)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'(?:children|sons|daughters)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:and|,)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ],
}

class PeopleFinder:
    def __init__(self):
        """Initialize the PeopleFinder with empty sets for tracking names."""
        self.names = set()
        self.relationships = set()
        self.maiden_names = set()
        self.nicknames = set()
        self.name_extractor = NameExtractor()

    def extract_maiden_name(self, name: str) -> Optional[str]:
        """Extract maiden name from a name string."""
        for pattern in NAME_PATTERNS['maiden_name']:
            maiden_match = re.search(pattern, name, re.IGNORECASE)
            if maiden_match:
                # Try all capture groups
                for group in maiden_match.groups():
                    if group:
                        return group.strip()
        return None

    def extract_nickname(self, name: str) -> Optional[str]:
        """Extract nickname from a name string."""
        for pattern in NAME_PATTERNS['nickname']:
            nickname_match = re.search(pattern, name)
            if nickname_match:
                for group in nickname_match.groups():
                    if group:
                        return group.strip()
        return None

    def split_names(self, text: str) -> List[str]:
        """Split text into individual names, handling conjunctions."""
        # Split on common conjunctions
        parts = re.split(r'\s+(?:and|,|or|but|with)\s+', text)
        # Clean each part
        return [part.strip() for part in parts if part.strip()]

    def extract_names(self, obituary_text: str, title: str = "") -> List[Dict[str, Any]]:
        """Extract names and relationships from obituary text."""
        if not obituary_text:
            return []

        # Initialize results list
        results = []
        seen_names = set()

        # Add logging to capture values
        logging.info(f"Extracting names from title: {title}")
        logging.info(f"Extracting names from text: {obituary_text}")

        # Try to extract deceased's name from title first
        deceased_name = None
        if title:
            for pattern in NAME_PATTERNS['title']:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    deceased_name = match.group(1).strip()
                    logging.info(f"Deceased name from title: {deceased_name}")
                    break

        # If not found in title, try first paragraph
        if not deceased_name:
            first_para = next((line.strip() for line in obituary_text.split('\n') if line.strip()), '')
            logging.info(f"First paragraph for deceased extraction: '{first_para}'")
            # Look for patterns like "John Smith passed away" or "John Smith died"
            para_patterns = [
                r'^([A-Z][a-zA-Z\s\"\'\(\)\-]+?)\s+(?:passed away|died|was born|passed on|left us)',
                r'^([A-Z][a-zA-Z\s\"\'\(\)\-]+?)\'s\s+(?:obituary|memorial|tribute)',
                r'^(?:In Memory of|In Loving Memory of|Remembering)\s+([A-Z][a-zA-Z\s\"\'\(\)\-]+?)(?:,|\.|$)',
            ]
            for pattern in para_patterns:
                match = re.search(pattern, first_para, re.IGNORECASE)
                if match:
                    deceased_name = match.group(1).strip()
                    logging.info(f"Deceased name from first paragraph: {deceased_name}")
                    break

        # Add deceased's name if found
        if deceased_name:
            # Extract maiden name and nickname
            maiden_name = self.extract_maiden_name(deceased_name)
            nickname = self.extract_nickname(deceased_name)
            # Clean up the name using NameExtractor
            clean_name = self.name_extractor.clean_name(deceased_name)
            results.append({
                'name': clean_name,
                'relationship': 'deceased',
                'original_name': deceased_name,
                'maiden_name': maiden_name,
                'nickname': nickname
            })
            seen_names.add(clean_name.lower())

        # Extract names for each relationship type using RELATIONSHIP_PATTERNS
        for rel_type, rel_patterns in RELATIONSHIP_PATTERNS.items():
            for pattern in rel_patterns:
                matches = re.finditer(pattern, obituary_text, re.IGNORECASE)
                for match in matches:
                    # Debug: print all sibling matches
                    if rel_type == 'sibling':
                        print(f"Sibling pattern: {pattern}")
                        print(f"Sibling match groups: {match.groups()}")
                    # Handle patterns that might capture multiple names
                    names = []
                    for i in range(1, len(match.groups()) + 1):
                        if match.group(i):
                            names.extend(self.split_names(match.group(i)))
                    if rel_type == 'sibling':
                        print(f"Sibling names extracted: {names}")
                    for name in names:
                        # Skip if name is just a preposition or conjunction
                        if name.lower() in ['to', 'and', 'or', 'but', 'with']:
                            continue
                        # Filter out phrases that are not likely to be names
                        if not re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)+$', name.strip()):
                            continue
                        # Extract maiden name and nickname
                        maiden_name = self.extract_maiden_name(name)
                        nickname = self.extract_nickname(name)
                        # Clean up the name using NameExtractor
                        clean_name = self.name_extractor.clean_name(name)
                        # Skip if we've seen this name before (unless it's a duplicate with a suffix like Jr.)
                        if clean_name.lower() in seen_names and not re.search(r'\b(Jr\.|Sr\.|III|IV|V)\b', clean_name):
                            continue
                        # Skip if this is the deceased's name
                        if deceased_name and clean_name.lower() == deceased_name.lower():
                            continue
                        results.append({
                            'name': clean_name,
                            'relationship': rel_type,
                            'original_name': name,
                            'maiden_name': maiden_name,
                            'nickname': nickname
                        })
                        seen_names.add(clean_name.lower())

        return results

    def process_obituary(self, obituary: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single obituary and extract names."""
        if not obituary:
            return obituary

        # Extract names from obituary text
        names = self.extract_names(
            obituary.get('obituary_text', ''),
            obituary.get('title', '')
        )

        # Update obituary with extracted names
        obituary['extracted_names'] = names
        return obituary 
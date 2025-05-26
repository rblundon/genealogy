"""
PeopleFinder: A module for finding and extracting people's information from obituaries.

This module provides functionality to extract names, relationships, and other relevant information
from obituary text.
"""

import re
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from genealogy.patterns import NAME_PATTERNS, RELATIONSHIP_PATTERNS
import logging

class PeopleFinder:
    def __init__(self):
        """Initialize the PeopleFinder with empty sets for tracking names."""
        self.names = set()
        self.relationships = set()
        self.maiden_names = set()
        self.nicknames = set()

    def clean_name(self, name: str) -> str:
        """Clean a name by removing parentheses, nicknames, and extra whitespace."""
        # Remove parentheses and their contents
        name = re.sub(r'\([^)]*\)', '', name)
        # Remove nicknames in quotes
        name = re.sub(r'"[^"]*"', '', name)
        # Remove common titles
        name = re.sub(r'\b(Mr\.|Mrs\.|Ms\.|Dr\.|Rev\.|Prof\.)\b', '', name)
        # Remove extra whitespace
        name = ' '.join(name.split())
        return name.strip()

    def extract_maiden_name(self, name: str) -> Optional[str]:
        """Extract maiden name from a name string."""
        maiden_match = re.search(NAME_PATTERNS['maiden_name'], name, re.IGNORECASE)
        if maiden_match:
            # Try both capture groups since we have two patterns
            maiden_name = maiden_match.group(1) or maiden_match.group(2)
            if maiden_name:
                return maiden_name.strip()
        return None

    def extract_nickname(self, name: str) -> Optional[str]:
        """Extract nickname from a name string."""
        nickname_match = re.search(NAME_PATTERNS['nickname'], name)
        if nickname_match:
            # Try both capture groups since we have two patterns
            nickname = nickname_match.group(1) or nickname_match.group(2)
            if nickname:
                return nickname.strip()
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
            # Use the title pattern from NAME_PATTERNS
            match = re.search(NAME_PATTERNS['title'], title, re.IGNORECASE)
            if match:
                deceased_name = match.group(1).strip()
                logging.info(f"Deceased name from title: {deceased_name}")

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
            
            # Clean up the name
            clean_name = self.clean_name(deceased_name)
            
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
                    # Handle patterns that might capture multiple names
                    names = []
                    for i in range(1, len(match.groups()) + 1):
                        if match.group(i):
                            names.extend(self.split_names(match.group(i)))
                    
                    for name in names:
                        # Skip if name is just a preposition or conjunction
                        if name.lower() in ['to', 'and', 'or', 'but', 'with']:
                            continue
                            
                        # Extract maiden name and nickname
                        maiden_name = self.extract_maiden_name(name)
                        nickname = self.extract_nickname(name)
                        
                        # Clean up the name
                        clean_name = self.clean_name(name)
                        
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
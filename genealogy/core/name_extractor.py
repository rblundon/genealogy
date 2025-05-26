"""
NameExtractor: A class for extracting and cleaning names from obituary text.
"""

import re
from typing import Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
import logging

class NameExtractor:
    def __init__(self):
        """Initialize the NameExtractor."""
        pass

    def clean_name(self, name: str) -> str:
        """Clean a name by removing artifacts and standardizing format."""
        logging.info(f"Cleaning name: {name}")
        if not name:
            return ""
            
        # Remove "Obituary" and year
        name = re.sub(r'\s*Obituary\s*(?:\(\d{4}\))?', '', name)
        name = re.sub(r'\s*Memorial\s*(?:\(\d{4}\))?', '', name)
        
        # Remove nicknames in quotes
        name = re.sub(r'"[^"]*"', '', name)
        name = re.sub(r"'[^']*'", '', name)
        
        # Remove common titles at the start
        name = re.sub(r'^(Mr\.|Mrs\.|Ms\.|Dr\.|Rev\.|Prof\.|Sir|Lady|Dame)\s+', '', name, flags=re.IGNORECASE)
        
        # Remove common titles elsewhere
        name = re.sub(r'\b(Mr\.|Mrs\.|Ms\.|Dr\.|Rev\.|Prof\.|Sir|Lady|Dame)\b', '', name, flags=re.IGNORECASE)
        
        # Remove location suffixes
        name = re.sub(r'\s*-\s*.*$', '', name)
        name = re.sub(r'\s*\|.*$', '', name)
        
        # Handle parentheses - only remove if they contain nicknames or titles
        name = re.sub(r'\([^)]*(?:nickname|aka|also known as)[^)]*\)', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\([^)]*(?:Mr\.|Mrs\.|Ms\.|Dr\.|Rev\.|Prof\.|Sir|Lady|Dame)[^)]*\)', '', name, flags=re.IGNORECASE)
        
        # Remove trailing conjunctions
        name = re.sub(r'\s+(?:and|or|but|with|,)\s*$', '', name, flags=re.IGNORECASE)
        
        # Remove all parentheses and their contents, except for (nee ...)
        name = re.sub(r'\((?!nee)[^)]*\)', '', name, flags=re.IGNORECASE)
        
        # Remove extra whitespace (after all cleaning)
        name = ' '.join(name.split())
        
        cleaned_name = name.strip()
        logging.info(f"Cleaned name: {cleaned_name}")
        return cleaned_name

    def extract_from_title(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """Extract name and location from page title."""
        if not soup:
            return None, None
            
        title = soup.find('title')
        if not title:
            return None, None
            
        title_text = title.get_text().strip()
        
        # Try different title patterns
        patterns = [
            # Standard obituary format
            r'^(.*?)\s+Obituary\s*-\s*([^-]+?)(?:\s*-\s*[^-]+)?$',
            # Memorial format
            r'^(.*?)\s+Memorial\s*-\s*([^-]+?)(?:\s*-\s*[^-]+)?$',
            # Simple format
            r'^(.*?)\s*-\s*([^-]+?)(?:\s*-\s*[^-]+)?$',
            # Funeral home format
            r'^(.*?)\s+(?:Obituary|Memorial)\s*-\s*([^-]+?)\s*-\s*[^-]+$',
            # Location first format
            r'^([^-]+?)\s*-\s*(.*?)\s+(?:Obituary|Memorial)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title_text, re.IGNORECASE)
            if match:
                # Check which group contains the name
                if 'Obituary' in match.group(1) or 'Memorial' in match.group(1):
                    name = self.clean_name(match.group(2))
                    location = match.group(1).strip()
                else:
                    name = self.clean_name(match.group(1))
                    location = match.group(2).strip()
                return name, location
                
        # If no pattern matches, try to extract just the name
        name = self.clean_name(title_text)
        return name, None

    def extract_full_name(self, soup: BeautifulSoup, text: str) -> Optional[str]:
        """Extract full name from obituary text."""
        if not text:
            return None
            
        # Try to find name in first paragraph
        first_para = next((p.get_text() for p in soup.find_all(['p', 'div']) if p.get_text().strip()), '')
        
        # Look for patterns like "John Smith passed away" or "John Smith died"
        patterns = [
            r'^([A-Z][a-zA-Z\s\"\'\(\)\-]+?)\s+(?:passed away|died|was born|passed on|left us)',
            r'^([A-Z][a-zA-Z\s\"\'\(\)\-]+?)\'s\s+(?:obituary|memorial|tribute)',
            r'^(?:In Memory of|In Loving Memory of|Remembering)\s+([A-Z][a-zA-Z\s\"\'\(\)\-]+?)(?:,|\.|$)',
            r'^([A-Z][a-zA-Z\s\"\'\(\)\-]+?)\s+(?:passed|died|was born)',
            r'^(?:The family of|The family announces the passing of)\s+([A-Z][a-zA-Z\s\"\'\(\)\-]+?)(?:,|\.|$)',
            r'^(?:We announce the passing of|We are sad to announce the passing of)\s+([A-Z][a-zA-Z\s\"\'\(\)\-]+?)(?:,|\.|$)',
            r'^(?:It is with great sadness that we announce the passing of)\s+([A-Z][a-zA-Z\s\"\'\(\)\-]+?)(?:,|\.|$)',
            r'^(?:With heavy hearts, we announce the passing of)\s+([A-Z][a-zA-Z\s\"\'\(\)\-]+?)(?:,|\.|$)',
            r'^(?:We are heartbroken to announce the passing of)\s+([A-Z][a-zA-Z\s\"\'\(\)\-]+?)(?:,|\.|$)',
            r'^(?:It is with deep sorrow that we announce the passing of)\s+([A-Z][a-zA-Z\s\"\'\(\)\-]+?)(?:,|\.|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, first_para, re.IGNORECASE)
            if match:
                return self.clean_name(match.group(1))
                
        return None

    @staticmethod
    def extract_name_components(text: str) -> dict:
        """Extract first, last, middle names, suffix, and nickname from the given text."""
        fields = {}
        
        # Extract name components
        name = text.split(',')[0]  # Assuming the name is the first part before a comma
        name_parts = name.split()
        if len(name_parts) >= 2:
            fields['first_name'] = name_parts[0]
            fields['last_name'] = name_parts[-1]
            if len(name_parts) > 2:
                fields['middle_name'] = ' '.join(name_parts[1:-1])
        else:
            fields['first_name'] = name_parts[0] if name_parts else ''
            fields['last_name'] = ''
        
        # Check for suffix (e.g., Jr., Sr., III)
        suffix_pattern = r'\b(Jr\.|Sr\.|III|IV|V)\b'
        suffix_match = re.search(suffix_pattern, text)
        if suffix_match:
            fields['suffix'] = suffix_match.group(0)
        
        # Check for nickname (e.g., "Joe" in "Joseph 'Joe' Smith")
        nickname_pattern = r'"([^"]*)"|\'([^\']*)\''
        nickname_match = re.search(nickname_pattern, text)
        if nickname_match:
            fields['nickname'] = nickname_match.group(1) or nickname_match.group(2)
        
        return fields 
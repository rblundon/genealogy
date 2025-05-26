"""
Common utilities for processing obituaries.
"""

import logging
import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, Tuple
import os
from genealogy.core.patterns import (
    DEATH_PATTERNS, BIRTH_PATTERNS, AGE_PATTERNS, 
    LOCATION_PATTERNS, NAME_PATTERNS, GENDER_PATTERNS
)
from genealogy.core.name_extractor import NameExtractor

# Global counter for GEDCOM-style IDs
_last_individual_id = 0

def get_next_individual_id() -> str:
    global _last_individual_id
    _last_individual_id += 1
    return f"I{_last_individual_id:04d}"

def initialize_individual_id_counter(input_file: str):
    """Scan the input file for existing IDs and set the counter to the highest found value."""
    global _last_individual_id
    if not os.path.exists(input_file):
        return
    try:
        import json
        with open(input_file, 'r') as f:
            data = json.load(f)
        max_id = 0
        for person in data:
            pid = person.get('id')
            if pid and pid.startswith('I'):
                try:
                    num = int(pid[1:])
                    if num > max_id:
                        max_id = num
                except ValueError:
                    continue
        _last_individual_id = max_id
    except Exception as e:
        logging.warning(f"Could not initialize individual ID counter: {e}")

def extract_location_from_text(text: str) -> Optional[str]:
    for pattern in NAME_PATTERNS['location']:
        match = re.search(pattern, text)
        if match:
            location = match.group(1).strip()
            # Clean up common artifacts
            location = re.sub(r'\s+', ' ', location)
            location = re.sub(r',\s*,', ',', location)
            # Remove common words that shouldn't be part of location
            location = re.sub(r'\b(?:at|in|the|and|or|but)\b', '', location, flags=re.IGNORECASE)
            location = ' '.join(location.split())
            return location.strip()
    return None

def extract_name_and_location_from_title(soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
    # Try to extract from <title> tag
    title_tag = soup.find('title')
    if title_tag and title_tag.text:
        title_text = title_tag.text.strip()
        # Example: "Maxine Kaczmarowski Obituary (2018) - Milwaukee, WI - Milwaukee Journal Sentinel"
        parts = [p.strip() for p in title_text.split(' - ')]
        if len(parts) >= 2:
            # Name is before 'Obituary' or first dash
            name_part = parts[0]
            name = re.sub(r' Obituary.*$', '', name_part, flags=re.IGNORECASE).strip()
            # Location is the second part
            location = parts[1]
            return name, location
    return None, None

def read_obituary(url: str, headers: Optional[dict] = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Read and clean obituary content from a URL.
    
    Args:
        url: The URL to read from
        headers: Optional headers for the request
        
    Returns:
        Tuple of (cleaned obituary text, full name, location) or (None, None, None) if there was an error
    """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script, style, and meta elements
        for element in soup(["script", "style", "meta", "link", "noscript"]):
            element.decompose()
            
        # Extract full name and location from <title> tag if possible
        full_name, location = extract_name_and_location_from_title(soup)
        
        # Fallback: Try to find the main obituary content
        main_content = None
        for selector in [
            'article', '.obituary', '.obit', '.obituary-content',
            '.obituary-text', '.obit-content', '.obit-text',
            '#obituary', '#obit', '#obituary-content',
            '#obituary-text', '#obit-content', '#obit-text'
        ]:
            if content := soup.select_one(selector):
                main_content = content
                break
                
        # If no specific container found, try to find the main content
        if not main_content:
            # Look for the largest text block that contains obituary indicators
            text_blocks = []
            for element in soup.find_all(['p', 'div']):
                text = element.get_text(strip=True)
                if len(text) > 100:  # Minimum length for obituary content
                    text_blocks.append((len(text), text))
            
            if text_blocks:
                # Sort by length and take the longest block
                text_blocks.sort(reverse=True)
                main_content = text_blocks[0][1]
            else:
                # Fallback to getting all text
                main_content = soup.get_text(separator=' ', strip=True)
        
        # Clean up the text
        if isinstance(main_content, str):
            text = main_content
        else:
            text = main_content.get_text(separator=' ', strip=True)
            
        # If we don't have a name yet, use NameExtractor to extract it from the text
        if not full_name:
            name_extractor = NameExtractor()
            full_name = name_extractor.extract_full_name(soup, text)
            if not full_name:
                # As a last resort, try to extract a likely name from the first 200 chars
                match = re.search(r'([A-Z][a-z]+(?: [A-Z][a-z]+)+)', text[:200])
                if match:
                    full_name = match.group(1)
        
        # Remove common meta description patterns
        text = re.sub(r'^.*?(?=died|passed away|reunited with|survived by|born|age)', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove common footer patterns
        text = re.sub(r'(?:visitation|funeral|memorial|service|burial).*$', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # If location was not found in the title, extract from the cleaned text
        if not location:
            location = extract_location_from_text(text)
        
        # Validate the text
        if not text or len(text) < 50:  # Minimum length for valid obituary
            logging.warning(f"Extracted text too short or empty from {url}")
            return None, None, None
            
        return text, full_name, location
        
    except Exception as e:
        logging.error(f"Error reading obituary from {url}: {str(e)}")
        return None, None, None 
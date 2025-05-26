"""
Common utilities for processing obituaries.
"""

import logging
import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, Tuple, List, Dict
import os
from genealogy.core.patterns import (
    DEATH_PATTERNS, BIRTH_PATTERNS, AGE_PATTERNS, 
    LOCATION_PATTERNS, NAME_PATTERNS, GENDER_PATTERNS
)
from genealogy.core.name_extractor import NameExtractor
import json

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

def link_people(people: List[Dict], person1_id: str, person2_id: str, field: str) -> None:
    """
    Create bi-directional links between two people in the specified field.
    
    Args:
        people: List of all people dictionaries
        person1_id: ID of the first person
        person2_id: ID of the second person
        field: The field to link (e.g., 'spouse', 'companion')
    """
    # Find both people in the list
    person1 = next((p for p in people if p.get('id') == person1_id), None)
    person2 = next((p for p in people if p.get('id') == person2_id), None)
    
    if person1 and person2:
        # Set the links in both directions
        person1[field] = person2_id
        person2[field] = person1_id
        logging.info(f"Linked {person1.get('full_name')} and {person2.get('full_name')} as {field}s")
    else:
        logging.warning(f"Could not link people: {person1_id} and {person2_id} - one or both not found")

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

def add_to_input_file(name: str, input_file: str) -> None:
    """
    Add a matched name to the input file.
    
    Args:
        name: The name to add
        input_file: The path to the input file
    """
    logging.info(f"Attempting to add name '{name}' to input file: {input_file}")
    try:
        # Read existing data
        data = []
        if os.path.exists(input_file):
            try:
                with open(input_file, 'r') as f:
                    data = json.load(f)
                    logging.info(f"Current data in input file: {data}")
            except json.JSONDecodeError as e:
                logging.error(f"Error reading JSON from {input_file}: {e}")
                return
            except Exception as e:
                logging.error(f"Error reading file {input_file}: {e}")
                return
        
        # Check if the name is already in the file
        if not any(person.get('full_name') == name for person in data):
            # Add a new entry with additional fields
            new_entry = {
                'full_name': name,
                'id': get_next_individual_id(),
                'location': None,
                'obituary_text': None,
                'birth_date': None,
                'death_date': None,
                'age': None,
                'gender': None,
                'spouse': None,
                'companion': None
            }
            data.append(new_entry)
            print(f"\nAdding new entry to {input_file}:")
            print(json.dumps(new_entry, indent=2))
            logging.info(f"Added new entry for '{name}' to input file.")
            
            # Write the updated data back to the file
            try:
                with open(input_file, 'w') as f:
                    json.dump(data, f, indent=2)
                    f.flush()  # Ensure data is written to disk
                    os.fsync(f.fileno())  # Force system to write to disk
                logging.info(f"Successfully wrote data to {input_file}")
            except Exception as e:
                logging.error(f"Error writing to file {input_file}: {e}")
                return
        else:
            logging.info(f"Name '{name}' already exists in the input file.")
            
    except Exception as e:
        logging.error(f"Error adding name to input file: {str(e)}") 
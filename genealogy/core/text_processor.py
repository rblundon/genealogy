"""
TextProcessor: A module for processing obituary text into sentences and extracting relationships.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import re
import logging
from .patterns import SPOUSE_PATTERNS, RELATIONSHIP_PATTERNS, CONTEXT_PATTERNS, NAME_PATTERNS
from .name_utils import infer_full_name
from .name_extractor import NameExtractor
from .obituary_utils import link_people, find_or_create_person

logger = logging.getLogger(__name__)
logger.propagate = True  # Ensure logs propagate to the root logger
# Note: To guarantee debug logs, set the logger level after logging.basicConfig in main.py if needed.

@dataclass
class ProcessedSentence:
    """Data class to hold processed sentence information"""
    sentence: str
    relationships: List[Dict]
    context: Optional[str] = None

class TextProcessor:
    """Processes obituary text into sentences and extracts relationships."""
    
    def __init__(self, people: List[Dict], current_person_id: str):
        self.people = people
        self.current_person_id = current_person_id
        self.name_extractor = NameExtractor()
        
    def process_text(self, text: str) -> List[ProcessedSentence]:
        """
        Process the text into sentences and extract relationships.
        
        Args:
            text: The text to process
            
        Returns:
            List of ProcessedSentence objects containing the processed sentences
            and their extracted relationships
        """
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        # Process each sentence
        processed_sentences = []
        for sentence in sentences:
            processed = self._process_sentence(sentence)
            if processed:
                processed_sentences.append(processed)
                
        return processed_sentences
        
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex patterns"""
        # Split on periods followed by space and capital letter
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]
        
    def _process_sentence(self, sentence: str) -> Optional[ProcessedSentence]:
        """
        Process a single sentence to extract relationships.
        
        Args:
            sentence: The sentence to process
            
        Returns:
            ProcessedSentence object if relationships were found, None otherwise
        """
        relationships = []
        context = None
        
        # Check each relationship type
        for relation_type, patterns in RELATIONSHIP_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    name = match.group(1).strip()
                    cleaned_name = self.name_extractor.clean_name(name)
                    
                    if not cleaned_name:
                        continue
                        
                    # If it's a single name, infer the full name using the current person's last name
                    if ' ' not in cleaned_name:
                        current_person = next((p for p in self.people if p.get('id') == self.current_person_id), None)
                        if current_person and current_person.get('last_name'):
                            cleaned_name = infer_full_name(cleaned_name, current_person.get('last_name'))
                    
                    # Find or create the person
                    person_id = find_or_create_person(self.people, cleaned_name)
                    if not person_id:
                        continue
                        
                    # Link the relationship
                    link_people(self.people, self.current_person_id, person_id, relation_type)
                    
                    # Add to relationships list
                    relationships.append({
                        'type': relation_type,
                        'name': cleaned_name,
                        'confidence': 'high'  # We can adjust this based on pattern complexity
                    })
                    
                    # Extract context if available
                    if len(match.groups()) > 1 and match.group(2):
                        context = match.group(2).strip()
                        
        if relationships:
            return ProcessedSentence(sentence, relationships, context)
        return None 
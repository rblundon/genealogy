"""
TextProcessor: A module for processing obituary text into sentences and extracting relationships.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import re
import logging
from .patterns import SPOUSE_PATTERNS
from .name_utils import infer_full_name

logger = logging.getLogger(__name__)
logger.propagate = True  # Ensure logs propagate to the root logger
# Note: To guarantee debug logs, set the logger level after logging.basicConfig in main.py if needed.

@dataclass
class ProcessedSentence:
    """Represents a processed sentence with its extracted relationships and context."""
    text: str
    relationships: List[Tuple[str, str, str]]  # (name, relationship_type, confidence)
    context: Optional[str] = None  # e.g., "survived by", "preceded by", etc.

class TextProcessor:
    """Processes obituary text into sentences and extracts relationships."""
    
    def __init__(self):
        self.current_last_name: Optional[str] = None
        
    def process_text(self, text: str, current_last_name: Optional[str] = None) -> List[ProcessedSentence]:
        """
        Process text into sentences and extract relationships from each.
        
        Args:
            text: The text to process
            current_last_name: The last name of the current person (to avoid self-matching)
            
        Returns:
            List of ProcessedSentence objects containing the processed sentences and their relationships
        """
        logger.debug(f"Processing text with current_last_name: {current_last_name}")
        self.current_last_name = current_last_name
        sentences = self._split_into_sentences(text)
        logger.debug(f"Split text into {len(sentences)} sentences")
        return [self._process_sentence(sentence) for sentence in sentences]
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using proper sentence boundaries.
        
        Args:
            text: The text to split
            
        Returns:
            List of sentences
        """
        # Basic sentence splitting - can be enhanced for better accuracy
        # Split on periods followed by space and capital letter, but not on common abbreviations
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        # Clean up the sentences
        cleaned_sentences = [s.strip() for s in sentences if s.strip()]
        for i, sentence in enumerate(cleaned_sentences, 1):
            logger.debug(f"Sentence {i}: {sentence}")
        return cleaned_sentences
    
    def _process_sentence(self, sentence: str) -> ProcessedSentence:
        """
        Process a single sentence and extract relationships.
        
        Args:
            sentence: The sentence to process
            
        Returns:
            ProcessedSentence object containing the sentence and its relationships
        """
        logger.debug(f"\nProcessing sentence: {sentence}")
        relationships = []
        
        # Extract spouse and companion relationships
        for pattern in SPOUSE_PATTERNS:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                if match.groups():
                    name = match.group(1).strip()
                    logger.debug(f"Found potential relationship name: {name}")
                    
                    # Skip if the name matches the current_last_name or contains specific phrases
                    if self.current_last_name and name.endswith(self.current_last_name):
                        logger.debug(f"Skipping {name} - matches current_last_name")
                        continue
                    if name.lower().startswith('of '):
                        logger.debug(f"Skipping {name} - starts with 'of'")
                        continue
                    if re.search(r'\b(husband|wife|daughter|son|father|mother|brother|sister) of\b', name, re.IGNORECASE):
                        logger.debug(f"Skipping {name} - contains relationship word")
                        continue
                        
                    # Handle conjunctions by splitting the name, but only if it's not part of a relationship phrase
                    if not re.search(r'\b(husband|wife|daughter|son|father|mother|brother|sister)\b', name, re.IGNORECASE):
                        names = re.split(r'\s+(?:and|or|but|with)\s+', name, flags=re.IGNORECASE)
                        logger.debug(f"Split name into parts: {names}")
                    else:
                        names = [name]
                        logger.debug(f"Keeping name as is due to relationship word: {name}")
                    
                    for single_name in names:
                        single_name = single_name.strip()
                        if single_name:
                            logger.debug(f"Processing single name: {single_name}")
                            
                            # Skip if the name starts with 'of' or contains relationship words
                            if single_name.lower().startswith('of '):
                                logger.debug(f"Skipping {single_name} - starts with 'of'")
                                continue
                            if re.search(r'\b(husband|wife|daughter|son|father|mother|brother|sister)\b', single_name, re.IGNORECASE):
                                logger.debug(f"Skipping {single_name} - contains relationship word")
                                continue
                            
                            # Check for maiden name pattern (e.g., 'Maxine (nee Paradowski)')
                            maiden_match = re.match(r'(\w+)\s+\(nee\s+(\w+)\)', single_name, re.IGNORECASE)
                            if maiden_match:
                                first_name = maiden_match.group(1)
                                logger.debug(f"Extracted first name from maiden name pattern: {first_name}")
                                single_name = infer_full_name(first_name, self.current_last_name)
                                logger.debug(f"Inferred full name: {single_name}")
                            
                            # Skip if the inferred name matches the current_last_name or contains specific phrases
                            if self.current_last_name and single_name.endswith(self.current_last_name):
                                logger.debug(f"Skipping {single_name} - matches current_last_name after inference")
                                continue
                            if single_name.lower().startswith('of '):
                                logger.debug(f"Skipping {single_name} - starts with 'of' after inference")
                                continue
                            if re.search(r'\b(husband|wife|daughter|son|father|mother|brother|sister) of\b', single_name, re.IGNORECASE):
                                logger.debug(f"Skipping {single_name} - contains relationship word after inference")
                                continue
                            
                            # Apply infer_full_name for single-word names
                            if len(single_name.split()) == 1 and self.current_last_name:
                                single_name = infer_full_name(single_name, self.current_last_name)
                                logger.debug(f"Inferred full name for single name: {single_name}")
                            
                            # Determine relationship type based on pattern content
                            if 'companion' in pattern.lower():
                                logger.debug(f"Adding companion relationship: {single_name}")
                                relationships.append((single_name, 'companion', 'high'))
                            else:
                                logger.debug(f"Adding spouse relationship: {single_name}")
                                relationships.append((single_name, 'spouse', 'high'))
        
        # Determine context (e.g., "survived by", "preceded by")
        context = None
        context_patterns = {
            'survived by': r'survived by',
            'preceded by': r'preceded by',
            'married to': r'married to',
        }
        for ctx, pattern in context_patterns.items():
            if re.search(pattern, sentence, re.IGNORECASE):
                context = ctx
                logger.debug(f"Found context: {context}")
                break
        
        result = ProcessedSentence(
            text=sentence,
            relationships=relationships,
            context=context
        )
        logger.debug(f"Processed sentence result: {result}")
        return result 
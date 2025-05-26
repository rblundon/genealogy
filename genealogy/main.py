"""
Main script for processing obituaries.
"""

import json
import logging
import argparse
import re
from genealogy.core.obituary_processor import ObituaryProcessor
from genealogy.core.name_parser import NameParser
from genealogy.core.patterns import NAME_PATTERNS, DEATH_PATTERNS
from genealogy.core.date_normalizer import DateNormalizer
from genealogy.core.obituary_utils import add_to_input_file, get_next_individual_id, link_people
from genealogy.core.name_extractor import NameExtractor
from genealogy.core.relationship_extraction import extract_spouses_and_companions
from genealogy.core.text_processor import TextProcessor

def extract_maiden_name(obituary_text: str) -> str | None:
    """
    Extract maiden name from obituary text if present.
    
    Args:
        obituary_text: The obituary text to search
        
    Returns:
        The maiden name if found, None otherwise
    """
    for pattern in NAME_PATTERNS['maiden_name']:
        match = re.search(pattern, obituary_text)
        if match:
            # Try each capture group
            for group in match.groups():
                if group:
                    return group.strip()
    return None

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process obituaries from a JSON file.')
    parser.add_argument('input_file', help='Path to the input JSON file')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh of all obituaries')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help='Set the logging level')
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,  # Set the logging level to DEBUG
        format='%(levelname)s:%(name)s:%(message)s'
    )
    
    # Initialize the obituary processor
    processor = ObituaryProcessor(args.input_file)
    
    # Process the obituaries
    try:
        processor.process_obituaries(force_refresh=args.force_refresh)
    except Exception as e:
        logging.error(f"Error processing file {args.input_file}: {str(e)}")
        raise
        
    logging.info("Processing complete!")

    # Read the input file
    with open(args.input_file, 'r') as f:
        people = json.load(f)
    
    # Filter people with obituary_text and sort by death_date
    people_with_obits = [p for p in people if p.get('obituary_text')]
    
    def get_sort_key(person):
        death_date = person.get('death_date')
        if death_date is None:
            return '9999-99-99'  # Put people with no death date at the end
        return death_date
    
    people_with_obits.sort(key=get_sort_key)
    
    # Process each person's obituary text sentence by sentence
    for person in people_with_obits:
        death_date = person.get('death_date', 'Unknown')
        logging.info(f"Processing {person.get('full_name')} (died {death_date})")
        
        obituary_text = person.get('obituary_text', '')
        current_last_name = person.get('last_name')
        current_person_id = person.get('id')
        
        # Create a TextProcessor for this person
        text_processor = TextProcessor(people, current_person_id)
        processed_sentences = text_processor.process_text(obituary_text)
        
        # Print each processed sentence and its relationships
        for sentence in processed_sentences:
            logging.info(f"\nSentence: {sentence.sentence}")
            if sentence.relationships:
                logging.info("Relationships found:")
                for rel in sentence.relationships:
                    logging.info(f"  - {rel['name']} ({rel['type']}, confidence: {rel['confidence']})")
            if sentence.context:
                logging.info(f"Context: {sentence.context}")

    # Write updated data back to file
    with open(args.input_file, 'w') as f:
        json.dump(people, f, indent=2)
    
    logging.info("Updates complete!")

    # Calculate death date from age if not present
    for person in people_with_obits:
        if person.get('death_date') is None and person.get('age') is not None:
            # Extract obituary date from text
            obituary_text = person.get('obituary_text', '')
            obituary_date = None
            for pattern in DEATH_PATTERNS:
                match = re.search(pattern, obituary_text, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    obituary_date = DateNormalizer.parse_date(date_str)
                    if obituary_date:
                        break
            if obituary_date:
                person['death_date'] = obituary_date
                logging.info(f"Calculated death date for {person.get('full_name')}: {obituary_date}")

    # Write updated data back to file again
    with open(args.input_file, 'w') as f:
        json.dump(people, f, indent=2)
    
    logging.info("Updates complete!")

if __name__ == '__main__':
    main() 
"""
Main script for processing obituaries.
"""

import json
import logging
import argparse
import re
from genealogy.core.obituary_processor import ObituaryProcessor
from genealogy.core.name_parser import NameParser
from genealogy.core.patterns import NAME_PATTERNS

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
    parser = argparse.ArgumentParser(description='Process obituary URLs from a JSON file.')
    parser.add_argument('input_file', help='Path to the input JSON file')
    parser.add_argument('--refresh-obits', action='store_true', help='Force refresh of obituary data')
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
# Phase 1: Extract the data from the obituary
    # Process the file
    logging.info("Starting obituary processing...")
    processor = ObituaryProcessor(args.input_file)
    processor.process_file(force_refresh=args.refresh_obits)
    logging.info("Processing complete!")

    # If we just wanted to refresh obits, exit here
    if args.refresh_obits:
        logging.info("Exiting after refresh-obits phase as requested.")
        return

# Phase 2: Update people with obituaries.
    # Determine name chunklets from full_name
    logging.info("Updating people with obituaries...")
    
    # Read the input file
    with open(args.input_file, 'r') as f:
        people = json.load(f)
    
    # Initialize name parser
    name_parser = NameParser()
    
    # Process each person with an obituary
    for person in people:
        if person.get('obituary_text'):
            try:
                parsed_name = name_parser.parse_name(person['full_name'])
                # Update person with parsed name components
                person.update({
                    'first_name': parsed_name.first_name,
                    'middle_name': parsed_name.middle_name,
                    'last_name': parsed_name.last_name,
                    'nickname': parsed_name.nickname,
                    'suffix': parsed_name.suffix,
                    'deceased': True
                })
                
                # Extract and log maiden name if present
                maiden_name = extract_maiden_name(person['obituary_text'])
                if maiden_name:
                    person['maiden_name'] = maiden_name
                    logging.info(f"Found maiden name '{maiden_name}' for {person['full_name']}")
                
                logging.info(f"Processed name for {person['full_name']}")
            except Exception as e:
                logging.error(f"Error processing name for {person['full_name']}: {str(e)}")
        else:
            # Set deceased to False for people without obituaries
            person['deceased'] = False
    
    # Write updated data back to file
    with open(args.input_file, 'w') as f:
        json.dump(people, f, indent=2)
    
    logging.info("Updates complete!")


if __name__ == '__main__':
    main() 
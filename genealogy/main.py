"""
Main script for processing obituaries and extracting information.
"""

import argparse
import json
import logging
from genealogy.core.obituary_reader import ObituaryReader
from genealogy.core.people_finder import PeopleFinder
from genealogy.core.obituary_catalog import ObituaryCatalog

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    """Main function to process obituaries and extract information."""
    parser = argparse.ArgumentParser(description='Process obituaries and extract information.')
    parser.add_argument('input_file', help='Input JSON file containing person records')
    parser.add_argument('--refresh-obits', action='store_true', help='Force refresh of obituaries')
    args = parser.parse_args()

    setup_logging()
    logging.info("Starting obituary processing...")

    # Phase 1: Get/Update obituaries
    logging.info("\nPhase 1: Get/Update obituaries")
    reader = ObituaryReader(args.input_file, args.input_file, args.refresh_obits)
    reader.read_obituaries()

    # Write results back to input file and re-read for Phase 2
    with open(args.input_file, 'r') as f:
        people = json.load(f)

    # Phase 2: Process obituary owner names
    logging.info("\nPhase 2: Process obituary owner names")
    finder = PeopleFinder()
    for person in people:
        if person.get('obituary_text'):
            finder.process_obituary(person)

    # Update obituary catalog
    catalog = ObituaryCatalog()
    catalog.update_catalog(people)

    logging.info("\nProcessing complete!")

if __name__ == '__main__':
    main() 
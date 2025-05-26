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
from genealogy.core.date_normalizer import DateNormalizer
from genealogy.core.obituary_utils import add_to_input_file, get_next_individual_id, link_people
from genealogy.core.name_extractor import NameExtractor
from genealogy.core.relationship_extraction import extract_spouses_and_companions

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
    logging.info("Updating name details ...")
    # Process each person with an obituary
    for person in people:
        if person.get('obituary_text'):
            try:
                parsed_name = name_parser.parse_name(person['full_name'])
                logging.info("Updating name details and setting as deceased for %s", person['full_name'])
                person.update({
                    'first_name': parsed_name.first_name,
                    'middle_name': parsed_name.middle_name,
                    'last_name': parsed_name.last_name,
                    'nickname': parsed_name.nickname,
                    'suffix': parsed_name.suffix,
                    'deceased': True
                })
                # Use extract_spouses_and_companions directly instead of RelationshipFinder
                current_last_name = person['last_name']
                relationships = extract_spouses_and_companions(person['obituary_text'], current_last_name)
                spouse_name = None
                companion_name = None
                for name, rel, _ in relationships:
                    if rel == 'spouse' and not spouse_name:
                        spouse_name = name
                    elif rel == 'companion' and not companion_name:
                        companion_name = name
                person['spouse'] = spouse_name
                person['companion'] = companion_name

                # Add new spouse/companion to in-memory people list if not already present
                def add_person_if_new(name):
                    if name and not any(p.get('full_name') == name for p in people):
                        # Parse the name using NameParser
                        parsed_name = name_parser.parse_name(name)
                        new_entry = {
                            'full_name': name,
                            'id': get_next_individual_id(),  # Assign a new ID
                            'location': None,
                            'obituary_text': None,
                            'birth_date': None,
                            'death_date': None,
                            'age': None,
                            'gender': None,
                            'spouse': None,
                            'companion': None,
                            'deceased': False,
                            # Add parsed name fields
                            'first_name': parsed_name.first_name,
                            'middle_name': parsed_name.middle_name,
                            'last_name': parsed_name.last_name,
                            'nickname': parsed_name.nickname,
                            'suffix': parsed_name.suffix
                        }
                        people.append(new_entry)
                        return new_entry['id']
                    return next((p['id'] for p in people if p.get('full_name') == name), None)

                # Add and link spouse if present
                if spouse_name:
                    spouse_id = add_person_if_new(spouse_name)
                    if spouse_id:
                        link_people(people, person['id'], spouse_id, 'spouse')

                # Add and link companion if present
                if companion_name:
                    companion_id = add_person_if_new(companion_name)
                    if companion_id:
                        link_people(people, person['id'], companion_id, 'companion')

                birth_date = DateNormalizer.find_birth_date(person['obituary_text'])
                death_date = DateNormalizer.find_death_date(person['obituary_text'])
                age = DateNormalizer.find_age(person['obituary_text'])
                if age and death_date and not birth_date:
                    birth_date = DateNormalizer.calculate_birth_date(death_date, age)
                if birth_date and death_date and not age:
                    age = DateNormalizer.calculate_age(birth_date, death_date)
                logging.info(f"Processing complete.")
                if 'spouse' not in person:
                    person['spouse'] = None
                if 'companion' not in person:
                    person['companion'] = None
            except Exception as e:
                logging.error(f"Error processing name for {person['full_name']}: {str(e)}")
        else:
            person['deceased'] = False

    # Write updated data back to file
    with open(args.input_file, 'w') as f:
        json.dump(people, f, indent=2)
    
    logging.info("Updates complete!")

if __name__ == '__main__':
    main() 
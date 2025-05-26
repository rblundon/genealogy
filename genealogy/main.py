"""
Main script for processing obituaries.
"""

import logging
import argparse
from genealogy.core.obituary_processor import ObituaryProcessor

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

if __name__ == '__main__':
    main() 
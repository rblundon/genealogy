import argparse
import sys
from .core.url_importer import URLImporter
from .utils.logging_config import setup_logging

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Genealogy Mapper - A tool for processing obituary URLs"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--import-url",
        metavar="URL",
        help="Import a new obituary URL"
    )
    
    return parser.parse_args()

def main() -> int:
    """Main entry point for the application."""
    args = parse_args()
    
    # Set up logging
    logger = setup_logging(debug=args.debug)
    logger.info("Starting Genealogy Mapper")
    
    try:
        if args.import_url:
            importer = URLImporter()
            if importer.import_url(args.import_url):
                logger.info("URL import completed successfully")
                return 0
            else:
                logger.error("URL import failed")
                return 1
        else:
            logger.error("No command specified. Use --help for available commands.")
            return 1
            
    except Exception as e:
        logger.exception("An error occurred")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
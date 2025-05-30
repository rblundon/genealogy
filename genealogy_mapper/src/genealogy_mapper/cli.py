import logging
import click
from rich.console import Console
from rich.logging import RichHandler
from .core.url_importer import URLImporter
from .core.obituary_scraper import ObituaryScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("genealogy_mapper")
console = Console()

@click.command()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--import-url', metavar='URL', help='Import an obituary URL')
@click.option('--extract-text', is_flag=True, help='Extract and display obituary text')
def cli(debug, import_url, extract_text):
    """Genealogy Mapper - A tool for processing and managing genealogy data."""
    if debug:
        logger.setLevel(logging.DEBUG)
    logger.info("Starting Genealogy Mapper")

    if import_url:
        importer = URLImporter()
        scraper = ObituaryScraper()
        if importer.import_url(import_url):
            logger.info("URL import completed successfully")
            if extract_text:
                logger.info("Extracting obituary text...")
                result = scraper.extract_legacy_com(import_url)
                if result:
                    console.print("\n[bold blue]Obituary Text:[/bold blue]")
                    console.print(result["text"])
                    console.print("\n[bold blue]Metadata:[/bold blue]")
                    for key, value in result["metadata"].items():
                        console.print(f"{key.replace('_', ' ').title()}: {value}")
                else:
                    logger.error("Failed to extract obituary text")
        else:
            logger.error("URL import failed")
    else:
        logger.error("No command specified. Use --help for available options.")

if __name__ == '__main__':
    cli() 
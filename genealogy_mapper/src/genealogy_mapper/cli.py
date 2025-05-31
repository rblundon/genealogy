import logging
import click
from rich.console import Console
from rich.logging import RichHandler
from .core.url_importer import URLImporter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("genealogy_mapper")
console = Console()

def display_obituary_text(text: str, metadata: dict) -> None:
    """Display obituary text and metadata."""
    console.print("\n[bold blue]Obituary Text:[/bold blue]")
    console.print(text)
    console.print("\n[bold blue]Metadata:[/bold blue]")
    for key, value in metadata.items():
        console.print(f"{key.replace('_', ' ').title()}: {value}")

@click.group()
@click.option('--timeout', type=int, default=3, help='Maximum time to wait for elements to load, in seconds')
@click.pass_context
def cli(ctx, timeout):
    """Genealogy Mapper CLI."""
    ctx.ensure_object(dict)
    ctx.obj['timeout'] = timeout
    logger.info("Starting Genealogy Mapper")

@cli.command()
@click.option('--import-url', help='Import a new obituary URL')
@click.pass_context
def import_url(ctx, import_url):
    """Import a new obituary URL."""
    importer = URLImporter(timeout=ctx.obj['timeout'])
    if importer.import_url(import_url):
        logger.info("URL import completed successfully")
    else:
        logger.error("URL import failed")

@cli.command()
@click.pass_context
def extract_obit_text(ctx):
    """Process all pending URLs and extract their text."""
    logger.info("Processing pending obituary URLs...")
    importer = URLImporter(timeout=ctx.obj['timeout'])
    processed = importer.process_pending_urls()
    if processed:
        logger.info(f"Successfully processed {len(processed)} URLs")
    else:
        logger.info("No URLs were processed")

if __name__ == '__main__':
    cli() 
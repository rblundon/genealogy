import logging
import click
from rich.console import Console
from rich.logging import RichHandler
from .core.url_importer import URLImporter
from .core.db_init import init_db
from .core.config import Config
from typing import Optional, Dict, Any, List
import sys
import json
from pathlib import Path
from .core.ner_processor import ObituaryNERProcessor
from .core.hybrid_processor import HybridProcessor
from .core.neo4j_ops import Neo4jOperations, Conflict, ConflictResolution
import os
from datetime import datetime

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

def format_for_neo4j(person_info: Dict[str, Any]) -> Dict[str, Any]:
    """Format person information for Neo4j database."""
    # Convert dates to ISO format if they exist
    if person_info.get('birth_date'):
        try:
            birth_date = datetime.strptime(person_info['birth_date'], "%d %b %Y")
            person_info['birth_date'] = birth_date.isoformat()
        except ValueError:
            pass
            
    if person_info.get('death_date'):
        try:
            death_date = datetime.strptime(person_info['death_date'], "%d %b %Y")
            person_info['death_date'] = death_date.isoformat()
        except ValueError:
            pass
    
    # Add metadata about data quality
    person_info['data_quality'] = {
        'birth_year_calculated': person_info.get('is_birth_year_calculated', False),
        'confidence': person_info.get('confidence', 0.0),
        'source': person_info.get('source', 'unknown')
    }
    
    # Remove internal processing fields
    person_info.pop('is_birth_year_calculated', None)
    person_info.pop('confidence', None)
    person_info.pop('source', None)
    
    return person_info

def interactive_conflict_resolver(conflicts: List[Conflict]) -> List[Conflict]:
    """Interactively resolve conflicts with user input."""
    resolved_conflicts = []
    
    for conflict in conflicts:
        console.print(f"\n[bold yellow]Conflict detected for {conflict.field}:[/bold yellow]")
        console.print(f"Existing value: {conflict.existing_value}")
        console.print(f"New value: {conflict.new_value}")
        
        while True:
            choice = console.input(
                "\nHow would you like to resolve this conflict?\n"
                "1. Keep existing value\n"
                "2. Use new value\n"
                "3. Merge values (for dates, keep more specific)\n"
                "4. Skip this field\n"
                "Choice (1-4): "
            )
            
            if choice == "1":
                conflict.resolution = ConflictResolution.KEEP_EXISTING
                break
            elif choice == "2":
                conflict.resolution = ConflictResolution.USE_NEW
                break
            elif choice == "3":
                conflict.resolution = ConflictResolution.MERGE
                break
            elif choice == "4":
                conflict.resolution = ConflictResolution.SKIP
                break
            else:
                console.print("[red]Invalid choice. Please try again.[/red]")
                
        resolved_conflicts.append(conflict)
        
    return resolved_conflicts

@click.group()
@click.option('--timeout', type=int, default=3, help='Maximum time to wait for elements to load, in seconds')
@click.option('--obituaries-file', type=click.Path(), help='Path to the obituary URLs JSON file (default: project root/obituary_urls.json)')
@click.pass_context
def cli(ctx, timeout, obituaries_file):
    """Genealogy Mapper CLI."""
    ctx.ensure_object(dict)
    ctx.obj['timeout'] = timeout
    ctx.obj['json_path'] = obituaries_file
    logger.info("Starting Genealogy Mapper")

@cli.command()
@click.option('--import-url', help='Import a new obituary URL')
@click.pass_context
def import_url(ctx, import_url):
    """Import a new obituary URL."""
    importer = URLImporter(timeout=ctx.obj['timeout'], json_path=ctx.obj['json_path'])
    if importer.import_url(import_url):
        logger.info("URL import completed successfully")
    else:
        logger.error("URL import failed")

@cli.command()
@click.pass_context
def extract_obit_text(ctx):
    """Process all pending URLs and extract their text."""
    logger.info("Processing pending obituary URLs...")
    importer = URLImporter(timeout=ctx.obj['timeout'], json_path=ctx.obj['json_path'])
    processed = importer.process_pending_urls()
    if processed:
        logger.info(f"Successfully processed {len(processed)} URLs")
    else:
        logger.info("No URLs were processed")

@cli.command()
@click.option('--db-directory', type=click.Path(), help='Path to Neo4j database directory (default: project_root/data/neo4j)')
@click.option('--config-path', type=click.Path(), help='Path to config file (default: project_root/config.yaml)')
def init_database(db_directory: Optional[str] = None, config_path: Optional[str] = None):
    """Initialize the Neo4j database with GEDCOM schema."""
    init_db(db_directory, config_path)

@cli.command()
@click.option('--config-path', type=click.Path(), help='Path to save config file (default: project_root/config.yaml)')
def create_config(config_path: Optional[str] = None):
    """Create a default configuration file."""
    try:
        Config.create_default_config(config_path)
        logger.info("Default configuration file created successfully")
    except Exception as e:
        logger.error(f"Failed to create configuration file: {e}")
        sys.exit(1)

@cli.command()
@click.option('--input-file', '-i', required=True, help='Path to JSON file containing obituary URLs and text')
@click.option('--output-file', '-o', help='Path to output JSON file (default: obituary_people.json)')
@click.option('--use-hybrid/--use-ner', default=True, help='Use hybrid processor (OpenAI + NER) or just NER')
def add_obit_people(input_file: str, output_file: Optional[str] = None, use_hybrid: bool = True):
    """Process obituaries and extract person information."""
    try:
        # Initialize processor
        if use_hybrid:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY environment variable not set")
                sys.exit(1)
            processor = HybridProcessor(api_key)
        else:
            processor = ObituaryNERProcessor()
        
        # Read input file
        with open(input_file, 'r') as f:
            data = json.load(f)
            
        # Process each obituary
        results = []
        for item in data.get('urls', []):
            if not item.get('extracted_text'):
                logger.warning(f"No text found for URL: {item.get('url')}")
                continue
                
            # Extract person information
            if use_hybrid:
                person_info = processor.extract_info(item['extracted_text'])
                # Convert ExtractionResult to dict
                person_dict = {
                    'full_name': person_info.full_name,
                    'maiden_name': person_info.maiden_name,
                    'birth_date': person_info.birth_date,
                    'death_date': person_info.death_date,
                    'age': person_info.age,
                    'gender': person_info.gender,
                    'is_birth_year_calculated': person_info.is_birth_year_calculated,
                    'confidence': person_info.confidence,
                    'source': person_info.source
                }
            else:
                person_info = processor.extract_person_info(item['extracted_text'])
                person_dict = {
                    'full_name': person_info.full_name,
                    'birth_date': person_info.birth_date,
                    'death_date': person_info.death_date,
                    'birth_place': person_info.birth_place,
                    'death_place': person_info.death_place,
                    'age': person_info.age,
                    'gender': person_info.gender,
                    'occupation': person_info.occupation,
                    'education': person_info.education,
                    'military_service': person_info.military_service,
                    'organizations': person_info.organizations
                }
            
            # Format for Neo4j
            person_dict = format_for_neo4j(person_dict)
            
            # Add URL and status to the result
            result = {
                'url': item['url'],
                'status': 'success' if person_dict['full_name'] else 'failed',
                'person_info': person_dict
            }
            results.append(result)
            
        # Write results to output file
        output_file = output_file or 'obituary_people.json'
        with open(output_file, 'w') as f:
            json.dump({'results': results}, f, indent=2)
            
        logger.info(f"Processed {len(results)} obituaries. Results written to {output_file}")
        
    except Exception as e:
        logger.error(f"Error processing obituaries: {e}")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--input-file', '-i', required=True, help='Path to JSON file containing processed person information')
@click.option('--config-path', type=click.Path(), help='Path to config file (default: project_root/config.yaml)')
@click.option('--dry-run', is_flag=True, help='Show what would be imported without making changes')
@click.option('--force', is_flag=True, help='Skip validation and force import')
@click.option('--interactive', is_flag=True, help='Interactively resolve conflicts')
def import_to_neo4j(input_file: str, config_path: Optional[str] = None, dry_run: bool = False, force: bool = False, interactive: bool = False):
    """Import processed person information into Neo4j database."""
    try:
        # Load configuration
        config = Config(config_path)
        neo4j_config = config.get_neo4j_config()
        
        # Initialize Neo4j operations
        neo4j_ops = Neo4jOperations(
            uri=neo4j_config['uri'],
            user=neo4j_config['user'],
            password=neo4j_config['password'],
            conflict_resolver=interactive_conflict_resolver if interactive else None
        )
        
        # Read input file
        with open(input_file, 'r') as f:
            data = json.load(f)
            
        # Import data
        stats = neo4j_ops.import_batch(data['results'], dry_run=dry_run)
        
        # Log results
        if dry_run:
            console.print("\n[bold blue]Dry Run Results:[/bold blue]")
            console.print(f"Total records: {stats['total']}")
            console.print(f"Planned creates: {stats['planned_creates']}")
            console.print(f"Planned updates: {stats['planned_updates']}")
            console.print(f"Planned skips: {stats['planned_skips']}")
            
            console.print("\n[bold blue]Detailed Operations:[/bold blue]")
            for op in stats['operations']:
                console.print(f"\n[bold]{op['type'].upper()}[/bold] - {op['person']}")
                console.print(f"URL: {op['url']}")
                if op['validation']['errors']:
                    console.print("[red]Errors:[/red]")
                    for error in op['validation']['errors']:
                        console.print(f"  - {error}")
                if op['validation']['warnings']:
                    console.print("[yellow]Warnings:[/yellow]")
                    for warning in op['validation']['warnings']:
                        console.print(f"  - {warning}")
                if op['conflicts']:
                    console.print("[yellow]Conflicts:[/yellow]")
                    for conflict in op['conflicts']:
                        console.print(f"  - {conflict['field']}:")
                        console.print(f"    Existing: {conflict['existing_value']}")
                        console.print(f"    New: {conflict['new_value']}")
                        if conflict['resolution']:
                            console.print(f"    Resolution: {conflict['resolution']}")
        else:
            console.print("\n[bold blue]Import Results:[/bold blue]")
            console.print(f"Total records: {stats['total']}")
            console.print(f"Successful: {stats['success']}")
            console.print(f"Failed: {stats['failed']}")
            console.print(f"Created: {stats['created']}")
            console.print(f"Updated: {stats['updated']}")
            
            if stats['messages']:
                console.print("\n[bold blue]Messages:[/bold blue]")
                for msg in stats['messages']:
                    if 'Error' in msg or 'Failed' in msg:
                        console.print(f"[red]{msg}[/red]")
                    elif 'Warning' in msg:
                        console.print(f"[yellow]{msg}[/yellow]")
                    else:
                        console.print(msg)
        
        # Close Neo4j connection
        neo4j_ops.close()
        
    except Exception as e:
        logger.error(f"Error importing to Neo4j: {e}")
        raise click.ClickException(str(e))

if __name__ == '__main__':
    cli() 
import logging
import click
from rich.console import Console
from rich.logging import RichHandler
from .core.url_importer import URLImporter
from .core.db_init import init_db
from .core.config import Config
from typing import Optional, Dict, Any, List, Set, Tuple
import sys
import json
from pathlib import Path
from .core.ner_processor import ObituaryNERProcessor
from .core.hybrid_processor import HybridProcessor
from .core.neo4j_ops import Neo4jOperations, Conflict, ConflictResolution
import os
from datetime import datetime
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
import importlib
from openai import OpenAI
from .core.relationship_processor import RelationshipProcessor
from .core.visualizer import RelationshipVisualizer
import yaml

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
    
    # Normalize gender
    if person_info.get('gender'):
        gender = person_info['gender'].lower()
        valid_genders = {
            'm': 'M', 'male': 'M',
            'f': 'F', 'female': 'F',
            'u': 'U', 'unknown': 'U'
        }
        if gender in valid_genders:
            person_info['gender'] = valid_genders[gender]
    
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
@click.argument('url')
@click.option('--input-file', '-i', type=click.Path(), help='Path to the obituary URLs JSON file')
@click.pass_context
def import_url(ctx, url, input_file):
    """Import a new obituary URL."""
    # Use input_file if provided, otherwise use the one from context
    json_path = input_file or ctx.obj['json_path']
    if not json_path:
        logger.error("No input file specified. Use -i/--input-file or set --obituaries-file")
        click.echo("Error: No input file specified. Use -i/--input-file or set --obituaries-file", err=True)
        raise click.Abort()
        
    importer = URLImporter(timeout=ctx.obj['timeout'], json_path=json_path)
    if importer.import_url(url):
        logger.info("URL import completed successfully")
    else:
        logger.error("URL import failed")

def validate_obituary_json(data: Dict[str, Any]) -> List[str]:
    """Validate the structure of the obituary URLs JSON file."""
    errors = []
    
    # Check top-level structure
    if not isinstance(data, dict):
        errors.append("JSON must be an object")
        return errors
        
    if 'urls' not in data:
        errors.append("Missing required field: 'urls'")
        return errors
        
    if not isinstance(data['urls'], list):
        errors.append("'urls' must be an array")
        return errors
        
    # Validate each URL entry
    for i, url_entry in enumerate(data['urls']):
        if not isinstance(url_entry, dict):
            errors.append(f"URL entry {i} must be an object")
            continue
            
        # Required fields
        if 'url' not in url_entry:
            errors.append(f"URL entry {i} missing required field: 'url'")
        elif not isinstance(url_entry['url'], str):
            errors.append(f"URL entry {i}: 'url' must be a string")
            
        if 'status' not in url_entry:
            errors.append(f"URL entry {i} missing required field: 'status'")
        elif url_entry['status'] not in ['pending', 'completed', 'failed']:
            errors.append(f"URL entry {i}: 'status' must be one of: pending, completed, failed")
            
        # Optional fields
        if 'extracted_text' in url_entry and not isinstance(url_entry['extracted_text'], (str, type(None))):
            errors.append(f"URL entry {i}: 'extracted_text' must be a string or null")
            
        if 'metadata' in url_entry:
            if not isinstance(url_entry['metadata'], dict):
                errors.append(f"URL entry {i}: 'metadata' must be an object")
            else:
                for key, value in url_entry['metadata'].items():
                    if not isinstance(value, (str, type(None))):
                        errors.append(f"URL entry {i}: metadata field '{key}' must be a string or null")
    
    return errors

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if all required dependencies are installed."""
    required_packages = {
        'selenium': 'selenium',
        'playwright': 'playwright',
        'beautifulsoup4': 'bs4',
        'requests': 'requests',
        'neo4j': 'neo4j',
        'openai': 'openai',
        'spacy': 'spacy',
        'rich': 'rich'
    }
    
    missing_packages = []
    for package, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing_packages.append(package)
    
    # Check if Playwright browsers are installed
    if 'playwright' not in missing_packages:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browsers = p.chromium, p.firefox, p.webkit
                for browser in browsers:
                    try:
                        browser.launch()
                    except Exception:
                        missing_packages.append('playwright-browsers')
                        break
        except Exception:
            missing_packages.append('playwright-browsers')
    
    return len(missing_packages) == 0, missing_packages

def setup_logging(verbose: bool = False) -> None:
    """Set up logging with appropriate level and format."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

@cli.command()
@click.option(
    "--timeout",
    type=int,
    default=5,
    help="Timeout in seconds for web scraping operations",
)
@click.option(
    "--obituaries-file",
    "-i",
    "--input-file",
    type=click.Path(exists=True),
    required=True,
    help="Path to the obituary URLs JSON file",
)
@click.option(
    "--force-rescrape",
    is_flag=True,
    help="Force rescrape of all URLs regardless of status",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be processed without making changes",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def extract_obit_text(
    timeout: int,
    obituaries_file: str,
    force_rescrape: bool,
    dry_run: bool,
    verbose: bool
) -> None:
    """Extract text from pending obituary URLs."""
    try:
        # Set up logging
        setup_logging(verbose)
        logger = logging.getLogger("genealogy_mapper")
        
        # Validate and normalize file path
        try:
            file_path = os.path.abspath(obituaries_file)
            logger.info(f"Using obituary file: {file_path}")
            
            # Check if file is writable
            if not os.access(file_path, os.W_OK):
                logger.error(f"File is not writable: {file_path}")
                click.echo(f"Error: File is not writable: {file_path}", err=True)
                raise click.Abort()
                
            # Check if file is in a safe location (not system directories)
            system_dirs = ['/bin', '/sbin', '/usr', '/etc', '/var', '/opt']
            if any(file_path.startswith(d) for d in system_dirs):
                logger.error(f"File path is in a system directory: {file_path}")
                click.echo(f"Error: File path is in a system directory: {file_path}", err=True)
                raise click.Abort()
                
        except Exception as e:
            logger.error(f"Error validating file path: {str(e)}")
            click.echo(f"Error validating file path: {str(e)}", err=True)
            raise click.Abort()
        
        # Check dependencies
        deps_ok, missing = check_dependencies()
        if not deps_ok:
            click.echo("Error: Missing required dependencies:", err=True)
            for package in missing:
                click.echo(f"  - {package}", err=True)
            click.echo("\nInstall missing dependencies with:", err=True)
            if 'playwright-browsers' in missing:
                click.echo("pip install playwright", err=True)
                click.echo("playwright install", err=True)
            else:
                click.echo(f"pip install {' '.join(missing)}", err=True)
            raise click.Abort()
        
        # Load and validate JSON file
        try:
            logger.debug(f"Loading JSON file: {file_path}")
            with open(file_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Successfully loaded JSON file with {len(data.get('urls', []))} URLs")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON file: {str(e)}")
            click.echo(f"Error: Invalid JSON file: {str(e)}", err=True)
            raise click.Abort()
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            click.echo(f"Error: File not found: {file_path}", err=True)
            raise click.Abort()
            
        # Validate JSON structure
        logger.debug("Validating JSON structure")
        errors = validate_obituary_json(data)
        if errors:
            logger.error("Invalid JSON structure")
            click.echo("Error: Invalid JSON structure:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            raise click.Abort()
        
        # Load configuration
        try:
            logger.debug("Loading configuration")
            config = Config()
            neo4j_config = config.get_neo4j_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            click.echo(f"Error loading configuration: {str(e)}", err=True)
            click.echo("Try running 'create-config' first", err=True)
            raise click.Abort()
        
        # Initialize URL importer with timeout
        try:
            logger.debug(f"Initializing URL importer with timeout={timeout}")
            importer = URLImporter(
                timeout=timeout,
                json_path=file_path,
                force_rescrape=force_rescrape
            )
        except Exception as e:
            logger.error(f"Error initializing URL importer: {str(e)}")
            click.echo(f"Error initializing URL importer: {str(e)}", err=True)
            raise click.Abort()
        
        # Count URLs to process
        urls_to_process = [
            url for url in data['urls']
            if force_rescrape or url['status'] == 'pending'
        ]
        
        if not urls_to_process:
            logger.info("No URLs to process")
            click.echo("No URLs to process")
            return
            
        # Show dry run information
        if dry_run:
            click.echo("\n[bold blue]Dry Run Mode[/bold blue]")
            click.echo(f"Would process {len(urls_to_process)} URLs:")
            for url in urls_to_process:
                click.echo(f"  - {url['url']} (current status: {url['status']})")
            click.echo("\nNo changes will be made.")
            return
            
        # Process URLs with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Processing {len(urls_to_process)} URLs...",
                total=len(urls_to_process)
            )
            
            def progress_callback(url: str, status: str) -> None:
                progress.update(task, advance=1)
                progress.print(f"Processed: {url} ({status})")
                logger.debug(f"Processed URL: {url} ({status})")
            
            try:
                # Process pending URLs with progress tracking
                logger.info(f"Starting URL processing (force_rescrape={force_rescrape})")
                importer.process_pending_urls(
                    force_rescrape=force_rescrape,
                    progress_callback=progress_callback
                )
            except Exception as e:
                logger.error(f"Error processing URLs: {str(e)}")
                click.echo(f"\nError processing URLs: {str(e)}", err=True)
                raise click.Abort()
        
        logger.info("Text extraction completed successfully")
        click.echo("\nText extraction completed successfully")
        
    except click.Abort:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        click.echo(f"Unexpected error: {str(e)}", err=True)
        raise click.Abort()

@cli.command()
@click.option('--db-directory', type=click.Path(), help='Path to Neo4j database directory (default: project_root/data/neo4j)')
@click.option('--config-path', type=click.Path(), help='Path to config file (default: project_root/config.yaml)')
def init_database(db_directory: Optional[str] = None, config_path: Optional[str] = None):
    """Initialize the Neo4j database with GEDCOM schema."""
    init_db(db_directory, config_path)

@cli.command()
@click.option('--config-path', type=click.Path(), help='Path to save config file (default: project_root/config.yaml)')
def create_config(config_path: Optional[str] = None):
    """Create a default configuration file with Neo4j and OpenAI settings."""
    try:
        # If no config path is provided, use the default location
        if config_path is None:
            config_path = str(Path(__file__).parent.parent.parent / 'config.yaml')
        
        # Create default config with both Neo4j and OpenAI settings
        default_config = {
            'neo4j': {
                'uri': 'bolt://localhost:7687',
                'user': 'neo4j',
                'password': 'your_password_here',
                'max_connection_lifetime': 3600,
                'max_connection_pool_size': 50,
                'connection_timeout': 30
            },
            'openai': {
                'api_key': 'your_openai_api_key_here',
                'model': 'gpt-4-turbo-preview',
                'temperature': 0.1,
                'max_tokens': 2000
            }
        }
        
        # Create the config file
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
            
        logger.info(f"Default configuration file created successfully at {config_path}")
        click.echo(f"Configuration file created at: {config_path}")
        click.echo("\nPlease update the following values in the config file:")
        click.echo("1. Neo4j password")
        click.echo("2. OpenAI API key")
        click.echo("3. Any other settings you want to customize")
    except Exception as e:
        logger.error(f"Failed to create configuration file: {e}")
        click.echo(f"Error: Failed to create configuration file: {e}", err=True)
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

@cli.command()
@click.option('--input-file', '-i', required=True, help='Path to JSON file containing obituary URLs and text')
@click.option('--output-file', '-o', help='Path to output JSON file (default: obituary_relationships.json)')
@click.option('--force', is_flag=True, help='Force reprocessing of all obituaries regardless of status')
@click.option('--dry-run', is_flag=True, help='Show what would be processed without making changes')
def extract_relationships(input_file: str, output_file: Optional[str] = None, force: bool = False, dry_run: bool = False):
    """Extract relationships from obituaries using OpenAI analysis."""
    try:
        # Load configuration
        config = Config()
        openai_config = config.get_openai_config()
        
        # Check for OpenAI API key
        api_key = openai_config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OpenAI API key not found in configuration or environment")
            click.echo("Error: OpenAI API key not found. Please set it in your config file or OPENAI_API_KEY environment variable.", err=True)
            raise click.Abort()
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Read input file
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            click.echo(f"Error: Input file not found: {input_file}", err=True)
            raise click.Abort()
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in input file: {input_file}")
            click.echo(f"Error: Invalid JSON in input file: {input_file}", err=True)
            raise click.Abort()
            
        # Create backup of input file
        backup_file = f"{input_file}.bak"
        try:
            with open(backup_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Created backup of input file at: {backup_file}")
        except Exception as e:
            logger.warning(f"Failed to create backup file: {e}")
            
        # Process each obituary
        results = []
        for item in data.get('urls', []):
            if not item.get('extracted_text'):
                logger.warning(f"No text found for URL: {item.get('url')}")
                continue
                
            # Skip if already processed and not forcing
            if not force and item.get('relationships_extracted', {}).get('status') == 'completed':
                logger.info(f"Skipping already processed URL: {item.get('url')}")
                continue
                
            if dry_run:
                logger.info(f"Would process URL: {item.get('url')}")
                continue
                
            try:
                # Prepare the prompt for OpenAI
                prompt = f"""Use Named Entity Recognition (NER): Identify all individuals identified as having familial relationships in the sources and create a neo4j person node for each unique individual, using GEDCOM-compatible properties include neo4j relationship mappings.

Obituary text:
{item['extracted_text']}

Please provide a detailed analysis of all people and their relationships."""

                # Call OpenAI API
                response = client.chat.completions.create(
                    model=openai_config.get('model', 'gpt-4-turbo-preview'),
                    messages=[
                        {"role": "system", "content": "You are a genealogy expert specializing in extracting family relationships from obituaries."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=float(openai_config.get('temperature', 0.1)),
                    max_tokens=int(openai_config.get('max_tokens', 2000))
                )
                
                # Parse the response
                analysis = response.choices[0].message.content
                
                # Create a copy of the item with the new analysis
                processed_item = item.copy()
                processed_item['relationships_extracted'] = {
                    'status': 'completed',
                    'last_attempt': datetime.now().isoformat(),
                    'analysis': analysis
                }
                
                results.append(processed_item)
                logger.info(f"Successfully processed URL: {item.get('url')}")
                
            except Exception as e:
                logger.error(f"Error processing URL {item.get('url')}: {str(e)}")
                processed_item = item.copy()
                processed_item['relationships_extracted'] = {
                    'status': 'failed',
                    'last_attempt': datetime.now().isoformat(),
                    'error': str(e)
                }
                results.append(processed_item)
        
        # Write results to output file
        output_file = output_file or 'obituary_relationships.json'
        with open(output_file, 'w') as f:
            json.dump({
                'results': [{
                    'url': item['url'],
                    'analysis': item['relationships_extracted'].get('analysis'),
                    'status': item['relationships_extracted'].get('status'),
                    'last_attempt': item['relationships_extracted'].get('last_attempt')
                } for item in results]
            }, f, indent=2)
            
        logger.info(f"Processed {len(results)} obituaries")
        click.echo(f"Successfully processed {len(results)} obituaries")
        click.echo(f"Results written to: {output_file}")
        click.echo(f"Input file backup created at: {backup_file}")
        
    except Exception as e:
        logger.error(f"Error extracting relationships: {e}")
        raise click.ClickException(str(e))

@cli.command()
@click.option('--input-file', '-i', required=True, help='Path to JSON file containing relationship analysis')
@click.option('--dry-run', is_flag=True, help='Show what would be imported without making changes')
def import_relationships(input_file: str, dry_run: bool = False):
    """Import extracted relationships into Neo4j."""
    try:
        # Load configuration
        config = Config()
        neo4j_config = config.get_neo4j_config()
        
        # Initialize processor
        processor = RelationshipProcessor(neo4j_config)
        
        # Read input file
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        if dry_run:
            click.echo("\n[bold blue]Dry Run Mode[/bold blue]")
            click.echo("Would import the following relationships:")
            for item in data.get('results', []):
                click.echo(f"\nURL: {item['url']}")
                click.echo("Analysis preview:")
                click.echo(item['analysis'][:200] + "...")
            return
        
        # Process each analysis
        success_count = 0
        for item in data.get('results', []):
            try:
                # Process the analysis
                processed_data = processor.process_analysis(item['analysis'])
                if processed_data:
                    # Import into Neo4j
                    if processor.import_relationships(processed_data):
                        success_count += 1
                        click.echo(f"Successfully imported relationships from: {item['url']}")
                    else:
                        click.echo(f"Failed to import relationships from: {item['url']}", err=True)
            except Exception as e:
                click.echo(f"Error processing {item['url']}: {str(e)}", err=True)
        
        click.echo(f"\nSuccessfully imported {success_count} out of {len(data.get('results', []))} analyses")
        
    except Exception as e:
        logger.error(f"Error importing relationships: {e}")
        raise click.ClickException(str(e))
    finally:
        processor.close()

@cli.command()
@click.option('--output-file', '-o', help='Path to save the visualization (default: output/relationship_graph.png)')
@click.option('--format', type=click.Choice(['png', 'json']), default='png', help='Output format')
def visualize_relationships(output_file: Optional[str] = None, format: str = 'png'):
    """Visualize the current relationship graph."""
    try:
        # Load configuration
        config = Config()
        neo4j_config = config.get_neo4j_config()
        
        # Initialize processor and visualizer
        processor = RelationshipProcessor(neo4j_config)
        visualizer = RelationshipVisualizer()
        
        # Get the current graph
        graph_data = processor.get_relationship_graph()
        if not graph_data:
            click.echo("No relationship data found in the database", err=True)
            return
        
        if format == 'png':
            # Create visualization
            output_path = visualizer.visualize_graph(graph_data, output_file)
            if output_path:
                click.echo(f"Visualization saved to: {output_path}")
            else:
                click.echo("Failed to create visualization", err=True)
        else:
            # Export JSON
            output_path = visualizer.export_graph_json(graph_data, output_file)
            if output_path:
                click.echo(f"Graph data exported to: {output_path}")
            else:
                click.echo("Failed to export graph data", err=True)
        
    except Exception as e:
        logger.error(f"Error visualizing relationships: {e}")
        raise click.ClickException(str(e))
    finally:
        processor.close()

@cli.command()
@click.option('--config-path', type=click.Path(), help='Path to config file (default: project_root/config.yaml)')
def test_openai(config_path: str = None):
    """Test OpenAI configuration and connectivity."""
    try:
        # Load configuration
        config = Config(config_path)
        openai_config = config.get_openai_config()
        
        # Check for OpenAI API key
        api_key = openai_config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OpenAI API key not found in configuration or environment")
            click.echo("Error: OpenAI API key not found. Please set it in your config file or OPENAI_API_KEY environment variable.", err=True)
            raise click.Abort()
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Display configuration
        click.echo("\n[bold blue]OpenAI Configuration:[/bold blue]")
        click.echo(f"Model: {openai_config.get('model')}")
        click.echo(f"Temperature: {openai_config.get('temperature', 0.1)}")
        click.echo(f"Max Tokens: {openai_config.get('max_tokens', 2000)}")
        
        # Test API connection with a simple request
        click.echo("\n[bold blue]Testing API Connection...[/bold blue]")
        response = client.chat.completions.create(
            model=openai_config.get('model'),
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Please respond with 'Connection successful' if you can read this message."}
            ],
            temperature=float(openai_config.get('temperature', 0.1)),
            max_tokens=int(openai_config.get('max_tokens', 2000))
        )
        
        # Check response
        if response.choices[0].message.content.strip() == "Connection successful":
            click.echo("[green]\u2713 API Connection Test: Successful[/green]")
            click.echo("[green]\u2713 Configuration is working correctly[/green]")
        else:
            click.echo("[yellow]\u26a0 API Connection Test: Response unexpected[/yellow]")
            click.echo(f"Response: {response.choices[0].message.content}")
            
    except Exception as e:
        logger.error(f"Error testing OpenAI configuration: {e}")
        click.echo(f"[red]Error: {str(e)}[/red]", err=True)
        raise click.ClickException(str(e))

@cli.command()
def debug_relationships():
    """Debug command to check relationships in Neo4j."""
    try:
        processor = RelationshipProcessor()
        processor.debug_check_relationships()
        processor.close()
    except Exception as e:
        logger.error(f"Error in debug-relationships command: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    cli() 
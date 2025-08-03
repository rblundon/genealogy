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
from urllib.parse import urlparse
from .core.obituary_manager import ObituaryManager
from .core.obituary_processor import ObituaryProcessor

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
    try:
        from genealogy_mapper.core.db_init import init_db
        success = init_db(db_directory, config_path)
        if success:
            click.echo("✅ Database initialized successfully")
        else:
            click.echo("❌ Failed to initialize database")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@cli.command()
@click.option('--db-directory', type=click.Path(), help='Path to Neo4j database directory (default: project_root/data/neo4j)')
@click.option('--config-path', type=click.Path(), help='Path to config file (default: project_root/config.yaml)')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
def clear_database(db_directory: Optional[str] = None, config_path: Optional[str] = None, force: bool = False):
    """Clear all data from the Neo4j database."""
    try:
        if not force:
            if not click.confirm("⚠️  This will delete ALL data from the database. Are you sure?"):
                click.echo("Operation cancelled.")
                return
        
        from genealogy_mapper.core.config import Config
        from neo4j import GraphDatabase
        
        # Get configuration
        config = Config(config_path)
        neo4j_config = config.get_neo4j_config()
        
        # Connect to database
        driver = GraphDatabase.driver(
            neo4j_config['uri'], 
            auth=(neo4j_config['user'], neo4j_config['password'])
        )
        
        with driver.session() as session:
            # Clear all nodes and relationships
            result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted")
            record = result.single()
            deleted_count = record['deleted'] if record else 0
            
            click.echo(f"✅ Cleared {deleted_count} nodes from database")
        
        driver.close()
        
    except Exception as e:
        click.echo(f"Error: {str(e)}")

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

@cli.command()
@click.argument('url')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.option('--force', is_flag=True, help='Force rescrape even if URL exists')
def add_obituary(url: str, dry_run: bool, force: bool):
    """Add a new obituary URL to the database."""
    try:
        # Extract domain for source
        domain = urlparse(url).netloc.lower()
        source = "legacy.com" if "legacy.com" in domain else domain
        
        with ObituaryManager() as manager:
            obituary_id = manager.add_obituary_url(url, source, dry_run=dry_run, force_rescrape=force)
            if obituary_id:
                if not dry_run:
                    click.echo(f"Successfully added obituary URL: {url}")
                    click.echo(f"Source detected: {source}")
                    click.echo(f"Obituary ID: {obituary_id}")
                    click.echo(f"Next steps:")
                    click.echo(f"  1. Extract text: python -m genealogy_mapper.cli extract-text {obituary_id}")
                    click.echo(f"  2. Create individual: python -m genealogy_mapper.cli create-individual {obituary_id}")
                    click.echo(f"  3. Process relationships: python -m genealogy_mapper.cli process-relationships <individual_id>")
                else:
                    click.echo(f"[Dry Run] Would add obituary URL: {url}")
            else:
                click.echo(f"Failed to add obituary URL: {url}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@cli.command()
@click.option('--force', is_flag=True, help='Process all URLs, even if they have "completed" status')
def process_obituaries(force: bool):
    """Process all pending obituaries."""
    try:
        with ObituaryManager() as manager:
            processed = manager.process_pending_urls(force_rescrape=force)
            if processed:
                click.echo(f"Successfully processed {len(processed)} obituaries")
            else:
                click.echo("No obituaries to process")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@cli.command()
@click.option('--status', '-s', type=click.Choice(['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']), help='Filter by status')
@click.option('--source', '-s', help='Filter by source website')
def list_obituaries(status: Optional[str] = None, source: Optional[str] = None):
    """List obituaries in the database."""
    try:
        manager = ObituaryManager()
        
        query = "MATCH (o:Obituary)"
        params = {}
        
        if status or source:
            query += " WHERE"
            conditions = []
            if status:
                conditions.append("o.status = $status")
                params['status'] = status
            if source:
                conditions.append("o.source = $source")
                params['source'] = source
            query += " " + " AND ".join(conditions)
        
        query += " RETURN o ORDER BY o.created_at"
        
        with manager.driver.session() as session:
            result = session.run(query, **params)
            obituaries = [dict(record['o']) for record in result]
            
            if not obituaries:
                click.echo("No obituaries found.")
                return
            
            # Print in a table format
            click.echo("\nObituaries:")
            click.echo("-" * 100)
            click.echo(f"{'URL':<50} {'Status':<10} {'Source':<15} {'Created':<20}")
            click.echo("-" * 100)
            
            for obit in obituaries:
                created = obit['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                click.echo(f"{obit['url']:<50} {obit['status']:<10} {obit['source']:<15} {created:<20}")
            
            click.echo("-" * 100)
            click.echo(f"Total: {len(obituaries)} obituaries")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}")
    finally:
        manager.close()

@cli.command()
@click.argument('url')
@click.option('--status', '-s', required=True, type=click.Choice(['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']), help='New status')
@click.option('--error', '-e', help='Error message (required if status is FAILED)')
def update_obituary(url: str, status: str, error: Optional[str] = None):
    """Update the status of an obituary."""
    if status == 'FAILED' and not error:
        click.echo("Error: Error message is required when status is FAILED")
        return
    
    try:
        manager = ObituaryManager()
        if manager.update_obituary_status(url, status, error):
            click.echo(f"Successfully updated obituary status: {url} -> {status}")
        else:
            click.echo(f"Failed to update obituary status: {url}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")
    finally:
        manager.close()

@cli.command()
@click.argument('url')
@click.option('--id', help='Process existing obituary by ID instead of URL')
def process_obituary(url: str, id: Optional[str] = None):
    """Process an obituary to extract text and create person record."""
    try:
        with ObituaryProcessor() as processor:
            if id:
                # Process existing obituary by ID
                person_id = processor.process_obituary(id)
                if person_id:
                    click.echo(f"Successfully processed obituary {id} and created individual {person_id}")
                else:
                    click.echo(f"Failed to process obituary {id}")
            else:
                # Add new obituary and process it
                with ObituaryManager() as manager:
                    obituary_id = manager.add_obituary_url(url, detect_source(url))
                    if not obituary_id:
                        click.echo("Failed to add obituary URL")
                        return
                    
                    # Process the newly added obituary
                    person_id = processor.process_obituary(obituary_id)
                    if person_id:
                        click.echo(f"Successfully processed obituary {obituary_id} and created individual {person_id}")
                    else:
                        click.echo(f"Failed to process obituary {obituary_id}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        raise click.Abort()

@cli.command()
@click.option('--status', type=click.Choice(['COMPLETED', 'PROCESSED', 'ALL']), default='COMPLETED', help='Filter obituaries by status')
@click.option('--force', is_flag=True, help='Force reprocessing of all obituaries regardless of status')
@click.option('--dry-run', is_flag=True, help='Show what would be processed without making changes')
@click.option('--skip-extraction', is_flag=True, help='Skip OpenAI extraction and use existing analysis')
@click.option('--analysis-file', '-a', help='Use existing analysis file instead of extracting from database')
def process_relationships_from_db(status: str, force: bool = False, dry_run: bool = False, skip_extraction: bool = False, analysis_file: Optional[str] = None):
    """Complete workflow: Extract and import relationships from obituaries in the database."""
    try:
        # Load configuration
        config = Config()
        openai_config = config.get_openai_config()
        neo4j_config = config.get_neo4j_config()
        
        # Check for OpenAI API key (unless skipping extraction)
        if not skip_extraction and not analysis_file:
            api_key = openai_config.get('api_key') or os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.error("OpenAI API key not found in configuration or environment")
                click.echo("Error: OpenAI API key not found. Please set it in your config file or OPENAI_API_KEY environment variable.", err=True)
                raise click.Abort()
        
        # Initialize processors
        obituary_manager = ObituaryManager(neo4j_config)
        relationship_processor = RelationshipProcessor(neo4j_config)
        
        if analysis_file:
            # Use existing analysis file
            click.echo(f"Using existing analysis file: {analysis_file}")
            with open(analysis_file, 'r') as f:
                data = json.load(f)
            results = data.get('results', [])
        else:
            # Get obituaries from database
            status_filter = None if status == 'ALL' else status
            obituaries = obituary_manager.get_obituaries_with_text(status_filter)
            
            if not obituaries:
                click.echo("No obituaries with extracted text found in the database.")
                return
            
            click.echo(f"Found {len(obituaries)} obituaries with extracted text")
            
            if skip_extraction:
                click.echo("Skipping extraction step - no analysis data available")
                return
            
            # Extract relationships using OpenAI
            client = OpenAI(api_key=api_key)
            results = []
            
            for obituary in obituaries:
                if not obituary.get('extracted_text'):
                    logger.warning(f"No text found for obituary: {obituary.get('url')}")
                    continue
                
                if dry_run:
                    logger.info(f"Would process obituary: {obituary.get('url')}")
                    continue
                
                try:
                    # Check for cached analysis first
                    cached_analysis = obituary_manager.get_openai_cache(obituary.get('id'))
                    
                    if cached_analysis:
                        logger.info(f"Using cached analysis for obituary: {obituary.get('url')}")
                        analysis = cached_analysis
                    else:
                        logger.info(f"Generating new analysis for obituary: {obituary.get('url')}")
                        
                        # Prepare the prompt for OpenAI
                        prompt = f"""Use Named Entity Recognition (NER): Identify all individuals identified as having familial relationships in the sources and create a neo4j person node for each unique individual, using GEDCOM-compatible properties include neo4j relationship mappings.

Obituary text:
{obituary['extracted_text']}

Please provide a detailed analysis of all people and their relationships."""

                        # Call OpenAI API
                        response = client.chat.completions.create(
                            model=openai_config.get('model', 'gpt-3.5-turbo'),
                            messages=[
                                {"role": "system", "content": "You are a genealogy expert specializing in extracting family relationships from obituaries."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=float(openai_config.get('temperature', 0.1)),
                            max_tokens=int(openai_config.get('max_tokens', 2000))
                        )
                        
                        # Parse the response
                        analysis = response.choices[0].message.content
                        
                        # Store in cache
                        obituary_manager.store_openai_cache(obituary.get('id'), analysis)
                    
                    # Create result entry
                    processed_item = {
                        'url': obituary.get('url'),
                        'id': obituary.get('id'),
                        'analysis': analysis
                    }
                    
                    results.append(processed_item)
                    logger.info(f"Successfully extracted relationships from: {obituary.get('url')}")
                    
                except Exception as e:
                    logger.error(f"Error processing obituary {obituary.get('url')}: {str(e)}")
        
        # Import relationships into Neo4j
        if dry_run:
            click.echo("\n[bold blue]Dry Run Mode[/bold blue]")
            click.echo("Would import the following relationships:")
            for item in results:
                click.echo(f"\nURL: {item['url']}")
                click.echo("Analysis preview:")
                click.echo(item['analysis'][:200] + "...")
            return
        
        # Process each analysis
        success_count = 0
        for item in results:
            try:
                # Process the analysis
                processed_data = relationship_processor.process_analysis(item['analysis'])
                if processed_data:
                    # Import into Neo4j
                    if relationship_processor.import_relationships(processed_data):
                        success_count += 1
                        click.echo(f"Successfully imported relationships from: {item['url']}")
                    else:
                        click.echo(f"Failed to import relationships from: {item['url']}", err=True)
            except Exception as e:
                click.echo(f"Error processing {item['url']}: {str(e)}", err=True)
        
        click.echo(f"\nSuccessfully imported {success_count} out of {len(results)} analyses")
        
    except Exception as e:
        logger.error(f"Error processing relationships from database: {e}")
        raise click.ClickException(str(e))
    finally:
        obituary_manager.close()
        relationship_processor.close()

@cli.command()
def show_cache_status():
    """Show the status of OpenAI cache for all obituaries."""
    try:
        # Load configuration
        config = Config()
        neo4j_config = config.get_neo4j_config()
        
        # Initialize manager
        obituary_manager = ObituaryManager(neo4j_config)
        
        with obituary_manager.driver.session() as session:
            query = """
            MATCH (o:Obituary)
            RETURN o.id as id, o.url as url, o.openai_cache IS NOT NULL as has_cache, 
                   o.openai_cache_timestamp as cache_time
            ORDER BY o.created_at
            """
            result = session.run(query)
            records = [r.data() for r in result]
            
            if not records:
                click.echo("ℹ️  No obituaries found")
                return
                
            click.echo("\n📊 OpenAI Cache Status:")
            click.echo("=" * 80)
            
            cached_count = 0
            for record in records:
                status = "✅ Cached" if record['has_cache'] else "❌ Not cached"
                cache_time = record['cache_time'] if record['cache_time'] else "N/A"
                click.echo(f"{record['id']}: {status}")
                click.echo(f"  URL: {record['url']}")
                if record['has_cache']:
                    click.echo(f"  Cached: {cache_time}")
                click.echo()
                if record['has_cache']:
                    cached_count += 1
            
            total = len(records)
            click.echo(f"📈 Summary: {cached_count}/{total} obituaries cached ({cached_count/total*100:.1f}%)")
            
    except Exception as e:
        logger.error(f"Error showing cache status: {e}")
        raise click.ClickException(str(e))
    finally:
        obituary_manager.close()

@cli.command()
@click.option('--obituary-id', help='Clear cache for specific obituary ID')
@click.option('--all', is_flag=True, help='Clear cache for all obituaries')
def clear_openai_cache(obituary_id: Optional[str] = None, all: bool = False):
    """Clear cached OpenAI analysis from obituary records."""
    try:
        # Load configuration
        config = Config()
        neo4j_config = config.get_neo4j_config()
        
        # Initialize manager
        obituary_manager = ObituaryManager(neo4j_config)
        
        if obituary_id:
            # Clear cache for specific obituary
            with obituary_manager.driver.session() as session:
                query = """
                MATCH (o:Obituary {id: $obituary_id})
                REMOVE o.openai_cache, o.openai_cache_timestamp
                RETURN o
                """
                result = session.run(query, obituary_id=obituary_id)
                record = result.single()
                if record:
                    click.echo(f"✅ Cleared cache for obituary: {obituary_id}")
                else:
                    click.echo(f"❌ Obituary not found: {obituary_id}")
                    
        elif all:
            # Clear cache for all obituaries
            with obituary_manager.driver.session() as session:
                query = """
                MATCH (o:Obituary)
                WHERE o.openai_cache IS NOT NULL
                REMOVE o.openai_cache, o.openai_cache_timestamp
                RETURN count(o) as cleared_count
                """
                result = session.run(query)
                record = result.single()
                if record:
                    click.echo(f"✅ Cleared cache for {record['cleared_count']} obituaries")
                else:
                    click.echo("ℹ️  No cached obituaries found")
        else:
            click.echo("❌ Please specify --obituary-id or --all")
            
    except Exception as e:
        logger.error(f"Error clearing OpenAI cache: {e}")
        raise click.ClickException(str(e))
    finally:
        obituary_manager.close()

@cli.command()
@click.argument('obituary_id')
@click.option('--person-name', help='Name of the person to link to')
@click.option('--auto-link', is_flag=True, help='Automatically link without prompting')
def link_obituary_to_person(obituary_id: str, person_name: Optional[str] = None, auto_link: bool = False):
    """Link an obituary to a person with interactive confirmation."""
    try:
        # Load configuration
        config = Config()
        neo4j_config = config.get_neo4j_config()
        
        # Initialize manager
        obituary_manager = ObituaryManager(neo4j_config)
        
        # Get obituary details
        with obituary_manager.driver.session() as session:
            query = """
            MATCH (o:Obituary {id: $obituary_id})
            RETURN o
            """
            result = session.run(query, obituary_id=obituary_id)
            obituary = result.single()
            
            if not obituary:
                click.echo(f"❌ Obituary {obituary_id} not found")
                return
        
        obituary_data = dict(obituary['o'])
        click.echo(f"\n📰 Obituary: {obituary_data.get('url', 'Unknown URL')}")
        
        # Check if already linked
        existing_person = obituary_manager.get_person_by_obituary(obituary_id)
        if existing_person:
            click.echo(f"✅ Already linked to: {existing_person.get('name_full', 'Unknown')}")
            return
        
        # Extract person name from obituary if not provided
        if not person_name:
            # Try to extract from obituary text or URL
            extracted_text = obituary_data.get('extracted_text', '')
            if extracted_text:
                # Simple extraction - look for common patterns
                lines = extracted_text.split('\n')
                for line in lines[:10]:  # Check first 10 lines
                    if any(keyword in line.lower() for keyword in ['obituary', 'death', 'passed', 'died']):
                        # Extract name from this line
                        import re
                        name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', line)
                        if name_match:
                            person_name = name_match.group(1)
                            break
            
            if not person_name:
                # Extract from URL
                url = obituary_data.get('url', '')
                if 'name/' in url:
                    person_name = url.split('name/')[1].split('-obituary')[0].replace('-', ' ').title()
        
        if not person_name:
            click.echo("❌ Could not determine person name from obituary")
            return
        
        click.echo(f"👤 Extracted person name: {person_name}")
        
        # Find existing persons with similar names
        existing_persons = obituary_manager.find_existing_person_by_name(person_name)
        
        if existing_persons:
            click.echo(f"\n🔍 Found {len(existing_persons)} existing persons with similar names:")
            for i, person in enumerate(existing_persons, 1):
                click.echo(f"  {i}. {person.get('name_full', 'Unknown')} (ID: {person.get('id', 'Unknown')})")
            
            if not auto_link:
                choice = click.prompt(
                    f"\nSelect person to link to (1-{len(existing_persons)}) or 'n' for new person",
                    type=str
                )
                
                if choice.lower() == 'n':
                    # Create new person
                    click.echo("Creating new person...")
                    # This would need to be implemented based on your person creation logic
                    click.echo("⚠️  Person creation not yet implemented")
                    return
                else:
                    try:
                        selected_index = int(choice) - 1
                        if 0 <= selected_index < len(existing_persons):
                            selected_person = existing_persons[selected_index]
                            person_id = selected_person.get('id')
                            
                            if obituary_manager.link_obituary_to_person(obituary_id, person_id):
                                click.echo(f"✅ Successfully linked obituary to {selected_person.get('name_full')}")
                            else:
                                click.echo("❌ Failed to link obituary to person")
                        else:
                            click.echo("❌ Invalid selection")
                    except ValueError:
                        click.echo("❌ Invalid input")
            else:
                # Auto-link to first match
                selected_person = existing_persons[0]
                person_id = selected_person.get('id')
                
                if obituary_manager.link_obituary_to_person(obituary_id, person_id):
                    click.echo(f"✅ Auto-linked obituary to {selected_person.get('name_full')}")
                else:
                    click.echo("❌ Failed to auto-link obituary to person")
        else:
            click.echo(f"\n✅ No existing persons found with name '{person_name}'")
            click.echo("This obituary will be linked to a new person when processed")
            
    except Exception as e:
        logger.error(f"Error linking obituary to person: {e}")
        raise click.ClickException(str(e))
    finally:
        obituary_manager.close()

@cli.command()
@click.argument('person_id')
def show_person_obituary(person_id: str):
    """Show the obituary linked to a person."""
    try:
        # Load configuration
        config = Config()
        neo4j_config = config.get_neo4j_config()
        
        # Initialize manager
        obituary_manager = ObituaryManager(neo4j_config)
        
        obituary = obituary_manager.get_obituary_by_person(person_id)
        
        if obituary:
            click.echo(f"\n📰 Obituary for person {person_id}:")
            click.echo(f"  URL: {obituary.get('url', 'Unknown')}")
            click.echo(f"  Status: {obituary.get('status', 'Unknown')}")
            click.echo(f"  Created: {obituary.get('created_at', 'Unknown')}")
            
            # Check cache status
            has_cache = obituary_manager.has_openai_cache(obituary.get('id'))
            click.echo(f"  OpenAI Cache: {'✅ Available' if has_cache else '❌ Not available'}")
        else:
            click.echo(f"❌ No obituary found for person {person_id}")
            
    except Exception as e:
        logger.error(f"Error showing person obituary: {e}")
        raise click.ClickException(str(e))
    finally:
        obituary_manager.close()

@cli.command()
@click.argument('obituary_id')
def show_obituary_person(obituary_id: str):
    """Show the person linked to an obituary."""
    try:
        # Load configuration
        config = Config()
        neo4j_config = config.get_neo4j_config()
        
        # Initialize manager
        obituary_manager = ObituaryManager(neo4j_config)
        
        person = obituary_manager.get_person_by_obituary(obituary_id)
        
        if person:
            click.echo(f"\n👤 Person for obituary {obituary_id}:")
            click.echo(f"  Name: {person.get('name_full', 'Unknown')}")
            click.echo(f"  ID: {person.get('id', 'Unknown')}")
            click.echo(f"  Gender: {person.get('gender', 'Unknown')}")
            click.echo(f"  Birth Date: {person.get('birth_date', 'Unknown')}")
            click.echo(f"  Death Date: {person.get('death_date', 'Unknown')}")
        else:
            click.echo(f"❌ No person linked to obituary {obituary_id}")
            
    except Exception as e:
        logger.error(f"Error showing obituary person: {e}")
        raise click.ClickException(str(e))
    finally:
        obituary_manager.close()

@cli.command()
@click.option('--dry-run', is_flag=True, help='Show what would be changed without making changes')
def normalize_traditional_names(dry_run: bool = False):
    """Apply traditional naming conventions to existing relationships in the database.
    
    This command:
    1. Finds all SPOUSE_OF relationships
    2. Identifies wives and changes their last names to their husbands' last names
    3. Preserves original last names as maiden_name
    4. Updates the database accordingly
    """
    try:
        # Load configuration
        config = Config()
        neo4j_config = config.get_neo4j_config()
        
        # Initialize processor
        processor = RelationshipProcessor(neo4j_config)
        
        if dry_run:
            click.echo("\n[bold blue]Dry Run Mode[/bold blue]")
            click.echo("Would apply traditional naming conventions to the following relationships:")
        
        # Get all individuals with spouse relationships
        with processor.driver.session() as session:
            query = """
            MATCH (p1:Individual)-[r:SPOUSE_OF]->(p2:Individual)
            RETURN p1.id as person1_id, p1.name as person1_name, 
                   p2.id as person2_id, p2.name as person2_name
            """
            result = session.run(query)
            spouse_relationships = []
            
            for record in result:
                spouse_relationships.append({
                    'person1_id': record['person1_id'],
                    'person1_name': record['person1_name'],
                    'person2_id': record['person2_id'],
                    'person2_name': record['person2_name']
                })
            
            if not spouse_relationships:
                click.echo("No spouse relationships found in the database.")
                return
            
            click.echo(f"Found {len(spouse_relationships)} spouse relationships")
            
            # Process each spouse relationship
            for rel in spouse_relationships:
                person1_name_parts = rel['person1_name'].split()
                person2_name_parts = rel['person2_name'].split()
                
                # More conservative heuristic: only change if last names are clearly different
                # and one person has a middle name while the other doesn't
                person1_last = person1_name_parts[-1] if person1_name_parts else ''
                person2_last = person2_name_parts[-1] if person2_name_parts else ''
                
                # Skip if they already have the same last name
                if person1_last == person2_last:
                    continue
                
                # For traditional naming, we need to determine which is the wife
                # We'll use a conservative approach based on name structure
                # In traditional naming, the wife takes the husband's last name
                
                # Heuristic: wife typically has fewer name parts (First Last vs First Middle Last)
                # This is a conservative approach - only change if clear pattern exists
                if len(person1_name_parts) == 2 and len(person2_name_parts) > 2:
                    # Person1 has simple name (First Last), Person2 has middle name
                    # Assume Person1 is wife taking husband's name
                    wife_id = rel['person1_id']
                    wife_name = rel['person1_name']
                    husband_name = rel['person2_name']
                    wife_name_parts = person1_name_parts
                    husband_name_parts = person2_name_parts
                elif len(person2_name_parts) == 2 and len(person1_name_parts) > 2:
                    # Person2 has simple name (First Last), Person1 has middle name
                    # Assume Person2 is wife taking husband's name
                    wife_id = rel['person2_id']
                    wife_name = rel['person2_name']
                    husband_name = rel['person1_name']
                    wife_name_parts = person2_name_parts
                    husband_name_parts = person1_name_parts
                else:
                    # Both have similar name structures, skip to avoid incorrect changes
                    continue
                
                # Only proceed if the wife's current last name is different from husband's
                wife_last = wife_name_parts[-1]
                husband_last = husband_name_parts[-1]
                
                if wife_last != husband_last:
                    maiden_name = wife_last
                    
                    # Create new name with husband's last name
                    if len(wife_name_parts) == 2:
                        new_name = f"{wife_name_parts[0]} {husband_last}"
                    else:
                        new_name = f"{' '.join(wife_name_parts[:-1])} {husband_last}"
                    
                    if dry_run:
                        click.echo(f"\nWould update {wife_id}:")
                        click.echo(f"  '{wife_name}' -> '{new_name}'")
                        click.echo(f"  maiden_name: {maiden_name}")
                    else:
                        # Update the person node
                        update_query = """
                        MATCH (p:Individual {id: $id})
                        SET p.name = $new_name, p.maiden_name = $maiden_name
                        RETURN p
                        """
                        result = session.run(update_query, 
                            id=wife_id,
                            new_name=new_name,
                            maiden_name=maiden_name
                        )
                        
                        if result.single():
                            click.echo(f"Updated {wife_id}: '{wife_name}' -> '{new_name}' (maiden: {maiden_name})")
                        else:
                            click.echo(f"Failed to update {wife_id}", err=True)
        
        if dry_run:
            click.echo("\nNo changes made (dry run mode)")
        else:
            click.echo(f"\nSuccessfully processed {len(spouse_relationships)} spouse relationships")
        
    except Exception as e:
        logger.error(f"Error normalizing traditional names: {e}")
        raise click.ClickException(str(e))
    finally:
        processor.close()


@cli.command()
def interactive_relationship_mapper():
    """Interactive tool to add missing parental relationships.
    
    This command:
    1. Finds all individuals without parental relationships
    2. Asks user if they have additional information for each person
    3. Prompts for father's and mother's names
    4. Searches for existing persons or creates new ones
    5. Links parents to children in the database
    """
    try:
        # Load configuration
        config = Config()
        neo4j_config = config.get_neo4j_config()
        
        # Import the interactive mapper
        from genealogy_mapper.core.interactive_relationship_mapper import InteractiveRelationshipMapper
        
        # Run the interactive mapping
        with InteractiveRelationshipMapper(neo4j_config) as mapper:
            mapper.run_interactive_mapping()
        
    except Exception as e:
        logger.error(f"Error in interactive relationship mapper: {e}")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('obituary_id')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
def extract_text(obituary_id: str, dry_run: bool):
    """Extract text from an obituary URL."""
    try:
        with ObituaryProcessor() as processor:
            if dry_run:
                click.echo(f"[Dry Run] Would extract text for obituary: {obituary_id}")
                return
            
            text = processor.extract_and_store_text(obituary_id)
            if text:
                click.echo(f"Successfully extracted and stored text for obituary {obituary_id}")
                click.echo(f"Next step: python -m genealogy_mapper.cli create-individual {obituary_id}")
            else:
                click.echo(f"Failed to extract and store text for obituary {obituary_id}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@cli.command()
@click.argument('obituary_id')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
def create_individual(obituary_id: str, dry_run: bool):
    """Create an Individual record from extracted obituary text."""
    try:
        with ObituaryProcessor() as processor:
            if dry_run:
                click.echo(f"[Dry Run] Would create individual for obituary: {obituary_id}")
                return
            
            individual_id = processor.process_obituary(obituary_id)
            if individual_id:
                click.echo(f"Successfully created individual {individual_id} for obituary {obituary_id}")
                click.echo(f"Next step: python -m genealogy_mapper.cli process-relationships {individual_id}")
            else:
                click.echo(f"Failed to create individual for obituary {obituary_id}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@cli.command()
@click.argument('individual_id')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
def process_relationships(individual_id: str, dry_run: bool):
    """Process relationships for an Individual record."""
    try:
        if dry_run:
            click.echo(f"[Dry Run] Would process relationships for individual: {individual_id}")
            return
        
        # TODO: Implement relationship processing
        click.echo(f"Relationship processing for individual {individual_id} - Not yet implemented")
        click.echo(f"Workflow complete!")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

@cli.command()
@click.argument('url')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.option('--force', is_flag=True, help='Force rescrape even if URL exists')
def process_obituary(url: str, dry_run: bool, force: bool):
    """Complete obituary processing workflow from URL to individual creation."""
    try:
        click.echo(f"🔄 Starting complete obituary workflow for: {url}")
        
        # Step 1: Add obituary URL
        click.echo(f"\n📝 Step 1: Adding obituary URL...")
        domain = urlparse(url).netloc.lower()
        source = "legacy.com" if "legacy.com" in domain else domain
        
        with ObituaryManager() as manager:
            obituary_id = manager.add_obituary_url(url, source, dry_run=dry_run, force_rescrape=force)
            if not obituary_id:
                click.echo(f"❌ Failed to add obituary URL: {url}")
                return
            
            click.echo(f"✅ Successfully added obituary URL: {url}")
            click.echo(f"📋 Obituary ID: {obituary_id}")
            
            if dry_run:
                click.echo(f"[Dry Run] Would continue with text extraction and individual creation")
                return
            
            # Step 2: Extract text
            click.echo(f"\n📄 Step 2: Extracting text from obituary...")
            with ObituaryProcessor() as processor:
                text = processor.extract_and_store_text(obituary_id)
                if not text:
                    click.echo(f"❌ Failed to extract and store text for obituary {obituary_id}")
                    return
                
                click.echo(f"✅ Successfully extracted and stored text for obituary {obituary_id}")
            
            # Step 3: Create individual
            click.echo(f"\n👤 Step 3: Creating individual record...")
            with ObituaryProcessor() as processor:
                individual_id = processor.process_obituary(obituary_id)
                if not individual_id:
                    click.echo(f"❌ Failed to create individual for obituary {obituary_id}")
                    return
                
                click.echo(f"✅ Successfully created individual {individual_id} for obituary {obituary_id}")
            
            click.echo(f"\n🎉 Workflow complete! Individual created: {individual_id}")
            click.echo(f"Next step: python -m genealogy_mapper.cli process-relationships {individual_id}")
            
    except Exception as e:
        click.echo(f"Error: {str(e)}")


if __name__ == '__main__':
    cli()
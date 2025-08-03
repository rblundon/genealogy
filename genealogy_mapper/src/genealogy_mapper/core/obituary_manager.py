import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, Callable
from neo4j import GraphDatabase
from .config import Config
import uuid
import requests
import validators
from urllib.parse import urlparse, unquote
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()

class ObituaryManager:
    """Manages obituary URLs and their processing status in Neo4j."""
    
    def __init__(self, neo4j_config: Optional[Dict[str, str]] = None, timeout: int = 5):
        """Initialize the obituary manager."""
        if neo4j_config is None:
            config = Config()
            neo4j_config = config.get_neo4j_config()
        
        self.driver = GraphDatabase.driver(
            neo4j_config['uri'],
            auth=(neo4j_config['user'], neo4j_config['password'])
        )
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
    
    def __enter__(self):
        """Enter the context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and clean up resources."""
        self.close()
    
    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()
        self.session.close()
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize a URL by removing escape characters and properly encoding it.
        
        Args:
            url (str): The URL to normalize
            
        Returns:
            str: Normalized URL
        """
        # Remove escape characters
        url = url.replace('\\', '')
        # URL decode to handle any encoded characters
        url = unquote(url)
        return url
    
    def validate_url(self, url: str) -> bool:
        """
        Validate a URL.
        
        Args:
            url (str): The URL to validate
            
        Returns:
            bool: True if the URL is valid and accessible, False otherwise
        """
        # Normalize the URL first
        url = self._normalize_url(url)
        
        if not validators.url(url):
            logger.error(f"Invalid URL format: {url}")
            return False
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 404:
                logger.error(f"URL not found: {url}")
                return False
            response.raise_for_status()
            logger.info(f"URL validation successful: {url}")
            return True
        except requests.RequestException as e:
            logger.error(f"URL not accessible: {url} - {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error accessing URL: {url} - {str(e)}")
            return False
    
    def extract_metadata(self, url: str) -> Dict[str, str]:
        """
        Extract metadata from the URL.
        
        Args:
            url (str): The URL to extract metadata from
            
        Returns:
            Dict[str, str]: Dictionary containing metadata
        """
        # Normalize the URL first
        url = self._normalize_url(url)
        
        metadata = {}
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Extract domain for source
            domain = urlparse(url).netloc.lower()
            
            # Basic metadata extraction (removed newspaper, location, publication_date)
            # Additional metadata can be added here if needed
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return metadata
    
    def add_obituary_url(self, url: str, source: str, dry_run: bool = False, force_rescrape: bool = False) -> Optional[str]:
        """Add a new obituary URL to the database.
        
        Args:
            url: The obituary URL
            source: The source website (e.g., "legacy.com")
            dry_run: If True, only validate and show what would be done
            force_rescrape: If True, process URL even if it exists
            
        Returns:
            Optional[str]: The obituary ID if successful, None otherwise
        """
        try:
            # Normalize the URL first
            url = self._normalize_url(url)
            
            # Validate URL
            if not self.validate_url(url):
                return None
            
            # Extract metadata
            metadata = self.extract_metadata(url)
            
            if dry_run:
                console.print("\n[bold blue]Dry Run Mode[/bold blue]")
                console.print(f"Would add obituary URL: {url}")
                console.print(f"Source: {source}")
                console.print("Metadata:")
                for key, value in metadata.items():
                    console.print(f"  {key}: {value}")
                return "DRY_RUN"
            
            with self.driver.session() as session:
                # Check if URL exists
                if not force_rescrape:
                    query = "MATCH (o:Obituary {url: $url}) RETURN o.id as id"
                    result = session.run(query, url=url)
                    record = result.single()
                    if record:
                        logger.error(f"URL already exists: {url}. Use --force to rescrape.")
                        return None
                
                # Generate UUID in Python
                obituary_id = str(uuid.uuid4())
                
                # Create obituary node with unique URL
                query = """
                MERGE (o:Obituary {url: $url})
                ON CREATE SET 
                    o.id = $id,
                    o.status = 'PENDING',
                    o.source = $source,
                    o.created_at = datetime(),
                    o.updated_at = datetime()
                RETURN o.id as id
                """
                result = session.run(query, 
                    url=url, 
                    id=obituary_id, 
                    source=source
                )
                record = result.single()
                if record:
                    logger.info(f"Added obituary URL: {url}")
                    return record['id']
                return None
        except Exception as e:
            logger.error(f"Error adding obituary URL: {str(e)}")
            return None
    
    def process_pending_urls(self, force_rescrape: bool = False, progress_callback: Optional[Callable[[str, str], None]] = None) -> List[Dict[str, Any]]:
        """
        Process all pending obituaries.
        
        Args:
            force_rescrape: If True, process all URLs even if they have "completed" status
            progress_callback: Callback function to report progress
            
        Returns:
            List[Dict[str, Any]]: List of processed obituaries
        """
        try:
            with self.driver.session() as session:
                # Get pending URLs
                query = """
                MATCH (o:Obituary)
                WHERE o.status = 'PENDING' OR $force_rescrape
                RETURN o
                ORDER BY o.created_at
                """
                result = session.run(query, force_rescrape=force_rescrape)
                urls = [dict(record['o']) for record in result]
                
                if not urls:
                    logger.info("No URLs to process")
                    return []
                
                processed = []
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeRemainingColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task(
                        f"Processing {len(urls)} URLs...",
                        total=len(urls)
                    )
                    
                    for url_data in urls:
                        url = url_data['url']
                        obituary_id = url_data.get('id')
                        try:
                            # Update status to PROCESSING
                            self.update_obituary_status(url, "PROCESSING")
                            
                            # Process URL using ObituaryProcessor
                            from .obituary_processor import ObituaryProcessor
                            with ObituaryProcessor() as processor:
                                if obituary_id:
                                    # Process existing obituary by ID
                                    person_id = processor.process_obituary(obituary_id)
                                    if person_id:
                                        logger.info(f"Successfully processed obituary {obituary_id} and created individual {person_id}")
                                        self.update_obituary_status(url, "COMPLETED")
                                        processed.append(url_data)
                                    else:
                                        logger.error(f"Failed to process obituary {obituary_id}")
                                        self.update_obituary_status(url, "FAILED", "Failed to extract person information")
                                else:
                                    logger.error(f"No obituary ID found for URL: {url}")
                                    self.update_obituary_status(url, "FAILED", "No obituary ID found")
                            
                            if progress_callback:
                                progress_callback(url, "completed")
                            
                        except Exception as e:
                            logger.error(f"Error processing URL {url}: {str(e)}")
                            self.update_obituary_status(url, "FAILED", str(e))
                            if progress_callback:
                                progress_callback(url, "failed")
                        
                        progress.update(task, advance=1)
                
                return processed
                
        except Exception as e:
            logger.error(f"Error processing pending URLs: {str(e)}")
            return []
    
    def update_obituary_status(self, url: str, status: str, error_message: Optional[str] = None) -> bool:
        """Update the processing status of an obituary.
        
        Args:
            url: The obituary URL
            status: New status (PENDING, PROCESSING, COMPLETED, FAILED)
            error_message: Optional error message if status is FAILED
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.driver.session() as session:
                query = """
                MATCH (o:Obituary {url: $url})
                SET o.status = $status,
                    o.updated_at = datetime()
                """
                if error_message:
                    query += ", o.error_message = $error_message"
                query += " RETURN o"
                
                result = session.run(query, 
                    url=url, 
                    status=status,
                    error_message=error_message
                )
                node = result.single()
                if node:
                    logger.info(f"Updated obituary status: {url} -> {status}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating obituary status: {str(e)}")
            return False
    
    def link_obituary_to_individual(self, url: str, individual_id: str, relationship_type: str = "MENTIONS") -> bool:
        """Link an obituary to an individual.
        
        Args:
            url: The obituary URL
            individual_id: The ID of the individual
            relationship_type: Type of relationship (MENTIONS or PROCESSED_BY)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH (o:Obituary {{url: $url}})
                MATCH (i:Individual {{id: $individual_id}})
                MERGE (o)-[r:{relationship_type}]->(i)
                RETURN r
                """
                result = session.run(query, url=url, individual_id=individual_id)
                rel = result.single()
                if rel:
                    logger.info(f"Linked obituary {url} to individual {individual_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error linking obituary to individual: {str(e)}")
            return False
    
    def get_pending_obituaries(self) -> List[Dict[str, Any]]:
        """Get all pending obituaries.
        
        Returns:
            List[Dict[str, Any]]: List of pending obituaries with their details
        """
        try:
            with self.driver.session() as session:
                query = """
                MATCH (o:Obituary)
                WHERE o.status = 'PENDING'
                RETURN o
                ORDER BY o.created_at
                """
                result = session.run(query)
                return [dict(record['o']) for record in result]
        except Exception as e:
            logger.error(f"Error getting pending obituaries: {str(e)}")
            return []
    
    def get_obituary_status(self, url: str) -> Optional[Dict[str, Any]]:
        """Get the status of an obituary.
        
        Args:
            url: The obituary URL
            
        Returns:
            Optional[Dict[str, Any]]: Obituary details if found, None otherwise
        """
        try:
            with self.driver.session() as session:
                query = """
                MATCH (o:Obituary {url: $url})
                RETURN o
                """
                result = session.run(query, url=url)
                record = result.single()
                return dict(record['o']) if record else None
        except Exception as e:
            logger.error(f"Error getting obituary status: {str(e)}")
            return None
    
    def get_obituaries_by_individual(self, individual_id: str) -> List[Dict[str, Any]]:
        """Get all obituaries mentioning an individual.
        
        Args:
            individual_id: The ID of the individual
            
        Returns:
            List[Dict[str, Any]]: List of obituaries mentioning the individual
        """
        try:
            with self.driver.session() as session:
                query = """
                MATCH (o:Obituary)-[:MENTIONS]->(i:Individual {id: $individual_id})
                RETURN o
                ORDER BY o.created_at
                """
                result = session.run(query, individual_id=individual_id)
                return [dict(record['o']) for record in result]
        except Exception as e:
            logger.error(f"Error getting obituaries by individual: {str(e)}")
            return []
    
    def get_obituaries_with_text(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get obituaries with extracted text from the database.
        
        Args:
            status: Optional status filter (e.g., 'COMPLETED', 'PROCESSED')
            
        Returns:
            List[Dict[str, Any]]: List of obituaries with extracted text
        """
        try:
            with self.driver.session() as session:
                if status:
                    query = """
                    MATCH (o:Obituary)
                    WHERE o.status = $status AND o.extracted_text IS NOT NULL
                    RETURN o
                    ORDER BY o.created_at
                    """
                    result = session.run(query, status=status)
                else:
                    query = """
                    MATCH (o:Obituary)
                    WHERE o.extracted_text IS NOT NULL
                    RETURN o
                    ORDER BY o.created_at
                    """
                    result = session.run(query)
                
                obituaries = []
                for record in result:
                    obit_data = dict(record['o'])
                    # Format for compatibility with existing relationship processor
                    obituaries.append({
                        'url': obit_data.get('url'),
                        'extracted_text': obit_data.get('extracted_text'),
                        'id': obit_data.get('id'),
                        'status': obit_data.get('status'),
                        'source': obit_data.get('source'),
                        'created_at': obit_data.get('created_at'),
                        'updated_at': obit_data.get('updated_at'),
                        'openai_cache': obit_data.get('openai_cache')
                    })
                
                logger.info(f"Found {len(obituaries)} obituaries with extracted text")
                return obituaries
        except Exception as e:
            logger.error(f"Error getting obituaries with text: {str(e)}")
            return []

    def store_openai_cache(self, obituary_id: str, analysis: str) -> bool:
        """Store OpenAI analysis in the obituary record as cache.
        
        Args:
            obituary_id: The ID of the obituary
            analysis: The OpenAI analysis response
            
        Returns:
            bool: True if successfully stored, False otherwise
        """
        try:
            with self.driver.session() as session:
                query = """
                MATCH (o:Obituary {id: $obituary_id})
                SET o.openai_cache = $analysis,
                    o.openai_cache_timestamp = datetime()
                RETURN o
                """
                result = session.run(query, obituary_id=obituary_id, analysis=analysis)
                record = result.single()
                if record:
                    logger.info(f"Stored OpenAI cache for obituary {obituary_id}")
                    return True
                else:
                    logger.error(f"Obituary {obituary_id} not found")
                    return False
        except Exception as e:
            logger.error(f"Error storing OpenAI cache: {str(e)}")
            return False

    def get_openai_cache(self, obituary_id: str) -> Optional[str]:
        """Get cached OpenAI analysis for an obituary.
        
        Args:
            obituary_id: The ID of the obituary
            
        Returns:
            Optional[str]: Cached analysis if available, None otherwise
        """
        try:
            with self.driver.session() as session:
                query = """
                MATCH (o:Obituary {id: $obituary_id})
                RETURN o.openai_cache as cache
                """
                result = session.run(query, obituary_id=obituary_id)
                record = result.single()
                if record and record['cache']:
                    logger.info(f"Found cached OpenAI analysis for obituary {obituary_id}")
                    return record['cache']
                else:
                    logger.info(f"No cached analysis found for obituary {obituary_id}")
                    return None
        except Exception as e:
            logger.error(f"Error retrieving OpenAI cache: {str(e)}")
            return None

    def has_openai_cache(self, obituary_id: str) -> bool:
        """Check if an obituary has cached OpenAI analysis.
        
        Args:
            obituary_id: The ID of the obituary
            
        Returns:
            bool: True if cached analysis exists, False otherwise
        """
        return self.get_openai_cache(obituary_id) is not None

    def find_existing_person_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find an existing person by name (case-insensitive).
        
        Args:
            name: The name to search for
            
        Returns:
            Optional[Dict[str, Any]]: Person data if found, None otherwise
        """
        try:
            with self.driver.session() as session:
                query = """
                MATCH (p:Person)
                WHERE toLower(p.name_full) CONTAINS toLower($name) 
                   OR toLower($name) CONTAINS toLower(p.name_full)
                RETURN p
                LIMIT 10
                """
                result = session.run(query, name=name)
                records = [dict(record['p']) for record in result]
                return records
        except Exception as e:
            logger.error(f"Error finding existing person: {str(e)}")
            return []

    def link_obituary_to_person(self, obituary_id: str, person_id: str) -> bool:
        """Link an obituary to a person (1:1 relationship).
        
        Args:
            obituary_id: The ID of the obituary
            person_id: The ID of the person
            
        Returns:
            bool: True if successfully linked, False otherwise
        """
        try:
            with self.driver.session() as session:
                # First, check if obituary is already linked
                check_query = """
                MATCH (o:Obituary {id: $obituary_id})
                RETURN o
                """
                result = session.run(check_query, obituary_id=obituary_id)
                obituary = result.single()
                
                if not obituary:
                    logger.error(f"Obituary {obituary_id} not found")
                    return False
                
                # Create the relationship
                link_query = """
                MATCH (o:Obituary {id: $obituary_id})
                MATCH (p:Person {id: $person_id})
                MERGE (o)-[:BELONGS_TO]->(p)
                RETURN o, p
                """
                result = session.run(link_query, obituary_id=obituary_id, person_id=person_id)
                record = result.single()
                
                if record:
                    logger.info(f"Successfully linked obituary {obituary_id} to person {person_id}")
                    return True
                else:
                    logger.error(f"Failed to link obituary {obituary_id} to person {person_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error linking obituary to person: {str(e)}")
            return False

    def get_person_by_obituary(self, obituary_id: str) -> Optional[Dict[str, Any]]:
        """Get the person linked to an obituary.
        
        Args:
            obituary_id: The ID of the obituary
            
        Returns:
            Optional[Dict[str, Any]]: Person data if found, None otherwise
        """
        try:
            with self.driver.session() as session:
                query = """
                MATCH (o:Obituary {id: $obituary_id})-[:BELONGS_TO]->(p:Person)
                RETURN p
                """
                result = session.run(query, obituary_id=obituary_id)
                record = result.single()
                return dict(record['p']) if record else None
        except Exception as e:
            logger.error(f"Error getting person by obituary: {str(e)}")
            return None

    def get_obituary_by_person(self, person_id: str) -> Optional[Dict[str, Any]]:
        """Get the obituary linked to a person.
        
        Args:
            person_id: The ID of the person
            
        Returns:
            Optional[Dict[str, Any]]: Obituary data if found, None otherwise
        """
        try:
            with self.driver.session() as session:
                query = """
                MATCH (p:Person {id: $person_id})<-[:BELONGS_TO]-(o:Obituary)
                RETURN o
                """
                result = session.run(query, person_id=person_id)
                record = result.single()
                return dict(record['o']) if record else None
        except Exception as e:
            logger.error(f"Error getting obituary by person: {str(e)}")
            return None 
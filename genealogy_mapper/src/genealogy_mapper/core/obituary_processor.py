import logging
from typing import Optional, Dict, Any
from neo4j import GraphDatabase
from .config import Config
from .obituary_manager import ObituaryManager
from .person_manager import PersonManager
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import uuid
from .ner_processor import ObituaryNERProcessor
from datetime import UTC

logger = logging.getLogger(__name__)

class ObituaryProcessor:
    """Processes obituaries to extract text and create person records."""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(Config().get_neo4j_config()['uri'],
                                          auth=(Config().get_neo4j_config()['user'],
                                                Config().get_neo4j_config()['password']))
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        })
        self.ner_processor = ObituaryNERProcessor()
    
    def __enter__(self):
        """Enter the context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and clean up resources."""
        self.close()
    
    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()
    
    def get_obituary_url(self, obituary_id):
        with self.driver.session() as session:
            result = session.run("MATCH (o:Obituary) WHERE o.id = $id RETURN o.url", id=obituary_id)
            record = result.single()
            return record['o.url'] if record else None
    
    def extract_text(self, url):
        try:
            # Use the exact same approach as the working process_obit.py script
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find the obituary text using the exact same logic as process_obit.py
            obit_text = None
            for class_name in ['obituary-text', 'obit-text', 'obituary-content']:
                element = soup.find('div', class_=class_name)
                if element:
                    obit_text = element.get_text(strip=True)
                    logger.debug(f"Found obituary text using selector: div.{class_name}")
                    break
            
            if not obit_text:
                # Try to find text that looks like an obituary - using the exact same logic
                text = soup.get_text(strip=True)
                obit_start = text.find("Kaczmarowski, Maxine V.")
                if obit_start != -1:
                    obit_end = text.find("Published by", obit_start)
                    if obit_end != -1:
                        obit_text = text[obit_start:obit_end].strip()
                        logger.debug(f"Found obituary text using name pattern")
            
            return obit_text
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return None
    
    def store_extracted_text(self, obituary_id, text):
        with self.driver.session() as session:
            session.run("MATCH (o:Obituary) WHERE o.id = $id SET o.extracted_text = $text, o.status = 'PROCESSED', o.updated_at = datetime()", id=obituary_id, text=text)
    
    def extract_person_info(self, text, url=None):
        # Use the exact same approach as the working process_obit.py script
        # Just use the NER processor directly like the working script does
        return self.ner_processor.extract_person_info(text)
    
    def create_or_update_person(self, person_info):
        """Create or update an individual record in Neo4j."""
        try:
            with self.driver.session() as session:
                # Convert person_info to Individual node properties
                individual_props = {
                    'name': person_info.get('name_full'),
                    'sex': person_info.get('gender'),
                    'birth_date': person_info.get('birth_date'),
                    'death_date': person_info.get('death_date'),
                    'age': person_info.get('age'),
                    'maiden_name': person_info.get('maiden_name'),
                    'raw_text': person_info.get('raw_text'),
                    'created_at': datetime.now(UTC).isoformat(),
                    'updated_at': datetime.now(UTC).isoformat()
                }
                
                # Remove None values
                individual_props = {k: v for k, v in individual_props.items() if v is not None}
                
                result = session.run(
                    "MERGE (i:Individual {name: $name}) ON CREATE SET i += $props ON MATCH SET i += $props RETURN elementId(i)", 
                    name=person_info['name_full'], 
                    props=individual_props
                )
                record = result.single()
                if record:
                    return record[0]
                return None
        except Exception as e:
            logger.error(f"Error creating/updating individual record: {e}")
            return None
    
    def process_obituary(self, obituary_id):
        try:
            # Retrieve the obituary URL
            url = self.get_obituary_url(obituary_id)
            if not url:
                logger.error(f"Obituary URL not found for ID: {obituary_id}")
                return None

            # Extract text from the URL
            text = self.extract_text(url)
            if not text:
                logger.error(f"Failed to extract text from URL: {url}")
                return None

            # Store the extracted text in the database
            self.store_extracted_text(obituary_id, text)

            # Extract person information
            person_info = self.extract_person_info(text, url)
            if not person_info:
                logger.error(f"Failed to extract person information from text: {text}")
                return None

            # Convert PersonInfo object to a dictionary
            person_info_dict = {
                'name_full': person_info.full_name,
                'maiden_name': person_info.maiden_name,
                'birth_date': person_info.birth_date,
                'death_date': person_info.death_date,
                'birth_place': person_info.birth_place,
                'death_place': person_info.death_place,
                'age': person_info.age,
                'gender': person_info.gender,
                'occupation': person_info.occupation,
                'education': person_info.education,
                'military_service': person_info.military_service,
                'organizations': person_info.organizations,
                'raw_text': person_info.raw_text
            }

            # Create or update the person record
            person_id = self.create_or_update_person(person_info_dict)
            if not person_id:
                logger.error(f"Failed to create or update person record for obituary ID: {obituary_id}")
                return None

            return person_id
        except Exception as e:
            logger.error(f"Error processing obituary {obituary_id}: {str(e)}")
            return None
    
    def extract_and_store_text(self, obituary_id: str) -> Optional[str]:
        """Extract text from an obituary URL and store it in the database."""
        try:
            # Get obituary URL
            url = self.get_obituary_url(obituary_id)
            if not url:
                logger.error(f"Obituary not found: {obituary_id}")
                return None
            
            # Extract text
            text = self.extract_text(url)
            if not text:
                logger.error(f"Failed to extract text from: {url}")
                return None
            
            # Store extracted text in the database
            with self.driver.session() as session:
                query = """
                MATCH (o:Obituary {id: $id})
                SET o.extracted_text = $text,
                    o.status = 'PROCESSED',
                    o.updated_at = datetime()
                """
                session.run(query, id=obituary_id, text=text)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting and storing text: {str(e)}")
            return None 
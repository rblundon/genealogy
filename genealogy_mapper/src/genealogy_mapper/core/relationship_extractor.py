import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from neo4j import GraphDatabase
from openai import OpenAI
from .config import Config
from .obituary_manager import ObituaryManager
from .relationship_processor import RelationshipProcessor
from .relationship_ner_processor import RelationshipNERProcessor

logger = logging.getLogger(__name__)

class RelationshipExtractor:
    """Extract and process relationships from obituaries using OpenAI and caching."""
    
    def __init__(self, neo4j_config: Optional[Dict[str, str]] = None):
        """Initialize the relationship extractor."""
        if neo4j_config is None:
            config = Config()
            neo4j_config = config.get_neo4j_config()
        
        self.neo4j_config = neo4j_config
        self.obituary_manager = ObituaryManager(neo4j_config)
        self.relationship_processor = RelationshipProcessor(neo4j_config)
        self.ner_processor = RelationshipNERProcessor()
        
        # Initialize OpenAI client
        openai_config = Config().get_openai_config()
        api_key = openai_config.get('api_key')
        if not api_key:
            raise ValueError("OpenAI API key not found in configuration")
        
        self.openai_client = OpenAI(api_key=api_key)
        self.openai_config = openai_config
    
    def close(self):
        """Close all connections."""
        self.obituary_manager.close()
        self.relationship_processor.close()
    
    def __enter__(self):
        """Enter the context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and clean up resources."""
        self.close()
    
    def _create_analysis_prompt(self, obituary_text: str) -> str:
        """Create the prompt for OpenAI relationship analysis."""
        return f"""Use Named Entity Recognition (NER) to identify all individuals and their relationships according to the GEDCOM specification. Your task is to extract family relationships from this obituary text and map them to GEDCOM-compatible format.

GEDCOM COMPLIANCE REQUIREMENTS:
1. INDIVIDUAL RECORDS: Each person must have a unique identifier and GEDCOM-compatible properties
2. RELATIONSHIP TYPES: Map to standard GEDCOM relationship types:
   - FAM (Family) records for spouses
   - FAMC (Family as Child) for parent-child relationships
   - FAMS (Family as Spouse) for marriage relationships
   - Sibling relationships within family groups
3. GENDER CODING: Use GEDCOM gender codes (M/F/U)
4. DATE FORMATS: Use GEDCOM date format (DD MMM YYYY)
5. DECEASED STATUS: Preserve death information for genealogical accuracy

EXTRACTION GUIDELINES:
- Identify ALL individuals mentioned, even briefly
- Preserve deceased status and death dates when available
- Map relationships to GEDCOM family structures
- Include full names with middle names/initials
- Handle complex family structures (step-families, in-laws, etc.)
- Distinguish between biological and legal relationships
- ONLY include relationships that are EXPLICITLY stated in the obituary text
- DO NOT infer relationships that are not directly mentioned
- If a person is mentioned but no relationships are stated, do not create any relationships for them

OUTPUT FORMAT:
For each individual, provide:
1. Individual Name (deceased) if applicable
   - Name: Full Name (GEDCOM format)
   - Gender: M/F/U (GEDCOM code)
   - Birth Date: DD MMM YYYY or (not provided)
   - Death Date: DD MMM YYYY or (not provided)
   - Status: deceased/alive
   - GEDCOM_ID: I#### (auto-assigned)
   - Relationships:
     - Spouse: Other Person Name (deceased) if applicable
     - Parent: Other Person Name (deceased) if applicable
     - Child: Other Person Name (deceased) if applicable
     - Sibling: Other Person Name (deceased) if applicable
     - In-law: Other Person Name (specify type)

EXAMPLE GEDCOM-COMPLIANT OUTPUT:
1. Maxine V. Kaczmarowski (deceased)
   - Name: Maxine V. Kaczmarowski
   - Gender: F
   - Birth Date: (not provided)
   - Death Date: 24 May 2018
   - Status: deceased
   - GEDCOM_ID: I0001
   - Relationships:
     - Spouse: Terrence Kaczmarowski (deceased)
     - Child: Patricia Kaczmarowski (deceased)
     - Sibling: Reginald Paradowski
     - Sibling: Joseph Paradowski

2. Terrence Kaczmarowski (deceased)
   - Name: Terrence Kaczmarowski
   - Gender: M
   - Birth Date: (not provided)
   - Death Date: (not provided)
   - Status: deceased
   - GEDCOM_ID: I0002
   - Relationships:
     - Spouse: Maxine V. Kaczmarowski (deceased)

3. Patricia Kaczmarowski (deceased)
   - Name: Patricia Kaczmarowski
   - Gender: F
   - Birth Date: (not provided)
   - Death Date: (not provided)
   - Status: deceased
   - GEDCOM_ID: I0003
   - Relationships:
     - Parent: Maxine V. Kaczmarowski (deceased)
     - Spouse: Steve Blundon

4. Autumn (mentioned but no relationships stated)
   - Name: Autumn
   - Gender: F
   - Birth Date: (not provided)
   - Death Date: (not provided)
   - Status: alive
   - GEDCOM_ID: I0004
   - Relationships: (none explicitly stated)

Obituary text:
{obituary_text}

Using Named Entity Recognition, identify ALL individuals and their familial relationships according to GEDCOM specifications. Be comprehensive and include every person mentioned, preserving death status and mapping relationships to GEDCOM family structures. IMPORTANT: Only include relationships that are EXPLICITLY stated in the obituary text - do not infer or assume relationships that are not directly mentioned."""
    
    def extract_relationships_from_obituary(self, obituary_id: str, force_reprocess: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract relationships from a single obituary using OpenAI.
        
        Args:
            obituary_id: The ID of the obituary to process
            force_reprocess: If True, ignore cached analysis and reprocess
            
        Returns:
            Dictionary containing the analysis results, or None if failed
        """
        try:
            # Get obituary data
            obituary_data = self.obituary_manager.get_obituary_by_id(obituary_id)
            if not obituary_data:
                logger.error(f"Obituary not found: {obituary_id}")
                return None
            
            # Check if we have extracted text
            if not obituary_data.get('extracted_text'):
                logger.error(f"No extracted text found for obituary: {obituary_id}")
                return None
            
            # Check for cached analysis (unless force reprocess)
            if not force_reprocess:
                cached_analysis = self.obituary_manager.get_openai_cache(obituary_id)
                if cached_analysis:
                    logger.info(f"Using cached analysis for obituary: {obituary_id}")
                    return {
                        'url': obituary_data.get('url'),
                        'id': obituary_id,
                        'analysis': cached_analysis,
                        'cached': True
                    }
            
            # Generate new analysis
            logger.info(f"Generating new analysis for obituary: {obituary_id}")
            
            # Create the prompt
            prompt = self._create_analysis_prompt(obituary_data['extracted_text'])
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=self.openai_config.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are a genealogy expert specializing in extracting family relationships from obituaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=float(self.openai_config.get('temperature', 0.1)),
                max_tokens=int(self.openai_config.get('max_tokens', 2000))
            )
            
            # Parse the response
            analysis = response.choices[0].message.content
            
            # Store in cache
            self.obituary_manager.store_openai_cache(obituary_id, analysis)
            
            return {
                'url': obituary_data.get('url'),
                'id': obituary_id,
                'analysis': analysis,
                'cached': False
            }
            
        except Exception as e:
            logger.error(f"Error extracting relationships from obituary {obituary_id}: {str(e)}")
            return None
    
    def process_relationships_from_obituary(self, obituary_id: str, force_reprocess: bool = False) -> bool:
        """
        Complete workflow: Extract and import relationships from a single obituary.
        
        Args:
            obituary_id: The ID of the obituary to process
            force_reprocess: If True, ignore cached analysis and reprocess
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract relationships
            result = self.extract_relationships_from_obituary(obituary_id, force_reprocess)
            if not result:
                logger.error(f"Failed to extract relationships from obituary: {obituary_id}")
                return False
            
            # Process the analysis
            processed_data = self.relationship_processor.process_analysis(result['analysis'])
            if not processed_data:
                logger.error(f"Failed to process analysis for obituary: {obituary_id}")
                return False
            
            # Import into Neo4j
            if self.relationship_processor.import_relationships(processed_data):
                logger.info(f"Successfully imported relationships from obituary: {obituary_id}")
                return True
            else:
                logger.error(f"Failed to import relationships from obituary: {obituary_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing relationships from obituary {obituary_id}: {str(e)}")
            return False
    
    def get_analysis_for_obituary(self, obituary_id: str) -> Optional[str]:
        """
        Get the cached analysis for an obituary.
        
        Args:
            obituary_id: The ID of the obituary
            
        Returns:
            The cached analysis text, or None if not found
        """
        return self.obituary_manager.get_openai_cache(obituary_id)
    
    def clear_cache_for_obituary(self, obituary_id: str) -> bool:
        """
        Clear the cached analysis for an obituary.
        
        Args:
            obituary_id: The ID of the obituary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.obituary_manager.driver.session() as session:
                query = """
                MATCH (o:Obituary {id: $id})
                SET o.openai_cache = NULL,
                    o.openai_cache_timestamp = NULL
                """
                session.run(query, id=obituary_id)
                return True
        except Exception as e:
            logger.error(f"Error clearing cache for obituary {obituary_id}: {str(e)}")
            return False
    
    def extract_relationships_with_ner(self, obituary_id: str, force_reprocess: bool = False) -> Optional[Dict[str, Any]]:
        """
        Extract relationships from a single obituary using custom NER processor.
        
        Args:
            obituary_id: The ID of the obituary to process
            force_reprocess: If True, ignore cached analysis and reprocess
            
        Returns:
            Dictionary containing the analysis results, or None if failed
        """
        try:
            # Get obituary data
            obituary_data = self.obituary_manager.get_obituary_by_id(obituary_id)
            if not obituary_data:
                logger.error(f"Obituary not found: {obituary_id}")
                return None
            
            # Check if we have extracted text
            if not obituary_data.get('extracted_text'):
                logger.error(f"No extracted text found for obituary: {obituary_id}")
                return None
            
            # Check for cached analysis (unless force reprocess)
            if not force_reprocess:
                cached_analysis = self.obituary_manager.get_openai_cache(obituary_id)
                if cached_analysis:
                    logger.info(f"Using cached analysis for obituary: {obituary_id}")
                    return {
                        'url': obituary_data.get('url'),
                        'id': obituary_id,
                        'analysis': cached_analysis,
                        'cached': True
                    }
            
            # Generate new analysis using custom NER
            logger.info(f"Generating new analysis using custom NER for obituary: {obituary_id}")
            
            # Extract persons and relationships using custom NER
            persons = self.ner_processor.extract_persons_with_relationships(obituary_data['extracted_text'])
            
            # Convert to GEDCOM format
            analysis = self.ner_processor.to_gedcom_format(persons)
            
            # Store in cache
            self.obituary_manager.store_openai_cache(obituary_id, analysis)
            
            return {
                'url': obituary_data.get('url'),
                'id': obituary_id,
                'analysis': analysis,
                'cached': False,
                'source': 'custom_ner'
            }
            
        except Exception as e:
            logger.error(f"Error extracting relationships with NER from obituary {obituary_id}: {str(e)}")
            return None 
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from neo4j import GraphDatabase
from .config import Config

logger = logging.getLogger(__name__)

class RelationshipProcessor:
    """Process and import relationships into Neo4j."""
    
    def __init__(self, neo4j_config: Optional[Dict[str, str]] = None):
        """Initialize the relationship processor."""
        if neo4j_config is None:
            config = Config()
            neo4j_config = config.get_neo4j_config()
        
        self.driver = GraphDatabase.driver(
            neo4j_config['uri'],
            auth=(neo4j_config['user'], neo4j_config['password'])
        )
    
    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()
    
    def _create_person_node(self, tx, person_data: Dict[str, Any]) -> str:
        """Create a person node in Neo4j."""
        query = """
        MERGE (p:Person {name_full: $name_full})
        SET p += $properties
        RETURN id(p) as person_id
        """
        result = tx.run(query, 
            name_full=person_data['name_full'],
            properties={k: v for k, v in person_data.items() if k != 'name_full'}
        )
        return result.single()['person_id']
    
    def _create_relationship(self, tx, from_id: str, to_id: str, rel_type: str, properties: Dict[str, Any] = None):
        """Create a relationship between two person nodes."""
        if properties is None:
            properties = {}
        
        query = f"""
        MATCH (from:Individual {{id: $from_id}})
        MATCH (to:Individual {{id: $to_id}})
        MERGE (from)-[r:{rel_type}]->(to)
        SET r += $properties
        """
        tx.run(query, from_id=from_id, to_id=to_id, properties=properties)
    
    def process_analysis(self, analysis: str) -> Dict[str, Any]:
        """Process the OpenAI analysis into structured data with GEDCOM-style IDs."""
        try:
            # Split the analysis into sections
            sections = analysis.split('\n\n')
            
            # Initialize data structures
            persons = []
            person_map = {}  # Map names to IDs
            current_id = 1
            
            logger.info("\nProcessing analysis sections:")
            
            # First pass: Create all person nodes and assign IDs
            for section in sections:
                if not section.strip():
                    continue
                    
                # Check if this is a person section (starts with a number)
                if section[0].isdigit():
                    # Extract person info
                    lines = section.split('\n')
                    name_line = lines[0]
                    
                    # Extract name and status
                    name_parts = name_line.split(' - ')
                    name = name_parts[0].split('. ')[1]  # Remove number and dot
                    status = name_parts[1] if len(name_parts) > 1 else None
                    
                    # Create GEDCOM-style ID
                    person_id = f"I{current_id:04d}"
                    current_id += 1
                    
                    # Check if we already have this name
                    if name in person_map:
                        logger.warning(f"Duplicate name found: {name}. Using existing ID: {person_map[name]}")
                        person_id = person_map[name]
                    else:
                        person_map[name] = person_id
                    
                    logger.info(f"\nProcessing person: {name} (ID: {person_id})")
                    
                    # Initialize person data
                    person_data = {
                        "id": person_id,
                        "name": name,
                        "gender": None,
                        "birth_date": None,
                        "death_date": None,
                        "relationships": [],
                        "raw_section": section  # Store the raw section for second pass
                    }
                    
                    # Process basic info
                    for line in lines[1:]:
                        line = line.strip()
                        if not line:
                            continue
                            
                        if line.startswith('   - Name:'):
                            person_data['name'] = line.split(': ')[1]
                        elif line.startswith('   - Gender:'):
                            person_data['gender'] = line.split(': ')[1]
                        elif line.startswith('   - Birth Date:'):
                            birth_date = line.split(': ')[1]
                            if birth_date != '(not provided)':
                                person_data['birth_date'] = birth_date
                        elif line.startswith('   - Death Date:'):
                            death_date = line.split(': ')[1]
                            if death_date != '(not provided)':
                                person_data['death_date'] = death_date
                    
                    persons.append(person_data)
            
            logger.info("\nPerson map:")
            for name, id in person_map.items():
                logger.info(f"{name} -> {id}")
            
            # Second pass: Process relationships now that all IDs are assigned
            for person in persons:
                lines = person['raw_section'].split('\n')
                in_relationships = False
                
                logger.info(f"\nProcessing relationships for {person['name']} ({person['id']}):")
                
                for line in lines[1:]:
                    line_stripped = line.lstrip()
                    if not line_stripped:
                        continue
                        
                    if line_stripped.startswith('- Relationships:'):
                        in_relationships = True
                        continue
                        
                    # Process relationships if we're in that section
                    if in_relationships and line_stripped.startswith('- '):
                        # Parse relationship
                        rel_parts = line_stripped.split(': ')
                        if len(rel_parts) == 2:
                            rel_type, target_names = rel_parts
                            # Handle multiple targets (e.g., "Sibling: Reginald Paradowski, Joseph Paradowski")
                            for target_name in target_names.split(', '):
                                if target_name in person_map:
                                    person['relationships'].append({
                                        "type": rel_type.replace('- ', '').strip(),
                                        "target_id": person_map[target_name]
                                    })
                                    logger.info(f"Added relationship: {rel_type.replace('- ', '').strip()} -> {target_name} ({person_map[target_name]})")
                                else:
                                    logger.error(f"Target name not found in person_map: {target_name}")
                    elif in_relationships and not line_stripped.startswith('- '):
                        in_relationships = False
                
                # Remove raw section as it's no longer needed
                del person['raw_section']
                
                logger.info(f"Total relationships for {person['name']}: {len(person['relationships'])}")
            
            return {
                'persons': persons,
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing analysis: {str(e)}")
            return None
    
    def import_relationships(self, analysis_data: Dict[str, Any]) -> bool:
        """Import relationships into Neo4j using the structured format."""
        try:
            with self.driver.session() as session:
                # First, create all person nodes
                for person in analysis_data.get('persons', []):
                    # Create person node with GEDCOM ID
                    query = """
                    MERGE (i:Individual {id: $id})
                    SET i += $properties
                    RETURN i
                    """
                    properties = {
                        'name': person['name'],
                        'sex': person['gender'],
                        'birth_date': person['birth_date'],
                        'death_date': person['death_date']
                    }
                    result = session.run(query, 
                        id=person['id'],
                        properties=properties
                    )
                    node = result.single()['i']
                    logger.info(f"Created/updated person node: {person['name']} ({person['id']}) with Neo4j ID: {node.id}")
                
                # Then create all relationships
                for person in analysis_data.get('persons', []):
                    logger.info(f"\nProcessing relationships for {person['name']} ({person['id']})")
                    relationships = person.get('relationships', [])
                    logger.info(f"Found {len(relationships)} relationships to process")
                    
                    for rel in relationships:
                        # Map relationship types to Neo4j relationship types
                        rel_type = rel['type'].upper()
                        if rel_type == 'SPOUSE':
                            rel_type = 'SPOUSE_OF'
                        elif rel_type == 'PARENT':
                            rel_type = 'PARENT_OF'
                        elif rel_type == 'CHILD':
                            rel_type = 'CHILD_OF'
                        elif rel_type == 'SIBLING':
                            rel_type = 'SIBLING_OF'
                        
                        logger.info(f"Creating relationship: {person['name']} -[{rel_type}]-> {rel['target_id']}")
                        
                        # Verify target node exists
                        verify_query = """
                        MATCH (i:Individual {id: $id})
                        RETURN i
                        """
                        result = session.run(verify_query, id=rel['target_id'])
                        target_node = result.single()
                        
                        if not target_node:
                            logger.error(f"Target node not found: {rel['target_id']}")
                            continue
                        
                        # Create bidirectional relationships for certain types
                        if rel_type in ['SPOUSE_OF', 'SIBLING_OF']:
                            # Create relationship in both directions
                            query = f"""
                            MATCH (from:Individual {{id: $from_id}})
                            MATCH (to:Individual {{id: $to_id}})
                            MERGE (from)-[r1:{rel_type}]->(to)
                            MERGE (to)-[r2:{rel_type}]->(from)
                            RETURN r1, r2
                            """
                            result = session.run(query, 
                                from_id=person['id'],
                                to_id=rel['target_id']
                            )
                            rels = result.single()
                            if rels and (rels['r1'] or rels['r2']):
                                logger.info(f"Created bidirectional relationship: {rel_type}")
                            else:
                                logger.error(f"Failed to create bidirectional relationship: {rel_type}")
                        else:
                            # Create relationship in one direction
                            query = f"""
                            MATCH (from:Individual {{id: $from_id}})
                            MATCH (to:Individual {{id: $to_id}})
                            MERGE (from)-[r:{rel_type}]->(to)
                            RETURN r
                            """
                            result = session.run(query, 
                                from_id=person['id'],
                                to_id=rel['target_id']
                            )
                            rel_obj = result.single()['r']
                            if rel_obj:
                                logger.info(f"Created relationship: {rel_type}")
                            else:
                                logger.error(f"Failed to create relationship: {rel_type}")
                
                return True
        except Exception as e:
            logger.error(f"Error importing relationships: {str(e)}")
            return False
    
    def get_relationship_graph(self) -> Dict[str, Any]:
        """Get the current relationship graph from Neo4j."""
        try:
            with self.driver.session() as session:
                # Get all people and their relationships
                query = """
                MATCH (i:Individual)
                OPTIONAL MATCH (i)-[r]->(related:Individual)
                RETURN i, r, related
                """
                result = session.run(query)
                
                # Process the results into a graph structure
                nodes = []
                edges = []
                seen_nodes = set()
                
                for record in result:
                    person = record['i']
                    if person.id not in seen_nodes:
                        nodes.append({
                            'id': person.id,
                            'label': person['name'],
                            'properties': dict(person)
                        })
                        seen_nodes.add(person.id)
                    
                    if record['r'] is not None:
                        # Get the relationship type from the relationship object
                        rel_type = type(record['r']).__name__
                        # Create edge with proper formatting
                        edge = {
                            'from': person.id,
                            'to': record['related'].id,
                            'label': rel_type,
                            'properties': dict(record['r'])
                        }
                        # Only add if we haven't seen this edge before
                        if not any(e['from'] == edge['from'] and e['to'] == edge['to'] and e['label'] == edge['label'] for e in edges):
                            edges.append(edge)
                
                return {
                    'nodes': nodes,
                    'edges': edges
                }
        except Exception as e:
            logger.error(f"Error getting relationship graph: {str(e)}")
            return None
    
    def debug_check_relationships(self) -> None:
        """Debug method to check relationships in Neo4j."""
        try:
            with self.driver.session() as session:
                # Check all relationships
                query = """
                MATCH (i:Individual)-[r]->(related:Individual)
                RETURN i.name as from_name, type(r) as rel_type, related.name as to_name
                """
                result = session.run(query)
                
                logger.info("\nChecking relationships in Neo4j:")
                found_relationships = False
                for record in result:
                    found_relationships = True
                    logger.info(f"Found relationship: {record['from_name']} -[{record['rel_type']}]-> {record['to_name']}")
                
                if not found_relationships:
                    logger.info("No relationships found in the database.")
                    
                # Check for any Individual nodes
                query = """
                MATCH (i:Individual)
                RETURN count(i) as node_count
                """
                result = session.run(query)
                count = result.single()['node_count']
                logger.info(f"\nTotal Individual nodes in database: {count}")
                
        except Exception as e:
            logger.error(f"Error checking relationships: {str(e)}")
            return None 
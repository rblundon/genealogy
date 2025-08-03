import logging
from typing import Dict, Any
from neo4j import GraphDatabase
import uuid

logger = logging.getLogger(__name__)

class PersonManager:
    def __init__(self, neo4j_config: Dict[str, str]):
        self.driver = GraphDatabase.driver(
            neo4j_config['uri'],
            auth=(neo4j_config['user'], neo4j_config['password'])
        )

    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()

    def create_person(self, person_data: Dict[str, Any]) -> str:
        """Create a person node in Neo4j and return the node ID."""
        with self.driver.session() as session:
            result = session.write_transaction(self._create_person_node, person_data)
            return result

    def _create_person_node(self, tx, person_data: Dict[str, Any]) -> str:
        """Create a person node in Neo4j with a GEDCOM-style ID."""
        # Generate a GEDCOM-style ID
        gedcom_id = f"I{uuid.uuid4().int % 10000:04d}"
        
        # Add the GEDCOM ID to the properties
        properties = {k: v for k, v in person_data.items() if k != 'name_full'}
        properties['gedcom_id'] = gedcom_id
        
        query = """
        MERGE (p:Person {name_full: $name_full})
        SET p += $properties
        RETURN elementId(p) as person_id
        """
        result = tx.run(query, 
            name_full=person_data['name_full'],
            properties=properties
        )
        return result.single()['person_id'] 
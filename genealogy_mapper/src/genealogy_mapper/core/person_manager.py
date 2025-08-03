import logging
from typing import Dict, Any
from neo4j import GraphDatabase
import uuid
from datetime import datetime, UTC

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

    def _get_next_individual_id(self, tx) -> int:
        """Get the next available individual ID."""
        result = tx.run("MATCH (i:Individual) RETURN max(toInteger(substring(i.id, 1))) as max_id")
        record = result.single()
        max_id = record['max_id'] if record and record['max_id'] else 0
        return max_id + 1

    def _create_person_node(self, tx, person_data: Dict[str, Any]) -> str:
        """Create an Individual node in Neo4j with a GEDCOM-style ID."""
        # Generate a GEDCOM-style ID (e.g., I1, I2, etc.)
        gedcom_id = f"I{self._get_next_individual_id(tx)}"
        
        # Prepare properties for Individual node
        individual_props = {
            'id': gedcom_id,
            'name': person_data.get('name_full'),
            'sex': person_data.get('gender'),
            'birth_date': person_data.get('birth_date'),
            'death_date': person_data.get('death_date'),
            'age': person_data.get('age'),
            'maiden_name': person_data.get('maiden_name'),
            'raw_text': person_data.get('raw_text'),
            'created_at': datetime.now(UTC).isoformat(),
            'updated_at': datetime.now(UTC).isoformat()
        }
        
        # Remove None values
        individual_props = {k: v for k, v in individual_props.items() if v is not None}
        
        # Create the Individual node
        result = tx.run(
            "CREATE (i:Individual $props) RETURN elementId(i)",
            props=individual_props
        )
        record = result.single()
        return record[0] if record else None 
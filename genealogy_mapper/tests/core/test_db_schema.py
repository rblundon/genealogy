import pytest
from neo4j import GraphDatabase
from genealogy_mapper.core.config import Config
from genealogy_mapper.core.db_init import init_db

@pytest.fixture
def neo4j_driver(temp_config_file):
    """Create a Neo4j driver instance using the temporary config."""
    config = Config(config_path=temp_config_file)
    neo4j_config = config.get_neo4j_config()
    driver = GraphDatabase.driver(
        neo4j_config['uri'],
        auth=(neo4j_config['user'], neo4j_config['password'])
    )
    yield driver
    driver.close()

def test_constraints_exist(neo4j_driver, temp_config_file):
    """Test that all required constraints exist in the database."""
    # Initialize the database
    assert init_db(config_path=temp_config_file) is True
    
    # Expected constraints
    expected_constraints = {
        'indi_id': {'label': 'Individual', 'property': 'id'},
        'fam_id': {'label': 'Family', 'property': 'id'},
        'sour_id': {'label': 'Source', 'property': 'id'},
        'repo_id': {'label': 'Repository', 'property': 'id'},
        'note_id': {'label': 'Note', 'property': 'id'},
        'media_id': {'label': 'Media', 'property': 'id'},
        'subn_id': {'label': 'Submission', 'property': 'id'}
    }
    
    with neo4j_driver.session() as session:
        # Get all constraints
        result = session.run("""
            SHOW CONSTRAINTS
            YIELD name, labelsOrTypes, properties
            RETURN name, labelsOrTypes[0] as label, properties[0] as property
        """)
        
        # Convert to dictionary for easier lookup
        existing_constraints = {
            record['name']: {
                'label': record['label'],
                'property': record['property']
            }
            for record in result
        }
        
        # Verify each expected constraint exists
        for constraint_name, constraint_info in expected_constraints.items():
            assert constraint_name in existing_constraints, f"Constraint {constraint_name} not found"
            assert existing_constraints[constraint_name]['label'] == constraint_info['label'], \
                f"Constraint {constraint_name} has wrong label"
            assert existing_constraints[constraint_name]['property'] == constraint_info['property'], \
                f"Constraint {constraint_name} has wrong property"

def test_indexes_exist(neo4j_driver, temp_config_file):
    """Test that all required indexes exist in the database."""
    # Initialize the database
    assert init_db(config_path=temp_config_file) is True
    
    # Expected indexes
    expected_indexes = {
        'indi_name': {'label': 'Individual', 'property': 'name'},
        'indi_birth_date': {'label': 'Individual', 'property': 'birth_date'},
        'indi_death_date': {'label': 'Individual', 'property': 'death_date'},
        'fam_marriage_date': {'label': 'Family', 'property': 'marriage_date'},
        'sour_author': {'label': 'Source', 'property': 'author'},
        'sour_publication': {'label': 'Source', 'property': 'publication'}
    }
    
    with neo4j_driver.session() as session:
        # Get all indexes
        result = session.run("""
            SHOW INDEXES
            YIELD name, labelsOrTypes, properties
            RETURN name, labelsOrTypes[0] as label, properties[0] as property
        """)
        
        # Convert to dictionary for easier lookup
        existing_indexes = {
            record['name']: {
                'label': record['label'],
                'property': record['property']
            }
            for record in result
        }
        
        # Verify each expected index exists
        for index_name, index_info in expected_indexes.items():
            assert index_name in existing_indexes, f"Index {index_name} not found"
            assert existing_indexes[index_name]['label'] == index_info['label'], \
                f"Index {index_name} has wrong label"
            assert existing_indexes[index_name]['property'] == index_info['property'], \
                f"Index {index_name} has wrong property" 
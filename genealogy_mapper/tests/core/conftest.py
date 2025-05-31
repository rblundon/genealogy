import os
import pytest
import tempfile
import yaml

@pytest.fixture
def temp_config_file():
    """Create a temporary config file with Neo4j connection details."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            'neo4j': {
                'uri': 'bolt://localhost:7687',
                'user': 'neo4j',
                'password': 'Gen1:1NASB'
            }
        }, f)
    yield f.name
    os.unlink(f.name) 
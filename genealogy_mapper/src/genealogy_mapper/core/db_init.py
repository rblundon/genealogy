import os
import sys
import logging
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from .config import Config

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Handles Neo4j database initialization and schema setup."""

    def __init__(self, db_directory: Optional[str] = None, config_path: Optional[str] = None, config_source: Optional[object] = None):
        """Initialize the database initializer.
        
        Args:
            db_directory: Optional path to database directory. If not provided,
                         will use a default location in the project root.
            config_path: Optional path to config file. If not provided,
                        will look for config.yaml in project root.
            config_source: Optional configuration source for testing or custom config.
        """
        self.db_directory = self._get_db_directory(db_directory)
        self.config = Config(config_path, config_source=config_source)
        neo4j_config = self.config.get_neo4j_config()
        self.uri = neo4j_config['uri']
        self.user = neo4j_config['user']
        self.password = neo4j_config['password']
        
    def _get_db_directory(self, db_directory: Optional[str]) -> str:
        """Get the database directory path.
        
        Args:
            db_directory: Optional custom database directory path.
            
        Returns:
            str: Path to database directory.
        """
        if db_directory:
            return os.path.abspath(db_directory)
            
        # Default to project_root/data/neo4j
        project_root = self._get_project_root()
        default_dir = os.path.join(project_root, "data", "neo4j")
        os.makedirs(default_dir, exist_ok=True)
        return default_dir
        
    def _get_project_root(self) -> str:
        """Get the project root directory.
        
        Returns:
            str: Path to project root.
        """
        current_path = Path(__file__).resolve()
        while current_path.name != "genealogy_mapper":
            if current_path.parent == current_path:
                raise RuntimeError("Could not find project root directory")
            current_path = current_path.parent
        return str(current_path.parent)
        
    def initialize_database(self) -> bool:
        """Initialize the Neo4j database with GEDCOM schema.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            # Test connection
            driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with driver.session() as session:
                # Create constraints
                self._create_constraints(session)
                
                # Create indexes
                self._create_indexes(session)
                
                # Create initial metadata
                self._create_metadata(session)
                
            driver.close()
            logger.info(f"Database initialized successfully in {self.db_directory}")
            return True
            
        except ServiceUnavailable as e:
            logger.error(f"Could not connect to Neo4j: {e}")
            return False
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
            
    def _create_constraints(self, session) -> None:
        """Create Neo4j constraints for GEDCOM data model."""
        constraints = [
            # Individual constraints
            "CREATE CONSTRAINT indi_id IF NOT EXISTS FOR (i:Individual) REQUIRE i.id IS UNIQUE",
            
            # Family constraints
            "CREATE CONSTRAINT fam_id IF NOT EXISTS FOR (f:Family) REQUIRE f.id IS UNIQUE",
            
            # Source constraints
            "CREATE CONSTRAINT sour_id IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE",
            
            # Repository constraints
            "CREATE CONSTRAINT repo_id IF NOT EXISTS FOR (r:Repository) REQUIRE r.id IS UNIQUE",
            
            # Note constraints
            "CREATE CONSTRAINT note_id IF NOT EXISTS FOR (n:Note) REQUIRE n.id IS UNIQUE",
            
            # Media constraints
            "CREATE CONSTRAINT media_id IF NOT EXISTS FOR (m:Media) REQUIRE m.id IS UNIQUE",
            
            # Submission constraints
            "CREATE CONSTRAINT subn_id IF NOT EXISTS FOR (s:Submission) REQUIRE s.id IS UNIQUE"
        ]
        
        for constraint in constraints:
            session.run(constraint)
            
    def _create_indexes(self, session) -> None:
        """Create Neo4j indexes for frequently queried properties."""
        indexes = [
            # Individual indexes
            "CREATE INDEX indi_name IF NOT EXISTS FOR (i:Individual) ON (i.name)",
            "CREATE INDEX indi_birth_date IF NOT EXISTS FOR (i:Individual) ON (i.birth_date)",
            "CREATE INDEX indi_death_date IF NOT EXISTS FOR (i:Individual) ON (i.death_date)",
            
            # Family indexes
            "CREATE INDEX fam_marriage_date IF NOT EXISTS FOR (f:Family) ON (f.marriage_date)",
            
            # Source indexes
            "CREATE INDEX sour_author IF NOT EXISTS FOR (s:Source) ON (s.author)",
            "CREATE INDEX sour_publication IF NOT EXISTS FOR (s:Source) ON (s.publication)"
        ]
        
        for index in indexes:
            session.run(index)
            
    def _create_metadata(self, session) -> None:
        """Create initial metadata node."""
        metadata = {
            "version": "1.0.0",
            "gedcom_version": "7.0",
            "created_at": datetime.now(UTC).isoformat(),
            "last_updated": datetime.now(UTC).isoformat(),
            "db_directory": self.db_directory
        }
        
        session.run(
            "CREATE (m:Metadata $metadata)",
            metadata=metadata
        )

def init_db(db_directory: Optional[str] = None, config_path: Optional[str] = None, config_source: Optional[object] = None) -> bool:
    """Initialize the Neo4j database.
    
    Args:
        db_directory: Optional path to database directory.
        config_path: Optional path to config file.
        config_source: Optional configuration source for testing or custom config.
        
    Returns:
        bool: True if initialization was successful, False otherwise.
    """
    initializer = DatabaseInitializer(db_directory, config_path, config_source=config_source)
    return initializer.initialize_database() 
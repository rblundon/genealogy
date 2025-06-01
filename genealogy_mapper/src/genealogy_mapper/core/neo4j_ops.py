from neo4j import GraphDatabase
from typing import Dict, Any, List, Optional, Tuple, Set, Callable
import logging
from datetime import datetime
import uuid
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Raised when data validation fails."""
    pass

class OperationType(Enum):
    CREATE = "create"
    UPDATE = "update"
    SKIP = "skip"

class ConflictResolution(Enum):
    KEEP_EXISTING = "keep_existing"
    USE_NEW = "use_new"
    MERGE = "merge"
    SKIP = "skip"

@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

@dataclass
class Conflict:
    """Represents a data conflict."""
    field: str
    existing_value: Any
    new_value: Any
    resolution: Optional[ConflictResolution] = None

@dataclass
class ImportOperation:
    """Represents a planned import operation."""
    type: OperationType
    person_info: Dict[str, Any]
    url: str
    existing_id: Optional[str] = None
    validation: Optional[ValidationResult] = None
    conflicts: List[Conflict] = None

class Neo4jOperations:
    def __init__(self, uri: str, user: str, password: str, conflict_resolver: Optional[Callable[[List[Conflict]], List[Conflict]]] = None):
        """Initialize Neo4j connection.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
            conflict_resolver: Optional callback function to resolve conflicts
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.conflict_resolver = conflict_resolver
        
    def close(self):
        """Close the Neo4j connection."""
        self.driver.close()

    def _validate_person_info(self, person_info: Dict[str, Any]) -> ValidationResult:
        """Validate person information before import."""
        errors = []
        warnings = []
        
        # Required fields
        if not person_info.get('full_name'):
            errors.append("Full name is required")
            
        # Date validation
        for date_field in ['birth_date', 'death_date']:
            if date_field in person_info and person_info[date_field]:
                try:
                    datetime.fromisoformat(person_info[date_field])
                except ValueError:
                    errors.append(f"Invalid {date_field} format: {person_info[date_field]}")
                    
        # Gender validation
        if person_info.get('gender') and person_info['gender'] not in ['M', 'F', 'U']:
            errors.append(f"Invalid gender: {person_info['gender']}")
            
        # Data quality warnings
        if person_info.get('data_quality', {}).get('birth_year_calculated'):
            warnings.append("Birth year was calculated, may be approximate")
            
        if person_info.get('data_quality', {}).get('confidence', 1.0) < 0.7:
            warnings.append("Low confidence in extracted data")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_update(self, existing_id: str, person_info: Dict[str, Any]) -> Tuple[ValidationResult, List[Conflict]]:
        """Validate that an update operation is safe and identify conflicts."""
        errors = []
        warnings = []
        conflicts = []
        
        try:
            with self.driver.session() as session:
                # Get existing person data
                query = """
                MATCH (i:Individual {id: $id})
                RETURN i
                """
                result = session.run(query, id=existing_id)
                existing = result.single()
                
                if not existing:
                    errors.append(f"Existing person {existing_id} not found")
                    return ValidationResult(False, errors, warnings), conflicts
                
                # Check for conflicting data
                existing_data = existing['i']
                for field in ['birth_date', 'death_date', 'gender', 'birth_place', 'death_place']:
                    if (existing_data.get(field) and 
                        person_info.get(field) and 
                        existing_data[field] != person_info[field]):
                        conflicts.append(Conflict(
                            field=field,
                            existing_value=existing_data[field],
                            new_value=person_info[field]
                        ))
                        warnings.append(f"{field.replace('_', ' ').title()} conflict: existing={existing_data[field]}, new={person_info[field]}")
                    
        except Exception as e:
            errors.append(f"Error validating update: {str(e)}")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        ), conflicts

    def _resolve_conflicts(self, conflicts: List[Conflict]) -> List[Conflict]:
        """Resolve conflicts using the provided resolver or default behavior."""
        if self.conflict_resolver:
            return self.conflict_resolver(conflicts)
        return conflicts

    def _apply_conflict_resolution(self, person_info: Dict[str, Any], existing_data: Dict[str, Any], conflicts: List[Conflict]) -> Dict[str, Any]:
        """Apply conflict resolutions to the person info."""
        resolved_info = person_info.copy()
        
        for conflict in conflicts:
            if conflict.resolution == ConflictResolution.KEEP_EXISTING:
                resolved_info[conflict.field] = existing_data[conflict.field]
            elif conflict.resolution == ConflictResolution.USE_NEW:
                resolved_info[conflict.field] = conflict.new_value
            elif conflict.resolution == ConflictResolution.MERGE:
                # For dates, keep the more specific one
                if conflict.field in ['birth_date', 'death_date']:
                    existing_date = datetime.fromisoformat(existing_data[conflict.field])
                    new_date = datetime.fromisoformat(conflict.new_value)
                    if new_date.year == existing_date.year:
                        # If years match, keep the more specific date
                        resolved_info[conflict.field] = max(
                            [existing_data[conflict.field], conflict.new_value],
                            key=lambda x: len(x)
                        )
                    else:
                        # If years differ, keep the existing date
                        resolved_info[conflict.field] = existing_data[conflict.field]
                else:
                    # For non-date fields, keep existing value
                    resolved_info[conflict.field] = existing_data[conflict.field]
            elif conflict.resolution == ConflictResolution.SKIP:
                # Skip this field update
                resolved_info[conflict.field] = existing_data[conflict.field]
                
        return resolved_info
        
    def _find_existing_person(self, tx, person_info: Dict[str, Any]) -> Optional[str]:
        """Find an existing person by name and dates."""
        query = """
        MATCH (i:Individual)
        WHERE i.name = $name
        AND (
            (i.birth_date = $birth_date AND i.birth_date IS NOT NULL)
            OR (i.death_date = $death_date AND i.death_date IS NOT NULL)
            OR (i.birth_date IS NULL AND i.death_date IS NULL)
        )
        RETURN i.id
        """
        result = tx.run(query, 
                       name=person_info['full_name'],
                       birth_date=person_info.get('birth_date'),
                       death_date=person_info.get('death_date'))
        record = result.single()
        return record[0] if record else None
        
    def _update_individual(self, tx, indi_id: str, person_info: Dict[str, Any]) -> None:
        """Update an existing Individual node."""
        # Prepare properties to update
        properties = {
            'id': indi_id,
            'name': person_info['full_name'],
            'sex': person_info.get('gender', 'U'),
            'birth_date': person_info.get('birth_date'),
            'birth_place': person_info.get('birth_place'),
            'death_date': person_info.get('death_date'),
            'death_place': person_info.get('death_place'),
            'updated_at': datetime.now().isoformat()
        }
        
        # Update the Individual node
        query = """
        MATCH (i:Individual {id: $id})
        SET i += $properties
        """
        tx.run(query, id=indi_id, properties=properties)
        
    def _create_individual(self, tx, person_info: Dict[str, Any]) -> str:
        """Create an Individual node in Neo4j."""
        # Generate a unique ID for the individual
        indi_id = f"I{str(uuid.uuid4())[:8]}"
        
        # Prepare properties
        properties = {
            'id': indi_id,
            'name': person_info['full_name'],
            'sex': person_info.get('gender', 'U'),
            'birth_date': person_info.get('birth_date'),
            'birth_place': person_info.get('birth_place'),
            'death_date': person_info.get('death_date'),
            'death_place': person_info.get('death_place'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Create the Individual node
        query = """
        CREATE (i:Individual $properties)
        RETURN i.id
        """
        result = tx.run(query, properties=properties)
        return result.single()[0]
        
    def _create_source(self, tx, url: str) -> str:
        """Create a Source node for the obituary."""
        # Generate a unique ID for the source
        sour_id = f"S{str(uuid.uuid4())[:8]}"
        
        # Prepare properties
        properties = {
            'id': sour_id,
            'title': f"Obituary from {url}",
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Create the Source node
        query = """
        CREATE (s:Source $properties)
        RETURN s.id
        """
        result = tx.run(query, properties=properties)
        return result.single()[0]
        
    def _create_citation(self, tx, indi_id: str, sour_id: str, data_quality: Dict[str, Any]):
        """Create a citation relationship between Individual and Source."""
        # First check if citation already exists
        query = """
        MATCH (i:Individual {id: $indi_id})-[c:CITED_IN]->(s:Source {id: $sour_id})
        RETURN c
        """
        result = tx.run(query, indi_id=indi_id, sour_id=sour_id)
        if result.single():
            logger.info(f"Citation already exists for {indi_id} -> {sour_id}")
            return
            
        # Create new citation
        query = """
        MATCH (i:Individual {id: $indi_id})
        MATCH (s:Source {id: $sour_id})
        CREATE (i)-[c:CITED_IN {
            confidence: $confidence,
            birth_year_calculated: $birth_year_calculated,
            source: $source,
            created_at: $created_at
        }]->(s)
        """
        tx.run(query, 
               indi_id=indi_id,
               sour_id=sour_id,
               confidence=data_quality.get('confidence', 0.0),
               birth_year_calculated=data_quality.get('birth_year_calculated', False),
               source=data_quality.get('source', 'unknown'),
               created_at=datetime.now().isoformat())

    def plan_import(self, results: List[Dict[str, Any]]) -> List[ImportOperation]:
        """Plan import operations without executing them."""
        operations = []
        
        for result in results:
            if result['status'] != 'success':
                operations.append(ImportOperation(
                    type=OperationType.SKIP,
                    person_info={},
                    url=result['url'],
                    validation=ValidationResult(False, ["Failed record"], []),
                    conflicts=[]
                ))
                continue
                
            person_info = result['person_info']
            url = result['url']
            
            # Validate person info
            validation = self._validate_person_info(person_info)
            if not validation.is_valid:
                operations.append(ImportOperation(
                    type=OperationType.SKIP,
                    person_info=person_info,
                    url=url,
                    validation=validation,
                    conflicts=[]
                ))
                continue
                
            # Check for existing person
            with self.driver.session() as session:
                existing_id = session.execute_read(lambda tx: self._find_existing_person(tx, person_info))
                
            if existing_id:
                # Validate update and get conflicts
                update_validation, conflicts = self._validate_update(existing_id, person_info)
                operations.append(ImportOperation(
                    type=OperationType.UPDATE,
                    person_info=person_info,
                    url=url,
                    existing_id=existing_id,
                    validation=update_validation,
                    conflicts=conflicts
                ))
            else:
                operations.append(ImportOperation(
                    type=OperationType.CREATE,
                    person_info=person_info,
                    url=url,
                    validation=validation,
                    conflicts=[]
                ))
                
        return operations
               
    def import_person(self, person_info: Dict[str, Any], url: str) -> Tuple[bool, str]:
        """Import a person and their obituary source into Neo4j.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Validate person info
            validation = self._validate_person_info(person_info)
            if not validation.is_valid:
                return False, f"Validation failed: {', '.join(validation.errors)}"
            
            with self.driver.session() as session:
                # Check for existing person
                existing_id = session.execute_read(lambda tx: self._find_existing_person(tx, person_info))
                
                if existing_id:
                    # Validate update and get conflicts
                    update_validation, conflicts = self._validate_update(existing_id, person_info)
                    if not update_validation.is_valid:
                        return False, f"Update validation failed: {', '.join(update_validation.errors)}"
                        
                    # Resolve conflicts
                    resolved_conflicts = self._resolve_conflicts(conflicts)
                    
                    # Get existing data
                    query = """
                    MATCH (i:Individual {id: $id})
                    RETURN i
                    """
                    result = session.run(query, id=existing_id)
                    existing_data = result.single()['i']
                    
                    # Apply conflict resolutions
                    resolved_info = self._apply_conflict_resolution(person_info, existing_data, resolved_conflicts)
                    
                    # Update existing person
                    session.execute_write(lambda tx: self._update_individual(tx, existing_id, resolved_info))
                    indi_id = existing_id
                    message = f"Updated existing person {person_info['full_name']}"
                    if update_validation.warnings:
                        message += f" (Warnings: {', '.join(update_validation.warnings)})"
                else:
                    # Create new person
                    indi_id = session.execute_write(lambda tx: self._create_individual(tx, person_info))
                    message = f"Created new person {person_info['full_name']}"
                    if validation.warnings:
                        message += f" (Warnings: {', '.join(validation.warnings)})"
                
                # Create source and citation
                sour_id = session.execute_write(lambda tx: self._create_source(tx, url))
                session.execute_write(lambda tx: self._create_citation(
                    tx,
                    indi_id,
                    sour_id,
                    person_info.get('data_quality', {})
                ))
                
                logger.info(message)
                return True, message
                
        except Exception as e:
            error_msg = f"Error importing person {person_info.get('full_name')}: {e}"
            logger.error(error_msg)
            return False, error_msg
            
    def import_batch(self, results: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
        """Import a batch of processed obituaries.
        
        Args:
            results: List of processed obituary results
            dry_run: If True, only plan operations without executing them
            
        Returns:
            Dict containing import statistics and messages
        """
        if dry_run:
            operations = self.plan_import(results)
            stats = {
                'total': len(results),
                'planned_creates': sum(1 for op in operations if op.type == OperationType.CREATE),
                'planned_updates': sum(1 for op in operations if op.type == OperationType.UPDATE),
                'planned_skips': sum(1 for op in operations if op.type == OperationType.SKIP),
                'operations': [
                    {
                        'type': op.type.value,
                        'person': op.person_info.get('full_name', 'N/A'),
                        'url': op.url,
                        'validation': {
                            'is_valid': op.validation.is_valid if op.validation else True,
                            'errors': op.validation.errors if op.validation else [],
                            'warnings': op.validation.warnings if op.validation else []
                        },
                        'conflicts': [
                            {
                                'field': c.field,
                                'existing_value': c.existing_value,
                                'new_value': c.new_value,
                                'resolution': c.resolution.value if c.resolution else None
                            }
                            for c in (op.conflicts or [])
                        ]
                    }
                    for op in operations
                ]
            }
            return stats
            
        stats = {
            'total': len(results),
            'success': 0,
            'failed': 0,
            'updated': 0,
            'created': 0,
            'messages': []
        }
        
        for result in results:
            if result['status'] == 'success':
                success, message = self.import_person(result['person_info'], result['url'])
                if success:
                    stats['success'] += 1
                    if 'Updated' in message:
                        stats['updated'] += 1
                    else:
                        stats['created'] += 1
                else:
                    stats['failed'] += 1
                stats['messages'].append(message)
            else:
                stats['failed'] += 1
                stats['messages'].append(f"Skipped failed record: {result['url']}")
                
        return stats 
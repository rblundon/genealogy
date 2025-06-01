# Neo4j Database Backend Design

## Overview

This document outlines the design for integrating Neo4j as the database backend for the genealogy mapper project. Neo4j's graph database structure is particularly well-suited for genealogy data, as it naturally represents relationships between people, events, and locations. The data model follows the GEDCOM 7.0 standard for genealogical data.

## Data Model

### Nodes

1. **Individual (INDI)**

   - Properties:
     - `id`: Unique identifier (XREF_ID)
     - `name`: Full name (NAME)
     - `sex`: Gender (SEX)
     - `birth_date`: Date of birth (BIRT.DATE)
     - `birth_place`: Place of birth (BIRT.PLAC)
     - `death_date`: Date of death (DEAT.DATE)
     - `death_place`: Place of death (DEAT.PLAC)
     - `burial_date`: Date of burial (BURI.DATE)
     - `burial_place`: Place of burial (BURI.PLAC)
     - `created_at`: Timestamp of record creation
     - `updated_at`: Timestamp of last update

2. **Family (FAM)**
   - Properties:
     - `id`: Unique identifier (XREF_ID)
     - `marriage_date`: Date of marriage (MARR.DATE)
     - `marriage_place`: Place of marriage (MARR.PLAC)
     - `divorce_date`: Date of divorce (DIV.DATE)
     - `created_at`: Timestamp of record creation
     - `updated_at`: Timestamp of last update

3. **Source (SOUR)**
   - Properties:
     - `id`: Unique identifier (XREF_ID)
     - `title`: Source title (TITL)
     - `author`: Author of source (AUTH)
     - `publication`: Publication information (PUBL)
     - `repository`: Repository information (REPO)
     - `created_at`: Timestamp of record creation
     - `updated_at`: Timestamp of last update

4. **Repository (REPO)**
   - Properties:
     - `id`: Unique identifier (XREF_ID)
     - `name`: Repository name (NAME)
     - `address`: Repository address (ADDR)
     - `created_at`: Timestamp of record creation
     - `updated_at`: Timestamp of last update

5. **Note (NOTE)**
   - Properties:
     - `id`: Unique identifier (XREF_ID)
     - `text`: Note text (CONT)
     - `created_at`: Timestamp of record creation
     - `updated_at`: Timestamp of last update

6. **Media (OBJE)**
   - Properties:
     - `id`: Unique identifier (XREF_ID)
     - `title`: Media title (TITL)
     - `file`: File reference (FILE)
     - `format`: File format (FORM)
     - `created_at`: Timestamp of record creation
     - `updated_at`: Timestamp of last update

7. **Submission (SUBN)**
   - Properties:
     - `id`: Unique identifier (XREF_ID)
     - `submitter`: Submitter information (SUBM)
     - `family_file`: Family file information (FAMF)
     - `temple`: Temple code (TEMP)
     - `created_at`: Timestamp of record creation
     - `updated_at`: Timestamp of last update

### Relationships

1. **Individual to Individual**
   - `CHILD_OF`: Links child to parents (FAMC)
   - `SPOUSE_OF`: Links spouses in a family (FAMS)
   - `ADOPTED_BY`: Links adopted child to adoptive parents (ADOP)
   - `FOSTERED_BY`: Links fostered child to foster parents (FOST)

2. **Individual to Family**
   - `HUSBAND_IN`: Links husband to family (HUSB)
   - `WIFE_IN`: Links wife to family (WIFE)
   - `CHILD_IN`: Links child to family (CHIL)

3. **Individual to Source**
   - `CITED_IN`: Links individual to source citation (SOUR)
   - `EVENT_CITED_IN`: Links specific event to source citation (SOUR)

4. **Individual to Note**
   - `HAS_NOTE`: Links individual to note (NOTE)
   - `EVENT_HAS_NOTE`: Links specific event to note (NOTE)

5. **Individual to Media**
   - `HAS_MEDIA`: Links individual to media object (OBJE)
   - `EVENT_HAS_MEDIA`: Links specific event to media object (OBJE)

6. **Source to Repository**
   - `HELD_AT`: Links source to repository (REPO)

7. **Submission to Individual**
   - `SUBMITTED_BY`: Links submission to submitter (SUBM)

### GEDCOM-Specific Constraints

1. **Individual Constraints**
   - Each individual must have a unique XREF_ID
   - Sex must be one of: M, F, U, or N
   - Dates must follow GEDCOM date format

2. **Family Constraints**
   - Each family must have at least one spouse
   - Marriage dates must be valid dates
   - Divorce dates must be after marriage dates

3. **Source Constraints**
   - Each source must have a title
   - Repository references must be valid

4. **Media Constraints**
   - Each media object must have a file reference
   - File format must be specified

## Implementation Plan

### Phase 1: Database Setup and Basic Operations

1. **Database Configuration**
   - Set up Neo4j connection handling
   - Implement connection pooling
   - Add configuration management
   - Create database initialization scripts

2. **Basic CRUD Operations**
   - Create base classes for node operations
   - Implement relationship management
   - Add transaction handling
   - Create data validation layer

3. **Migration from JSON**
   - Create migration script from JSON to Neo4j
   - Implement data validation during migration
   - Add rollback capability

### Phase 2: Advanced Features

1. **Query Optimization**
   - Implement indexing strategy
   - Create query caching
   - Add query performance monitoring

2. **Relationship Inference**
   - Implement relationship deduction from obituary text
   - Add confidence scoring for inferred relationships
   - Create relationship validation rules

3. **Data Enrichment**
   - Add external data source integration
   - Implement data verification
   - Create data enrichment pipeline

### Phase 3: API and Integration

1. **API Development**
   - Create RESTful API endpoints
   - Implement query parameters
   - Add response formatting

2. **Integration with Existing Code**
   - Modify URLImporter to use Neo4j
   - Update scraper to store data in Neo4j
   - Add Neo4j-specific error handling

3. **Testing and Validation**
   - Create comprehensive test suite
   - Implement performance testing
   - Add data integrity checks

## Technical Requirements

### Dependencies

- Neo4j Python Driver
- Py2neo (for higher-level operations)
- Connection pooling library
- Data validation library

### Configuration

```python
NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'user': 'neo4j',
    'password': 'password',
    'max_connection_lifetime': 3600,
    'max_connection_pool_size': 50,
    'connection_timeout': 30
}

### Indexing Strategy

```cypher
// Create indexes for frequently queried properties
CREATE INDEX person_name_index FOR (p:Person) ON (p.name);
CREATE INDEX obituary_url_index FOR (o:Obituary) ON (o.url);
CREATE INDEX location_name_index FOR (l:Location) ON (l.name);
```

## Error Handling

1. **Connection Errors**
   - Implement retry mechanism
   - Add connection timeout handling
   - Create fallback options

2. **Data Validation**
   - Add input validation
   - Implement data type checking
   - Create constraint validation

3. **Transaction Management**
   - Implement rollback on failure
   - Add transaction timeout handling
   - Create deadlock detection

## Performance Considerations

1. **Query Optimization**

   - Use parameterized queries
   - Implement query caching
   - Add query timeout handling

2. **Batch Operations**

   - Implement batch processing
   - Add bulk import capability
   - Create batch size optimization

3. **Monitoring**

   - Add performance metrics
   - Implement query logging
   - Create health checks

## Security Considerations

1. **Authentication**

   - Implement role-based access
   - Add user management
   - Create audit logging

2. **Data Protection**

   - Implement data encryption
   - Add backup strategy
   - Create data retention policy

## Future Considerations

1. **Scalability**

   - Plan for horizontal scaling
   - Consider sharding strategy
   - Implement load balancing

2. **Integration**

   - Add support for other data sources
   - Implement export capabilities
   - Create API versioning

3. **Advanced Features**

   - Implement graph algorithms
   - Add machine learning capabilities
   - Create visualization tools

## Testing Strategy

### Mock Testing Approach

The Neo4j integration uses a comprehensive mock testing strategy to ensure reliable and isolated testing of database operations. This approach prevents test dependencies on actual database connections and allows for consistent test execution.

#### Mock Fixtures

```python
@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver and session."""
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    return mock_driver, mock_session
```

#### Test Categories

1. **Database Initialization Tests**
   - Test database creation and configuration
   - Verify constraint and index creation
   - Validate metadata node creation
   - Example:
     ```python
     @patch('neo4j.GraphDatabase.driver')
     def test_database_initialization(mock_driver, mock_neo4j_driver):
         mock_driver.return_value = mock_neo4j_driver[0]
         mock_neo4j_driver[1].run.return_value.single.return_value = {"n": 1}
         assert init_db(config_path=temp_config_file) is True
     ```

2. **Connection Tests**
   - Test connection handling
   - Verify authentication
   - Test connection pooling
   - Example:
     ```python
     @patch('neo4j.GraphDatabase.driver')
     def test_neo4j_connection(mock_driver, mock_neo4j_driver):
         mock_driver.return_value = mock_neo4j_driver[0]
         mock_neo4j_driver[1].run.return_value.single.return_value = {"n": 1}
         driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "test_password"))
         with driver.session() as session:
             result = session.run("RETURN 1 as n")
             assert result.single()["n"] == 1
     ```

3. **Schema Tests**
   - Verify constraint creation
   - Test index creation
   - Validate schema integrity
   - Example:
     ```python
     @patch('neo4j.GraphDatabase.driver')
     def test_constraints_exist(mock_driver, mock_neo4j_driver):
         mock_driver.return_value = mock_neo4j_driver[0]
         assert init_db(config_path=temp_config_file) is True
         calls = [call[0][0] for call in mock_neo4j_driver[1].run.call_args_list]
         assert any("CREATE CONSTRAINT indi_id" in call for call in calls)
     ```

#### Environment Management

Tests use environment variables and configuration fixtures to manage test settings:

```python
@pytest.fixture
def env_vars(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("NEO4J_URI", "bolt://localhost:7687")
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "test_password")
    yield
    # Cleanup is handled automatically by monkeypatch
```

#### Best Practices

1. **Isolation**
   - Each test should be independent
   - Use fixtures for setup and teardown
   - Mock external dependencies

2. **Coverage**
   - Test both success and failure cases
   - Verify error handling
   - Test edge cases

3. **Maintainability**
   - Use descriptive test names
   - Document test purpose
   - Keep tests focused and simple

4. **Performance**
   - Mock expensive operations
   - Use connection pooling in tests
   - Minimize test execution time

# Genealogy Mapper Design Document

## Overview

The Genealogy Mapper is a tool designed to process and manage obituary URLs for genealogy research. It provides a robust system for importing, validating, and storing obituary URLs, with support for extracting text and metadata from various obituary websites.

## Core Components

### 1. Configuration System

The application uses a YAML-based configuration system (`config.yaml`) to manage settings:

```yaml
# Neo4j Configuration
neo4j:
  uri: bolt://localhost:7687
  user: neo4j
  password: your-secure-password-here
```

### 2. Database Initialization

The system uses Neo4j as its database, managed through Docker:

- Container Name: `genealogy-neo4j`
- Ports:
  - Browser Interface: 7474
  - Bolt Connection: 7687
- Default Credentials:
  - Username: `neo4j`
  - Password: `********`

### 3. Information Extraction System

The system uses a hybrid approach combining OpenAI and regex-based extraction:

#### HybridProcessor

The `HybridProcessor` class combines two extraction methods:

1. **OpenAI Extraction**
   - Uses GPT models for natural language understanding
   - High confidence scoring
   - Handles complex context and variations

2. **Regex-based Extraction**
   - Pattern matching for specific formats
   - Medium confidence scoring
   - Used as fallback

3. **Result Merging**
   - Combines results from both methods
   - Prefers OpenAI results when available
   - Uses regex results as fallback

### 4. Pattern Categories

Patterns are organized in `patterns.py`:

1. **Date Patterns**

   - Death date patterns
   - Date range patterns
   - Address date patterns

2. **Name Patterns**

   - Full name patterns
   - Maiden name patterns

3. **Location Patterns**

   - Address patterns
   - City/State patterns

4. **Service Patterns**

   - Funeral service patterns
   - Memorial service patterns

### 5. Data Models

#### ExtractionResult

```python
@dataclass
class ExtractionResult:
    full_name: Optional[str]
    maiden_name: Optional[str]
    death_date: Optional[str]
    age: Optional[int]
    birth_date: Optional[str]
    gender: Optional[str]
    confidence: float
    source: str  # 'openai' or 'regex'
```

### 6. CLI Interface

The command-line interface provides several commands:

```bash
# Process obituaries
python -m genealogy_mapper.cli process-obits [--force] [--debug]

# Import URLs
python -m genealogy_mapper.cli import-urls <urls_file>

# Manage Neo4j
python scripts/manage_neo4j.py [status|start|stop|remove]
```

## Data Flow

1. **URL Import**

   - Read URLs from input file
   - Validate URL format
   - Store in JSON format

2. **Obituary Processing**

   - Read obituary URLs from JSON
   - Scrape obituary text
   - Extract metadata
   - Store results

3. **Hybrid Information Extraction**
   - Primary: OpenAI extraction
   - Fallback: Regex pattern matching
   - Result merging and confidence scoring

## Error Handling

The system implements comprehensive error handling:

1. **URL Validation**
   - Format validation
   - Domain validation
   - Duplicate checking

2. **Scraping Errors**
   - Timeout handling
   - Element not found handling
   - Network error handling

3. **Extraction Errors**
   - OpenAI API error handling
   - Fallback to regex patterns
   - Result validation

## Security Considerations

1. **API Key Management**
   - OpenAI API key stored in environment variables
   - No hardcoded credentials

2. **Database Security**
   - Neo4j credentials in config file
   - Docker container isolation

3. **Input Validation**
   - URL sanitization
   - Content validation

## Development Environment

1. **Virtual Environment**
   - Name: `.genealogy-env`
   - Python version: 3.8+
   - Dependencies managed via `requirements.txt`

2. **Testing**
   - pytest for unit tests
   - Coverage reporting
   - Debug HTML saving

## Future Enhancements

1. **Extraction System**

   - Support for more OpenAI models
   - Enhanced result merging logic
   - Additional pattern categories

2. **Database**

   - Graph schema optimization
   - Query performance improvements
   - Backup and recovery

3. **User Interface**

   - Web interface
   - Progress tracking
   - Result visualization

4. **Integration**

   - Additional obituary sources
   - Genealogy API integration
   - Export capabilities

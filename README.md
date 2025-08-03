# Genealogy Mapper

A tool for extracting and managing genealogical information from obituaries.

## Features

- Extract obituary URLs from web pages
- Process obituary text to extract person information
- Store data in Neo4j database with GEDCOM-compatible schema
- Support for both NER and hybrid (OpenAI + NER) processing
- Interactive conflict resolution for data imports
- Configurable timeouts for web scraping operations
- Detailed logging and progress tracking
- Dry-run mode for previewing changes

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/genealogy-mapper.git
   cd genealogy-mapper
   ```

2. Create and activate a virtual environment:
   ```bash
   # Create virtual environment
   python3 -m venv .venv

   # Activate virtual environment
   # On macOS/Linux:
   source .geneaology-env/bin/activate
   # On Windows:
   .venv\Scripts\activate

   # Verify activation
   which python  # Should show path to .venv/bin/python
   ```

3. Install dependencies:
   ```bash
   # Install core dependencies and the package in editable mode
   pip install -e .

   # Install development dependencies (optional)
   pip install -e ".[dev]"

   # Install Playwright browsers (required for web scraping)
   playwright install
   ```

   This step:
   - Installs all core dependencies (web scraping, NLP, database, etc.)
   - Installs the package in editable mode for development
   - Installs Playwright browsers (Chromium, Firefox, and WebKit) for web scraping
   - Optionally installs development tools (testing, linting, formatting)

   Core dependencies include:
   - `selenium` and `webdriver-manager` for web scraping
   - `playwright` and its browsers for modern web scraping
   - `neo4j` for database operations
   - `openai` for text processing
   - `spacy` for natural language processing
   - `click` for CLI interface
   - `rich` for terminal formatting

   Development tools (optional) include:
   - `pytest` for testing
   - `black` for code formatting
   - `flake8` for linting
   - `mypy` for type checking
   - `pre-commit` for git hooks

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and Neo4j credentials
   ```

   Required environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key for text processing
   - `NEO4J_URI`: Neo4j database connection URI (default: bolt://localhost:7687)
   - `NEO4J_USER`: Neo4j username (default: neo4j)
   - `NEO4J_PASSWORD`: Your Neo4j password
   - `LOG_LEVEL`: Optional logging level (default: INFO)

## Database Management

### Initialization
The `init-database` command sets up the Neo4j database with:
- GEDCOM-compatible schema
- Required constraints and indexes
- Initial configuration

This is only needed once when first setting up the database:
```bash
python -m genealogy_mapper.cli init-database
```

### Maintenance
Regular database maintenance tasks:
1. **Backup**
   ```bash
   # Using Neo4j's built-in backup tool
   neo4j-admin backup --backup-dir=/path/to/backup --database=neo4j
   ```

2. **Monitoring**
   - Check database status: `python -m genealogy_mapper.scripts.manage_neo4j status`
   - View database metrics in Neo4j Browser (http://localhost:7474)
   - Monitor disk space usage

3. **Performance**
   - Indexes are automatically created during initialization
   - Regular database restarts can help clear memory cache
   - Monitor query performance in Neo4j Browser

### Resetting the Database
If you need to start fresh:

1. **Soft Reset** (keeps schema, removes data)
   ```bash
   # Stop the database
   python -m genealogy_mapper.scripts.manage_neo4j stop
   
   # Remove data directory
   rm -rf data/neo4j/data/*
   
   # Start database and reinitialize
   python -m genealogy_mapper.scripts.manage_neo4j start
   python -m genealogy_mapper.cli init-database
   ```

2. **Hard Reset** (complete removal)
   ```bash
   # Remove the container and all data
   python -m genealogy_mapper.scripts.manage_neo4j remove
   
   # Start fresh
   python -m genealogy_mapper.scripts.manage_neo4j start
   python -m genealogy_mapper.cli init-database
   ```

### Database Schema
The database uses a GEDCOM-compatible schema with the following structure:

1. **Node Types**

   a. **Individual**
      - Properties:
        - `id`: Unique identifier
        - `name`: Full name
        - `birth_date`: Date of birth
        - `death_date`: Date of death
        - `gender`: M/F/U
        - `birth_place`: Place of birth
        - `death_place`: Place of death
        - `occupation`: Occupation
        - `education`: Education details
        - `military_service`: Military service details
        - `data_quality`: Metadata about data quality

   b. **Family**
      - Properties:
        - `id`: Unique identifier
        - `marriage_date`: Date of marriage
        - `marriage_place`: Place of marriage
        - `divorce_date`: Date of divorce (if applicable)

   c. **Source**
      - Properties:
        - `id`: Unique identifier
        - `author`: Author of the source
        - `publication`: Publication details
        - `title`: Source title
        - `date`: Source date

   d. **Repository**
      - Properties:
        - `id`: Unique identifier
        - `name`: Repository name
        - `address`: Repository address

   e. **Note**
      - Properties:
        - `id`: Unique identifier
        - `text`: Note content
        - `date`: Note date

   f. **Media**
      - Properties:
        - `id`: Unique identifier
        - `file`: File reference
        - `format`: Media format
        - `title`: Media title

   g. **Submission**
      - Properties:
        - `id`: Unique identifier
        - `submitter`: Submitter details
        - `date`: Submission date

   h. **Obituary**
      - Properties:
        - `id`: Unique identifier (UUID)
        - `url`: Unique obituary URL
        - `status`: Processing status (PENDING, PROCESSING, COMPLETED, FAILED)
        - `source`: Source website
        - `created_at`: Creation timestamp
        - `updated_at`: Last update timestamp
        - `error_message`: Error message (if failed)

2. **Relationships**

   a. **Family Relationships**
      - `(Individual)-[:PARENT_OF]->(Individual)`
      - `(Individual)-[:CHILD_OF]->(Individual)`
      - `(Individual)-[:SPOUSE_OF]->(Individual)`
      - `(Individual)-[:SIBLING_OF]->(Individual)`

   b. **Source Relationships**
      - `(Source)-[:CITES]->(Individual)`
      - `(Source)-[:CITES]->(Family)`
      - `(Repository)-[:HOLDS]->(Source)`

   c. **Media Relationships**
      - `(Media)-[:REFERENCES]->(Individual)`
      - `(Media)-[:REFERENCES]->(Family)`

   d. **Note Relationships**
      - `(Note)-[:ATTACHED_TO]->(Individual)`
      - `(Note)-[:ATTACHED_TO]->(Family)`

   e. **Obituary Relationships**
      - `(Obituary)-[:MENTIONS]->(Individual)`
      - `(Obituary)-[:PROCESSED_BY]->(Individual)`

3. **Constraints**
   - Unique constraints on all `id` properties
   - Unique constraint on Individual `name`
   - Unique constraint on Obituary `url`

4. **Indexes**
   - Individual: `name`, `birth_date`, `death_date`
   - Family: `marriage_date`
   - Source: `author`, `publication`
   - Obituary: `status`, `source`, `created_at`

This schema provides:
- Complete GEDCOM compatibility
- Efficient querying through indexes
- Data integrity through constraints
- Flexible relationship modeling
- Comprehensive metadata tracking

## Program Flow

1. **Configuration Setup**
   - Create configuration file with Neo4j and OpenAI settings
   - Initialize Neo4j database with GEDCOM schema
   - Set up required dependencies

2. **Add Obituary URLs**
   - Use `add-obituary` command to add new obituary URLs
   - Automatically detects source from URL
   - Validates URL accessibility
   - Extracts metadata (newspaper, location, publication date)
   - Supports dry-run mode and force rescrape
   ```bash
   # Add a new obituary
   python -m genealogy_mapper.cli add-obituary "https://www.legacy.com/us/obituaries/example"
   
   # Dry run mode
   python -m genealogy_mapper.cli add-obituary "https://www.legacy.com/us/obituaries/example" --dry-run
   
   # Force rescrape existing URL
   python -m genealogy_mapper.cli add-obituary "https://www.legacy.com/us/obituaries/example" --force
   ```

python -m genealogy_mapper.cli list-obituaries

3. **Process Obituaries**
   - Extract text content from pending obituaries
   - Process text to identify individuals and relationships
   - Store extracted information in Neo4j

4. **Import to Neo4j**
   - Import processed data into Neo4j database
   - Create nodes for individuals and relationships
   - Handle conflicts and duplicates

5. **Visualize Relationships**
   - Generate visual representation of family relationships
   - Export graph data in various formats

## Command Options

### Obituary Management

#### Add a New Obituary
```bash
python -m genealogy_mapper.cli add-obituary "https://www.legacy.com/us/obituaries/example"
```
Options:
- `--dry-run`: Show what would be done without making changes
- `--force`: Force rescrape even if URL exists

Features:
- Automatic source detection from URL
- URL validation and accessibility check
- Metadata extraction (newspaper, location, publication date)
- Progress tracking and error handling
- Rich console output with detailed information

#### List Obituaries
```bash
python -m genealogy_mapper.cli list-obituaries [--status STATUS] [--source SOURCE]
```
Options:
- `--status`: Filter by status (PENDING, PROCESSING, COMPLETED, FAILED)
- `--source`: Filter by source website

#### Update Obituary Status
```bash
python -m genealogy_mapper.cli update-obituary URL --status STATUS [--error ERROR]
```
Options:
- `--status`: New status (PENDING, PROCESSING, COMPLETED, FAILED)
- `--error`: Error message (required if status is FAILED)

#### Process Obituaries
```bash
python -m genealogy_mapper.cli process-obituaries [--force]
```
Options:
- `--force`: Process all URLs, even if they have "completed" status

### Deprecated Commands

> **Note**: The following commands are deprecated and will be removed in a future version. Please use the new obituary management commands instead.

#### Import URL (Deprecated)
```bash
python -m genealogy_mapper.cli import-url URL
```
This command is deprecated. Please use `add-obituary` instead, which provides enhanced functionality including:
- Automatic source detection
- URL validation
- Metadata extraction
- Progress tracking
- Dry run mode
- Force rescrape option

## Development

### Project Structure

```
genealogy_mapper/
├── src/
│   └── genealogy_mapper/
│       ├── core/
│       │   ├── hybrid_processor.py
│       │   ├── neo4j_ops.py
│       │   ├── ner_processor.py
│       │   └── url_importer.py
│       └── cli.py
├── tests/
├── config.yaml
└── obituary_urls.json
```

### Running Tests

```bash
pytest
```

## Troubleshooting

1. **Missing Dependencies**
   - The program will check for required dependencies
   - If any are missing, you'll see a list and installation command
   - Run the suggested `pip install` command to install missing packages

2. **Configuration Issues**
   - Run `create-config` first to set up the configuration file
   - Check that your `.env` file has the required API keys and credentials
   - Use `--verbose` flag to see detailed configuration loading logs

3. **URL Processing Failures**
   - Use `--dry-run` to preview which URLs will be processed
   - Try increasing the timeout for slow websites
   - Use `--force-rescrape` to retry failed URLs
   - Check logs with `--verbose` for detailed error information

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Obituary Management

The system now includes a dedicated obituary management system that stores obituary URLs and their processing status directly in Neo4j. This provides better data consistency, tracking, and querying capabilities.

### Obituary Commands

1. **Add a New Obituary**
   ```bash
   # Add a new obituary URL (source is automatically detected)
   python -m genealogy_mapper.cli add-obituary "https://www.legacy.com/us/obituaries/example"
   ```

2. **List Obituaries**
   ```bash
   # List all obituaries
   python -m genealogy_mapper.cli list-obituaries

   # Filter by status
   python -m genealogy_mapper.cli list-obituaries --status PENDING

   # Filter by source
   python -m genealogy_mapper.cli list-obituaries --source "legacy.com"
   ```

3. **Update Obituary Status**
   ```bash
   # Update status to COMPLETED
   python -m genealogy_mapper.cli update-obituary "https://example.com/obit" --status COMPLETED

   # Update status to FAILED with error message
   python -m genealogy_mapper.cli update-obituary "https://example.com/obit" --status FAILED --error "Failed to extract text"
   ```

### Obituary Schema

The obituary management system uses the following Neo4j schema:

1. **Node Type**: `Obituary`
   - Properties:
     - `id`: Unique identifier (UUID)
     - `url`: Unique obituary URL
     - `status`: Processing status (PENDING, PROCESSING, COMPLETED, FAILED)
     - `source`: Source website (e.g., "legacy.com")
     - `created_at`: Timestamp of creation
     - `updated_at`: Timestamp of last update
     - `error_message`: Optional error message for failed processing

2. **Relationships**:
   - `(Obituary)-[:MENTIONS]->(Individual)`: Links obituary to individuals mentioned in it
   - `(Obituary)-[:PROCESSED_BY]->(Individual)`: Links obituary to the person it's about

3. **Constraints and Indexes**:
   - Unique constraint on `url`
   - Unique constraint on `id`
   - Index on `status` for quick filtering
   - Index on `source` for source-based queries
   - Index on `created_at` for chronological queries

### Benefits of Neo4j Storage

1. **Data Consistency**
   - Centralized storage of obituary information
   - Automatic tracking of processing status
   - Built-in constraints to prevent duplicates

2. **Querying Capabilities**
   - Find all obituaries mentioning a specific person
   - Track processing status across the system
   - Analyze patterns in obituary sources

3. **Integration**
   - Direct linking to individual nodes
   - Support for relationship tracking
   - Metadata management

4. **Monitoring**
   - Track processing status in real-time
   - Monitor error rates and patterns
   - Analyze processing times

### Example Queries

1. **Find Pending Obituaries**
   ```cypher
   MATCH (o:Obituary)
   WHERE o.status = 'PENDING'
   RETURN o
   ORDER BY o.created_at
   ```

2. **Find Obituaries by Source**
   ```cypher
   MATCH (o:Obituary)
   WHERE o.source = 'legacy.com'
   RETURN o
   ORDER BY o.created_at
   ```

3. **Find Obituaries Mentioning a Person**
   ```cypher
   MATCH (o:Obituary)-[:MENTIONS]->(i:Individual {name: 'John Smith'})
   RETURN o
   ORDER BY o.created_at
   ```

4. **Get Processing Statistics**
   ```cypher
   MATCH (o:Obituary)
   RETURN o.status, count(*) as count
   ORDER BY count DESC
   ```

### Migration from JSON Storage

If you were previously using the JSON-based storage system, you can migrate your data using the following steps:

1. **Export Existing URLs**
   ```bash
   # Export URLs from JSON file
   python -m genealogy_mapper.cli export-urls -i obituary_urls.json -o urls.txt
   ```

2. **Import to Neo4j**
   ```bash
   # Import URLs to Neo4j
   cat urls.txt | xargs -I {} python -m genealogy_mapper.cli add-obituary {}
   ```

3. **Verify Migration**
   ```bash
   # Check imported obituaries
   python -m genealogy_mapper.cli list-obituaries
   ``` 
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
   source .venv/bin/activate
   # On Windows:
   .venv\Scripts\activate

   # Verify activation
   which python  # Should show path to .venv/bin/python
   ```

3. Install dependencies:
   ```bash
   # Install all dependencies (including development tools)
   pip install -r requirements-dev.txt

   # Install the package in editable mode
   pip install -e .

   # Install Playwright browsers (required for web scraping)
   playwright install
   ```

   This step:
   - Installs all core dependencies (web scraping, NLP, database, etc.)
   - Installs development tools (testing, linting, formatting)
   - Installs the package in editable mode for development
   - Installs Playwright browsers (Chromium, Firefox, and WebKit) for web scraping

   Core dependencies include:
   - `selenium` and `webdriver-manager` for web scraping
   - `playwright` and its browsers for modern web scraping
   - `neo4j` for database operations
   - `openai` for text processing
   - `spacy` for natural language processing
   - `click` for CLI interface
   - `rich` for terminal formatting

   Development tools include:
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
The database uses a GEDCOM-compatible schema with:
- Person nodes with properties (name, birth date, death date, etc.)
- Relationship types (FAMILY, PARENT, CHILD, etc.)
- Constraints on unique identifiers
- Indexes for common query patterns

## Program Flow

Before starting, ensure you have:
1. Created and activated the virtual environment (`.venv`)
2. Installed all dependencies:
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```
3. Set up your environment variables (`.env` file)

Then proceed with:

1. **Initial Setup** (Only needed once)
   ```bash
   # Create configuration file (if not already created)
   python -m genealogy_mapper.cli create-config

   # Initialize Neo4j database (only needed once for first-time setup)
   python -m genealogy_mapper.cli init-database
   ```

2. **Import Obituary URLs**
   ```bash
   # Import a single URL
   python -m genealogy_mapper.cli import-url --import-url "https://example.com/obituary"

   # Import with custom timeout
   python -m genealogy_mapper.cli import-url --import-url "https://example.com/obituary" --timeout 10
   ```

3. **Extract Text from URLs**
   ```bash
   # Basic extraction
   python -m genealogy_mapper.cli extract-obit-text -i obituary_urls.json

   # With verbose logging
   python -m genealogy_mapper.cli extract-obit-text -i obituary_urls.json -v

   # Dry run to preview changes
   python -m genealogy_mapper.cli extract-obit-text -i obituary_urls.json --dry-run

   # Force rescrape of all URLs
   python -m genealogy_mapper.cli extract-obit-text -i obituary_urls.json --force-rescrape

   # All options together
   python -m genealogy_mapper.cli extract-obit-text -i obituary_urls.json --timeout 5 --force-rescrape --dry-run -v
   ```

4. **Process Obituaries**
   ```bash
   # Using hybrid processor (OpenAI + NER)
   python -m genealogy_mapper.cli add-obit-people -i obituary_urls.json -o processed_obituaries.json

   # Using NER only
   python -m genealogy_mapper.cli add-obit-people -i obituary_urls.json -o processed_obituaries.json --use-ner
   ```

5. **Import to Neo4j**
   ```bash
   # Basic import
   python -m genealogy_mapper.cli import-to-neo4j -i processed_obituaries.json

   # Preview changes without importing
   python -m genealogy_mapper.cli import-to-neo4j -i processed_obituaries.json --dry-run

   # Interactive conflict resolution
   python -m genealogy_mapper.cli import-to-neo4j -i processed_obituaries.json --interactive

   # Force import (skip validation)
   python -m genealogy_mapper.cli import-to-neo4j -i processed_obituaries.json --force
   ```

## Command Options

### extract-obit-text

Extract text from pending obituary URLs with the following options:

- `-i, --input-file, --obituaries-file`: Path to the obituary URLs JSON file (default: obituary_urls.json)
- `--timeout`: Timeout in seconds for web scraping operations (default: 3)
- `--force-rescrape`: Force rescrape of all URLs regardless of status
- `--dry-run`: Show what would be processed without making changes
- `-v, --verbose`: Enable verbose logging

Example output with verbose logging:
```
[INFO] Loading JSON file: obituary_urls.json
[INFO] Validating JSON structure
[INFO] Loading configuration
[INFO] Initializing URL importer with timeout=5
[INFO] Starting URL processing (force_rescrape=False)
⠋ Processing 5 URLs... [████████████████████] 100% 0:00:00
Processed: https://example.com/obit1 (completed)
Processed: https://example.com/obit2 (failed)
...
[INFO] Text extraction completed successfully
```

### Configuration Options

#### Timeouts

- Default timeout: 3 seconds
- Can be overridden per command using `--timeout`
- Affects web scraping operations (URL import and text extraction)
- Recommended values:
  - Fast sites: 3-5 seconds
  - Medium sites: 5-10 seconds
  - Slow sites: 10-30 seconds

#### Conflict Resolution

When importing data that conflicts with existing records, you can choose how to handle each conflict:

1. **Keep Existing**: Preserve the current value in the database
2. **Use New**: Replace with the new value from the import
3. **Merge**: For dates, keep the more specific one; for other fields, keep existing
4. **Skip**: Don't update this field

Conflicts are detected for:
- Birth dates
- Death dates
- Gender
- Birth place
- Death place

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
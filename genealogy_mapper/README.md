# Genealogy Mapper

A tool for processing and managing obituary URLs for genealogy research.

## Features

- Import and validate obituary URLs
- Store URLs in a structured JSON format
- Extract obituary text and metadata using Selenium
- Support for Legacy.com obituaries
- Comprehensive logging (both info and debug levels)
- Command-line interface
- Force rescrape option for reprocessing URLs
- Debug HTML saving for troubleshooting
- Configurable obituaries file location

## Setup

1. Create and activate a virtual environment:

    ```bash
    # Create virtual environment
    python -m venv .genealogy-env

    # Activate virtual environment
    # On macOS/Linux:
    source .genealogy-env/bin/activate
    # On Windows:
    .genealogy-env\Scripts\activate
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Set up environment variables:

   The application requires several environment variables to be set. You can set these in your shell or create a `.env` file in the project root:

   ```bash
   # OpenAI API key for text extraction
   export OPENAI_API_KEY='your-api-key-here'

   # Neo4j database credentials
   export NEO4J_URI='bolt://localhost:7687'
   export NEO4J_USER='neo4j'
   export NEO4J_PASSWORD='your-secure-password-here'

   # Optional: Debug logging (set to DEBUG for verbose output)
   export LOG_LEVEL='INFO'
   ```

   Or create a `.env` file:

   ```plaintext
   OPENAI_API_KEY=your-api-key-here
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-secure-password-here
   LOG_LEVEL=INFO
   ```

   Note: The `.env` file should be added to `.gitignore` to prevent committing sensitive information.

4. **Neo4j Database**

   The application uses Neo4j as its database. You can manage the Neo4j container using the provided script:

   ```bash
   # Check the status of the Neo4j container
   python scripts/manage_neo4j.py status

   # Start the Neo4j container
   python scripts/manage_neo4j.py start

   # Stop the Neo4j container
   python scripts/manage_neo4j.py stop

   # Remove the Neo4j container
   python scripts/manage_neo4j.py remove
   ```

   The Neo4j container exposes the following endpoints:

   - Browser Interface: <http://localhost:7474>
   - Bolt Connection: bolt://localhost:7687

   Default credentials:
   - Username: `neo4j`
   - Password: `********` (See config.yaml)

5. **Configuration**

   The application uses a `config.yaml` file for configuration. Ensure this file is present in the project root with the following structure:

   ```yaml
   # Neo4j Configuration
   neo4j:
     uri: bolt://localhost:7687
     user: neo4j
     password: your-secure-password-here
   ```

6. **Running Tests**

   To run the tests, execute:

   ```bash
   python -m pytest
   ```

   This will also verify that the Neo4j container is running and accessible.

## Development

### Project Structure

```plaintext
genealogy_mapper/
├── src/
│   └── genealogy_mapper/
│       ├── core/
│       │   ├── scrapers/
│       │   │   ├── base_scraper.py
│       │   │   ├── factory.py
│       │   │   └── legacy_scraper.py
│       │   └── url_importer.py
│       ├── utils/
│       │   └── logging_config.py
│       └── cli.py
├── tests/
│   ├── core/
│   │   ├── test_obituary_scraper.py
│   │   └── test_url_importer.py
│   ├── test_legacy_scraper.py
│   ├── test_scraper_factory.py
│   └── test_url_importer.py
├── pyproject.toml
└── README.md
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with verbose output
pytest -v
```

### Debug HTML

When running with debug logging enabled, the tool saves the full HTML of scraped pages to:

```plaintext
src/genealogy_mapper/debug/legacyscraper_page.html
```

This is useful for troubleshooting scraping issues.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

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

## Installation

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

## Usage

### Import a URL

```bash
# Basic usage
python -m genealogy_mapper import-url "https://www.legacy.com/us/obituaries/example"

# With debug logging
python -m genealogy_mapper --debug import-url "https://www.legacy.com/us/obituaries/example"

# With custom timeout (in seconds)
python -m genealogy_mapper --timeout 30 import-url "https://www.legacy.com/us/obituaries/example"

# With custom obituaries file location
python -m genealogy_mapper --obituaries-file /path/to/obituary_urls.json import-url "https://www.legacy.com/us/obituaries/example"
```

### Extract Obituary Text

```bash
# Process pending URLs
python -m genealogy_mapper extract-obit-text

# Force reprocess all URLs
python -m genealogy_mapper --force-rescrape extract-obit-text

# With custom obituaries file location
python -m genealogy_mapper --obituaries-file /path/to/obituary_urls.json extract-obit-text
```

### Global Options

The following options can be used with any command:

- `--timeout`: Set custom timeout in seconds (default: 3)
- `--obituaries-file`: Specify custom location for the obituary URLs JSON file (default: project root/obituary_urls.json)
- `--debug`: Enable debug logging
- `--force-rescrape`: Process all URLs regardless of status

### Logging

The tool provides two levels of logging:

- Info level: Basic operation information (default)
- Debug level: Detailed debugging information (enabled with --debug flag)

Logs are stored in the `logs` directory.

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
```
src/genealogy_mapper/debug/legacyscraper_page.html
```
This is useful for troubleshooting scraping issues.

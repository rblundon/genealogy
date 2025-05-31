# Genealogy Mapper

A tool for processing and managing obituary URLs for genealogy research.

## Features

- Import and validate obituary URLs
- Store URLs in a structured JSON format
- Comprehensive logging (both info and debug levels)
- Command-line interface

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
genealogy-mapper --import-url "https://www.legacy.com/us/obituaries/example"

# With debug logging
genealogy-mapper --debug --import-url "https://www.legacy.com/us/obituaries/example"
```

### Logging

The tool provides two levels of logging:
- Info level: Basic operation information (default)
- Debug level: Detailed debugging information (enabled with --debug flag)

Logs are stored in the `logs` directory.

## Development

### Project Structure

```
genealogy_mapper/
├── src/
│   └── genealogy_mapper/
│       ├── core/
│       │   └── url_importer.py
│       ├── utils/
│       │   └── logging_config.py
│       └── cli.py
├── tests/
├── pyproject.toml
└── README.md
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
``` 
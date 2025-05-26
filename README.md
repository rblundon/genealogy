# Genealogy Project

A Python package for processing genealogical data from obituaries and other sources.

## Features

- Read and process obituaries from various sources
- Extract names, relationships, and other relevant information
- Manage obituary catalogs with sorting and filtering capabilities
- Normalize dates and other data formats
- Comprehensive logging and error handling

## Installation

```bash
pip install -e .
```

## Usage

Basic usage:

```bash
genealogy input.json
```

With options:

```bash
genealogy input.json --output-file output.json --refresh-obits --log-file process.log --log-level DEBUG
```

### Command Line Options

- `input_file`: Path to input JSON file containing people data
- `--output-file`: Path to output JSON file (default: input_file with _processed suffix)
- `--refresh-obits`: Force refresh of obituaries
- `--log-file`: Path to log file (default: log to console only)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Project Structure

```
genealogy/
├── core/
│   ├── __init__.py
│   ├── obituary_reader.py
│   ├── people_finder.py
│   ├── obituary_catalog.py
│   └── date_normalizer.py
├── utils/
│   ├── __init__.py
│   └── logging_config.py
├── __init__.py
└── main.py
```

## Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install development dependencies: `pip install -e .`

## License

MIT License

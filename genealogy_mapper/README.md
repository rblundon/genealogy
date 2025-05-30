# Genealogy Mapper

A Python-based tool for processing and managing genealogy data, with a focus on obituaries and family relationships.

## Features

- Import obituary URLs from various sources
- Validate and store URLs in a structured JSON format
- Process and extract information from obituaries
- Manage family relationships and connections

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/genealogy.git
cd genealogy/genealogy_mapper
```

2. Create and activate a virtual environment:
```bash
python -m venv .genealogy-env
source .genealogy-env/bin/activate  # On Unix/macOS
# or
.genealogy-env\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
# Install core dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .
```

## Usage

### Importing URLs

To import an obituary URL:

```bash
genealogy-mapper --import-url "https://www.legacy.com/us/obituaries/example"
```

For debug output:

```bash
genealogy-mapper --debug --import-url "https://www.legacy.com/us/obituaries/example"
```

### Development

Run tests:
```bash
pytest -v
```

Run tests with coverage:
```bash
pytest --cov=genealogy_mapper --cov-report=term-missing
```

## Project Structure

```
genealogy_mapper/
├── src/
│   └── genealogy_mapper/
│       ├── core/
│       │   └── url_importer.py
│       └── cli.py
├── tests/
│   └── core/
│       └── test_url_importer.py
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Dependencies

### Core Dependencies
- requests: For making HTTP requests
- validators: For URL validation
- python-dateutil: For date handling
- rich: For terminal formatting

### Development Dependencies
- pytest: For testing
- black: For code formatting
- flake8: For linting
- mypy: For type checking
- pytest-cov: For test coverage
- pre-commit: For git hooks

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
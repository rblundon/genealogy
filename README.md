# Genealogy Mapper

A tool for extracting and managing genealogical information from obituaries.

## Features

- Extract obituary URLs from web pages
- Process obituary text to extract person information
- Store data in Neo4j database with GEDCOM-compatible schema
- Support for both NER and hybrid (OpenAI + NER) processing
- Interactive conflict resolution for data imports

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/genealogy-mapper.git
cd genealogy-mapper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and Neo4j credentials
```

## Usage

### Basic Workflow

1. Import obituary URLs:
```bash
python -m genealogy_mapper.cli import-url --import-url "https://example.com/obituary"
```

2. Extract text from pending URLs:
```bash
python -m genealogy_mapper.cli extract-obit-text
```

3. Process obituaries and extract person information:
```bash
# Using hybrid processor (OpenAI + NER)
python -m genealogy_mapper.cli add-obit-people -i obituary_urls.json -o processed_obituaries.json

# Using NER only
python -m genealogy_mapper.cli add-obit-people -i obituary_urls.json -o processed_obituaries.json --use-ner
```

4. Import data into Neo4j:
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

### Conflict Resolution

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

### Configuration

Create a configuration file:
```bash
python -m genealogy_mapper.cli create-config
```

Initialize the Neo4j database:
```bash
python -m genealogy_mapper.cli init-database
```

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

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
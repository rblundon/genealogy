# Genealogy Mapper

A tool for extracting and analyzing genealogical information from obituaries using Neo4j and OpenAI.

## Features

- Extract text from obituary URLs
- Process obituaries to identify people and relationships
- Store data in Neo4j graph database
- Visualize family relationships
- OpenAI-powered relationship analysis
- Interactive conflict resolution
- Comprehensive logging and error handling

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/genealogy-mapper.git
cd genealogy-mapper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `NEO4J_URI`: Neo4j database URI (default: bolt://localhost:7687)
- `NEO4J_USER`: Neo4j username (default: neo4j)
- `NEO4J_PASSWORD`: Neo4j password
- `OPENAI_API_KEY`: Your OpenAI API key

## Configuration

The application can be configured through:
1. Configuration file (config.yaml)
2. Environment variables
3. Command-line arguments

### Creating Configuration

Create a default configuration file:
```bash
python -m genealogy_mapper.cli create-config
```

This will create a `config.yaml` file with default settings for both Neo4j and OpenAI.

### Configuration Options

#### Neo4j Configuration
```yaml
neo4j:
  uri: bolt://localhost:7687
  user: neo4j
  password: your_password_here
  max_connection_lifetime: 3600
  max_connection_pool_size: 50
  connection_timeout: 30
```

#### OpenAI Configuration
```yaml
openai:
  api_key: your_openai_api_key_here
  model: gpt-4-turbo-preview
  temperature: 0.1
  max_tokens: 2000
```

### Environment Variables

You can also set configuration through environment variables:

```bash
# Neo4j settings
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_password

# OpenAI settings
export OPENAI_API_KEY=your_api_key
export OPENAI_MODEL=gpt-4-turbo-preview
export OPENAI_TEMPERATURE=0.1
export OPENAI_MAX_TOKENS=2000
```

The configuration is loaded in this order:
1. Default values
2. Values from config file
3. Environment variables (these take precedence)

## Usage

### Basic Workflow

1. **Set up configuration**
   ```bash
   # Create default configuration file
   python -m genealogy_mapper.cli create-config
   
   # Edit config.yaml to add your Neo4j password and OpenAI API key
   # Or set them as environment variables:
   export NEO4J_PASSWORD=your_password
   export OPENAI_API_KEY=your_api_key
   ```

2. **Initialize the database**
   ```bash
   python -m genealogy_mapper.cli init-database
   ```

3. **Import obituary URLs**
   ```bash
   python -m genealogy_mapper.cli import-url "https://example.com/obituary"
   ```

4. **Extract text from obituaries**
   ```bash
   python -m genealogy_mapper.cli extract-obit-text -i obituary_urls.json
   ```

5. **Process obituaries to identify people**
   ```bash
   python -m genealogy_mapper.cli add-obit-people -i obituary_urls.json
   ```

6. **Extract relationships using OpenAI**
   ```bash
   python -m genealogy_mapper.cli extract-relationships -i obituary_urls.json -o relationships_analysis.json
   ```

7. **Import relationships into Neo4j**
   ```bash
   python -m genealogy_mapper.cli import-relationships -i relationships_analysis.json
   ```

8. **Visualize the relationship graph**
   ```bash
   python -m genealogy_mapper.cli visualize-relationships -o family_tree.png
   ```

### Advanced Options

#### Interactive Conflict Resolution
```bash
python -m genealogy_mapper.cli import-to-neo4j -i obituary_people.json --interactive
```

#### Dry Run Mode
```bash
python -m genealogy_mapper.cli extract-relationships -i obituary_urls.json --dry-run
```

#### Force Reprocessing
```bash
python -m genealogy_mapper.cli extract-obit-text -i obituary_urls.json --force-rescrape
```

### Testing Configuration

Test your OpenAI configuration:
```bash
python -m genealogy_mapper.cli test-openai
```

## Data Model

The application uses a Neo4j graph database with the following structure:

### Nodes
- Individual (Person)
- Source (Obituary)
- Family
- Repository

### Relationships
- CITED_IN (Person -> Source)
- FAMILY (Person -> Family)
- PARENT_OF (Person -> Person)
- SPOUSE_OF (Person -> Person)

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
black src/
flake8 src/
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

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
# Install core dependencies and the package in editable mode
pip install -e .

# Install development dependencies (optional)
pip install -e ".[dev]"
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

### Quick Start (Recommended)

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

3. **Process an obituary (complete workflow)**
   ```bash
   python -m genealogy_mapper.cli process-obituary "https://example.com/obituary"
   ```

This single command will:
- Add the obituary URL to the database
- Extract text from the obituary
- Create an individual record
- (Future: Process relationships)

### Step-by-Step Workflow

For more control or debugging, you can run each step individually:

1. **Add obituary URL**
   ```bash
   python -m genealogy_mapper.cli add-obituary "https://example.com/obituary"
   ```

2. **Extract text from obituary**
   ```bash
   python -m genealogy_mapper.cli extract-text <obituary_id>
   ```

3. **Create individual record**
   ```bash
   python -m genealogy_mapper.cli create-individual <obituary_id>
   ```

4. **Process relationships (future)**
   ```bash
   python -m genealogy_mapper.cli process-relationships <individual_id>
   ```

### Database Management

**Clear all data:**
```bash
python -m genealogy_mapper.cli clear-database --force
```

**Reinitialize database:**
```bash
python -m genealogy_mapper.cli init-database
```

### Legacy Commands (Deprecated)

The following commands are still available but not recommended for new workflows:

- `extract-obit-text` - Use `extract-text` instead
- `add-obit-people` - Use `create-individual` instead
- `extract-relationships` - Use `process-relationships` instead
- `import-relationships` - Use `process-relationships` instead

### Advanced Options

#### Dry Run Mode
```bash
# Test the complete workflow without making changes
python -m genealogy_mapper.cli process-obituary "https://example.com/obituary" --dry-run

# Test individual steps
python -m genealogy_mapper.cli add-obituary "https://example.com/obituary" --dry-run
python -m genealogy_mapper.cli extract-text <obituary_id> --dry-run
python -m genealogy_mapper.cli create-individual <obituary_id> --dry-run
```

#### Force Reprocessing
```bash
# Force rescrape even if URL already exists
python -m genealogy_mapper.cli process-obituary "https://example.com/obituary" --force
```

#### Interactive Relationship Mapping
```bash
# Add missing parental relationships interactively
python -m genealogy_mapper.cli interactive-relationship-mapper
```

#### Traditional Name Normalization
```bash
# Apply traditional naming conventions (wife's last name to husband's)
python -m genealogy_mapper.cli normalize-traditional-names
```

#### OpenAI Cache Management
```bash
# Show cache status for all obituaries
python -m genealogy_mapper.cli show-cache-status

# Clear OpenAI cache
python -m genealogy_mapper.cli clear-openai-cache --all
```

### Testing Configuration

Test your OpenAI configuration:
```bash
python -m genealogy_mapper.cli test-openai
```

## Command Reference

### Core Workflow Commands

| Command | Description | Example |
|---------|-------------|---------|
| `process-obituary` | Complete workflow from URL to individual | `process-obituary "https://example.com/obit"` |
| `add-obituary` | Add obituary URL to database | `add-obituary "https://example.com/obit"` |
| `extract-text` | Extract text from obituary | `extract-text <obituary_id>` |
| `create-individual` | Create individual record | `create-individual <obituary_id>` |
| `process-relationships` | Process relationships (future) | `process-relationships <individual_id>` |

### Database Management

| Command | Description | Example |
|---------|-------------|---------|
| `init-database` | Initialize database schema | `init-database` |
| `clear-database` | Clear all data | `clear-database --force` |
| `list-obituaries` | List all obituaries | `list-obituaries` |

### Advanced Features

| Command | Description | Example |
|---------|-------------|---------|
| `interactive-relationship-mapper` | Add missing parental relationships | `interactive-relationship-mapper` |
| `normalize-traditional-names` | Apply traditional naming conventions | `normalize-traditional-names` |
| `process-relationships-from-db` | Extract relationships from database | `process-relationships-from-db` |

### Utility Commands

| Command | Description | Example |
|---------|-------------|---------|
| `create-config` | Create default config file | `create-config` |
| `test-openai` | Test OpenAI configuration | `test-openai` |
| `show-cache-status` | Show OpenAI cache status | `show-cache-status` |
| `clear-openai-cache` | Clear OpenAI cache | `clear-openai-cache --all` |
| `visualize-relationships` | Create relationship graph | `visualize-relationships` |

### Options

Most commands support these common options:
- `--dry-run`: Show what would be done without making changes
- `--force`: Force reprocessing even if already exists
- `--verbose`: Enable detailed logging

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

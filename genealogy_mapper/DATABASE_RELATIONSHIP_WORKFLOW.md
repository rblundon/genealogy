# Database Relationship Processing Workflow

## Overview

The relationship processing has been refactored to work directly with obituaries stored in the Neo4j database, eliminating the need for separate JSON files and providing a more streamlined workflow.

## New Commands

### 1. `extract-relationships-from-db`
Extract relationships from obituaries in the database using OpenAI analysis.

```bash
python -m genealogy_mapper.cli extract-relationships-from-db [OPTIONS]
```

**Options:**
- `--status`: Filter obituaries by status (`COMPLETED`, `PROCESSED`, `ALL`)
- `--output-file, -o`: Output JSON file path (default: `database_relationships.json`)
- `--force`: Force reprocessing of all obituaries
- `--dry-run`: Show what would be processed without making changes

**Example:**
```bash
# Extract relationships from completed obituaries
python -m genealogy_mapper.cli extract-relationships-from-db

# Extract from all obituaries with extracted text
python -m genealogy_mapper.cli extract-relationships-from-db --status ALL

# Dry run to see what would be processed
python -m genealogy_mapper.cli extract-relationships-from-db --dry-run
```

### 2. `import-relationships-from-db`
Import extracted relationships from database analysis into Neo4j.

```bash
python -m genealogy_mapper.cli import-relationships-from-db [OPTIONS]
```

**Options:**
- `--input-file, -i`: Input JSON file with relationship analysis (required)
- `--dry-run`: Show what would be imported without making changes

**Example:**
```bash
# Import relationships from analysis file
python -m genealogy_mapper.cli import-relationships-from-db -i database_relationships.json

# Dry run to preview imports
python -m genealogy_mapper.cli import-relationships-from-db -i database_relationships.json --dry-run
```

### 3. `process-relationships-from-db` ⭐ **NEW COMPLETE WORKFLOW**
Complete workflow: Extract and import relationships from obituaries in the database in one step.

```bash
python -m genealogy_mapper.cli process-relationships-from-db [OPTIONS]
```

**Options:**
- `--status`: Filter obituaries by status (`COMPLETED`, `PROCESSED`, `ALL`)
- `--force`: Force reprocessing of all obituaries
- `--dry-run`: Show what would be processed without making changes
- `--skip-extraction`: Skip OpenAI extraction and use existing analysis
- `--analysis-file, -a`: Use existing analysis file instead of extracting from database

**Examples:**

**Complete workflow (recommended):**
```bash
# Process all completed obituaries in one step
python -m genealogy_mapper.cli process-relationships-from-db

# Process all obituaries with extracted text
python -m genealogy_mapper.cli process-relationships-from-db --status ALL

# Dry run to preview the complete workflow
python -m genealogy_mapper.cli process-relationships-from-db --dry-run
```

**Using existing analysis file:**
```bash
# Use existing analysis file and import to database
python -m genealogy_mapper.cli process-relationships-from-db -a existing_analysis.json
```

## Workflow Comparison

### Old Workflow (File-based)
1. Export obituaries to JSON file
2. Extract relationships from JSON file
3. Import relationships from analysis file

### New Workflow (Database-based) ⭐
1. **Single command**: `process-relationships-from-db`
   - Reads obituaries directly from database
   - Extracts relationships using OpenAI
   - Imports relationships into Neo4j
   - All in one step!

## Benefits of the New Workflow

1. **Simplified Process**: One command instead of three
2. **Direct Database Access**: No need for intermediate JSON files
3. **Real-time Data**: Always works with current database state
4. **Better Error Handling**: Integrated error handling across the entire workflow
5. **Flexible Options**: Can use existing analysis files or skip extraction
6. **Dry Run Support**: Preview what will happen before making changes

## Database Requirements

The new workflow requires:
- Neo4j database with obituaries
- Obituaries with `extracted_text` field populated
- OpenAI API key configured (for extraction step)

## Example Complete Workflow

```bash
# 1. Add obituary to database
python -m genealogy_mapper.cli add-obituary "https://example.com/obituary"

# 2. Process obituary (extract text and create person)
python -m genealogy_mapper.cli process-obituaries

# 3. Extract and import all relationships in one step
python -m genealogy_mapper.cli process-relationships-from-db

# 4. Visualize the family tree
python -m genealogy_mapper.cli visualize-relationships
```

## Troubleshooting

### No obituaries found
- Ensure obituaries have been processed and have `extracted_text`
- Check database connection and configuration

### OpenAI API errors
- Verify OpenAI API key is set in config or environment
- Check API quota and billing status

### Import failures
- Check Neo4j database connection
- Verify database schema is properly initialized
- Review relationship processor logs for specific errors

## Migration from Old Workflow

If you have existing JSON files from the old workflow:

```bash
# Use existing analysis file with new workflow
python -m genealogy_mapper.cli process-relationships-from-db -a your_existing_analysis.json
```

This allows you to use existing analysis data while benefiting from the new database-based import process. 
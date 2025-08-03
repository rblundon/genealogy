# Traditional Naming Conventions

## Overview

The genealogy mapper includes functionality to handle traditional naming conventions where spouses take each other's last names. This is particularly useful for genealogical research where historical naming patterns need to be preserved and standardized.

## Features

### 1. Automatic Name Normalization
- **Identifies spouse relationships** in the database
- **Determines which spouse should take the other's last name** using intelligent heuristics
- **Preserves original last names** as `maiden_name` field
- **Updates person names** to reflect traditional naming conventions

### 2. Conservative Heuristics
The system uses conservative logic to avoid incorrect changes:

- **Only processes couples with different last names**
- **Requires clear name structure differences** (e.g., one spouse has middle name, other doesn't)
- **Skips ambiguous cases** to prevent incorrect changes
- **Preserves maiden names** for genealogical research

## Usage

### CLI Command
```bash
# Preview changes without making them
python -m genealogy_mapper.cli normalize-traditional-names --dry-run

# Apply traditional naming conventions
python -m genealogy_mapper.cli normalize-traditional-names
```

### Programmatic Usage
```python
from genealogy_mapper.core.relationship_processor import RelationshipProcessor

processor = RelationshipProcessor()
normalized_persons = processor._normalize_traditional_names(persons)
```

## Examples

### Example 1: Simple Name Change
**Before:**
- John Smith (M)
- Mary Johnson (F) - married to John

**After:**
- John Smith (M)
- Mary Smith (F) - maiden: Johnson

### Example 2: Middle Name Preservation
**Before:**
- Robert Wilson (M)
- Sarah Davis (F) - married to Robert

**After:**
- Robert Wilson (M)
- Sarah Wilson (F) - maiden: Davis

### Example 3: Complex Names
**Before:**
- Michael Brown (M)
- Elizabeth Taylor (F) - married to Michael

**After:**
- Michael Brown (M)
- Elizabeth Brown (F) - maiden: Taylor

## Database Schema

### Person Node Properties
- `name`: Current full name
- `maiden_name`: Original last name (if changed)
- `sex`: Gender (M/F)
- `birth_date`: Birth date
- `death_date`: Death date

### Example Neo4j Query
```cypher
MATCH (p:Individual)
WHERE p.maiden_name IS NOT NULL
RETURN p.name, p.maiden_name
```

## Heuristics

### Name Change Logic
1. **Identify spouse relationships** using `SPOUSE_OF` relationships
2. **Compare name structures** between spouses
3. **Determine likely wife** based on name complexity
4. **Apply traditional naming** if clear pattern exists

### Conservative Rules
- ✅ Only change if last names are different
- ✅ Require clear name structure differences
- ✅ Preserve maiden names in separate field
- ❌ Skip ambiguous cases
- ❌ Don't change already-matching names

## Integration

### Relationship Processing
The traditional naming normalization is automatically applied during:
- `process-relationships-from-db` command
- `extract-relationships-from-db` command
- Manual relationship processing

### Database Updates
When names are normalized:
1. **Person node is updated** with new name
2. **Maiden name is stored** in `maiden_name` field
3. **Relationships remain unchanged**
4. **History is preserved** for genealogical research

## Benefits

### For Genealogical Research
- **Preserves naming history** through maiden names
- **Standardizes family names** for easier searching
- **Maintains relationship integrity** while updating names
- **Supports traditional research methods**

### For Data Management
- **Automated processing** reduces manual work
- **Conservative approach** prevents errors
- **Audit trail** through maiden name preservation
- **Flexible application** via CLI or programmatic access

## Troubleshooting

### No Changes Applied
- Check if spouse relationships exist in database
- Verify that couples have different last names
- Ensure name structures are sufficiently different

### Unexpected Changes
- Review the heuristics logic
- Use `--dry-run` to preview changes
- Check maiden names for verification

### Database Issues
- Verify Neo4j connection
- Check person node structure
- Ensure proper permissions for updates

## Future Enhancements

### Planned Features
- **Custom naming rules** for specific cultures
- **Batch processing** for large datasets
- **Historical period detection** for appropriate naming
- **Manual override options** for edge cases

### Configuration Options
- **Enable/disable automatic normalization**
- **Custom heuristics** for different naming patterns
- **Culture-specific rules** for international research
- **Audit logging** for all name changes 
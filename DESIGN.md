# Genealogy Mapper Design Decisions

## Markdown Standards

This document follows standard markdown formatting:

1. **Headers**
   - Use `#` for main title
   - Use `##` for section headers
   - Use `###` for subsections
   - Add a blank line before and after headers

2. **Lists**
   - Use `-` for unordered lists
   - Use `1.` for ordered lists
   - Indent nested lists with 2 spaces
   - Add a blank line before and after lists

3. **Code Blocks**
   - Use triple backticks with language specification
   - Add a blank line before and after code blocks
   - Example:
     ```python
     def example():
         pass
     ```

4. **Inline Code**
   - Use single backticks for inline code
   - Example: `variable_name`

5. **Links**
   - Use `[text](url)` format
   - Add a blank line before and after link blocks

6. **Tables**
   - Use `|` for column separation
   - Use `-` for header separation
   - Example:
     | Column 1 | Column 2 |
     |----------|----------|
     | Value 1  | Value 2  |

7. **Blockquotes**
   - Use `>` for blockquotes
   - Add a blank line before and after

8. **Horizontal Rules**
   - Use `---` for horizontal rules
   - Add a blank line before and after

## Data Storage

### JSON File Location

- The `obituary_urls.json` file is stored in the project root directory (`/Users/rblundon/git/genealogy/obituary_urls.json`), not within the program code.
- Rationale: This makes it easier to find and manage the data file, and allows for easier backup and version control.

### JSON Structure

```json
{
  "urls": [
    {
      "url": "string",
      "date_added": "YYYY-MM-DD",
      "source": "string",
      "status": "pending|completed|failed",
      "extracted_text": "string|null",
      "metadata": {
        "name": "string",
        "birth_date": "string|null",
        "death_date": "string|null",
        "newspaper": "string|null",
        "location": "string|null",
        "publication_date": "string|null"
      }
    }
  ],
  "last_updated": "ISO8601 timestamp"
}
```

- `date_added`: Used instead of `imported_at` to track when URLs are added
- `source`: Identifies the source website (e.g., "legacy.com")
- `status`: Tracks the processing state of each URL
- `extracted_text`: The full text content of the obituary
- `metadata`: Contains structured information about the obituary

## Web Scraping

### Scraper Architecture

- Uses a factory pattern (`ScraperFactory`) to create appropriate scrapers based on URL
- Base scraper class (`BaseScraper`) provides common functionality
- Legacy.com scraper (`LegacyScraper`) handles Legacy.com specific extraction
- Each scraper implements its own text and metadata extraction logic

### Selenium Usage

- Selenium is used instead of simple HTTP requests because Legacy.com requires JavaScript execution
- Headless mode is enabled by default for better performance
- Chrome WebDriver is managed automatically via webdriver-manager
- Debug HTML is saved when logging is enabled

### Timeout Configuration

- Default timeout is set to 30 seconds for element loading
- This value was chosen to handle slow-loading pages and network delays
- Timeout is configurable via CLI `--timeout` option
- Timeout is applied to both page load and element wait operations

### Text Extraction Strategy

1. First attempts to extract from JSON-LD data (most reliable)
2. Falls back to CSS selectors if JSON-LD extraction fails
3. Uses multiple selectors to handle different page layouts:
   - `.obit-text` for main obituary text
   - `.obit-name` for name
   - `.obit-date` for dates
   - `.obit-location` for location

### Force Rescrape Feature

- Added to allow reprocessing of URLs regardless of status
- Useful for:
  - Retrying failed extractions
  - Updating existing data
  - Testing changes to extraction logic
- Enabled via CLI `--force-rescrape` flag

## CLI Design

### Command Structure

- Uses Click's command groups for better organization
- Global options:
  - `--timeout`: Set custom timeout (default: 30s)
  - `--debug`: Enable debug logging
  - `--force-rescrape`: Process all URLs regardless of status
- Commands:
  - `import-url`: Import a new URL
  - `extract-obit-text`: Process pending URLs

### Error Handling

- Failed scrapes are marked with "failed" status
- URLs can be reprocessed using force rescrape
- Detailed logging for debugging
- Debug HTML saved for troubleshooting
- Graceful handling of network errors and timeouts

## Future Considerations

### Rate Limiting

- Consider adding rate limiting for large batches of URLs
- Respect website's robots.txt and terms of service
- Add delays between requests

### Data Validation

- Add schema validation for the JSON structure
- Validate extracted text and metadata
- Add data cleaning and normalization

### Performance

- Consider parallel processing for multiple URLs
- Cache results to avoid re-scraping unchanged content
- Add progress bars for long-running operations

### Additional Sources

- Add support for more obituary websites
- Create new scraper implementations
- Add source-specific metadata extraction

## Configuration

### Timeouts

- Default timeout: 3 seconds
- Configurable per operation
- Affects:
  - Page loading
  - Element waiting
  - API calls
- Recommended values:
  - Fast sites: 3-5 seconds
  - Medium sites: 5-10 seconds
  - Slow sites: 10-30 seconds

### Conflict Resolution

The system implements a sophisticated conflict resolution system for handling data inconsistencies:

1. **Detection**
   - Compares new data with existing records
   - Identifies conflicts in:
     - Dates
     - Names
     - Places
     - Relationships

2. **Resolution Strategies**
   - Keep Existing: Preserve current data
   - Use New: Replace with new data
   - Merge: Combine data intelligently
   - Skip: No update

3. **Interactive Mode**
   - User-guided resolution
   - Preview of changes
   - Batch resolution options

4. **Validation**
   - Data format checking
   - Consistency verification
   - Quality metrics

## Data Model

### Neo4j Schema

1. **Nodes**
   - Individual
     - Properties: `id`, `name`, `birth_date`, `death_date`, `gender`
     - Metadata: `created_at`, `updated_at`, `data_quality`
   - Source
     - Properties: `id`, `title`, `url`, `type`
     - Metadata: `created_at`, `updated_at`
   - Place
     - Properties: `id`, `name`, `type`, `coordinates`
     - Metadata: `created_at`, `updated_at`

2. **Relationships**
   - CITED_IN
     - Properties: `confidence`, `source`
     - Metadata: `created_at`
   - BORN_IN
     - Properties: `date`
     - Metadata: `created_at`
   - DIED_IN
     - Properties: `date`
     - Metadata: `created_at`
   - RELATED_TO
     - Properties: `relationship_type`
     - Metadata: `created_at`

## Implementation Details

### Web Scraping

1. **Timeout Handling**
   ```python
   def process_url(url: str, timeout: int = 3):
       try:
           # Set page load timeout
           page.set_default_timeout(timeout)
           # Wait for content
           page.wait_for_selector('.content', timeout=timeout)
       except TimeoutError:
           logger.warning(f"Timeout after {timeout} seconds")
           return None
   ```

2. **Error Recovery**
   - Automatic retries
   - Fallback strategies
   - Error logging

### Data Processing

1. **Hybrid Processing**
   ```python
   class HybridProcessor:
       def extract_info(self, text: str) -> PersonInfo:
           # NER processing
           ner_results = self.ner_processor.process(text)
           # OpenAI processing
           ai_results = self.openai_processor.process(text)
           # Merge results
           return self.merge_results(ner_results, ai_results)
   ```

2. **Conflict Resolution**
   ```python
   class ConflictResolver:
       def resolve(self, existing: Dict, new: Dict) -> Dict:
           conflicts = self.detect_conflicts(existing, new)
           if self.interactive:
               return self.interactive_resolve(conflicts)
           return self.auto_resolve(conflicts)
   ```

## Future Enhancements

1. **Performance**
   - Parallel processing
   - Caching system
   - Optimized timeouts

2. **Data Quality**
   - Enhanced validation
   - Confidence scoring
   - Source reliability tracking

3. **User Interface**
   - Web interface
   - Batch operations
   - Progress tracking

4. **Integration**
   - GEDCOM import/export
   - DNA data integration
   - External API support

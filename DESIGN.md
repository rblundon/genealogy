# Genealogy Mapper Design Decisions

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
- `metadata`: Contains structured information about the obituary

## Web Scraping

### Selenium Usage
- Selenium is used instead of simple HTTP requests because Legacy.com requires JavaScript execution.
- Headless mode is enabled by default for better performance.

### Timeout Configuration
- Default timeout is set to 3 seconds for element loading.
- This value was chosen as a balance between speed and reliability.
- Timeout is configurable via CLI `--timeout` option for flexibility.

### Text Extraction Strategy
1. First attempts to extract from JSON-LD data (most reliable)
2. Falls back to CSS selectors if JSON-LD extraction fails
3. Uses multiple selectors to handle different page layouts

## CLI Design

### Command Structure
- Uses Click's command groups for better organization
- Global options (like `--timeout`) are available to all commands
- Commands are named without dashes (e.g., `extract-obit-text`)

### Error Handling
- Failed scrapes are marked with "failed" status
- URLs can be reprocessed regardless of status
- Detailed logging for debugging

## Future Considerations

### Rate Limiting
- Consider adding rate limiting for large batches of URLs
- Respect website's robots.txt and terms of service

### Data Validation
- Add schema validation for the JSON structure
- Validate extracted text and metadata

### Performance
- Consider parallel processing for multiple URLs
- Cache results to avoid re-scraping unchanged content 
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

# Web Scraper

A flexible and robust web scraping framework built with Python.

## Features

- Built-in error handling and logging
- Session management for efficient scraping
- JSON data export
- Customizable headers and user agents
- Type hints for better code maintainability

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

## Best Practices

1. Always respect the website's robots.txt file
2. Implement appropriate delays between requests
3. Use proper error handling
4. Set appropriate User-Agent headers
5. Consider using proxies for large-scale scraping

## License

MIT License

## Setup

1. Install Python dependencies:

    pip install -r requirements.txt

2. Run the scraper as usual:

    python obituary_scraper.py people.json

The scraper will use a headless Chrome browser to fetch and render search result pages, allowing it to see JavaScript-loaded content.

## Input File Template

The input file should be a JSON file with the following structure:

```json
[
  {
    "name": "George Wendt",
    "birth_date": null,
    "death_date": null,
    "url": "https://www.legacy.com/us/obituaries/legacyremembers/george-wendt-obituary?pid=209121532",
    "id": "P1"
  },
]
```

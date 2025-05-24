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

1. Create a new scraper by subclassing the `WebScraper` class
2. Implement the `scrape()` method with your specific scraping logic
3. Run your scraper

Example:
```python
from scraper import WebScraper

class MyScraper(WebScraper):
    def scrape(self):
        soup = self.get_page(self.base_url)
        if not soup:
            return []
        
        # Add your scraping logic here
        data = []
        # ... your scraping code ...
        return data

# Use the scraper
scraper = MyScraper('https://example.com')
data = scraper.scrape()
scraper.save_to_json(data, 'output.json')
```

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

2. Install ChromeDriver:

    - Download ChromeDriver from https://sites.google.com/chromium.org/driver/
    - Make sure the version matches your installed Google Chrome browser.
    - Place the `chromedriver` binary in your PATH (e.g., `/usr/local/bin`).
    - On macOS, you can use Homebrew:
      brew install chromedriver

3. Run the scraper as usual:

    python obituary_scraper.py people.json

The scraper will use a headless Chrome browser to fetch and render search result pages, allowing it to see JavaScript-loaded content.

## Input File Template

The input file should be a JSON file with the following structure:

```json
[
  {
    "name": "Maxine Kaczmarowski",
    "birth_date": null,
    "death_date": "May 24, 2018",
    "location": "Milwaukee, WI",
    "obituary_text": "Kaczmarowski, Maxine V. (NEE Paradowski) Reunited with her husband Terrence and daughter Patricia on May 24, 2018 at the age of 87 years. Survived by her faithful son-in-law Steve Blundon; grandchildren Ryan (Amy) Blundon and Megan (Ross) Wurz; great-grandchildren Autumn, Caralyn and Finley; and brothers Reginald (Donna) Paradowski and Joseph (Rosemary) Paradowski. Also survived by other relatives and friends. Maxine was always up for Bingo, loved traveling the world and made the best walnut torte, chicken dumpling soup and apple pie. Visitation Wednesday, May 30 from 9:30 to 10:30 AM at ST. ROMAN CHURCH (1810 W. Bolivar Ave) followed by the Celebration of Mass of Christian Burial at 10:30 AM. Interment St. Adalbert Cemetery.",
    "url": "https://www.legacy.com/us/obituaries/jsonline/name/maxine-kaczmarowski-obituary?id=3326788",
    "first_name": "Maxine",
    "last_name": "Kaczmarowski",
    "id": "P1"
  },
  {
    "name": "Terrence Kaczmarowski",
    "birth_date": "1 Jan 1928",
    "death_date": "December 18, 2008",
    "location": "Milwaukee, WI",
    "obituary_text": "Kaczmarowski, Terrence E. Thursday, December 18, 2008, age 80 years. Beloved husband of Maxine (nee Paradowski). Loving father of the late Patricia (Steve) Blundon. Cherished grandfather of Ryan (Amy) and Megan (Ross) Wurz. Proud gramps of Autumn and Caralyn. Brother-in-law of Reginald (Donna) Paradowski and Joseph (Rose Mary) Paradowski. Also survived by other relatives and friends. Visitation Monday at the Funeral Home from 4-8PM. Mass of Christian Burial Tuesday 10AM at ST. ROMAN CHURCH, 1810 W. Bolivar Ave. Please meet directly at church for Mass. Interment St. Adalbert Cemetery. Retiree of Maynard Steel after 46 years, and employee of the Franklin Walmart for 13 years. JOHN J. WALLOCH FUNERAL HOME 4309 S. 20th St. 414-281-7145 Family Owned/Operated-We Care",
    "url": "https://www.legacy.com/us/obituaries/jsonline/name/terrence-kaczmarowski-obituary?id=3182470",
    "first_name": "Terry",
    "last_name": "Kaczmarowski",
    "id": "P2"
  }
]
```
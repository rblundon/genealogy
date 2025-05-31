import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

@pytest.fixture(scope="session")
def chrome_driver():
    """Create a Chrome WebDriver instance for testing."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    yield driver
    
    driver.quit()

@pytest.fixture(scope="session")
def test_data_dir():
    """Get the path to the test data directory."""
    return os.path.join(os.path.dirname(__file__), 'test_data')

@pytest.fixture(scope="session")
def sample_html():
    """Get a sample HTML file for testing."""
    return """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "articleBody": "Test obituary text for Maxine Kaczmarowski",
                "headline": "Maxine Kaczmarowski Obituary",
                "datePublished": "2018-05-27T00:00:00.000Z",
                "publisher": {
                    "name": "Legacy"
                },
                "deathPlace": {
                    "address": {
                        "addressLocality": "Milwaukee",
                        "addressRegion": "WI"
                    }
                }
            }
            </script>
        </head>
        <body>
            <h1 class="obit-name">Maxine Kaczmarowski</h1>
            <div class="obit-location">Milwaukee, WI</div>
            <div class="obit-source">Legacy</div>
            <div class="obit-dates">1920 - 2018</div>
            <div class="obit-text">
                Test obituary text for Maxine Kaczmarowski
            </div>
        </body>
    </html>
    """ 
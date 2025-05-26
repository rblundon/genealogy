"""
Test suite for name extraction functionality.
"""

import unittest
from bs4 import BeautifulSoup
from genealogy.core.name_extractor import NameExtractor
from genealogy.core.obituary_processor import ObituaryProcessor
from genealogy.core.obituary_reader import ObituaryReader
from genealogy.core.people_finder import PeopleFinder

class TestNameExtraction(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.name_extractor = NameExtractor()
        self.obituary_processor = ObituaryProcessor()
        self.people_finder = PeopleFinder()

    def test_clean_name(self):
        """Test name cleaning functionality."""
        test_cases = [
            ("John Smith (Johnny) Obituary", "John Smith"),
            ("Mary Jane (née Jones) Smith", "Mary Jane Smith"),
            ("Robert \"Bob\" Johnson Jr.", "Robert Johnson Jr."),
            ("Dr. James Wilson III", "James Wilson III"),
            ("Mrs. Sarah Brown - 2023", "Sarah Brown"),
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.name_extractor.clean_name(input_name)
                self.assertEqual(result, expected)

    def test_extract_from_title(self):
        """Test name extraction from title."""
        test_cases = [
            (
                """
                <html>
                    <head><title>John Smith Obituary - New York - Smith Funeral Home</title></head>
                    <body></body>
                </html>
                """,
                ("John Smith", "New York")
            ),
            (
                """
                <html>
                    <head><title>Mary Jane Smith Memorial - Chicago, IL</title></head>
                    <body></body>
                </html>
                """,
                ("Mary Jane Smith", "Chicago, IL")
            ),
        ]
        
        for html, expected in test_cases:
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                name, location = self.name_extractor.extract_from_title(soup)
                self.assertEqual(name, expected[0])
                self.assertEqual(location, expected[1])

    def test_extract_full_name(self):
        """Test full name extraction from text."""
        test_cases = [
            (
                """
                <html>
                    <head><title>Obituary</title></head>
                    <body>
                        <p>John Smith passed away peacefully on January 1, 2023.</p>
                    </body>
                </html>
                """,
                "John Smith"
            ),
            (
                """
                <html>
                    <head><title>Memorial</title></head>
                    <body>
                        <p>In loving memory of Mary Jane Smith, who died on February 2, 2023.</p>
                    </body>
                </html>
                """,
                "Mary Jane Smith"
            ),
        ]
        
        for html, expected in test_cases:
            with self.subTest(html=html):
                soup = BeautifulSoup(html, 'html.parser')
                text = soup.get_text()
                result = self.name_extractor.extract_full_name(soup, text)
                self.assertEqual(result, expected)

    def test_people_finder_integration(self):
        """Test PeopleFinder integration with NameExtractor."""
        test_obituary = {
            'title': 'John Smith Obituary - New York',
            'obituary_text': """
                John Smith passed away on January 1, 2023.
                He is survived by his wife Mary Smith and children Robert Smith and Sarah Smith.
                His brother James Smith and sister Jane Smith also survive him.
            """
        }
        
        result = self.people_finder.process_obituary(test_obituary)
        self.assertIn('extracted_names', result)
        
        # Verify deceased
        deceased = next((n for n in result['extracted_names'] if n['relationship'] == 'deceased'), None)
        self.assertIsNotNone(deceased)
        self.assertEqual(deceased['name'], 'John Smith')
        
        # Verify family members
        names = {n['name'] for n in result['extracted_names']}
        expected_names = {'John Smith', 'Mary Smith', 'Robert Smith', 'Sarah Smith', 'James Smith', 'Jane Smith'}
        self.assertEqual(names, expected_names)

    def test_obituary_processor_integration(self):
        """Test ObituaryProcessor integration with NameExtractor."""
        test_person = {
            'url': 'http://example.com/obituary',
            'id': 'test123'
        }
        
        # Mock the response
        test_html = """
            <html>
                <head><title>John Smith Obituary - New York - Smith Funeral Home</title></head>
                <body>
                    <p>John Smith passed away on January 1, 2023.</p>
                    <p>He was born on January 1, 1950.</p>
                </body>
            </html>
        """
        
        # Monkey patch requests.Session.get
        import requests
        original_get = requests.Session.get
        def mock_get(self, *args, **kwargs):
            class MockResponse:
                def __init__(self, text):
                    self.text = text
                def raise_for_status(self):
                    pass
            return MockResponse(test_html)
        requests.Session.get = mock_get
        
        try:
            result = self.obituary_processor.process_url('http://example.com/obituary', test_person)
            self.assertEqual(result['full_name'], 'John Smith')
            self.assertEqual(result['location'], 'New York')
        finally:
            # Restore original requests.Session.get
            requests.Session.get = original_get

if __name__ == '__main__':
    unittest.main() 
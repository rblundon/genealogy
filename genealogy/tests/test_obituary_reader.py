"""
Tests for the ObituaryReader class.
"""

import unittest
import tempfile
import json
import os
from unittest.mock import patch, MagicMock
from genealogy.core.obituary_reader import ObituaryReader

class TestObituaryReader(unittest.TestCase):
    def setUp(self):
        """Set up test cases."""
        # Create temporary input and output files
        self.input_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        self.output_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
        
        # Sample input data
        self.sample_data = [
            {
                'id': '1',
                'name': 'John Smith',
                'obituary_url': 'http://example.com/obit1',
                'obituary_text': None
            },
            {
                'id': '2',
                'name': 'Mary Smith',
                'obituary_url': 'http://example.com/obit2',
                'obituary_text': 'This is a valid obituary text. It is long enough to pass the validation. The word obituary is present and the text is more than 100 characters. This ensures the test for already processed obituaries works as expected.'
            }
        ]
        
        # Write sample data to input file
        json.dump(self.sample_data, self.input_file)
        self.input_file.close()
        self.output_file.close()

    def tearDown(self):
        """Clean up test files."""
        os.unlink(self.input_file.name)
        os.unlink(self.output_file.name)

    def test_is_valid_url(self):
        """Test URL validation."""
        reader = ObituaryReader(self.input_file.name, self.output_file.name)
        
        # Valid URLs
        self.assertTrue(reader.is_valid_url('http://example.com'))
        self.assertTrue(reader.is_valid_url('https://example.com/path'))
        
        # Invalid URLs
        self.assertFalse(reader.is_valid_url(''))
        self.assertFalse(reader.is_valid_url('not a url'))
        self.assertFalse(reader.is_valid_url('http://'))

    def test_is_valid_obituary_text(self):
        """Test obituary text validation."""
        reader = ObituaryReader(self.input_file.name, self.output_file.name)
        
        # Valid text
        valid_text = """
        John Smith passed away on January 15, 2020.
        He was survived by his wife and children.
        """
        self.assertTrue(reader.is_valid_obituary_text(valid_text))
        
        # Invalid text
        self.assertFalse(reader.is_valid_obituary_text(''))
        self.assertFalse(reader.is_valid_obituary_text('Too short'))
        self.assertFalse(reader.is_valid_obituary_text('This is not an obituary'))

    @patch('requests.get')
    def test_read_obituary(self, mock_get):
        """Test reading obituary from URL."""
        reader = ObituaryReader(self.input_file.name, self.output_file.name)
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <body>
                <script>var x = 1;</script>
                <style>.hidden { display: none; }</style>
                <div>John Smith passed away on January 15, 2020.</div>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test successful read
        text = reader.read_obituary('http://example.com/obit')
        self.assertIsNotNone(text)
        self.assertIn('John Smith passed away', text)
        self.assertNotIn('var x = 1', text)
        self.assertNotIn('.hidden', text)
        
        # Test failed read
        mock_get.side_effect = Exception('Connection error')
        text = reader.read_obituary('http://example.com/obit')
        self.assertIsNone(text)

    def test_extract_fields(self):
        """Test extracting fields from obituary text."""
        reader = ObituaryReader(self.input_file.name, self.output_file.name)
        
        text = """
        John Smith passed away on January 15, 2020 at the age of 75.
        He was born on January 15, 1945.
        """
        
        fields = reader.extract_fields(text)
        self.assertEqual(fields['death_date'], '15 Jan 2020')
        self.assertEqual(fields['birth_date'], '15 Jan 1945')

    @patch('requests.get')
    def test_process_person(self, mock_get):
        """Test processing a single person."""
        reader = ObituaryReader(self.input_file.name, self.output_file.name)
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <body>
                John Smith passed away on January 15, 2020 at the age of 75.
                He was born on January 15, 1945.
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test processing new person
        person = {
            'id': '1',
            'name': 'John Smith',
            'obituary_url': 'http://example.com/obit1',
            'obituary_text': None
        }
        
        processed = reader.process_person(person)
        self.assertIsNotNone(processed['obituary_text'])
        self.assertEqual(processed['death_date'], '15 Jan 2020')
        self.assertEqual(processed['birth_date'], '15 Jan 1945')
        
        # Test skipping already processed person
        person = {
            'id': '2',
            'name': 'Mary Smith',
            'obituary_url': 'http://example.com/obit2',
            'obituary_text': 'This is a valid obituary text. It is long enough to pass the validation. The word obituary is present and the text is more than 100 characters. This ensures the test for already processed obituaries works as expected.'
        }
        
        processed = reader.process_person(person)
        self.assertEqual(processed['obituary_text'], 'This is a valid obituary text. It is long enough to pass the validation. The word obituary is present and the text is more than 100 characters. This ensures the test for already processed obituaries works as expected.')

    @patch('requests.get')
    def test_read_obituaries(self, mock_get):
        """Test reading all obituaries."""
        reader = ObituaryReader(self.input_file.name, self.output_file.name)
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <body>
                John Smith passed away on January 15, 2020 at the age of 75.
                He was born on January 15, 1945.
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Process all obituaries
        reader.read_obituaries()
        
        # Check output file
        with open(self.output_file.name, 'r') as f:
            output_data = json.load(f)
            
        self.assertEqual(len(output_data), 2)
        self.assertIsNotNone(output_data[0]['obituary_text'])
        self.assertEqual(output_data[0]['death_date'], '15 Jan 2020')
        self.assertEqual(output_data[0]['birth_date'], '15 Jan 1945')
        self.assertEqual(output_data[1]['obituary_text'], 'This is a valid obituary text. It is long enough to pass the validation. The word obituary is present and the text is more than 100 characters. This ensures the test for already processed obituaries works as expected.')

if __name__ == '__main__':
    unittest.main() 
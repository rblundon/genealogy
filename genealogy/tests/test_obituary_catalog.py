"""
Tests for the ObituaryCatalog class.
"""

import unittest
import tempfile
import os
import json
from datetime import datetime
from genealogy.core.obituary_catalog import ObituaryCatalog

class TestObituaryCatalog(unittest.TestCase):
    def setUp(self):
        """Set up test cases."""
        self.catalog = ObituaryCatalog()
        
        # Sample people data
        self.people = [
            {
                'id': '1',
                'name': 'John Smith',
                'death_date': '15 Jan 2020',
                'last_processed': '2020-01-15 10:00:00'
            },
            {
                'id': '2',
                'name': 'Mary Smith',
                'death_date': '20 Jan 2020',
                'last_processed': '2020-01-20 10:00:00'
            },
            {
                'id': '3',
                'name': 'James Smith',
                'death_date': None,
                'last_processed': '2020-01-25 10:00:00'
            }
        ]

    def test_add_people(self):
        """Test adding people to the catalog."""
        self.catalog.add_people(self.people)
        self.assertEqual(len(self.catalog.people), 3)

    def test_sort_by_death_date_oldest_first(self):
        """Test sorting by death date (oldest first)."""
        self.catalog.add_people(self.people)
        sorted_people = self.catalog.sort_by_death_date(oldest_first=True)
        
        # Check order
        self.assertEqual(sorted_people[0]['name'], 'John Smith')
        self.assertEqual(sorted_people[1]['name'], 'Mary Smith')
        self.assertEqual(sorted_people[2]['name'], 'James Smith')

    def test_sort_by_death_date_newest_first(self):
        """Test sorting by death date (newest first)."""
        self.catalog.add_people(self.people)
        sorted_people = self.catalog.sort_by_death_date(oldest_first=False)
        
        # Check order
        self.assertEqual(sorted_people[0]['name'], 'Mary Smith')
        self.assertEqual(sorted_people[1]['name'], 'John Smith')
        self.assertEqual(sorted_people[2]['name'], 'James Smith')

    def test_get_unprocessed_obituaries(self):
        """Test getting unprocessed obituaries."""
        self.catalog.add_people(self.people)
        
        # Test with date before all processing
        date = datetime.strptime('2020-01-10 00:00:00', '%Y-%m-%d %H:%M:%S')
        unprocessed = self.catalog.get_unprocessed_obituaries(date)
        self.assertEqual(len(unprocessed), 3)
        
        # Test with date after some processing
        date = datetime.strptime('2020-01-16 00:00:00', '%Y-%m-%d %H:%M:%S')
        unprocessed = self.catalog.get_unprocessed_obituaries(date)
        self.assertEqual(len(unprocessed), 2)
        
        # Test with date after all processing
        date = datetime.strptime('2020-01-26 00:00:00', '%Y-%m-%d %H:%M:%S')
        unprocessed = self.catalog.get_unprocessed_obituaries(date)
        self.assertEqual(len(unprocessed), 0)

    def test_mark_as_processed(self):
        """Test marking an obituary as processed."""
        self.catalog.add_people(self.people)
        self.catalog.mark_as_processed('1')
        
        # Check that the timestamp was updated
        person = next(p for p in self.catalog.people if p['id'] == '1')
        self.assertIsNotNone(person['last_processed'])
        self.assertNotEqual(person['last_processed'], '2020-01-15 10:00:00')

    def test_save_and_load_catalog(self):
        """Test saving and loading the catalog."""
        # Add people and save
        self.catalog.add_people(self.people)
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            self.catalog.save_catalog(temp.name)
            
            # Load catalog
            loaded_catalog = ObituaryCatalog.load_catalog(temp.name)
            
            # Check that data was preserved
            self.assertEqual(len(loaded_catalog.people), 3)
            self.assertEqual(loaded_catalog.people[0]['name'], 'John Smith')
            self.assertEqual(loaded_catalog.people[1]['name'], 'Mary Smith')
            self.assertEqual(loaded_catalog.people[2]['name'], 'James Smith')
            
        # Clean up
        os.unlink(temp.name)

if __name__ == '__main__':
    unittest.main() 
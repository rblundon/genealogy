import unittest
from datetime import datetime
import json
import os
from obituary_catalog import ObituaryCatalog

class TestObituaryCatalog(unittest.TestCase):
    def setUp(self):
        """Set up test data before each test."""
        self.catalog = ObituaryCatalog()
        self.test_people = [
            {
                'id': 'P001',
                'name': 'John Smith',
                'death_date': '15 Jan 2020',
                'birth_date': '01 Jan 1940'
            },
            {
                'id': 'P002',
                'name': 'Jane Doe',
                'death_date': '20 Mar 2023',
                'birth_date': '15 Mar 1950'
            },
            {
                'id': 'P003',
                'name': 'Bob Wilson',
                'death_date': '10 Dec 2019',
                'birth_date': '05 Dec 1935'
            },
            {
                'id': 'P004',
                'name': 'Alice Brown',
                'death_date': None,
                'birth_date': '20 Feb 1960'
            }
        ]
        self.catalog.add_people(self.test_people)
        self.test_catalog_file = 'test_catalog.json'

    def tearDown(self):
        """Clean up after each test."""
        if os.path.exists(self.test_catalog_file):
            os.remove(self.test_catalog_file)

    def test_add_people(self):
        """Test adding people to the catalog."""
        self.assertEqual(len(self.catalog.people), 4)
        self.assertEqual(self.catalog.people[0]['id'], 'P001')
        self.assertEqual(self.catalog.people[1]['name'], 'Jane Doe')

    def test_get_death_date(self):
        """Test death date extraction and parsing."""
        # Test valid date
        date = self.catalog.get_death_date(self.test_people[0])
        self.assertEqual(date, datetime(2020, 1, 15))

        # Test missing date
        date = self.catalog.get_death_date(self.test_people[3])
        self.assertEqual(date, datetime.max)

        # Test invalid date format
        invalid_person = {'death_date': 'invalid-date'}
        date = self.catalog.get_death_date(invalid_person)
        self.assertEqual(date, datetime.max)

    def test_sort_by_death_date(self):
        """Test sorting by death date."""
        # Test oldest first (default)
        sorted_people = self.catalog.sort_by_death_date(oldest_first=True)
        self.assertEqual(sorted_people[0]['id'], 'P003')  # Dec 2019
        self.assertEqual(sorted_people[1]['id'], 'P001')  # Jan 2020
        self.assertEqual(sorted_people[2]['id'], 'P002')  # Mar 2023
        self.assertEqual(sorted_people[3]['id'], 'P004')  # No date

        # Test newest first
        sorted_people = self.catalog.sort_by_death_date(oldest_first=False)
        self.assertEqual(sorted_people[0]['id'], 'P002')  # Mar 2023
        self.assertEqual(sorted_people[1]['id'], 'P001')  # Jan 2020
        self.assertEqual(sorted_people[2]['id'], 'P003')  # Dec 2019
        self.assertEqual(sorted_people[3]['id'], 'P004')  # No date

    def test_get_unprocessed_obituaries(self):
        """Test getting unprocessed obituaries."""
        # Test with no last_processed_date
        unprocessed = self.catalog.get_unprocessed_obituaries()
        self.assertEqual(len(unprocessed), 4)

        # Test with last_processed_date
        last_date = datetime(2020, 1, 1)
        self.catalog.last_processed_date = last_date
        unprocessed = self.catalog.get_unprocessed_obituaries(last_date)
        self.assertEqual(len(unprocessed), 4)  # All should be unprocessed

        # Mark some as processed
        self.catalog.mark_as_processed('P001')
        self.catalog.mark_as_processed('P002')
        unprocessed = self.catalog.get_unprocessed_obituaries(last_date)
        self.assertEqual(len(unprocessed), 2)  # Only P003 and P004 should be unprocessed

    def test_mark_as_processed(self):
        """Test marking obituaries as processed."""
        self.catalog.mark_as_processed('P001')
        processed_person = next(p for p in self.catalog.people if p['id'] == 'P001')
        self.assertIn('last_processed', processed_person)
        
        # Verify timestamp format
        try:
            datetime.strptime(processed_person['last_processed'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            self.fail("last_processed timestamp is not in the correct format")

    def test_save_and_load_catalog(self):
        """Test saving and loading the catalog."""
        # Save catalog
        self.catalog.save_catalog(self.test_catalog_file)
        self.assertTrue(os.path.exists(self.test_catalog_file))

        # Load catalog
        loaded_catalog = ObituaryCatalog.load_catalog(self.test_catalog_file)
        self.assertEqual(len(loaded_catalog.people), 4)
        self.assertEqual(loaded_catalog.people[0]['id'], 'P001')
        self.assertEqual(loaded_catalog.people[1]['name'], 'Jane Doe')

    def test_catalog_persistence(self):
        """Test that catalog data persists correctly."""
        # Add some processing timestamps
        self.catalog.mark_as_processed('P001')
        self.catalog.mark_as_processed('P002')
        
        # Save and reload
        self.catalog.save_catalog(self.test_catalog_file)
        loaded_catalog = ObituaryCatalog.load_catalog(self.test_catalog_file)
        
        # Verify processing timestamps were preserved
        p001 = next(p for p in loaded_catalog.people if p['id'] == 'P001')
        p002 = next(p for p in loaded_catalog.people if p['id'] == 'P002')
        self.assertIn('last_processed', p001)
        self.assertIn('last_processed', p002)
        self.assertNotIn('last_processed', loaded_catalog.people[2])  # P003
        self.assertNotIn('last_processed', loaded_catalog.people[3])  # P004

if __name__ == '__main__':
    unittest.main() 
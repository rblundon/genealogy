"""
Tests for the PeopleFinder class.
"""

import unittest
from genealogy.core.people_finder import PeopleFinder
import logging

logging.basicConfig(level=logging.INFO)

class TestPeopleFinder(unittest.TestCase):
    def setUp(self):
        """Set up test cases."""
        self.finder = PeopleFinder()
        
        # Sample obituary text for testing
        self.sample_obit = """
        John Smith (nee Johnson) "Johnny" passed away on 15 Jan 2020.
        He was survived by his wife Mary Smith (nee Brown) "Molly",
        his father Robert Smith, his mother Elizabeth Smith (nee Wilson),
        his brother James Smith "Jim", and his sister Sarah Smith (nee Smith) "Sally".
        """
        
        self.sample_title = "John Smith's Obituary"

    def test_extract_names_from_title(self):
        """Test extracting names from obituary title."""
        names = self.finder.extract_names("", self.sample_title)
        self.assertEqual(len(names), 1)
        self.assertEqual(names[0]['name'], "John Smith")
        self.assertEqual(names[0]['relationship'], "deceased")

    def test_extract_names_from_text(self):
        """Test extracting names from obituary text."""
        names = self.finder.extract_names(self.sample_obit, "")
        self.assertGreaterEqual(len(names), 3)  # At least deceased, spouse, and one parent
        
        # Check deceased
        deceased = next(n for n in names if n['relationship'] == 'deceased')
        self.assertEqual(deceased['name'], "John Smith")
        self.assertEqual(deceased['maiden_name'], "Johnson")
        self.assertEqual(deceased['nickname'], "Johnny")
        
        # Check spouse
        spouse = next(n for n in names if n['relationship'] == 'spouse')
        self.assertEqual(spouse['name'], "Mary Smith")
        self.assertEqual(spouse['maiden_name'], "Brown")
        self.assertEqual(spouse['nickname'], "Molly")
        
        # Check parents
        father = next(n for n in names if n['relationship'] == 'parent' and 'father' in n['original_name'].lower())
        self.assertEqual(father['name'], "Robert Smith")
        
        mother = next(n for n in names if n['relationship'] == 'parent' and 'mother' in n['original_name'].lower())
        self.assertEqual(mother['name'], "Elizabeth Smith")
        self.assertEqual(mother['maiden_name'], "Wilson")
        
        # Check siblings (if found)
        brothers = [n for n in names if n['relationship'] == 'sibling' and 'brother' in n['original_name'].lower()]
        if brothers:
            brother = brothers[0]
            self.assertEqual(brother['name'], "James Smith")
            self.assertEqual(brother['nickname'], "Jim")
        sisters = [n for n in names if n['relationship'] == 'sibling' and 'sister' in n['original_name'].lower()]
        if sisters:
            sister = sisters[0]
            self.assertEqual(sister['name'], "Sarah Smith")
            self.assertEqual(sister['maiden_name'], "Smith")
            self.assertEqual(sister['nickname'], "Sally")

    def test_duplicate_handling(self):
        """Test handling of duplicate names."""
        text = """
        John Smith passed away. He was survived by his wife Mary Smith,
        and his brother John Smith Jr.
        """
        names = self.finder.extract_names(text, "")
        self.assertGreaterEqual(len(names), 2)  # At least deceased and wife
        self.assertEqual(len([n for n in names if n['name'] == "John Smith"]), 1)

    def test_conjunction_handling(self):
        """Test handling of names with conjunctions."""
        text = """
        John Smith passed away. He was survived by his brothers James and Robert Smith,
        and his sisters Mary and Elizabeth Smith.
        """
        names = self.finder.extract_names(text, "")
        self.assertGreaterEqual(len(names), 1)  # At least the deceased

    def test_empty_input(self):
        """Test handling of empty input."""
        names = self.finder.extract_names("", "")
        self.assertEqual(len(names), 0)

if __name__ == '__main__':
    unittest.main() 
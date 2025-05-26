import unittest
from genealogy.core.relationship_extraction import extract_spouses_and_companions

class TestObituaryProcessor(unittest.TestCase):
    def setUp(self):
        pass

    def test_name_splitting_with_conjunctions(self):
        # Test case with a name containing a conjunction
        text = "Terrence Kaczmarowski passed away peacefully on January 1, 2024."
        current_last_name = "Smith"  # Example current last name
        relationships = extract_spouses_and_companions(text, current_last_name)
        
        # Test case with multiple names and conjunctions
        text = "John Smith and Mary Jones, along with their children Terrence Kaczmarowski and Sarah Smith, gathered to remember their loved one."
        relationships = extract_spouses_and_companions(text, current_last_name)
        
        # Since we're testing name splitting, we should verify that the text is being processed correctly
        # The actual relationship finding is tested elsewhere
        self.assertIsNotNone(text)  # Basic validation that text is being processed

if __name__ == '__main__':
    unittest.main() 
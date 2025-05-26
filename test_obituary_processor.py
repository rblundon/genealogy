import unittest
from genealogy.core.relationship_extraction import extract_spouses_and_companions
from genealogy.core.name_extractor import NameExtractor

class TestObituaryProcessor(unittest.TestCase):
    def setUp(self):
        self.name_extractor = NameExtractor()

    def test_reunited_with_husband(self):
        # Test case from Maxine Kaczmarowski's obituary
        text = "Reunited with her husband Terrence and daughter Patricia on May 24, 2018 at the age of 87 years."
        current_last_name = "Kaczmarowski"
        
        relationships = extract_spouses_and_companions(text, current_last_name)
        spouse_name = None
        for name, rel, _ in relationships:
            if rel == 'spouse':
                spouse_name = name
                break
        
        # Verify that Terrence Kaczmarowski is correctly identified as the spouse
        self.assertEqual(spouse_name, "Terrence Kaczmarowski")

    def test_name_cleaning(self):
        # Test the name cleaning functionality
        test_cases = [
            ("Terrence and", "Terrence"),  # Should remove trailing 'and'
            ("Terrence (Terry) Kaczmarowski", "Terrence Kaczmarowski"),  # Should preserve last name
            ("Mr. Terrence Kaczmarowski", "Terrence Kaczmarowski"),  # Should remove title
            ("Terrence Kaczmarowski (nee Smith)", "Terrence Kaczmarowski (nee Smith)"),  # Should preserve maiden name
        ]
        
        for input_name, expected_output in test_cases:
            cleaned_name = self.name_extractor.clean_name(input_name)
            self.assertEqual(cleaned_name, expected_output)

if __name__ == '__main__':
    unittest.main() 
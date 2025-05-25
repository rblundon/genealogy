import unittest
from patterns import (
    DEATH_PATTERNS, BIRTH_PATTERNS, AGE_PATTERNS,
    NAME_PATTERNS, RELATIONSHIP_PATTERNS
)
from common_classes import DateNormalizer
import re

class TestPatterns(unittest.TestCase):
    def setUp(self):
        self.date_normalizer = DateNormalizer()

    def test_death_patterns(self):
        test_cases = [
            "passed away unexpectedly while mowing grass on May 24, 2018",
            "passed away on January 1st, 2020",
            "died on March 15, 2019",
            "passed on December 31, 2021",
            "May 24, 2018 at the age of 87",
            "January 1, 2020, age 65",
            "March 15, 2019"
        ]
        
        for text in test_cases:
            death_date = self.date_normalizer.find_death_date(text)
            self.assertIsNotNone(death_date, f"Failed to extract death date from: {text}")
            self.assertTrue(re.match(r'\d{2} \w{3} \d{4}', death_date), 
                          f"Invalid date format: {death_date}")

    def test_birth_patterns(self):
        test_cases = [
            "born on May 24, 1950",
            "born January 1st, 1955",
            "birth date: March 15, 1960",
            "born in 1965"
        ]
        
        for text in test_cases:
            birth_date = self.date_normalizer.find_birth_date(text)
            self.assertIsNotNone(birth_date, f"Failed to extract birth date from: {text}")
            if "born in" not in text.lower():
                self.assertTrue(re.match(r'\d{2} \w{3} \d{4}', birth_date),
                              f"Invalid date format: {birth_date}")
            else:
                self.assertTrue(re.match(r'01 Jan \d{4}', birth_date),
                              f"Invalid year-only format: {birth_date}")

    def test_age_patterns(self):
        test_cases = [
            "age 87 years",
            "aged 65",
            "87 years old",
            "age 90"
        ]
        
        for text in test_cases:
            age = self.date_normalizer.find_age(text)
            self.assertIsNotNone(age, f"Failed to extract age from: {text}")
            self.assertIsInstance(age, int, f"Age should be an integer, got: {type(age)}")
            self.assertTrue(0 < age < 120, f"Age {age} seems unreasonable")

    def test_name_patterns(self):
        test_cases = {
            'title': "John Smith Obituary",
            'location': "- New York - Smith Funeral Home",
            'maiden_name': "née Johnson",
            'nickname': 'known as "Johnny"'
        }
        
        for pattern_type, text in test_cases.items():
            pattern = NAME_PATTERNS[pattern_type]
            match = re.search(pattern, text)
            self.assertIsNotNone(match, f"Failed to match {pattern_type} pattern: {text}")

    def test_relationship_patterns(self):
        test_cases = {
            'spouse': [
                "married to Jane Smith",
                "spouse John Smith",
                "married Mary Johnson"
            ],
            'parent': [
                "son of Robert Smith",
                "father was William Johnson"
            ],
            'sibling': [
                "brother James Smith",
                "siblings include Sarah and Michael"
            ],
            'child': [
                "children include John and Mary",
                "son Robert Smith"
            ]
        }
        
        for rel_type, texts in test_cases.items():
            patterns = RELATIONSHIP_PATTERNS[rel_type]
            for text in texts:
                matched = False
                for pattern in patterns:
                    if re.search(pattern, text):
                        matched = True
                        break
                self.assertTrue(matched, f"Failed to match {rel_type} pattern: {text}")

    def test_date_calculation(self):
        test_cases = [
            ("24 May 2018", 87, "01 Jan 1931"),
            ("01 Jan 2020", 65, "01 Jan 1955"),
            ("15 Mar 2019", 90, "01 Jan 1929")
        ]
        
        for death_date, age, expected_birth in test_cases:
            calculated_birth = self.date_normalizer.calculate_birth_date(death_date, age)
            self.assertEqual(calculated_birth, expected_birth,
                           f"Birth date calculation failed for death date {death_date} and age {age}")

if __name__ == '__main__':
    unittest.main() 
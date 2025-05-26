"""
Tests for the DateNormalizer class.
"""

import unittest
from datetime import datetime
from genealogy.core.date_normalizer import DateNormalizer

class TestDateNormalizer(unittest.TestCase):
    def test_parse_date(self):
        """Test date parsing with various formats."""
        test_cases = [
            ('15 Jan 2020', '15 Jan 2020'),
            ('January 15 2020', '15 Jan 2020'),
            ('2020-01-15', '15 Jan 2020'),
            ('01/15/2020', '15 Jan 2020'),
            ('15/01/2020', '15 Jan 2020'),
            ('2020', '01 Jan 2020'),
            ('15th Jan 2020', '15 Jan 2020'),
            ('January 15th 2020', '15 Jan 2020'),
            ('', None),
            ('invalid', None),
        ]
        
        for input_date, expected in test_cases:
            with self.subTest(input_date=input_date):
                result = DateNormalizer.parse_date(input_date)
                self.assertEqual(result, expected)

    def test_find_death_date(self):
        """Test finding death dates in text."""
        test_cases = [
            ('died on 15 Jan 2020', '15 Jan 2020'),
            ('passed away on January 15 2020', '15 Jan 2020'),
            ('passed on 15 Jan 2020', '15 Jan 2020'),
            ('death on 15 Jan 2020', '15 Jan 2020'),
            ('15 Jan 2020 - Death', '15 Jan 2020'),
            ('no death date here', None),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = DateNormalizer.find_death_date(text)
                self.assertEqual(result, expected)

    def test_find_birth_date(self):
        """Test finding birth dates in text."""
        test_cases = [
            ('born on 15 Jan 2020', '15 Jan 2020'),
            ('born January 15 2020', '15 Jan 2020'),
            ('birth date: 15 Jan 2020', '15 Jan 2020'),
            ('15 Jan 2020 - Birth', '15 Jan 2020'),
            ('no birth date here', None),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = DateNormalizer.find_birth_date(text)
                self.assertEqual(result, expected)

    def test_find_age(self):
        """Test finding age in text."""
        test_cases = [
            ('age 75', 75),
            ('aged 75', 75),
            ('75 years old', 75),
            ('75 years of age', 75),
            ('no age here', None),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = DateNormalizer.find_age(text)
                self.assertEqual(result, expected)

    def test_calculate_birth_date(self):
        """Test calculating birth date from death date and age."""
        test_cases = [
            ('15 Jan 2020', 75, '15 Jan 1945'),
            ('01 Jan 2020', 1, '01 Jan 2019'),
            ('invalid', 75, None),
            ('15 Jan 2020', 'invalid', None),
        ]
        
        for death_date, age, expected in test_cases:
            with self.subTest(death_date=death_date, age=age):
                result = DateNormalizer.calculate_birth_date(death_date, age)
                self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main() 
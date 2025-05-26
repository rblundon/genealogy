import unittest
from datetime import datetime
from genealogy.core.date_normalizer import DateNormalizer

class TestDateNormalizer(unittest.TestCase):
    def test_parse_date(self):
        """Test date parsing with various formats."""
        test_cases = [
            ("15 Jan 2020", "15 Jan 2020"),
            ("January 15, 2020", "15 Jan 2020"),
            ("Jan 15, 2020", "15 Jan 2020"),
            ("2020-01-15", "15 Jan 2020"),
            ("01/15/2020", "15 Jan 2020"),
            ("15/01/2020", "15 Jan 2020"),
            ("2020", "01 Jan 2020"),  # Year only
            ("15th Jan 2020", "15 Jan 2020"),  # With ordinal
            ("January 15th, 2020", "15 Jan 2020"),  # With ordinal and comma
        ]
        
        for input_date, expected in test_cases:
            with self.subTest(input_date=input_date):
                result = DateNormalizer.parse_date(input_date)
                self.assertEqual(result, expected)

    def test_extract_death_date_and_age(self):
        """Test extraction of death date and age from text."""
        test_cases = [
            (
                "Died on May 24, 2018 at the age of 87 years",
                "24 May 2018",
                87
            ),
            (
                "Passed away on January 15, 2020 at the age of 65 years",
                "15 Jan 2020",
                65
            ),
            (
                "Passed away unexpectedly while mowing grass on May 11th, 2025",
                "11 May 2025",
                None
            ),
            (
                "Died on March 15, 2023",
                "15 Mar 2023",
                None
            ),
            (
                "Passed on April 20, 2024",
                "20 Apr 2024",
                None
            ),
            (
                "May 1, 2023 at the age of 90",
                "01 May 2023",
                None
            ),
        ]
        
        for text, expected_date, expected_age in test_cases:
            with self.subTest(text=text):
                date, age = DateNormalizer.extract_death_date_and_age(text)
                self.assertEqual(date, expected_date)
                self.assertEqual(age, expected_age)

    def test_find_birth_date(self):
        """Test birth date extraction from text."""
        test_cases = [
            (
                "Born February 16th, 1941",
                "16 Feb 1941"
            ),
            (
                "Born on January 15, 2020",
                "15 Jan 2020"
            ),
            (
                "Birth date: March 1, 1990",
                "01 Mar 1990"
            ),
            (
                "Born in 1985",
                "01 Jan 1985"
            ),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = DateNormalizer.find_birth_date(text)
                self.assertEqual(result, expected)

    def test_calculate_age_from_dates(self):
        """Test age calculation from birth and death dates."""
        test_cases = [
            # (birth_date, death_date, expected_age)
            ("16 Feb 1941", "11 May 2025", 84),  # Birthday hasn't occurred
            ("16 Feb 1941", "16 Feb 2025", 84),  # Birthday on death date
            ("16 Feb 1941", "20 Feb 2025", 84),  # Birthday has occurred
            ("01 Jan 2000", "31 Dec 2024", 24),  # Year boundary
            ("31 Dec 2000", "01 Jan 2025", 24),  # Year boundary
        ]
        
        for birth_date, death_date, expected_age in test_cases:
            with self.subTest(birth_date=birth_date, death_date=death_date):
                result = DateNormalizer.calculate_age_from_dates(birth_date, death_date)
                self.assertEqual(result, expected_age)

    def test_find_age(self):
        """Test age extraction and calculation from text."""
        test_cases = [
            # Text with explicit age
            (
                "Died on May 24, 2018 at the age of 87 years",
                87
            ),
            # Text with birth and death dates
            (
                "Born February 16th, 1941. Passed away on May 11th, 2025",
                84
            ),
            # Text with age pattern
            (
                "Age 65 at time of death",
                65
            ),
            # Additional age patterns
            (
                "age 70 years",
                70
            ),
            (
                "age 75",
                75
            ),
            (
                "age of 80 years",
                80
            ),
            (
                "aged 85",
                85
            ),
            # Text with no age information
            (
                "Passed away peacefully",
                None
            ),
        ]
        
        for text, expected_age in test_cases:
            with self.subTest(text=text):
                result = DateNormalizer.find_age(text)
                self.assertEqual(result, expected_age)

    def test_calculate_birth_date(self):
        """Test birth date calculation from death date and age."""
        test_cases = [
            # (death_date, age, expected_year)
            ("24 May 2018", 87, "1931"),
            ("15 Jan 2020", 65, "1955"),
            ("11 May 2025", 84, "1941"),
        ]
        
        for death_date, age, expected_year in test_cases:
            with self.subTest(death_date=death_date, age=age):
                result = DateNormalizer.calculate_birth_date(death_date, age)
                self.assertEqual(result, expected_year)

    def test_normalize_existing_dates(self):
        """Test normalization of existing dates in people data."""
        input_data = [
            {
                "birth_date": "February 16th, 1941",
                "death_date": "May 11th, 2025"
            },
            {
                "birth_date": "01/15/2020",
                "death_date": "2020-01-15"
            }
        ]
        
        expected_data = [
            {
                "birth_date": "16 Feb 1941",
                "death_date": "11 May 2025"
            },
            {
                "birth_date": "15 Jan 2020",
                "death_date": "15 Jan 2020"
            }
        ]
        
        result = DateNormalizer.normalize_existing_dates(input_data)
        self.assertEqual(result, expected_data)

if __name__ == '__main__':
    unittest.main() 
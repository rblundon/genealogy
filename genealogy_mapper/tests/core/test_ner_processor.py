import pytest
from datetime import datetime
from genealogy_mapper.core.ner_processor import ObituaryNERProcessor, PersonInfo
import re

@pytest.fixture
def ner_processor():
    """Create an instance of ObituaryNERProcessor."""
    return ObituaryNERProcessor()

def test_format_date():
    """Test date formatting to standard format."""
    processor = ObituaryNERProcessor()
    
    # Test various date formats
    test_cases = [
        ("01/01/2020", "01 Jan 2020"),
        ("1-1-2020", "01 Jan 2020"),
        ("January 1, 2020", "01 Jan 2020"),
        ("Jan 1, 2020", "01 Jan 2020"),
        ("1 Jan 2020", "01 Jan 2020"),
        ("2020-01-01", "01 Jan 2020"),
    ]
    
    for input_date, expected in test_cases:
        assert processor._format_date(input_date) == expected

def test_extract_dates_simple():
    """Test extraction of dates from simple text."""
    processor = ObituaryNERProcessor()
    text = "John Smith (01 Jan 1920 - 01 Jan 2020)"
    doc = processor.nlp(text)
    birth_date, death_date = processor._extract_dates(doc)
    assert birth_date == "01 Jan 1920"
    assert death_date == "01 Jan 2020"

def test_extract_dates_with_born_died():
    """Test extraction of dates with 'born' and 'died' keywords."""
    processor = ObituaryNERProcessor()
    text = "John Smith was born on January 1, 1920 and died on January 1, 2020."
    doc = processor.nlp(text)
    birth_date, death_date = processor._extract_dates(doc)
    assert birth_date == "01 Jan 1920"
    assert death_date == "01 Jan 2020"

def test_extract_dates_with_slashes():
    """Test extraction of dates with slash format."""
    processor = ObituaryNERProcessor()
    text = "John Smith (01/01/1920 - 01/01/2020)"
    doc = processor.nlp(text)
    birth_date, death_date = processor._extract_dates(doc)
    assert birth_date == "01 Jan 1920"
    assert death_date == "01 Jan 2020"

def test_extract_dates_with_dashes():
    """Test extraction of dates with dash format."""
    processor = ObituaryNERProcessor()
    text = "John Smith (01-01-1920 - 01-01-2020)"
    doc = processor.nlp(text)
    birth_date, death_date = processor._extract_dates(doc)
    assert birth_date == "01 Jan 1920"  # First date is birth date
    assert death_date == "01 Jan 2020"  # Second date is death date

def test_extract_dates_from_ner():
    """Test extraction of dates using NER when pattern matching fails."""
    processor = ObituaryNERProcessor()
    text = "John Smith was born in 1920 and passed away in 2020."
    doc = processor.nlp(text)
    birth_date, death_date = processor._extract_dates(doc)
    # Note: This test might be flaky as it depends on spaCy's NER model
    # We're just checking that we get some dates, not specific values
    assert birth_date is not None
    assert death_date is not None

def test_extract_person_info_with_dates():
    """Test extraction of person information including dates."""
    processor = ObituaryNERProcessor()
    text = """
    John Smith was born on January 1, 1920 in New York City.
    He passed away on January 1, 2020 in Boston.
    He was a professor at Harvard University.
    """
    person_info = processor.extract_person_info(text)
    assert person_info.full_name == "John Smith"
    assert person_info.birth_date == "01 Jan 1920"
    assert person_info.death_date == "01 Jan 2020"
    assert "Harvard University" in person_info.organizations

def test_extract_person_info_basic(ner_processor):
    """Test basic person information extraction."""
    text = """
    John Smith, 85, of Springfield, passed away on January 15, 2024.
    He was born on March 20, 1938, in Chicago, Illinois.
    John was a retired teacher and a veteran of the U.S. Army.
    He graduated from Springfield High School and earned his degree from the University of Illinois.
    """
    person_info = ner_processor.extract_person_info(text)
    assert person_info.full_name == "John Smith"
    # Check that dates are present and in the correct format
    assert person_info.birth_date is not None
    assert person_info.death_date is not None
    assert re.match(r'\d{2} [A-Za-z]{3} \d{4}', person_info.birth_date)
    assert re.match(r'\d{2} [A-Za-z]{3} \d{4}', person_info.death_date)
    # Normalize whitespace for comparison
    expected_text = ' '.join(text.strip().split())
    assert person_info.raw_text == expected_text

def test_extract_person_info_complex(ner_processor):
    """Test extraction of more complex person information."""
    text = """
    Mary Jane Wilson, 92, of Boston, Massachusetts, died peacefully on February 1, 2024.
    Born in New York City on May 10, 1931, she was the daughter of James and Elizabeth Wilson.
    Mary was a distinguished professor at Harvard University and a member of the American Medical Association.
    She served in the U.S. Navy during the Korean War and later earned her Ph.D. from MIT.
    """
    
    person_info = ner_processor.extract_person_info(text)
    
    assert isinstance(person_info, PersonInfo)
    assert person_info.full_name == "Mary Jane Wilson"
    assert "Harvard University" in person_info.organizations
    assert "American Medical Association" in person_info.organizations
    assert "MIT" in person_info.organizations

def test_extract_person_info_minimal(ner_processor):
    """Test extraction with minimal information."""
    text = "John Doe passed away."
    
    person_info = ner_processor.extract_person_info(text)
    
    assert isinstance(person_info, PersonInfo)
    assert person_info.full_name == "John Doe"
    assert person_info.organizations == [] 
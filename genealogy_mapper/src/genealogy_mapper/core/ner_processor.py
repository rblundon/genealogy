import spacy
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from dateutil import parser
import re
from .patterns import (
    NAME_PATTERNS,
    GENDER_PATTERNS,
    AGE_PATTERNS,
    DEATH_DATE_PATTERNS,
    DATE_RANGE_PATTERNS,
    ADDRESS_PATTERNS,
    SERVICE_PATTERNS,
    ADDRESS_DATE_PATTERNS,
)

logger = logging.getLogger(__name__)

@dataclass
class PersonInfo:
    """Data class to store extracted person information."""
    full_name: Optional[str] = None
    maiden_name: Optional[str] = None  # Added field for maiden name
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    birth_place: Optional[str] = None
    death_place: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    education: Optional[List[str]] = None
    military_service: Optional[List[str]] = None
    organizations: Optional[List[str]] = None
    raw_text: Optional[str] = None

class BaseNERProcessor:
    """Base class for NER processing."""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize the NER processor.
        
        Args:
            model_name: Name of the spaCy model to use.
        """
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            logger.warning(f"Model {model_name} not found. Downloading...")
            spacy.cli.download(model_name)
            self.nlp = spacy.load(model_name)

class ObituaryNERProcessor(BaseNERProcessor):
    """NER processor specifically for obituaries."""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize the obituary NER processor.
        
        Args:
            model_name: Name of the spaCy model to use. Defaults to "en_core_web_sm".
        """
        super().__init__(model_name)
        
    def _format_date(self, date_str: str) -> Optional[str]:
        """Format a date string to the standard format '01 Jun 2025'.
        
        Args:
            date_str: The date string to format.
            
        Returns:
            Formatted date string or None if parsing fails.
        """
        try:
            # Try to parse the date
            parsed_date = parser.parse(date_str, fuzzy=True)
            # Format as "01 Jun 2025"
            return parsed_date.strftime("%d %b %Y")
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
            return None

    def _extract_name_and_gender(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract full name, maiden name, and gender from text."""
        full_name = None
        maiden_name = None
        gender = None
        
        # First try to find a name using spaCy's NER
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                full_name = ent.text.strip()
                break
        
        # If NER didn't find a name, try regex patterns
        if not full_name:
            for pattern in NAME_PATTERNS:
                match = re.search(pattern, text)
                if match:
                    if len(match.groups()) == 3:  # First two patterns (with maiden name)
                        if pattern.startswith(r'([A-Za-z]+),'):  # First pattern
                            last_name, first_name, maiden = match.groups()
                            full_name = f"{first_name.strip()} {last_name}"
                        else:  # Second pattern
                            first_name, last_name, maiden = match.groups()
                            full_name = f"{first_name.strip()} {last_name}"
                        maiden_name = maiden
                    else:  # Last two patterns (without maiden name)
                        if pattern.startswith(r'([A-Za-z]+),'):  # Third pattern
                            last_name, first_name = match.groups()
                            full_name = f"{first_name.strip()} {last_name}"
                        else:  # Fourth pattern
                            first_name, last_name = match.groups()
                            full_name = f"{first_name.strip()} {last_name}"
                    break
        
        # If still no name found, try to extract from the first sentence
        if not full_name:
            first_sentence = text.split('.')[0].strip()
            words = first_sentence.split()
            if len(words) >= 2:
                # Try to find a name-like pattern (two capitalized words)
                for i in range(len(words) - 1):
                    if words[i][0].isupper() and words[i+1][0].isupper():
                        full_name = f"{words[i]} {words[i+1]}"
                        break
        
        # Determine gender based on patterns
        for gender_type, patterns in GENDER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    gender = gender_type
                    break
            if gender:
                break
        
        return full_name, maiden_name, gender

    def _extract_age(self, text: str) -> Optional[int]:
        """Extract age from text."""
        for pattern in AGE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None

    def _extract_dates(self, doc) -> Tuple[Optional[str], Optional[str]]:
        """Extract birth and death dates from text."""
        birth_date = None
        death_date = None
        text = doc.text
        
        # First try to match date range patterns
        for pattern, num_dates, _ in DATE_RANGE_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                if num_dates == 2:
                    birth_date = self._format_date(match.group(1))
                    death_date = self._format_date(match.group(2))
                    if birth_date and death_date:
                        return birth_date, death_date
                elif num_dates == 1:
                    date = self._format_date(match.group(1))
                    if date:
                        # If we only have one date, assume it's the death date
                        death_date = date
        
        # If no date range found, try to find birth and death dates separately
        # Look for "born on" or "born in" patterns
        born_patterns = [
            r'born\s+on\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})',
            r'born\s+on\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})',
            r'born\s+in\s+(\d{4})',
            r'born\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})',
            r'born\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})'
        ]
        
        for pattern in born_patterns:
            match = re.search(pattern, text)
            if match:
                birth_date = self._format_date(match.group(1))
                if birth_date:
                    break
        
        # Look for death date patterns
        for pattern, _, _ in DEATH_DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                death_date = self._format_date(match.group(1))
                if death_date:
                    break
        
        # If we still don't have dates, try using NER
        if not birth_date or not death_date:
            dates = []
            for ent in doc.ents:
                if ent.label_ == "DATE":
                    date = self._format_date(ent.text)
                    if date:
                        dates.append(date)
            
            if dates:
                # Sort dates chronologically
                dates.sort(key=lambda x: parser.parse(x, fuzzy=True))
                if not birth_date and len(dates) > 0:
                    birth_date = dates[0]
                if not death_date and len(dates) > 1:
                    death_date = dates[-1]
        
        return birth_date, death_date
    
    def _is_address_date(self, date_text: str, full_text: str, date_position: int) -> bool:
        """Check if a date is part of an address."""
        # Look for address indicators near the date
        context_start = max(0, date_position - 50)
        context_end = min(len(full_text), date_position + len(date_text) + 50)
        context = full_text[context_start:context_end]
        
        for pattern in ADDRESS_PATTERNS:
            if re.search(pattern, context, re.IGNORECASE):
                return True
        
        # Check if the date is a 4-digit year that's part of an address
        if re.match(r'^\d{4}$', date_text):
            for pattern in ADDRESS_DATE_PATTERNS:
                if re.search(pattern, context, re.IGNORECASE):
                    return True
        
        return False

    def _is_visitation_date(self, date_text: str, full_text: str, date_position: int) -> bool:
        """Check if a date is part of a visitation or funeral service."""
        # Look for service indicators near the date
        context_start = max(0, date_position - 50)
        context_end = min(len(full_text), date_position + len(date_text) + 50)
        context = full_text[context_start:context_end]
        
        for pattern in SERVICE_PATTERNS:
            if re.search(pattern, context, re.IGNORECASE):
                return True
        
        return False

    def _calculate_birth_year(self, death_date: str, age: int) -> Optional[str]:
        """Calculate birth year from death date and age."""
        try:
            # Parse the death date
            death_dt = datetime.strptime(death_date, "%d %b %Y")
            # Calculate birth year
            birth_year = death_dt.year - age
            return str(birth_year)
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to calculate birth year: {e}")
            return None

    def extract_person_info(self, text: str) -> PersonInfo:
        """Extract person information from obituary text."""
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract basic information
        full_name, maiden_name, gender = self._extract_name_and_gender(text)
        age = self._extract_age(text)
        birth_date, death_date = self._extract_dates(doc)
        
        # Calculate birth year if we have death date and age but no birth date
        if not birth_date and death_date and age:
            try:
                death_year = int(death_date.split()[-1])
                birth_year = death_year - age
                birth_date = f"01 Jan {birth_year}"
            except (ValueError, IndexError):
                pass
        
        # Extract organizations, education, and military service
        organizations = []
        education = []
        military_service = []
        
        # Look for education institutions
        education_terms = ['university', 'college', 'school', 'institute', 'academy']
        for sent in doc.sents:
            sent_text = sent.text.lower()
            if any(term in sent_text for term in education_terms):
                # Extract the institution name
                for ent in sent.ents:
                    if ent.label_ in ['ORG', 'GPE']:
                        org_name = ent.text.strip()
                        if org_name:
                            education.append(org_name)
                            organizations.append(org_name)
        
        # Look for military service
        military_terms = ['army', 'navy', 'air force', 'marines', 'coast guard', 'military']
        for sent in doc.sents:
            sent_text = sent.text.lower()
            if any(term in sent_text for term in military_terms):
                # Extract the military branch
                for ent in sent.ents:
                    if ent.label_ in ['ORG', 'GPE']:
                        branch = ent.text.strip()
                        if branch:
                            military_service.append(branch)
        
        # Look for other organizations
        for sent in doc.sents:
            for ent in sent.ents:
                if ent.label_ == 'ORG':
                    org_name = ent.text.strip()
                    if org_name and org_name not in organizations:
                        organizations.append(org_name)
        
        # Normalize organization names
        organizations = [self._normalize_org_name(org) for org in organizations]
        education = [self._normalize_org_name(edu) for edu in education]
        
        return PersonInfo(
            full_name=full_name,
            maiden_name=maiden_name,
            birth_date=birth_date,
            death_date=death_date,
            birth_place=None,  # TODO: Implement birth place extraction
            death_place=None,  # TODO: Implement death place extraction
            age=age,
            gender=gender,
            occupation=None,  # TODO: Implement occupation extraction
            education=education,
            military_service=military_service,
            organizations=organizations,
            raw_text=text
        )
    
    def _normalize_org_name(self, name: str) -> str:
        """Normalize organization name by removing common prefixes and suffixes."""
        # Remove common prefixes
        prefixes = ['the', 'a', 'an']
        for prefix in prefixes:
            if name.lower().startswith(f"{prefix} "):
                name = name[len(prefix) + 1:]
        
        # Remove trailing punctuation
        name = name.rstrip('.,;:')
        
        return name.strip() 
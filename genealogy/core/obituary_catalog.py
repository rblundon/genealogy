"""
ObituaryCatalog: A module for cataloging and sorting obituaries by death date.

This module provides a class to manage a list of obituary records, sort them by death date,
track processing status, and persist the catalog to a file.
"""

from datetime import datetime
import logging
from typing import List, Dict, Any, Optional
import json
import os
import tempfile

logger = logging.getLogger(__name__)

class ObituaryCatalog:
    def __init__(self):
        self.people: List[Dict[str, Any]] = []
        self.last_processed_date: Optional[datetime] = None
        self.catalog = {}

    def add_people(self, people: List[Dict[str, Any]]):
        """Add people to the catalog."""
        self.people.extend(people)

    def get_death_date_key(self, person: Dict[str, Any]) -> tuple:
        """Return a tuple for sorting: (has_death_date, date or min/max)."""
        if '_parsed_death_date' in person:
            return person['_parsed_death_date']
        death_date = person.get('death_date')
        if not death_date:
            key = (1, datetime.max)  # 1 means missing, always last
        else:
            try:
                key = (0, datetime.strptime(death_date, '%d %b %Y'))  # 0 means present
            except ValueError:
                key = (1, datetime.max)
        person['_parsed_death_date'] = key
        return key

    def sort_by_death_date(self, oldest_first: bool = True) -> List[Dict[str, Any]]:
        """Sort people by death date, always putting missing dates last."""
        logger.info("Sorting people by death date...")
        sorted_people = sorted(self.people, key=self.get_death_date_key)
        if not oldest_first:
            # For newest first, reverse the list (missing dates still last)
            with_dates = [p for p in sorted_people if p.get('death_date')]
            without_dates = [p for p in sorted_people if not p.get('death_date')]
            sorted_people = list(reversed(with_dates)) + without_dates
        # Log the order
        logger.info("\nProcessing order by death date:")
        for i, person in enumerate(sorted_people, 1):
            death_date = person.get('death_date', 'No death date')
            name = person.get('name', 'Unknown')
            logger.info(f"{i}. {name} - {death_date}")
        return sorted_people

    def get_unprocessed_obituaries(self, last_processed_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get obituaries that haven't been processed since the given date."""
        if last_processed_date is None:
            return self.people
        return [
            person for person in self.people
            if not person.get('last_processed') or 
            datetime.strptime(person['last_processed'], '%Y-%m-%d %H:%M:%S') < last_processed_date
        ]

    def mark_as_processed(self, person_id: str):
        """Mark an obituary as processed with current timestamp."""
        for person in self.people:
            if person.get('id') == person_id:
                person['last_processed'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                break

    def update_catalog(self, people: List[Dict[str, Any]]) -> None:
        """Update the catalog with new people data."""
        for person in people:
            if person.get('id') and person.get('name'):
                self.catalog[person['id']] = {
                    'name': person['name'],
                    'url': person.get('url'),
                    'death_date': person.get('death_date'),
                    'location': person.get('location')
                }

    def save_catalog(self, filename: str):
        """Save the catalog to a file using atomic write."""
        data = {
            'people': self.people,
            'last_processed_date': self.last_processed_date.strftime('%Y-%m-%d %H:%M:%S') if self.last_processed_date else None
        }
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
                json.dump(data, temp, indent=2)
            os.replace(temp.name, filename)
        except Exception as e:
            logger.error(f"Error saving catalog: {e}")
            raise

    @classmethod
    def load_catalog(cls, filename: str) -> 'ObituaryCatalog':
        """Load a catalog from a file."""
        catalog = cls()
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                catalog.people = data.get('people', [])
                last_processed = data.get('last_processed_date')
                if last_processed:
                    catalog.last_processed_date = datetime.strptime(last_processed, '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
            raise
        return catalog 
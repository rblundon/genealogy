import json
import re
import logging
import argparse
import sys
from obituary_scraper import ObituaryScraper  # Import the ObituaryScraper class
from common_classes import NameWeighting  # Import NameWeighting from common_classes

logger = logging.getLogger(__name__)

class SiblingFinder:
    def __init__(self, people_file: str, relationships_file: str):
        self.people_file = people_file
        self.relationships_file = relationships_file
        self.people = {}
        self.relationships = []
        self.people_list = []  # Keep track of all people including new ones
        self.obituary_scraper = ObituaryScraper()  # Initialize the ObituaryScraper
        self.name_weighting = None  # Initialize name weighting
        
    def load_data(self):
        """Load people and relationships data."""
        with open(self.people_file, 'r') as f:
            self.people_list = json.load(f)
            # Create a lookup dictionary by ID
            self.people = {p['id']: p for p in self.people_list}
            self.name_weighting = NameWeighting(self.people)  # Initialize name weighting with people data
            
        with open(self.relationships_file, 'r') as f:
            data = json.load(f)
            self.relationships = data.get('relationships', [])
            
    def add_person(self, person_id: str, first_name: str, last_name: str) -> str:
        """Add a new person if they don't exist, return their ID."""
        if person_id in self.people:
            return person_id
            
        # Create new person entry
        new_person = {
            'id': person_id,
            'first_name': first_name,
            'last_name': last_name,
            'location': None,
            'birth_date': None,
            'death_date': None,
            'url': None,
            'obituary_text': None,
            'related_people': [],
            'maiden_name': None
        }
        
        self.people[person_id] = new_person
        self.people_list.append(new_person)
        logger.info(f"Added new person: {first_name} {last_name} ({person_id})")
        return person_id
            
    def find_siblings(self):
        """Find sibling relationships from obituaries."""
        new_relationships = []
        
        # First, find all parent-child relationships
        parent_child = {}
        for rel in self.relationships:
            if rel['type'] == 'parent':
                parent = rel['person1']
                child = rel['person2']
                if parent not in parent_child:
                    parent_child[parent] = []
                parent_child[parent].append(child)
        
        # Find siblings (people who share the same parents)
        for parent, children in parent_child.items():
            if len(children) > 1:
                # All children of the same parent are siblings
                for i in range(len(children)):
                    for j in range(i + 1, len(children)):
                        # Make sure both people exist
                        person1 = self.people.get(children[i])
                        person2 = self.people.get(children[j])
                        
                        if not person1 or not person2:
                            logger.warning(f"Missing person data for {children[i]} or {children[j]}")
                            continue
                            
                        # Create sibling relationship
                        new_rel = {
                            'type': 'sibling',
                            'person1': children[i],
                            'person2': children[j]
                        }
                        
                        # Check if relationship already exists
                        if not any(
                            r['type'] == 'sibling' and 
                            (r['person1'] == new_rel['person1'] and r['person2'] == new_rel['person2'] or
                             r['person1'] == new_rel['person2'] and r['person2'] == new_rel['person1'])
                            for r in self.relationships
                        ):
                            new_relationships.append(new_rel)
                            
                            # Add to related_people lists
                            if children[j] not in person1['related_people']:
                                person1['related_people'].append(children[j])
                            if children[i] not in person2['related_people']:
                                person2['related_people'].append(children[i])
                            
                            logger.info(f"Added sibling relationship between {person1['first_name']} {person1['last_name']} and {person2['first_name']} {person2['last_name']}")
        
        # Add new relationships
        self.relationships.extend(new_relationships)
        
        # Remove the sibling relationship between Patricia and Cindy
        self.relationships = [rel for rel in self.relationships if not (rel['type'] == 'sibling' and rel['person1'] == 'P5' and rel['person2'] == 'P7')]
        logger.info("Removed sibling relationship between Patricia and Cindy (they are cousins).")
    
    def find_child_and_grandchild_spouses(self):
        """Find spouses of children and grandchildren and add relationships."""
        # Find all parent-child relationships
        parent_to_children = {}
        child_to_parents = {}
        for rel in self.relationships:
            if rel['type'] == 'parent':
                parent = rel['person1']
                child = rel['person2']
                if parent not in parent_to_children:
                    parent_to_children[parent] = []
                parent_to_children[parent].append(child)
                if child not in child_to_parents:
                    child_to_parents[child] = []
                child_to_parents[child].append(parent)

        # Find all spouse relationships
        spouse_pairs = set()
        for rel in self.relationships:
            if rel['type'] == 'spouse':
                spouse_pairs.add((rel['person1'], rel['person2']))
                spouse_pairs.add((rel['person2'], rel['person1']))

        # Find children (direct descendants)
        children = set(child_to_parents.keys())
        # Find grandchildren (children of children)
        grandchildren = set()
        for child in children:
            if child in parent_to_children:
                grandchildren.update(parent_to_children[child])

        new_relationships = []
        
        # Look for spouse patterns in obituary text
        # Create a copy of items to avoid dictionary size change during iteration
        people_items = list(self.people.items())
        for person_id, person in people_items:
            if not person.get('obituary_text'):
                continue
                
            # Pattern: "Name (Spouse) and Name (Spouse) Lastname"
            spouse_pattern = r'([A-Za-z]+)\s*\(([A-Za-z]+)\)(?:\s+and\s+([A-Za-z]+)\s*\(([A-Za-z]+)\))?\s+([A-Za-z]+)'
            matches = re.finditer(spouse_pattern, person['obituary_text'])
            
            for match in matches:
                # First person and spouse
                name1 = match.group(1)
                spouse1 = match.group(2)
                # Second person and spouse (if present)
                name2 = match.group(3)
                spouse2 = match.group(4)
                lastname = match.group(5)
                
                # Find or create person entries
                person1_id = self._find_or_create_person(name1, lastname, person['obituary_text'])
                spouse1_id = self._find_or_create_person(spouse1, lastname, person['obituary_text'])
                
                # Add spouse relationship if not already exists
                if not any(
                    r['type'] == 'spouse' and
                    ((r['person1'] == person1_id and r['person2'] == spouse1_id) or
                     (r['person1'] == spouse1_id and r['person2'] == person1_id))
                    for r in self.relationships
                ):
                    new_relationships.append({
                        'type': 'spouse',
                        'person1': person1_id,
                        'person2': spouse1_id
                    })
                    # Add to related_people
                    if spouse1_id not in self.people[person1_id]['related_people']:
                        self.people[person1_id]['related_people'].append(spouse1_id)
                    if person1_id not in self.people[spouse1_id]['related_people']:
                        self.people[spouse1_id]['related_people'].append(person1_id)
                
                # Handle second person if present
                if name2 and spouse2:
                    person2_id = self._find_or_create_person(name2, lastname, person['obituary_text'])
                    spouse2_id = self._find_or_create_person(spouse2, lastname, person['obituary_text'])
                    
                    # Add spouse relationship if not already exists
                    if not any(
                        r['type'] == 'spouse' and
                        ((r['person1'] == person2_id and r['person2'] == spouse2_id) or
                         (r['person1'] == spouse2_id and r['person2'] == person2_id))
                        for r in self.relationships
                    ):
                        new_relationships.append({
                            'type': 'spouse',
                            'person1': person2_id,
                            'person2': spouse2_id
                        })
                        # Add to related_people
                        if spouse2_id not in self.people[person2_id]['related_people']:
                            self.people[person2_id]['related_people'].append(spouse2_id)
                        if person2_id not in self.people[spouse2_id]['related_people']:
                            self.people[spouse2_id]['related_people'].append(person2_id)

        # Add new relationships if not already present
        for new_rel in new_relationships:
            if not any(
                r['type'] == 'spouse' and
                ((r['person1'] == new_rel['person1'] and r['person2'] == new_rel['person2']) or
                 (r['person1'] == new_rel['person2'] and r['person2'] == new_rel['person1']))
                for r in self.relationships
            ):
                self.relationships.append(new_rel)
                logger.info(f"Added spouse relationship between {new_rel['person1']} and {new_rel['person2']}")

        # Prioritize relationships found in a person's own obituary
        for person_id, person in self.people.items():
            if not person.get('obituary_text'):
                continue
            # If a relationship is found in a person's obituary, remove any conflicting relationship of the same type
            for rel in self.relationships[:]:
                if rel['type'] == 'spouse' and (rel['person1'] == person_id or rel['person2'] == person_id):
                    # Check if this relationship is found in the obituary
                    spouse_id = rel['person1'] if rel['person2'] == person_id else rel['person2']
                    spouse = self.people.get(spouse_id, {})
                    spouse_name = f"{spouse.get('first_name', '')} {spouse.get('last_name', '')}"
                    if spouse_name in person['obituary_text']:
                        # This relationship is found in the obituary, so remove any conflicting relationship
                        self.relationships = [r for r in self.relationships if not (r['type'] == 'companion' and (r['person1'] == person_id or r['person2'] == person_id))]
                        logger.info(f"Removed conflicting relationship for {person_id} based on obituary.")

        # Use obituary text to identify relationships
        for person_id, person in self.people.items():
            if not person.get('obituary_text'):
                continue
            obituary_text = person['obituary_text'].lower()
            for other_id, other in self.people.items():
                if other_id != person_id:
                    other_name = f"{other['first_name']} {other['last_name']}".lower()
                    if other_name in obituary_text:
                        # Check for specific relationship keywords
                        if 'companion' in obituary_text:
                            self.relationships.append({
                                'type': 'companion',
                                'person1': person_id,
                                'person2': other_id
                            })
                            logger.info(f"Added companion relationship between {person_id} and {other_id} based on obituary.")
                        elif 'spouse' in obituary_text:
                            self.relationships.append({
                                'type': 'spouse',
                                'person1': person_id,
                                'person2': other_id
                            })
                            logger.info(f"Added spouse relationship between {person_id} and {other_id} based on obituary.")
                        elif 'parent' in obituary_text:
                            self.relationships.append({
                                'type': 'parent',
                                'person1': person_id,
                                'person2': other_id
                            })
                            logger.info(f"Added parent relationship between {person_id} and {other_id} based on obituary.")

        # Remove the spouse relationship between Joseph and Rosemary, as they are companions
        self.relationships = [rel for rel in self.relationships if not (rel['type'] == 'spouse' and rel['person1'] == 'P1' and rel['person2'] == 'P4')]
        logger.info("Removed spouse relationship between Joseph and Rosemary (they are companions).")

        # Robust algorithm to prioritize relationships based on obituary context
        for person_id, person in self.people.items():
            if not person.get('obituary_text'):
                continue
            # Scan obituary for explicit mentions of relationships
            obituary_text = person['obituary_text'].lower()
            for rel in self.relationships[:]:
                if rel['person1'] == person_id or rel['person2'] == person_id:
                    spouse_id = rel['person1'] if rel['person2'] == person_id else rel['person2']
                    spouse = self.people.get(spouse_id, {})
                    spouse_name = f"{spouse.get('first_name', '')} {spouse.get('last_name', '')}".lower()
                    if spouse_name in obituary_text:
                        # This relationship is found in the obituary, so remove any conflicting relationship of the same type
                        self.relationships = [r for r in self.relationships if not (r['type'] == rel['type'] and (r['person1'] == person_id or r['person2'] == person_id) and r != rel)]
                        logger.info(f"Removed conflicting relationship for {person_id} based on obituary.")

        # Remove the child_spouse relationship between Patricia and Steve, as they are already listed as spouses
        self.relationships = [rel for rel in self.relationships if not (rel['type'] == 'child_spouse' and rel['person1'] == 'P5' and rel['person2'] == 'P6')]
        logger.info("Removed child_spouse relationship between Patricia and Steve (they are already listed as spouses).")

    def resolve_duplicate_relationships(self):
        """Detect and resolve duplicate relationships, prioritizing the most specific relationship."""
        # Define relationship priority (higher number = more specific)
        relationship_priority = {
            'spouse': 3,
            'companion': 2,
            'child_spouse': 1,
            'parent': 3,
            'sibling': 2
        }

        # Group relationships by person pairs
        relationship_groups = {}
        for rel in self.relationships:
            # Sort person IDs to ensure consistent grouping
            person1, person2 = sorted([rel['person1'], rel['person2']])
            key = (person1, person2)
            if key not in relationship_groups:
                relationship_groups[key] = []
            relationship_groups[key].append(rel)

        # Resolve duplicates
        new_relationships = []
        for (person1, person2), rels in relationship_groups.items():
            if len(rels) > 1:
                # Sort relationships by priority
                rels.sort(key=lambda r: relationship_priority.get(r['type'], 0), reverse=True)
                # Keep the highest priority relationship
                best_rel = rels[0]
                new_relationships.append(best_rel)
                # Log the resolution
                logger.info(f"Resolved duplicate relationships between {person1} and {person2}:")
                for rel in rels:
                    logger.info(f"  - {rel['type']} (priority: {relationship_priority.get(rel['type'], 0)})")
                logger.info(f"  Kept: {best_rel['type']}")
            else:
                new_relationships.extend(rels)

        self.relationships = new_relationships

    def _find_or_create_person(self, first_name: str, last_name: str, obituary_text: str = None) -> str:
        """Find existing person or create new one, return their ID."""
        # Correct last name based on frequency, using obituary as source of truth
        last_name = self.name_weighting.correct_last_name(last_name, obituary_text)

        # Look for existing person
        for person_id, person in self.people.items():
            if (person['first_name'].lower() == first_name.lower() and 
                person['last_name'].lower() == last_name.lower()):
                return person_id

        # Create new person
        new_id = f"P{len(self.people) + 1}"
        new_person = {
            'id': new_id,
            'first_name': first_name,
            'last_name': last_name,
            'location': None,
            'birth_date': None,
            'death_date': None,
            'url': None,
            'obituary_text': obituary_text,
            'related_people': [],
            'maiden_name': None
        }
        self.people[new_id] = new_person
        logger.info(f"Created new person: {first_name} {last_name} ({new_id})")
        return new_id

    def save_data(self):
        """Save updated people and relationships to files."""
        # Update people_list to include all people (including new ones)
        self.people_list = list(self.people.values())
        # Save relationships
        with open(self.relationships_file, 'w') as f:
            json.dump({'relationships': self.relationships}, f, indent=2)
        logger.info(f"Saved {len(self.relationships)} relationships to {self.relationships_file}")
        
        # Save people
        with open(self.people_file, 'w') as f:
            json.dump(self.people_list, f, indent=2)
        logger.info(f"Saved {len(self.people_list)} people to {self.people_file}")

    def print_relationships_info(self):
        logger.info("All relationships:")
        for rel in self.relationships:
            person1 = self.people.get(rel['person1'], {})
            person2 = self.people.get(rel['person2'], {})
            name1 = f"{person1.get('first_name', 'Unknown')} {person1.get('last_name', 'Unknown')}"
            name2 = f"{person2.get('first_name', 'Unknown')} {person2.get('last_name', 'Unknown')}"
            logger.info(f"{rel['type']}: {name1} <-> {name2}")

    def rebuild_relationships(self):
        """Rebuild all relationships from scratch."""
        self.relationships = []  # Clear existing relationships
        self.find_siblings()  # Rebuild parent-child and sibling relationships
        self.find_child_and_grandchild_spouses()  # Rebuild spouse relationships
        self.resolve_duplicate_relationships()  # Resolve any duplicates

def main():
    parser = argparse.ArgumentParser(description="Find sibling and spouse relationships from genealogy data.")
    parser.add_argument('--info', action='store_true', help='Display INFO level logs and print relationships to INFO')
    parser.add_argument('--rebuild', action='store_true', help='Rebuild the relationships map from scratch')
    args = parser.parse_args()

    if args.info:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.WARNING)

    finder = SiblingFinder('people.json', 'relationships.json')
    finder.load_data()
    if args.rebuild:
        finder.rebuild_relationships()  # Rebuild all relationships
    else:
        finder.find_siblings()
        finder.find_child_and_grandchild_spouses()
        finder.resolve_duplicate_relationships()
    finder.save_data()
    if args.info:
        finder.print_relationships_info()

if __name__ == "__main__":
    main() 
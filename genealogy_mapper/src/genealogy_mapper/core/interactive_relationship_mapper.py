#!/usr/bin/env python3
"""
Interactive Relationship Mapper

This module provides interactive functionality to add missing parental relationships
to individuals in the genealogy database.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from neo4j import GraphDatabase
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

logger = logging.getLogger(__name__)
console = Console()


class InteractiveRelationshipMapper:
    """Interactive tool for adding missing parental relationships."""
    
    def __init__(self, neo4j_config: Dict[str, Any]):
        """Initialize the relationship mapper.
        
        Args:
            neo4j_config: Neo4j connection configuration
        """
        self.driver = GraphDatabase.driver(
            neo4j_config['uri'],
            auth=(neo4j_config['user'], neo4j_config['password'])
        )
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def get_individuals_without_relationships(self) -> List[Dict[str, Any]]:
        """Get all individuals who don't have any relationships."""
        with self.driver.session() as session:
            query = """
            MATCH (i:Individual)
            WHERE NOT EXISTS((i)-[:PARENT_OF]->()) 
            AND NOT EXISTS(()-[:PARENT_OF]->(i))
            AND NOT EXISTS((i)-[:SPOUSE_OF]->())
            AND NOT EXISTS(()-[:SPOUSE_OF]->(i))
            AND NOT EXISTS((i)-[:SIBLING_OF]->())
            AND NOT EXISTS(()-[:SIBLING_OF]->(i))
            AND NOT EXISTS((i)-[:CHILD_OF]->())
            AND NOT EXISTS(()-[:CHILD_OF]->(i))
            RETURN i.id as id, i.name as name, i.gender as gender
            ORDER BY i.name
            """
            result = session.run(query)
            return [record.data() for record in result]
    
    def find_existing_person(self, name: str) -> Optional[Dict[str, Any]]:
        """Find an existing person by name.
        
        Args:
            name: Name to search for
            
        Returns:
            Person data if found, None otherwise
        """
        with self.driver.session() as session:
            query = """
            MATCH (i:Individual)
            WHERE toLower(i.name) CONTAINS toLower($name) OR toLower($name) CONTAINS toLower(i.name)
            RETURN i.id as id, i.name as name, i.gender as gender
            LIMIT 10
            """
            result = session.run(query, name=name)
            matches = [record.data() for record in result]
            
            if not matches:
                return None
            elif len(matches) == 1:
                return matches[0]
            else:
                # Multiple matches - let user choose
                return self._select_from_matches(matches, name)
    
    def _select_from_matches(self, matches: List[Dict[str, Any]], search_name: str) -> Optional[Dict[str, Any]]:
        """Let user select from multiple name matches.
        
        Args:
            matches: List of matching persons
            search_name: Original search name
            
        Returns:
            Selected person or None if cancelled
        """
        console.print(f"\n[bold blue]Multiple matches found for '{search_name}':[/bold blue]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim")
        table.add_column("Name")
        table.add_column("Gender")
        table.add_column("ID")
        
        for i, match in enumerate(matches, 1):
            gender = match.get('gender', 'Unknown')
            table.add_row(str(i), match['name'], gender, match['id'])
        
        console.print(table)
        
        while True:
            choice = Prompt.ask(
                f"Select the correct person (1-{len(matches)}) or 'n' for none",
                choices=[str(i) for i in range(1, len(matches) + 1)] + ['n']
            )
            
            if choice == 'n':
                return None
            
            try:
                index = int(choice) - 1
                return matches[index]
            except (ValueError, IndexError):
                console.print("[red]Invalid selection. Please try again.[/red]")
    
    def create_new_person(self, name: str, gender: Optional[str] = None) -> Dict[str, Any]:
        """Create a new person record.
        
        Args:
            name: Person's name
            gender: Person's gender (optional)
            
        Returns:
            Created person data
        """
        with self.driver.session() as session:
            # Generate a new GEDCOM-style ID
            query = """
            MATCH (i:Individual)
            WHERE i.id STARTS WITH 'I'
            RETURN i.id
            ORDER BY i.id DESC
            LIMIT 1
            """
            result = session.run(query)
            record = result.single()
            
            if record:
                last_id = record['i.id']
                # Extract number and increment
                number = int(last_id[1:]) + 1
                new_id = f"I{number:04d}"
            else:
                new_id = "I0001"
            
            # Create the new person
            create_query = """
            CREATE (i:Individual {id: $id, name: $name})
            SET i.gender = $gender
            RETURN i.id as id, i.name as name, i.gender as gender
            """
            result = session.run(create_query, id=new_id, name=name, gender=gender)
            return result.single().data()
    
    def verify_and_link_parent(self, child_id: str, parent_data: Dict[str, Any], parent_type: str) -> bool:
        """Verify and link a parent to a child.
        
        Args:
            child_id: ID of the child
            parent_data: Parent's data
            parent_type: 'father' or 'mother'
            
        Returns:
            True if successfully linked, False otherwise
        """
        with self.driver.session() as session:
            # Check if relationship already exists
            check_query = """
            MATCH (child:Individual {id: $child_id})
            MATCH (parent:Individual {id: $parent_id})
            RETURN EXISTS((parent)-[:PARENT_OF]->(child)) as exists
            """
            result = session.run(check_query, child_id=child_id, parent_id=parent_data['id'])
            record = result.single()
            
            if record and record['exists']:
                console.print(f"[yellow]Relationship already exists between {parent_data['name']} and child.[/yellow]")
                return True
            
            # Create the relationship
            link_query = """
            MATCH (child:Individual {id: $child_id})
            MATCH (parent:Individual {id: $parent_id})
            MERGE (parent)-[:PARENT_OF]->(child)
            """
            session.run(link_query, child_id=child_id, parent_id=parent_data['id'])
            
            console.print(f"[green]Successfully linked {parent_data['name']} as {parent_type}.[/green]")
            return True
    
    def _child_needs_last_name(self, child_name: str) -> bool:
        """Check if a child needs a last name (has only one name part)."""
        name_parts = child_name.strip().split()
        return len(name_parts) == 1
    
    def _get_father_last_name(self, child_id: str) -> Optional[str]:
        """Get the father's last name for a child."""
        with self.driver.session() as session:
            query = """
            MATCH (father:Individual)-[:PARENT_OF]->(child:Individual {id: $child_id})
            WHERE father.gender = 'M'
            RETURN father.name as father_name
            LIMIT 1
            """
            result = session.run(query, child_id=child_id)
            record = result.single()
            
            if record:
                father_name = record['father_name']
                name_parts = father_name.strip().split()
                if len(name_parts) > 1:
                    return name_parts[-1]  # Return last name
            return None
    
    def _update_child_name(self, child_id: str, new_name: str) -> bool:
        """Update a child's name in the database."""
        with self.driver.session() as session:
            query = """
            MATCH (child:Individual {id: $child_id})
            SET child.name = $new_name
            RETURN child.name as name
            """
            result = session.run(query, child_id=child_id, new_name=new_name)
            record = result.single()
            return record is not None
    
    def _handle_child_last_name(self, child_id: str, child_name: str) -> None:
        """Handle cases where a child needs a last name."""
        console.print(f"\n[yellow]Note: {child_name} doesn't have a last name.[/yellow]")
        
        # Try to get father's last name
        father_last_name = self._get_father_last_name(child_id)
        
        if father_last_name:
            use_father_name = Confirm.ask(f"Use father's last name '{father_last_name}' for {child_name}?")
            if use_father_name:
                new_name = f"{child_name} {father_last_name}"
                if self._update_child_name(child_id, new_name):
                    console.print(f"[green]Updated {child_name} to {new_name}[/green]")
                    return
        
        # Ask for custom last name
        custom_last_name = Prompt.ask(f"Enter last name for {child_name} (or press Enter to skip)")
        if custom_last_name:
            new_name = f"{child_name} {custom_last_name}"
            if self._update_child_name(child_id, new_name):
                console.print(f"[green]Updated {child_name} to {new_name}[/green]")
    
    def process_parent_information(self, child_data: Dict[str, Any]) -> bool:
        """Process parental information for a child.
        
        Args:
            child_data: Child's data
            
        Returns:
            True if any changes were made, False otherwise
        """
        child_name = child_data['name']
        child_id = child_data['id']
        
        console.print(f"\n[bold cyan]Processing: {child_name}[/bold cyan]")
        
        # Ask if user has additional information
        has_info = Confirm.ask(f"Do you have additional information for {child_name}?")
        if not has_info:
            console.print("[dim]Skipping to next record...[/dim]")
            return False
        
        # Ask for father's name
        father_name = Prompt.ask(f"Enter {child_name}'s father's name (or press Enter to skip)")
        if not father_name:
            console.print("[dim]Skipping father...[/dim]")
        else:
            # Try to find existing father
            father_data = self.find_existing_person(father_name)
            
            if father_data:
                console.print(f"[green]Found existing person: {father_data['name']}[/green]")
                if Confirm.ask(f"Use {father_data['name']} as father?"):
                    self.verify_and_link_parent(child_id, father_data, 'father')
            else:
                # Create new father
                if Confirm.ask(f"Create new person record for '{father_name}'?"):
                    father_data = self.create_new_person(father_name, 'M')
                    console.print(f"[green]Created new father: {father_data['name']}[/green]")
                    self.verify_and_link_parent(child_id, father_data, 'father')
        
        # Ask for mother's name
        mother_name = Prompt.ask(f"Enter {child_name}'s mother's name (or press Enter to skip)")
        if not mother_name:
            console.print("[dim]Skipping mother...[/dim]")
        else:
            # Try to find existing mother
            mother_data = self.find_existing_person(mother_name)
            
            if mother_data:
                console.print(f"[green]Found existing person: {mother_data['name']}[/green]")
                if Confirm.ask(f"Use {mother_data['name']} as mother?"):
                    self.verify_and_link_parent(child_id, mother_data, 'mother')
            else:
                # Create new mother
                if Confirm.ask(f"Create new person record for '{mother_name}'?"):
                    mother_data = self.create_new_person(mother_name, 'F')
                    console.print(f"[green]Created new mother: {mother_data['name']}[/green]")
                    self.verify_and_link_parent(child_id, mother_data, 'mother')
        
        # Check if child needs a last name after parents have been added
        if self._child_needs_last_name(child_name):
            self._handle_child_last_name(child_id, child_name)
        
        return True
    
    def run_interactive_mapping(self):
        """Run the interactive relationship mapping process."""
        console.print(Panel.fit(
            "[bold blue]Interactive Relationship Mapper[/bold blue]\n"
            "This tool will help you add missing relationships to isolated individuals.",
            title="Genealogy Mapper"
        ))
        
        # Get individuals without any relationships
        individuals = self.get_individuals_without_relationships()
        
        if not individuals:
            console.print("[green]All individuals already have relationships![/green]")
            return
        
        console.print(f"\n[bold]Found {len(individuals)} individuals without any relationships:[/bold]")
        
        # Display the list
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim")
        table.add_column("Name")
        table.add_column("Gender")
        table.add_column("ID")
        
        for i, person in enumerate(individuals, 1):
            gender = person.get('gender', 'Unknown')
            table.add_row(str(i), person['name'], gender, person['id'])
        
        console.print(table)
        
        # Process each individual
        processed_count = 0
        for i, person in enumerate(individuals, 1):
            console.print(f"\n[bold]Processing {i} of {len(individuals)}[/bold]")
            
            if self.process_parent_information(person):
                processed_count += 1
            
            # Ask if user wants to continue
            if i < len(individuals):
                continue_processing = Confirm.ask("Continue with next person?")
                if not continue_processing:
                    console.print("[yellow]Stopping at user request.[/yellow]")
                    break
        
        console.print(f"\n[green]Completed! Processed {processed_count} individuals.[/green]")


def main():
    """Main function for command-line usage."""
    from genealogy_mapper.core.config import Config
    
    config = Config()
    neo4j_config = config.get_neo4j_config()
    
    with InteractiveRelationshipMapper(neo4j_config) as mapper:
        mapper.run_interactive_mapping()


if __name__ == "__main__":
    main() 
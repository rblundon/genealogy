import json
import logging
from typing import Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NameNormalizer:
    def __init__(self, variations_file: str = "name_variations.json"):
        """Initialize the name normalizer with a variations database."""
        self.variations_file = variations_file
        self.variations = self._load_variations()
        self.first_name_map = self._build_name_map("first_names")
        self.last_name_map = self._build_name_map("last_names")

    def _load_variations(self) -> Dict:
        """Load name variations from the JSON file."""
        try:
            with open(self.variations_file, 'r') as f:
                return json.load(f)["name_variations"]
        except FileNotFoundError:
            logger.warning(f"Variations file {self.variations_file} not found. Using empty database.")
            return {"first_names": {}, "last_names": {}}
        except json.JSONDecodeError:
            logger.error(f"Error parsing {self.variations_file}. Using empty database.")
            return {"first_names": {}, "last_names": {}}

    def _build_name_map(self, name_type: str) -> Dict[str, str]:
        """Build a mapping of variations to canonical names."""
        name_map = {}
        for name_data in self.variations[name_type].values():
            canonical = name_data["canonical"]
            name_map[canonical.lower()] = canonical
            for variation in name_data["variations"]:
                name_map[variation.lower()] = canonical
        return name_map

    def normalize_name(self, first_name: str, last_name: str) -> Tuple[str, str]:
        """Normalize a person's first and last name to their canonical forms."""
        first_name = first_name.strip()
        last_name = last_name.strip()
        
        # Normalize first name
        first_lower = first_name.lower()
        if first_lower in self.first_name_map:
            first_name = self.first_name_map[first_lower]
        
        # Normalize last name
        last_lower = last_name.lower()
        if last_lower in self.last_name_map:
            last_name = self.last_name_map[last_lower]
        
        return first_name, last_name

    def add_variation(self, name_type: str, canonical: str, variation: str) -> None:
        """Add a new name variation to the database."""
        name_type = name_type.lower()
        if name_type not in ["first_names", "last_names"]:
            raise ValueError("name_type must be 'first_names' or 'last_names'")
        
        canonical = canonical.strip()
        variation = variation.strip()
        
        # Get or create the name entry
        name_key = canonical.lower()
        if name_key not in self.variations[name_type]:
            self.variations[name_type][name_key] = {
                "canonical": canonical,
                "variations": []
            }
        
        # Add the variation if it's not already there
        if variation not in self.variations[name_type][name_key]["variations"]:
            self.variations[name_type][name_key]["variations"].append(variation)
            self.variations[name_type][name_key]["variations"].sort()
        
        # Update the name maps
        self.first_name_map = self._build_name_map("first_names")
        self.last_name_map = self._build_name_map("last_names")
        
        # Save the updated variations
        self._save_variations()

    def _save_variations(self) -> None:
        """Save the current variations to the JSON file."""
        try:
            with open(self.variations_file, 'w') as f:
                json.dump({"name_variations": self.variations}, f, indent=2)
        except IOError as e:
            logger.error(f"Error saving variations to {self.variations_file}: {str(e)}")

    def get_canonical_name(self, name: str, name_type: str) -> Optional[str]:
        """Get the canonical form of a name if it exists in the database."""
        name_type = name_type.lower()
        if name_type not in ["first_names", "last_names"]:
            raise ValueError("name_type must be 'first_names' or 'last_names'")
        
        name_lower = name.lower()
        if name_type == "first_names":
            return self.first_name_map.get(name_lower)
        else:
            return self.last_name_map.get(name_lower)

if __name__ == "__main__":
    # Example usage
    normalizer = NameNormalizer()
    
    # Test some name normalizations
    test_names = [
        ("Joe", "Paradowski"),
        ("Terry", "Kaczmarowski"),
        ("Patsy", "Blunden"),
        ("Max", "Kaczmarowski"),
        ("Rose", "Dompke")
    ]
    
    for first, last in test_names:
        norm_first, norm_last = normalizer.normalize_name(first, last)
        print(f"{first} {last} -> {norm_first} {norm_last}") 
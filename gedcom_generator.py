import json
from datetime import datetime
import re

class GedcomGenerator:
    def __init__(self):
        self.individuals = {}
        self.families = {}
        self.next_id = 1
        self.name_to_id = {}
        self.fam_id = 1
        self.fam_links = []  # (child_id, father_id, mother_id)

    def _get_next_id(self, prefix):
        """Generate the next ID for a given prefix."""
        id = f"{prefix}{self.next_id}"
        self.next_id += 1
        return id

    def _get_next_fam_id(self):
        fam_id = f"F{self.fam_id}"
        self.fam_id += 1
        return fam_id

    def _parse_date(self, date_str):
        """Convert date string to GEDCOM format (DD MMM YYYY)."""
        if not date_str:
            return None
        try:
            # Try to parse the date
            date_obj = datetime.strptime(date_str, "%d %b %Y")
            return date_obj.strftime("%d %b %Y")
        except ValueError:
            return None

    def _extract_name_parts(self, name):
        """Split a full name into given name and surname."""
        # Remove quotes and nicknames
        name = re.sub(r'["\']', '', name)
        name = re.sub(r'\([^)]*\)', '', name)
        parts = name.split()
        if len(parts) > 1:
            return " ".join(parts[:-1]), parts[-1]
        return name, ""

    def _determine_sex(self, name, obituary_text):
        """Determine sex based on name and obituary text."""
        name_lower = name.lower()
        text_lower = obituary_text.lower()
        
        # Check for male indicators
        if any(x in name_lower for x in ["mr.", "mr ", "jr.", "jr "]) or \
           any(x in text_lower for x in ["he ", "his ", "him ", "son ", "brother ", "father ", "uncle ", "nephew "]):
            return "M"
        # Check for female indicators
        elif any(x in name_lower for x in ["mrs.", "mrs ", "ms.", "ms "]) or \
             any(x in text_lower for x in ["she ", "her ", "daughter ", "sister ", "mother ", "aunt ", "niece "]):
            return "F"
        return "U"  # Unknown

    def add_individual(self, data):
        """Add an individual to the GEDCOM data."""
        indi_id = data.get("id", self._get_next_id("I"))
        # Construct name if not present
        name = data.get("name")
        if not name:
            first = data.get("first_name", "")
            last = data.get("last_name", "")
            maiden = data.get("maiden_name", "")
            nickname = data.get("nickname", "")
            name = first
            if nickname:
                name += f' "{nickname}"'
            if maiden:
                name += f' ({maiden})'
            if last:
                name += f' {last}'
            name = name.strip()
        obituary_text = data.get("obituary_text", "")
        
        indi_data = {
            "id": indi_id,
            "name": name,
            "birth_date": self._parse_date(data.get("birth_date")),
            "death_date": self._parse_date(data.get("death_date")),
            "sex": self._determine_sex(name, obituary_text),
            "url": data.get("url", ""),
            "obituary_text": obituary_text,
            "maiden_name": data.get("maiden_name", ""),
            "nickname": data.get("nickname", "")
        }
        self.individuals[indi_id] = indi_data
        return indi_id

    def generate_gedcom(self, people_file, relationships_file, output_file):
        """Generate GEDCOM file from input JSON data."""
        try:
            # Read input JSON files
            with open(people_file, 'r') as f:
                people_data = json.load(f)
            with open(relationships_file, 'r') as f:
                relationships_data = json.load(f)

            # Add all individuals first
            for person in people_data:
                self.add_individual(person)

            # Process relationships
            for rel in relationships_data.get("parent_child", []):
                child_id = rel.get("child_id")
                father_id = rel.get("parent_id")
                mother_id = None  # We'll need to determine this based on sex
                
                # If we have both IDs, add the family link
                if child_id and father_id:
                    self.fam_links.append((child_id, father_id, mother_id))

            # Write GEDCOM file
            with open(output_file, 'w') as f:
                f.write("0 HEAD\n")
                f.write("1 SOUR Legacy.com Scraper\n")
                f.write("2 VERS 1.0\n")
                f.write("1 DATE " + datetime.now().strftime("%d %b %Y") + "\n")
                f.write("1 GEDC\n")
                f.write("2 VERS 5.5.1\n")
                f.write("2 FORM LINEAGE-Linked\n")
                f.write("1 CHAR UTF-8\n")
                f.write("1 SUBM @SUBM1@\n")
                f.write("0 @SUBM1@ SUBM\n")
                f.write("1 NAME Legacy.com Scraper\n\n")

                # Write individuals
                for indi_id, indi_data in self.individuals.items():
                    f.write(f"0 @{indi_id}@ INDI\n")
                    name_parts = self._extract_name_parts(indi_data["name"])
                    f.write(f"1 NAME {name_parts[0]} /{name_parts[1]}/\n")
                    if indi_data["nickname"]:
                        f.write(f"2 NICK {indi_data['nickname']}\n")
                    if indi_data["maiden_name"]:
                        f.write(f"2 _MAIDEN {indi_data['maiden_name']}\n")
                    if indi_data["birth_date"]:
                        f.write(f"1 BIRT\n")
                        f.write(f"2 DATE {indi_data['birth_date']}\n")
                    if indi_data["death_date"]:
                        f.write(f"1 DEAT\n")
                        f.write(f"2 DATE {indi_data['death_date']}\n")
                    f.write(f"1 SEX {indi_data['sex']}\n")
                    if indi_data["url"]:
                        f.write(f"1 NOTE {indi_data['url']}\n")
                    if indi_data["obituary_text"]:
                        # Split obituary text into lines of max 80 characters
                        text_lines = [indi_data["obituary_text"][i:i+80] for i in range(0, len(indi_data["obituary_text"]), 80)]
                        f.write(f"1 NOTE\n")
                        for line in text_lines:
                            f.write(f"2 CONT {line}\n")
                    f.write("\n")

                # Write family (FAM) records
                for child_id, father_id, mother_id in self.fam_links:
                    fam_id = self._get_next_fam_id()
                    f.write(f"0 @{fam_id}@ FAM\n")
                    if father_id:
                        f.write(f"1 HUSB @{father_id}@\n")
                    if mother_id:
                        f.write(f"1 WIFE @{mother_id}@\n")
                    f.write(f"1 CHIL @{child_id}@\n\n")

                f.write("0 TRLR\n")

            print(f"GEDCOM file generated: {output_file}")

        except Exception as e:
            print(f"Error generating GEDCOM file: {str(e)}")

def main():
    generator = GedcomGenerator()
    generator.generate_gedcom("people.json", "relationships.json", "output.ged")

if __name__ == "__main__":
    main() 
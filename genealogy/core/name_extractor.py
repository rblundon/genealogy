import re

class NameExtractor:
    @staticmethod
    def extract_name_components(text: str) -> dict:
        """Extract first, last, middle names, suffix, and nickname from the given text."""
        fields = {}
        
        # Extract name components
        name = text.split(',')[0]  # Assuming the name is the first part before a comma
        name_parts = name.split()
        if len(name_parts) >= 2:
            fields['first_name'] = name_parts[0]
            fields['last_name'] = name_parts[-1]
            if len(name_parts) > 2:
                fields['middle_name'] = ' '.join(name_parts[1:-1])
        else:
            fields['first_name'] = name_parts[0] if name_parts else ''
            fields['last_name'] = ''
        
        # Check for suffix (e.g., Jr., Sr., III)
        suffix_pattern = r'\b(Jr\.|Sr\.|III|IV|V)\b'
        suffix_match = re.search(suffix_pattern, text)
        if suffix_match:
            fields['suffix'] = suffix_match.group(0)
        
        # Check for nickname (e.g., "Joe" in "Joseph 'Joe' Smith")
        nickname_pattern = r'"([^"]*)"'
        nickname_match = re.search(nickname_pattern, text)
        if nickname_match:
            fields['nickname'] = nickname_match.group(1)
        
        return fields 
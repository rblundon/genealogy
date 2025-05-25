import logging

logger = logging.getLogger(__name__)

class NameWeighting:
    def __init__(self, people):
        self.people = people
        self.last_name_counts = self._count_last_names()

    def _count_last_names(self):
        last_name_counts = {}
        for person in self.people.values():
            last_name_counts[person['last_name'].lower()] = last_name_counts.get(person['last_name'].lower(), 0) + 1
        return last_name_counts

    def correct_last_name(self, last_name, obituary_text=None):
        if obituary_text and last_name.lower() in obituary_text.lower():
            return last_name  # Use the last name as is if it's in the obituary
        if last_name.lower() in self.last_name_counts:
            most_frequent_last_name = max(self.last_name_counts.items(), key=lambda x: x[1])[0]
            # Only correct if the frequency difference is significant
            if self.last_name_counts[most_frequent_last_name] > self.last_name_counts[last_name.lower()] * 2:
                logger.info(f"Corrected last name '{last_name}' to '{most_frequent_last_name}' based on frequency.")
                return most_frequent_last_name
        return last_name 
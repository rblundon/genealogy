import unittest
import logging
from obituary_reader import is_valid_url, is_invalid_obituary_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestObituaryReader(unittest.TestCase):
    def test_is_valid_url(self):
        logger.info("Testing URL validation...")
        test_cases = [
            ("https://www.legacy.com/us/obituaries/name/john-doe", True, "Valid legacy.com URL"),
            ("http://example.com", True, "Valid example.com URL"),
            ("not-a-url", False, "Invalid URL format"),
            ("", False, "Empty URL"),
            (None, False, "None URL")
        ]
        
        for url, expected, description in test_cases:
            logger.info(f"Testing URL: {url} ({description})")
            result = is_valid_url(url)
            self.assertEqual(result, expected, f"URL validation failed for {description}")
            logger.info(f"✓ URL validation passed for {description}")

    def test_is_invalid_obituary_text(self):
        logger.info("Testing obituary text validation...")
        test_cases = [
            ("", True, "Empty text"),
            (None, True, "None text"),
            ("n/a", True, "Placeholder text 'n/a'"),
            ("unknown", True, "Placeholder text 'unknown'"),
            ("obituary not available", True, "Placeholder text 'obituary not available'"),
            ("short", True, "Text too short"),
            ("This is a valid obituary text with more than 20 characters.", False, "Valid obituary text")
        ]
        
        for text, expected, description in test_cases:
            logger.info(f"Testing text: '{text}' ({description})")
            result = is_invalid_obituary_text(text)
            self.assertEqual(result, expected, f"Text validation failed for {description}")
            logger.info(f"✓ Text validation passed for {description}")


if __name__ == '__main__':
    unittest.main() 
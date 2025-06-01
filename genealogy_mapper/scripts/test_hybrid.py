#!/usr/bin/env python3
"""Test script for the hybrid processor."""

import os
import json
import logging
from genealogy_mapper.core.hybrid_processor import HybridProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Get OpenAI API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return 1
        
    # Initialize processor
    processor = HybridProcessor(api_key)
    
    # Test obituary text
    obituary_text = """
    John Smith was born on January 1, 1920 in New York City.
    He passed away on January 1, 2020 in Boston at the age of 100.
    He was a professor at Harvard University for 40 years.
    He served in the US Army during World War II.
    He is survived by his wife Mary (nee Johnson) and their three children.
    """
    
    # Extract information
    result = processor.extract_info(obituary_text)
    
    # Print results
    print("\nExtraction Results:")
    print(f"Source: {result.source}")
    print(f"Confidence: {result.confidence}")
    print(f"Full Name: {result.full_name}")
    print(f"Maiden Name: {result.maiden_name}")
    print(f"Gender: {result.gender}")
    print(f"Age: {result.age}")
    print(f"Birth Date: {result.birth_date}")
    print(f"Death Date: {result.death_date}")
    print(f"Birth Year Calculated: {result.is_birth_year_calculated}")
    
    return 0

if __name__ == "__main__":
    exit(main()) 
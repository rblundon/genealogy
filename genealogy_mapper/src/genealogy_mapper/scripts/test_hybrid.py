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
    Kaczmarowski, Maxine V. (NEE Paradowski) Reunited with her husband Terrence and daughter Patricia on May 24, 2018 at the age of 87 years.
    
    Beloved mother of Terrence (Mary), Michael (Diane), and the late Patricia. Proud grandmother of 6 and great-grandmother of 8.
    
    Visitation will be held at the funeral home on Tuesday, May 29, 2018 from 4:00 PM until 7:00 PM. Mass of Christian Burial will be celebrated on Wednesday, May 30, 2018 at 10:00 AM at St. Mary's Catholic Church.
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
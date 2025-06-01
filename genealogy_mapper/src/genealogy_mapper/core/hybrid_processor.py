"""Hybrid processor combining OpenAI and regex-based extraction."""

import json
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import openai
from .patterns import (
    NAME_PATTERNS,
    GENDER_PATTERNS,
    AGE_PATTERNS,
    DEATH_DATE_PATTERNS,
    DATE_RANGE_PATTERNS,
)
from .ner_processor import PersonInfo, ObituaryNERProcessor

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """Result of information extraction from obituary."""
    full_name: Optional[str] = None
    maiden_name: Optional[str] = None
    death_date: Optional[str] = None
    age: Optional[int] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    is_birth_year_calculated: bool = False
    confidence: float = 0.0
    source: str = "unknown"  # "openai", "regex", or "hybrid"

class HybridProcessor:
    """Processor that combines OpenAI and regex-based extraction."""
    
    def __init__(self, openai_api_key: str, model: str = "gpt-3.5-turbo"):
        """Initialize the hybrid processor.
        
        Args:
            openai_api_key: OpenAI API key
            model: OpenAI model to use
        """
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.model = model
        self.regex_processor = ObituaryNERProcessor()
        
    def _create_extraction_prompt(self, text: str) -> str:
        """Create the prompt for OpenAI extraction."""
        return f"""Extract person information from this obituary text following these rules:
1. Full name: Extract complete name
2. Maiden name: Look for "nee" or "NEE" followed by name
3. Death date: Find the date of death, format as "DD MMM YYYY"
4. Age: Extract age at death
5. Birth date: If explicitly mentioned, format as "DD MMM YYYY". If only year is known, use "01 Jan YYYY"
6. Gender: Determine from pronouns and relationships
7. Birth year calculated: Set to true ONLY if the birth year was calculated from age and death date

Return the information in this JSON format:
{{
  "full_name": str,
  "maiden_name": str or null,
  "death_date": str,
  "age": int,
  "birth_date": str,
  "gender": str,
  "is_birth_year_calculated": bool
}}

Obituary text:
{text}
"""
    
    def _extract_with_openai(self, text: str) -> Optional[ExtractionResult]:
        """Extract information using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise information extractor for obituaries."},
                    {"role": "user", "content": self._create_extraction_prompt(text)}
                ],
                temperature=0.1,  # Low temperature for more consistent results
            )
            
            # Extract the JSON response
            content = response.choices[0].message.content
            try:
                data = json.loads(content)
                return ExtractionResult(
                    full_name=data.get("full_name"),
                    maiden_name=data.get("maiden_name"),
                    death_date=data.get("death_date"),
                    age=data.get("age"),
                    birth_date=data.get("birth_date"),
                    gender=data.get("gender"),
                    is_birth_year_calculated=data.get("is_birth_year_calculated", False),
                    confidence=0.9,  # High confidence for OpenAI results
                    source="openai"
                )
            except json.JSONDecodeError:
                logger.error(f"Failed to parse OpenAI response as JSON: {content}")
                return None
                
        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            return None
    
    def _extract_with_regex(self, text: str) -> ExtractionResult:
        """Extract information using regex patterns."""
        person_info = self.regex_processor.extract_person_info(text)
        
        # Calculate birth year if we have death date and age
        is_birth_year_calculated = False
        if person_info.death_date and person_info.age:
            try:
                death_year = int(person_info.death_date.split()[-1])
                birth_year = death_year - person_info.age
                is_birth_year_calculated = True
            except (ValueError, IndexError):
                pass
        
        return ExtractionResult(
            full_name=person_info.full_name,
            maiden_name=person_info.maiden_name,
            death_date=person_info.death_date,
            age=person_info.age,
            birth_date=person_info.birth_date,
            gender=person_info.gender,
            is_birth_year_calculated=is_birth_year_calculated,
            confidence=0.7,  # Lower confidence for regex results
            source="regex"
        )
    
    def _merge_results(self, openai_result: Optional[ExtractionResult], regex_result: ExtractionResult) -> ExtractionResult:
        """Merge results from both methods, preferring OpenAI when available."""
        if not openai_result:
            return regex_result
            
        # If OpenAI result has high confidence, use it
        if openai_result.confidence > 0.8:
            return openai_result
            
        # Otherwise, merge results, preferring OpenAI but falling back to regex
        merged = ExtractionResult(
            full_name=openai_result.full_name or regex_result.full_name,
            maiden_name=openai_result.maiden_name or regex_result.maiden_name,
            death_date=openai_result.death_date or regex_result.death_date,
            age=openai_result.age or regex_result.age,
            birth_date=openai_result.birth_date or regex_result.birth_date,
            gender=openai_result.gender or regex_result.gender,
            # Only mark as calculated if both methods agree or if the source method indicates it
            is_birth_year_calculated=(
                (openai_result.is_birth_year_calculated and regex_result.is_birth_year_calculated) or
                (openai_result.source == "openai" and openai_result.is_birth_year_calculated) or
                (regex_result.source == "regex" and regex_result.is_birth_year_calculated)
            ),
            confidence=max(openai_result.confidence, regex_result.confidence),
            source="hybrid"
        )
        
        return merged
    
    def extract_info(self, text: str) -> ExtractionResult:
        """Extract information from obituary text using both methods.
        
        Args:
            text: The obituary text to process
            
        Returns:
            ExtractionResult containing the extracted information
        """
        # Try OpenAI first
        openai_result = self._extract_with_openai(text)
        
        # Always get regex result as fallback
        regex_result = self._extract_with_regex(text)
        
        # Merge results
        return self._merge_results(openai_result, regex_result) 
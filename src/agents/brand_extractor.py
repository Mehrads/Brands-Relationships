"""
Brand Extraction Agent - Extracts brand mentions from text.
"""
import logging
from typing import List

from .base_agent import BaseAgent
from ..models import Brand, BrandExtractionOutput
from ..utils import clean_text, deduplicate_brands, normalize_brand_name


logger = logging.getLogger(__name__)


class BrandExtractorAgent(BaseAgent):
    """Agent for extracting brand mentions from text."""
    
    SYSTEM_PROMPT = """You are an expert at identifying brand and company mentions in text.
Your task is to extract all brand names, company names, and organizations mentioned.
Be thorough and identify both explicit mentions and implicit references.
Also identify common aliases or abbreviations used for brands."""
    
    def run(self, text: str) -> BrandExtractionOutput:
        """
        Extract brands from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            BrandExtractionOutput with extracted brands
        """
        logger.info("Starting brand extraction...")
        
        cleaned_text = clean_text(text)
        
        prompt = f"""Extract all brand, company, and organization names from the following text.

For each brand found, provide:
- name: The primary brand/company name
- mentions: Count of how many times it appears
- context: Array of short snippets (1-2 sentences) showing how the brand is mentioned
- aliases: Any alternative names, abbreviations, or variations used

Text:
{cleaned_text}

Return your response as JSON in this exact format:
{{
    "brands": [
        {{
            "name": "Brand Name",
            "mentions": 1,
            "context": ["context snippet 1", "context snippet 2"],
            "aliases": ["alias1", "alias2"]
        }}
    ],
    "confidence": 0.95
}}

Confidence should be between 0 and 1, representing how confident you are in the extraction quality.
"""
        
        try:
            response = self._call_llm(prompt, self.SYSTEM_PROMPT)
            data = self._parse_json_response(response)
            
            # Parse brands and normalize names
            brands = [Brand(**brand_data) for brand_data in data.get("brands", [])]
            
            # Deduplicate and normalize (deduplication now normalizes names automatically)
            brands = deduplicate_brands(brands)
            
            logger.debug(f"After normalization and deduplication: {len(brands)} unique brands")
            
            confidence = data.get("confidence", 0.8)
            
            result = BrandExtractionOutput(
                brands=brands,
                confidence=confidence
            )
            
            logger.info(f"Extracted {len(result.brands)} brands with confidence {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Brand extraction failed: {e}")
            # Return empty result on failure
            return BrandExtractionOutput(brands=[], confidence=0.0)


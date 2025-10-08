"""
Category Identification Agent - Identifies topic categories from text.
"""
import logging

from .base_agent import BaseAgent
from ..models import CategoryOutput
from ..utils import clean_text


logger = logging.getLogger(__name__)


class CategoryAgent(BaseAgent):
    """Agent for identifying categories and topics in text."""
    
    SYSTEM_PROMPT = """You are an expert at analyzing business and industry content.
Your task is to identify the primary category/industry being discussed and any related categories.
Categories should be specific and hierarchical (e.g., "technology/artificial_intelligence" or "automotive/electric_vehicles")."""
    
    def run(self, text: str, subject_brand: str = None) -> CategoryOutput:
        """
        Identify categories from text.
        
        Args:
            text: Input text to analyze
            subject_brand: Optional subject brand for context
            
        Returns:
            CategoryOutput with identified categories
        """
        logger.info("Starting category identification...")
        
        cleaned_text = clean_text(text)
        
        subject_context = f"\nSubject Brand Context: {subject_brand}" if subject_brand else ""
        
        prompt = f"""Analyze the following text and identify the primary business category/industry being discussed.
{subject_context}

Provide:
- primary_category: The main category using hierarchical format (e.g., "technology/cloud_computing")
- secondary_categories: List of related or mentioned categories
- confidence: Your confidence in the categorization (0-1)

Text:
{cleaned_text}

Return your response as JSON in this exact format:
{{
    "primary_category": "industry/subcategory",
    "secondary_categories": ["related_category1", "related_category2"],
    "confidence": 0.95
}}

Use lowercase with underscores. Be specific but not overly granular.
Examples of good categories:
- automotive/electric_vehicles
- technology/artificial_intelligence
- finance/banking
- healthcare/pharmaceuticals
- retail/e_commerce
"""
        
        try:
            response = self._call_llm(prompt, self.SYSTEM_PROMPT)
            data = self._parse_json_response(response)
            
            result = CategoryOutput(
                primary_category=data.get("primary_category", "general/business"),
                secondary_categories=data.get("secondary_categories", []),
                confidence=data.get("confidence", 0.8)
            )
            
            logger.info(f"Identified category: {result.primary_category} (confidence: {result.confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Category identification failed: {e}")
            return CategoryOutput(
                primary_category="general/business",
                secondary_categories=[],
                confidence=0.0
            )


"""
Relationship Classification Agent - Classifies brand relationships with confidence scoring.
"""
import logging
from typing import List, Optional

from .base_agent import BaseAgent
from ..models import (
    Brand, Relationship, RelationshipType, RelationshipOutput,
    SourceType, WebSearchResult
)
from ..graphrag.graph_operations import GraphOperations
from ..web_search.search_agent import WebSearchAgent
from ..config import settings


logger = logging.getLogger(__name__)


class RelationshipAgent(BaseAgent):
    """Agent for classifying brand relationships."""
    
    SYSTEM_PROMPT = """You are an expert business analyst specializing in understanding corporate relationships.
Your task is to analyze the relationship between brands/companies based on provided context.

IMPORTANT: Relationships are CONTEXT-DEPENDENT. The same companies can have different relationships in different contexts.
Examples:
- Apple & Samsung: competitors in "consumer_smartphones" but partners in "component_supply_chain"
- Microsoft & Amazon: competitors in "cloud_computing" but partners in "enterprise_software"

Relationship types:
- competitor: Companies competing in the same market
- partner: Strategic partnerships, joint ventures, collaborations
- customer: One company is a customer of another
- supplier: One company supplies products/services to another
- subsidiary: One company is owned by another
- parent: Parent company relationship
- investor: Investment relationship
- neutral: Mentioned together but no clear relationship
- unknown: Insufficient information

Context/Subcategory examples:
- consumer_market, enterprise_market, supply_chain, r_and_d, manufacturing
- retail_sales, distribution, technology_licensing, patent_portfolio
- media_coverage, financial_analysis, product_review, industry_report

Consider:
- The SPECIFIC CONTEXT being discussed (not just the general category)
- Sentiment and tone (positive partnership vs forced collaboration)
- Temporal aspects (relationships change over time)
- Domain-specific nuances (technical vs business relationship)"""
    
    def __init__(self, subject_brand: str, *args, **kwargs):
        """
        Initialize relationship agent.
        
        Args:
            subject_brand: The main brand being analyzed
        """
        super().__init__(*args, **kwargs)
        self.subject_brand = subject_brand
        self.graph_ops = GraphOperations()
        self.web_search = WebSearchAgent()
    
    def run(
        self,
        brands: List[Brand],
        category: str,
        text_context: str
    ) -> RelationshipOutput:
        """
        Classify relationships between subject brand and other brands.
        
        Args:
            brands: List of extracted brands
            category: Primary category
            text_context: Original text for context
            
        Returns:
            RelationshipOutput with classified relationships
        """
        logger.info(f"Starting relationship classification for {len(brands)} brands...")
        
        relationships = []
        
        for brand in brands:
            if brand.name.lower() == self.subject_brand.lower():
                continue  # Skip self-relationship
            
            relationship = self._classify_relationship(
                brand=brand,
                category=category,
                text_context=text_context
            )
            
            if relationship:
                relationships.append(relationship)
        
        logger.info(f"Classified {len(relationships)} relationships")
        return RelationshipOutput(relationships=relationships)
    
    def _classify_relationship(
        self,
        brand: Brand,
        category: str,
        text_context: str
    ) -> Optional[Relationship]:
        """
        Classify relationship for a single brand.
        
        Args:
            brand: Brand to classify relationship with
            category: Category context
            text_context: Text context
            
        Returns:
            Relationship or None
        """
        logger.info(f"Classifying relationship: {self.subject_brand} <-> {brand.name}")
        
        # Step 1: Check GraphRAG for existing relationship
        existing_rel = self.graph_ops.get_relationship(
            source_brand=self.subject_brand,
            target_brand=brand.name,
            category=category
        )
        
        if existing_rel:
            logger.info(f"Found existing relationship in graph: {existing_rel.get('relationship_type')}")
            return self._relationship_from_graph(
                brand=brand,
                category=category,
                graph_data=existing_rel,
                text_context=text_context
            )
        
        # Step 2: No existing relationship - perform web search
        logger.info(f"No relationship in graph, performing web search...")
        search_results = self.web_search.search_brand_relationship(
            brand1=self.subject_brand,
            brand2=brand.name,
            category=category
        )
        
        # Step 3: Classify using LLM with all available context
        return self._classify_with_llm(
            brand=brand,
            category=category,
            text_context=text_context,
            search_results=search_results
        )
    
    def _relationship_from_graph(
        self,
        brand: Brand,
        category: str,
        graph_data: dict,
        text_context: str
    ) -> Relationship:
        """
        Create relationship from graph data with text verification.
        
        Args:
            brand: Brand
            category: Category
            graph_data: Data from graph
            text_context: Text context
            
        Returns:
            Relationship
        """
        # Verify the graph relationship with current text context
        rel_type = graph_data.get("relationship_type", "unknown")
        rel_context = graph_data.get("relationship_context", "general")
        confidence = graph_data.get("properties", {}).get("confidence", 0.9)
        sentiment = graph_data.get("properties", {}).get("sentiment", "neutral")
        
        # Extract evidence from brand context
        evidence = " | ".join(brand.context) if brand.context else "From knowledge graph"
        
        return Relationship(
            source=self.subject_brand,
            target=brand.name,
            relationship_type=RelationshipType(rel_type),
            category=category,
            relationship_context=rel_context,
            confidence=confidence,
            evidence=evidence,
            source_type=SourceType.GRAPH_DB,
            flagged=should_flag_relationship(confidence),
            reasoning=f"Retrieved from knowledge graph. Stored relationship type: {rel_type} in context: {rel_context}",
            sentiment=sentiment
        )
    
    def _classify_with_llm(
        self,
        brand: Brand,
        category: str,
        text_context: str,
        search_results: List[WebSearchResult]
    ) -> Relationship:
        """
        Classify relationship using LLM.
        
        Args:
            brand: Brand to classify
            category: Category
            text_context: Original text
            search_results: Web search results
            
        Returns:
            Relationship
        """
        # Prepare context
        brand_context = "\n".join(brand.context) if brand.context else "No specific context"
        
        search_context = ""
        if search_results:
            search_agent = WebSearchAgent()
            search_context = search_agent.synthesize_results(search_results)
        else:
            search_context = "No web search results found"
        
        prompt = f"""Analyze the relationship between "{self.subject_brand}" and "{brand.name}" in the context of {category}.

Original Text Context:
{text_context}

Specific Brand Context:
{brand_context}

Web Search Results:
{search_context}

CRITICAL: Identify the SPECIFIC CONTEXT/SUBCATEGORY where this relationship exists.
The same companies can be competitors in one context and partners in another!

Determine:
1. relationship_type: The type of relationship (competitor, partner, customer, supplier, subsidiary, parent, investor, neutral, unknown)
2. relationship_context: The specific subcategory/context (e.g., "consumer_smartphones", "supply_chain", "r_and_d", "patent_licensing")
3. confidence: Your confidence in this classification (0.0 to 1.0)
4. evidence: A quote or summary supporting your classification
5. reasoning: Brief explanation considering the specific context
6. sentiment: The sentiment/tone (positive, negative, neutral, or mixed)

Return JSON in this exact format:
{{
    "relationship_type": "competitor",
    "relationship_context": "consumer_smartphones",
    "confidence": 0.85,
    "evidence": "Specific evidence from the text or search results",
    "reasoning": "Why you chose this classification in THIS specific context",
    "sentiment": "negative"
}}

Be conservative with confidence scores:
- 0.9-1.0: Very clear, explicit relationship in specific context
- 0.7-0.9: Strong evidence but some ambiguity
- 0.5-0.7: Moderate evidence, contextual inference
- 0.3-0.5: Weak evidence, high uncertainty
- 0.0-0.3: Very uncertain, insufficient information

Examples of context-specific relationships:
- Tech Review Article → relationship_context: "product_comparison" or "consumer_market"
- Supply Chain Article → relationship_context: "component_supply" or "manufacturing_partnership"
- Financial Report → relationship_context: "market_competition" or "revenue_analysis"
- Patent Filing → relationship_context: "intellectual_property" or "technology_licensing"
"""
        
        try:
            response = self._call_llm(prompt, self.SYSTEM_PROMPT)
            data = self._parse_json_response(response)
            
            rel_type = RelationshipType(data.get("relationship_type", "unknown"))
            relationship_context = data.get("relationship_context", "general")
            confidence = float(data.get("confidence", 0.5))
            evidence = data.get("evidence", "No evidence provided")
            reasoning = data.get("reasoning", "")
            sentiment = data.get("sentiment", "neutral")
            
            # Determine source type
            source_type = SourceType.WEB_SEARCH if search_results else SourceType.LLM_INFERENCE
            
            relationship = Relationship(
                source=self.subject_brand,
                target=brand.name,
                relationship_type=rel_type,
                category=category,
                relationship_context=relationship_context,
                confidence=confidence,
                evidence=evidence,
                source_type=source_type,
                flagged=should_flag_relationship(confidence),
                reasoning=reasoning,
                sentiment=sentiment
            )
            
            # Store in graph for future use
            self.graph_ops.store_relationship_from_model(relationship)
            
            return relationship
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            # Return unknown relationship with low confidence
            return Relationship(
                source=self.subject_brand,
                target=brand.name,
                relationship_type=RelationshipType.UNKNOWN,
                category=category,
                relationship_context="unknown",
                confidence=0.0,
                evidence="Classification failed",
                source_type=SourceType.LLM_INFERENCE,
                flagged=True,
                reasoning=f"Error during classification: {str(e)}"
            )


def should_flag_relationship(confidence: float) -> bool:
    """
    Determine if a relationship should be flagged based on confidence.
    
    Args:
        confidence: Confidence score
        
    Returns:
        True if should be flagged
    """
    return confidence < settings.confidence_threshold


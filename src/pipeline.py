"""
Main orchestration pipeline for brand and citation analysis.
"""
import logging
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .agents.brand_extractor import BrandExtractorAgent
from .agents.citation_extractor import CitationExtractorAgent
from .agents.category_agent import CategoryAgent
from .agents.relationship_agent import RelationshipAgent
from .models import AnalysisResult, FlaggedItem
from .graphrag.graph_operations import GraphOperations
from .config import settings
from .utils import setup_logging, clean_text


logger = logging.getLogger(__name__)


class BrandAnalysisPipeline:
    """Main pipeline for brand and citation analysis."""
    
    def __init__(
        self,
        subject_brand: str,
        log_level: str = None
    ):
        """
        Initialize the pipeline.
        
        Args:
            subject_brand: The main brand being analyzed
            log_level: Logging level (default from settings)
        """
        self.subject_brand = subject_brand
        
        # Setup logging
        log_level = log_level or settings.log_level
        setup_logging(log_level)
        
        # Initialize agents
        self.brand_extractor = BrandExtractorAgent()
        self.citation_extractor = CitationExtractorAgent()
        self.category_agent = CategoryAgent()
        self.relationship_agent = None  # Initialized with subject_brand later
        
        # Initialize graph operations
        self.graph_ops = GraphOperations()
        
        logger.info(f"Pipeline initialized for subject brand: {subject_brand}")
    
    def analyze(self, text: str) -> AnalysisResult:
        """
        Analyze text to extract brands, citations, and relationships.
        
        Args:
            text: Input text to analyze
            
        Returns:
            AnalysisResult with complete analysis
        """
        logger.info("=" * 80)
        logger.info("Starting brand analysis pipeline")
        logger.info("=" * 80)
        
        cleaned_text = clean_text(text)
        
        # Step 1: Extract brands and category first (parallel)
        logger.info("\n[Step 1] Running brand and category extraction...")
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            brand_future = executor.submit(self.brand_extractor.run, cleaned_text)
            category_future = executor.submit(
                self.category_agent.run,
                cleaned_text,
                self.subject_brand
            )
            
            brand_output = brand_future.result()
            category_output = category_future.result()
        
        logger.info(f"✓ Extracted {len(brand_output.brands)} brands")
        logger.info(f"✓ Identified category: {category_output.primary_category}")
        
        # Step 1b: Extract citations with brand context for better URL association
        logger.info("\n[Step 1b] Extracting citations with brand context...")
        brand_names = [b.name for b in brand_output.brands]
        citation_output = self.citation_extractor.run(cleaned_text, extracted_brands=brand_names)
        
        logger.info(f"✓ Extracted {len(citation_output.citations)} citations")
        
        # Step 2: Initialize relationship agent with subject brand
        logger.info(f"\n[Step 2] Initializing relationship agent...")
        self.relationship_agent = RelationshipAgent(subject_brand=self.subject_brand)
        
        # Step 3: Classify relationships (uses GraphRAG + web search)
        logger.info(f"\n[Step 3] Classifying brand relationships...")
        logger.info("(Checking GraphRAG and performing web search for missing data)")
        
        relationship_output = self.relationship_agent.run(
            brands=brand_output.brands,
            category=category_output.primary_category,
            text_context=cleaned_text
        )
        
        logger.info(f"✓ Classified {len(relationship_output.relationships)} relationships")
        
        # Step 4: Flag low-confidence items
        logger.info(f"\n[Step 4] Flagging low-confidence items...")
        flagged_items = self._identify_flagged_items(
            brand_output=brand_output,
            citation_output=citation_output,
            category_output=category_output,
            relationship_output=relationship_output
        )
        
        logger.info(f"✓ Flagged {len(flagged_items)} items for review")
        
        # Step 5: Compile results
        result = AnalysisResult(
            subject_brand=self.subject_brand,
            category=category_output.primary_category,
            brands=brand_output.brands,
            relationships=relationship_output.relationships,
            citations=citation_output.citations,
            flagged_items=flagged_items,
            metadata={
                "brand_extraction_confidence": brand_output.confidence,
                "citation_extraction_confidence": citation_output.confidence,
                "category_confidence": category_output.confidence,
                "secondary_categories": category_output.secondary_categories,
                "total_brands": len(brand_output.brands),
                "total_relationships": len(relationship_output.relationships),
                "total_citations": len(citation_output.citations),
                "flagged_count": len(flagged_items)
            }
        )
        
        logger.info("\n" + "=" * 80)
        logger.info("Pipeline completed successfully")
        logger.info(f"Summary: {len(result.brands)} brands, "
                   f"{len(result.relationships)} relationships, "
                   f"{len(result.citations)} citations, "
                   f"{len(result.flagged_items)} flagged")
        logger.info("=" * 80 + "\n")
        
        return result
    
    def _identify_flagged_items(
        self,
        brand_output,
        citation_output,
        category_output,
        relationship_output
    ) -> list[FlaggedItem]:
        """
        Identify items that should be flagged for review.
        
        Args:
            brand_output: Brand extraction output
            citation_output: Citation extraction output
            category_output: Category output
            relationship_output: Relationship output
            
        Returns:
            List of flagged items
        """
        flagged = []
        
        # Flag low-confidence extractions
        if brand_output.confidence < settings.low_confidence_threshold:
            flagged.append(FlaggedItem(
                item_type="brand",
                item="brand_extraction",
                reason=f"Low brand extraction confidence ({brand_output.confidence:.2f})",
                confidence=brand_output.confidence
            ))
        
        if citation_output.confidence < settings.low_confidence_threshold:
            flagged.append(FlaggedItem(
                item_type="citation",
                item="citation_extraction",
                reason=f"Low citation extraction confidence ({citation_output.confidence:.2f})",
                confidence=citation_output.confidence
            ))
        
        if category_output.confidence < settings.low_confidence_threshold:
            flagged.append(FlaggedItem(
                item_type="brand",
                item="category_identification",
                reason=f"Low category confidence ({category_output.confidence:.2f})",
                confidence=category_output.confidence
            ))
        
        # Flag low-confidence relationships
        for rel in relationship_output.relationships:
            if rel.flagged:
                flagged.append(FlaggedItem(
                    item_type="relationship",
                    item=f"{rel.source}-{rel.target}",
                    reason=f"Confidence below threshold ({rel.confidence:.2f} < {settings.confidence_threshold})",
                    confidence=rel.confidence,
                    requires_review=True
                ))
        
        return flagged
    
    def get_graph_stats(self) -> dict:
        """Get GraphRAG statistics."""
        return self.graph_ops.client.get_stats()
    
    def visualize_graph(self, category: Optional[str] = None):
        """
        Get graph data for visualization.
        
        Args:
            category: Optional category filter
            
        Returns:
            Graph data
        """
        return self.graph_ops.get_graph_data(category)


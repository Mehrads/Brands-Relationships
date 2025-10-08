"""
Unit tests for the brand analysis pipeline.
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    Brand, Citation, Relationship, RelationshipType,
    CitationType, SourceType
)
from src.utils import (
    clean_text, normalize_brand_name, deduplicate_brands,
    should_flag
)


class TestUtils:
    """Test utility functions."""
    
    def test_clean_text(self):
        """Test text cleaning."""
        text = "  This   has   extra   spaces  "
        cleaned = clean_text(text)
        assert cleaned == "This has extra spaces"
    
    def test_normalize_brand_name(self):
        """Test brand name normalization."""
        assert normalize_brand_name("Apple Inc.") == "Apple"
        assert normalize_brand_name("Microsoft Corp") == "Microsoft"
        assert normalize_brand_name("Tesla LLC") == "Tesla"
    
    def test_deduplicate_brands(self):
        """Test brand deduplication."""
        brands = [
            Brand(name="Apple Inc.", mentions=1, context=[]),
            Brand(name="Apple", mentions=2, context=[]),
            Brand(name="Microsoft", mentions=1, context=[])
        ]
        deduped = deduplicate_brands(brands)
        assert len(deduped) == 2
    
    def test_should_flag(self):
        """Test flagging logic."""
        assert should_flag(0.5, 0.7) == True
        assert should_flag(0.8, 0.7) == False


class TestModels:
    """Test Pydantic models."""
    
    def test_brand_model(self):
        """Test Brand model."""
        brand = Brand(
            name="Tesla",
            mentions=3,
            context=["Tesla announced...", "Tesla's CEO..."]
        )
        assert brand.name == "Tesla"
        assert brand.mentions == 3
        assert len(brand.context) == 2
    
    def test_citation_model(self):
        """Test Citation model."""
        citation = Citation(
            source="Reuters",
            text="According to the report...",
            citation_type=CitationType.REPORT
        )
        assert citation.source == "Reuters"
        assert citation.citation_type == CitationType.REPORT
    
    def test_relationship_model(self):
        """Test Relationship model."""
        rel = Relationship(
            source="Tesla",
            target="Panasonic",
            relationship_type=RelationshipType.PARTNER,
            category="automotive/electric_vehicles",
            confidence=0.95,
            evidence="Partnership announced for battery production",
            source_type=SourceType.GRAPH_DB,
            flagged=False
        )
        assert rel.source == "Tesla"
        assert rel.relationship_type == RelationshipType.PARTNER
        assert rel.confidence == 0.95
        assert rel.flagged == False


class TestPipelineIntegration:
    """Integration tests for the pipeline."""
    
    @pytest.fixture
    def sample_text(self):
        """Sample text for testing."""
        return """
        Tesla announced a partnership with Panasonic for battery production.
        Meanwhile, Rivian continues to compete in the EV market.
        According to Bloomberg, the industry is rapidly evolving.
        """
    
    def test_pipeline_basic(self, sample_text):
        """Test basic pipeline execution."""
        # This is a placeholder for when API keys are available
        # Uncomment when running with proper credentials
        
        # from src.pipeline import BrandAnalysisPipeline
        # pipeline = BrandAnalysisPipeline(subject_brand="Tesla")
        # result = pipeline.analyze(sample_text)
        # assert result.subject_brand == "Tesla"
        # assert len(result.brands) > 0
        pass


def test_imports():
    """Test that all modules can be imported."""
    from src.agents.brand_extractor import BrandExtractorAgent
    from src.agents.citation_extractor import CitationExtractorAgent
    from src.agents.category_agent import CategoryAgent
    from src.agents.relationship_agent import RelationshipAgent
    from src.web_search.search_agent import WebSearchAgent
    from src.graphrag.neo4j_client import Neo4jClient
    from src.graphrag.graph_operations import GraphOperations
    from src.pipeline import BrandAnalysisPipeline
    
    # If we got here, all imports succeeded
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


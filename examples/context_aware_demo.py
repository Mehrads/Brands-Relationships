"""
Demonstration of Context-Aware Relationship Analysis

This example shows how the same companies can have different relationships
in different contexts - a key feature for nuanced brand analysis.
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import BrandAnalysisPipeline
from src.graphrag.neo4j_client import close_neo4j_client
from src.utils import setup_logging

logger = logging.getLogger(__name__)


def demonstrate_context_awareness():
    """Show how relationships change based on context."""
    
    logger.info("=" * 80)
    logger.info("CONTEXT-AWARE RELATIONSHIP ANALYSIS DEMO")
    logger.info("=" * 80)
    
    # Example 1: Apple & Samsung - Different contexts
    logger.info("\nEXAMPLE 1: Apple & Samsung - Multi-Context Relationship")
    logger.info("-" * 80)
    
    # Context 1: Consumer Market Competition
    text1 = """
    In the latest smartphone market analysis, Apple and Samsung continue their fierce
    rivalry in the premium smartphone segment. Apple's iPhone 15 directly competes
    with Samsung's Galaxy S24 series for market share among high-end consumers.
    Industry analysts note that both companies are fighting for the same customer base.
    """
    
    logger.info("\nText 1 (Consumer Market Context):")
    logger.info(text1.strip())
    
    pipeline = BrandAnalysisPipeline(subject_brand="Apple")
    result1 = pipeline.analyze(text1)
    
    logger.info("\n📊 Relationship Found:")
    for rel in result1.relationships:
        if rel.target == "Samsung":
            logger.info(f"  Type: {rel.relationship_type.value}")
            logger.info(f"  Context: {rel.relationship_context}")
            logger.info(f"  Sentiment: {rel.sentiment}")
            logger.info(f"  Confidence: {rel.confidence:.2f}")
            logger.info(f"  Evidence: {rel.evidence[:100]}...")
    
    # Context 2: Supply Chain Partnership
    text2 = """
    Apple relies on Samsung as a key supplier for OLED display panels and NAND flash
    memory chips. According to supply chain reports, Samsung's semiconductor division
    is a critical partner in Apple's component sourcing strategy. The partnership
    ensures Apple has access to cutting-edge display technology for its devices.
    """
    
    logger.info("\nText 2 (Supply Chain Context):")
    logger.info(text2.strip())
    
    result2 = pipeline.analyze(text2)
    
    logger.info("\n📊 Relationship Found:")
    for rel in result2.relationships:
        if rel.target == "Samsung":
            logger.info(f"  Type: {rel.relationship_type.value}")
            logger.info(f"  Context: {rel.relationship_context}")
            logger.info(f"  Sentiment: {rel.sentiment}")
            logger.info(f"  Confidence: {rel.confidence:.2f}")
            logger.info(f"  Evidence: {rel.evidence[:100]}...")
    
    logger.info("\n" + "=" * 80)
    logger.info("KEY INSIGHT: Same companies, different relationships in different contexts!")
    logger.info("=" * 80)
    
    # Example 2: Microsoft & Amazon
    logger.info("\nEXAMPLE 2: Microsoft & Amazon - Multi-Context Relationship")
    logger.info("-" * 80)
    
    # Context 1: Cloud Computing Competition
    text3 = """
    Microsoft Azure and Amazon Web Services (AWS) are locked in intense competition
    for the cloud computing market. Both companies are vying for enterprise customers,
    with AWS holding market leadership while Microsoft Azure rapidly gains ground.
    """
    
    logger.info("\nText 3 (Cloud Computing Context):")
    logger.info(text3.strip())
    
    pipeline2 = BrandAnalysisPipeline(subject_brand="Microsoft")
    result3 = pipeline2.analyze(text3)
    
    logger.info("\n📊 Relationship Found:")
    for rel in result3.relationships:
        if "Amazon" in rel.target:
            logger.info(f"  Type: {rel.relationship_type.value}")
            logger.info(f"  Context: {rel.relationship_context}")
            logger.info(f"  Sentiment: {rel.sentiment}")
            logger.info(f"  Confidence: {rel.confidence:.2f}")
    
    # Context 2: Enterprise Software Partnership
    text4 = """
    Microsoft and Amazon announced a partnership to integrate Microsoft 365 
    productivity tools with Amazon's Alexa for Business platform. The collaboration
    enables enterprise customers to use voice commands for Microsoft applications,
    combining strengths from both technology leaders.
    """
    
    logger.info("\nText 4 (Enterprise Software Context):")
    logger.info(text4.strip())
    
    result4 = pipeline2.analyze(text4)
    
    logger.info("\n📊 Relationship Found:")
    for rel in result4.relationships:
        if "Amazon" in rel.target:
            logger.info(f"  Type: {rel.relationship_type.value}")
            logger.info(f"  Context: {rel.relationship_context}")
            logger.info(f"  Sentiment: {rel.sentiment}")
            logger.info(f"  Confidence: {rel.confidence:.2f}")
    
    # Show Graph Summary
    logger.info("\n" + "=" * 80)
    logger.info("NEO4J GRAPH SUMMARY")
    logger.info("=" * 80)
    logger.info("\nThe graph now contains MULTIPLE relationships between the same companies,")
    logger.info("each stored with its specific context. This allows for nuanced analysis:")
    logger.info("\n• Apple → Samsung (competitor) in 'consumer_smartphones' context")
    logger.info("• Apple → Samsung (supplier) in 'component_supply_chain' context")
    logger.info("• Microsoft → Amazon (competitor) in 'cloud_computing' context")
    logger.info("• Microsoft → Amazon (partner) in 'enterprise_software' context")
    
    logger.info("\n💡 BENEFIT: Future queries will retrieve context-specific relationships,")
    logger.info("   enabling accurate analysis regardless of the discussion context!")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ Context-Aware Analysis Complete!")
    logger.info("=" * 80)


def show_visualization_tip():
    """Show how to visualize context-aware relationships."""
    logger.info("\n" + "=" * 80)
    logger.info("VISUALIZATION TIP")
    logger.info("=" * 80)
    logger.info("\nTo visualize these context-aware relationships:")
    logger.info("\n1. View all relationships:")
    logger.info("   python main.py visualize")
    logger.info("\n2. Filter by specific context in Neo4j Browser:")
    logger.info("   Visit: https://console.neo4j.io/")
    logger.info("   Query: MATCH (a)-[r:RELATES_TO {relationship_context: 'consumer_smartphones'}]->(b)")
    logger.info("          RETURN a, r, b")
    logger.info("\n3. Compare different contexts:")
    logger.info("   Find all Apple-Samsung relationships across contexts")
    logger.info("   Query: MATCH (a:Brand {name: 'Apple'})-[r:RELATES_TO]->(b:Brand {name: 'Samsung'})")
    logger.info("          RETURN r.relationship_type, r.relationship_context, r.sentiment")
    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    setup_logging("INFO")
    try:
        demonstrate_context_awareness()
        show_visualization_tip()
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        close_neo4j_client()


"""
Example usage of the brand analysis pipeline.
"""
import sys
import os
import json
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import BrandAnalysisPipeline
from src.graphrag.neo4j_client import close_neo4j_client
from src.utils import setup_logging

logger = logging.getLogger(__name__)


def example_1_automotive():
    """Example: Automotive industry analysis."""
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 1: Automotive Industry - Tesla Analysis")
    logger.info("=" * 80)
    
    text = """
    Tesla announced a new partnership with Panasonic to expand battery production 
    capacity at Gigafactory Nevada. This collaboration strengthens their existing 
    relationship in the electric vehicle battery space.
    
    Meanwhile, Rivian continues to compete aggressively in the EV pickup truck 
    market, positioning itself as a direct competitor to Tesla's Cybertruck.
    
    According to a Reuters report published last week, Ford has invested heavily 
    in electric vehicle technology and is partnering with SK Innovation for battery 
    supply. Industry analysts suggest Ford is catching up to Tesla in the EV race.
    
    General Motors announced they will source battery components from LG Energy 
    Solution, marking a significant partnership in their electric vehicle strategy.
    """
    
    pipeline = BrandAnalysisPipeline(subject_brand="Tesla")
    result = pipeline.analyze(text)
    
    print_results(result)
    return result


def example_2_technology():
    """Example: Technology industry analysis."""
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 2: Technology Industry - Microsoft Analysis")
    logger.info("=" * 80)
    
    text = """
    Microsoft expanded its partnership with OpenAI with a reported $10 billion 
    investment, according to Bloomberg sources. This strengthens Microsoft's 
    position in the AI race against competitors.
    
    Google, a key competitor in the cloud and AI space, recently launched Bard 
    to compete with OpenAI's ChatGPT. The rivalry between Microsoft and Google 
    in AI has intensified significantly.
    
    Amazon Web Services remains a major competitor to Microsoft Azure in the 
    cloud computing market. A recent Gartner report shows both companies 
    competing for enterprise cloud customers.
    
    Nvidia supplies GPUs to Microsoft for AI training, making them a critical 
    supplier in Microsoft's AI infrastructure strategy.
    """
    
    pipeline = BrandAnalysisPipeline(subject_brand="Microsoft")
    result = pipeline.analyze(text)
    
    print_results(result)
    return result


def example_3_finance():
    """Example: Finance industry analysis."""
    logger.info("\n" + "=" * 80)
    logger.info("EXAMPLE 3: Finance Industry - JPMorgan Analysis")
    logger.info("=" * 80)
    
    text = """
    JPMorgan Chase announced a strategic partnership with Visa to enhance digital 
    payment capabilities. The collaboration will integrate advanced fraud detection 
    systems across JPMorgan's retail banking network.
    
    Goldman Sachs continues to compete with JPMorgan in the investment banking 
    sector, particularly for major M&A deals. A Wall Street Journal report 
    indicates fierce competition between the two banks.
    
    Mastercard also partners with JPMorgan for payment processing services, 
    creating a complex network of relationships in the payments ecosystem.
    
    Bank of America, another major competitor, recently announced they are 
    expanding their wealth management division to compete more directly with 
    JPMorgan's private banking services.
    """
    
    pipeline = BrandAnalysisPipeline(subject_brand="JPMorgan")
    result = pipeline.analyze(text)
    
    print_results(result)
    return result


def print_results(result):
    """Print analysis results in a readable format."""
    logger.info(f"\nSubject Brand: {result.subject_brand}")
    logger.info(f"Category: {result.category}\n")
    
    logger.info("BRANDS FOUND:")
    logger.info("-" * 40)
    for brand in result.brands:
        logger.info(f"  • {brand.name} ({brand.mentions} mentions)")
    logger.info("")
    
    logger.info("RELATIONSHIPS:")
    logger.info("-" * 40)
    for rel in result.relationships:
        flag = "⚠️ " if rel.flagged else "✓ "
        logger.info(f"{flag}{rel.source} --[{rel.relationship_type.value}]--> {rel.target}")
        logger.info(f"   Confidence: {rel.confidence:.2f} | Source: {rel.source_type.value}")
        logger.info(f"   Evidence: {rel.evidence[:100]}...")
        logger.info("")
    
    logger.info("CITATIONS:")
    logger.info("-" * 40)
    for citation in result.citations:
        logger.info(f"  • {citation.source} ({citation.citation_type.value})")
        logger.info(f"    \"{citation.text[:80]}...\"")
        logger.info("")
    
    if result.flagged_items:
        logger.info("⚠️  FLAGGED FOR REVIEW:")
        logger.info("-" * 40)
        for item in result.flagged_items:
            logger.info(f"  • {item.item}: {item.reason}")
        logger.info("")


def main():
    """Run all examples."""
    setup_logging("INFO")
    
    try:
        # Run examples
        example_1_automotive()
        example_2_technology()
        example_3_finance()
        
        # Show final graph stats
        logger.info("\n" + "=" * 80)
        logger.info("FINAL GRAPH STATISTICS")
        logger.info("=" * 80)
        
        from src.graphrag.neo4j_client import get_neo4j_client
        client = get_neo4j_client()
        stats = client.get_stats()
        
        logger.info(f"\nTotal brands in graph: {stats['brands']}")
        logger.info(f"Total relationships in graph: {stats['relationships']}")
        
        logger.info("\n✓ All examples completed!")
        logger.info("Run 'python main.py visualize' to see the graph visualization\n")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        close_neo4j_client()


if __name__ == "__main__":
    main()


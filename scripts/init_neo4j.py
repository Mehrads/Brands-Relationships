"""
Initialize Neo4j database with schema and constraints.
"""
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graphrag.neo4j_client import get_neo4j_client, close_neo4j_client
from src.utils import setup_logging

logger = logging.getLogger(__name__)


def main():
    """Initialize Neo4j database."""
    setup_logging("INFO")
    
    logger.info("Initializing Neo4j database...")
    logger.info("-" * 50)
    
    try:
        # Get client
        client = get_neo4j_client()
        
        # Create constraints and indexes
        logger.info("\nCreating constraints and indexes...")
        client.create_constraints()
        
        # Get stats
        stats = client.get_stats()
        logger.info("\nDatabase initialized successfully!")
        logger.info("Current stats:")
        logger.info(f"  - Brands: {stats['brands']}")
        logger.info(f"  - Relationships: {stats['relationships']}")
        
        logger.info("\n✓ Neo4j is ready to use!")
        
    except Exception as e:
        logger.error(f"\n✗ Error: {e}")
        logger.error("\nMake sure Neo4j is running and credentials are correct in .env file")
        sys.exit(1)
    finally:
        close_neo4j_client()


if __name__ == "__main__":
    main()


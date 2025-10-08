"""
Command-line interface for the brand analysis pipeline.
"""
import argparse
import json
import sys
import logging
from pathlib import Path

from src.pipeline import BrandAnalysisPipeline
from src.graphrag.neo4j_client import close_neo4j_client
from src.config import settings

logger = logging.getLogger(__name__)


def analyze_command(args):
    """Execute analysis command."""
    # Read input text
    if args.input:
        with open(args.input, 'r') as f:
            text = f.read()
    else:
        logger.info("Enter text to analyze (Ctrl+D when done):")
        text = sys.stdin.read()
    
    # Initialize pipeline
    pipeline = BrandAnalysisPipeline(
        subject_brand=args.subject_brand,
        log_level=args.log_level
    )
    
    # Run analysis
    result = pipeline.analyze(text)
    
    # Format output
    output_data = result.model_dump()
    
    # Save or print
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        logger.info(f"\n✓ Results saved to {args.output}")
    else:
        logger.info("\n" + "=" * 80)
        logger.info("ANALYSIS RESULTS")
        logger.info("=" * 80 + "\n")
        logger.info(json.dumps(output_data, indent=2, default=str))
    
    # Print summary
    logger.info("\n" + "-" * 80)
    logger.info("SUMMARY")
    logger.info("-" * 80)
    logger.info(f"Subject Brand: {result.subject_brand}")
    logger.info(f"Category: {result.category}")
    logger.info(f"Brands Found: {len(result.brands)}")
    logger.info(f"Relationships: {len(result.relationships)}")
    logger.info(f"Citations: {len(result.citations)}")
    logger.info(f"Flagged Items: {len(result.flagged_items)}")
    
    if result.flagged_items:
        logger.info("\n⚠️  FLAGGED FOR REVIEW:")
        for item in result.flagged_items:
            logger.info(f"  - {item.item}: {item.reason}")
    
    logger.info("")


def visualize_command(args):
    """Execute visualization command."""
    from scripts.visualize_graph import main as viz_main
    # Pass args to visualization script
    sys.argv = ['visualize']
    if args.category:
        sys.argv.extend(['--category', args.category])
    if args.output:
        sys.argv.extend(['--output', args.output])
    if args.text_only:
        sys.argv.append('--text-only')
    
    viz_main()


def stats_command(args):
    """Show GraphRAG statistics."""
    from src.graphrag.neo4j_client import get_neo4j_client
    
    client = get_neo4j_client()
    stats = client.get_stats()
    
    logger.info("\n" + "=" * 80)
    logger.info("GRAPHRAG STATISTICS")
    logger.info("=" * 80 + "\n")
    logger.info(f"Brands in graph: {stats['brands']}")
    logger.info(f"Relationships in graph: {stats['relationships']}")
    logger.info("")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Brand & Citation Analysis Pipeline with GraphRAG"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze text for brands and relationships')
    analyze_parser.add_argument('--input', '-i', help='Input text file')
    analyze_parser.add_argument('--subject-brand', '-s', required=True, help='Subject brand name')
    analyze_parser.add_argument('--output', '-o', help='Output JSON file')
    analyze_parser.add_argument('--log-level', default='INFO', 
                               choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                               help='Logging level')
    
    # Visualize command
    viz_parser = subparsers.add_parser('visualize', help='Visualize relationship graph')
    viz_parser.add_argument('--category', '-c', help='Filter by category')
    viz_parser.add_argument('--output', '-o', default='graph.html', help='Output HTML file')
    viz_parser.add_argument('--text-only', '-t', action='store_true', help='Text-only visualization')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show GraphRAG statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'analyze':
            analyze_command(args)
        elif args.command == 'visualize':
            visualize_command(args)
        elif args.command == 'stats':
            stats_command(args)
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\nError: {e}")
        sys.exit(1)
    finally:
        close_neo4j_client()


if __name__ == "__main__":
    main()


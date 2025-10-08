"""
Visualize brand relationship graph.
"""
import sys
import os
import argparse
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.graphrag.graph_operations import GraphOperations
from src.graphrag.neo4j_client import close_neo4j_client
from src.utils import setup_logging

logger = logging.getLogger(__name__)

try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False


def visualize_with_pyvis(graph_data: dict, output_file: str = "graph.html"):
    """
    Create interactive visualization using pyvis.
    
    Args:
        graph_data: Graph data with nodes and edges
        output_file: Output HTML file
    """
    if not PYVIS_AVAILABLE:
        logger.error("Error: pyvis not installed. Run: pip install pyvis")
        return
    
    net = Network(height="750px", width="100%", directed=True, notebook=False)
    
    # Color mapping for relationship types
    color_map = {
        "competitor": "#FF6B6B",
        "partner": "#4ECDC4",
        "customer": "#45B7D1",
        "supplier": "#FFA07A",
        "subsidiary": "#98D8C8",
        "parent": "#F7DC6F",
        "investor": "#BB8FCE",
        "neutral": "#AAB7B8",
        "unknown": "#808080"
    }
    
    # Add nodes
    for node in graph_data["nodes"]:
        net.add_node(node["id"], label=node["label"], title=node["label"])
    
    # Add edges
    for edge in graph_data["edges"]:
        color = color_map.get(edge["type"], "#808080")
        net.add_edge(
            edge["source"],
            edge["target"],
            label=edge["type"],
            color=color,
            title=f"{edge['type']} ({edge['category']})"
        )
    
    # Configure physics
    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -30000,
          "centralGravity": 0.3,
          "springLength": 200
        }
      },
      "edges": {
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.5
          }
        },
        "smooth": {
          "type": "continuous"
        }
      }
    }
    """)
    
    net.save_graph(output_file)
    logger.info(f"✓ Visualization saved to {output_file}")
    logger.info(f"  Open this file in a web browser to view the graph")


def print_text_visualization(graph_data: dict):
    """Print text-based graph visualization."""
    logger.info("\n" + "=" * 80)
    logger.info("BRAND RELATIONSHIP GRAPH")
    logger.info("=" * 80)
    
    logger.info(f"\nNodes: {len(graph_data['nodes'])}")
    logger.info(f"Edges: {len(graph_data['edges'])}\n")
    
    # Group by category
    by_category = {}
    for edge in graph_data["edges"]:
        cat = edge["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(edge)
    
    for category, edges in by_category.items():
        logger.info(f"\n{category.upper()}")
        logger.info("-" * len(category))
        for edge in edges:
            logger.info(f"  {edge['source']} --[{edge['type']}]--> {edge['target']}")
    
    logger.info("\n" + "=" * 80)


def main():
    """Main visualization function."""
    parser = argparse.ArgumentParser(description="Visualize brand relationship graph")
    parser.add_argument("--category", "-c", help="Filter by category")
    parser.add_argument("--output", "-o", default="graph.html", help="Output file for interactive visualization")
    parser.add_argument("--text-only", "-t", action="store_true", help="Text-only visualization")
    
    args = parser.parse_args()
    
    setup_logging("INFO")
    
    try:
        graph_ops = GraphOperations()
        graph_data = graph_ops.get_graph_data(category=args.category)
        
        if not graph_data["nodes"]:
            logger.warning("No graph data found. Analyze some text first!")
            sys.exit(1)
        
        # Text visualization
        print_text_visualization(graph_data)
        
        # Interactive visualization
        if not args.text_only:
            visualize_with_pyvis(graph_data, args.output)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    finally:
        close_neo4j_client()


if __name__ == "__main__":
    main()


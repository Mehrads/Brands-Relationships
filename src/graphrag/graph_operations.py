"""
Graph operations for brand relationships.
"""
import logging
from typing import Optional, List, Dict, Any

from .neo4j_client import get_neo4j_client
from ..models import GraphNode, GraphEdge, Relationship, RelationshipType


logger = logging.getLogger(__name__)


class GraphOperations:
    """Operations for managing brand relationship graph."""
    
    def __init__(self):
        """Initialize graph operations."""
        self.client = get_neo4j_client()
    
    def create_brand_node(self, brand_name: str, properties: Dict[str, Any] = None) -> bool:
        """
        Create or update a brand node.
        
        Args:
            brand_name: Brand name (unique identifier)
            properties: Additional node properties
            
        Returns:
            True if successful
        """
        properties = properties or {}
        
        query = """
        MERGE (b:Brand {name: $name})
        SET b += $properties
        SET b.updated_at = datetime()
        RETURN b
        """
        
        try:
            self.client.execute_write(
                query,
                {"name": brand_name, "properties": properties}
            )
            logger.info(f"Created/updated brand node: {brand_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create brand node: {e}")
            return False
    
    def create_relationship(
        self,
        source_brand: str,
        target_brand: str,
        relationship_type: str,
        category: str,
        relationship_context: str,
        properties: Dict[str, Any] = None
    ) -> bool:
        """
        Create or update a relationship between brands.
        
        Args:
            source_brand: Source brand name
            target_brand: Target brand name
            relationship_type: Type of relationship
            category: Business category context
            relationship_context: Specific context/subcategory
            properties: Additional edge properties
            
        Returns:
            True if successful
        """
        properties = properties or {}
        
        # First ensure both nodes exist
        self.create_brand_node(source_brand)
        self.create_brand_node(target_brand)
        
        # Use category + context as unique key for relationships
        query = """
        MATCH (source:Brand {name: $source})
        MATCH (target:Brand {name: $target})
        MERGE (source)-[r:RELATES_TO {category: $category, relationship_context: $context}]->(target)
        SET r.relationship_type = $rel_type
        SET r += $properties
        SET r.updated_at = datetime()
        RETURN r
        """
        
        try:
            self.client.execute_write(
                query,
                {
                    "source": source_brand,
                    "target": target_brand,
                    "category": category,
                    "context": relationship_context,
                    "rel_type": relationship_type,
                    "properties": properties
                }
            )
            logger.info(f"Created/updated relationship: {source_brand} -[{relationship_type}]-> {target_brand} ({category}/{relationship_context})")
            return True
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            return False
    
    def get_relationship(
        self,
        source_brand: str,
        target_brand: str,
        category: Optional[str] = None,
        relationship_context: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get relationship between two brands.
        
        Args:
            source_brand: Source brand name
            target_brand: Target brand name
            category: Optional category filter
            relationship_context: Optional context filter
            
        Returns:
            Relationship data or None if not found
        """
        if category and relationship_context:
            # Exact match with category and context
            query = """
            MATCH (source:Brand {name: $source})-[r:RELATES_TO {category: $category, relationship_context: $context}]->(target:Brand {name: $target})
            RETURN r.relationship_type as relationship_type, 
                   r.category as category,
                   r.relationship_context as relationship_context,
                   properties(r) as properties
            """
            params = {"source": source_brand, "target": target_brand, "category": category, "context": relationship_context}
        elif category:
            # All relationships in this category
            query = """
            MATCH (source:Brand {name: $source})-[r:RELATES_TO {category: $category}]->(target:Brand {name: $target})
            RETURN r.relationship_type as relationship_type,
                   r.category as category,
                   r.relationship_context as relationship_context,
                   properties(r) as properties
            ORDER BY r.updated_at DESC
            """
            params = {"source": source_brand, "target": target_brand, "category": category}
        else:
            # Any relationship
            query = """
            MATCH (source:Brand {name: $source})-[r:RELATES_TO]->(target:Brand {name: $target})
            RETURN r.relationship_type as relationship_type,
                   r.category as category,
                   r.relationship_context as relationship_context,
                   properties(r) as properties
            ORDER BY r.updated_at DESC
            LIMIT 1
            """
            params = {"source": source_brand, "target": target_brand}
        
        try:
            results = self.client.execute_query(query, params)
            if results:
                return results[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get relationship: {e}")
            return None
    
    def get_all_relationships_for_brand(
        self,
        brand_name: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships for a brand.
        
        Args:
            brand_name: Brand name
            category: Optional category filter
            
        Returns:
            List of relationships
        """
        if category:
            query = """
            MATCH (b:Brand {name: $brand})-[r:RELATES_TO {category: $category}]-(other:Brand)
            RETURN b.name as source,
                   other.name as target,
                   r.relationship_type as relationship_type,
                   r.category as category,
                   properties(r) as properties
            """
            params = {"brand": brand_name, "category": category}
        else:
            query = """
            MATCH (b:Brand {name: $brand})-[r:RELATES_TO]-(other:Brand)
            RETURN b.name as source,
                   other.name as target,
                   r.relationship_type as relationship_type,
                   r.category as category,
                   properties(r) as properties
            """
            params = {"brand": brand_name}
        
        try:
            return self.client.execute_query(query, params)
        except Exception as e:
            logger.error(f"Failed to get relationships for brand: {e}")
            return []
    
    def get_brands_by_category(self, category: str) -> List[str]:
        """
        Get all brands in a category.
        
        Args:
            category: Business category
            
        Returns:
            List of brand names
        """
        query = """
        MATCH (b:Brand)-[r:RELATES_TO {category: $category}]-()
        RETURN DISTINCT b.name as name
        """
        
        try:
            results = self.client.execute_query(query, {"category": category})
            return [r["name"] for r in results]
        except Exception as e:
            logger.error(f"Failed to get brands by category: {e}")
            return []
    
    def relationship_exists(
        self,
        source_brand: str,
        target_brand: str,
        category: Optional[str] = None
    ) -> bool:
        """
        Check if relationship exists.
        
        Args:
            source_brand: Source brand name
            target_brand: Target brand name
            category: Optional category filter
            
        Returns:
            True if relationship exists
        """
        return self.get_relationship(source_brand, target_brand, category) is not None
    
    def get_graph_data(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get graph data for visualization.
        
        Args:
            category: Optional category filter
            
        Returns:
            Graph data with nodes and edges
        """
        if category:
            query = """
            MATCH (source:Brand)-[r:RELATES_TO {category: $category}]->(target:Brand)
            RETURN source.name as source,
                   target.name as target,
                   r.relationship_type as relationship_type,
                   r.category as category
            """
            params = {"category": category}
        else:
            query = """
            MATCH (source:Brand)-[r:RELATES_TO]->(target:Brand)
            RETURN source.name as source,
                   target.name as target,
                   r.relationship_type as relationship_type,
                   r.category as category
            LIMIT 1000
            """
            params = {}
        
        try:
            relationships = self.client.execute_query(query, params)
            
            # Extract unique nodes
            nodes = set()
            edges = []
            
            for rel in relationships:
                nodes.add(rel["source"])
                nodes.add(rel["target"])
                edges.append({
                    "source": rel["source"],
                    "target": rel["target"],
                    "type": rel["relationship_type"],
                    "category": rel["category"]
                })
            
            return {
                "nodes": [{"id": node, "label": node} for node in nodes],
                "edges": edges
            }
        except Exception as e:
            logger.error(f"Failed to get graph data: {e}")
            return {"nodes": [], "edges": []}
    
    def store_relationship_from_model(self, relationship: Relationship) -> bool:
        """
        Store a relationship from the Relationship model.
        
        Args:
            relationship: Relationship model instance
            
        Returns:
            True if successful
        """
        properties = {
            "confidence": relationship.confidence,
            "evidence": relationship.evidence,
            "source_type": relationship.source_type.value,
            "flagged": relationship.flagged
        }
        
        if relationship.reasoning:
            properties["reasoning"] = relationship.reasoning
        
        if relationship.sentiment:
            properties["sentiment"] = relationship.sentiment
        
        return self.create_relationship(
            source_brand=relationship.source,
            target_brand=relationship.target,
            relationship_type=relationship.relationship_type.value,
            category=relationship.category,
            relationship_context=relationship.relationship_context,
            properties=properties
        )


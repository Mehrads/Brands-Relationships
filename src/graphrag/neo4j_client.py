"""
Neo4j database client for GraphRAG.
"""
import logging
from typing import Optional, List, Dict, Any
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

from ..config import settings


logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j database client."""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        Initialize Neo4j client.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except AuthError:
            logger.error("Neo4j authentication failed")
            raise
        except ServiceUnavailable:
            logger.error(f"Neo4j service unavailable at {self.uri}")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records as dictionaries
        """
        parameters = parameters or {}
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            raise
    
    def execute_write(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a write transaction.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records as dictionaries
        """
        parameters = parameters or {}
        
        def _tx_function(tx):
            result = tx.run(query, parameters)
            return [dict(record) for record in result]
        
        try:
            with self.driver.session() as session:
                return session.execute_write(_tx_function)
        except Exception as e:
            logger.error(f"Write transaction failed: {e}")
            logger.error(f"Query: {query}")
            raise
    
    def create_constraints(self):
        """Create database constraints and indexes."""
        constraints = [
            # Unique constraint on Brand name
            "CREATE CONSTRAINT brand_name_unique IF NOT EXISTS FOR (b:Brand) REQUIRE b.name IS UNIQUE",
            # Index on category for faster lookups
            "CREATE INDEX relationship_category IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.category)",
        ]
        
        for constraint in constraints:
            try:
                self.execute_write(constraint)
                logger.info(f"Created constraint/index: {constraint}")
            except Exception as e:
                logger.warning(f"Constraint/index creation failed (may already exist): {e}")
    
    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)."""
        query = "MATCH (n) DETACH DELETE n"
        self.execute_write(query)
        logger.warning("Database cleared")
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        query = """
        MATCH (b:Brand)
        OPTIONAL MATCH ()-[r:RELATES_TO]->()
        RETURN count(DISTINCT b) as brand_count, count(DISTINCT r) as relationship_count
        """
        result = self.execute_query(query)
        if result:
            return {
                "brands": result[0].get("brand_count", 0),
                "relationships": result[0].get("relationship_count", 0)
            }
        return {"brands": 0, "relationships": 0}


# Singleton instance
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """Get or create Neo4j client singleton."""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    return _neo4j_client


def close_neo4j_client():
    """Close the Neo4j client singleton."""
    global _neo4j_client
    if _neo4j_client:
        _neo4j_client.close()
        _neo4j_client = None


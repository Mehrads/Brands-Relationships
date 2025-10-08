"""
FastAPI web service for the brand analysis pipeline.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

from src.pipeline import BrandAnalysisPipeline
from src.graphrag.neo4j_client import get_neo4j_client
from src.models import AnalysisResult


app = FastAPI(
    title="Brand Analysis Pipeline API",
    description="Multi-agent system for brand and citation analysis with GraphRAG",
    version="1.0.0"
)


class AnalysisRequest(BaseModel):
    """Request model for analysis."""
    text: str
    subject_brand: str


class VisualizationRequest(BaseModel):
    """Request model for graph visualization."""
    category: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Brand Analysis Pipeline API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze",
            "visualize": "/visualize",
            "stats": "/stats",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        client = get_neo4j_client()
        stats = client.get_stats()
        return {
            "status": "healthy",
            "neo4j": "connected",
            "graph_stats": stats
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    """
    Analyze text for brand mentions and relationships.
    
    Args:
        request: Analysis request with text and subject brand
        
    Returns:
        Analysis results
    """
    try:
        pipeline = BrandAnalysisPipeline(subject_brand=request.subject_brand)
        result = pipeline.analyze(request.text)
        
        return result.model_dump()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/visualize")
async def visualize(request: VisualizationRequest):
    """
    Get graph data for visualization.
    
    Args:
        request: Visualization request with optional category filter
        
    Returns:
        Graph data with nodes and edges
    """
    try:
        from src.graphrag.graph_operations import GraphOperations
        
        graph_ops = GraphOperations()
        graph_data = graph_ops.get_graph_data(category=request.category)
        
        return graph_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """
    Get GraphRAG statistics.
    
    Returns:
        Database statistics
    """
    try:
        client = get_neo4j_client()
        stats = client.get_stats()
        
        return {
            "brands": stats["brands"],
            "relationships": stats["relationships"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories")
async def get_categories():
    """
    Get all categories in the graph.
    
    Returns:
        List of categories
    """
    try:
        client = get_neo4j_client()
        
        query = """
        MATCH ()-[r:RELATES_TO]->()
        RETURN DISTINCT r.category as category
        ORDER BY category
        """
        
        results = client.execute_query(query)
        categories = [r["category"] for r in results if r.get("category")]
        
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


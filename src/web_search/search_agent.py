"""
Web Search Agent - Searches the web for brand relationship information.
"""
import logging
from typing import List, Optional
import time
import json

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    logging.warning("tavily-python not available")

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    logging.warning("duckduckgo-search not available")

from ..models import WebSearchResult
from ..config import settings


logger = logging.getLogger(__name__)


class WebSearchAgent:
    """Agent for searching the web for brand relationships."""
    
    def __init__(self, max_results: int = None):
        """
        Initialize web search agent.
        
        Args:
            max_results: Maximum number of search results
        """
        self.max_results = max_results or settings.max_web_search_results
    
    def search_brand_relationship(
        self,
        brand1: str,
        brand2: str,
        category: Optional[str] = None
    ) -> List[WebSearchResult]:
        """
        Search for information about relationship between two brands.
        
        Args:
            brand1: First brand name
            brand2: Second brand name
            category: Optional category context
            
        Returns:
            List of search results
        """
        # Construct search query
        query = f'"{brand1}" "{brand2}" relationship'
        if category:
            category_keywords = category.replace("_", " ").replace("/", " ")
            query += f" {category_keywords}"
        
        logger.info(f"Searching web for: {query}")
        
        return self._perform_search(query)
    
    def search_brand_info(self, brand: str) -> List[WebSearchResult]:
        """
        Search for general information about a brand.
        
        Args:
            brand: Brand name
            
        Returns:
            List of search results
        """
        query = f'"{brand}" company business'
        logger.info(f"Searching web for: {query}")
        
        return self._perform_search(query)
    
    def _perform_search(self, query: str) -> List[WebSearchResult]:
        """
        Perform the actual web search.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        results = []
        
        # Try Tavily first (best for this use case)
        if TAVILY_AVAILABLE and settings.tavily_api_key:
            results = self._tavily_search(query)
        # Fallback to DuckDuckGo
        elif DDGS_AVAILABLE:
            results = self._ddgs_search(query)
        
        return results[:self.max_results]
    
    def _tavily_search(self, query: str) -> List[WebSearchResult]:
        """
        Perform Tavily search (AI-optimized search).
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        results = []
        
        try:
            client = TavilyClient(api_key=settings.tavily_api_key)
            search_results = client.search(
                query=query,
                max_results=self.max_results,
                search_depth="advanced"  # More comprehensive results
            )
            
            for result in search_results.get("results", []):
                results.append(WebSearchResult(
                    title=result.get("title", ""),
                    snippet=result.get("content", ""),
                    url=result.get("url", ""),
                    source=self._extract_domain(result.get("url", ""))
                ))
                    
            logger.info(f"Found {len(results)} results from Tavily")
            
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
        
        return results
    
    def _ddgs_search(self, query: str) -> List[WebSearchResult]:
        """
        Perform DuckDuckGo search.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        results = []
        
        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=self.max_results)
                
                for result in search_results:
                    results.append(WebSearchResult(
                        title=result.get("title", ""),
                        snippet=result.get("body", ""),
                        url=result.get("href", ""),
                        source=self._extract_domain(result.get("href", ""))
                    ))
                    
            logger.info(f"Found {len(results)} results from DuckDuckGo")
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
        
        return results
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except:
            return "unknown"
    
    def synthesize_results(self, results: List[WebSearchResult]) -> str:
        """
        Synthesize search results into a text summary.
        
        Args:
            results: List of search results
            
        Returns:
            Combined text summary
        """
        if not results:
            return "No search results found."
        
        synthesis = []
        for i, result in enumerate(results, 1):
            synthesis.append(f"[{i}] {result.title}")
            synthesis.append(f"    {result.snippet}")
            synthesis.append(f"    Source: {result.source} ({result.url})")
            synthesis.append("")
        
        return "\n".join(synthesis)


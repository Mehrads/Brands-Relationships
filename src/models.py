"""
Pydantic models for structured data validation across the pipeline.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class RelationshipType(str, Enum):
    """Types of brand relationships."""
    COMPETITOR = "competitor"
    PARTNER = "partner"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    SUBSIDIARY = "subsidiary"
    PARENT = "parent"
    INVESTOR = "investor"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class SourceType(str, Enum):
    """Source of relationship information."""
    GRAPH_DB = "graph_db"
    WEB_SEARCH = "web_search"
    LLM_INFERENCE = "llm_inference"


class CitationType(str, Enum):
    """Types of citations."""
    REPORT = "report"
    ARTICLE = "article"
    STATEMENT = "statement"
    STUDY = "study"
    CASE_STUDY = "case_study"
    WHITEPAPER = "whitepaper"
    ANNOUNCEMENT = "announcement"
    BLOG_POST = "blog_post"
    SOCIAL_MEDIA = "social_media"
    OTHER = "other"


class Brand(BaseModel):
    """Extracted brand information."""
    name: str = Field(..., description="Brand/company name")
    mentions: int = Field(default=1, description="Number of mentions in text")
    context: List[str] = Field(default_factory=list, description="Context snippets where brand appears")
    aliases: List[str] = Field(default_factory=list, description="Alternative names or abbreviations")


class Citation(BaseModel):
    """Citation or source information."""
    source: str = Field(..., description="Source name (e.g., Reuters, Bloomberg)")
    text: str = Field(..., description="Cited text or claim")
    citation_type: CitationType = Field(default=CitationType.OTHER, description="Type of citation")
    url: Optional[str] = Field(default=None, description="URL if available")
    date: Optional[str] = Field(default=None, description="Publication date if available")


class Relationship(BaseModel):
    """Brand relationship with metadata."""
    source: str = Field(..., description="Source brand")
    target: str = Field(..., description="Target brand")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    category: str = Field(..., description="Business category/industry context")
    relationship_context: str = Field(..., description="Specific context/subcategory of the relationship (e.g., 'consumer_market', 'supply_chain', 'r_and_d')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    evidence: str = Field(..., description="Supporting evidence from text")
    source_type: SourceType = Field(..., description="Where this relationship was found")
    flagged: bool = Field(default=False, description="Whether flagged for review")
    reasoning: Optional[str] = Field(default=None, description="LLM reasoning for the classification")
    sentiment: Optional[str] = Field(default=None, description="Sentiment of the relationship (positive, negative, neutral)")
    

class FlaggedItem(BaseModel):
    """Item flagged for human review."""
    item_type: Literal["relationship", "brand", "citation"] = Field(..., description="Type of flagged item")
    item: str = Field(..., description="Description of the item")
    reason: str = Field(..., description="Reason for flagging")
    confidence: Optional[float] = Field(default=None, description="Confidence score if applicable")
    requires_review: bool = Field(default=True, description="Whether human review is required")


class BrandExtractionOutput(BaseModel):
    """Output from brand extraction agent."""
    brands: List[Brand] = Field(default_factory=list, description="Extracted brands")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall extraction confidence")


class CitationExtractionOutput(BaseModel):
    """Output from citation extraction agent."""
    citations: List[Citation] = Field(default_factory=list, description="Extracted citations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall extraction confidence")


class CategoryOutput(BaseModel):
    """Output from category identification agent."""
    primary_category: str = Field(..., description="Primary category/industry")
    secondary_categories: List[str] = Field(default_factory=list, description="Related categories")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Category identification confidence")


class RelationshipOutput(BaseModel):
    """Output from relationship classification agent."""
    relationships: List[Relationship] = Field(default_factory=list, description="Classified relationships")


class WebSearchResult(BaseModel):
    """Web search result."""
    title: str = Field(..., description="Result title")
    snippet: str = Field(..., description="Result snippet")
    url: str = Field(..., description="Result URL")
    source: str = Field(..., description="Source website")


class AnalysisResult(BaseModel):
    """Final pipeline output."""
    subject_brand: str = Field(..., description="The subject brand being analyzed")
    category: str = Field(..., description="Primary category")
    brands: List[Brand] = Field(default_factory=list, description="All extracted brands")
    relationships: List[Relationship] = Field(default_factory=list, description="Brand relationships")
    citations: List[Citation] = Field(default_factory=list, description="Extracted citations")
    flagged_items: List[FlaggedItem] = Field(default_factory=list, description="Items flagged for review")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class GraphNode(BaseModel):
    """Neo4j graph node representation."""
    name: str = Field(..., description="Brand name (unique identifier)")
    label: str = Field(default="Brand", description="Node label")
    properties: dict = Field(default_factory=dict, description="Additional properties")


class GraphEdge(BaseModel):
    """Neo4j graph edge representation."""
    source: str = Field(..., description="Source node name")
    target: str = Field(..., description="Target node name")
    relationship_type: str = Field(..., description="Relationship type")
    category: str = Field(..., description="Category context")
    relationship_context: str = Field(..., description="Specific context/subcategory")
    properties: dict = Field(default_factory=dict, description="Edge properties")


"""
Configuration management for the pipeline.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # LLM Configuration
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_base_url: Optional[str] = os.getenv("OPENAI_BASE_URL")  # For OpenRouter or custom endpoints
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")  # openai or anthropic
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    
    # Neo4j Configuration
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # Web Search Configuration
    tavily_api_key: Optional[str] = os.getenv("TAVILY_API_KEY")
    serpapi_api_key: Optional[str] = os.getenv("SERPAPI_API_KEY")
    max_web_search_results: int = int(os.getenv("MAX_WEB_SEARCH_RESULTS", "5"))
    
    # Pipeline Configuration
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
    low_confidence_threshold: float = float(os.getenv("LOW_CONFIDENCE_THRESHOLD", "0.5"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


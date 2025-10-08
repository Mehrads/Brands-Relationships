"""
Utility functions for the pipeline.
"""
import logging
import json
import re
from typing import Any, Dict, List
from datetime import datetime
from urllib.parse import urlparse


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text.strip()


def extract_json_from_response(response: str) -> Dict[str, Any]:
    """Extract JSON from LLM response, handling markdown code blocks."""
    response = response.strip()
    
    # Remove markdown code blocks if present
    if response.startswith("```"):
        lines = response.split('\n')
        # Remove first line (```json or ```)
        lines = lines[1:]
        # Remove last line (```)
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        response = '\n'.join(lines)
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON: {e}")
        logging.error(f"Response: {response}")
        raise


def format_timestamp() -> str:
    """Get formatted timestamp."""
    return datetime.now().isoformat()


def calculate_confidence_average(confidences: list[float]) -> float:
    """Calculate average confidence score."""
    if not confidences:
        return 0.0
    return sum(confidences) / len(confidences)


def should_flag(confidence: float, threshold: float) -> bool:
    """Determine if an item should be flagged based on confidence."""
    return confidence < threshold


def normalize_brand_name(name: str) -> str:
    """
    Normalize brand name for consistent matching and deduplication.
    
    Examples:
    - "Meta Platforms, Inc." → "Meta"
    - "Apple Inc." → "Apple"
    - "Amazon Web Services" → "Amazon Web Services" (keep service names)
    """
    # Remove common suffixes
    suffixes = [
        ' Platforms, Inc.', ' Platforms Inc', ' Platforms',
        ' Inc.', ' Inc', 
        ' LLC', ' LLC.', ' L.L.C.', ' L.L.C',
        ' Corp.', ' Corp', ' Corporation',
        ' Ltd.', ' Ltd', ' Limited',
        ' Co.', ' Co', ' Company',
        ' S.A.', ' SA', ' S.A', ' PLC', ' Plc'
    ]
    
    normalized = name.strip()
    
    # Try suffixes from longest to shortest to avoid partial matches
    for suffix in sorted(suffixes, key=len, reverse=True):
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
            break  # Only remove one suffix
    
    # Special cases for well-known brands
    brand_mappings = {
        'Meta Platforms': 'Meta',
        'Alphabet Inc': 'Google',  # Alphabet is Google's parent
        'X (formerly Twitter)': 'X',
        'Twitter': 'X',
        'Amazon Web Services': 'AWS',
    }
    
    for variant, canonical in brand_mappings.items():
        if normalized.lower() == variant.lower():
            return canonical
    
    return normalized


def deduplicate_brands(brands: list) -> list:
    """
    Deduplicate brand list based on normalized names.
    Merges mentions and context for duplicate brands.
    """
    seen = {}
    result = []
    
    for brand in brands:
        normalized = normalize_brand_name(brand.name)
        key = normalized.lower()
        
        if key not in seen:
            # First occurrence - normalize the name
            brand.name = normalized
            seen[key] = len(result)
            result.append(brand)
        else:
            # Duplicate found - merge data
            existing_idx = seen[key]
            existing = result[existing_idx]
            existing.mentions += brand.mentions
            existing.context.extend(brand.context)
            # Merge aliases
            for alias in brand.aliases:
                if alias not in existing.aliases:
                    existing.aliases.append(alias)
            # Add original name as alias if different
            if brand.name != normalized:
                if brand.name not in existing.aliases:
                    existing.aliases.append(brand.name)
    
    return result


def extract_urls_from_text(text: str) -> List[str]:
    """
    Extract all URLs from text.
    
    Args:
        text: Input text
        
    Returns:
        List of URLs found
    """
    # URL regex pattern
    url_pattern = r'https?://[^\s\)"\']+'
    urls = re.findall(url_pattern, text)
    return urls


def extract_domain_from_url(url: str) -> str:
    """
    Extract domain name from URL.
    
    Args:
        url: Full URL
        
    Returns:
        Domain name
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return ""


def match_url_to_brand(url: str, brands: List[str]) -> str:
    """
    Match a URL to a brand name.
    
    Args:
        url: URL to match
        brands: List of brand names
        
    Returns:
        Matching brand name or empty string
    """
    domain = extract_domain_from_url(url).lower()
    
    for brand in brands:
        brand_lower = brand.lower().replace(' ', '')
        # Check if brand name appears in domain
        if brand_lower in domain or domain in brand_lower:
            return brand
    
    return ""


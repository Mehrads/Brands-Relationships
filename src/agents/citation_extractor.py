"""
Citation Extraction Agent - Extracts citations and sources from text.
"""
import logging
from typing import List
import re

from .base_agent import BaseAgent
from ..models import Citation, CitationExtractionOutput, CitationType
from ..utils import clean_text, extract_urls_from_text, extract_domain_from_url


logger = logging.getLogger(__name__)


class CitationExtractorAgent(BaseAgent):
    """Agent for extracting citations and sources from text."""
    
    SYSTEM_PROMPT = """You are an expert at identifying citations, sources, and references in text.
Your task is to extract all mentions of sources, reports, studies, articles, statements, and announcements.
Identify both explicit citations (e.g., "according to Reuters") and implicit references."""
    
    def run(self, text: str, extracted_brands: List[str] = None) -> CitationExtractionOutput:
        """
        Extract citations from text with URL association.
        
        Args:
            text: Input text to analyze
            extracted_brands: Optional list of already extracted brand names for URL matching
            
        Returns:
            CitationExtractionOutput with extracted citations
        """
        logger.info("Starting citation extraction...")
        
        cleaned_text = clean_text(text)
        
        # Extract URLs from text
        urls = extract_urls_from_text(text)
        logger.info(f"Found {len(urls)} URLs in text")
        
        # Create URL context map (URL -> surrounding text)
        url_contexts = {}
        for url in urls:
            # Find the sentence containing this URL
            pattern = r'([^.!?]*' + re.escape(url) + r'[^.!?]*[.!?])'
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                url_contexts[url] = matches[0].strip()
        
        # Build URL list string for the prompt
        urls_str = "\n".join([f"- {url}" for url in urls]) if urls else "No URLs found"
        
        prompt = f"""Extract all citations, sources, and references from the following text.

IMPORTANT: The text contains {len(urls)} URLs. Use these URLs to enrich the citations.

URLs found in text:
{urls_str}

For each citation found, provide:
- source: Name of the source (publication, organization, person, website)
- text: The actual claim or information being cited (keep it concise but informative)
- citation_type: Type (report, article, statement, study, case_study, whitepaper, announcement, blog_post, social_media, other)
- url: The associated URL if available (match from the URLs above)
- date: Publication date if mentioned (null if not available)

Text to analyze:
{cleaned_text}

Return your response as JSON in this exact format:
{{
    "citations": [
        {{
            "source": "Bloomberg",
            "text": "Apple is finalizing a partnership with OpenAI",
            "citation_type": "report",
            "url": "https://www.bloomberg.com/technology/apple-ai-deal-2025",
            "date": null
        }}
    ],
    "confidence": 0.95
}}

Guidelines:
- Match URLs to their corresponding claims
- Include the URL even if the source is mentioned by name
- For social media posts, use citation_type "social_media"
- For blog posts, use "blog_post"
- For case studies, use "case_study"  
- For whitepapers/PDFs, use "whitepaper"
- Be thorough - extract ALL citations including indirect references

Valid citation_type values: report, article, statement, study, case_study, whitepaper, announcement, blog_post, social_media, other
Confidence should be between 0 and 1.
"""
        
        try:
            response = self._call_llm(prompt, self.SYSTEM_PROMPT)
            data = self._parse_json_response(response)
            
            # Parse citations
            citations = []
            for citation_data in data.get("citations", []):
                # Convert citation_type string to enum
                ctype = citation_data.get("citation_type", "other")
                try:
                    citation_data["citation_type"] = CitationType(ctype)
                except ValueError:
                    logger.warning(f"Invalid citation type '{ctype}', using 'other'")
                    citation_data["citation_type"] = CitationType.OTHER
                
                citations.append(Citation(**citation_data))
            
            # If LLM missed some URLs, try to add them as citations
            llm_urls = {c.url for c in citations if c.url}
            for url in urls:
                if url not in llm_urls:
                    # Try to create a citation for this URL
                    domain = extract_domain_from_url(url)
                    source = domain.split('.')[0].title() if domain else "Unknown"
                    context = url_contexts.get(url, "URL reference")
                    
                    citations.append(Citation(
                        source=source,
                        text=context[:200],  # Limited context
                        citation_type=CitationType.OTHER,
                        url=url
                    ))
                    logger.debug(f"Added missing URL citation: {url}")
            
            confidence = data.get("confidence", 0.8)
            
            # Adjust confidence if we had to supplement URLs
            if len(citations) > len(data.get("citations", [])):
                confidence = min(confidence, 0.85)  # Slightly lower since we supplemented
            
            result = CitationExtractionOutput(
                citations=citations,
                confidence=confidence
            )
            
            logger.info(f"Extracted {len(result.citations)} citations with confidence {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Citation extraction failed: {e}")
            # Fallback: At least extract URLs
            citations = []
            for url in urls:
                domain = extract_domain_from_url(url)
                source = domain.split('.')[0].title() if domain else "Unknown"
                context = url_contexts.get(url, "URL reference")
                
                citations.append(Citation(
                    source=source,
                    text=context[:200],
                    citation_type=CitationType.OTHER,
                    url=url
                ))
            
            confidence = 0.5 if citations else 0.0
            return CitationExtractionOutput(citations=citations, confidence=confidence)


"""
Base agent class for all agents in the pipeline.
"""
import json
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from openai import OpenAI
from anthropic import Anthropic

from ..config import settings
from ..utils import extract_json_from_response


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, model: Optional[str] = None, temperature: float = 0.0):
        """
        Initialize base agent.
        
        Args:
            model: LLM model to use
            temperature: Temperature for LLM responses
        """
        self.model = model or settings.llm_model
        self.temperature = temperature
        self.provider = settings.llm_provider
        
        # Initialize LLM client
        if self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            # Support custom base URL (e.g., OpenRouter)
            client_kwargs = {"api_key": settings.openai_api_key}
            if settings.openai_base_url:
                client_kwargs["base_url"] = settings.openai_base_url
            self.client = OpenAI(**client_kwargs)
        elif self.provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            self.client = Anthropic(api_key=settings.anthropic_api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Call LLM with prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            LLM response text
        """
        try:
            if self.provider == "openai":
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
                
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=self.temperature,
                    system=system_prompt or "",
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        return extract_json_from_response(response)
    
    @abstractmethod
    def run(self, *args, **kwargs):
        """Execute the agent's main task."""
        pass


"""
LLM client for converting natural language to SQL queries.
Supports multiple LLM providers (OpenAI, Anthropic, local models via Ollama).
"""
import os
import json
from typing import Optional, Dict, Any
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class LLMClient:
    """Client for interacting with LLMs to generate SQL queries."""
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM client.
        
        Args:
            provider: LLM provider name (openai, anthropic, ollama)
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai").lower()
        self.api_key = os.getenv("LLM_API_KEY")
        self.model = os.getenv("LLM_MODEL", self._get_default_model())
        self.base_url = os.getenv("LLM_BASE_URL")
        
        if self.provider == LLMProvider.OPENAI:
            self._init_openai()
        elif self.provider == LLMProvider.ANTHROPIC:
            self._init_anthropic()
        elif self.provider == LLMProvider.OLLAMA:
            self._init_ollama()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _get_default_model(self) -> str:
        """Get default model for provider."""
        defaults = {
            LLMProvider.OPENAI: "gpt-4o-mini",
            LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
            LLMProvider.OLLAMA: "llama3.1"
        }
        return defaults.get(self.provider, "gpt-4o-mini")
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
    
    def _init_anthropic(self):
        """Initialize Anthropic client."""
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")
    
    def _init_ollama(self):
        """Initialize Ollama client."""
        try:
            from openai import OpenAI
            # Ollama uses OpenAI-compatible API
            base_url = self.base_url or "http://localhost:11434/v1"
            self.client = OpenAI(api_key="ollama", base_url=base_url)
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
    
    def generate_sql(
        self, 
        natural_language_query: str, 
        schema_context: str,
        examples: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Generate SQL query from natural language.
        
        Args:
            natural_language_query: User's natural language question
            schema_context: Database schema context
            examples: Optional few-shot examples
            
        Returns:
            Dictionary with 'sql' and 'explanation' keys
        """
        system_prompt = self._build_system_prompt(schema_context, examples)
        user_prompt = f"Convert this question to SQL: {natural_language_query}"
        
        if self.provider == LLMProvider.ANTHROPIC:
            return self._generate_anthropic(system_prompt, user_prompt)
        else:
            return self._generate_openai_compatible(system_prompt, user_prompt)
    
    def _build_system_prompt(self, schema_context: str, examples: Optional[list] = None) -> str:
        """Build system prompt with schema context."""
        prompt = """You are a SQL query generator. Convert natural language questions to PostgreSQL SQL queries.

Database Schema:
{schema}

Rules:
1. Only generate SELECT queries (read-only)
2. Use proper SQL syntax for PostgreSQL
3. Use table and column names exactly as shown in the schema
4. Return only the SQL query, no explanations in the query itself
5. Use parameterized queries where appropriate
6. Include proper JOINs when querying multiple tables

""".format(schema=schema_context)
        
        if examples:
            prompt += "\nExamples:\n"
            for example in examples:
                prompt += f"Q: {example['question']}\n"
                prompt += f"SQL: {example['sql']}\n\n"
        
        return prompt
    
    def _generate_openai_compatible(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Generate SQL using OpenAI-compatible API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistent SQL generation
            response_format={"type": "json_object"} if self.provider == LLMProvider.OLLAMA else None
        )
        
        content = response.choices[0].message.content
        
        # Try to parse as JSON first, otherwise treat as plain SQL
        try:
            result = json.loads(content)
            sql = result.get("sql", content)
            explanation = result.get("explanation", "")
        except json.JSONDecodeError:
            # If not JSON, assume the content is the SQL query
            sql = content.strip()
            explanation = ""
        
        return {
            "sql": sql,
            "explanation": explanation,
            "model": self.model,
            "provider": self.provider
        }
    
    def _generate_anthropic(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Generate SQL using Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        
        content = response.content[0].text
        
        # Try to parse as JSON first
        try:
            result = json.loads(content)
            sql = result.get("sql", content)
            explanation = result.get("explanation", "")
        except json.JSONDecodeError:
            sql = content.strip()
            explanation = ""
        
        return {
            "sql": sql,
            "explanation": explanation,
            "model": self.model,
            "provider": self.provider
        }

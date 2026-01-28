"""
LLM Analysis Engine.

Pluggable LLM providers for AI-powered log analysis:
- OpenAI
- Google Gemini
- Anthropic
- Groq
- OpenRouter
- Ollama (Local)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings, get_yaml_config
from app.models.log import LogFile, LogEntry


settings = get_settings()
yaml_config = get_yaml_config()


# Prompt templates for different analysis types
PROMPT_TEMPLATES = {
    "root_cause": """You are an expert Apache Spark engineer analyzing Spark application logs.

Analyze the following log entries and identify the root cause of any errors or issues.

## Log Entries:
{log_entries}

## Your Analysis Should Include:
1. **Root Cause**: What is the primary cause of the issue?
2. **Contributing Factors**: Any secondary issues that contributed
3. **Severity Assessment**: Rate severity (low/medium/high/critical)
4. **Evidence**: Point to specific log lines that support your analysis

Provide a clear, actionable analysis.""",

    "memory_issues": """You are an expert Apache Spark engineer specializing in memory optimization.

Analyze the following Spark logs for memory-related issues.

## Log Entries:
{log_entries}

## Analyze For:
1. **OutOfMemoryError occurrences**
2. **GC overhead issues**
3. **Memory pressure indicators**
4. **Executor memory problems**
5. **Driver memory issues**

## For Each Issue Provide:
- Description of the problem
- Root cause
- Recommended memory configuration changes
- Code optimization suggestions if applicable

Format your response as structured JSON.""",

    "performance": """You are an expert Apache Spark engineer specializing in performance tuning.

Analyze the following Spark logs for performance bottlenecks.

## Log Entries:
{log_entries}

## Analyze For:
1. **Shuffle operations** that are taking too long
2. **Data skew** indicators
3. **Serialization overhead**
4. **Task scheduling delays**
5. **Disk spills**
6. **Network bottlenecks**

## For Each Issue Provide:
- Description and location in logs
- Root cause analysis
- Performance impact estimate
- Optimization recommendations

Format your response as structured JSON.""",

    "config_optimization": """You are an expert Apache Spark engineer.

Based on the following Spark logs, recommend configuration optimizations.

## Log Entries:
{log_entries}

## Current Issues Detected:
{issues_summary}

## Provide Configuration Recommendations:
For each recommendation include:
- Configuration key (e.g., spark.executor.memory)
- Current value (if detectable, else null)
- Recommended value
- Reason for the change
- Expected impact (performance, stability, cost)

Focus on:
1. Memory settings
2. Shuffle settings
3. Parallelism settings
4. Serialization settings
5. Dynamic allocation settings

Format your response as JSON with a "config_suggestions" array.
Each object in "config_suggestions" MUST have these keys:
- config_key
- current_value
- suggested_value
- reason
- impact""",

    "full": """You are an expert Apache Spark engineer performing a comprehensive log analysis.

## Log Entries:
{log_entries}

## Provide a Complete Analysis:

### 1. Summary
Brief overview of the application's health and main issues.

### 2. Root Cause Analysis
For each error/issue found:
- What happened
- Why it happened
- Severity level

### 3. Recommendations
Prioritized list of actions to resolve issues.
Each recommendation MUST include:
- title: Short actionable title
- description: Detailed explanation
- priority: "low", "medium", "high", or "critical" (lowercase)
- category: Type of issue (e.g., "memory", "network", "code")

### 4. Spark Configuration Suggestions
Specific configuration changes.
Each suggestion MUST include:
- config_key: The Spark property name
- current_value: The value seen in logs (or null)
- suggested_value: The recommended value
- reason: Why this change is needed
- impact: expected benefit

Format your response as structured JSON with keys:
- summary (string)
- root_cause (string)
- severity (string: "low", "medium", "high", "critical")
- recommendations (array of objects: {{title, description, priority, category}})
- config_suggestions (array of objects: {{config_key, current_value, suggested_value, reason, impact}})"""
}


@dataclass
class AnalysisResult:
    """Result from LLM analysis."""
    summary: Optional[str] = None
    root_cause: Optional[str] = None
    severity: Optional[str] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    config_suggestions: Optional[List[Dict[str, Any]]] = None
    tokens_used: Optional[int] = None
    raw_response: Optional[str] = None


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    @abstractmethod
    async def generate(self, prompt: str) -> tuple[str, int]:
        """Generate response from LLM.
        
        Returns:
            tuple: (response_text, tokens_used)
        """
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name or settings.openai_model)
        self.api_key = settings.openai_api_key
        
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
    
    async def generate(self, prompt: str) -> tuple[str, int]:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.api_key)
        
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert Apache Spark engineer and log analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4096
        )
        
        tokens = response.usage.total_tokens if response.usage else 0
        return response.choices[0].message.content, tokens


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""
    
    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name or settings.gemini_model)
        self.api_key = settings.gemini_api_key
        
        if not self.api_key:
            raise ValueError("Gemini API key not configured")
    
    async def generate(self, prompt: str) -> tuple[str, int]:
        import google.generativeai as genai
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model_name)
        
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=4096
            )
        )
        
        # Gemini doesn't provide token count directly in same way
        tokens = len(prompt.split()) + len(response.text.split())  # Rough estimate
        return response.text, tokens


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name or settings.anthropic_model)
        self.api_key = settings.anthropic_api_key
        
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")
    
    async def generate(self, prompt: str) -> tuple[str, int]:
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic(api_key=self.api_key)
        
        response = await client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ],
            system="You are an expert Apache Spark engineer and log analyst."
        )
        
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return response.content[0].text, tokens


class GroqProvider(BaseLLMProvider):
    """Groq provider."""
    
    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name or settings.groq_model)
        self.api_key = settings.groq_api_key
        
        if not self.api_key:
            raise ValueError("Groq API key not configured")
    
    async def generate(self, prompt: str) -> tuple[str, int]:
        from groq import AsyncGroq
        
        client = AsyncGroq(api_key=self.api_key)
        
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert Apache Spark engineer and log analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4096
        )
        
        tokens = response.usage.total_tokens if response.usage else 0
        return response.choices[0].message.content, tokens


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider (unified API for multiple models)."""
    
    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name or settings.openrouter_model)
        self.api_key = settings.openrouter_api_key
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
    
    async def generate(self, prompt: str) -> tuple[str, int]:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": "You are an expert Apache Spark engineer and log analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4096
                }
            )
            response.raise_for_status()
            data = response.json()
            
            tokens = data.get("usage", {}).get("total_tokens", 0)
            return data["choices"][0]["message"]["content"], tokens


class OllamaProvider(BaseLLMProvider):
    """Ollama local provider."""
    
    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name or settings.ollama_model)
        self.base_url = settings.ollama_base_url
    
    async def generate(self, prompt: str) -> tuple[str, int]:
        import httpx
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": f"System: You are an expert Apache Spark engineer and log analyst.\n\nUser: {prompt}",
                    "stream": False,
                    "options": {
                        "temperature": 0.3
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Ollama doesn't provide token count directly
            tokens = len(prompt.split()) + len(data["response"].split())
            return data["response"], tokens


class LLMService:
    """Service for LLM-powered log analysis."""
    
    PROVIDERS = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "anthropic": AnthropicProvider,
        "groq": GroqProvider,
        "openrouter": OpenRouterProvider,
        "ollama": OllamaProvider
    }
    
    def __init__(self, provider: str = None, model_name: str = None):
        provider = provider or settings.default_llm_provider
        
        if provider not in self.PROVIDERS:
            raise ValueError(f"Unknown LLM provider: {provider}. Available: {list(self.PROVIDERS.keys())}")
        
        self.provider_name = provider
        self.provider = self.PROVIDERS[provider](model_name)
        self.model_name = self.provider.model_name
    
    async def analyze_logs(
        self,
        db: AsyncSession,
        log_file_id: int,
        analysis_type: str = "full"
    ) -> Dict[str, Any]:
        """Analyze logs using configured LLM provider."""
        # Get log entries
        result = await db.execute(
            select(LogEntry)
            .where(LogEntry.log_file_id == log_file_id)
            .order_by(LogEntry.line_number)
            .limit(500)  # Limit to avoid token overflow
        )
        entries = result.scalars().all()
        
        if not entries:
            return {
                "summary": "No log entries found for analysis.",
                "root_cause": None,
                "severity": "low",
                "recommendations": [],
                "config_suggestions": []
            }
        
        # Focus on errors and warnings
        error_entries = [e for e in entries if e.is_error or e.is_warning]
        if error_entries:
            entries_to_analyze = error_entries[:100]
        else:
            entries_to_analyze = entries[:100]
        
        # Format log entries for prompt
        log_text = self._format_entries(entries_to_analyze)
        
        # Get appropriate prompt template
        template = PROMPT_TEMPLATES.get(analysis_type, PROMPT_TEMPLATES["full"])
        
        # Build issues summary for config optimization
        issues_summary = ""
        if analysis_type == "config_optimization":
            error_categories = {}
            for e in error_entries:
                if e.category:
                    error_categories[e.category] = error_categories.get(e.category, 0) + 1
            issues_summary = json.dumps(error_categories) if error_categories else "No categorized issues found"
        
        # Create prompt
        prompt = template.format(
            log_entries=log_text,
            issues_summary=issues_summary
        )
        
        # Generate analysis
        response_text, tokens_used = await self.provider.generate(prompt)
        
        # Parse response
        return self._parse_response(response_text, tokens_used)
    
    def _format_entries(self, entries: List[LogEntry]) -> str:
        """Format log entries for LLM prompt."""
        lines = []
        for entry in entries:
            level = entry.level.value if entry.level else "UNKNOWN"
            ts = entry.timestamp.isoformat() if entry.timestamp else "N/A"
            
            line = f"[{ts}] [{level}]"
            if entry.component:
                line += f" [{entry.component}]"
            line += f" {entry.message}"
            
            if entry.stack_trace:
                line += f"\n{entry.stack_trace}"
            
            lines.append(line)
        
        return "\n".join(lines)
    
    def _parse_response(self, response: str, tokens_used: int) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
        result = {
            "summary": None,
            "root_cause": None,
            "severity": None,
            "recommendations": [],
            "config_suggestions": [],
            "tokens_used": tokens_used
        }
        
        # Try to parse as JSON
        try:
            # Find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                # Ensure summary is a string
                summary_data = data.get("summary")
                if isinstance(summary_data, (dict, list)):
                    result["summary"] = json.dumps(summary_data)
                else:
                    result["summary"] = summary_data
                
                # Ensure root_cause is a string
                root_cause_data = data.get("root_cause")
                if isinstance(root_cause_data, (dict, list)):
                    result["root_cause"] = json.dumps(root_cause_data)
                else:
                    result["root_cause"] = root_cause_data
                result["severity"] = data.get("severity", "medium").lower()
                
                # Robust parsing for recommendations
                raw_recommendations = data.get("recommendations", [])
                clean_recommendations = []
                for rec in raw_recommendations:
                    # Map 'action' to 'title' if title missing
                    title = rec.get("title") or rec.get("action") or "Recommendation"
                    # Map 'what_to_do' or 'description'
                    description = rec.get("description") or rec.get("details") or title
                    
                    category = rec.get("category", "general")
                    priority = rec.get("priority", "medium").lower()
                    if priority not in ["low", "medium", "high", "critical"]:
                        priority = "medium"
                        
                    clean_recommendations.append({
                        "title": title,
                        "description": description,
                        "priority": priority,
                        "category": category,
                        "code_example": rec.get("code_example")
                    })
                result["recommendations"] = clean_recommendations

                # Robust parsing for config suggestions
                raw_suggestions = data.get("config_suggestions", [])
                clean_suggestions = []
                for sug in raw_suggestions:
                    clean_suggestions.append({
                        "config_key": sug.get("config_key", "unknown"),
                        "current_value": sug.get("current_value"),
                        "suggested_value": sug.get("suggested_value", ""),
                        "reason": sug.get("reason", ""),
                        "impact": sug.get("impact", "Unknown impact")
                    })
                result["config_suggestions"] = clean_suggestions
                
                return result
        except json.JSONDecodeError:
            pass
        
        # Fallback: treat entire response as summary
        result["summary"] = response
        result["severity"] = "medium"
        
        return result

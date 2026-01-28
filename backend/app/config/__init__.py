"""
Configuration module for the application.
Loads settings from environment variables, .env file, and config.yaml.
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Any, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = Field(default="Intelligent Apache Spark Log Analyzer")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="development")
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # Database
    database_url: str = Field(default="sqlite:///./spark_logs.db")
    
    # Security
    secret_key: str = Field(default="change-me-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    api_key_header: str = Field(default="X-API-Key")
    
    # LLM Providers
    default_llm_provider: str = Field(default="openai")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4-turbo-preview")
    
    # Gemini
    gemini_api_key: Optional[str] = Field(default=None)
    gemini_model: str = Field(default="gemini-pro")
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None)
    anthropic_model: str = Field(default="claude-3-sonnet-20240229")
    
    # Groq
    groq_api_key: Optional[str] = Field(default=None)
    groq_model: str = Field(default="mixtral-8x7b-32768")
    
    # OpenRouter
    openrouter_api_key: Optional[str] = Field(default=None)
    openrouter_model: str = Field(default="openai/gpt-4-turbo-preview")
    
    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama2")
    
    # Log Ingestion
    log_upload_dir: str = Field(default="./uploads")
    log_watch_dir: str = Field(default="./watch")
    max_upload_size_mb: int = Field(default=100)
    supported_extensions: str = Field(default=".log,.txt,.gz,.zip")
    
    # Background Tasks
    watch_poll_interval_seconds: int = Field(default=30)
    
    @property
    def supported_extensions_list(self) -> list[str]:
        """Return supported extensions as a list."""
        return [ext.strip() for ext in self.supported_extensions.split(",")]


class YAMLConfig:
    """YAML configuration loader."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config: dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self._config = yaml.safe_load(f) or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation.
        
        Example: config.get("llm.default_provider")
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    def get_section(self, section: str) -> dict[str, Any]:
        """Get an entire configuration section."""
        return self._config.get(section, {})
    
    @property
    def raw(self) -> dict[str, Any]:
        """Return raw configuration dictionary."""
        return self._config


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


@lru_cache()
def get_yaml_config() -> YAMLConfig:
    """Get cached YAML configuration."""
    config_path = os.getenv("CONFIG_PATH", "config.yaml")
    return YAMLConfig(config_path)


# Convenience function for dependency injection
def get_config() -> tuple[Settings, YAMLConfig]:
    """Get both settings and YAML config."""
    return get_settings(), get_yaml_config()

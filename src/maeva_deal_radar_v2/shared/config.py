"""Configuration centralisée chargée depuis les variables d'environnement."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Paramètres de l'application chargés depuis .env."""

    # LLM APIs
    anthropic_api_key: str = Field(default="", description="Clé API Anthropic")
    openai_api_key: str = Field(default="", description="Clé API OpenAI")

    # Signaux et sourcing
    tavily_api_key: str = Field(default="", description="Clé API Tavily")
    pappers_api_key: str = Field(default="", description="Clé API Pappers")

    # Base de données
    database_url: str = Field(
        default="sqlite:///./data/maeva_v2.db",
        description="URL de connexion SQLite",
    )

    # Environnement
    environment: str = Field(default="development", description="Environnement")
    log_level: str = Field(default="INFO", description="Niveau de log")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Retourne les paramètres en singleton (cache LRU)."""
    return Settings()

"""Classes de base pour les sources de signaux M&A/PE."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RawSignal(BaseModel):
    """Signal brut capté depuis une source externe.

    Représentation normalisée avant qualification.
    Chaque source produit des RawSignal dans ce format.
    """

    source_name: str
    source_url: str
    company_name: str
    content: str = Field(min_length=10, max_length=3000)
    signal_type: str = "unknown"
    geography: str = "France"
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def lead_id(self) -> str:
        """Identifiant unique dérivé du nom de société et de la source."""
        import hashlib
        key = f"{self.company_name}:{self.source_url}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]


class BaseSignalSource(ABC):
    """Classe abstraite pour toutes les sources de signaux.

    Chaque source doit implémenter fetch() qui retourne une liste
    de RawSignal normalisés.
    """

    name: str = "unnamed_source"

    @abstractmethod
    def fetch(self, max_results: int = 20) -> list[RawSignal]:
        """Interroge la source et retourne les signaux détectés.

        Args:
            max_results: Nombre maximum de signaux à retourner.

        Returns:
            Liste de RawSignal normalisés, du plus récent au plus ancien.
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
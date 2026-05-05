"""Modèles de données partagés entre tous les domaines."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class SignalType(StrEnum):
    """Types de signaux détectés sur les sources externes."""

    FUNDING = "funding"
    HIRING = "hiring"
    EXPANSION = "expansion"
    PARTNERSHIP = "partnership"
    LEADERSHIP_CHANGE = "leadership_change"
    DEAL_ANNOUNCED = "deal_announced"
    FUND_CLOSING = "fund_closing"
    UNKNOWN = "unknown"


class QualificationStatus(StrEnum):
    """Statut de qualification d'un lead."""

    KEEP = "KEEP"
    REVIEW = "REVIEW"
    STOP = "STOP"
    PENDING = "PENDING"


class OutreachChannel(StrEnum):
    """Canal d'approche utilisé."""

    EMAIL = "email"
    LINKEDIN = "linkedin"


class OutreachStatus(StrEnum):
    """Statut d'une tâche d'approche."""

    PLANNED = "PLANNED"
    DONE = "DONE"
    POSTPONED = "POSTPONED"
    CANCELLED = "CANCELLED"
    STOPPED = "STOPPED"


class Signal(BaseModel):
    """Signal brut capté sur une source externe."""

    source_url: HttpUrl
    page_url: HttpUrl
    content_snippet: str = Field(min_length=10, max_length=2000)
    signal_type: SignalType = SignalType.UNKNOWN
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    raw_metadata: dict[str, str] = Field(default_factory=dict)


class Lead(BaseModel):
    """Société cible construite à partir d'un ou plusieurs signaux."""

    company_name: str = Field(min_length=2, max_length=200)
    website: HttpUrl | None = None
    sector: str = Field(default="", max_length=100)
    geography: str = Field(default="Île-de-France", max_length=100)
    target_role: str = Field(default="", max_length=100)
    personalization_fact: str = Field(default="", max_length=500)
    primary_signal: SignalType = SignalType.UNKNOWN
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    qualification_status: QualificationStatus = QualificationStatus.PENDING
    source_url: HttpUrl | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OutreachTask(BaseModel):
    """Tâche d'approche planifiée pour Maeva."""

    sequence_uid: str = Field(min_length=1, max_length=100)
    company: str = Field(min_length=2, max_length=200)
    track: str = Field(pattern=r"^(PE|MA)$")
    contact_name: str = Field(default="", max_length=100)
    title: str = Field(default="", max_length=100)
    step_code: str = Field(
        pattern=r"^STEP_[0-3]_(EMAIL|LINKEDIN|FOLLOWUP_[12]_EMAIL)$"
    )
    planned_date: datetime
    channel: OutreachChannel
    message_subject: str = Field(default="", max_length=200)
    message_body: str = Field(default="", max_length=5000)
    sequence_status: OutreachStatus = OutreachStatus.PLANNED
    execution_note: str = Field(default="", max_length=500)
    executed_at: datetime | None = None
    stop_reason: str = Field(default="", max_length=200)

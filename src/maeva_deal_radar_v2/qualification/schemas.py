"""Schémas Pydantic pour le domaine qualification."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class QualificationDecision(StrEnum):
    """Les trois décisions possibles du qualifier."""

    KEEP = "KEEP"
    STOP = "STOP"
    REVIEW = "REVIEW"


class QualificationResult(BaseModel):
    """Résultat du qualifier pour un lead donné."""

    decision: QualificationDecision
    confidence: float = Field(ge=0.0, le=1.0)
    justification: str = Field(min_length=10, max_length=1000)
    raw_reasoning: str = Field(default="")


class EvalCase(BaseModel):
    """Un cas d'évaluation : inputs + décision humaine de référence."""

    id: str
    company_name: str
    source_url: str
    content: str
    signal_type: str
    geography: str = "Île-de-France"
    human_decision: QualificationDecision
    notes: str = ""


class EvalReport(BaseModel):
    """Rapport agrégé produit par le harness d'évaluation."""

    total_cases: int
    correct: int
    precision_keep: float = Field(ge=0.0, le=1.0)
    recall_keep: float = Field(ge=0.0, le=1.0)
    f1_keep: float = Field(ge=0.0, le=1.0)
    precision_stop: float = Field(ge=0.0, le=1.0)
    recall_stop: float = Field(ge=0.0, le=1.0)
    f1_stop: float = Field(ge=0.0, le=1.0)
    accuracy: float = Field(ge=0.0, le=1.0)
    errors: list[dict[str, str]] = Field(default_factory=list)

    @property
    def summary(self) -> str:
        """Résumé lisible du rapport."""
        return (
            f"Accuracy: {self.accuracy:.1%} ({self.correct}/{self.total_cases}) | "
            f"F1-KEEP: {self.f1_keep:.2f} | "
            f"F1-STOP: {self.f1_stop:.2f}"
        )

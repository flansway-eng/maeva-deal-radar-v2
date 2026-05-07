"""Qualifier de leads M&A/PE basé sur Claude (Anthropic).

Classifie chaque lead en KEEP / STOP / REVIEW avec justification,
en utilisant le mécanisme tool_use pour un output structuré garanti.
"""

from __future__ import annotations

import logging
from typing import Any

import anthropic

from maeva_deal_radar_v2.qualification.schemas import (
    QualificationDecision,
    QualificationResult,
)
from maeva_deal_radar_v2.shared.config import get_settings

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """Tu es un assistant spécialisé dans la qualification de leads
pour Maeva, chargée de prospection dans l'écosystème M&A et Private Equity
en Île-de-France.

Maeva cherche à identifier et contacter des professionnels travaillant dans :
- Des fonds de Private Equity mid-market (tickets entre 10M et 500M euros)
- Des équipes M&A advisory et Transaction Services
- Des deal teams actives en Île-de-France ou avec une présence parisienne
- Des fonds ayant récemment levé, recruté, ou annoncé des deals

Elle NE cherche PAS :
- Des job boards, pages de recrutement ou offres d'emploi
- Des annuaires, classements ou contenus média
- Des cabinets de conseil généralistes sans activité PE directe
- Des formations, guides ou contenus éducatifs
- Des fonds infrastructure, immobilier ou venture capital early-stage

Ta décision :
- KEEP : source pertinente, contact potentiel identifiable, bon timing
- STOP : source non pertinente, bruit, hors scope
- REVIEW : cas ambigu nécessitant validation humaine"""

QUALIFY_TOOL: dict[str, Any] = {
    "name": "qualify_lead",
    "description": "Qualifie un lead M&A/PE et retourne une décision structurée.",
    "input_schema": {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["KEEP", "STOP", "REVIEW"],
                "description": "Décision de qualification du lead.",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Niveau de confiance entre 0.0 et 1.0.",
            },
            "justification": {
                "type": "string",
                "description": (
                    "Justification concise de la décision en 1-3 phrases, "
                    "en français, orientée critères Maeva."
                ),
            },
        },
        "required": ["decision", "confidence", "justification"],
    },
}


def qualify_lead(
    company_name: str,
    source_url: str,
    content: str,
    signal_type: str = "unknown",
    geography: str = "Île-de-France",
) -> QualificationResult:
    """Qualifie un lead en appelant Claude via tool_use.

    Args:
        company_name: Nom de la société cible.
        source_url: URL de la source détectée.
        content: Extrait du contenu de la page source.
        signal_type: Type de signal détecté.
        geography: Zone géographique.

    Returns:
        QualificationResult avec décision, confiance et justification.
    """
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    user_message = f"""Qualifie ce lead pour Maeva :

Société : {company_name}
Source : {source_url}
Géographie : {geography}
Signal détecté : {signal_type}
Contenu extrait :
{content}

Retourne ta décision via l'outil qualify_lead."""

    logger.debug("Qualification de '%s' via Claude...", company_name)

    response = client.messages.create(  # type: ignore[call-overload]
        model=MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        tools=[QUALIFY_TOOL],
        tool_choice={"type": "tool", "name": "qualify_lead"},
        messages=[{"role": "user", "content": user_message}],
    )

    tool_use_block = next(
        block for block in response.content if block.type == "tool_use"
    )
    tool_input: dict[str, Any] = tool_use_block.input

    raw_reasoning = " | ".join(
        block.text
        for block in response.content
        if block.type == "text" and hasattr(block, "text")
    )

    result = QualificationResult(
        decision=QualificationDecision(tool_input["decision"]),
        confidence=float(tool_input["confidence"]),
        justification=str(tool_input["justification"]),
        raw_reasoning=raw_reasoning,
    )

    logger.info(
        "Lead '%s' → %s (confiance: %.0f%%)",
        company_name,
        result.decision,
        result.confidence * 100,
    )

    return result

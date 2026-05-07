"""Source de signaux BODACC via l'API data.gouv.fr.

BODACC = Bulletin Officiel des Annonces Civiles et Commerciales.
Publie en premier les modifications légales d'entreprises (avant la presse).
Aucune clé API requise — données publiques.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from maeva_deal_radar_v2.signals.base import BaseSignalSource, RawSignal

logger = logging.getLogger(__name__)

BODACC_API_URL = (
    "https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/"
    "catalog/datasets/annonces-commerciales/records"
)

SIGNAL_TYPE_MAP = {
    "creation": "expansion",
    "modification": "leadership_change",
    "vente": "deal_announced",
    "cession": "deal_announced",
    "radiation": "unknown",
    "depot": "unknown",
    "divers": "unknown",
}

IDF_DEPARTMENTS = {"75", "77", "78", "91", "92", "93", "94", "95"}


class BodaccSource(BaseSignalSource):
    """Source BODACC — annonces légales françaises en temps réel."""

    name = "bodacc"

    def __init__(self, departments: set[str] | None = None) -> None:
        """Initialise la source BODACC.

        Args:
            departments: Codes départements à surveiller.
                         Par défaut : Île-de-France (75, 77, 78, 91-95).
        """
        self.departments = departments or IDF_DEPARTMENTS

    def fetch(self, max_results: int = 20) -> list[RawSignal]:
        """Récupère les annonces BODACC récentes pour les départements cibles.

        Args:
            max_results: Nombre maximum d'annonces à retourner.

        Returns:
            Liste de RawSignal normalisés depuis BODACC.
        """
        dept_filter = " or ".join(
            f'numerodepartement="{d}"' for d in sorted(self.departments)
        )
        params: dict[str, Any] = {
            "limit": min(max_results, 100),
            "order_by": "dateparution desc",
            "where": dept_filter,
        }

        try:
            response = httpx.get(
                BODACC_API_URL,
                params=params,
                timeout=15.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("Erreur BODACC API: %s", e)
            return []

        records = response.json().get("results", [])
        signals: list[RawSignal] = []

        for record in records:
            signal = self._parse_record(record)
            if signal is not None:
                signals.append(signal)
            if len(signals) >= max_results:
                break

        logger.info("BODACC: %d signaux récupérés.", len(signals))
        return signals

    def _parse_record(self, record: dict[str, Any]) -> RawSignal | None:
        """Transforme un enregistrement BODACC en RawSignal."""
        company_name: str = (record.get("commercant") or "").strip()
        if not company_name or len(company_name) < 2:
            return None

        dept: str = str(record.get("numerodepartement") or "")
        familleavis: str = (record.get("familleavis") or "").lower()
        familleavis_lib: str = record.get("familleavis_lib") or familleavis
        signal_type = SIGNAL_TYPE_MAP.get(familleavis, "unknown")

        ville: str = record.get("ville") or ""
        tribunal: str = record.get("tribunal") or ""
        date_str: str = record.get("dateparution") or ""

        content = (
            f"Annonce BODACC : {familleavis_lib} — "
            f"Société : {company_name}"
            + (f" — Ville : {ville}" if ville else "")
            + (f" — {tribunal}" if tribunal else "")
        )

        source_url: str = (
            record.get("url_complete")
            or (
                "https://www.bodacc.fr/pages/annonces-commerciales-detail/"
                f"?q.id=id:{record.get('id', 'unknown')}"
            )
        )

        detected_at = datetime.utcnow()
        if date_str:
            try:
                detected_at = datetime.fromisoformat(date_str)
            except ValueError:
                pass

        return RawSignal(
            source_name=self.name,
            source_url=source_url,
            company_name=company_name,
            content=content,
            signal_type=signal_type,
            geography=f"Département {dept}" if dept else "France",
            detected_at=detected_at,
            raw_metadata={
                "familleavis": familleavis,
                "tribunal": tribunal,
                "ville": ville,
                "numerodepartement": dept,
                "date_parution": date_str,
            },
        )

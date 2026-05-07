"""Source de signaux Pappers — données légales et dirigeants d'entreprises françaises.

Pappers agrège les données INPI, greffe et BODACC.
Clé API requise (gratuit jusqu'à 100 requêtes/jour).
Documentation : https://www.pappers.fr/api/documentation
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from maeva_deal_radar_v2.shared.config import get_settings
from maeva_deal_radar_v2.signals.base import BaseSignalSource, RawSignal

logger = logging.getLogger(__name__)

PAPPERS_API_BASE = "https://api.pappers.fr/v2"

PE_FORMES_JURIDIQUES = {
    "SA", "SAS", "SASU", "SCA", "SE", "SNC",
}

IDF_CODES_POSTAUX_PREFIX = {
    "75", "77", "78", "91", "92", "93", "94", "95",
}


class PappersSource(BaseSignalSource):
    """Source Pappers — changements de dirigeants et annonces légales."""

    name = "pappers"

    def __init__(self, api_key: str | None = None) -> None:
        """Initialise la source Pappers.

        Args:
            api_key: Clé API Pappers. Si None, chargée depuis les settings.
        """
        self.api_key = api_key or get_settings().pappers_api_key

    def fetch(self, max_results: int = 20) -> list[RawSignal]:
        """Récupère les entreprises IDF avec changements récents.

        Recherche les sociétés par actions en Île-de-France ayant eu
        des modifications récentes (dirigeants, capital, statuts).

        Args:
            max_results: Nombre maximum de signaux à retourner.

        Returns:
            Liste de RawSignal normalisés depuis Pappers.
        """
        if not self.api_key:
            logger.warning("Pappers: clé API manquante, source désactivée.")
            return []

        params: dict[str, Any] = {
            "api_token": self.api_key,
            "par_page": min(max_results * 2, 50),
            "page": 1,
            "precision": "standard",
            "departement": "75,77,78,91,92,93,94,95",
            "date_radiation": "",
        }

        try:
            response = httpx.get(
                f"{PAPPERS_API_BASE}/recherche",
                params=params,
                timeout=15.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("Erreur Pappers API: %s", e)
            return []

        data = response.json()
        companies: list[dict[str, Any]] = data.get("resultats", [])

        signals: list[RawSignal] = []
        for company in companies:
            signal = self._parse_company(company)
            if signal is not None:
                signals.append(signal)
            if len(signals) >= max_results:
                break

        logger.info("Pappers: %d signaux récupérés.", len(signals))
        return signals

    def _parse_company(
        self, company: dict[str, Any]
    ) -> RawSignal | None:
        """Transforme un résultat Pappers en RawSignal."""
        nom: str = (company.get("nom_entreprise") or "").strip()
        if not nom or len(nom) < 2:
            return None

        siren: str = company.get("siren") or ""
        forme: str = company.get("forme_juridique") or ""
        siege: dict[str, Any] = company.get("siege") or {}
        cp: str = str(siege.get("code_postal") or "")
        ville: str = siege.get("ville") or ""
        date_creation: str = company.get("date_creation") or ""
        date_mise_a_jour: str = company.get("date_mise_a_jour") or ""

        signal_type = "expansion"
        if date_mise_a_jour and date_mise_a_jour != date_creation:
            signal_type = "leadership_change"

        content_parts = [f"Société : {nom}"]
        if forme:
            content_parts.append(f"Forme juridique : {forme}")
        if ville:
            content_parts.append(f"Siège : {ville} ({cp})")
        if date_mise_a_jour:
            content_parts.append(f"Mise à jour : {date_mise_a_jour}")

        content = " — ".join(content_parts)

        source_url = (
            f"https://www.pappers.fr/entreprise/{nom.lower().replace(' ', '-')}"
            f"-{siren}"
            if siren
            else f"https://www.pappers.fr/recherche?q={nom}"
        )

        detected_at = datetime.utcnow()
        if date_mise_a_jour:
            try:
                detected_at = datetime.fromisoformat(date_mise_a_jour)
            except ValueError:
                pass

        return RawSignal(
            source_name=self.name,
            source_url=source_url,
            company_name=nom,
            content=content,
            signal_type=signal_type,
            geography=f"{ville} ({cp})" if ville else "Île-de-France",
            detected_at=detected_at,
            raw_metadata={
                "siren": siren,
                "forme_juridique": forme,
                "code_postal": cp,
                "ville": ville,
                "date_creation": date_creation,
                "date_mise_a_jour": date_mise_a_jour,
            },
        )

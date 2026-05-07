"""Source de signaux via flux RSS spécialisés M&A/PE.

Supporte tout flux RSS standard. Les sources par défaut sont
des médias économiques français accessibles sans abonnement.
Aucune clé API requise.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import feedparser

from maeva_deal_radar_v2.signals.base import BaseSignalSource, RawSignal

logger = logging.getLogger(__name__)

DEFAULT_RSS_SOURCES = [
    {
        "name": "lesechos_finance",
        "url": "https://www.lesechos.fr/rss/rss_finance.xml",
        "signal_type": "deal_announced",
        "geography": "France",
    },
    {
        "name": "lemonde_economie",
        "url": "https://www.lemonde.fr/economie/rss_full.xml",
        "signal_type": "deal_announced",
        "geography": "France",
    },
    {
        "name": "bfm_business",
        "url": "https://www.bfmtv.com/rss/economie/",
        "signal_type": "deal_announced",
        "geography": "France",
    },
]

KEYWORDS_PE = {
    "private equity", "capital investissement", "lbo", "mid-market",
    "fonds", "acquisition", "cession", "levée", "closing", "build-up",
    "transaction", "deal", "portefeuille", "participation", "rachat",
    "investissement", "fusion", "capital-investissement",
}


class RssSource(BaseSignalSource):
    """Source RSS générique pour flux spécialisés M&A/PE."""

    name = "rss"

    def __init__(
        self,
        sources: list[dict[str, str]] | None = None,
    ) -> None:
        """Initialise la source RSS.

        Args:
            sources: Liste de dicts avec 'name', 'url', 'signal_type',
                     'geography'. Si None, utilise les sources par défaut.
        """
        self.sources = sources or DEFAULT_RSS_SOURCES

    def fetch(self, max_results: int = 20) -> list[RawSignal]:
        """Récupère les entrées RSS récentes depuis toutes les sources.

        Args:
            max_results: Nombre maximum de signaux au total.

        Returns:
            Liste de RawSignal normalisés, triés par date décroissante.
        """
        all_signals: list[RawSignal] = []
        per_source = max(1, max_results // len(self.sources))

        for source_config in self.sources:
            signals = self._fetch_source(source_config, per_source)
            all_signals.extend(signals)
            logger.info(
                "RSS [%s]: %d signaux récupérés.",
                source_config["name"],
                len(signals),
            )

        all_signals.sort(key=lambda s: s.detected_at, reverse=True)
        return all_signals[:max_results]

    def _fetch_source(
        self,
        source_config: dict[str, str],
        max_results: int,
    ) -> list[RawSignal]:
        """Récupère les entrées d'un flux RSS unique."""
        url = source_config["url"]
        try:
            feed: Any = feedparser.parse(url)
        except Exception as e:
            logger.error("Erreur RSS [%s]: %s", source_config["name"], e)
            return []

        if not feed.entries:
            logger.warning(
                "Aucune entrée dans le flux RSS : %s (bozo=%s)",
                url,
                feed.bozo,
            )
            return []

        signals: list[RawSignal] = []

        for entry in feed.entries[:max_results * 3]:
            signal = self._parse_entry(entry, source_config)
            if signal is not None:
                signals.append(signal)
            if len(signals) >= max_results:
                break

        return signals

    def _parse_entry(
        self,
        entry: Any,
        source_config: dict[str, str],
    ) -> RawSignal | None:
        """Transforme une entrée RSS en RawSignal."""
        title: str = getattr(entry, "title", "") or ""
        summary: str = getattr(entry, "summary", "") or ""
        link: str = getattr(entry, "link", "") or ""

        if not title or not link:
            return None

        combined = f"{title} {summary}".lower()
        if not any(kw in combined for kw in KEYWORDS_PE):
            return None

        content = title
        if summary:
            clean_summary = summary[:500].strip()
            content = f"{title} — {clean_summary}"

        if len(content) < 10:
            return None

        company_name = self._extract_company(title)

        detected_at = datetime.utcnow()
        published = getattr(entry, "published_parsed", None)
        if published:
            try:
                detected_at = datetime(*published[:6])
            except (TypeError, ValueError):
                pass

        return RawSignal(
            source_name=source_config["name"],
            source_url=link,
            company_name=company_name,
            content=content,
            signal_type=source_config.get("signal_type", "unknown"),
            geography=source_config.get("geography", "France"),
            detected_at=detected_at,
            raw_metadata={
                "title": title,
                "feed_url": source_config["url"],
            },
        )

    def _extract_company(self, title: str) -> str:
        """Extrait un nom de société depuis un titre d'article RSS."""
        separators = [
            " acquiert", " cède", " lève", " annonce", " rejoint",
            " nomme", " ouvre", " lance", " rachète", " vend",
            " fusionne", " investit", " entre", " sort", " clos",
            " :",
        ]
        title_lower = title.lower()
        for sep in separators:
            idx = title_lower.find(sep)
            if idx > 3:
                candidate = title[:idx].strip()
                if 2 <= len(candidate) <= 80:
                    return candidate
        return title[:80].strip()

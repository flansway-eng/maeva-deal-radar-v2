"""Pipeline d'orchestration des sources de signaux.

Orchestre BODACC + RSS + Pappers, qualifie chaque signal via Claude,
et stocke les leads qualifiés KEEP dans LanceDB.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from maeva_deal_radar_v2.memory.vector_store import upsert_lead
from maeva_deal_radar_v2.qualification.qualifier import qualify_lead
from maeva_deal_radar_v2.qualification.schemas import QualificationDecision
from maeva_deal_radar_v2.signals.base import BaseSignalSource, RawSignal
from maeva_deal_radar_v2.signals.bodacc import BodaccSource
from maeva_deal_radar_v2.signals.pappers import PappersSource
from maeva_deal_radar_v2.signals.rss import RssSource

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Résultat d'une exécution du pipeline."""

    signals_fetched: int = 0
    signals_qualified: int = 0
    leads_kept: int = 0
    leads_stopped: int = 0
    leads_review: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """Résumé lisible de l'exécution."""
        return (
            f"Signaux: {self.signals_fetched} récupérés, "
            f"{self.signals_qualified} qualifiés — "
            f"KEEP: {self.leads_kept} | "
            f"STOP: {self.leads_stopped} | "
            f"REVIEW: {self.leads_review}"
        )


def build_default_sources() -> list[BaseSignalSource]:
    """Construit la liste des sources actives par défaut."""
    return [
        BodaccSource(),
        RssSource(),
        PappersSource(),
    ]


def run_pipeline(
    sources: list[BaseSignalSource] | None = None,
    max_signals_per_source: int = 10,
    qualify_delay: float = 0.5,
    store_in_lancedb: bool = True,
    verbose: bool = True,
) -> PipelineResult:
    """Exécute le pipeline complet : collecte → qualification → stockage.

    Args:
        sources: Sources à utiliser. Si None, utilise les sources par défaut.
        max_signals_per_source: Nombre max de signaux par source.
        qualify_delay: Pause entre chaque appel API de qualification.
        store_in_lancedb: Si True, stocke les KEEP dans LanceDB.
        verbose: Affiche la progression en temps réel.

    Returns:
        PipelineResult avec les statistiques d'exécution.
    """
    if sources is None:
        sources = build_default_sources()

    result = PipelineResult()

    all_signals: list[RawSignal] = []
    for source in sources:
        try:
            signals = source.fetch(max_results=max_signals_per_source)
            all_signals.extend(signals)
            if verbose:
                print(f"[{source.name}] {len(signals)} signaux récupérés.")
        except Exception as e:
            error_msg = f"Erreur source {source.name}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)

    result.signals_fetched = len(all_signals)

    seen_ids: set[str] = set()
    unique_signals: list[RawSignal] = []
    for signal in all_signals:
        if signal.lead_id not in seen_ids:
            seen_ids.add(signal.lead_id)
            unique_signals.append(signal)

    dedup_count = result.signals_fetched - len(unique_signals)
    if dedup_count > 0 and verbose:
        print(f"Déduplication : {dedup_count} doublons supprimés.")

    if verbose:
        print(f"\nQualification de {len(unique_signals)} signaux uniques...\n")

    for i, signal in enumerate(unique_signals, 1):
        if verbose:
            print(
                f"[{i:2d}/{len(unique_signals)}] "
                f"{signal.company_name[:35]:<35} ",
                end="",
                flush=True,
            )

        try:
            qual = qualify_lead(
                company_name=signal.company_name,
                source_url=str(signal.source_url),
                content=signal.content,
                signal_type=signal.signal_type,
                geography=signal.geography,
            )
            result.signals_qualified += 1

            if qual.decision == QualificationDecision.KEEP:
                result.leads_kept += 1
                if store_in_lancedb:
                    upsert_lead(
                        lead_id=signal.lead_id,
                        company_name=signal.company_name,
                        content=signal.content,
                        signal_type=signal.signal_type,
                        qualification_status=qual.decision.value,
                        confidence_score=qual.confidence,
                        source_url=str(signal.source_url),
                        geography=signal.geography,
                    )
            elif qual.decision == QualificationDecision.STOP:
                result.leads_stopped += 1
            else:
                result.leads_review += 1

            if verbose:
                marker = {"KEEP": "✓", "STOP": "✗", "REVIEW": "?"}.get(
                    qual.decision.value, "?"
                )
                print(
                    f"{marker} {qual.decision.value:<6} "
                    f"conf: {qual.confidence:.0%}"
                )

        except Exception as e:
            error_msg = f"Erreur qualification {signal.company_name}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            if verbose:
                print(f"ERREUR: {e}")

        if i < len(unique_signals):
            time.sleep(qualify_delay)

    if verbose:
        print(f"\n{'='*60}")
        print(f"PIPELINE : {result.summary}")
        if store_in_lancedb and result.leads_kept > 0:
            print(f"{result.leads_kept} leads stockés dans LanceDB.")
        print(f"{'='*60}")

    return result

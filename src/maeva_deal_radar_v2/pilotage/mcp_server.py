"""Serveur MCP — pilotage de Maeva Deal Radar Room en langage naturel.

Expose les opérations du système comme outils MCP utilisables depuis Claude.
Maeva peut lancer le pipeline, chercher des leads, et consulter les stats
sans ouvrir un terminal.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Maeva Deal Radar Room",
    instructions=(
        "Tu es le copilote de prospection M&A/PE de Maeva. "
        "Tu peux lancer le pipeline de captation de signaux, "
        "rechercher des leads similaires, qualifier des leads à la demande, "
        "et consulter les statistiques de la base. "
        "Toutes les données concernent le marché M&A/PE mid-market "
        "en Île-de-France."
    ),
)


@mcp.tool()
def run_pipeline(
    max_signals_per_source: int = 5,
    sources: str = "bodacc,rss",
) -> str:
    """Lance le pipeline de captation et qualification des signaux M&A/PE.

    Collecte les signaux depuis les sources actives (BODACC, RSS, Pappers),
    qualifie chaque signal avec Claude, et stocke les leads KEEP dans LanceDB.

    Args:
        max_signals_per_source: Nombre maximum de signaux par source (1-20).
        sources: Sources à activer, séparées par des virgules.
                 Valeurs possibles : bodacc, rss, pappers.
                 Exemple : "bodacc,rss" ou "bodacc,rss,pappers".

    Returns:
        Résumé de l'exécution avec statistiques.
    """
    from maeva_deal_radar_v2.signals.bodacc import BodaccSource
    from maeva_deal_radar_v2.signals.pappers import PappersSource
    from maeva_deal_radar_v2.signals.pipeline import run_pipeline as _run
    from maeva_deal_radar_v2.signals.rss import RssSource

    source_map = {
        "bodacc": BodaccSource,
        "rss": RssSource,
        "pappers": PappersSource,
    }

    requested = [s.strip().lower() for s in sources.split(",")]
    active_sources = [
        source_map[name]()
        for name in requested
        if name in source_map
    ]

    if not active_sources:
        return "Aucune source valide spécifiée. Utilisez : bodacc, rss, pappers."

    result = _run(
        sources=active_sources,
        max_signals_per_source=max(1, min(max_signals_per_source, 20)),
        qualify_delay=0.3,
        store_in_lancedb=True,
        verbose=False,
    )

    lines = [
        f"Pipeline exécuté sur {len(active_sources)} source(s).",
        f"Signaux récupérés : {result.signals_fetched}",
        f"Signaux qualifiés : {result.signals_qualified}",
        f"Leads KEEP stockés en LanceDB : {result.leads_kept}",
        f"Leads STOP éliminés : {result.leads_stopped}",
        f"Leads REVIEW (à valider) : {result.leads_review}",
    ]
    if result.errors:
        lines.append(f"Erreurs : {len(result.errors)}")
        lines.extend(f"  - {e}" for e in result.errors[:3])

    return "\n".join(lines)


@mcp.tool()
def search_leads(
    query: str,
    k: int = 5,
    filter_status: str = "",
) -> str:
    """Recherche des leads similaires à une requête textuelle dans LanceDB.

    Utilise la similarité sémantique (bge-m3) pour trouver les leads
    les plus proches de la requête, quelle que soit la formulation exacte.

    Args:
        query: Requête en langage naturel.
               Exemples : "fonds PE mid-market Paris", "closing récent IDF",
               "équipe deal flow renforcée".
        k: Nombre de résultats à retourner (1-20).
        filter_status: Si renseigné, filtre par statut de qualification.
                       Valeurs : KEEP, STOP, REVIEW, PENDING.

    Returns:
        Liste des leads similaires avec leurs informations.
    """
    from maeva_deal_radar_v2.memory.vector_store import search_similar

    results = search_similar(
        query=query,
        k=max(1, min(k, 20)),
        qualification_filter=filter_status.upper() if filter_status else None,
    )

    if not results:
        return f"Aucun lead trouvé pour : '{query}'"

    lines = [f"Résultats pour '{query}' ({len(results)} leads) :\n"]
    for i, lead in enumerate(results, 1):
        score = lead.get("_distance", lead.get("score", "N/A"))
        score_str = f"{1 - float(score):.0%}" if isinstance(score, (int, float)) else "N/A"
        lines.append(
            f"{i}. {lead.get('company_name', 'N/A')} "
            f"[{lead.get('qualification_status', 'N/A')}] "
            f"similarité: {score_str}"
        )
        lines.append(f"   Source: {lead.get('source_url', 'N/A')}")
        lines.append(f"   Signal: {lead.get('signal_type', 'N/A')}")
        content = lead.get("content", "")
        if content:
            lines.append(f"   Contenu: {content[:100]}...")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def qualify_single_lead(
    company_name: str,
    source_url: str,
    description: str,
    signal_type: str = "unknown",
    geography: str = "Île-de-France",
) -> str:
    """Qualifie un lead unique décrit manuellement.

    Utile pour tester rapidement si une société mérite l'attention
    de Maeva, ou pour valider une découverte manuelle.

    Args:
        company_name: Nom de la société à qualifier.
        source_url: URL de la source (page web, article, etc.).
        description: Description du signal ou du contenu observé.
        signal_type: Type de signal observé (hiring, expansion, deal_announced, etc.).
        geography: Zone géographique (défaut : Île-de-France).

    Returns:
        Décision de qualification avec justification détaillée.
    """
    from maeva_deal_radar_v2.qualification.qualifier import qualify_lead as _qualify

    result = _qualify(
        company_name=company_name,
        source_url=source_url,
        content=description,
        signal_type=signal_type,
        geography=geography,
    )

    emoji = {"KEEP": "✓", "STOP": "✗", "REVIEW": "?"}.get(
        result.decision.value, "?"
    )

    return (
        f"{emoji} Décision : {result.decision.value}\n"
        f"Confiance : {result.confidence:.0%}\n"
        f"Justification : {result.justification}"
    )


@mcp.tool()
def get_stats() -> str:
    """Retourne les statistiques actuelles de la base de leads LanceDB.

    Returns:
        Nombre total de leads, distribution par statut de qualification.
    """
    from maeva_deal_radar_v2.memory.vector_store import count, get_all

    total = count()
    if total == 0:
        return "Base vide — aucun lead en base. Lancez d'abord run_pipeline."

    leads = get_all()
    from collections import Counter
    status_counts = Counter(
        lead.get("qualification_status", "UNKNOWN") for lead in leads
    )

    lines = [
        f"Base LanceDB — {total} leads au total :",
        "",
    ]
    for status, count_val in sorted(status_counts.items()):
        emoji = {"KEEP": "✓", "STOP": "✗", "REVIEW": "?", "PENDING": "…"}.get(
            status, "?"
        )
        lines.append(f"  {emoji} {status} : {count_val}")

    return "\n".join(lines)


@mcp.tool()
def get_recent_leads(
    limit: int = 10,
    status_filter: str = "KEEP",
) -> str:
    """Retourne les leads récents depuis LanceDB.

    Args:
        limit: Nombre maximum de leads à retourner (1-50).
        status_filter: Filtre par statut. Valeurs : KEEP, STOP, REVIEW, ALL.

    Returns:
        Liste des leads correspondant aux critères.
    """
    from maeva_deal_radar_v2.memory.vector_store import get_all

    all_leads = get_all()

    if status_filter.upper() != "ALL":
        filtered = [
            lead for lead in all_leads
            if lead.get("qualification_status", "") == status_filter.upper()
        ]
    else:
        filtered = all_leads

    filtered = filtered[:max(1, min(limit, 50))]

    if not filtered:
        return f"Aucun lead avec le statut {status_filter}."

    lines = [f"Leads {status_filter} ({len(filtered)}) :\n"]
    for i, lead in enumerate(filtered, 1):
        lines.append(
            f"{i}. {lead.get('company_name', 'N/A')} "
            f"— {lead.get('signal_type', 'N/A')} "
            f"— {lead.get('geography', 'N/A')}"
        )
        content = lead.get("content", "")
        if content:
            lines.append(f"   {content[:80]}...")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()

"""Interface LanceDB pour le stockage et la recherche vectorielle des leads."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

import lancedb
import pyarrow as pa
from maeva_deal_radar_v2.memory.embedder import EMBEDDING_DIM, embed

logger = logging.getLogger(__name__)

DB_PATH = Path(".lancedb")
TABLE_NAME = "leads"

SCHEMA = pa.schema(
    [
        pa.field("id", pa.string()),
        pa.field("company_name", pa.string()),
        pa.field("content", pa.string()),
        pa.field("signal_type", pa.string()),
        pa.field("qualification_status", pa.string()),
        pa.field("confidence_score", pa.float32()),
        pa.field("source_url", pa.string()),
        pa.field("geography", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
    ]
)


def _get_table() -> Any:
    """Ouvre ou crée la table LanceDB."""
    db = lancedb.connect(str(DB_PATH))
    tables = list(db.list_tables())
    if TABLE_NAME in tables:
        return db.open_table(TABLE_NAME)
    logger.info("Création de la table '%s' dans LanceDB.", TABLE_NAME)
    try:
        return db.create_table(TABLE_NAME, schema=SCHEMA)
    except ValueError:
        return db.open_table(TABLE_NAME)


def upsert_lead(
    lead_id: str,
    company_name: str,
    content: str,
    signal_type: str = "unknown",
    qualification_status: str = "PENDING",
    confidence_score: float = 0.5,
    source_url: str = "",
    geography: str = "Île-de-France",
) -> None:
    """Insère ou met à jour un lead dans l'index vectoriel."""
    table = _get_table()
    vector = embed(content)
    row = {
        "id": lead_id,
        "company_name": company_name,
        "content": content,
        "signal_type": signal_type,
        "qualification_status": qualification_status,
        "confidence_score": confidence_score,
        "source_url": source_url,
        "geography": geography,
        "vector": vector,
    }
    try:
        table.delete(f"id = '{lead_id}'")
    except Exception:
        pass
    table.add([row])
    logger.debug("Lead '%s' indexé dans LanceDB.", company_name)


def search_similar(
    query: str,
    k: int = 5,
    qualification_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Recherche les leads les plus similaires à une requête textuelle."""
    table = _get_table()
    query_vector = embed(query)
    search = table.search(query_vector).limit(k)
    if qualification_filter:
        search = search.where(
            f"qualification_status = '{qualification_filter}'",
            prefilter=True,
        )
    results: list[dict[str, Any]] = search.to_list()
    return results


def get_all() -> list[dict[str, Any]]:
    """Retourne tous les leads de l'index sans dépendance pandas."""
    table = _get_table()
    arrow_table = table.to_arrow()
    return cast(list[dict[str, Any]], arrow_table.to_pylist())


def count() -> int:
    """Retourne le nombre de leads dans l'index."""
    table = _get_table()
    return int(table.count_rows())

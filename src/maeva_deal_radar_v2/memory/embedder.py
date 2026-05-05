"""Module d'embedding : transforme du texte en vecteurs numériques.

Modèle : BAAI/bge-m3 (multilingue, français + anglais, dimension 1024).
Téléchargement automatique au premier appel (~570 Mo, mis en cache ensuite).
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import cast

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_ID = "BAAI/bge-m3"
EMBEDDING_DIM = 1024


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Charge le modèle une seule fois en mémoire (singleton)."""
    logger.info("Chargement du modèle %s...", MODEL_ID)
    model = cast(SentenceTransformer, SentenceTransformer(MODEL_ID))
    logger.info("Modèle prêt. Dimension des vecteurs : %d", EMBEDDING_DIM)
    return model


def embed(text: str) -> list[float]:
    """Transforme un texte en vecteur normalisé de dimension 1024.

    Args:
        text: Le texte à embedder (nom de société, snippet, description).

    Returns:
        Vecteur de 1024 flottants normalisé en L2.
    """
    model = _get_model()
    raw = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
    vector = np.asarray(raw, dtype=np.float32)
    return cast(list[float], vector.tolist())


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Transforme une liste de textes en vecteurs.

    Plus efficace qu'appeler embed() en boucle : le modèle traite
    les textes en parallèle par lots de 32.

    Args:
        texts: Liste de textes à embedder.

    Returns:
        Liste de vecteurs, dans le même ordre que l'entrée.
    """
    if not texts:
        return []
    model = _get_model()
    raw = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=len(texts) > 10,
    )
    vectors = np.asarray(raw, dtype=np.float32)
    return cast(list[list[float]], vectors.tolist())


def similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Calcule la similarité cosinus entre deux vecteurs normalisés.

    Args:
        vec_a: Premier vecteur (dimension 1024).
        vec_b: Deuxième vecteur (dimension 1024).

    Returns:
        Score entre 0.0 (aucun rapport) et 1.0 (identiques).
    """
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    return float(np.dot(a, b))

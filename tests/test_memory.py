"""Tests d'intégration pour le domaine memory."""

from __future__ import annotations

import math
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest

from maeva_deal_radar_v2.memory.embedder import (
    EMBEDDING_DIM,
    embed,
    embed_batch,
    similarity,
)
from maeva_deal_radar_v2.memory.vector_store import (
    count,
    get_all,
    search_similar,
    upsert_lead,
)


class TestEmbedder:
    """Tests du module embedder."""

    def test_embed_returns_correct_dimension(self) -> None:
        """Un embedding doit avoir exactement 1024 dimensions."""
        vector = embed("Astorg Private Equity Paris")
        assert len(vector) == EMBEDDING_DIM

    def test_embed_returns_floats(self) -> None:
        """Chaque élément du vecteur doit être un flottant."""
        vector = embed("LBO France mid-market")
        assert all(isinstance(v, float) for v in vector)

    def test_embed_normalized(self) -> None:
        """Le vecteur doit être normalisé (norme L2 proche de 1.0)."""
        vector = embed("IK Partners deal flow")
        norm = math.sqrt(sum(v * v for v in vector))
        assert abs(norm - 1.0) < 1e-5

    def test_embed_batch_consistent(self) -> None:
        """embed_batch doit produire le même résultat qu'embed() sur chaque texte."""
        texts = ["Ardian", "Eurazeo", "PAI Partners"]
        single = [embed(t) for t in texts]
        batch = embed_batch(texts)
        assert len(batch) == len(texts)
        for s, b in zip(single, batch, strict=True):
            sim = similarity(s, b)
            assert sim > 0.9999

    def test_embed_batch_empty(self) -> None:
        """embed_batch sur liste vide doit retourner liste vide."""
        assert embed_batch([]) == []

    def test_similarity_identical(self) -> None:
        """La similarité d'un vecteur avec lui-même doit être 1.0."""
        vector = embed("Capza Private Equity")
        sim = similarity(vector, vector)
        assert abs(sim - 1.0) < 1e-5

    def test_similarity_semantic(self) -> None:
        """Deux textes sémantiquement proches doivent avoir une similarité élevée."""
        v_astorg = embed("Astorg Private Equity fonds mid-market France")
        v_lbo = embed("LBO France fonds mid-market investissement")
        v_meteo = embed("météo Paris aujourd'hui pluie nuages")
        sim_pe = similarity(v_astorg, v_lbo)
        sim_off = similarity(v_astorg, v_meteo)
        assert sim_pe > sim_off


class TestVectorStore:
    """Tests du module vector_store."""

    @pytest.fixture(autouse=True)
    def setup_test_data(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> Generator[None, None, None]:
        """Insère des leads de test avant chaque test.

        Utilise un UUID pour garantir l'unicité du chemin entre tests.
        monkeypatch restaure DB_PATH automatiquement après chaque test.
        """
        import maeva_deal_radar_v2.memory.vector_store as vs

        unique_db = tmp_path / f".lancedb_{uuid.uuid4().hex[:8]}"
        monkeypatch.setattr(vs, "DB_PATH", unique_db)

        upsert_lead(
            lead_id="test-astorg",
            company_name="Astorg",
            content="Astorg fonds levée capital investissement portefeuille",
            signal_type="HIRING",
            qualification_status="KEEP",
            confidence_score=0.9,
        )
        upsert_lead(
            lead_id="test-lbo",
            company_name="LBO France",
            content="LBO France closing fonds capital investissement mid-market",
            signal_type="EXPANSION",
            qualification_status="KEEP",
            confidence_score=0.85,
        )
        upsert_lead(
            lead_id="test-stop",
            company_name="Job Board PE",
            content="offres emploi recrutement carrières postes à pourvoir",
            signal_type="UNKNOWN",
            qualification_status="STOP",
            confidence_score=0.1,
        )
        yield

    def test_count_after_upsert(self) -> None:
        """Le compteur doit refléter les leads insérés."""
        assert count() >= 3

    def test_search_returns_results(self) -> None:
        """Une recherche doit retourner des résultats."""
        results = search_similar("fonds investissement mid-market", k=2)
        assert len(results) >= 1

    def test_search_relevance(self) -> None:
        """Leads PE doivent être plus similaires entre eux qu'avec un job board."""
        results = search_similar(
            "closing fonds levée capital investissement", k=3
        )
        companies = [r["company_name"] for r in results]
        assert "Job Board PE" not in companies[:2]

    def test_search_with_filter(self) -> None:
        """Le filtre par qualification_status doit fonctionner."""
        results = search_similar(
            "investissement", k=5, qualification_filter="KEEP"
        )
        assert all(r["qualification_status"] == "KEEP" for r in results)

    def test_get_all(self) -> None:
        """get_all doit retourner tous les leads."""
        all_leads = get_all()
        assert len(all_leads) >= 3

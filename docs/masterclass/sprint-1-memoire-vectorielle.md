# Sprint 1 — Mémoire vectorielle avec LanceDB et bge-m3

Date : Sprint 1 — Durée réelle : environ 3 heures — Statut : terminé

## Contexte avant cette étape

Le Sprint 0 a posé les fondations : dépôt, outillage, modèles Pydantic.
Mais le projet ne fait encore rien d'intelligent. L'objectif du Sprint 1 :
transformer les 172 décisions de qualification de Maeva (KEEP/STOP/CORRECT)
en capital algorithmique permanent via un index vectoriel.

Après ce sprint, le système peut trouver des leads similaires à ceux que
Maeva a approuvés, et déduplication sémantique des sources.

## Le choix du modèle : bge-m3 en local

Deux options en 2026 : OpenAI text-embedding-3-small (API) ou BAAI/bge-m3
via sentence-transformers (local, gratuit). On a choisi bge-m3 parce que la
prospection M&A mélange français et anglais (bge-m3 est multilingue natif),
et on évite une dépendance API sur une couche aussi centrale. Dimension de
sortie : 1024 flottants par texte.

## Architecture des deux modules

memory/embedder.py expose trois fonctions :

    embed(text) -> list[float]
    embed_batch(texts) -> list[list[float]]
    similarity(vec_a, vec_b) -> float

Le modèle est chargé une seule fois via @lru_cache(maxsize=1). Charger un
modèle de deep learning prend 2 à 10 secondes — on ne peut pas se permettre
de le recharger à chaque appel. normalize_embeddings=True produit des vecteurs
L2-normalisés : la similarité cosinus devient équivalente au produit scalaire.

memory/vector_store.py expose quatre fonctions :

    upsert_lead(lead_id, company_name, content, ...) -> None
    search_similar(query, k, qualification_filter) -> list[dict]
    get_all() -> list[dict]
    count() -> int

LanceDB est une base vectorielle embarquée (comme SQLite, mais pour les
vecteurs). Pas de serveur. Les données vivent dans .lancedb/ ignoré par Git.

## Les trois incidents de débogage

### Incident 1 : types mypy et bibliothèques tierces

sentence-transformers et lancedb n'ont pas de stubs mypy complets. En mode
strict, mypy génère des faux positifs. Solution en deux couches :

    [[tool.mypy.overrides]]
    module = ["sentence_transformers.*", "torch.*", "lancedb.*", "pyarrow.*"]
    ignore_missing_imports = true
    ignore_errors = true

Et cast() de typing pour les retours où on connaît le type réel :

    vector = cast(list[float], np.asarray(raw).tolist())

Distinction clé : ignore_errors neutralise les erreurs DANS le module tiers,
pas dans notre code. Pour notre code, cast() est la bonne réponse.

### Incident 2 : Table 'leads' already exists

Les tests VectorStore échouaient avec ValueError alors que list_tables()
renvoyait False. Deux causes combinées :

1. list_tables() en LanceDB 0.30.x renvoie un itérateur paresseux — le
   matérialiser avec list() corrige le check.
2. Entre deux tests, pytest peut réutiliser le même tmp_path.

Solution :
- list(db.list_tables()) pour matérialiser l'itérateur
- try/except sur create_table() comme fallback robuste
- UUID dans le chemin de test pour garantir l'unicité
- monkeypatch au lieu de patching manuel pour restauration automatique

### Incident 3 : pandas requis par to_pandas()

get_all() utilisait table.to_pandas() qui requiert pandas (non installé).
Fix : table.to_arrow().to_pylist() qui n'utilise que pyarrow.

Règle : préférer les méthodes natives des bibliothèques installées plutôt
que des conversions qui introduisent des dépendances implicites.

## La triade qualité au vert

12 tests passent en 52 secondes (modèle en cache) :

7 tests TestEmbedder : dimension 1024, types float, normalisation L2,
cohérence embed/embed_batch, liste vide, similarité identique, pertinence
sémantique (PE vs météo).

5 tests TestVectorStore : compteur après upsert, résultats non vides,
pertinence (job board écarté du top 2), filtre par statut, get_all sans
pandas.

## Concept clé : la similarité cosinus

La similarité cosinus mesure l'angle entre deux vecteurs à 1024 dimensions.
Cosinus proche de 1 : vecteurs parallèles (textes proches). Cosinus proche
de 0 : vecteurs orthogonaux (textes sans rapport).

Exemple observé dans les tests :
similarity(v_astorg_PE, v_lbo_PE) > similarity(v_astorg_PE, v_meteo)
bge-m3 sait qu'Astorg Private Equity est plus proche de LBO France
mid-market que de météo Paris pluie.

## État final du projet

Commits : 10
Modules memory : embedder.py, vector_store.py
Tests : 15 au total (12 memory + 3 sanité)
Modèle : BAAI/bge-m3 en cache dans ~/.cache/huggingface/

## Prochaine étape

Sprint 2 — Qualifier apprenant : utiliser les 172 décisions historiques
de Maeva comme dataset d'évaluation pour un qualifier basé sur un reasoning
model, avec harness de mesure de la qualité des décisions.
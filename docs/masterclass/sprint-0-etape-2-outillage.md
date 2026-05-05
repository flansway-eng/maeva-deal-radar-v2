# Sprint 0 — Étape 2 : Outillage qualité, secrets et premiers modèles

> **Date** : Sprint 0
> **Durée réelle** : environ 2 heures
> **Statut** : terminé

## Le contexte avant cette étape

L'étape 1 a posé les fondations du dépôt : structure Git, Python 3.12,
arborescence de dossiers, documentation. Mais le projet ne contient encore
aucun code métier et aucune convention de qualité. Sans outillage, chaque
développeur invente ses propres règles, et le code diverge rapidement.

Cette étape installe la discipline de code qui empêche le projet de dériver
sur la durée. Pas de fonctionnalité visible — uniquement de l'infrastructure
de qualité. Investissement de 2 heures aujourd'hui, centaines d'heures
gagnées sur la durée du projet.

## Ce qu'on a installé et pourquoi

### Ruff — linter et formateur

Ruff remplace en 2026 trois outils distincts : flake8 (linting), black
(formatage), isort (ordre des imports). Il est 10 à 100 fois plus rapide
que ses prédécesseurs parce qu'il est écrit en Rust.

Installation via uv :

    uv add --dev ruff

Configuration dans pyproject.toml :

    [tool.ruff]
    line-length = 88
    target-version = "py312"
    src = ["src"]

    [tool.ruff.lint]
    select = ["E", "W", "F", "I", "B", "UP"]
    ignore = ["E501"]

Le jeu de règles UP (pyupgrade) est particulièrement utile : il détecte
les patterns Python obsolètes et les signale. Exemple vécu dans cette
étape : UP042 signale que (str, Enum) est remplacé par StrEnum en
Python 3.11+. Ruff nous a appris quelque chose qu'on ne savait pas.

Workflow recommandé :

    uv run ruff check --fix src/ tests/   # corrige les erreurs auto
    uv run ruff check src/ tests/         # vérifie qu'il ne reste rien

### Mypy — vérification de types statique

Mypy analyse le code sans l'exécuter et détecte les erreurs de types.
En mode strict, il exige que toutes les fonctions soient typées et que
les types soient cohérents.

    uv add --dev mypy

Configuration :

    [tool.mypy]
    python_version = "3.12"
    strict = true
    plugins = ["pydantic.mypy"]

Le plugin pydantic.mypy est essentiel : sans lui, mypy ne comprend pas
les modèles Pydantic et génère des faux positifs.

### Pytest — framework de tests

    uv add --dev pytest

Configuration :

    [tool.pytest.ini_options]
    testpaths = ["tests"]
    python_files = ["test_*.py"]
    python_functions = ["test_*"]
    addopts = "-v --tb=short"

Premier test écrit : un test de sanité dans tests/test_sanity.py qui
vérifie que le package s'importe, que Python est bien en 3.12+, et que
Pydantic v2 est disponible. Ce n'est pas un test métier — c'est un test
de l'environnement lui-même.

### La règle de séparation prod / dev

uv distingue deux types de dépendances :

    uv add pydantic python-dotenv      # dépendances de production
    uv add --dev ruff pytest mypy      # dépendances de développement

En production, on installe uniquement les dépendances prod :

    uv sync --no-dev

Cela réduit la surface d'attaque et le temps d'installation. Ruff,
pytest, mypy n'ont rien à faire sur un serveur de production.

## La gestion des secrets

Deux fichiers, deux rôles opposés :

.env.example — committé dans Git. Contient les noms des variables sans
leurs valeurs réelles. Sert de documentation et de template.

.env — jamais committé. Contient les vraies valeurs. Ignoré par
.gitignore. Chargé au démarrage par python-dotenv.

La règle absolue : si une clé API atterrit dans Git, même une seconde,
elle est compromise. Il faut la révoquer immédiatement sur la plateforme
qui l'a émise. L'historique Git est public et indexé.

Le module shared/config.py centralise le chargement des variables :

    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        anthropic_api_key: str = Field(default="")
        ...
        model_config = {"env_file": ".env"}

    @lru_cache
    def get_settings() -> Settings:
        return Settings()

Le décorateur @lru_cache crée un singleton : les Settings ne sont
chargées qu'une fois, au premier appel. Les appels suivants utilisent
le cache. C'est le pattern standard pour les configurations applicatives.

## La structure des domaines métier

On a créé les six dossiers de domaines métier qui étaient dans notre
plan depuis le début mais n'existaient pas encore sur disque :

    src/maeva_deal_radar_v2/
    ├── signals/        # captation des signaux externes
    ├── qualification/  # qualifier apprenant
    ├── memory/         # graphe + vecteurs + SQLite
    ├── outreach/       # messages et séquences
    ├── pilotage/       # serveur MCP et dashboards
    └── shared/         # types et configuration communs

Chaque dossier est un domaine métier autonome avec son __init__.py.
Les domaines ne se connaissent que via les types définis dans shared/.

## Les premiers modèles Pydantic

Trois modèles dans shared/models.py couvrent le cœur du pipeline :

Signal — information brute captée sur une source externe. Champs clés :
source_url, content_snippet, signal_type (enum StrEnum), confidence_score
(float entre 0 et 1).

Lead — société cible construite à partir d'un ou plusieurs signaux.
Champs clés : company_name, sector, geography, qualification_status,
confidence_score.

OutreachTask — tâche d'approche planifiée. Champs clés : sequence_uid,
company, step_code (validé par regex), channel, message_body,
sequence_status.

Ces trois modèles correspondent aux tables SQLite de la v1.
On ne réinvente pas — on formalise avec des types stricts.

## Leçon : le piège UP042

Ruff a signalé quatre violations UP042 dans models.py :

    class SignalType(str, Enum):   # pattern Python 3.10
    class SignalType(StrEnum):     # pattern Python 3.11+

Ces violations ne sont pas auto-fixables en mode safe parce que StrEnum
a quelques différences de comportement subtiles. Ruff nous laisse décider.

La correction : remplacer from enum import Enum par from enum import
StrEnum, et supprimer str des héritages. Simple, moderne, propre.

La leçon : les règles UP ne signalent pas des bugs — elles signalent
des opportunités de modernisation. C'est le type de feedback continu
qu'un linter doit fournir.

## La triade qualité au vert

À la fin de cette étape, les trois outils passent sur l'ensemble du code :

    uv run ruff check src/ tests/   → All checks passed!
    uv run mypy src/                → Success: no issues found in 9 source files
    uv run pytest                   → 3 passed in 0.08s

C'est l'état qu'on vise à maintenir à chaque commit sur toute la durée
du projet. Si l'un des trois échoue avant un commit, on ne commit pas.

## État final du projet après cette étape

Commits : 8 (5 précédents + 3 nouveaux)
Dépendances prod : pydantic, python-dotenv, pydantic-settings
Dépendances dev : ruff, pytest, mypy
Modèles Pydantic : Signal, Lead, OutreachTask
Tests : 3 tests de sanité
Secrets : .env.example committé, .env ignoré

## Prochaine étape

Sprint 1 — Mémoire vectorielle : ajout de LanceDB comme index vectoriel,
embedding des 172 décisions historiques de Maeva, et premier module de
déduplication sémantique dans memory/.

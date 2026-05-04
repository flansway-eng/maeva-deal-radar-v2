# Maeva Deal Radar Room v2

> Refonte 2026 du copilote de prospection M&A/PE de Maeva.
> Architecture événementielle, modulaire, apprenante — Python 3.12 + uv.

## Pourquoi ce projet

La v1 du Deal Radar Room accompagne déjà la prospection M&A/PE de Maeva avec
100 tâches actives et un historique de 172 décisions humaines journalisées.
Le système fonctionne mais a atteint les limites d'une architecture batch :
pipeline séquentiel, scripts à lancer à la main, logique métier mélangée
dans un dossier core/ fourre-tout.

La v2 vise à passer à une architecture événementielle, modulaire et apprenante,
sans casser la v1 qui continue de tourner pendant la construction de la nouvelle.

Principe directeur : transformer le flux de jugements humains de Maeva en
capital algorithmique qui s'accumule, plutôt que de le perdre après usage.

## Architecture cible

Cinq domaines métier autonomes, plus un module de types partagés :

- signals/ — captation des signaux (Pappers, BODACC, Tavily, RSS sectoriels)
- qualification/ — qualifier apprenant basé sur les 172 décisions historiques
- memory/ — graphe de connaissances + vecteurs + état SQLite
- outreach/ — génération de messages, séquences, multi-armed bandit
- pilotage/ — serveur MCP, dashboards, contrôle conversationnel
- shared/ — modèles Pydantic et types communs

## Documentation

- Masterclass pédagogique : docs/masterclass/ — récit pas-à-pas du projet,
  sprint après sprint, conçu pour être lu de manière autonome.
- Décisions d'architecture : docs/decisions/ — ADR au format standard
  (Context / Decision / Consequences), datés et immuables.
- Vue d'ensemble : docs/architecture/ — schémas et explications globales.

## Statut

Sprint 0 en cours — fondations du projet (init, structure, conventions).

## Stack technique

- Python 3.12 (épinglé via .python-version)
- uv pour la gestion de dépendances et l'environnement virtuel
- Pydantic v2 pour les modèles de données (à venir)
- SQLite pour l'état (à venir)
- LanceDB pour l'index vectoriel (sprint 1)
- Inngest pour le bus d'événements (sprint 3)

## Licence

À définir.

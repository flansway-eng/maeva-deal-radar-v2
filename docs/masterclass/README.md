# Masterclass — Construire un copilote de prospection M&A en 2026

Cette masterclass raconte, sprint après sprint, étape après étape, la refonte
complète d'un système de prospection M&A/PE en architecture événementielle
moderne. Elle est rédigée à chaud, au fil de la construction du projet
Maeva Deal Radar Room v2.

## À qui s'adresse cette masterclass

Public intermédiaire : développeurs ayant déjà écrit du code Python, Git,
un peu de SQL, mais qui découvrent l'architecture logicielle, les patterns
événementiels, l'IA agentique et l'outillage moderne 2026.

Pas besoin d'être expert en M&A ou en private equity pour suivre — le métier
sert de prétexte pour explorer des concepts d'ingénierie réutilisables ailleurs.

## Comment lire cette masterclass

Chaque fiche est autonome : on peut la lire sans avoir lu les précédentes.
Les commandes sont copiables, les diagnostics sont expliqués, et chaque
décision d'architecture renvoie vers un ADR (docs/decisions/) qui en détaille
le contexte.

Trois types d'éléments dans chaque fiche :

- Le quoi : la liste factuelle des actions menées.
- Le pourquoi : le raisonnement d'architecture derrière chaque choix.
- Le piège évité : ce qui aurait pu mal tourner et la leçon à en tirer.

## Sprints prévus

Sprint 0 — Fondations (init, structure, conventions) — En cours
Sprint 1 — Mémoire vectorielle et déduplication sémantique — À venir
Sprint 2 — Qualifier apprenant et harness d'évaluation — À venir
Sprint 3 — Sources françaises en streaming et bus d'événements — À venir
Sprint 4 — Boucle fermée et pilotage MCP — À venir
Sprint 5 — Graphe de connaissances (optionnel) — À venir

## Conventions de la masterclass

- Code dans les fiches : reproductible tel quel, copier-coller direct.
- Sorties terminal : reproduites fidèlement, y compris les erreurs.
- Frictions traversées : documentées, parce qu'elles font partie du métier.
- Choix d'architecture : explicités, jamais implicites.

## Pourquoi cette discipline

Une masterclass écrite après-coup ment toujours un peu : on lisse, on oublie
les détours, on présente une trajectoire propre qui n'a jamais existé. Cette
masterclass est écrite à chaud, sprint après sprint, ce qui préserve la
matière vraie : les hésitations, les pièges, les diagnostics. C'est ce qui
en fait, j'espère, une ressource utile à quelqu'un qui construit son propre
projet en parallèle de sa lecture.

## Pour suivre les mises à jour

Ce dépôt évolue à mesure que les sprints avancent. Pour suivre, il suffit de
regarder l'historique des commits sur main et le diff du dossier
docs/masterclass/.

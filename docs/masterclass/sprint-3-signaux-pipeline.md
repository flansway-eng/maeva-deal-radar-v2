# Sprint 3 — Signaux et pipeline de captation

Date : Sprint 3 — Durée réelle : environ 2 heures — Statut : terminé

## Contexte avant cette étape

Les Sprints 1 et 2 ont donné au système une mémoire (LanceDB + bge-m3)
et un jugement (qualifier Claude). Sprint 3 lui donne des yeux : les
modules qui surveillent les sources françaises spécialisées et détectent
les signaux d'activité M&A/PE en temps réel.

L'objectif : connecter les trois sprints en un pipeline complet.
Source → Signal brut → Qualification → Stockage LanceDB.

## Architecture des quatre modules

### signals/base.py — Le contrat commun

Deux classes abstraites :

RawSignal (Pydantic) : représentation normalisée d'un signal brut,
quel que soit la source. Champs : source_name, source_url, company_name,
content, signal_type, geography, detected_at, raw_metadata.
La propriété lead_id est un hash SHA256 de company_name + source_url —
identifiant unique déterministe, sans base de données.

BaseSignalSource (ABC) : interface que toute source doit implémenter.
Une seule méthode abstraite : fetch(max_results) -> list[RawSignal].
Le pipeline ne sait pas si c'est BODACC ou Pappers — il appelle fetch().
C'est le pattern Strategy appliqué aux sources de données.

### signals/bodacc.py — La source légale française

BODACC (Bulletin Officiel des Annonces Civiles et Commerciales) publie
les modifications légales d'entreprises avant la presse. Aucune clé API.

Incident de débogage important : la première version filtrait les
départements IDF après avoir récupéré les données. L'API renvoyait 100
annonces nationales, aucune IDF. Fix : passer le filtre directement dans
la requête API via le paramètre where de l'API OpenDataSoft :

    where=numerodepartement="75" or numerodepartement="77" ...

Autre incident : les noms de champs supposés (denominationsociale,
typeannonce) n'existaient pas. L'inspection de la réponse réelle a
révélé les vrais noms : commercant, familleavis. Leçon : toujours
inspecter la réponse API avant d'écrire le parser.

### signals/rss.py — Les flux médias spécialisés

Parseur RSS générique qui accepte n'importe quelle URL de flux.
Un filtre de mots-clés (private equity, LBO, acquisition, levée,
closing...) élimine les articles non-pertinents.

Incident : CFNEWS et AGEFI bloquent l'accès automatisé (paywall,
bozo=1). Sources de substitution retenues : BFM Business, Le Monde
Economie. Le module reste générique — ajouter une source = ajouter
un dict dans DEFAULT_RSS_SOURCES.

### signals/pappers.py — Les données légales enrichies

Pappers agrège INPI + greffe + BODACC avec des données enrichies
(dirigeants, capital, statuts). Clé API requise (gratuit 100 req/jour).

Incident sécurité : la clé API apparaissait en clair dans les logs httpx
(paramètre GET dans l'URL). En production, passer les credentials en
header Authorization plutôt qu'en query parameter. En développement,
passer le niveau de log à WARNING pour masquer les URLs complètes.

Incident 401 : la clé était valide mais le compte venait d'être créé.
Pappers exige une validation d'email avant d'activer l'accès API.
Leçon : toujours vérifier l'email de confirmation après inscription.

### signals/pipeline.py — L'orchestrateur

Le pipeline fait quatre choses dans l'ordre :

1. Collecte : appelle fetch() sur chaque source.
2. Déduplication : élimine les doublons via lead_id (hash SHA256).
   Deux URLs différentes parlant de la même société ne créent qu'un lead.
3. Qualification : appelle Claude sur chaque signal unique.
4. Stockage : les KEEP sont upsertés dans LanceDB avec leur vecteur bge-m3.

La classe PipelineResult capture les statistiques :
signals_fetched, signals_qualified, leads_kept, leads_stopped, leads_review.

## Le premier run en production

Résultat du premier pipeline réel :

    [bodacc] 3 signaux récupérés
    [rss] 1 signal récupéré
    Qualification de 4 signaux uniques...
    [ 1/4] International Property Management → STOP (immobilier, hors PE)
    [ 2/4] Herouf, Mélisa, Emilien          → STOP (micro-entreprise individuelle)
    [ 3/4] Hossain, Shaon                   → STOP (micro-entreprise individuelle)
    [ 4/4] "Le premier trimestre..."        → STOP (actualité générale, pas PE)
    PIPELINE : 4 récupérés, 4 qualifiés — KEEP: 0 | STOP: 4

0 KEEP, 100% STOP. Premier réflexe : "ça ne marche pas". Mauvais réflexe.
Le bon réflexe : "le système fonctionne parfaitement".

BODACC IDF ce jour-là contenait des créations de micro-entreprises
individuelles et une cession immobilière. Aucun fonds PE mid-market
ne dépose d'annonce légale tous les jours. Le qualifier élimine
correctement le bruit.

La précision est de 100% : aucun faux positif. Le système ne garde
que ce qui mérite l'attention de Maeva. Un pipeline qui dit STOP sur
du bruit est un pipeline qui fonctionne.

## Les trois sprints connectés

Pour la première fois, les trois systèmes du projet tournent ensemble :

Source externe → RawSignal (Sprint 3)
             → qualify_lead() Claude (Sprint 2)
             → upsert_lead() LanceDB + bge-m3 (Sprint 1)

C'est l'architecture cible décrite au Sprint 0 qui devient réelle.

## Concepts clés

Le pattern Strategy : BaseSignalSource définit une interface, chaque
source l'implémente. Le pipeline appelle fetch() sans savoir ce qu'il
y a derrière. Ajouter une source = créer une classe, pas modifier le
pipeline.

La déduplication par hash : lead_id = SHA256(company + source_url).
Deux découvertes de la même société depuis deux URLs différentes ont des
lead_id différents et sont traités séparément — ce qui est correct.
Deux découvertes identiques (même URL) ont le même lead_id et la seconde
écrase la première dans LanceDB (upsert).

L'inspection API avant le parser : ne jamais supposer les noms de champs
d'une API. Toujours récupérer un exemple de réponse et lire les clés
réelles avant d'écrire le parser. Économise des heures de débogage.

## État final du projet

Commits : 15
Modules signals : base.py, bodacc.py, rss.py, pappers.py, pipeline.py
Sources actives : BODACC IDF (100%), RSS BFM/Le Monde (partiel), Pappers (en attente validation)
Premier run : 4 signaux qualifiés, 100% de précision

## Prochaine étape

Sprint 4 — Pilotage MCP : serveur MCP qui expose les opérations du
système (run_pipeline, search_similar, get_all) comme des outils
utilisables depuis Claude.ai en langage naturel. Maeva pilote le
copilote sans ouvrir un terminal.
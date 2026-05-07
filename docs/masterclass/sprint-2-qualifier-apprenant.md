# Sprint 2 — Qualifier apprenant avec Claude

Date : Sprint 2 — Durée réelle : environ 2 heures — Statut : terminé

## Contexte avant cette étape

Le Sprint 1 a donné au système une mémoire vectorielle. Il peut stocker
des leads et trouver des leads similaires. Mais il ne sait pas encore
évaluer si un lead est bon ou mauvais pour Maeva.

L'objectif du Sprint 2 : qualifier automatiquement chaque lead détecté
en KEEP, STOP ou REVIEW, avec une justification, en utilisant Claude
comme reasoning model. Et mesurer cette qualification sur un dataset
de référence avant de l'utiliser en production.

## La décision clé : mesurer avant de construire

Le pattern qu'utilisent les équipes ML sérieuses : on construit le
système de mesure (le harness) avant le système à mesurer (le qualifier).
Cela force à définir explicitement ce qu'est "bon" avant d'écrire le
code qui doit être bon.

Pour ce sprint, on a conçu 30 cas synthétiques couvrant :
- 10 cas KEEP clairs (fonds PE réels IDF mid-market)
- 10 cas STOP clairs (job boards, annuaires, presse)
- 10 cas REVIEW ambigus (banques M&A, family offices, fonds adjacents)

Le dataset vit dans tests/fixtures/eval_cases.json et est committé dans
Git. Note importante : data/ est dans .gitignore pour les données Maeva
sensibles. Les fixtures de test sont dans tests/fixtures/ qui n'est pas
ignoré. Un dataset synthétique n'est pas une donnée sensible — il doit
être versionné.

## Architecture des trois modules

### qualification/schemas.py

Quatre types Pydantic :

QualificationDecision — StrEnum avec KEEP, STOP, REVIEW.

QualificationResult — ce que retourne le qualifier : decision,
confidence (0.0 à 1.0), justification (texte), raw_reasoning.

EvalCase — un cas d'évaluation : inputs du lead + human_decision
comme ground truth.

EvalReport — rapport agrégé : accuracy, précision/rappel/F1 par classe,
liste des erreurs avec justifications.

### qualification/qualifier.py

Le qualifier appelle Claude Sonnet via l'API Anthropic en utilisant
le mécanisme tool_use. Au lieu de demander du JSON en texte libre
(fragile), on déclare un outil avec un schéma strict :

    QUALIFY_TOOL = {
        "name": "qualify_lead",
        "input_schema": {
            "properties": {
                "decision": {"enum": ["KEEP", "STOP", "REVIEW"]},
                "confidence": {"type": "number"},
                "justification": {"type": "string"},
            }
        }
    }

Claude est obligé de remplir ce schéma. Output structuré garanti,
jamais de JSON malformé à parser.

Le prompt système décrit précisément les critères de Maeva : fonds PE
mid-market IDF, deal teams actives, signal récent. Et ce qu'elle ne
cherche pas : job boards, annuaires, formations, fonds infrastructure.

### qualification/harness.py

Le harness charge les 30 cas, appelle le qualifier avec un délai entre
chaque appel (évite le rate limiting), compare les décisions, et calcule
précision/rappel/F1 par classe.

## Les résultats de l'évaluation

Accuracy globale : 73.3% (22/30 corrects)
F1-KEEP : 0.80
F1-STOP : 0.87

Mais l'accuracy globale est trompeuse. Le détail révèle quelque chose
de plus intéressant :

KEEP : 10/10 corrects (100%)
STOP : 10/10 corrects (100%)
REVIEW : 2/10 corrects (20%)

Claude est parfait sur les cas non-ambigus. Il échoue uniquement sur
les cas REVIEW — et pour une raison instructive.

## La vraie leçon : les erreurs ne sont pas des erreurs

Les justifications de Claude sur les cas REVIEW "erronés" sont
remarquablement cohérentes :

Sur Lazard, Rothschild, PwC Transaction Services, ICG → Claude dit
KEEP. Ces acteurs ont des deal teams actives, des signaux récents, et
correspondent aux critères Maeva. Claude a raison de les vouloir garder.

Sur Meridiam, Altaroc, TotalEnergies → Claude dit STOP. Infrastructure,
retail PE et corporate venture sont explicitement hors scope dans le
prompt. Claude a raison de les éliminer.

REVIEW est une catégorie qui signifie "je ne sais pas". Claude, lui,
sait. Il prend une décision tranchée là où nos labels étaient hésitants.

La métrique qui compte vraiment pour Maeva : zéro faux négatif sur les
vrais leads (jamais un KEEP envoyé en STOP). Ce critère est respecté à
100%.

Un système de qualification utilisable en production n'est pas un système
qui reproduit tous les labels humains — c'est un système qui ne manque
jamais un vrai lead et élimine efficacement le bruit. Claude fait les deux.

## Les incidents techniques

### Overloads mypy et SDK Anthropic

L'appel client.messages.create() avec tools et tool_choice comme
dict[str, Any] ne matchait pas les overloads stricts du SDK Anthropic.
Solution : # type: ignore[call-overload] ciblé sur la ligne d'appel.
On ne baisse pas la strictness globale — on annote une exception
documentée sur une ligne précise.

### Le fichier eval_cases.json ignoré par Git

Premier commit : data/eval_cases.json ignoré parce que data/ est dans
.gitignore. Solution : déplacer vers tests/fixtures/eval_cases.json.
Règle apprise : les fixtures de test (données synthétiques) appartiennent
à tests/, pas à data/ qui est réservé aux données locales et sensibles.

## État final du projet

Commits : 13
Modules qualification : schemas.py, qualifier.py, harness.py
Dataset : 30 cas dans tests/fixtures/eval_cases.json
Résultat harness : 100% sur KEEP/STOP, 73.3% global
Modèle : claude-sonnet-4-5 via tool_use

## Prochaine étape

Sprint 3 — Signaux et bus d'événements : intégration des sources
françaises spécialisées (Pappers, BODACC, RSS CFNEWS/AGEFI) et
passage du pipeline batch à une architecture événementielle via Inngest.
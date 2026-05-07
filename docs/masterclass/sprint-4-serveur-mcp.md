# Sprint 4 — Serveur MCP : pilotage en langage naturel

Date : Sprint 4 — Durée réelle : environ 1h30 — Statut : terminé

## Contexte avant cette étape

Les trois premiers sprints ont construit les couches techniques :
mémoire vectorielle (Sprint 1), qualifier (Sprint 2), signaux (Sprint 3).
Le Sprint 4 expose tout ça à Maeva en langage naturel via le protocole MCP.

MCP (Model Context Protocol) est le standard d'Anthropic pour connecter
des systèmes externes à Claude. Un serveur MCP expose des outils que
Claude peut appeler. Maeva décrit ce qu'elle veut faire, Claude appelle
le bon outil, le système exécute l'action réelle.

Avant : Maeva ouvre un terminal, tape des commandes Python, lit des logs.
Après : Maeva tape dans Claude.ai, le copilote exécute et répond.

## Architecture du serveur

Le serveur vit dans pilotage/mcp_server.py. Il utilise FastMCP du SDK
officiel Anthropic (mcp==1.27.0). Chaque outil est une fonction Python
décorée avec @mcp.tool() :

    mcp = FastMCP("Maeva Deal Radar Room")

    @mcp.tool()
    def run_pipeline(max_signals_per_source: int = 5, sources: str = "bodacc,rss") -> str:
        ...

Le docstring de chaque fonction devient la description que Claude lit
pour décider quand et comment appeler l'outil. C'est le contrat entre
le développeur et le modèle.

## Les cinq outils exposés

run_pipeline — Lance la collecte + qualification des signaux.
Paramètres : max_signals_per_source (1-20), sources (bodacc,rss,pappers).
Retourne : résumé avec statistiques d'exécution.

search_leads — Recherche sémantique dans LanceDB via bge-m3.
Paramètres : query (texte libre), k (nombre de résultats), filter_status.
Retourne : liste de leads similaires avec scores de similarité.

qualify_single_lead — Qualifie un lead décrit manuellement.
Paramètres : company_name, source_url, description, signal_type, geography.
Retourne : décision KEEP/STOP/REVIEW avec justification Claude.

get_stats — Statistiques de la base LanceDB.
Paramètres : aucun.
Retourne : total leads, distribution par statut.

get_recent_leads — Derniers leads qualifiés.
Paramètres : limit (1-50), status_filter (KEEP/STOP/REVIEW/ALL).
Retourne : liste des leads correspondants.

## Installation et test

Installation du SDK :

    uv add "mcp[cli]"

mcp[cli] installe à la fois le SDK Python et les outils CLI dont
mcp dev pour l'inspecteur local.

Démarrage du serveur en mode debug :

    uv run mcp dev src/maeva_deal_radar_v2/pilotage/mcp_server.py

L'inspecteur ouvre automatiquement dans le navigateur Windows depuis WSL.
L'interface graphique avait un problème de rendu avec Edge sur WSL — la
page Outils restait blanche. Solution : tester les outils directement en
Python, ce qui est équivalent pour valider la logique.

## Le test de validation

    from maeva_deal_radar_v2.pilotage.mcp_server import get_stats, qualify_single_lead

    get_stats()
    # → "Base vide — aucun lead en base. Lancez d'abord run_pipeline."

    qualify_single_lead(
        company_name="Ardian",
        source_url="https://ardian.com/news",
        description="Ardian annonce le closing de son nouveau fonds mid-market à 3 milliards.",
        signal_type="fund_closing",
    )
    # → "✓ Décision : KEEP — Confiance : 95%"
    # → Justification : Ardian est un acteur majeur du PE mid-market en IDF.
    #   Le closing d'un fonds de 3 milliards constitue un signal fort...

Les deux outils répondent correctement. Le serveur MCP est opérationnel.

## Configuration Claude Desktop (Windows)

Pour brancher le serveur à Claude Desktop sur Windows, créer ou modifier
le fichier de configuration Claude Desktop :

    %APPDATA%\Claude\claude_desktop_config.json

Contenu :

    {
      "mcpServers": {
        "maeva-deal-radar": {
          "command": "wsl",
          "args": [
            "-e", "bash", "-c",
            "cd /home/maeva/mesLabos/maeva-deal-radar-v2 && uv run python -m maeva_deal_radar_v2.pilotage.mcp_server"
          ]
        }
      }
    }

Redémarrer Claude Desktop. Le serveur apparaît dans la liste des outils
disponibles. Maeva peut alors piloter le système en langage naturel.

## Concepts clés

Le protocole STDIO : le serveur MCP communique via stdin/stdout avec
Claude Desktop. Pas de port réseau, pas de configuration firewall.
Claude Desktop lance le serveur comme un sous-processus et lit ses
réponses sur stdout. Simple et robuste.

Les docstrings comme contrat : Claude lit les docstrings des outils pour
décider comment les utiliser. Un docstring mal rédigé produit de mauvais
appels. Un docstring précis avec des exemples produit des appels corrects.
C'est du prompt engineering dans le code Python.

Les imports différés : les imports lourds (bge-m3, LanceDB, Claude SDK)
sont faits à l'intérieur de chaque fonction outil, pas au niveau module.
Cela évite de charger 500 Mo de modèle au démarrage du serveur — le
modèle se charge uniquement quand un outil est réellement appelé.

## État final du projet

Commits : 17
Modules pilotage : mcp_server.py avec 5 outils
SDK : mcp==1.27.0 avec FastMCP
Test validé : qualify_single_lead → KEEP 95% sur Ardian

## Ce qu'il reste à faire

Valider la clé Pappers (crédits nécessaires sur moncompte.pappers.fr)
pour activer la troisième source de signaux.

Configurer Claude Desktop sur Windows pour le pilotage en production.

Réécrire les passages [VOTRE VOIX] dans les cinq fiches masterclass.

Relancer le pipeline régulièrement (quotidien ou hebdomadaire) pour
alimenter la base LanceDB avec de vrais leads IDF.
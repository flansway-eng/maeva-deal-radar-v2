# Sprint 0 — Étape 1 : Fondations du dépôt

> **Date** : Sprint 0
> **Durée réelle** : environ 5 heures (incluant les frictions diagnostiquées)
> **Statut** : terminé

## Le contexte avant cette étape

Maeva Deal Radar Room v1 est un système de prospection M&A/PE qui tourne
en production avec 100 tâches actives et 172 décisions humaines journalisées.
Le système fonctionne, mais il a atteint les limites d'une architecture batch :
chaque module se lance à la main, le pipeline est séquentiel, et la logique
métier s'entasse dans un dossier `core/` fourre-tout.

La v2 vise une refonte vers une architecture événementielle, modulaire et
apprenante. Cette étape pose les fondations du nouveau dépôt : pas encore
de fonctionnalité visible, mais des choix structurants qui conditionnent
tout le reste du projet.

## Le contrat de cette étape

À la fin de cette étape, on doit avoir :

- Un nouveau dépôt Git `maeva-deal-radar-v2` à côté de la v1
- Un projet Python initialisé proprement avec uv et Python 3.12
- Une structure de dossiers par domaines métier
- Un .gitignore enrichi pour le contexte du projet
- Un README projet et une structure de documentation
- Un dépôt GitHub public lié et synchronisé

## Le pré-requis : l'environnement

Avant toute commande, on confirme l'environnement disponible :

    pwd
    ls -la
    uv --version
    python3 --version
    git --version

Sortie attendue : un dossier vide, uv 0.9 ou plus récent, Python 3.12 ou plus
récent, Git 2.40 ou plus récent. Sur WSL Ubuntu 24, ces composants sont
disponibles ou installables en une commande.

## Sous-étape 1 : initialiser le projet Python avec uv

La commande clé :

    uv init --python 3.12 --package --name maeva-deal-radar-v2

Trois flags méritent qu'on s'arrête sur leur signification :

- `--python 3.12` épingle la version Python du projet, ce qui crée
  un fichier `.python-version` qui sera lu par tous les outils compatibles.
- `--package` crée une structure de package Python proprement installable,
  avec `src/maeva_deal_radar_v2/` comme racine importable. Sans ce flag,
  on aurait juste un script jetable.
- `--name maeva-deal-radar-v2` force le nom du package, qui sinon serait
  déduit du nom du dossier.

uv crée alors : `pyproject.toml`, `README.md`, le dossier `src/`, et
initialise discrètement Git avec un `.gitignore` minimal et la branche
par défaut.

[VOTRE OBSERVATION : noter ici votre ressenti à ce moment précis — la
rapidité de uv comparée à pip + venv classique, ou tout autre détail
qui vous a frappé]

### Le piège : la corruption silencieuse du pyproject.toml

Premier incident significatif de la session. Après le `uv init`, le contenu
du `pyproject.toml` apparaissait étrange à l'inspection :

    readme = "[README.md](http://README.md)"
    email = "[flansway@gmail.com](mailto:flansway@gmail.com)"

Au lieu de `"README.md"` et `"flansway@gmail.com"` simples. Ce n'était pas
uv qui se comportait mal — c'était l'interface entre le clavier et le shell
qui markdownisait certains motifs au moment du copier-coller. uv a reçu des
chaînes corrompues et les a fidèlement écrites dans le fichier.

**Diagnostic** : la commande `cat -A pyproject.toml` confirme la corruption
en affichant les caractères bruts.

**Réparation** : édition manuelle du fichier pour rétablir les bonnes
chaînes, puis vérification avec `uv sync` qui valide la syntaxe.

**La leçon** : quand on travaille avec une IA via une interface qui peut
transformer le texte (markdown auto, élision), certains noms de fichiers
ou patterns peuvent être altérés silencieusement au copier-coller. La
parade : pour les contenus critiques, utiliser des outils qui produisent
du texte non-transformable (`cat -A`, captures d'écran), et préférer la
saisie au clavier au copier-coller pour les commandes courtes.

## Sous-étape 2 : forcer la branche main

uv (ou Git) crée par défaut une branche `master`. Le standard 2026 est
`main`. On rectifie :

    git branch -m master main
    cat .git/HEAD

La seconde commande affiche `ref: refs/heads/main` — confirmation que
l'intention est bien réglée.

### Subtilité Git à connaître

Tant qu'aucun commit n'a été fait, `git branch` ne renvoie rien — pas
même un `* main`. Pourquoi ? Parce qu'une branche Git est techniquement
un pointeur vers un commit. Sans commit, pas de pointeur, donc pas de
branche affichable. Pourtant, le fichier `.git/HEAD` contient bien
`ref: refs/heads/main` — c'est l'intention enregistrée. La branche se
matérialise au premier commit.

**La leçon** : une branche Git sans commit est une intention, pas une
réalité. C'est ce qui explique le silence apparent de `git branch` au
démarrage d'un projet.

## Sous-étape 3 : structure de dossiers par domaines métier

Le défaut le plus courant des projets Python qui grossissent : un dossier
`core/` qui devient un fourre-tout. Au bout de quelques mois, plus
personne ne sait ce qui dépend de quoi.

La solution adoptée pour Maeva Deal Radar Room v2 : découper par
**domaine métier** (bounded context au sens DDD) :

    src/maeva_deal_radar_v2/
    ├── signals/        # Captation Pappers, BODACC, Tavily, RSS
    ├── qualification/  # Qualifier apprenant
    ├── memory/         # Graphe + vecteurs + SQLite
    ├── outreach/       # Messages, séquences, bandit
    ├── pilotage/       # Serveur MCP, dashboards
    └── shared/         # Modèles Pydantic et types communs

Chaque dossier est autonome. Les domaines ne se connaissent que via les
types définis dans `shared/`. Pas de dépendance circulaire entre domaines.

**La règle** : si un domaine A doit utiliser quelque chose de B, ce
quelque chose remonte dans `shared/` ou dans une couche dédiée. Le
domaine A n'importe jamais directement depuis B.

[VOTRE VOIX : reformuler ici la philosophie du bounded context avec
votre propre métaphore — ça aide énormément les lecteurs à comprendre]

## Sous-étape 4 : enrichir le .gitignore

uv génère un `.gitignore` minimal de 9 lignes. Pour notre projet, on
ajoute des sections critiques :

- Secrets et credentials : `.env`, `.env.*`, `*.pem`, `*.key`
- Bases de données SQLite : `*.db`, `*.db-journal`
- Index vectoriel local : `.lancedb/`
- Caches d'outils : `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`
- Données et exports locaux : `data/`, `exports/`, `logs/`
- Fichiers Cursor : `.cursor/`
- Fichiers OS : `.DS_Store`, `Thumbs.db`

Le fichier final fait environ 70 lignes, organisé par sections avec
bandeaux. Une convention `.gitignore` méconnue mais utile : la négation
avec `!`. Par exemple `!.env.example` ré-inclut le fichier exemple
même si la ligne `.env.*` l'exclurait.

### Le piège : le conflit buffer Cursor / fichier disque

Deuxième incident. En écrivant le `.gitignore` d'abord via Cmd+K dans
Cursor, puis en le réécrivant via heredoc dans le terminal, Cursor a
détecté un conflit :

    Failed to save '.gitignore': The content of the file is newer.
    Please compare your version with the file contents or overwrite
    the content of the file with your changes.

**Diagnostic** : Cursor avait l'ancienne version en mémoire (buffer),
le terminal avait écrit la nouvelle version sur disque. Sauver la
version Cursor aurait écrasé la bonne.

**Réparation** : choisir "Compare", fermer l'onglet sans sauver, ouvrir
un terminal pour valider la version disque (`cat`, `wc -l`).

**La leçon** : Cursor garde un buffer en mémoire de chaque fichier
ouvert. Quand le fichier est modifié à l'extérieur de l'IDE, le buffer
devient obsolète. Si on sauve sans rafraîchir, on écrase la version
disque par l'ancienne version. Discipline : avant de modifier un
fichier en CLI alors qu'il est ouvert dans Cursor, fermer son onglet
ou utiliser "Revert File".

## Sous-étape 5 : premier commit

L'identité Git doit être configurée avant tout commit :

    git config --get user.name
    git config --get user.email

Si non configuré : `git config --global user.name "..."` et idem
pour `user.email`.

La séquence :

    git status                                       # voir l'état
    git add .                                        # stager tous les fichiers
    git status                                       # confirmer le staging
    git commit -m "chore: initialisation du projet v2 ..."

Convention adoptée : **Conventional Commits**. Format
`<type>(<scope>): <description>`. Pour ce premier commit, type `chore`
(tâche de maintenance, ni feature ni bugfix).

### Le piège : le commit prématuré

Troisième incident, et celui qui m'a coûté le plus de temps de
diagnostic. Lors du premier commit, le `README.md` racine était vide
(0 octet, créé par `uv init`). Je l'ai rempli APRÈS le commit, sans
faire un nouveau commit pour figer ce contenu.

Le lendemain matin, voulant restaurer un `README.md` corrompu via
`git checkout HEAD -- README.md`, Git m'a fidèlement redonné le
contenu enregistré au commit : un fichier vide. Mes 53 lignes de
contenu projet écrites entre temps n'avaient jamais été commitées,
donc Git ne pouvait pas les restaurer.

**La leçon** : `git checkout HEAD -- <fichier>` ne restaure que ce
qui a été committé. Si une modification n'a jamais atteint un
commit, Git ne peut pas la restaurer. La discipline professionnelle :
commit après chaque modification cohérente, même si on n'a pas fini.
Quitte à utiliser des `wip:` (work in progress) qu'on écrasera ensuite.

## Sous-étape 6 : authentification GitHub avec gh

Pour pousser le projet vers GitHub, on utilise GitHub CLI (`gh`) :

    sudo apt install gh -y
    gh auth login

`gh` propose un flow OAuth via navigateur : il génère un code à 8
caractères, ouvre le navigateur sur `github.com/login/device`, où on
saisit le code et on autorise.

### Le piège : le navigateur Windows depuis WSL

Quatrième incident. Sur WSL Ubuntu, `gh` cherche à ouvrir un
navigateur via `xdg-open`, `x-www-browser`, etc. Aucun de ces
utilitaires n'est installé par défaut sur WSL. Résultat :

    Failed opening a web browser at https://github.com/login/device
    exec: "xdg-open,x-www-browser,www-browser,wslview": executable
    file not found in $PATH

**Diagnostic** : WSL n'a pas la notion de navigateur préféré. Il faut
installer `wslu` qui fournit `wslview`, le pont vers le navigateur
Windows par défaut.

**Réparation** :

    sudo apt install wslu -y

Puis relancer `gh auth login`. Cette fois `wslview` ouvre Chrome (ou
Edge selon le navigateur par défaut Windows).

### Le second piège : le mauvais navigateur

Quand `wslview` ouvre Edge alors que vous êtes connecté à GitHub
sur Chrome, vous risquez de vous authentifier avec un mauvais compte.
Symptôme : `gh auth status` confirme une auth, mais sous une identité
inattendue.

**La leçon** : avant chaque OAuth device flow, vérifier dans quel
navigateur on est connecté à l'identité voulue, et router le flow
vers ce navigateur-là (en copiant l'URL si l'auto-ouverture ouvre
le mauvais).

### Le timing du device flow

Le device flow OAuth fonctionne en deux étapes synchronisées :
`gh` poll les serveurs GitHub en boucle ; quand vous cliquez
"Authorize" dans le navigateur, le prochain poll récupère le token.

**Si le poll a expiré entre temps**, votre validation côté navigateur
ne sert à rien — le terminal n'aura jamais le token. Symptôme :
`gh auth status` retourne *« You are not logged into any GitHub
hosts »* malgré la page de succès dans le navigateur.

**La parade** : ne pas traîner entre l'affichage du code et la
validation. Une dizaine de minutes maximum.

## Sous-étape 7 : créer le dépôt distant et pousser

Une fois `gh` authentifié sur le bon compte, une seule commande
crée le dépôt distant et y pousse le commit local :

    gh repo create maeva-deal-radar-v2 --public --source=. \
       --remote=origin --push --description "..."

Décomposition des flags :

- `--public` : visibilité publique
- `--source=.` : lier au dossier courant
- `--remote=origin` : nommer le remote distant `origin`
- `--push` : pousser immédiatement le commit local

Sortie attendue : trois lignes confirmant la création, l'ajout du
remote, et le push.

Vérifications post-push :

    git remote -v       # doit afficher origin avec l'URL HTTPS
    git branch -vv      # doit afficher main avec [origin/main]
    git log --oneline   # doit afficher le commit unique

Vérification visuelle dans le navigateur sur l'URL du dépôt :
le badge "Public", la description, l'arborescence, et le commit
visible.

## Sous-étape 8 : structure de documentation

Création de trois sous-dossiers dans `docs/` :

    docs/masterclass/   # le récit pas-à-pas du projet (ce fichier)
    docs/architecture/  # schémas et explications globales
    docs/decisions/     # ADR au format Context/Decision/Consequences

Chaque dossier reçoit un `README.md` minimal qui explique son rôle.
Les ADR seront numérotés (`0001-titre.md`, `0002-titre.md`, ...) et
datés, immuables une fois publiés.

### La méthode tee + variable

Après les frictions de copier-coller markdown qui avaient corrompu
les noms de fichiers, on adopte une méthode atomique :

    F=docs/masterclass/README.md
    echo "Cible: $F"
    tee "$F" > /dev/null << 'EOF'
    [contenu]
    EOF

Le passage par variable shell évite que le nom de fichier ne soit
markdownisé au copier-coller. La redirection vers `/dev/null` empêche
`tee` de recopier le contenu à l'écran. Le marqueur `EOF` entre
apostrophes empêche l'expansion de variables dans le contenu.

**La leçon** : pour les écritures de fichiers dont le nom contient
des extensions markdownisables (`.md`), passer par une variable
shell est la parade la plus fiable.

## Synthèse — concepts appris dans cette étape

Cette étape a posé six concepts d'ingénierie réutilisables bien
au-delà du projet :

1. **L'addition non-destructive en refonte logicielle** : on construit
   le nouveau système à côté de l'ancien et on ne bascule qu'une fois
   la valeur prouvée.

2. **Le bounded context** : découper un projet par domaine métier
   plutôt que par couche technique, pour empêcher le chaos de
   croissance.

3. **La discipline du commit ciblé** : un commit = une intention.
   Si on peut décrire un commit avec deux phrases qui n'ont rien à
   voir, c'est qu'il devrait être deux commits.

4. **Le commit non-prématuré** : ne jamais committer un fichier
   incomplet "pour le remplir plus tard". Soit on remplit avant le
   commit, soit on attend.

5. **La vérification asymétrique avant l'irréversible** : avant un
   `rm`, un `git push --force`, ou tout acte destructif, le coût
   d'une vérification supplémentaire est toujours inférieur au coût
   d'une erreur.

6. **Les outils non-transformables** : quand l'interface entre l'humain
   et le système ajoute des transformations cosmétiques, utiliser des
   outils qui produisent du texte brut (`cat -A`, `xxd`, captures
   d'écran de l'IDE) pour voir l'état réel.

## État final du projet après cette étape

- Dépôt local : `~/mesLabos/maeva-deal-radar-v2/`
- Dépôt distant : `https://github.com/flansway-eng/maeva-deal-radar-v2`
- Branche : `main` (locale et distante synchronisées)
- Commits : 4 (initial + 3 commits de documentation)
- Python : 3.12.3 dans `.venv/` géré par uv
- Identité Git : ARECIE SG <flansway@gmail.com>
- Auth GitHub : gh authentifié sur flansway-eng

[VOTRE OBSERVATION : ajouter ici un mot personnel — ce qui vous a
le plus surpris dans cette étape, ou la sensation au moment de voir
votre projet en ligne pour la première fois]

## Prochaine étape

Sprint 0 — Étape 2 : outillage qualité (ruff, pytest, mypy), gestion
des secrets via `.env`, et premiers modèles Pydantic dans `shared/`.

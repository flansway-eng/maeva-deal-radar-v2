# Guide Maeva — Deal Radar Room
## Votre copilote de prospection M&A/PE

---

## Accéder à l'application

Ouvrez votre navigateur et allez sur :

    https://maeva-deal-radar.onrender.com

Pas d'installation, pas de compte, pas de mot de passe.
L'application fonctionne directement dans le navigateur.

Note : si la page met 20-30 secondes à s'afficher la première fois,
c'est normal. Le serveur se réveille après une période d'inactivité.

---

## L'interface en un coup d'œil

L'écran est divisé en quatre sections :

TABLEAU DE BORD (haut gauche)
Affiche le nombre de leads actuellement en base.
Total, KEEP (à contacter), STOP (éliminés), REVIEW (à valider).

LANCER LE PIPELINE (haut droite)
Lance la recherche automatique de nouveaux signaux.

RECHERCHE SÉMANTIQUE (bas gauche)
Cherche dans vos leads existants par concept, pas par mot exact.

QUALIFIER UN LEAD (bas droite)
Évalue manuellement une société que vous avez découverte.

---

## Action 1 — Lancer le pipeline de captation

Le pipeline surveille trois sources :
- BODACC : annonces légales officielles (nominations, fusions, cessions)
- RSS : médias économiques français (BFM Business, Le Monde)
- Pappers : données légales enrichies (quand les crédits sont actifs)

Comment faire :
1. Sélectionnez les sources souhaitées en cliquant sur les boutons
   BODACC, RSS, Pappers (noir = actif, gris = inactif)
2. Cliquez sur "▶ Lancer la captation"
3. Le message "Pipeline lancé en arrière-plan" s'affiche — c'est normal
4. Attendez 30 à 60 secondes
5. Le tableau de bord se met à jour automatiquement

Quand lancer le pipeline :
- Le matin avant de commencer votre journée
- Après un événement de marché important (closing annoncé, levée de fonds)
- En début de semaine pour couvrir les annonces du week-end

Les leads qualifiés KEEP apparaissent automatiquement en bas de page.

---

## Action 2 — Rechercher des leads similaires

La recherche sémantique comprend le sens de votre requête,
pas juste les mots exacts. Vous pouvez écrire en langage naturel.

Exemples de recherches efficaces :

    fonds PE mid-market Paris récent
    closing annoncé Île-de-France
    équipe deal flow renforcée
    fonds levée capital investissement
    acquisition PME française

Comment faire :
1. Tapez votre requête dans le champ "Recherche sémantique"
2. Appuyez sur Entrée ou cliquez "🔍 Rechercher"
3. Les leads les plus proches sémantiquement s'affichent

Si aucun résultat : la base est peut-être vide. Lancez d'abord
le pipeline pour alimenter la base en leads.

---

## Action 3 — Qualifier un lead manuellement

Vous avez découvert une société intéressante lors de votre veille
(LinkedIn, presse spécialisée, recommandation) ? Soumettez-la
directement pour que Claude l'évalue selon vos critères.

Comment faire :
1. Remplissez les champs obligatoires (marqués *) :
   - Nom de la société : ex. "Weinberg Capital Partners"
   - URL source : la page web où vous avez trouvé l'information
   - Description : décrivez ce que vous avez observé (2-3 phrases)

2. Remplissez le type de signal si vous le connaissez :
   hiring         (recrutement d'équipe)
   expansion      (ouverture, croissance)
   deal_announced (transaction annoncée)
   fund_closing   (closing de fonds)
   leadership_change (changement de dirigeant)

3. Cliquez "⚡ Qualifier"
4. La décision s'affiche en 3-5 secondes avec une justification

Exemple de qualification manuelle :

   Société      : Ardian
   URL          : https://ardian.com/news/recrutement-2026
   Description  : Ardian recrute 3 managing directors pour son équipe
                  mid-market France. Signal fort de développement
                  de l'activité deal flow en Île-de-France.
   Signal       : hiring

Résultat attendu : KEEP à 90%+ avec justification détaillée.

---

## Lire les résultats

Trois décisions possibles :

✓ KEEP — Lead pertinent, à contacter en priorité.
  Le score de confiance indique la certitude du système (80-95% = fort).
  La justification explique pourquoi ce lead correspond à vos critères.

✗ STOP — Lead non pertinent, éliminé automatiquement.
  Exemples : job board, annuaire, presse généraliste, hors scope.

? REVIEW — Cas ambigu, nécessite votre jugement.
  Exemples : banque avec desk M&A, family office, fonds adjacent.
  À vous de décider si ça vaut la peine d'approfondir.

---

## Fréquence recommandée

Quotidien (5 minutes) :
  Lancez le pipeline BODACC + RSS le matin.
  Consultez les nouveaux leads KEEP.

Hebdomadaire (15 minutes) :
  Relancez avec Pappers si vous avez des crédits.
  Faites une recherche sémantique sur vos thèmes du moment.
  Qualifiez manuellement les découvertes de la semaine.

---

## Ce que le système ne fait pas

Il ne vous contacte pas à votre place.
Il ne rédige pas les messages d'approche.
Il ne gère pas votre CRM.
Il ne remplace pas votre jugement sur les cas REVIEW.

Ce qu'il fait : trouver les signaux avant la concurrence,
éliminer le bruit, et vous donner une décision argumentée
sur chaque lead en quelques secondes.

---

## En cas de problème

Page blanche au chargement :
  Attendez 30 secondes et rafraîchissez (F5).
  Le serveur se réveille après inactivité.

Pipeline qui ne se termine pas :
  Attendez 2 minutes. Si toujours en cours, rafraîchissez la page
  et relancez.

Erreur sur une qualification :
  Vérifiez que la description fait au moins 2-3 phrases.
  Essayez avec une URL différente.

Pour toute autre question, contactez l'équipe technique.

---

*Maeva Deal Radar Room v2.0 — Roger Flan*
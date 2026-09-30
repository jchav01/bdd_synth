# bdd_synth

Base synthetique shopper / retail analytics pour s'entrainer a l'exploration, au controle qualite et a la lecture shopper.

## Fichiers principaux

- `base_synthetique_shopper_retail_analytics.xlsx` : classeur initial avec donnees et dictionnaire.
- `shopper_retail_observations.csv` : table retail source, ligne magasin x produit x semaine.
- `explorer_base_shopper_retail.py` : exploration standard corrigee de la table retail.
- `exploration_shopper_retail.html` : rapport HTML de l'exploration retail.
- `enrichir_base_shopper_research.py` : script d'enrichissement shopper research synthetique.
- `inventaire_bases_shopper.py` : inventaire standard des tables disponibles.
- `inventaire_bases_shopper.html` : rapport HTML d'inventaire.
- `shopper_segments.csv` : definitions des segments shopper synthetiques.
- `shopper_research_dictionary.csv` : dictionnaire des champs shopper ajoutes.
- `shopper_research_method_note.md` : note de methode et garde-fous d'interpretation.

## V2 shopper in-situ

Une seconde base a ete construite localement pour se rapprocher d'une logique d'etude shopper in-situ en magasin : interviews shoppers, observations rayon, sessions terrain et contexte ventes.

Fichiers legers pousses dans le repo :

- `shopper_insitu_method_note.md`
- `shopper_insitu_questionnaire_dictionary.csv`
- `shopper_insitu_stores.csv`
- `shopper_insitu_products.csv`

Fichiers generes localement dans `outputs/` :

- `generer_base_shopper_insitu_v2.py`
- `inventaire_shopper_insitu_v2.html`
- `shopper_insitu_fieldwork_sessions.csv`
- `shopper_insitu_interviews.csv`
- `shopper_insitu_shelf_observations.csv`
- `shopper_insitu_retail_sales_context.csv`

Les grosses tables d'interviews, d'observations et de contexte ventes n'ont pas ete poussees via le connecteur GitHub de cette session. Elles sont conservees localement et peuvent etre regenerees depuis le script local.

## Regenerer les fichiers enrichis

Depuis le dossier du repo :

```bash
python enrichir_base_shopper_research.py
python inventaire_bases_shopper.py
```

Ces scripts creent notamment :

- `shopper_retail_observations_enriched.csv`
- `shopper_trip_sample.csv`
- `inventaire_bases_shopper.html`

## Logique d'analyse

Le fil directeur est volontairement simple : comprendre les variables, verifier la fiabilite, proposer une analyse, verifier qu'elle tient, l'interpreter dans le contexte shopper, puis la rendre presentable au client.

Les variables shopper enrichies sont des hypotheses synthetiques inferees depuis des signaux retail. Elles servent a travailler des regularites de comportement shopper, pas a prouver directement des motivations individuelles reelles ni a reproduire une methodologie proprietaire Action Plus.

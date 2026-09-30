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

# Shopper research enrichment note

This enrichment keeps the original retail analytics table and adds synthetic shopper-research fields.

It is designed for learning and analysis inspired by public shopper-research practices: category strategy, merchandising, shopper missions, decision drivers, segmentation and store/category behavior.

It is not a proprietary Action Plus model and does not claim to reproduce their internal methodology.

## Files

- `shopper_retail_observations_enriched.csv`: original rows plus inferred shopper variables.
- `shopper_trip_sample.csv`: synthetic exit-interview style trip records.
- `shopper_segments.csv`: segment definitions and directional indexes.
- `shopper_research_dictionary.csv`: definitions for added variables.

## Volumes

- Source observation rows: 14976
- Enriched observation rows: 14976
- Synthetic trip rows: 5000

## Interpretation rule

Use the enriched variables to form shopper hypotheses, not as direct proof of motivations. The strongest workflow is:

1. Understand what the variables mean.
2. Check whether the data is reliable enough.
3. Propose an analysis.
4. Check that the pattern holds.
5. Interpret it in a shopper context.
6. Turn it into a client-ready story.

# Shopper in-situ synthetic base v2

This version remodels the earlier retail analytics dataset into a synthetic in-store shopper research setup.

The core unit is no longer only store x product x week. The dataset now includes fieldwork sessions, shopper interviews and shelf observations. Retail sales remain available as context.

## Intended use

Use this base for standard shopper-research questions:

1. Who is shopping the category?
2. What mission brought them to the store?
3. What was planned versus triggered in-store?
4. What did shoppers notice at shelf?
5. What drove purchase, non-purchase or substitution?
6. Which regular patterns appear by category, store format, mission and segment?

## Important limitation

This is a synthetic training base. It is inspired by common public shopper-research practices and in-situ fieldwork logic. It is not a proprietary Action Plus dataset and does not reproduce their internal protocols, questionnaires, quotas, weighting or coding rules.

## Tables

- `shopper_insitu_stores.csv`: store frame and fieldwork context.
- `shopper_insitu_products.csv`: product frame and category roles.
- `shopper_insitu_fieldwork_sessions.csv`: store-date-daypart survey sessions.
- `shopper_insitu_interviews.csv`: synthetic shopper intercept interviews.
- `shopper_insitu_shelf_observations.csv`: synthetic observed shelf behavior.
- `shopper_insitu_retail_sales_context.csv`: cleaned retail context by store-category-week.
- `shopper_insitu_questionnaire_dictionary.csv`: variable and question dictionary.

## Reading principle

Prefer regularities over isolated anomalies. Treat declared answers and observed behaviors separately, then connect them only when the pattern is stable enough.

from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SOURCE = BASE_DIR / "shopper_retail_observations.csv"
ENRICHED = BASE_DIR / "shopper_retail_observations_enriched.csv"
TRIPS = BASE_DIR / "shopper_trip_sample.csv"
SEGMENTS = BASE_DIR / "shopper_segments.csv"
DICTIONARY = BASE_DIR / "shopper_research_dictionary.csv"
README = BASE_DIR / "shopper_research_method_note.md"

random.seed(20260930)


def to_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def to_bool(value):
    if value == "TRUE":
        return True
    if value == "FALSE":
        return False
    return None


def clamp(value, low, high):
    return max(low, min(high, value))


def round2(value):
    if value is None:
        return ""
    return round(value, 2)


def weighted_choice(weight_map):
    total = sum(max(0, weight) for weight in weight_map.values())
    if total <= 0:
        return next(iter(weight_map))
    r = random.random() * total
    upto = 0
    for key, weight in weight_map.items():
        upto += max(0, weight)
        if upto >= r:
            return key
    return next(reversed(weight_map))


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


SEGMENT_ROWS = [
    {
        "shopper_segment": "Budget optimizers",
        "description": "Cherchent a securiser le prix total du panier, comparent les remises et arbitrent facilement.",
        "typical_missions": "promo_hunt; stock_up",
        "price_sensitivity": 90,
        "promo_affinity": 88,
        "brand_loyalty": 32,
        "planning_level": 72,
    },
    {
        "shopper_segment": "Family stock-up",
        "description": "Achats planifies, formats familiaux, categories de routine et paniers volumineux.",
        "typical_missions": "stock_up; planned_replenishment",
        "price_sensitivity": 67,
        "promo_affinity": 62,
        "brand_loyalty": 54,
        "planning_level": 86,
    },
    {
        "shopper_segment": "Convenience routine",
        "description": "Visites frequentes, besoin rapide, faible tolerance a la rupture et decision pragmatique.",
        "typical_missions": "top_up; meal_solution",
        "price_sensitivity": 46,
        "promo_affinity": 38,
        "brand_loyalty": 58,
        "planning_level": 52,
    },
    {
        "shopper_segment": "Promo explorers",
        "description": "Entrent volontiers dans la categorie via prospectus, display ou mecanique promotionnelle.",
        "typical_missions": "promo_hunt; treat_impulse",
        "price_sensitivity": 74,
        "promo_affinity": 94,
        "brand_loyalty": 36,
        "planning_level": 45,
    },
    {
        "shopper_segment": "Brand reassurance",
        "description": "Preferent la securite de choix, les routines et les marques percues comme fiables.",
        "typical_missions": "planned_replenishment; top_up",
        "price_sensitivity": 39,
        "promo_affinity": 34,
        "brand_loyalty": 84,
        "planning_level": 71,
    },
    {
        "shopper_segment": "Impulse and inspiration",
        "description": "Plus sensibles a l'exposition, au contexte de consommation et aux achats non prevus.",
        "typical_missions": "treat_impulse; meal_solution",
        "price_sensitivity": 52,
        "promo_affinity": 57,
        "brand_loyalty": 42,
        "planning_level": 31,
    },
]


def category_role(category):
    return {
        "Boissons soft": "Traffic and impulse",
        "Epicerie salee": "Impulse and occasion",
        "Petit dejeuner": "Routine basket builder",
        "Hygiene": "Routine and reassurance",
        "Entretien": "Stock-up and value",
        "Frais libre-service": "Meal solution",
    }.get(category, "Routine basket builder")


def mission_weights(row):
    category = row["category"]
    store_format = row["store_format"]
    promo = to_bool(row["promotion_flag"]) is True
    display = to_bool(row["display_flag"]) is True
    endcap = to_bool(row["endcap_flag"]) is True
    discount = to_float(row["discount_pct"]) or 0

    weights = {
        "stock_up": 12,
        "top_up": 16,
        "planned_replenishment": 20,
        "meal_solution": 12,
        "treat_impulse": 8,
        "promo_hunt": 6,
    }
    if store_format == "Hyper":
        weights["stock_up"] += 24
        weights["planned_replenishment"] += 8
    if store_format in {"Super", "Proximite"}:
        weights["top_up"] += 14
        weights["meal_solution"] += 8
    if category in {"Entretien", "Petit dejeuner", "Hygiene"}:
        weights["planned_replenishment"] += 16
    if category == "Entretien":
        weights["stock_up"] += 16
    if category == "Frais libre-service":
        weights["meal_solution"] += 24
        weights["top_up"] += 8
    if category in {"Boissons soft", "Epicerie salee"}:
        weights["treat_impulse"] += 17
    if promo:
        weights["promo_hunt"] += 20 + discount * 120
    if display or endcap:
        weights["treat_impulse"] += 16
        weights["promo_hunt"] += 7
    return weights


def segment_weights(row, mission):
    promo = to_bool(row["promotion_flag"]) is True
    discount = to_float(row["discount_pct"]) or 0
    store_format = row["store_format"]
    category = row["category"]
    display = to_bool(row["display_flag"]) is True
    stockout = to_bool(row["stockout_flag"]) is True

    weights = {
        "Budget optimizers": 12,
        "Family stock-up": 15,
        "Convenience routine": 16,
        "Promo explorers": 10,
        "Brand reassurance": 14,
        "Impulse and inspiration": 10,
    }
    if promo or discount > 0.12 or mission == "promo_hunt":
        weights["Budget optimizers"] += 18
        weights["Promo explorers"] += 24
    if store_format == "Hyper" or mission == "stock_up":
        weights["Family stock-up"] += 24
    if store_format in {"Super", "Proximite"} or mission in {"top_up", "meal_solution"}:
        weights["Convenience routine"] += 19
    if category in {"Hygiene", "Petit dejeuner"} and not promo:
        weights["Brand reassurance"] += 18
    if category in {"Boissons soft", "Epicerie salee"} or display:
        weights["Impulse and inspiration"] += 18
    if stockout:
        weights["Brand reassurance"] -= 4
        weights["Convenience routine"] += 4
    return weights


def planning_type(mission, promo, display):
    if mission in {"stock_up", "planned_replenishment"}:
        return "Planned"
    if mission == "promo_hunt":
        return "Planned deal-seeking"
    if mission in {"meal_solution", "top_up"}:
        return "Semi-planned"
    if mission == "treat_impulse" or display:
        return "Unplanned or triggered in-store"
    return "Semi-planned"


def decision_driver(row, mission):
    promo = to_bool(row["promotion_flag"]) is True
    display = to_bool(row["display_flag"]) is True
    stockout = to_bool(row["stockout_flag"]) is True
    discount = to_float(row["discount_pct"]) or 0
    category = row["category"]
    if stockout:
        return "Availability"
    if promo and discount >= 0.15:
        return "Price and promotion"
    if display or mission == "treat_impulse":
        return "Visibility and inspiration"
    if category in {"Hygiene", "Petit dejeuner"}:
        return "Routine and trust"
    if mission in {"top_up", "meal_solution"}:
        return "Convenience"
    return "Category need"


def enrich_row(row, cat_avg_price):
    mission = weighted_choice(mission_weights(row))
    segment = weighted_choice(segment_weights(row, mission))
    promo = to_bool(row["promotion_flag"]) is True
    display = to_bool(row["display_flag"]) is True
    endcap = to_bool(row["endcap_flag"]) is True
    stockout = to_bool(row["stockout_flag"]) is True
    discount = to_float(row["discount_pct"]) or 0
    shelf_price = to_float(row["shelf_price_eur"])
    category = row["category"]
    avg_price = cat_avg_price.get(category)
    price_position = shelf_price / avg_price if shelf_price is not None and avg_price else None

    price_sensitivity = 42 + discount * 130 + (18 if mission == "promo_hunt" else 0) + (12 if segment == "Budget optimizers" else 0)
    promo_affinity = 35 + (32 if promo else 0) + discount * 100 + (18 if segment == "Promo explorers" else 0)
    brand_loyalty = 62 - discount * 70 + (22 if segment == "Brand reassurance" else 0) - (10 if promo else 0)
    impulse = 20 + (24 if display else 0) + (18 if endcap else 0) + (24 if mission == "treat_impulse" else 0)
    convenience = 35 + (24 if mission in {"top_up", "meal_solution"} else 0) + (12 if row["store_format"] in {"Super", "Proximite"} else 0)

    if price_position is None:
        value_band = "Unknown"
    elif discount >= 0.18:
        value_band = "Strong deal"
    elif price_position <= 0.92:
        value_band = "Low price"
    elif price_position >= 1.10:
        value_band = "Premium price"
    else:
        value_band = "Fair price"

    if stockout:
        substitution = weighted_choice({
            "Switch brand": 35,
            "Switch size or format": 24,
            "Postpone purchase": 26,
            "Leave category": 15,
        })
    else:
        substitution = "No stockout observed"

    driver = decision_driver(row, mission)
    enriched = dict(row)
    enriched.update({
        "shopper_mission_primary": mission,
        "shopper_segment_primary": segment,
        "shopper_need_state": {
            "stock_up": "Family or pantry refill",
            "top_up": "Immediate replenishment",
            "planned_replenishment": "Routine category need",
            "meal_solution": "Convenient meal or occasion",
            "treat_impulse": "Impulse or pleasure",
            "promo_hunt": "Deal seeking",
        }[mission],
        "purchase_planning_type": planning_type(mission, promo, display),
        "category_role_in_trip": category_role(category),
        "primary_decision_driver": driver,
        "decision_tree_entry": {
            "Price and promotion": "Price",
            "Availability": "Availability",
            "Visibility and inspiration": "Occasion",
            "Routine and trust": "Brand or habit",
            "Convenience": "Mission",
            "Category need": "Category",
        }[driver],
        "perceived_value_band": value_band,
        "price_position_vs_category": "" if price_position is None else round(price_position, 3),
        "shopper_price_sensitivity_index": round2(clamp(price_sensitivity, 0, 100)),
        "promo_affinity_index": round2(clamp(promo_affinity, 0, 100)),
        "brand_loyalty_proxy_index": round2(clamp(brand_loyalty, 0, 100)),
        "impulse_trigger_index": round2(clamp(impulse, 0, 100)),
        "convenience_need_index": round2(clamp(convenience, 0, 100)),
        "substitution_behavior_if_oos": substitution,
        "shopper_interpretation_scope": "Observed retail signal, shopper motivation inferred",
    })
    return enriched


def build_enriched_observations(rows):
    prices_by_category = defaultdict(list)
    for row in rows:
        price = to_float(row["shelf_price_eur"])
        if price is not None and price > 0.05 and not row.get("anomaly_type"):
            prices_by_category[row["category"]].append(price)
    cat_avg_price = {
        category: sum(values) / len(values)
        for category, values in prices_by_category.items()
        if values
    }
    return [enrich_row(row, cat_avg_price) for row in rows]


def build_trip_sample(enriched, n=5000):
    stores = sorted({row["store_id"] for row in enriched})
    weeks = sorted({row["week_number"] for row in enriched}, key=lambda x: int(x))
    categories = sorted({row["category"] for row in enriched})
    rows_by_store_week = defaultdict(list)
    for row in enriched:
        rows_by_store_week[(row["store_id"], row["week_number"])].append(row)

    trips = []
    for i in range(1, n + 1):
        store = random.choice(stores)
        week = random.choice(weeks)
        candidates = rows_by_store_week[(store, week)]
        if not candidates:
            candidates = enriched
        base = random.choice(candidates)
        segment = base["shopper_segment_primary"]
        mission = weighted_choice(mission_weights(base))
        main_category = base["category"]
        basket_categories = {main_category}
        category_count = {
            "stock_up": random.randint(5, 10),
            "planned_replenishment": random.randint(3, 7),
            "top_up": random.randint(1, 4),
            "meal_solution": random.randint(2, 5),
            "treat_impulse": random.randint(1, 3),
            "promo_hunt": random.randint(2, 6),
        }[mission]
        for _ in range(max(0, category_count - 1)):
            basket_categories.add(random.choice(categories))
        promo_influenced = mission == "promo_hunt" or random.random() < (0.34 if segment in {"Promo explorers", "Budget optimizers"} else 0.16)
        impulse_added = mission == "treat_impulse" or random.random() < (0.28 if base["display_flag"] == "TRUE" else 0.10)
        substitution = random.random() < (0.19 if base["stockout_flag"] == "TRUE" else 0.04)
        list_used = mission in {"stock_up", "planned_replenishment", "promo_hunt"} and random.random() < 0.68
        time_pressure = weighted_choice({
            "Low": 25 if mission == "stock_up" else 12,
            "Medium": 45,
            "High": 18 if mission == "stock_up" else 36,
        })
        spend = max(4, random.gauss({
            "stock_up": 86,
            "planned_replenishment": 54,
            "top_up": 22,
            "meal_solution": 31,
            "treat_impulse": 15,
            "promo_hunt": 48,
        }[mission], 14))
        satisfaction = 7.4 + (0.5 if not substitution else -1.1) + (0.4 if promo_influenced else 0) + random.gauss(0, 0.7)
        trips.append({
            "trip_id": f"TRIP{i:05d}",
            "week_number": week,
            "store_id": store,
            "shopper_segment": segment,
            "shopping_mission": mission,
            "main_category": main_category,
            "basket_category_count": len(basket_categories),
            "basket_categories": "; ".join(sorted(basket_categories)),
            "estimated_basket_value_eur": round(spend, 2),
            "list_used_flag": list_used,
            "promo_influenced_flag": promo_influenced,
            "impulse_item_added_flag": impulse_added,
            "substitution_made_flag": substitution,
            "time_pressure": time_pressure,
            "satisfaction_score_1_10": round(clamp(satisfaction, 1, 10), 1),
            "research_source_type": "Synthetic exit-interview style record",
        })
    return trips


def dictionary_rows(enriched_fields):
    definitions = {
        "shopper_mission_primary": "Mission d'achat dominante inferee pour la ligne retail.",
        "shopper_segment_primary": "Segment shopper dominant infere pour la ligne.",
        "shopper_need_state": "Besoin ou contexte shopper associe a la mission.",
        "purchase_planning_type": "Degre de planification suppose de l'achat.",
        "category_role_in_trip": "Role de la categorie dans le panier ou la visite.",
        "primary_decision_driver": "Driver principal suppose: prix, disponibilite, routine, visibilite, praticite.",
        "decision_tree_entry": "Niveau d'entree synthetique dans l'arbre de decision shopper.",
        "perceived_value_band": "Lecture synthetique du prix percu relativement a la categorie et a la remise.",
        "price_position_vs_category": "Prix rayon relatif au prix moyen observe de la categorie.",
        "shopper_price_sensitivity_index": "Indice 0-100 de sensibilite au prix inferee.",
        "promo_affinity_index": "Indice 0-100 d'affinite promotionnelle inferee.",
        "brand_loyalty_proxy_index": "Indice proxy 0-100 de fidelite ou routine de choix.",
        "impulse_trigger_index": "Indice 0-100 de probabilite d'achat declenche par exposition ou occasion.",
        "convenience_need_index": "Indice 0-100 de besoin de praticite.",
        "substitution_behavior_if_oos": "Comportement probable si rupture observee.",
        "shopper_interpretation_scope": "Rappel que la motivation est inferee depuis un signal retail.",
    }
    rows = []
    for field in enriched_fields:
        if field in definitions:
            rows.append({
                "table": "shopper_retail_observations_enriched",
                "field": field,
                "type": "synthetic derived",
                "definition": definitions[field],
                "analysis_use": "Shopper behavior hypotheses and descriptive segmentation",
            })
    trip_defs = {
        "trip_id": "Identifiant synthetique de visite shopper.",
        "shopping_mission": "Mission d'achat principale de la visite.",
        "shopper_segment": "Segment shopper du repondant synthetique.",
        "basket_categories": "Categories presentes dans le panier declare ou observe.",
        "list_used_flag": "Le shopper a utilise une liste ou un plan d'achat.",
        "promo_influenced_flag": "La visite ou l'achat a ete influence par une promo.",
        "impulse_item_added_flag": "Au moins un produit a ete ajoute non prevu.",
        "substitution_made_flag": "Substitution realisee, souvent liee a une rupture ou indisponibilite.",
        "satisfaction_score_1_10": "Satisfaction synthetique de sortie de visite.",
    }
    for field, definition in trip_defs.items():
        rows.append({
            "table": "shopper_trip_sample",
            "field": field,
            "type": "synthetic survey-like",
            "definition": definition,
            "analysis_use": "Mission analysis, segmentation, basket behavior",
        })
    return rows


def write_readme(source_count, enriched_count, trip_count):
    README.write_text(
        f"""# Shopper research enrichment note

This enrichment keeps the original retail analytics table and adds synthetic shopper-research fields.

It is designed for learning and analysis inspired by public shopper-research practices: category strategy, merchandising, shopper missions, decision drivers, segmentation and store/category behavior.

It is not a proprietary Action Plus model and does not claim to reproduce their internal methodology.

## Files

- `shopper_retail_observations_enriched.csv`: original rows plus inferred shopper variables.
- `shopper_trip_sample.csv`: synthetic exit-interview style trip records.
- `shopper_segments.csv`: segment definitions and directional indexes.
- `shopper_research_dictionary.csv`: definitions for added variables.

## Volumes

- Source observation rows: {source_count}
- Enriched observation rows: {enriched_count}
- Synthetic trip rows: {trip_count}

## Interpretation rule

Use the enriched variables to form shopper hypotheses, not as direct proof of motivations. The strongest workflow is:

1. Understand what the variables mean.
2. Check whether the data is reliable enough.
3. Propose an analysis.
4. Check that the pattern holds.
5. Interpret it in a shopper context.
6. Turn it into a client-ready story.
""",
        encoding="utf-8",
    )


def main():
    rows = read_csv(SOURCE)
    enriched = build_enriched_observations(rows)
    trips = build_trip_sample(enriched)
    enriched_fields = list(enriched[0].keys())
    write_csv(ENRICHED, enriched, enriched_fields)
    write_csv(TRIPS, trips, list(trips[0].keys()))
    write_csv(SEGMENTS, SEGMENT_ROWS, list(SEGMENT_ROWS[0].keys()))
    write_csv(DICTIONARY, dictionary_rows(enriched_fields), ["table", "field", "type", "definition", "analysis_use"])
    write_readme(len(rows), len(enriched), len(trips))

    segment_counts = Counter(row["shopper_segment_primary"] for row in enriched)
    mission_counts = Counter(row["shopper_mission_primary"] for row in enriched)
    print(f"Wrote {ENRICHED.name}: {len(enriched)} rows")
    print(f"Wrote {TRIPS.name}: {len(trips)} rows")
    print("Top segments:", dict(segment_counts.most_common(4)))
    print("Top missions:", dict(mission_counts.most_common(4)))


if __name__ == "__main__":
    main()

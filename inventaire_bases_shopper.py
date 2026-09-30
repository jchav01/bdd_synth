from __future__ import annotations

import csv
import html
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / "inventaire_bases_shopper.html"

TABLES = [
    ("Retail observations", BASE_DIR / "shopper_retail_observations.csv"),
    ("Retail observations enriched", BASE_DIR / "shopper_retail_observations_enriched.csv"),
    ("Shopper trip sample", BASE_DIR / "shopper_trip_sample.csv"),
    ("Shopper segments", BASE_DIR / "shopper_segments.csv"),
    ("Shopper research dictionary", BASE_DIR / "shopper_research_dictionary.csv"),
]


def esc(value):
    return html.escape(str(value))


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader), reader.fieldnames or []


def to_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def to_bool(value):
    if value in {"TRUE", "True", "true", True}:
        return True
    if value in {"FALSE", "False", "false", False}:
        return False
    return None


def fmt_number(value, digits=0):
    if value is None:
        return "n/a"
    if digits == 0:
        return f"{value:,.0f}".replace(",", " ")
    return f"{value:,.{digits}f}".replace(",", " ")


def fmt_pct(value, digits=1):
    if value is None:
        return "n/a"
    return f"{100 * value:.{digits}f}%"


def simple_table(headers, rows):
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def hbar(items, unit="", width=900, left=230, bar_h=23):
    items = [(str(k), float(v or 0)) for k, v in items]
    if not items:
        return "<p class='muted'>No data.</p>"
    max_v = max(v for _, v in items) or 1
    right = 140
    top = 24
    gap = 8
    chart_w = width - left - right
    height = top + len(items) * (bar_h + gap) + 12
    out = [f"<svg viewBox='0 0 {width} {height}' class='chart' role='img'>"]
    for i, (label, value) in enumerate(items):
        y = top + i * (bar_h + gap)
        w = max(2, value / max_v * chart_w)
        out.append(f"<text x='0' y='{y+16}' class='axis-label'>{esc(label)}</text>")
        out.append(f"<rect x='{left}' y='{y}' width='{w:.1f}' height='{bar_h}' rx='3' class='bar'></rect>")
        out.append(f"<text x='{left+w+8:.1f}' y='{y+16}' class='value'>{esc(fmt_number(value))} {esc(unit)}</text>")
    out.append("</svg>")
    return "\n".join(out)


def missing_summary(rows, columns, exclude_expected_blanks=None, top_n=12):
    exclude_expected_blanks = exclude_expected_blanks or set()
    counts = []
    n = len(rows)
    for col in columns:
        if col in exclude_expected_blanks:
            continue
        missing = sum(1 for row in rows if row.get(col, "") == "")
        if missing:
            counts.append((col, missing, missing / n if n else 0))
    counts.sort(key=lambda item: item[1], reverse=True)
    return counts[:top_n]


def count_col(rows, col, top_n=10):
    c = Counter(row.get(col, "") or "Missing" for row in rows)
    return c.most_common(top_n)


def section(title, body, note=None, wide=False):
    cls = "panel wide" if wide else "panel"
    note_html = f"<p class='note'>{esc(note)}</p>" if note else ""
    return f"<section class='{cls}'><h2>{esc(title)}</h2>{note_html}{body}</section>"


def overview_table(table_infos):
    rows = []
    for name, path, rows_data, columns in table_infos:
        rows.append([
            esc(name),
            esc(path.name),
            fmt_number(len(rows_data)),
            fmt_number(len(columns)),
            esc(", ".join(columns[:6]) + ("..." if len(columns) > 6 else "")),
        ])
    return simple_table(["Table", "File", "Rows", "Columns", "First columns"], rows)


def retail_metrics(rows):
    n = len(rows)
    clean_rows = [r for r in rows if not r.get("anomaly_type") and (to_float(r.get("units_sold")) or 0) >= 0]
    date_values = [r["week_start_date"] for r in rows if r.get("week_start_date")]
    metrics = [
        ["Source rows", fmt_number(n)],
        ["Clean business rows", f"{fmt_number(len(clean_rows))} ({fmt_pct(len(clean_rows)/n)})"],
        ["Date range", f"{min(date_values)} to {max(date_values)}" if date_values else "n/a"],
        ["Stores", fmt_number(len({r['store_id'] for r in rows if r.get('store_id')}))],
        ["Products", fmt_number(len({r['product_id'] for r in rows if r.get('product_id')}))],
        ["Categories", fmt_number(len({r['category'] for r in rows if r.get('category')}))],
        ["Promo rows", fmt_pct(sum(to_bool(r["promotion_flag"]) is True for r in clean_rows) / len(clean_rows))],
        ["Stockout rows", fmt_pct(sum(to_bool(r["stockout_flag"]) is True for r in clean_rows) / len(clean_rows))],
        ["Net sales clean", f"{fmt_number(sum(to_float(r['net_sales_eur']) or 0 for r in clean_rows))} EUR"],
        ["Units clean", fmt_number(sum(to_float(r["units_sold"]) or 0 for r in clean_rows))],
    ]
    return simple_table(["Metric", "Value"], metrics)


def trip_metrics(rows):
    n = len(rows)
    metrics = [
        ["Trips", fmt_number(n)],
        ["Segments", fmt_number(len({r['shopper_segment'] for r in rows if r.get('shopper_segment')}))],
        ["Missions", fmt_number(len({r['shopping_mission'] for r in rows if r.get('shopping_mission')}))],
        ["Avg basket value", f"{fmt_number(sum(to_float(r['estimated_basket_value_eur']) or 0 for r in rows) / n, 2)} EUR"],
        ["List used", fmt_pct(sum(to_bool(r["list_used_flag"]) is True for r in rows) / n)],
        ["Promo influenced", fmt_pct(sum(to_bool(r["promo_influenced_flag"]) is True for r in rows) / n)],
        ["Impulse item added", fmt_pct(sum(to_bool(r["impulse_item_added_flag"]) is True for r in rows) / n)],
        ["Substitution made", fmt_pct(sum(to_bool(r["substitution_made_flag"]) is True for r in rows) / n)],
    ]
    return simple_table(["Metric", "Value"], metrics)


def build_report():
    table_infos = []
    for name, path in TABLES:
        rows, columns = read_csv(path)
        table_infos.append((name, path, rows, columns))

    by_name = {name: (rows, columns) for name, _, rows, columns in table_infos}
    retail_rows, retail_cols = by_name["Retail observations"]
    enriched_rows, enriched_cols = by_name["Retail observations enriched"]
    trip_rows, trip_cols = by_name["Shopper trip sample"]
    segment_rows, segment_cols = by_name["Shopper segments"]

    added_cols = [c for c in enriched_cols if c not in retail_cols]
    sections = []
    sections.append(section("Tables available", overview_table(table_infos), wide=True))
    sections.append(section("Original retail table inventory", retail_metrics(retail_rows)))
    sections.append(section(
        "Enriched shopper fields",
        simple_table(["Added field"], [[esc(c)] for c in added_cols]),
        "These fields are inferred synthetic shopper variables, not direct observations of motivation.",
    ))
    sections.append(section(
        "First shopper missions",
        hbar(count_col(enriched_rows, "shopper_mission_primary", 8), "rows"),
    ))
    sections.append(section(
        "First shopper segments",
        hbar(count_col(enriched_rows, "shopper_segment_primary", 8), "rows"),
    ))
    sections.append(section(
        "Decision drivers",
        hbar(count_col(enriched_rows, "primary_decision_driver", 8), "rows"),
    ))
    sections.append(section(
        "Planning types",
        hbar(count_col(enriched_rows, "purchase_planning_type", 8), "rows"),
    ))
    sections.append(section(
        "Trip sample inventory",
        trip_metrics(trip_rows),
        "This table behaves like a synthetic exit-interview layer and is better suited for mission and basket questions.",
    ))
    sections.append(section(
        "Trip missions",
        hbar(count_col(trip_rows, "shopping_mission", 8), "trips"),
    ))
    sections.append(section(
        "Trip segments",
        hbar(count_col(trip_rows, "shopper_segment", 8), "trips"),
    ))

    expected_blank = {"campaign_id", "anomaly_type", "missingness_pattern"}
    missing_rows = [
        [esc(col), fmt_number(count), fmt_pct(rate)]
        for col, count, rate in missing_summary(enriched_rows, enriched_cols, expected_blank)
    ]
    sections.append(section(
        "Main missing data fields",
        simple_table(["Field", "Missing rows", "Share"], missing_rows),
        "Expected optional blanks such as campaign_id, anomaly_type and missingness_pattern are excluded here.",
        wide=True,
    ))

    segment_preview = [
        [
            esc(row["shopper_segment"]),
            esc(row["description"]),
            esc(row["typical_missions"]),
            esc(row["price_sensitivity"]),
            esc(row["promo_affinity"]),
            esc(row["brand_loyalty"]),
        ]
        for row in segment_rows
    ]
    sections.append(section(
        "Segment definitions",
        simple_table(["Segment", "Description", "Typical missions", "Price", "Promo", "Brand loyalty"], segment_preview),
        wide=True,
    ))

    questions = [
        ["Who buys?", "Compare shopper segments by category, mission and store format."],
        ["What is bought?", "Read category roles, value bands, decision drivers and basket categories."],
        ["Where?", "Compare store formats and regions after checking traffic and missingness."],
        ["When?", "Use monthly and weekly patterns before attributing them to shopper behavior."],
        ["Promo", "Check whether promo_hunt and price sensitivity concentrate in specific categories or stores."],
        ["Rupture", "Use substitution fields only as hypotheses; confirm with stockout and sales patterns."],
        ["Client story", "Separate observed retail signal, inferred shopper behavior and recommended action."],
    ]
    sections.append(section(
        "First analysis questions",
        simple_table(["Angle", "First question"], [[esc(a), esc(b)] for a, b in questions]),
        wide=True,
    ))

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Inventaire des bases shopper</title>
  <style>
    :root {{ --ink:#202832; --muted:#5d6878; --bg:#f5f7fa; --panel:#fff; --line:#d8e0e8; --bar:#236a73; }}
    body {{ margin:0; font-family:Arial, Helvetica, sans-serif; background:var(--bg); color:var(--ink); }}
    header {{ padding:28px 34px 10px; }}
    h1 {{ margin:0 0 8px; font-size:26px; }}
    h2 {{ margin:0 0 12px; font-size:17px; }}
    .subtitle,.note,.muted {{ color:var(--muted); font-size:13px; line-height:1.45; }}
    main {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(440px,1fr)); gap:18px; padding:18px 34px 34px; }}
    .panel {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:18px; overflow-x:auto; box-shadow:0 1px 2px rgba(15,25,35,.06); }}
    .wide {{ grid-column:1/-1; }}
    table {{ border-collapse:collapse; width:100%; font-size:13px; }}
    th,td {{ padding:8px 9px; border-bottom:1px solid #e5ebf1; text-align:left; vertical-align:top; }}
    th {{ background:#eef3f7; white-space:nowrap; }}
    td {{ max-width:640px; }}
    .chart {{ width:100%; height:auto; display:block; }}
    .bar {{ fill:var(--bar); }}
    .axis-label,.value {{ fill:var(--muted); font-size:12px; }}
    .value {{ font-weight:700; }}
  </style>
</head>
<body>
  <header>
    <h1>Inventaire des bases shopper</h1>
    <p class="subtitle">Exploration standarde initiale: contenu, colonnes, volumes, champs shopper ajoutes et premiers controles.</p>
  </header>
  <main>{''.join(sections)}</main>
</body>
</html>
"""


def main():
    HTML_PATH.write_text(build_report(), encoding="utf-8")
    print(f"Wrote {HTML_PATH}")


if __name__ == "__main__":
    main()

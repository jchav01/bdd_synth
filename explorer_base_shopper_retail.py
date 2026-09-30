from __future__ import annotations

import csv
import html
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


# Usage:
#   python explorer_base_shopper_retail.py
#
# The script expects shopper_retail_observations.csv in the same folder.
# It creates exploration_shopper_retail.html in the same folder.

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "shopper_retail_observations.csv"
HTML_PATH = BASE_DIR / "exploration_shopper_retail.html"


def to_float(value: str):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def to_int(value: str):
    number = to_float(value)
    return int(number) if number is not None else None


def to_bool(value: str):
    if value == "TRUE":
        return True
    if value == "FALSE":
        return False
    return None


def fmt_number(value, digits=0):
    if value is None:
        return "n/a"
    if isinstance(value, float) and math.isnan(value):
        return "n/a"
    if digits == 0:
        return f"{value:,.0f}".replace(",", " ")
    return f"{value:,.{digits}f}".replace(",", " ")


def fmt_pct(value, digits=1):
    if value is None:
        return "n/a"
    return f"{value * 100:.{digits}f}%"


def esc(value):
    return html.escape(str(value))


def read_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader), reader.fieldnames or []


def add_metric(metrics, label, value):
    metrics.append((label, value))


def aggregate_sum(rows, group_col, value_col):
    result = defaultdict(float)
    for row in rows:
        value = to_float(row.get(value_col, ""))
        if value is not None:
            result[row[group_col] or "Missing"] += value
    return dict(result)


def aggregate_count(rows, group_col):
    result = Counter()
    for row in rows:
        result[row[group_col] or "Missing"] += 1
    return dict(result)


def aggregate_avg(rows, group_col, value_col):
    sums = defaultdict(float)
    counts = defaultdict(int)
    for row in rows:
        value = to_float(row.get(value_col, ""))
        if value is not None:
            key = row[group_col] or "Missing"
            sums[key] += value
            counts[key] += 1
    return {key: sums[key] / counts[key] for key in sums}


def sort_items(mapping, limit=None, reverse=True):
    items = sorted(mapping.items(), key=lambda item: item[1], reverse=reverse)
    return items[:limit] if limit else items


def chart_shell(title, svg):
    return f"""
    <section class="card">
      <h2>{esc(title)}</h2>
      {svg}
    </section>
    """


def horizontal_bar_chart(items, value_label="", width=920, bar_height=26, left=210):
    items = [(str(label), float(value or 0)) for label, value in items]
    if not items:
        return "<p>No data.</p>"
    max_value = max(abs(value) for _, value in items) or 1
    right = 120
    top = 34
    gap = 10
    height = top + len(items) * (bar_height + gap) + 14
    chart_width = width - left - right
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    for i, (label, value) in enumerate(items):
        y = top + i * (bar_height + gap)
        w = max(2, abs(value) / max_value * chart_width)
        parts.append(f'<text x="0" y="{y + 18}" class="axis-label">{esc(label)}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="{bar_height}" rx="3" class="bar"></rect>')
        parts.append(
            f'<text x="{left + w + 8:.1f}" y="{y + 18}" class="value-label">{esc(fmt_number(value, 1 if abs(value) < 100 else 0))} {esc(value_label)}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def vertical_bar_chart(items, value_label="", width=920, height=340):
    items = [(str(label), float(value or 0)) for label, value in items]
    if not items:
        return "<p>No data.</p>"
    left = 58
    right = 18
    top = 28
    bottom = 64
    max_value = max(value for _, value in items) or 1
    chart_w = width - left - right
    chart_h = height - top - bottom
    bar_w = chart_w / max(len(items), 1) * 0.68
    step = chart_w / max(len(items), 1)
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    parts.append(f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" class="axis"></line>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" class="axis"></line>')
    for i, (label, value) in enumerate(items):
        x = left + i * step + (step - bar_w) / 2
        bar_h = value / max_value * chart_h
        y = height - bottom - bar_h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="3" class="bar"></rect>')
        parts.append(f'<text x="{x + bar_w/2:.1f}" y="{height-bottom+22}" class="tick" text-anchor="middle">{esc(label)}</text>')
    parts.append(f'<text x="{left}" y="18" class="value-label">Max: {esc(fmt_number(max_value, 0))} {esc(value_label)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def line_chart(items, value_label="", width=920, height=340):
    items = [(str(label), float(value or 0)) for label, value in items]
    if len(items) < 2:
        return "<p>No data.</p>"
    left = 58
    right = 22
    top = 28
    bottom = 64
    values = [value for _, value in items]
    min_v = min(0, min(values))
    max_v = max(values) or 1
    spread = max_v - min_v or 1
    chart_w = width - left - right
    chart_h = height - top - bottom

    def xy(i, value):
        x = left + (i / (len(items) - 1)) * chart_w
        y = top + (max_v - value) / spread * chart_h
        return x, y

    points = [xy(i, value) for i, (_, value) in enumerate(items)]
    point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    parts.append(f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" class="axis"></line>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" class="axis"></line>')
    parts.append(f'<polyline points="{point_text}" fill="none" class="line"></polyline>')
    for x, y in points:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" class="dot"></circle>')
    for i, (label, _) in enumerate(items):
        if i % max(1, len(items) // 10) == 0 or i == len(items) - 1:
            x, _ = xy(i, values[i])
            parts.append(f'<text x="{x:.1f}" y="{height-bottom+22}" class="tick" text-anchor="middle">{esc(label)}</text>')
    parts.append(f'<text x="{left}" y="18" class="value-label">Max: {esc(fmt_number(max_v, 0))} {esc(value_label)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def histogram(values, bins=12, width=920, height=340):
    values = [value for value in values if value is not None]
    if not values:
        return "<p>No data.</p>"
    min_v = min(values)
    max_v = max(values)
    if min_v == max_v:
        return f"<p>All values equal {esc(min_v)}.</p>"
    step = (max_v - min_v) / bins
    counts = [0] * bins
    for value in values:
        index = min(bins - 1, int((value - min_v) / step))
        counts[index] += 1
    labels = [f"{min_v + i * step:.0f}" for i in range(bins)]
    return vertical_bar_chart(list(zip(labels, counts)), value_label="rows", width=width, height=height)


def simple_table(headers, rows):
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    body = "\n".join(
        "<tr>" + "".join(f"<td>{esc(value)}</td>" for value in row) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def build_report(rows, columns):
    n_rows = len(rows)
    date_values = [row["week_start_date"] for row in rows if row.get("week_start_date")]
    date_min = min(date_values) if date_values else "n/a"
    date_max = max(date_values) if date_values else "n/a"

    stores = {row["store_id"] for row in rows if row.get("store_id")}
    products = {row["product_id"] for row in rows if row.get("product_id")}
    categories = {row["category"] for row in rows if row.get("category")}

    units = [to_float(row["units_sold"]) for row in rows]
    sales = [to_float(row["net_sales_eur"]) for row in rows]
    units_clean = [value for value in units if value is not None]
    sales_clean = [value for value in sales if value is not None]

    missing_counts = Counter()
    for row in rows:
        for col in columns:
            if row.get(col, "") == "":
                missing_counts[col] += 1

    metrics = []
    add_metric(metrics, "Rows", fmt_number(n_rows))
    add_metric(metrics, "Columns", fmt_number(len(columns)))
    add_metric(metrics, "Date range", f"{date_min} to {date_max}")
    add_metric(metrics, "Stores", fmt_number(len(stores)))
    add_metric(metrics, "Products", fmt_number(len(products)))
    add_metric(metrics, "Categories", fmt_number(len(categories)))
    add_metric(metrics, "Total units", fmt_number(sum(units_clean)))
    add_metric(metrics, "Total net sales EUR", fmt_number(sum(sales_clean), 2))
    add_metric(metrics, "Average units per row", fmt_number(sum(units_clean) / len(units_clean), 2))
    add_metric(metrics, "Rows with promotion", fmt_pct(sum(to_bool(row["promotion_flag"]) is True for row in rows) / n_rows))
    add_metric(metrics, "Rows with stockout", fmt_pct(sum(to_bool(row["stockout_flag"]) is True for row in rows) / n_rows))

    sales_by_month = aggregate_sum(rows, "period_month", "net_sales_eur")
    units_by_category = aggregate_sum(rows, "category", "units_sold")
    sales_by_category = aggregate_sum(rows, "category", "net_sales_eur")
    sales_by_store = aggregate_sum(rows, "store_id", "net_sales_eur")
    units_by_product = aggregate_sum(rows, "product_id", "units_sold")
    sales_by_region = aggregate_sum(rows, "region", "net_sales_eur")
    quality_counts = aggregate_count(rows, "data_quality_flag")
    anomaly_counts = aggregate_count([row for row in rows if row.get("anomaly_type")], "anomaly_type")

    promo_rows = [row for row in rows if to_bool(row["promotion_flag"]) is True]
    non_promo_rows = [row for row in rows if to_bool(row["promotion_flag"]) is False]
    promo_avg_units = sum(to_float(row["units_sold"]) or 0 for row in promo_rows) / max(len(promo_rows), 1)
    non_promo_avg_units = sum(to_float(row["units_sold"]) or 0 for row in non_promo_rows) / max(len(non_promo_rows), 1)

    discount_bins = {
        "No promo": [],
        "0-10%": [],
        "10-20%": [],
        "20%+": [],
    }
    for row in rows:
        discount = to_float(row["discount_pct"])
        unit = to_float(row["units_sold"])
        if discount is None or unit is None:
            continue
        if discount == 0:
            discount_bins["No promo"].append(unit)
        elif discount < 0.10:
            discount_bins["0-10%"].append(unit)
        elif discount < 0.20:
            discount_bins["10-20%"].append(unit)
        else:
            discount_bins["20%+"].append(unit)
    avg_units_by_discount_bin = [
        (label, sum(values) / len(values) if values else 0)
        for label, values in discount_bins.items()
    ]

    missing_top = [
        (col, count)
        for col, count in sort_items(missing_counts, limit=12)
        if count > 0
    ]

    sections = []
    sections.append(
        f"""
        <section class="card wide">
          <h2>Quick overview</h2>
          {simple_table(["Metric", "Value"], metrics)}
        </section>
        """
    )
    sections.append(chart_shell("Net sales by month", line_chart(sort_items(sales_by_month, reverse=False), "EUR")))
    sections.append(chart_shell("Units sold by category", horizontal_bar_chart(sort_items(units_by_category), "units")))
    sections.append(chart_shell("Net sales by category", horizontal_bar_chart(sort_items(sales_by_category), "EUR")))
    sections.append(chart_shell("Net sales by region", horizontal_bar_chart(sort_items(sales_by_region), "EUR")))
    sections.append(chart_shell("Net sales by store", horizontal_bar_chart(sort_items(sales_by_store, limit=12), "EUR")))
    sections.append(chart_shell("Top products by units sold", horizontal_bar_chart(sort_items(units_by_product, limit=10), "units")))
    sections.append(chart_shell("Average units: promo vs no promo", horizontal_bar_chart([
        ("Promotion rows", promo_avg_units),
        ("Non-promotion rows", non_promo_avg_units),
    ], "units / row")))
    sections.append(chart_shell("Average units by discount band", horizontal_bar_chart(avg_units_by_discount_bin, "units / row")))
    sections.append(chart_shell("Distribution of units sold", histogram(units_clean, bins=14)))
    sections.append(chart_shell("Top missing-value columns", horizontal_bar_chart(missing_top, "missing rows")))
    sections.append(chart_shell("Data quality flags", horizontal_bar_chart(sort_items(quality_counts), "rows")))
    sections.append(chart_shell("Anomaly types", horizontal_bar_chart(sort_items(anomaly_counts), "rows")))

    top_category_rows = [
        [label, fmt_number(value)]
        for label, value in sort_items(sales_by_category)
    ]
    top_missing_rows = [
        [label, fmt_number(value), fmt_pct(value / n_rows)]
        for label, value in missing_top
    ]
    sections.append(
        f"""
        <section class="card wide">
          <h2>Simple tables</h2>
          <h3>Net sales by category</h3>
          {simple_table(["Category", "Net sales EUR"], top_category_rows)}
          <h3>Missing values</h3>
          {simple_table(["Column", "Missing rows", "Share"], top_missing_rows)}
        </section>
        """
    )

    return "\n".join(sections)


def html_page(content):
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Exploration shopper retail</title>
  <style>
    :root {{
      --ink: #1f2933;
      --muted: #5b6673;
      --bg: #f4f6f8;
      --card: #ffffff;
      --line: #cbd5df;
      --bar: #2f6f73;
      --dot: #c2410c;
    }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: var(--bg);
    }}
    header {{
      padding: 28px 34px 10px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 26px;
    }}
    .subtitle {{
      margin: 0;
      color: var(--muted);
      font-size: 14px;
    }}
    main {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(440px, 1fr));
      gap: 18px;
      padding: 18px 34px 34px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid #dde3ea;
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 1px 2px rgba(20, 35, 50, 0.06);
      overflow-x: auto;
    }}
    .wide {{
      grid-column: 1 / -1;
    }}
    h2 {{
      font-size: 17px;
      margin: 0 0 14px;
    }}
    h3 {{
      font-size: 14px;
      margin: 18px 0 8px;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 13px;
    }}
    th, td {{
      border-bottom: 1px solid #e4e9ef;
      padding: 8px 9px;
      text-align: left;
      white-space: nowrap;
    }}
    th {{
      background: #eef3f7;
      font-weight: 700;
    }}
    svg {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .bar {{
      fill: var(--bar);
    }}
    .line {{
      stroke: var(--bar);
      stroke-width: 3;
    }}
    .dot {{
      fill: var(--dot);
    }}
    .axis {{
      stroke: var(--line);
      stroke-width: 1;
    }}
    .axis-label, .tick, .value-label {{
      fill: var(--muted);
      font-size: 12px;
    }}
    .value-label {{
      font-weight: 700;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Exploration standard de la base shopper retail</h1>
    <p class="subtitle">Genere le {esc(generated_at)} a partir de shopper_retail_observations.csv.</p>
  </header>
  <main>
    {content}
  </main>
</body>
</html>
"""


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")
    rows, columns = read_rows(CSV_PATH)
    content = build_report(rows, columns)
    HTML_PATH.write_text(html_page(content), encoding="utf-8")
    print(f"Read {len(rows)} rows from {CSV_PATH.name}")
    print(f"Wrote {HTML_PATH}")


if __name__ == "__main__":
    main()

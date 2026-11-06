#!/usr/bin/env python3
"""Expense Analyzer.

Reads a CSV of expenses, categorises each expense, and reports:
  * total spending for each month
  * spending per category within each month
  * overall totals per category

CSV format (header row required):
    date,description,amount[,category]

  - date: YYYY-MM-DD or MM/DD/YYYY
  - amount: positive = money spent; negative = refund (netted separately)
  - category: optional — if present and non-empty it is used as-is;
    otherwise the category is inferred from the description.

Pure standard library — no dependencies.

Usage:
    python3 expense_analyzer.py expenses.csv
    python3 expense_analyzer.py expenses.csv --format json
    python3 expense_analyzer.py expenses.csv --month 2026-09
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime

# Ordered rules: the first category whose keyword appears in the
# description wins, so more specific entries come first
# (e.g. "Uber Eats" must hit Dining before "uber" hits Transport).
CATEGORY_RULES = [
    ("Dining", ["uber eats", "doordash", "grubhub", "restaurant", "starbucks",
                "coffee", "cafe", "bakery", "pizza", "burger", "chipotle",
                "mcdonald", "dining", "lunch", "dinner", "breakfast"]),
    ("Housing", ["rent", "mortgage", "apartment", "hoa", "landlord"]),
    ("Utilities", ["electric", "water bill", "gas bill", "internet", "wifi",
                   "phone", "mobile", "utility", "utilities", "spectrum",
                   "xfinity", "broadband"]),
    ("Groceries", ["kroger", "h-e-b", "heb", "whole foods", "trader joe",
                   "aldi", "instacart", "groceries", "grocery", "supermarket",
                   "costco", "walmart"]),
    ("Healthcare", ["pharmacy", "cvs", "walgreens", "doctor", "dental",
                    "dentist", "clinic", "hospital", "vision", "medical",
                    "health"]),
    ("Subscriptions", ["netflix", "spotify", "hulu", "subscription",
                       "membership", "gym", "icloud", "adobe", "prime",
                       "openai", "chatgpt", "youtube premium"]),
    ("Travel", ["airline", "flight", "hotel", "airbnb", "expedia",
                "southwest", "delta air", "united airlines",
                "american airlines", "booking"]),
    ("Transport", ["uber", "lyft", "shell", "exxon", "chevron", "fuel",
                   "gas station", "parking", "toll", "transit", "metro",
                   "car wash", "oil change"]),
    ("Shopping", ["amazon", "target", "best buy", "ikea", "etsy", "ebay",
                  "clothing", "shoes", "mall"]),
    ("Entertainment", ["movie", "cinema", "concert", "ticket", "steam",
                        "games", "bowling", "museum", "theatre", "theater"]),
    ("Personal Care", ["salon", "haircut", "spa", "cosmetics", "sephora",
                       "barber", "nails"]),
    ("Education", ["udemy", "coursera", "tuition", "course", "books",
                   "bookstore", "training"]),
]

UNCATEGORIZED = "Other"

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d")


def parse_date(raw):
    raw = (raw or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date: {raw!r} (expected YYYY-MM-DD or MM/DD/YYYY)")


def parse_amount(raw):
    cleaned = (raw or "").strip().replace("$", "").replace(",", "")
    if not cleaned:
        raise ValueError("Missing amount")
    return round(float(cleaned), 2)


def categorize(description):
    """Infer a category from the description using CATEGORY_RULES."""
    text = (description or "").lower()
    for category, keywords in CATEGORY_RULES:
        if any(keyword in text for keyword in keywords):
            return category
    return UNCATEGORIZED


def load_expenses(path):
    """Load expenses from a CSV file into a list of dicts."""
    expenses = []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row")
        fields = {name.strip().lower(): name for name in reader.fieldnames}
        for required in ("date", "description", "amount"):
            if required not in fields:
                raise ValueError(f"CSV is missing a '{required}' column")
        for line_no, row in enumerate(reader, start=2):
            try:
                date = parse_date(row[fields["date"]])
                amount = parse_amount(row[fields["amount"]])
            except ValueError as exc:
                raise ValueError(f"Line {line_no}: {exc}") from exc
            description = (row[fields["description"]] or "").strip()
            given = ""
            if "category" in fields:
                given = (row[fields["category"]] or "").strip()
            expenses.append({
                "date": date,
                "month": f"{date.year:04d}-{date.month:02d}",
                "description": description,
                "amount": amount,
                "category": given if given else categorize(description),
            })
    return expenses


def summarize(expenses):
    """Aggregate expenses into per-month and per-category totals."""
    months = {}
    overall_categories = defaultdict(float)
    total_spend = 0.0
    total_refunds = 0.0
    for expense in expenses:
        bucket = months.setdefault(expense["month"], {
            "spend": 0.0, "refunds": 0.0, "categories": defaultdict(float),
            "count": 0,
        })
        bucket["count"] += 1
        if expense["amount"] < 0:
            bucket["refunds"] += -expense["amount"]
            total_refunds += -expense["amount"]
        else:
            bucket["spend"] += expense["amount"]
            bucket["categories"][expense["category"]] += expense["amount"]
            overall_categories[expense["category"]] += expense["amount"]
            total_spend += expense["amount"]
    return {
        "months": {
            month: {
                "spend": round(data["spend"], 2),
                "refunds": round(data["refunds"], 2),
                "count": data["count"],
                "categories": {k: round(v, 2) for k, v in
                               sorted(data["categories"].items(),
                                      key=lambda item: -item[1])},
            }
            for month, data in sorted(months.items())
        },
        "overall_categories": {k: round(v, 2) for k, v in
                               sorted(overall_categories.items(),
                                      key=lambda item: -item[1])},
        "total_spend": round(total_spend, 2),
        "total_refunds": round(total_refunds, 2),
    }


def format_text(summary):
    lines = ["Expense Report", "=" * 60]
    for month, data in summary["months"].items():
        lines.append(f"\n{month}  —  total spend: ${data['spend']:,.2f}"
                     f"  ({data['count']} transactions)")
        if data["refunds"]:
            lines.append(f"  refunds: ${data['refunds']:,.2f}")
        for category, amount in data["categories"].items():
            lines.append(f"  {category:<16} ${amount:>10,.2f}")
    lines.append("\n" + "=" * 60)
    lines.append(f"TOTAL SPEND (all months): ${summary['total_spend']:,.2f}")
    if summary["total_refunds"]:
        lines.append(f"TOTAL REFUNDS:            ${summary['total_refunds']:,.2f}")
    lines.append("\nSpending by category (all months):")
    for category, amount in summary["overall_categories"].items():
        lines.append(f"  {category:<16} ${amount:>10,.2f}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Analyse expenses by month and category.")
    parser.add_argument("csv_file", help="Path to the expenses CSV file")
    parser.add_argument("--format", choices=("text", "json"), default="text",
                        help="Output format (default: text)")
    parser.add_argument("--month", help="Only report this month (YYYY-MM)")
    args = parser.parse_args(argv)

    try:
        expenses = load_expenses(args.csv_file)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if args.month:
        expenses = [e for e in expenses if e["month"] == args.month]
    summary = summarize(expenses)
    if args.format == "json":
        print(json.dumps(summary, indent=2))
    else:
        print(format_text(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())

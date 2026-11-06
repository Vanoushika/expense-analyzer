# Expense Analyzer

A small command-line tool that analyses your expenses from a CSV file:

- **Total spending for each month**
- **Every expense segregated into a category** — Housing, Groceries, Dining, Transport, Shopping, Subscriptions, Utilities, Healthcare, Travel, Entertainment, Personal Care, Education, or Other
- **Per-category totals** inside each month and across all months

Categories are inferred automatically from the expense description (for example, "Kroger" → Groceries, "Uber Eats" → Dining, "Netflix" → Subscriptions). If your CSV already has a `category` column, that value is used instead. Negative amounts are treated as refunds and reported separately, never mixed into spending.

Pure Python standard library — nothing to install.

## Input format

A CSV file with a header row:

```csv
date,description,amount
2026-09-01,Apartment rent,1500.00
2026-09-04,Kroger groceries,96.30
2026-09-09,DoorDash dinner,32.80
```

- `date` — `YYYY-MM-DD` or `MM/DD/YYYY`
- `description` — free text; used for categorisation
- `amount` — positive = money spent; negative = refund
- `category` — optional; overrides automatic categorisation when present

Bank and card exports can be adapted to this shape by renaming columns.

## Usage

```bash
# Full report
python3 expense_analyzer.py sample_expenses.csv

# A single month
python3 expense_analyzer.py sample_expenses.csv --month 2026-09

# Machine-readable output
python3 expense_analyzer.py sample_expenses.csv --format json
```

Example output (from the bundled `sample_expenses.csv`):

```
Expense Report
============================================================

2026-08  —  total spend: $1,864.58  (9 transactions)
  Housing          $  1,500.00
  Groceries        $    120.50
  ...

============================================================
TOTAL SPEND (all months): $5,809.26
```

## Project structure

```
expense-analyzer/
├── expense_analyzer.py      # The complete tool (CLI + categorisation + reports)
├── sample_expenses.csv      # Sample data covering three months
├── test_expense_analyzer.py # Unit tests
└── README.md
```

## Tests

```bash
python3 -m unittest -v
```

## Customising categories

Edit the `CATEGORY_RULES` list at the top of `expense_analyzer.py` — each entry maps a category name to the keywords that identify it. Rules are checked in order, so put more specific patterns first.

"""Unit tests for expense_analyzer. Run: python3 -m unittest -v"""

import os
import tempfile
import unittest

from expense_analyzer import (categorize, load_expenses, parse_amount,
                              parse_date, summarize)


class CategorizeTests(unittest.TestCase):
    def test_groceries(self):
        self.assertEqual(categorize("Kroger groceries"), "Groceries")

    def test_dining_beats_transport_for_uber_eats(self):
        self.assertEqual(categorize("Uber Eats order"), "Dining")

    def test_transport(self):
        self.assertEqual(categorize("Uber ride to airport"), "Transport")

    def test_subscriptions(self):
        self.assertEqual(categorize("Netflix subscription"), "Subscriptions")

    def test_housing(self):
        self.assertEqual(categorize("Apartment rent"), "Housing")

    def test_unknown_falls_back_to_other(self):
        self.assertEqual(categorize("Miscellaneous payment xyz"), "Other")


class ParsingTests(unittest.TestCase):
    def test_parse_date_iso(self):
        self.assertEqual(str(parse_date("2026-09-14")), "2026-09-14")

    def test_parse_date_us_format(self):
        self.assertEqual(str(parse_date("09/14/2026")), "2026-09-14")

    def test_parse_amount_with_symbols(self):
        self.assertEqual(parse_amount("$1,234.50"), 1234.50)


class SummarizeTests(unittest.TestCase):
    def _write_csv(self, text):
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".csv", delete=False, encoding="utf-8")
        handle.write(text)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def test_monthly_totals_and_categories(self):
        path = self._write_csv(
            "date,description,amount\n"
            "2026-09-01,Apartment rent,1500.00\n"
            "2026-09-04,Kroger groceries,100.00\n"
            "2026-10-01,Apartment rent,1500.00\n"
        )
        summary = summarize(load_expenses(path))
        self.assertEqual(summary["months"]["2026-09"]["spend"], 1600.00)
        self.assertEqual(summary["months"]["2026-09"]["categories"]["Housing"], 1500.00)
        self.assertEqual(summary["months"]["2026-10"]["spend"], 1500.00)
        self.assertEqual(summary["total_spend"], 3100.00)

    def test_refunds_are_separate_from_spend(self):
        path = self._write_csv(
            "date,description,amount\n"
            "2026-09-10,Amazon order,50.00\n"
            "2026-09-12,Amazon refund,-20.00\n"
        )
        summary = summarize(load_expenses(path))
        self.assertEqual(summary["months"]["2026-09"]["spend"], 50.00)
        self.assertEqual(summary["months"]["2026-09"]["refunds"], 20.00)

    def test_given_category_overrides_inference(self):
        path = self._write_csv(
            "date,description,amount,category\n"
            "2026-09-10,Amazon order,50.00,Gifts\n"
        )
        expenses = load_expenses(path)
        self.assertEqual(expenses[0]["category"], "Gifts")


if __name__ == "__main__":
    unittest.main()

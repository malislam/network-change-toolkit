import csv
from datetime import date
from pathlib import Path
import unittest
from inventory_report import review


class InventoryTests(unittest.TestCase):
    def setUp(self):
        with (Path(__file__).parent / 'inventory-demo.csv').open() as stream:
            self.rows = list(csv.DictReader(stream))
        self.today = date(2026, 9, 23)

    def test_baseline_expiry_and_missing_information(self):
        result = review(self.rows, self.today)
        self.assertIn('REVIEW: version differs from supplied baseline', result[0]['findings'])
        self.assertIn('DUE: license_renewal in 22 days', result[0]['findings'])
        self.assertIn('OVERDUE: support_end passed 22 days ago', result[1]['findings'])
        self.assertIn('UNKNOWN: owner missing', result[2]['findings'])
        self.assertIn('UNKNOWN: license_renewal not supplied', result[2]['findings'])

    def test_exact_horizon_and_today_are_due(self):
        self.rows[0]['license_renewal'] = '2026-09-23'
        self.assertIn('DUE: license_renewal in 0 days', review(self.rows, self.today)[0]['findings'])
        self.rows[0]['license_renewal'] = '2026-12-22'
        self.assertIn('DUE: license_renewal in 90 days', review(self.rows, self.today)[0]['findings'])

    def test_bad_date_and_duplicate_asset_rejected(self):
        self.rows[0]['license_renewal'] = 'not-a-date'
        with self.assertRaises(ValueError):
            review(self.rows, self.today)
        self.rows[0]['license_renewal'] = ''
        self.rows.append(self.rows[0])
        with self.assertRaises(ValueError):
            review(self.rows, self.today)

    def test_future_observation_and_empty_inventory_rejected(self):
        with self.assertRaises(ValueError):
            review(self.rows, date(2026, 1, 1))
        with self.assertRaises(ValueError):
            review([], self.today)


if __name__ == '__main__':
    unittest.main()

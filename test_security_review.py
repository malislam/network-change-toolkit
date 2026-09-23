import copy
import unittest
from pathlib import Path
from security_review import load, review

ROOT = Path(__file__).parent


class SecurityReviewTests(unittest.TestCase):
    def setUp(self):
        self.design = load(ROOT / 'security-design.json')
        self.policy = load(ROOT / 'security-policy-good.json')

    def test_good(self):
        self.assertEqual(review(self.design, self.policy), [])

    def test_drift(self):
        results = review(self.design, load(ROOT / 'security-policy-drift.json'))
        for prefix in ('UNAPPROVED:', 'BLOCKED:', 'NO LOGGING:', 'UNREACHED:'):
            self.assertTrue(any(r.startswith(prefix) for r in results), prefix)

    def test_early_deny_blocks_required(self):
        self.policy['rules'].insert(0, dict(id='deny-all', source='*', destination='*', service='*', action='deny', log=True))
        results = review(self.design, self.policy)
        self.assertEqual(sum(r.startswith('BLOCKED:') for r in results), 6)

    def test_empty_policy_is_not_pass(self):
        self.assertEqual(len(review(self.design, {'rules': []})), 6)

    def test_unknown_zone_rejected(self):
        self.policy['rules'][0]['source'] = 'typo'
        with self.assertRaises(ValueError):
            review(self.design, self.policy)

    def test_duplicate_id_rejected(self):
        self.policy['rules'].append(copy.deepcopy(self.policy['rules'][0]))
        with self.assertRaises(ValueError):
            review(self.design, self.policy)

    def test_log_string_rejected(self):
        self.policy['rules'][0]['log'] = 'true'
        with self.assertRaises(ValueError):
            review(self.design, self.policy)

    def test_extra_field_rejected(self):
        self.policy['rules'][0]['ports'] = 'any'
        with self.assertRaises(ValueError):
            review(self.design, self.policy)

    def test_reverse_direction_not_implicitly_allowed(self):
        self.policy['rules'].append(dict(id='reverse', source='cameras', destination='edge', service='video-tcp', action='allow', log=True))
        self.assertTrue(any(r.startswith('UNAPPROVED:') for r in review(self.design, self.policy)))


if __name__ == '__main__':
    unittest.main()

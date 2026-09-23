from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from review import compare, InputError, load_json, markdown


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.before = load_json(ROOT / "before.json")
        self.after = load_json(ROOT / "after-healthy.json")
        self.plan = load_json(ROOT / "plan.json")

    def result(self):
        return compare(self.before, self.after, self.plan)

    def test_healthy_and_exact_planned_transition_pass(self):
        result = self.result()
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["counts"]["ACCEPTED"], 1)

    def test_regressions_have_actionable_findings(self):
        self.after = load_json(ROOT / "after-regression.json")
        result = self.result()
        self.assertEqual(result["status"], "FAIL")
        failed = {item["path"] for item in result["findings"] if item["level"] == "FAIL"}
        self.assertIn("lab-nexus-b/after/vpc/peer_link", failed)
        self.assertIn("lab-nexus-a/vlans/120", failed)
        self.assertIn("lab-nexus-b/port_channels/port-channel10", failed)

    def test_partial_evidence_cannot_pass(self):
        self.after = load_json(ROOT / "after-partial.json")
        self.assertEqual(self.result()["status"], "INCOMPLETE")

    def test_missing_peer_cannot_pass(self):
        self.after["devices"].pop("lab-nexus-b")
        self.assertEqual(self.result()["status"], "INCOMPLETE")

    def test_missing_collection_is_not_reported_as_removed_objects(self):
        self.after["devices"]["lab-nexus-b"].pop("vlans")
        result = self.result()
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertFalse(any(f["level"] == "FAIL" for f in result["findings"]))

    def test_explicit_empty_collection_does_show_removals(self):
        self.after["devices"]["lab-nexus-b"]["vlans"] = {}
        self.assertEqual(self.result()["status"], "FAIL")

    def test_explicit_null_state_is_unknown(self):
        self.after["devices"]["lab-nexus-b"]["interfaces"]["Ethernet1/1"] = None
        self.assertEqual(self.result()["status"], "INCOMPLETE")

    def test_mismatched_exception_does_not_hide_regression(self):
        self.after["devices"]["lab-nexus-a"]["interfaces"]["Ethernet1/2"] = "suspended"
        result = self.result()
        self.assertEqual(result["status"], "FAIL")
        self.assertGreater(result["counts"]["INCOMPLETE"], 0)

    def test_explicit_decommission_is_accepted(self):
        self.plan["allowed_changes"][0]["after"] = None
        self.after["devices"]["lab-nexus-a"]["interfaces"].pop("Ethernet1/2")
        self.assertEqual(self.result()["status"], "PASS")

    def test_unknown_cannot_be_waived(self):
        self.plan["allowed_changes"][0]["after"] = "unknown"
        with self.assertRaises(InputError):
            self.result()

    def test_vpc_cannot_be_waived(self):
        self.plan["allowed_changes"][0]["collection"] = "vpc"
        with self.assertRaises(InputError):
            self.result()

    def test_wrong_target_version_fails(self):
        self.after["devices"]["lab-nexus-b"]["version"] = "WRONG"
        self.assertEqual(self.result()["status"], "FAIL")

    def test_missing_version_is_incomplete(self):
        self.after["devices"]["lab-nexus-b"].pop("version")
        self.assertEqual(self.result()["status"], "INCOMPLETE")

    def test_baseline_vpc_failure_is_not_hidden_by_recovery(self):
        self.before["devices"]["lab-nexus-a"]["vpc"]["consistency"] = "failed"
        self.assertEqual(self.result()["status"], "FAIL")

    def test_earlier_after_timestamp_fails(self):
        self.after["captured_at"] = self.before["captured_at"]
        self.assertEqual(self.result()["status"], "FAIL")

    def test_timestamp_without_timezone_is_incomplete(self):
        self.after["captured_at"] = "2026-01-01T02:00:00"
        self.assertEqual(self.result()["status"], "INCOMPLETE")

    def test_bad_state_is_rejected(self):
        self.after["devices"]["lab-nexus-a"]["interfaces"]["Ethernet1/1"] = "UPPP"
        with self.assertRaises(InputError):
            self.result()

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "duplicate.json"
            path.write_text('{"devices": {}, "devices": {}}', encoding="utf-8")
            with self.assertRaises(InputError):
                load_json(path)

    def test_markdown_escapes_table_delimiter(self):
        report = markdown(self.result())
        self.assertIn("bgp\\|default\\|192.0.2.10", report)

    def test_cli_writes_reports_and_returns_statuses(self):
        with tempfile.TemporaryDirectory() as temp:
            for fixture, expected in (("healthy", 0), ("regression", 1), ("partial", 2)):
                out = Path(temp) / f"{fixture}.json"
                md = Path(temp) / f"{fixture}.md"
                result = subprocess.run([sys.executable, str(ROOT / "review.py"),
                    str(ROOT / "before.json"), str(ROOT / f"after-{fixture}.json"),
                    "--plan", str(ROOT / "plan.json"), "--json", str(out), "--markdown", str(md)],
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(json.loads(out.read_text())["exit_code"], expected)
                self.assertIn("Nexus change evidence review", md.read_text())

    def test_cli_invalid_input_returns_three(self):
        result = subprocess.run([sys.executable, str(ROOT / "review.py"), "no-such-file.json",
            str(ROOT / "after-healthy.json"), "--plan", str(ROOT / "plan.json")],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 3)
        self.assertIn("Input/output error", result.stderr)


if __name__ == "__main__":
    unittest.main()

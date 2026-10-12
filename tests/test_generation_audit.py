"""Synthetic artifacts only: detect incomplete runs without disclosing replies."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from audit_generation import audit_model, digest, sha256


class TestGenerationAudit(unittest.TestCase):
    def fixture(self, root, first_status="complete", skip=False):
        d = root / "fake"
        (d / "chunks").mkdir(parents=True)
        meta = {"model": "fake", "prompts_sha256": "plan", "runner_sha256": "runner",
                "n_prompts": 2, "subset_sha256": None}
        (d / "run.json").write_text(json.dumps(meta))
        rows = []
        for pid, step, status in [("p1", 1, "complete"), ("m1", 1, first_status)] + (
                [] if skip else [("m1#2", 2, "complete")]):
            rows.append({"prompt_id": pid, "step": step, "status": status,
                         "model": "fake", "run_sha256": digest(meta),
                         "text": "PRIVATE RESPONSE MUST NEVER APPEAR",
                         "text_sha256": hashlib.sha256(b"PRIVATE RESPONSE MUST NEVER APPEAR").hexdigest()})
        self.write_rows(d, rows)
        if skip:
            (d / "chunks/s2-skipped.json").write_text(json.dumps({"step1_not_usable": ["m1"]}))
        return d, rows

    def write_rows(self, d, rows):
        (d / "responses.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        summary = {"records": len(rows), "planned": 3, "responses_sha256": sha256(d / "responses.jsonl"),
                   "run_sha256": digest(json.loads((d / "run.json").read_text())),
                   "status": {s: sum(r["status"] == s for r in rows) for s in {r["status"] for r in rows}}}
        (d / "summary-test.json").write_text(json.dumps(summary))

    def audit(self, d):
        result = audit_model(d, {"p1": 1, "m1": 1, "m1#2": 2}, "plan", "runner")
        self.assertNotIn("PRIVATE RESPONSE", json.dumps(result))
        return result

    def test_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            d, _ = self.fixture(Path(tmp))
            result = self.audit(d)
            self.assertEqual(result["disposition"], "complete")
            self.assertEqual(result["errors"], [])

    def test_recorded_unusable_first_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            d, _ = self.fixture(Path(tmp), "unexpected_reasoning", skip=True)
            result = self.audit(d)
            self.assertEqual(result["disposition"], "complete_with_generation_failures")
            self.assertEqual(result["recorded_step2_skips"], 1)
            self.assertEqual(result["unexpected_missing"], 0)

    def test_cannot_skip_usable_first_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            d, _ = self.fixture(Path(tmp), skip=True)
            self.assertEqual(self.audit(d)["disposition"], "incomplete")

    def test_missing_and_duplicate_do_not_cancel_each_other(self):
        with tempfile.TemporaryDirectory() as tmp:
            d, rows = self.fixture(Path(tmp))
            self.write_rows(d, rows[:2] + rows[:1])
            result = self.audit(d)
            self.assertEqual(result["records"], result["expected"])
            self.assertEqual(result["disposition"], "incomplete")
            self.assertIn("duplicate IDs: 1", result["errors"])

    def test_checksum_and_run_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            d, rows = self.fixture(Path(tmp))
            rows[0]["run_sha256"] = "wrong"
            rows[0]["text_sha256"] = "wrong"
            self.write_rows(d, rows)
            result = self.audit(d)
            self.assertIn("run binding mismatches: 1", result["errors"])
            self.assertIn("text checksum mismatches: 1", result["errors"])

    def test_bad_status_and_malformed_json_are_not_disclosed(self):
        with tempfile.TemporaryDirectory() as tmp:
            d, rows = self.fixture(Path(tmp))
            rows[0]["status"] = "PRIVATE RESPONSE MUST NEVER APPEAR"
            self.write_rows(d, rows)
            self.assertEqual(self.audit(d)["disposition"], "incomplete")
            (d / "responses.jsonl").write_text('{"text":"PRIVATE RESPONSE MUST NEVER APPEAR"')
            self.assertEqual(self.audit(d)["disposition"], "incomplete")


if __name__ == "__main__":
    unittest.main()

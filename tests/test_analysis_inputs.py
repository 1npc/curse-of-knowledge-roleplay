"""Exercise combined-plan joins and confirmatory isolation with synthetic replies."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "analysis"))
from score_run import load_inputs, summary_key, account_for_skipped_steps
from confirmatory import load_runs, Units


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


class TestCombinedPlan(unittest.TestCase):
    def test_documented_missing_second_step_preserves_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "chunks").mkdir()
            (d / "chunks/s2-skipped.json").write_text(json.dumps({"step1_not_usable": ["m1"]}))
            rows = [{"prompt_id": "m1", "status": "unexpected_reasoning", "text": "unusable"}]
            result = account_for_skipped_steps(rows, d, {"m1": {"next_step": [1]}})
            self.assertEqual(len(result), 2)
            self.assertEqual(result[1]["status"], "upstream_failure")
            self.assertTrue(result[1]["synthetic_missing"])
            with self.assertRaisesRegex(ValueError, "does not match"):
                account_for_skipped_steps(result, d, {"m1": {"next_step": [1]}})

    def test_combined_scoring_with_synthetic_responses(self):
        # Stimuli may be read before freeze; none of the actual model outputs are used.
        from oc.build import build_item, build_canon
        main = json.loads((ROOT / "items/main/skeletons.json").read_text())["items"]
        real = json.loads((ROOT / "items/real/skeletons.json").read_text())["items"][0]
        entry = json.loads((ROOT / "items/canon/subset.json").read_text())["entries"][0]
        base = next(it for it in main if it["id"] == entry["base"])
        prompts = [build_item(base, "zh")[0], build_item(real, "zh")[0], build_canon(entry, base)[0]]
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            plan = tmp / "plan.jsonl"
            write_rows(plan, prompts)
            with self.assertRaisesRegex(ValueError, "absent"):
                load_inputs(plan, [ROOT / "items/main/skeletons.json"])
            run = tmp / "run"
            write_rows(run / "fake/responses.jsonl", [
                {"prompt_id": p["prompt_id"], "status": "complete", "text": "No idea.", "finish_reason": "stop"}
                for p in prompts])
            command = [sys.executable, str(ROOT / "tools/score_run.py"), str(run), str(plan),
                       str(ROOT / "items/main/skeletons.json"), str(ROOT / "items/real/skeletons.json")]
            done = subprocess.run(command, capture_output=True, text=True,
                                  env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            self.assertEqual(done.returncode, 0, done.stderr)
            scored = [json.loads(line) for line in (run / "fake/scored.jsonl").read_text().splitlines()]
            by_id = {r['prompt_id']: r for r in scored}
            scored = [by_id[p['prompt_id']] for p in prompts]
            self.assertEqual(len(scored), 3)
            self.assertEqual([r["world"] for r in scored], [p["world"] for p in prompts])
            self.assertTrue(summary_key(scored[1]).startswith("real_world:"))
            self.assertTrue(summary_key(scored[2]).startswith("canon:"))

    def test_duplicate_sources_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            write_rows(tmp / "plan.jsonl", [{"prompt_id": "p", "item": "A"}])
            (tmp / "items.json").write_text(json.dumps({"items": [{"id": "A"}]}))
            with self.assertRaisesRegex(ValueError, "duplicate item"):
                load_inputs(tmp / "plan.jsonl", [tmp / "items.json", tmp / "items.json"])


class TestConfirmatoryScope(unittest.TestCase):
    @staticmethod
    def probe(item, hit=True):
        return {"prompt_id": item + ":probe", "item": item, "lang": "zh", "version": "A",
                "arm": "probe_translate", "S": "real", "status": "complete",
                "score": {"R": False, "U2": hit, "hit_t": hit, "hit_f": False}}

    def test_auxiliary_probes_and_scale_models_cannot_change_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            write_rows(run / "confirm/scored.jsonl", [self.probe("S01"), self.probe("N01", False)])
            write_rows(run / "scale/scored.jsonl", [self.probe("S01", False)])
            data = load_runs([run], models=["confirm"], item_ids={"S01"})
            self.assertEqual(set(data), {"confirm"})
            self.assertEqual(len(data["confirm"]), 1)
            self.assertTrue(Units(data).gate[("confirm", "zh")])

    def test_missing_requested_model_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "no scored files"):
                load_runs([Path(tmp)], models=["missing"], item_ids={"S01"})

    def test_conflicting_duplicate_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            one, two = Path(tmp) / "one", Path(tmp) / "two"
            write_rows(one / "model/scored.jsonl", [self.probe("S01")])
            write_rows(two / "model/scored.jsonl", [self.probe("S01", False)])
            with self.assertRaisesRegex(ValueError, "conflicting duplicate"):
                load_runs([one, two])

    def test_identical_truncated_duplicates_and_primary_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            one, two = Path(tmp) / "one", Path(tmp) / "two"
            row = dict(self.probe("S01"), status="truncated")
            write_rows(one / "model/scored.jsonl", [row])
            write_rows(two / "model/scored.jsonl", [row])
            rows = load_runs([one, two])["model"]
            self.assertEqual(len(rows), 1)
            self.assertFalse(rows[0]["score"]["hit_t"])


if __name__ == "__main__":
    unittest.main()

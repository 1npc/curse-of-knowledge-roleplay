"""Audit generation completeness without exposing response text or computing scores.

Only IDs, generation statuses, protocol metadata and checksums enter the report.
Use before the analysis freeze; this script never imports the scorer.

    python3 tools/audit_generation.py --out docs/main-generation-status.json
    python3 tools/audit_generation.py --runs /remote/project/runs --out /tmp/audit.json

Exit 0 means all runs are accounted for (including recorded generation failures),
1 means missing/inconsistent data, and 2 means a malformed audit input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUSES = {"complete", "truncated", "empty", "unexpected_finish", "unexpected_reasoning",
            "no_final", "tokenization_mismatch", "context_overflow"}
USABLE_STEP1 = {"complete", "truncated"}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def read_plan(path):
    steps = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            p = json.loads(line)
            pid = p["prompt_id"]
            if pid in steps or "#" in pid:
                raise ValueError("duplicate or invalid plan ID")
            steps[pid] = 1
            if p.get("next_step"):
                steps[pid + "#2"] = 2
    return steps


def audit_model(directory, steps, plan_sha, runner_sha):
    """Never return response fields, arbitrary status strings or parsing exceptions."""
    expected_n = len(steps)
    result = {"model": directory.name, "expected": expected_n, "records": 0,
              "status": {}, "disposition": "not_started", "errors": []}
    errors = result["errors"]
    if not directory.is_dir():
        return result
    if not (directory / "responses.jsonl").exists():
        result["disposition"] = "incomplete"
        errors.append("merged responses missing")
        return result
    try:
        meta = json.loads((directory / "run.json").read_text())
        run_sha = digest(meta)
        result["run_sha256"] = run_sha
        if meta["model"] != directory.name:
            errors.append("run model mismatch")
        if meta["prompts_sha256"] != plan_sha:
            errors.append("prompt plan hash mismatch")
        if meta["runner_sha256"] != runner_sha:
            errors.append("runner hash mismatch")
        if meta["n_prompts"] != sum(s == 1 for s in steps.values()):
            errors.append("run prompt count mismatch")
        if meta.get("subset_sha256") is not None:
            errors.append("unexpected prompt subset")

        seen, counts, record_n = {}, Counter(), 0
        duplicate_n = foreign_n = binding_n = step_n = text_hash_n = 0
        with (directory / "responses.jsonl").open(encoding="utf-8") as handle:
            for line in handle:
                r = json.loads(line)
                record_n += 1
                pid = r["prompt_id"]
                status = r["status"]
                # Map unrecognized strings to a fixed label: never echo arbitrary content.
                counts[status if status in STATUSES else "unknown_status"] += 1
                duplicate_n += pid in seen
                foreign_n += pid not in steps
                step_n += r.get("step") != steps.get(pid)
                binding_n += r.get("model") != directory.name or r.get("run_sha256") != run_sha
                if "text" in r:
                    text_hash_n += hashlib.sha256(r["text"].encode()).hexdigest() != r.get("text_sha256")
                seen[pid] = status
        result.update(records=record_n, status=dict(sorted(counts.items())),
                      responses_sha256=sha256(directory / "responses.jsonl"))
        for count, label in ((duplicate_n, "duplicate IDs"), (foreign_n, "unplanned IDs"),
                             (binding_n, "run binding mismatches"), (step_n, "step mismatches"),
                             (text_hash_n, "text checksum mismatches")):
            if count:
                errors.append(f"{label}: {count}")
        if "unknown_status" in counts:
            errors.append("unknown generation status")
        skipped_path = directory / "chunks" / "s2-skipped.json"
        skipped = json.loads(skipped_path.read_text())["step1_not_usable"] if skipped_path.exists() else []
        if len(skipped) != len(set(skipped)):
            errors.append("duplicate skip entries")
        valid_skips = {pid + "#2" for pid in skipped if pid + "#2" in steps
                       and pid in seen and seen[pid] in STATUSES - USABLE_STEP1}
        if len(valid_skips) != len(skipped):
            errors.append("skip without an observed unusable first step")
        missing = set(steps) - seen.keys()
        result.update(missing=len(missing), recorded_step2_skips=len(valid_skips),
                      unexpected_missing=len(missing - valid_skips))
        if missing != valid_skips:
            errors.append("missing IDs do not match recorded unusable first steps")

        intents = {p.name.removesuffix(".intent.json") for p in (directory / "chunks").glob("*.intent.json")}
        unresolved = sum(not (directory / "chunks" / (name + ".jsonl")).exists() for name in intents)
        result["unresolved_chunks"] = unresolved
        if unresolved:
            errors.append("unresolved generation intents")
        summaries = [json.loads(p.read_text()) for p in directory.glob("summary-*.json")]
        if not summaries:
            errors.append("completion summary missing")
        else:
            summary = max(summaries, key=lambda s: s.get("finished", ""))
            for key, expected in (("records", record_n), ("planned", expected_n),
                                  ("responses_sha256", result["responses_sha256"]),
                                  ("run_sha256", run_sha), ("status", dict(counts))):
                if summary.get(key) != expected:
                    errors.append(f"completion summary mismatch: {key}")
        result["disposition"] = "incomplete" if errors else (
            "complete_with_generation_failures" if valid_skips or any(
                counts[s] for s in STATUSES - USABLE_STEP1) else "complete")
    except (OSError, ValueError, KeyError, TypeError):
        # JSON exceptions can contain excerpts of source text. Do not print them.
        errors.append("unreadable or malformed generation artifact (details suppressed)")
        result["disposition"] = "incomplete"
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registry", type=Path, default=ROOT / "docs" / "main-run-registry.json")
    ap.add_argument("--runs", type=Path, default=ROOT / "runs")
    ap.add_argument("--inputs", type=Path, help="directory containing the three deployed plan files")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    try:
        registry = json.loads(args.registry.read_text())
        report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
                  "scope": "generation metadata and checksums only; no response text or scores",
                  "generation_commit": registry["generation_commit"], "runs": {}}
        for name, config in registry["runs"].items():
            plan = args.inputs / Path(config["plan"]).name if args.inputs else ROOT / config["plan"]
            plan_sha = sha256(plan)
            if plan_sha != config["plan_sha256"]:
                raise ValueError("local plan hash mismatch")
            steps = read_plan(plan)
            report["runs"][name] = [audit_model(args.runs / name / model, steps, plan_sha,
                                                registry["runner_sha256"])
                                     for model in config["models"]]
        rows = [r for models in report["runs"].values() for r in models]
        report["all_accounted_for"] = all(r["disposition"].startswith("complete") for r in rows)
        report["records"] = sum(r["records"] for r in rows)
        report["expected"] = sum(r["expected"] for r in rows)
        report["recorded_step2_skips"] = sum(r.get("recorded_step2_skips", 0) for r in rows)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n")
        for name, models in report["runs"].items():
            for r in models:
                print(f"{name}/{r['model']}: {r['disposition']} {r['records']}/{r['expected']}"
                      f"; recorded skips={r.get('recorded_step2_skips', 0)}; errors={len(r['errors'])}")
        print(f"All accounted for: {report['all_accounted_for']}")
        return 0 if report["all_accounted_for"] else 1
    except (OSError, ValueError, KeyError, TypeError):
        print("Invalid audit input; details suppressed to avoid exposing response text.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

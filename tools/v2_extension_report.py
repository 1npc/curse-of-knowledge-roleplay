"""Study 2 confirmation set on the seven models outside the locked four-model cohort (added 10/6).

Scores runs/<run>/<model>/responses.jsonl with the frozen v2 scorer (tools/score_access_v2.py), then
applies the frozen v2 confirmatory function (oc_v2.analyze.confirmatory) to (a) the seven added
models and (b) all eleven, reusing the existing core-cohort scores. These are extension analyses;
the locked four-model result is unchanged. Also writes per-model, per-channel net use.
Usage: python3 tools/v2_extension_report.py runs/<run>
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from oc_v2.analyze import confirmatory  # noqa: E402

CORE = {"gemma4_31b": "analysis/h200-v2-20261002/gemma4_31b/scores/confirmatory/gemma4_31b.jsonl",
        **{m: f"analysis/h200-v2-20261002/core-rest/scores/confirmatory/{m}.jsonl" for m in ("glm47_flash", "nemotron3_nano30b", "qwen35_9b")}}


def load(p):
    return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]


def main():
    run = Path(sys.argv[1])
    added = sorted(d.name for d in run.iterdir() if (d / "responses.jsonl").exists())
    rows = []
    for m in added:
        out = run / m / "v2scored.jsonl"
        if not out.exists():
            subprocess.run([sys.executable, str(ROOT / "tools/score_access_v2.py"), "--plan", str(ROOT / "items/access-v2/confirmatory.jsonl"),
                            "--items", str(ROOT / "items/access-v2/confirmatory-items.json"), "--responses", str(run / m / "responses.jsonl"),
                            "--model", m, "--out", str(out)], check=True)
        rows += load(out)
    core = [r for m, p in CORE.items() for r in load(ROOT / p)]
    res = {"added_models": added, "added": confirmatory(rows, added), "all_eleven": confirmatory(rows + core, added + list(CORE))}
    per = defaultdict(dict)
    for r in rows + core:
        if r["set"] == "confirmatory" and r["Q"] in ("content", "plan") and r["representation"] == "R2" and r["delay"] == 0 \
                and r["method"] == "full" and not r["accessible"]:
            per[r["model"]].setdefault(r["boundary"], []).append(r["D"])
    res["per_model_full_context"] = {m: {b: mean(v) for b, v in d.items()} for m, d in per.items()}
    probes = defaultdict(list)
    for r in rows:
        if r["Q"] == "state":
            probes[r["model"]].append(r["state_correct"])
    res["added_probe_accuracy"] = {m: mean(v) for m, v in probes.items()}
    (run / "v2-extension.json").write_text(json.dumps(res, indent=1, default=str))
    for k in ("added", "all_eleven"):
        h = res[k]
        print(k, {b: round(100 * v["estimate"], 1) for b, v in h["H1_components"].items()}, "C2", round(100 * h["H2"]["estimate"], 1),
              {c: round(100 * v["estimate"], 1) for c, v in h["H3_components"].items()}, h["family_p_holm"])
    for m, d in sorted(res["per_model_full_context"].items()):
        print(f"{m:<18}", {b: round(100 * v, 1) for b, v in d.items()})


if __name__ == "__main__":
    main()

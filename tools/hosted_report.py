"""Score and summarize the hosted-model runs (runs/hosted-1008; added 10/8).

Splits each model's replies into Study 1 prompts and bridge prompts, scores them with the frozen
scorers (tools/score_run.py and tools/score_access_v2.py), and reports per model:
  Study 1 (content question): net use for the repertoire (C-T- D0), the inaudibility flag (E_inaud_S),
  the non-comprehension flag and the prose sentence when run; target use for the fluent control;
  state-probe accuracy; translation recovery of both canaries.
  Bridge: net use of unheard speech and use of audible speech under Study 2's prompt and with all
  four Study 1 features.
Writes analysis/results/added-1006/hosted.json.
Usage: python3 tools/hosted_report.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "runs/hosted-1008"
MODELS = ["gpt6sol", "opus55", "sonnet55", "gemini31pro", "gemini38flash", "grok47", "deepseekv4pro"]


def main():
    s1_plan = {json.loads(l)["prompt_id"] for l in (ROOT / "items/hosted/study1_core.jsonl").read_text().splitlines()}
    br_plan = {json.loads(l)["prompt_id"]: json.loads(l)["bridge"] for l in (ROOT / "items/access-v2/bridge.jsonl").read_text().splitlines()}
    s1_dir, br_dir = ROOT / "runs/hosted-1008-s1", ROOT / "runs/hosted-1008-bridge"
    res = {}
    for m in MODELS:
        raw = [json.loads(l) for l in (RUN / m / "responses.jsonl").read_text().splitlines() if l.strip()]
        best = {}  # a prompt repeated after a restart: keep the last complete reply, else the last one
        for r in raw:
            if r["prompt_id"] not in best or r["status"] == "complete" or best[r["prompt_id"]]["status"] != "complete":
                best[r["prompt_id"]] = r
        rows = list(best.values())
        for d, keep in ((s1_dir, s1_plan), (br_dir, br_plan)):
            (d / m).mkdir(parents=True, exist_ok=True)
            (d / m / "responses.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows if r["prompt_id"] in keep))
        res[m] = {"replies": len(rows), "status": {s: sum(r["status"] == s for r in rows) for s in {r["status"] for r in rows}},
                  "cost": json.loads((RUN / m / "ledger.json").read_text())["models"].get(m, 0.0)}
    subprocess.run([sys.executable, str(ROOT / "tools/score_run.py"), str(s1_dir), str(ROOT / "items/hosted/study1_core.jsonl"),
                    str(ROOT / "items/main/skeletons.json"), str(ROOT / "items/real/skeletons.json"), "--quiet"], check=True, capture_output=True)
    for m in MODELS:
        rows = [json.loads(l) for l in (s1_dir / m / "scored.jsonl").read_text().splitlines() if l.strip()]
        sel = lambda c, D, S: [r for r in rows if r["arm"] == "main" and r["cell"] == c and r["D"] == D and r["S"] == S]
        net = lambda rs: mean(r["score"]["hit_t"] for r in rs) - mean(r["score"]["hit_f"] for r in rs) if len(rs) >= 100 else None  # cells not run report None
        out = {"repertoire": net(sel("C-T-", "D0", "real")), "inaudible_flag": net(sel("Einaud_S", "D0", "english")),
               "understood_flag": net(sel("C-T-_flag", "D0", "real")), "prose": net(sel("C-T-", "D1", "real")),
               "fluent_control_use": mean(r["score"]["hit_t"] for r in sel("C+T-", "D0", "real")) if len(sel("C+T-", "D0", "real")) >= 100 else None}
        out["n_cells"] = {k: len(sel(*c)) for k, c in {"repertoire": ("C-T-", "D0", "real"), "inaudible_flag": ("Einaud_S", "D0", "english"),
                          "understood_flag": ("C-T-_flag", "D0", "real"), "prose": ("C-T-", "D1", "real")}.items()}
        hits = [r for r in sel("C-T-", "D0", "real") if r["score"]["hit_t"]]
        out["repertoire_hit_modes"] = {k: sum(r["score"]["mode"] == k for r in hits) for k in ("unframed", "tentative", "attributed")}
        probes = [r for r in rows if r["arm"] == "probe_state"]
        out["state_probe_correct"] = mean(r.get("probe_answer") == r.get("probe_expected") for r in probes) if probes else None
        tr = [r for r in rows if r["arm"] == "probe_translate"]
        out["translation_both_canaries"] = mean(r["score"]["U2"] for r in tr) if tr else None
        out["n_study1"] = len(rows)
        res[m]["study1"] = out
        bfile = br_dir / m / "v2scored.jsonl"
        bplan = br_dir / m / "plan.jsonl"
        ids = {json.loads(l)["prompt_id"] for l in (br_dir / m / "responses.jsonl").read_text().splitlines()}
        bplan.write_text("".join(l + "\n" for l in (ROOT / "items/access-v2/bridge.jsonl").read_text().splitlines() if json.loads(l)["prompt_id"] in ids))
        subprocess.run([sys.executable, str(ROOT / "tools/score_access_v2.py"), "--plan", str(bplan), "--items", str(ROOT / "items/access-v2/discovery-items.json"),
                        "--responses", str(br_dir / m / "responses.jsonl"), "--model", m, "--out", str(bfile)], check=True, capture_output=True)
        b = [json.loads(l) for l in bfile.read_text().splitlines() if l.strip()]
        bres = {}
        for sw in ("base", "all"):
            inacc = [r["D"] for r in b if br_plan[r["prompt_id"]] == sw and not r["accessible"]]
            acc = [r["hit_t"] for r in b if br_plan[r["prompt_id"]] == sw and r["accessible"]]
            bres[sw] = {"unheard_net": mean(inacc) if inacc else None, "audible_use": mean(acc) if acc else None, "n": len(inacc) + len(acc)}
        res[m]["bridge"] = bres
        f = lambda x: "  –  " if x is None else f"{100 * x:5.1f}"
        s = out
        print(f"{m:<14} ${res[m]['cost']:.2f}  rep {f(s['repertoire'])} inaud {f(s['inaudible_flag'])} undflag {f(s['understood_flag'])} "
              f"prose {f(s['prose'])} fluent {f(s['fluent_control_use'])} probe {f(s['state_probe_correct'])} transl {f(s['translation_both_canaries'])} | "
              f"bridge base {f(bres['base']['unheard_net'])} (aud {f(bres['base']['audible_use'])}) all {f(bres['all']['unheard_net'])} (aud {f(bres['all']['audible_use'])})")
    (ROOT / "analysis/results/added-1006/hosted.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

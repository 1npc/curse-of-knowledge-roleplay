"""Derived inputs for the v4 figures: per-model core cells, per-question repertoire leakage and leak framing.

Writes analysis/results/added-1006/{open_content_only,by_question,leak_framing}.json from scored runs.
Run from the repository root.
"""
import csv
import json
from collections import defaultdict
from statistics import mean

OUT = "analysis/results/added-1006/"
OPEN = ["falcon_h1_34b", "gemma4_12b", "gemma4_31b", "glm47_flash", "gpt_oss_20b", "mistral_small3",
        "nemotron3_nano30b", "phi4", "qwen35_9b", "qwen38_27b", "seed_oss_36b"]
HOSTED = ["deepseekv4pro", "sonnet55", "gemini31pro", "opus55", "grok47", "gemini38flash", "gpt6sol"]
SMALL = ("qwen35_4b", "qwen35_2b", "qwen35_08b", "gemma4_e2b")


def rows(path):
    return [json.loads(l) for l in open(path)]


def open_content_only():
    out = {}
    for m in OPEN:
        rs = rows(f"runs/main-v1/{m}/scored.jsonl")

        def sel(c, D, S, v=None):
            return [r for r in rs if r["arm"] == "main" and r.get("set") == "main" and r["Q"] == "content" and r["cell"] == c
                    and r["D"] == D and r["S"] == S and (v is None or r["version"] == v)]

        def net(x):
            return mean(r["score"]["hit_t"] for r in x) - mean(r["score"]["hit_f"] for r in x)

        out[m] = {"repertoire": net(sel("C-T-", "D0", "real")), "inaudible_flag": net(sel("Einaud_S", "D0", "english")),
                  "understood_flag": net(sel("C-T-_flag", "D0", "real")), "prose": net(sel("C-T-", "D1", "real")),
                  "fluent_control_use": mean(r["score"]["hit_t"] for r in sel("C+T-", "D0", "real", "A"))}
    json.dump(out, open(OUT + "open_content_only.json", "w"), indent=1)


def by_question():
    d = defaultdict(dict)
    for r in csv.DictReader(open("analysis/results/main-20260929/by_Q.csv")):
        if r["cell"] == "C-T-" and r["D"] == "D0" and r["S"] == "real" and r["model"] not in SMALL:
            d[r["model"]][r["Q"]] = float(r["oc"])
    json.dump(d, open(OUT + "by_question.json", "w"), indent=1)


def leak_framing():
    def modes(rs):
        hits = [r for r in rs if r["score"]["hit_t"]]
        n = len(hits)
        return {"n": n, **{k: (sum(r["score"]["mode"] == k for r in hits) / n if n else None)
                           for k in ("unframed", "attributed", "tentative")}}

    out = {}
    for m in OPEN:
        rs = rows(f"runs/main-v1/{m}/scored.jsonl")
        out[m] = modes([r for r in rs if r["arm"] == "main" and r.get("set") == "main" and r["Q"] == "content"
                        and r["cell"] == "C-T-" and r["D"] == "D0" and r["S"] == "real"])
    for m in HOSTED:
        rs = rows(f"runs/hosted-1008-s1/{m}/scored.jsonl")
        out[m] = modes([r for r in rs if r["arm"] == "main" and r["cell"] == "C-T-" and r["D"] == "D0" and r["S"] == "real"])
    json.dump(out, open(OUT + "leak_framing.json", "w"), indent=1)


if __name__ == "__main__":
    open_content_only()
    by_question()
    leak_framing()

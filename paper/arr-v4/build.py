"""Assemble the restructured ARR manuscript (v4) (standard library only; formatting, no statistics).

Study 1 tables and figures are generated from analysis/results/main-20260929 (code adapted from
the archived two-boundary draft, paper/arr/archive/pre-access-v2-source.zip). Study 2 floats are
copied verbatim from the access-v2 manuscript paper/arr/main.tex by their labels, so their numbers
stay exactly those of the frozen access-v2 analysis. The prose lives in body.tex; markers of the
form `% INSERT name` are replaced here. Output: main.tex (compile with latexmk -pdf main.tex).
Usage: python3 paper/arr-v3/build.py
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal, ROUND_HALF_UP
import re
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
R1 = ROOT / "analysis/results/main-20260929"
V2 = (ROOT / "paper/arr/main.tex").read_text(encoding="utf-8")
NAMES2 = {"gpt6sol": "GPT-6 Sol", "opus55": "Claude Opus 5.5", "sonnet55": "Claude Sonnet 5.5", "gemini31pro": "Gemini 3.1 Pro",
          "gemini38flash": "Gemini 3.8 Flash", "grok47": "Grok 4.7", "deepseekv4pro": "DeepSeek-V4-Pro"}
NAMES = {"qwen38_27b": "Qwen3.8-27B", "qwen35_9b": "Qwen3.5-9B", "gemma4_31b": "Gemma-4-31B", "gemma4_12b": "Gemma-4-12B",
         "glm47_flash": "GLM-4.7-Flash", "mistral_small3": "Mistral-Small-24B", "gpt_oss_20b": "gpt-oss-20b", "phi4": "Phi-4",
         "seed_oss_36b": "Seed-OSS-36B", "nemotron3_nano30b": "Nemotron-3-Nano", "falcon_h1_34b": "Falcon-H1-34B"}


def load(f):
    return json.loads((R1 / f).read_text())


def pc(x):
    return f"{100 * x:.1f}"


def ci(r):
    return f"[{pc(r['ci95'][0])}, {pc(r['ci95'][1])}]"


def esc(s):
    return str(s).replace("_", r"\_").replace("&", r"\&").replace("%", r"\%")


def table(rows, cols, caption, label, wide=False, tight=False):
    env = "table*" if wide else "table"
    return "\n".join([f"\\begin{{{env}}}[t]", r"\centering\footnotesize\setlength{\tabcolsep}{3.2pt}" if tight else r"\centering\small", r"\begin{tabular}{@{}" + cols + r"@{}}", r"\toprule", *rows,
                      r"\bottomrule", r"\end{tabular}", r"\caption{" + caption + "}", r"\label{" + label + "}", f"\\end{{{env}}}"])


CAPTIONS = {
    "tab:accesscases": "Study 2 channels. Each event contains an item--location fact. The character view replaces an inaccessible event by the observation in the last column, and accessible controls keep the full event.",
    "fig:discoveryheatmap": "Study 2 discovery: 11 models, 96 scenes, direct Boolean (R2). (a) Net use of inaccessible content (pp); (b) use of the same content when it is accessible (\\%); (c) means over channels. Dots mark the four confirmation models.",
    "fig:behavior": "Study 2, four confirmation models, 32 scenes. (a) Net use after zero, two or four neutral exchanges; (b) change from zero exchanges under full context; (c) change in choosing location A when the inaccessible fact switches from B to A. Bars are 95\\% skeleton-bootstrap intervals.",
    "tab:confirm": "Study 2 confirmation (four models, 96 original-character scenes). The channel test requires all four channels to be positive, the state-correct test uses replies whose state probe is correct (6,068), and the view test requires the view to reduce leakage, keep accessible use within 5 pp, and keep more observations than removal. One Holm-adjusted $p$ per family.",
}


CAPTION_TRIMS = [(" The pooled four-boundary claim does not assert a positive effect in every cell.", ""),
                 (" These saved-data summaries add no hypothesis test.", ""),
                 (" These are secondary descriptive intervals, without additional confirmation tests.", ""),
                 ("with 95\\% descriptive intervals", "with 95\\% intervals"),
                 (" These are descriptive cells with unadjusted 95\\% paired-bootstrap intervals.", " Intervals are 95\\% paired-bootstrap intervals."),
                 ("Additional descriptive option-position sensitivity", "Option-position sensitivity"),
                 (" This selected illustration is not a prevalence sample.", "")]


def set_caption(block, text):
    i = block.find("\\caption{") + len("\\caption{")
    depth, j = 1, i
    while depth:
        depth += {"{": 1, "}": -1}.get(block[j], 0)
        j += 1
    return block[:i] + text + block[j - 1:]


def v2_float(label, renames=()):
    i = V2.find("\\label{%s}" % label)
    assert i > 0, label
    b = max(V2.rfind("\\begin{table", 0, i), V2.rfind("\\begin{figure", 0, i))
    kind = re.match(r"\\begin\{(\w+\*?)\}", V2[b:]).group(1)
    e = V2.find("\\end{%s}" % kind, i) + len("\\end{%s}" % kind)
    out = V2[b:e]
    for a, c in renames:
        out = out.replace(a, c)
    assert "HumanField" not in out, label
    if label in CAPTIONS:
        out = set_caption(out, CAPTIONS[label])
    for a, c in CAPTION_TRIMS:
        out = out.replace(a, c)
    return out


def study1():
    conf, models = load("confirmatory.json"), load("model_metrics.json")
    models.sort(key=lambda r: r["language"]["point"])
    ins = {}
    # Figure: per-model leakage under five ways of stating the boundary
    fig = [r"\begin{figure*}[t]", r"\centering", r"\begin{tikzpicture}[x=0.112cm,y=0.47cm,font=\footnotesize]"]
    colors = ["OCblue", "OCgreen", "OCorange", "OCpurple", "OCred"]
    specs = [("language", "Language repertoire only"), ("flag_understand", "Per-utterance flag: not understood"),
             ("flag_inaudible", "Per-utterance flag: not audible"), ("narrated_inaudible", "Not audible, also narrated"),
             ("language_prose", "Repertoire plus a prose sentence")]
    for j, (k, label) in enumerate(specs):
        x = 0 if j % 2 == 0 else 51
        y = 12.2 - (j // 2) * .62
        fig.append(f"\\fill[{colors[j]}] ({x},{y}) circle[radius=1.8pt];\\node[anchor=west] at ({x + 2},{y}) {{{label}}};")
    for x in range(0, 101, 20):
        fig.append(f"\\draw[black!13] ({x},-.55)--({x},10.6);\\node[anchor=north] at ({x},-.62) {{{x}}};")
    for i, r in enumerate(models):
        y = 10 - i
        fig.append(f"\\node[anchor=east] at (-3,{y}) {{{NAMES[r['model']]}}};")
        for j, (key, _) in enumerate(specs):
            yy = y + (2 - j) * .145
            x = 100 * r[key]["point"]
            lo, hi = [100 * a for a in r[key]["ci95"]]
            fig.append(f"\\draw[{colors[j]},line width=.55pt] ({lo:.3f},{yy:.3f})--({hi:.3f},{yy:.3f});"
                       f"\\fill[{colors[j]}] ({x:.3f},{yy:.3f}) circle[radius=1.6pt];")
    fig += [r"\node[anchor=north] at (50,-1.25) {Net use of inaccessible content, $100D$ (target minus foil, pp)};", r"\end{tikzpicture}",
            r"\caption{Study 1: how the boundary is stated changes leakage, but no format removes it for most models. "
            r"Each row is one model, averaged over its capable language units; bars are 95\% skeleton-bootstrap intervals.}",
            r"\label{fig:s1}", r"\end{figure*}"]
    ins["S1_FIGURE"] = "\n".join(fig)
    desc = {"H1": "Leak, cannot understand", "H1i": "Leak, cannot hear", "H2a": "Sentence lowers leak",
            "H2b": "Narration lowers leak", "H3": "Flag vs.\ repertoire",
            "H4": "Hear minus understand", "H5a": "Leak, state read correctly"}
    rows = [r"Test & Estimate [95\% CI] & $p$\\", r"\midrule"]
    for k, label in desc.items():
        r = conf[k]
        rows.append(f"{label} & {pc(r['point'])} {ci(r)} & {r['p_holm']:.3f}" + r"\\")
    rows.append(r"\midrule")
    for key, label in [("reduction", "List-first, reduction (\\%)"), ("retention", "List-first, permitted use")]:
        r = conf["H5b"][key]
        rows.append(f"{label} & {pc(r['point'])} {ci(r)} & " + (f"{conf['H5b']['p_holm']:.3f}" if key == "reduction" else "joint") + r"\\")
    ins["S1_TABLE"] = table(rows, "lrr", "The eight tests of Study~1 (11 models, pp unless noted). Thresholds are 10 pp for the three net-use tests, zero "
                            "for the four contrasts, and a 50\\% reduction with a loss of at most 5 pp in permitted use for the list-first prompt. Values "
                            "of $p$ come from one-sided bootstrap tests with Holm correction over the eight tests, and 0.004 is the smallest value 2,000 "
                            "draws resolve. The last row is the permitted-use condition of the list-first test.", "tab:s1", False, tight=True)
    rows = [r"& \multicolumn{2}{c}{Not understood} & \multicolumn{2}{c}{Not audible} & Transl.\\",
            r"Model & Base & Filter & Base & Filter & (pp)\\", r"\midrule"]
    for r in models:
        rows.append(NAMES[r["model"]] + " & " + " & ".join(pc(r[k]["point"]) for k in
                    ["base_language", "m1g_language", "base_inaudible", "m1g_inaudible", "retention"]) + r"\\")
    ins["S1_MITIGATION"] = table(rows, "lrrrrr", "Study 1, the list-first prompt (Filter) by model (content and planning questions). Leakage is net use in pp; the last "
                                 "column is the change in target use when a working translator makes the content accessible.", "tab:s1m", tight=True)
    rows = [r"Model & \multicolumn{2}{c}{First-step list names target (\%)} & Translator use change\\",
            r"& Not understood & Not audible & (pp) [95\% CI]\\", r"\midrule"]
    for r in models:
        rows.append(NAMES[r["model"]] + " & " + pc(r["step1_language"]["point"]) + " & " + pc(r["step1_inaudible"]["point"]) +
                    " & " + pc(r["retention"]["point"]) + " " + ci(r["retention"]) + r"\\")
    ins["S1_STEP1"] = table(rows, "lrrl", "Study 1: target use in the first-step perception list of the list-first prompt, which predicts where the filter fails.", "tab:s1step1", True)
    labels = {"unconditional": "Unconditional (no capability filter)", "soft": "Soft hedge credit", "exclude_truncated": "Exclude truncated",
              "exclude_flagged": "Exclude language/echo flags", "complete_only": "Complete responses only",
              "worst_failed_mitigation": "Worst-case failed list-first reply", "u2": "Both canaries required"}
    rows = [r"Variant & Not underst. & Not audible & Reduction (\%) & Translator (pp) & Supported\\", r"\midrule"]
    for k, v in load("sensitivities.json").items():
        rows.append(labels[k] + " & " + " & ".join([pc(v["H1"]["point"]), pc(v["H1i"]["point"]), pc(v["H5b"]["reduction"]["point"]),
                                                     pc(v["H5b"]["retention"]["point"]), f"{sum(x['supported'] for x in v.values())}/8"]) + r"\\")
    ins["S1_SENSITIVITY"] = table(rows, "lrrrrc", "Study 1 scoring and conditioning sensitivities.", "tab:s1sens", True)
    rows = [r"Subset & Reduction (\%) & Transl. (pp) & Holm $p$\\", r"\midrule"]
    sets = list(load("by_language_confirmatory.json").items()) + [("Without " + k, v) for k, v in load("leave_one_character_out.json").items()] + \
        [("Two-way bootstrap", load("two_way_bootstrap.json")["tests"])]
    for name, v in sets:
        h = v["H5b"]
        rows.append(esc({"zh": "Chinese", "ja": "Japanese", "es": "Spanish"}.get(name, name)) + " & " + pc(h["reduction"]["point"]) + " & " + pc(h["retention"]["point"]) + " & " + f"{h['p_holm']:.3f}" + r"\\")
    ins["S1_SUBGROUPS"] = table(rows, "lrrr", "The list-first test of Study 1 by language, leaving one character out, and with a two-way (skeleton $\\times$ "
                                "character) bootstrap. The joint criterion fails in several subsets.", "tab:s1sub", tight=True)
    el = {"deny_while_using": "Denial while using the content, prose sentence", "unattributed_share_D1_minus_U": "Unattributed use, prose sentence minus no language state",
          "offline_translator": "Offline $-$ absent translator", "original_confounded_boundary": "Repertoire minus narrated inaudibility (unmatched)",
          "FS_language_reduction": "Few-shot reduction (4 models)", "mode_DA_minus_OH": "Direct address $-$ overheard",
          "spoken_minus_real": "Spoken-only $-$ full state", "language_zh_minus_ja": "Chinese minus Japanese", "language_zh_minus_es": "Chinese minus Spanish",
          "language_ja_minus_es": "Japanese minus Spanish", "admission_A_D1_minus_U": "Explicit admission, prose sentence minus no language state",
          "admission_admission_with_attribution_D1_minus_U": "Admission or attribution, prose sentence minus no language state",
          "canon_canon_C+_D0_minus_U": "Canon speakers, repertoire minus no language state", "canon_canon_weak_C-_D0_minus_U": "Weak canon non-speakers, repertoire minus no language state",
          "canon_name_prior_C-_D0_minus_U": "Non-speakers with a name prior, repertoire minus no language state", "non_cyberpunk_minus_main": "Present-day world $-$ main set"}
    rows = [r"Exploratory contrast & Estimate (pp) & 95\% CI & BH $q$\\", r"\midrule"]
    for k, v in load("exploratory.json").items():
        rows.append(el.get(k, esc(k)) + " & " + pc(v["point"]) + " & " + ci(v) + " & " + f"{v['q_bh']:.3f}" + r"\\")
    ins["S1_EXPLORATORY"] = table(rows, "lrrr", "Study 1 exploratory family (Benjamini--Hochberg, $q=.10$). "
                                  "No language state means the state omits the character's languages. The world comparison uses different scenario sets.", "tab:s1expl", True)
    rob = load("prompt_robustness.json")
    rows = [r"Model & Main prompt & Boundary-instruction & Minimal & Community\\", r"\midrule"]
    for m in ["gemma4_31b", "qwen38_27b", "qwen35_9b"]:
        d = {r["arm"]: r for r in rob if r["model"] == m}
        rows.append(NAMES[m] + " & " + " & ".join(pc(d[a]["point"]) + " " + ci(d[a]) for a in ["main", "robust:c1", "robust:minimal", "robust:community"]) + r"\\")
    ins["S1_ROBUSTNESS"] = table(rows, "lllll", "Study 1: language-boundary leakage (repertoire only, pp) under three alternative system prompts. "
                                 "The boundary-instruction prompt tells the model to preserve visible knowledge boundaries.", "tab:s1rob", True)
    return ins


def added():
    """Tables for the experiments added on 10/6 (bridge, format ablation, sampling, Study 2 extension)."""
    ins = {}
    br = json.loads((ROOT / "analysis/results/added-1006/bridge.json").read_text())
    rep = json.loads((ROOT / "analysis/results/added-1006/bridge-replication.json").read_text())
    cols = [("base", "Base"), ("sys", "Sys."), ("card", "Sheet"), ("schema", "State"), ("ask", "Quest."), ("all", "All")]
    whole = lambda x: f"{100 * x:.0f}"

    def cell(m, k, acc="inaccessible"):  # bold when the paired interval for the change from base excludes zero
        v = m[f"{k}:{acc}"]
        lo, hi = v["delta_ci95"]
        s = whole(v["estimate"])
        return f"\\textbf{{{s}}}" if k != "base" and (lo > 0 or hi < 0) else s

    rows = [r"Model & " + " & ".join(c for _, c in cols) + r"\\", r"\midrule"]
    for m in ["gemma4_31b", "qwen38_27b", "falcon_h1_34b", "seed_oss_36b"]:
        rows.append(NAMES[m] + " & " + " & ".join(cell(br[m], k) for k, _ in cols) + r"\\")
        rows.append(r"\quad new scenes & " + " & ".join(cell(rep[m], k) for k, _ in cols) + r"\\")
    ins["BRIDGE_TABLE"] = table(rows, "lrrrrrr", "Net use of unheard speech (pp) when single Study 1 features are swapped into Study 2's hearing prompts, "
                                "on the discovery scenes and on the 96 confirmation scenes (new scenes). Bold marks a change from Base whose paired 95\\% interval excludes zero. "
                                "All 11 models are in Appendix Tables~\\ref{tab:bridgefull} and~\\ref{tab:bridgerep}.", "tab:bridge", False, tight=True)
    for key, data, label, scenes in (("BRIDGE_FULL", br, "tab:bridgefull", "discovery scenes (96 scenes, 384 prompts per swap)"),
                                     ("BRIDGE_REP", rep, "tab:bridgerep", "confirmation scenes, with each character renamed to a Study 1 persona (96 scenes, 384 prompts per swap)")):
        rows = [r"Model & " + " & ".join(c for _, c in cols) + r" & Audible use\\", r"\midrule"]
        for m in sorted(data, key=lambda m: data[m]["base:inaccessible"]["estimate"]):
            aud = [data[m][f"{k}:accessible"]["estimate"] for k, _ in cols]
            rows.append(NAMES[m] + " & " + " & ".join(cell(data[m], k) for k, _ in cols) + " & " + (whole(min(aud)) if whole(min(aud)) == whole(max(aud)) else f"{whole(min(aud))}--{whole(max(aud))}") + r"\\")
        ins[key] = table(rows, "lrrrrrrr", f"Bridge experiment on the {scenes}. Columns give net use of unheard speech (pp) under Study 2's prompt (Base), "
                         "with one Study 1 feature swapped in, and with all four. Bold marks a change from Base whose paired 95\\% skeleton-bootstrap interval "
                         "excludes zero. The last column is the range of target use for the same speech when audible (\\%).", label, True)
    hs = json.loads((ROOT / "analysis/results/added-1006/hosted_swaps.json").read_text())
    rows = [r"Model & " + " & ".join(c for _, c in cols) + r"\\", r"\midrule"]
    for m in ("sonnet55", "gemini31pro"):
        def hcell(k):
            if k not in hs[m]:
                return "--"
            v = hs[m][k]
            lo, hi = v["delta_ci95"]
            s = f"{100 * v['estimate']:.1f}"
            return f"\\textbf{{{s}}}" if k != "base" and (lo > 0 or hi < 0) else s
        rows.append(NAMES2[m] + " & " + " & ".join(hcell(k) for k, _ in cols) + r"\\")
    ins["HOSTED_SWAPS"] = table(rows, "lrrrrrr", "Single-feature swaps for two proprietary models on the discovery hearing prompts (192 unheard prompts per cell, net use in pp). "
                                "Bold marks a change from Base whose paired 95\\% interval excludes zero. Gemini 3.1 Pro was run on the two swaps that moved "
                                "the open-weight models most.", "tab:hostedswaps", tight=True)
    ab = json.loads((ROOT / "analysis/results/added-1006/ablation.json").read_text())
    combos = [("l0q0c0", "Study 1 prompt"), ("l1q0c0", "+ channel"), ("l0q1c0", "+ question"), ("l0q0c1", "+ minimal"), ("l1q1c1", "All three")]
    rows = [r"Model & " + " & ".join(c for _, c in combos) + r"\\", r"\midrule"]
    for cell, label in (("Einaud_S", "Not-audible flag"), ("C-T-_flag", "Not-understood flag")):
        rows.append(r"\multicolumn{6}{@{}l}{\emph{" + label + r"}}\\")
        for m in ["gemma4_31b", "qwen38_27b", "seed_oss_36b", "phi4"]:
            rows.append(NAMES[m] + " & " + " & ".join(pc(ab["cells"][m][k][cell]) for k, _ in combos) + r"\\")
    ins["ABLATION_TABLE"] = table(rows, "lrrrrr", "Format ablation from Study 1 toward Study 2 (96 skeletons, content question). Net use (pp) when one "
                                  "Study 2 feature is added (a field naming the channel, the direct question, a minimal context) and with all three.",
                                  "tab:ablation", True)
    ha = json.loads((ROOT / "analysis/results/added-1006/human-audit.json").read_text())
    rows = [r"Condition & $n$ & Human $D$ & Scorer $D$ & Precision & Recall\\", r"\midrule"]
    for st, v in ha["strata"].items():
        rows.append(esc(st.replace("S1 ", "Study 1, ").replace("S2 ", "Study 2, ").replace("M1g answer", "list-first answer")) + f" & {v['n']} & " + " & ".join(pc(v[k]) for k in ("D_human", "D_scorer", "target_precision", "target_recall")) + r"\\")
    ins["HUMAN_TABLE"] = table(rows, "lrrrrr", "Human audit, first sample (150 replies from both studies, one annotator who is not an author). $D$ is net use (pp) reweighted to each condition; precision and "
                               "recall are the scorer's for target use against the human labels, weighted the same way. Neither the annotator nor the scorer "
                               "found a foil use.", "tab:human", True)
    key = {json.loads(l)["audit_id"]: json.loads(l) for l in (ROOT / "analysis/study2-human-review/key.jsonl").read_text().splitlines() if l.strip()}
    with open(ROOT / "analysis/study2-human-review/content-labels.csv", encoding="utf-8-sig") as fh:
        labels = list(csv.DictReader(fh))

    def used(r, i):
        v = [r[f"use_set{i}_place"], r[f"use_set{i}_object"]]
        return 1 if "1" in v else (None if "U" in v else 0)
    cells = {}
    for r in labels:
        k = key[r["audit_id"]]
        t = k["target_candidate"]
        at, af = used(r, t), used(r, 3 - t)
        if at is None or af is None:
            continue
        c = cells.setdefault((k["boundary"], k["accessible"]), [0, 0, 0, 0])
        c[0] += 1
        c[1] += at - af
        c[2] += k["machine_target"] - k["machine_foil"]
        c[3] += at == k["machine_target"]
    rows = [r"Channel & Access & $n$ & Author $D$ & Scorer $D$ & Target agreement\\", r"\midrule"]
    for ch in ("Hear", "Understand", "See", "Receive"):
        for acc in (False, True):
            n, ad, sd, ag = cells[(ch, acc)]
            rows.append(f"{ch} & {'yes' if acc else 'no'} & {n} & {100 * ad / n:.1f} & {100 * sd / n:.1f} & {ag}/{n}" + r"\\")
    ins["HUMAN2_TABLE"] = table(rows, "llrrrr", "Human audit, second sample (640 Study~2 replies, labeled by one of the authors). $D$ is net use (pp) "
                                "over the replies without an unresolved label, access marks whether the character can access the event, and target "
                                "agreement counts replies where author and scorer agree on target use.", "tab:human2", True)
    ho = json.loads((ROOT / "analysis/results/added-1006/hosted.json").read_text())
    rows = [r"Model & Repertoire & Audibility & Compr. & Prose & Control & State & Transl. & Bridge\\",
            r"& flag & flag & flag & sentence & use & probe & probe & base $\to$ all\\", r"\midrule"]
    f = lambda x: "n.r." if x is None else pc(x)
    for m in ["gpt6sol", "opus55", "sonnet55", "gemini31pro", "gemini38flash", "grok47", "deepseekv4pro"]:
        s1, br = ho[m]["study1"], ho[m]["bridge"]
        rows.append(NAMES2[m] + " & " + " & ".join(f(s1[k]) for k in ("repertoire", "inaudible_flag", "understood_flag", "prose", "fluent_control_use",
                    "state_probe_correct", "translation_both_canaries")) + f" & {f(br['base']['unheard_net'])} $\\to$ {f(br['all']['unheard_net'])}" + r"\\")
    ins["HOSTED_TABLE"] = table(rows, "lrrrrrrrr", "Proprietary models and DeepSeek-V4-Pro on Study 1 core conditions (content question, 288 items per cell) and on both ends "
                                "of the bridge. Leakage is net use in pp, control use and probes are percentages.", "tab:hosted", True)
    hc = json.loads((ROOT / "analysis/results/added-1006/hosted_ci.json").read_text())
    cells = [("repertoire", "Repertoire"), ("inaudible_flag", "Audibility flag"), ("understood_flag", "Compr. flag"), ("prose", "Prose sentence")]
    rows = [r"Model & " + " & ".join(c for _, c in cells) + r"\\", r"\midrule"]
    cell = lambda v: f"{pc(v['estimate'])} [{pc(v['ci95'][0])}, {pc(v['ci95'][1])}]"
    for m in ["gpt6sol", "opus55", "sonnet55", "gemini31pro", "gemini38flash", "grok47", "deepseekv4pro"]:
        rows.append(NAMES2[m] + " & " + " & ".join(cell(hc[m][k]) for k, _ in cells) + r"\\")
    rows.append(r"\midrule")
    rows.append("Claude Opus 5.5, complete replies only & " + " & ".join(cell(hc["opus55"].get(k + "_complete_only", hc["opus55"][k])) for k, _ in cells) + r"\\")
    ins["HOSTED_CI"] = table(rows, "lrrrr", "Proprietary models and DeepSeek-V4-Pro on the Study 1 core cells, with net use (pp) and 95\\% intervals from 2,000 skeleton-bootstrap draws "
                             "(288 items, 576 replies per cell). The last row drops the replies that Anthropic's content filter withheld.", "tab:hostedci", True)
    ext = json.loads((ROOT / "analysis/results/added-1006/v2-extension.json").read_text())
    chans = ["Hear", "Understand", "See", "Receive"]
    per = ext["per_model_full_context"]
    core = {"gemma4_31b", "glm47_flash", "nemotron3_nano30b", "qwen35_9b"}
    order = sorted(per, key=lambda m: sum(per[m].values()))
    rows = [r"Model & Hear & Understand & See & Receive\\", r"\midrule"]
    for m in order:
        rows.append(NAMES[m] + (r"$^\ast$" if m in core else "") + " & " + " & ".join(pc(per[m][c]) for c in chans) + r"\\")
    rows.append(r"\midrule")
    for key, label in (("all_eleven", "All 11 models"), ("added", "7 added models")):
        h = ext[key]["H1_components"]
        rows.append(label + " & " + " & ".join(pc(h[c]["estimate"]) for c in chans) + r"\\")
    ins["S2_EXT_TABLE"] = table(rows, "lrrrr", "Study 2 confirmation set (96 original-character scenes), net use of inaccessible content under full "
                                "context (pp). $^\\ast$Locked four-model cohort.", "tab:s2ext", tight=True)
    return ins


def study2():
    ren = [("H1: ", "Channel, "), ("H2: State-correct", "State-correct"), ("H3: Full", "View, full"), ("H3: ", "View, "), ("H1 is the conjunction", "The channel test is the conjunction"), ("H3 combines", "the view test combines"), ("H2 includes", "The state-correct test includes"), ("for C001, Qwen3.5-9B, R2, delay zero", "for scene C001, Qwen3.5-9B, access flag, no delay"), ("in the four-core subset.", "across the four core models."), ("Independent probe prefix &", "Probe prefix &"), ("Independent probe user &", "Probe question &"), ("Replace \\texttt{The glove is in the church.} with \\texttt{The broom is in the stairwell.}", "\\texttt{The glove is in the church.} $\\rightarrow$ \\texttt{The broom is in the stairwell.}"), ("Replace \\texttt{audible\\_to\\_Mira Sen}: \\texttt{false} with \\texttt{true}.", "\\texttt{audible\\_to\\_Mira Sen}: \\texttt{false} $\\rightarrow$ \\texttt{true}")]
    labels = {"S2_ACCESS": "tab:accesscases", "S2_CONFIRM": "tab:confirm", "S2_HEATMAP": "fig:discoveryheatmap", "S2_METHODS": "tab:methods",
              "S2_BEHAVIOR": "fig:behavior", "S2_REPRESENTATION": "tab:representation", "S2_DISCMETHODS": "tab:discoverymethods",
              "S2_DELAY": "tab:delay", "S2_DECISION": "tab:decision", "S2_CHOICEORDER": "tab:choiceorder", "S2_TRANSLATE": "tab:translate",
              "S2_STATEBOUNDARY": "tab:stateboundary", "S2_PROBES": "tab:probecontrols", "S2_CASEIN": "tab:caseinput",
              "S2_CASEOUT": "tab:caseoutput", "S2_MODELDETAIL": "tab:modeldetail", "S2_ROSTER": "tab:roster"}
    return {k: v2_float(v, ren) for k, v in labels.items()}


PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[review]{acl}
\usepackage{times,latexsym}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{microtype,booktabs,amsmath,amssymb,tabularx}
\usepackage{tikz,pgfplots,fontawesome5}
\pgfplotsset{compat=1.18}
\usetikzlibrary{plotmarks,arrows.meta,calc,positioning,shapes.callouts,backgrounds,fit}
\pgfsetplotmarksize{1.7pt}
\tikzset{every picture/.append style={font=\sffamily\scriptsize},
  card/.style={rounded corners=2pt,draw=black!18,fill=black!2,inner sep=3pt,align=left},
  chip/.style={rounded corners=1.5pt,inner sep=1.5pt,font=\sffamily\tiny\bfseries,text=white},
  panel/.style={font=\sffamily\scriptsize\bfseries,anchor=north west,inner sep=0pt}}
\newcommand{\leak}[1]{\textcolor{OIorange!85!black}{\textbf{#1}}}
\setcounter{topnumber}{3}\setcounter{bottomnumber}{2}\setcounter{totalnumber}{5}\setcounter{dbltopnumber}{2}
\renewcommand{\topfraction}{0.9}\renewcommand{\bottomfraction}{0.6}\renewcommand{\textfraction}{0.08}
\renewcommand{\floatpagefraction}{0.75}\renewcommand{\dbltopfraction}{0.9}\renewcommand{\dblfloatpagefraction}{0.75}
\usepackage{placeins,adjustbox,float}
% Included PDFs carry no file paths into the output (anonymous review).
\pdfsuppressptexinfo=-1
% Avoid paragraphs whose last line holds a single word: the last line must fill about a third of the column.
\setlength{\parfillskip}{0pt plus 0.65\columnwidth}\setlength{\emergencystretch}{2em}
% A paragraph never leaves one or two of its lines at the top of a column or page, nor one at the bottom.
\widowpenalties 3 10000 10000 0 \clubpenalty=10000
\DeclareCaptionJustification{fullfill}{\setlength{\parfillskip}{0pt plus 0.65\linewidth}\setlength{\emergencystretch}{1.5em}}
\captionsetup{justification=fullfill}
\makeatletter\let\OCthebib\thebibliography\def\thebibliography#1{\OCthebib{#1}\emergencystretch=4em\parfillskip=0pt plus 0.15\columnwidth\relax}\makeatother
\newsavebox{\OCtable}
\newsavebox{\OCfigure}
\definecolor{OCblue}{HTML}{5B7FAF}
\definecolor{OCorange}{HTML}{D2876C}
\definecolor{OCgreen}{HTML}{68A595}
\definecolor{OCpurple}{HTML}{B497B6}
\definecolor{OCred}{HTML}{B5635A}
\hypersetup{pdfauthor={Anonymous},pdftitle={Language Models Give Characters Knowledge They Cannot Have}}
"""


# Appendix captions written as sentences rather than with semicolons.
CAPTION_SENTENCES = [
    ("net canary-use points; state correctness is a percentage", "net canary-use points, and state correctness is a percentage"),
    ("times two versions; all 6,144 outputs are valid", "times two versions, and all 6,144 outputs are valid"),
    ("applies only to comprehension; all of its state probes are correct", "applies only to comprehension, where all state probes are correct"),
    ("threshold is 85\\%; the primary analysis is unconditional", "threshold is 85\\%, and the primary analysis is unconditional"),
    ("Leakage is net pp; accessible use is a percentage", "Leakage is net pp and accessible use is a percentage"),
    ("Leakage is net $D$ in pp; accessible target use", "Leakage is net $D$ in pp, and accessible target use"),
    ("neutral exchanges; (b) change from zero exchanges under full context; (c) change", "neutral exchanges. (b) Change from zero exchanges under full context. (c) Change"),
    ("within each stratum; original paired effects", "within each stratum. Original paired effects"),
    ("in all four rows; inaccessible view scores", "in all four rows, inaccessible view scores"),
    ("reweighted to each condition; precision and recall", "reweighted to each condition. Precision and recall"),
]


def _bold_cells(line):
    """Bold every cell of a header row, keeping \multicolumn as the cell's first token."""
    end = line.rstrip()
    tail = ""
    if end.endswith("\\\\"):
        end, tail = end[:-2], "\\\\"
    cells = re.split(r"(?<!\\)&", end)
    out = []
    for c in cells:
        t = c.strip()
        if not t:
            out.append(c)
        elif t.startswith("\\multicolumn"):
            m = re.match(r"(\\multicolumn\{[^}]*\}\{[^}]*\})\{(.*)\}$", t)
            out.append(f" {m.group(1)}{{\\textbf{{{m.group(2)}}}}} " if m else c)
        else:
            out.append(f" \\textbf{{{t}}} ")
    return "&".join(out).strip() + tail


def table_widths(body):
    """Natural width (pt) of every tabular, measured once with pdflatex and cached by content."""
    import hashlib
    import subprocess
    import tempfile
    cache_path = P / "table_widths.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    tabs = {}
    for m in re.finditer(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", body, re.S):
        t = m.group(0)
        lab = re.search(r"\\label\{([^}]*)\}", t)
        tab = re.search(r"\\begin\{tabular\}.*?\\end\{tabular\}", t, re.S)
        if lab and tab:
            tabs[lab.group(1)] = (hashlib.sha1(tab.group(0).encode()).hexdigest(), tab.group(0))
    todo = {k: v for k, v in tabs.items() if cache.get(k, {}).get("sha") != v[0]}
    if todo:
        doc = PREAMBLE + "\\begin{document}\n" + "".join(
            f"\\sbox0{{\\sffamily\\footnotesize\\setlength{{\\tabcolsep}}{{3.5pt}}\\renewcommand{{\\arraystretch}}{{1.12}}{tab}}}\\typeout{{TW {k} \\the\\wd0}}\n" for k, (_, tab) in todo.items()) + "\\end{document}\n"
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "w.tex").write_text(doc)
            (Path(d) / "acl.sty").write_bytes((P / "acl.sty").read_bytes())
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "w.tex"], cwd=d, capture_output=True)
            for k, w in re.findall(r"^TW (\S+) ([\d.]+)pt", (Path(d) / "w.log").read_text(errors="ignore"), re.M):
                cache[k] = {"sha": todo[k][0], "pt": float(w)}
        cache_path.write_text(json.dumps(cache, indent=1, sort_keys=True))
    return {k: cache[k]["pt"] for k in tabs if k in cache}


def style_tables(body, widths=None):
    """One look for every table: sans-serif footnote size, bold header, one decimal, a little more row height."""
    app = body.find("\\appendix")

    def one(m):
        t = m.group(0)
        lab = re.search(r"\\label\{([^}]*)\}", t)
        if m.start() < app:  # main-text tables keep the layout chosen for them
            lab = None
        elif "tabcolsep" not in t:
            t = t.replace("\\centering", "\\centering\\setlength{\\tabcolsep}{4.5pt}", 1)
        t = re.sub(r"\\centering\\(small|footnotesize)", r"\\centering\\sffamily\\footnotesize\\renewcommand{\\arraystretch}{1.12}", t, count=1)
        if "\\toprule" in t and "\\midrule" in t:
            a = t.index("\\toprule") + len("\\toprule")
            b = t.index("\\midrule", a)
            head = "\n".join(_bold_cells(l) if l.strip() else l for l in t[a:b].split("\n"))
            rest = t[b:]
            if "ttfamily" not in rest:
                rest = re.sub(r"(?<![\d.])(-?\d+)\.(\d{2})(?![\d])", lambda x: str(Decimal(x.group(0)).quantize(Decimal("0.1"), ROUND_HALF_UP)), rest.split("\\bottomrule")[0]) + "\\bottomrule" + rest.split("\\bottomrule", 1)[1]
            t = t[:a] + head + rest
        return t
    return re.sub(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", one, body, flags=re.S)


def onecolumn_appendix(body, pairs=(("tab:translate", "tab:representation"),)):
    """The appendix is set in one column: every float there becomes a here-or-top float of the page width, and
    each pair of narrow tables shares one float side by side."""
    i = body.find("\\appendix")
    if i < 0:
        return body
    head, app = body[:i], body[i:]
    app = re.sub(r"\\begin\{(table|figure)\*?\}\[[^\]]*\]", lambda m: f"\\begin{{{m.group(1)}}}[!htbp]", app)
    app = re.sub(r"\\end\{(table|figure)\*\}", lambda m: f"\\end{{{m.group(1)}}}", app)
    for a, b in pairs:
        blocks = []
        for lab in (a, b):
            m = re.search(r"\\begin\{table\}\[!htbp\]((?:(?!\\begin\{table\}).)*?\\label\{" + re.escape(lab) + r"\}.*?)\\end\{table\}", app, re.S)
            if not m:
                break
            inner = m.group(1)
            inner = re.sub(r"\\ifdim\\wd\\OCtable>\\linewidth\\PackageError\{[^}]*\}\{[^}]*\}\{[^}]*\}\\fi\n?", "", inner)
            inner = inner.replace("\\usebox{\\OCtable}", "\\adjustbox{max width=\\linewidth}{\\usebox{\\OCtable}}")
            inner = re.sub(r"(\\begin\{tabular\}.*?\\end\{tabular\})", r"\\adjustbox{max width=\\linewidth}{\1}", inner, flags=re.S) if "OCtable" not in inner else inner
            blocks.append((m.group(0), inner))
        if len(blocks) != 2:
            continue
        pair = ("\\begin{table}[!htbp]\n\\begin{minipage}[t]{0.47\\linewidth}" + blocks[0][1] + "\\end{minipage}\\hfill\n"
                "\\begin{minipage}[t]{0.47\\linewidth}" + blocks[1][1] + "\\end{minipage}\n\\end{table}")
        app = app.replace(blocks[0][0], pair, 1).replace(blocks[1][0], "", 1)
    # Every appendix table spans its full column, so tables, captions and text share the same edges.
    def full_width(m):
        spec = m.group(1)
        spec = "@{\\extracolsep{\\fill}}" + (spec[3:] if spec.startswith("@{}") else spec)
        return "\\begin{tabular*}{\\linewidth}{" + spec + "}" + m.group(2) + "\\end{tabular*}"
    app = re.sub(r"\\begin\{tabular\}\{((?:[^{}]|\{[^{}]*\})*)\}(.*?)\\end\{tabular\}", full_width, app, flags=re.S)
    # Appendix floats stay where they are written, so each page fills in order and no page holds floats alone.
    app = app.replace("}[!htbp]", "}[H]")
    return head + app


def twocolumn_appendix(body, pairs=(("tab:translate", "tab:representation"),)):
    """The appendix keeps the paper's two columns. Every table and figure spans both columns at full width, so they
    pack together on float pages, and each pair of narrow tables shares one float side by side."""
    i = body.find("\\appendix")
    if i < 0:
        return body
    head, app = body[:i], body[i:]
    app = app.replace("\\FloatBarrier\n", "")

    def full(m):
        spec = m.group(1)
        spec = "@{\\extracolsep{\\fill}}" + (spec[3:] if spec.startswith("@{}") else spec)
        return "\\begin{tabular*}{\\linewidth}{" + spec + "}" + m.group(2) + "\\end{tabular*}"

    paired = {lab for p in pairs for lab in p}

    def one(m):
        kind, t = m.group(1), m.group(0)
        t = re.sub(r"\\begin\{%s\*?\}\[[^\]]*\]" % kind, lambda _: "\\begin{%s*}[!tp]" % kind, t)
        t = re.sub(r"\\end\{%s\*?\}" % kind, lambda _: "\\end{%s*}" % kind, t)
        lab = re.search(r"\\label\{([^}]*)\}", t)
        if kind == "table" and not (lab and lab.group(1) in paired):  # stretch to the full text width
            t = re.sub(r"\\begin\{tabular\}\{((?:[^{}]|\{[^{}]*\})*)\}(.*?)\\end\{tabular\}", full, t, flags=re.S)
        return t
    app = re.sub(r"\\begin\{(table|figure)\*?\}.*?\\end\{\1\*?\}", one, app, flags=re.S)
    for a, c in pairs:
        blocks = []
        for lab in (a, c):
            m = re.search(r"\\begin\{table\*\}\[!tp\]((?:(?!\\begin\{table).)*?\\label\{" + re.escape(lab) + r"\}.*?)\\end\{table\*\}", app, re.S)
            if not m:
                break
            inner = re.sub(r"\\ifdim\\wd\\OCtable>\\linewidth\\PackageError\{[^}]*\}\{[^}]*\}\{[^}]*\}\\fi\n?", "", m.group(1))
            if "OCtable" in inner:
                inner = inner.replace("\\usebox{\\OCtable}", "\\adjustbox{max width=\\linewidth}{\\usebox{\\OCtable}}")
            else:
                inner = re.sub(r"(\\begin\{tabular\}.*?\\end\{tabular\})", lambda x: "\\adjustbox{max width=\\linewidth}{" + x.group(1) + "}", inner, flags=re.S)
            blocks.append((m.group(0), inner))
        if len(blocks) == 2:
            pair = ("\\begin{table*}[!tp]\n\\begin{minipage}[t]{0.47\\linewidth}" + blocks[0][1] + "\\end{minipage}\\hfill\n"
                    "\\begin{minipage}[t]{0.47\\linewidth}" + blocks[1][1] + "\\end{minipage}\n\\end{table*}")
            app = app.replace(blocks[0][0], pair, 1).replace(blocks[1][0], "", 1)
    return head + app


# Rewordings that keep table cells and captions from ending on a single word.
LATE_FIXES = ((r"\textbf{Version} & \textbf{Access} & \textbf{Probe}", r"\textbf{Twin} & \textbf{Access} & \textbf{Probe}"),
              # One term per concept (net use, permitted use) and no internal process detail.
              ("Leakage is net use in pp, control use and probes are percentages.", "Net use is in pp, and permitted use and probes are percentages."),
              ("Study 1: language-boundary leakage (repertoire only, pp)", "Net use in Study 1 under the language boundary (repertoire only, pp)"),
              ("View, full minus view leakage &", "View, full minus view net use &"),
              ("requires the view to reduce leakage, keep accessible use within 5 pp", "requires the view to reduce net use, keep permitted use within 5 pp"),
              ("Five methods in the complete prespecified six-model discovery cohort on 48 matched scenes", "Five methods on six discovery models and 48 matched scenes"),
              ("Leakage is net pp and accessible use is a percentage.", "Net use is in pp and permitted use is a percentage."),
              (r"\textbf{Method} & \textbf{Leakage} & \textbf{Access. use}", r"\textbf{Method} & \textbf{Net use} & \textbf{Permitted use}"),
              ("four equally sized channels; always No gives", "four equally sized channels, and always answering No gives"),
              ("State-correct boundary decomposition in the four-model confirmation. Values are pp. The .85 gate applies only to comprehension, where all state probes are correct. Eligibility is fixed from translation results, and model-specific ratios are recomputed over the original 96-scene bootstrap.",
               "State-correct net use for the four models of Section~\\ref{sec:s2} (pp). The capability-eligible column keeps only model and language units whose translation probe reaches 85\\%, which changes only comprehension."),
              ("Representation effects on inaccessible net use (pp), with 95\\% intervals. Eleven completed discovery models, 24 matched scenes. The same comprehension prose contrast is +5.73 [0.00, 11.98] across the four core models.",
               "Representation effects on net use (pp), with 95\\% intervals. Eleven discovery models, 24 matched scenes. The same comprehension prose contrast is +5.7 [0.0, 12.0] across the four core models."),
              (" Original paired effects and tests remain unchanged.", ""),
              ("Both-canary translation use on 64 original-character prompts per model--language unit (\\%). The diagnostic threshold is 85\\%, and the primary analysis is unconditional.",
               "Translation probe accuracy (\\%), the share of 64 prompts per model and language in which both hidden values are translated. Main estimates use all units, and the capability-eligible estimates of Table~\\ref{tab:stateboundary} drop units below 85\\%."),
              ("Confirmation cohort. Leakage is net $D$ in pp, and accessible target use and partial-event retention are percentages. Retention excludes Hear. Full-context and projected inputs may have different schemas even in accessible controls.",
               "Confirmation set. Net use $D$ is in pp, and permitted use and partial-event retention are percentages. Retention excludes Hear."))


def late_fixes(body):
    for x, y in LATE_FIXES:
        assert x in body, x
        body = body.replace(x, y)
    return body


def main():
    body = (P / "body.tex").read_text(encoding="utf-8")
    sys.path.insert(0, str(P))
    import figures
    ins = {**study1(), **study2(), **added(), **{k: f() for k, f in figures.ALL.items()}}
    for k, v in ins.items():
        body = body.replace(f"% INSERT {k}\n", v + "\n")
    left = re.findall(r"^% INSERT (\w+)$", body, re.M)
    assert not left, f"unfilled markers: {left}"
    assert "HumanField" not in body
    for x, y in CAPTION_SENTENCES:  # entries whose float is no longer inserted are skipped
        body = body.replace(x, y)
    body = twocolumn_appendix(style_tables(body))
    body = late_fixes(body)
    (P / "main.tex").write_text(PREAMBLE + figures.COLORS + "\n" + body, encoding="utf-8")
    print("wrote main.tex;", len(ins), "insertable floats,", body.count("\\cite"), "cite commands")


if __name__ == "__main__":
    main()

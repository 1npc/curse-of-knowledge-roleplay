"""Assemble the two-study ARR manuscript (standard library only; formatting, no statistics).

Study 1 tables and figures are generated from analysis/results/main-20260929 (code adapted from
the archived two-boundary draft, paper/arr/archive/pre-access-v2-source.zip). Study 2 floats are
copied verbatim from the access-v2 manuscript paper/arr/main.tex by their labels, so their numbers
stay exactly those of the frozen access-v2 analysis. The prose lives in body.tex; markers of the
form `% INSERT name` are replaced here. Output: main.tex (compile with latexmk -pdf main.tex).
Usage: python3 paper/arr-v3/build.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
R1 = ROOT / "analysis/results/main-20260929"
V2 = (ROOT / "paper/arr/main.tex").read_text(encoding="utf-8")
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
    return "\n".join([f"\\begin{{{env}}}[t]", r"\centering\footnotesize\setlength{\tabcolsep}{3.5pt}" if tight else r"\centering\small", r"\begin{tabular}{@{}" + cols + r"@{}}", r"\toprule", *rows,
                      r"\bottomrule", r"\end{tabular}", r"\caption{" + caption + "}", r"\label{" + label + "}", f"\\end{{{env}}}"])


CAPTIONS = {
    "tab:accesscases": "Study 2 channels. Each event contains an item--location fact. The character view replaces an inaccessible event by the observation in the last column; accessible controls keep the full event.",
    "fig:discoveryheatmap": "Study 2 discovery: 11 models, 96 scenes, direct Boolean (R2). (a) Net use of inaccessible content (pp); (b) use of the same content when it is accessible (\\%); (c) means over channels. Dots mark the four confirmation models.",
    "fig:behavior": "Study 2, four confirmation models, 32 scenes. (a) Net use after zero, two or four neutral exchanges; (b) change from zero exchanges under full context; (c) change in choosing location A when the inaccessible fact switches from B to A. Bars are 95\\% skeleton-bootstrap intervals.",
    "tab:confirm": "Study 2 confirmation (four models, 96 original-character scenes). C1 requires all four channels to be positive, C2 uses replies whose state probe is correct (6,068), and C3 requires the view to reduce leakage, keep accessible use within 5 pp, and keep more observations than removal. One Holm-adjusted $p$ per family.",
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
    desc = {"H1": "Not understood: repertoire only", "H1i": "Not audible: flag only", "H2a": "Repertoire $-$ repertoire + sentence",
            "H2b": "Audible flag $-$ flag + narration", "H3": "Repertoire $-$ understood flag",
            "H4": "Audible flag $-$ understood flag", "H5a": "Repertoire, probe answered correctly"}
    rows = [r"Test & Statistic & Estimate & 95\% CI & Holm $p$\\", r"\midrule"]
    for k, label in desc.items():
        r = conf[k]
        rows.append(f"{k} & {label} & {pc(r['point'])} & {ci(r)} & {r['p_holm']:.3f}" + r"\\")
    rows.append(r"\midrule")
    for key, label in [("reduction", "M1g: mean relative reduction (\\%)"), ("retention", "M1g: change in translator-enabled use")]:
        r = conf["H5b"][key]
        rows.append(f"H5b & {label} & {pc(r['point'])} & {ci(r)} & " + (f"{conf['H5b']['p_holm']:.3f}" if key == "reduction" else "joint") + r"\\")
    ins["S1_TABLE"] = table(rows, "llrrr", "Study 1 confirmatory family (11 models, 33 model--language units; estimates in pp unless noted). "
                            "Tests are one-sided against the locked thresholds (H1, H1i, H5a: 10 pp; others: 0; H5b: reduction $\\geq$ 50\\% and "
                            "change $\\geq -5$ pp), Holm-corrected over eight tests; 0.004 is the resolution of 2,000 bootstrap draws.", "tab:s1", True)
    rows = [r"& \multicolumn{2}{c}{Not understood} & \multicolumn{2}{c}{Not audible} & Transl.\\",
            r"Model & Base & M1g & Base & M1g & (pp)\\", r"\midrule"]
    for r in models:
        rows.append(NAMES[r["model"]] + " & " + " & ".join(pc(r[k]["point"]) for k in
                    ["base_language", "m1g_language", "base_inaudible", "m1g_inaudible", "retention"]) + r"\\")
    ins["S1_MITIGATION"] = table(rows, "lrrrrr", "Study 1, M1g by model (content and planning questions). Leakage is net use in pp; the last "
                                 "column is the change in target use when a working translator makes the content accessible.", "tab:s1m", tight=True)
    rows = [r"Model & \multicolumn{2}{c}{Step-1 list names target (\%)} & Translator use change\\",
            r"& Not understood & Not audible & (pp) [95\% CI]\\", r"\midrule"]
    for r in models:
        rows.append(NAMES[r["model"]] + " & " + pc(r["step1_language"]["point"]) + " & " + pc(r["step1_inaudible"]["point"]) +
                    " & " + pc(r["retention"]["point"]) + " " + ci(r["retention"]) + r"\\")
    ins["S1_STEP1"] = table(rows, "lrrl", "Study 1: target use in the M1g step-1 perception list, which predicts where the filter fails.", "tab:s1step1", True)
    labels = {"unconditional": "Unconditional (no capability filter)", "soft": "Soft hedge credit", "exclude_truncated": "Exclude truncated",
              "exclude_flagged": "Exclude language/echo flags", "complete_only": "Complete responses only",
              "worst_failed_mitigation": "Worst-case failed M1g", "u2": "Both canaries required"}
    rows = [r"Variant & Not underst. & Not audible & Reduction (\%) & Translator (pp) & Supported\\", r"\midrule"]
    for k, v in load("sensitivities.json").items():
        rows.append(labels[k] + " & " + " & ".join([pc(v["H1"]["point"]), pc(v["H1i"]["point"]), pc(v["H5b"]["reduction"]["point"]),
                                                     pc(v["H5b"]["retention"]["point"]), f"{sum(x['supported'] for x in v.values())}/8"]) + r"\\")
    ins["S1_SENSITIVITY"] = table(rows, "lrrrrc", "Study 1 scoring and conditioning sensitivities.", "tab:s1sens", True)
    rows = [r"Subset & Reduction (\%) & Translator (pp) & H5b $p$\\", r"\midrule"]
    sets = list(load("by_language_confirmatory.json").items()) + [("Without " + k, v) for k, v in load("leave_one_character_out.json").items()] + \
        [("Two-way bootstrap", load("two_way_bootstrap.json")["tests"])]
    for name, v in sets:
        h = v["H5b"]
        rows.append(esc(name) + " & " + pc(h["reduction"]["point"]) + " & " + pc(h["retention"]["point"]) + " & " + f"{h['p_holm']:.3f}" + r"\\")
    ins["S1_SUBGROUPS"] = table(rows, "lrrr", "Study 1: H5b by language, leaving one character out, and with a two-way (skeleton $\\times$ "
                                "character) bootstrap. The joint criterion fails in several subsets.", "tab:s1sub", tight=True)
    el = {"deny_while_using": "Denial with use (C$-$T$-$ D1)", "unattributed_share_D1_minus_U": "Unattributed-use share: D1 $-$ U",
          "offline_translator": "Offline $-$ absent translator", "original_confounded_boundary": "Original unmatched contrast (C$-$T$-$ $-$ narrated)",
          "FS_language_reduction": "Few-shot reduction (4 models)", "mode_DA_minus_OH": "Direct address $-$ overheard",
          "spoken_minus_real": "Spoken-only $-$ full state", "language_zh_minus_ja": "zh $-$ ja", "language_zh_minus_es": "zh $-$ es",
          "language_ja_minus_es": "ja $-$ es", "admission_A_D1_minus_U": "Explicit admission: D1 $-$ U",
          "admission_admission_with_attribution_D1_minus_U": "Admission incl. attribution: D1 $-$ U",
          "canon_canon_C+_D0_minus_U": "Canon C+: D0 $-$ U", "canon_canon_weak_C-_D0_minus_U": "Canon weak C$-$: D0 $-$ U",
          "canon_name_prior_C-_D0_minus_U": "Name prior C$-$: D0 $-$ U", "non_cyberpunk_minus_main": "Present-day world $-$ main set"}
    rows = [r"Exploratory contrast & Estimate (pp) & 95\% CI & BH $q$\\", r"\midrule"]
    for k, v in load("exploratory.json").items():
        rows.append(el.get(k, esc(k)) + " & " + pc(v["point"]) + " & " + ci(v) + " & " + f"{v['q_bh']:.3f}" + r"\\")
    ins["S1_EXPLORATORY"] = table(rows, "lrrr", "Study 1 exploratory family (Benjamini--Hochberg, $q=.10$). The world comparison uses "
                                  "different scenario sets.", "tab:s1expl", True)
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
    cols = [("base", "Study 2 prompt"), ("sys", "+ S1 system"), ("card", "+ S1 sheet"), ("schema", "+ S1 state"), ("ask", "+ S1 question"), ("all", "All four")]
    rows = [r"Model & " + " & ".join(c for _, c in cols) + r"\\", r"\midrule"]
    for m in ["gemma4_31b", "qwen38_27b", "phi4"]:
        rows.append(NAMES[m] + " & " + " & ".join(pc(br[m][f"{k}:inaccessible"]["estimate"]) for k, _ in cols) + r"\\")
    rows.append(r"\midrule")
    for m in ["gemma4_31b", "qwen38_27b", "phi4"]:
        rows.append(NAMES[m] + " (heard) & " + " & ".join(pc(br[m][f"{k}:accessible"]["estimate"]) for k, _ in cols) + r"\\")
    ins["BRIDGE_TABLE"] = table(rows, "lrrrrrr", "Bridge experiment on Study 2's hearing prompts (96 scenes). Each column swaps in one Study 1 feature; "
                                "the last swaps in all four. Top: net use of unheard speech (pp); bottom: use of the same speech when audible (\\%).", "tab:bridge", True)
    ab = json.loads((ROOT / "analysis/results/added-1006/ablation.json").read_text())
    combos = [("l0q0c0", "Study 1 prompt"), ("l1q0c0", "+ channel"), ("l0q1c0", "+ question"), ("l0q0c1", "+ minimal"), ("l1q1c1", "All three")]
    rows = [r"Model & " + " & ".join(c for _, c in combos) + r"\\", r"\midrule"]
    for cell, label in (("Einaud_S", "not audible"), ("C-T-_flag", "not understood")):
        rows.append(r"\multicolumn{6}{@{}l}{\emph{Flag: " + label + r"}}\\")
        for m in ["gemma4_31b", "qwen38_27b", "seed_oss_36b", "phi4"]:
            rows.append(NAMES[m] + " & " + " & ".join(pc(ab["cells"][m][k][cell]) for k, _ in combos) + r"\\")
    ins["ABLATION_TABLE"] = table(rows, "lrrrrr", "Format ablation from Study 1 toward Study 2 (96 skeletons, content question): net use (pp) when one "
                                  "Study 2 feature is added (a field naming the channel, the direct question, a minimal context) and with all three.",
                                  "tab:ablation", True)
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
    ren = [("H1: ", "C1: "), ("H2: ", "C2: "), ("H3: ", "C3: "), ("H1 is", "C1 is"), ("H3 combines", "C3 combines"), ("H2 includes", "C2 includes")]
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
\usepackage{tikz}
\usepackage{placeins}
\newsavebox{\OCtable}
\newsavebox{\OCfigure}
\definecolor{OCblue}{HTML}{0072B2}
\definecolor{OCorange}{HTML}{D55E00}
\definecolor{OCgreen}{HTML}{009E73}
\definecolor{OCpurple}{HTML}{CC79A7}
\definecolor{OCred}{HTML}{A6192E}
\hypersetup{pdfauthor={Anonymous},pdftitle={Role-Playing Language Models Use Information Their Characters Cannot Access}}
"""


def main():
    body = (P / "body.tex").read_text(encoding="utf-8")
    ins = {**study1(), **study2(), **added()}
    for k, v in ins.items():
        body = body.replace(f"% INSERT {k}\n", v + "\n")
    left = re.findall(r"^% INSERT (\w+)$", body, re.M)
    assert not left, f"unfilled markers: {left}"
    assert "HumanField" not in body
    (P / "main.tex").write_text(PREAMBLE + body, encoding="utf-8")
    print("wrote main.tex;", len(ins), "insertable floats,", body.count("\\cite"), "cite commands")


if __name__ == "__main__":
    main()

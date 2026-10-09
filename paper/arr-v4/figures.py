"""TikZ figures for the manuscript, generated from saved results (standard library only).

Every number drawn here is read from a results file; nothing is typed by hand except labels. All panels
share frame() for axes, legend() for keys and heat() for heatmap cells. Colors follow Okabe-Ito: orange =
hidden content or leakage, blue = cannot understand or permitted content, green = remedies and the
character view, gray = controls.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R1 = ROOT / "analysis/results/main-20260929"
RA = ROOT / "analysis/results/added-1006"
NAMES = {"qwen38_27b": "Qwen3.8-27B", "qwen35_9b": "Qwen3.5-9B", "gemma4_31b": "Gemma-4-31B", "gemma4_12b": "Gemma-4-12B",
         "glm47_flash": "GLM-4.7-Flash", "mistral_small3": "Mistral-Small-24B", "gpt_oss_20b": "gpt-oss-20b", "phi4": "Phi-4",
         "seed_oss_36b": "Seed-OSS-36B", "nemotron3_nano30b": "Nemotron-3-Nano", "falcon_h1_34b": "Falcon-H1-34B",
         "deepseekv4pro": "DeepSeek-V4-Pro", "gpt6sol": "GPT-6 Sol", "opus55": "Claude Opus 5.5", "sonnet55": "Claude Sonnet 5.5",
         "gemini31pro": "Gemini 3.1 Pro", "gemini38flash": "Gemini 3.8 Flash", "grok47": "Grok 4.7"}
# Muted palette in the style of Nature figures: terracotta for hidden content and leakage, steel blue for
# comprehension and permitted content, sage teal for remedies, with light blue, mauve and gray as accents.
COLORS = r"""\definecolor{OIblue}{HTML}{5B7FAF}\definecolor{OIorange}{HTML}{D2876C}\definecolor{OIgreen}{HTML}{68A595}
\definecolor{OIsky}{HTML}{9CC2DD}\definecolor{OIpurple}{HTML}{B497B6}\definecolor{OIgray}{HTML}{9A9A9A}"""


def load(p):
    return json.loads(Path(p).read_text())


def frame(w, h, xr, yr, xticks, yticks, xlabel="", ylabel="", grid="y", fmt=lambda v: f"{v:g}", yfmt=lambda v: f"{v:g}"):
    """Axes in a scope already shifted to the panel's lower-left corner: returns (tikz lines, x map, y map)."""
    X = lambda v: (v - xr[0]) / (xr[1] - xr[0]) * w
    Y = lambda v: (v - yr[0]) / (yr[1] - yr[0]) * h
    L = []
    if "y" in grid:
        L += [f"\\draw[black!9] (0,{Y(t):.3f})--({w},{Y(t):.3f});" for t in yticks]
    if "x" in grid:
        L += [f"\\draw[black!9] ({X(t):.3f},0)--({X(t):.3f},{h});" for t in xticks]
    L.append(f"\\draw[black!45,line width=.4pt] (0,{h})--(0,0)--({w},0);")
    L += [f"\\node[anchor=north,font=\\sffamily\\tiny,text=black!70,inner sep=1.5pt] at ({X(t):.3f},0) {{{fmt(t)}}};" for t in xticks]
    L += [f"\\node[anchor=east,font=\\sffamily\\tiny,text=black!70,inner sep=1.5pt] at (0,{Y(t):.3f}) {{{yfmt(t)}}};" for t in yticks]
    if xlabel:
        L.append(f"\\node[anchor=north,font=\\sffamily\\scriptsize] at ({w / 2},-0.3) {{{xlabel}}};")
    if ylabel:
        L.append(f"\\node[anchor=south,rotate=90,font=\\sffamily\\scriptsize] at (-0.55,{h / 2}) {{{ylabel}}};")
    return L, X, Y


def legend(items, x0, y, step=0.105):
    """A row of legend entries [(kind, color, label)], kind 'box' or a plot mark, advanced by label length."""
    L, x = [], x0
    for kind, col, lab in items:
        if kind == "box":
            L.append(f"\\fill[{col}] ({x:.3f},{y - 0.06:.3f}) rectangle ({x + 0.15:.3f},{y + 0.06:.3f});")
        else:
            L.append(f"\\node[{col},inner sep=0pt] at ({x + 0.075:.3f},{y:.3f}) {{\\pgfuseplotmark{{{kind}}}}};")
        L.append(f"\\node[anchor=west,font=\\sffamily\\tiny,inner sep=1pt] at ({x + 0.17:.3f},{y:.3f}) {{{lab}}};")
        x += 0.42 + step * len(lab)
    return L


def heat(v):
    """White-to-orange fill for a net-use value in pp, with a readable text color."""
    v = max(0.0, min(100.0, v))
    return f"OIorange!{v * 0.85:.0f}!white", "black!80"


# ---- pixel sprites (original designs, drawn as filled squares) ----
SPRITE_PAL = {"k": "3B302C", "s": "F1C7A1", "S": "D9A27C", "m": "B5675A", "w": "F4F1EA", "W": "D8D4CC",
              "c": "5B7FAF", "C": "45679A", "o": "6E8FBF", "O": "4E6E9E", "b": "8BA6CC", "g": "A0896C", "G": "7E6A52",
              "h": "4A3328", "H": "6B4A38", "r": "B8664E", "R": "974F3B", "n": "4D4A5A", "N": "3A3846",
              "y": "D9B45A", "Y": "B8913A", "e": "9A9A9A", "E": "777777", "t": "68A595", "T": "4E8C7C",
              "q": "B497B6", "f": "E8DCC8", "F": "C9B79C", "l": "9CC2DD", "p": "C98B5E"}
SPRITES = {
    "mech1": ["...cccc...", "..cccccc..", "..ccccccC.", "..ssssss..", "..skssks..", "..ssssss..", "...smms...", "...ssss...",
              ".bbbbbbbb.", "bboobboobb", "sboooooobs", "sboooooobs", ".oooooooo.", ".oo....oo.", ".kk....kk."],
    "mech2": ["...gggg...", "..gggggg..", "..ggggggG.", "..ssssss..", "..skssks..", "..ssssss..", "...smms...", "...ssss...",
              ".GGGGGGGG.", "GGffGGffGG", "sGffffffGs", "sGffffffGs", ".ffffffff.", ".ff....ff.", ".kk....kk."],
    "hero":  ["...hhhh...", "..hhhhhh.h", ".hhhhhhhhh", ".hssssssh.", ".hskssksh.", ".hssssssh.", "..ssmmss..", "...ssss...",
              ".rrrrrrrr.", "rrrwwwwrrr", "srrwwwwrrs", "srrwwwwrrs", ".nnnnnnnn.", ".nn....nn.", ".kk....kk."],
    "comp":  ["..HHHHHH..", ".HHHHHHHH.", ".HssssssH.", ".sskssks..", ".ssssssss.", ".sHHmmHHs.", "..HHHHHH..", "...ssss...",
              ".nnnnnnnn.", "nnnlllnnnn", "snnlllnnns", "snnnnnnnns", ".NNNNNNNN.", ".NN....NN.", ".kk....kk."],
    "robot": ["....y.....", "....k.....", ".eeeeeeee.", ".eEEEEEEe.", ".eEtEEtEe.", ".eEEEEEEe.", ".eEEkkEEe.", ".eeeeeeee.",
              "..eeeeee..", ".EeeeeeeE.", ".Ee....eE."],
    "mirror": ["..yyyy..", ".yllllY.", "yllwllY.", "yllllllY", "yllllllY", ".yllllY.", "..yyyy..", "...YY...", "..YYYY.."],
    "house":  ["...RR...", "..RRRR..", ".RRRRRR.", "RRRRRRRR", ".eeeeee.", ".eeggee.", ".eeggee.", ".eeggee."],
    "chair":  ["pp......", "pp......", "pp......", "pppppp..", "pppppp..", "p....p..", "p....p..", "p....p.."],
    "church": ["...k....", "..kkk...", "...k....", "..ffff..", ".ffffff.", "ffffffff", ".FFggFF.", ".FFggFF."],
    "flag":   ["kttttt..", "kttttttt", "kttttttt", "kttttt..", "k.......", "k.......", "k.......", "k......."],
    "mute":   ["....k.....", "...kk.r..r", "kkkkk..rr.", "kkkkk..rr.", "kkkkk.r..r", "...kk.....", "....k....."],
    "ask":    [".kkkkkkkk.", "kwwwkkwwwk", "kwwkwwkwwk", "kwwwwwkwwk", "kwwwwkwwwk", "kwwwwwwwwk", "kwwwwkwwwk", ".kkkkkkkk.", "..kk......"],
    "eyex":   ["k........k", "k........k", ".kk....kk.", "...kkkk...", "..k..k..k.", ".k...k...k"],
    "mail":   ["kkkkkkkkkk", "kkwwwwwwkk", "kwkwwwwkwk", "kwwkwwkwwk", "kwwwkkwwwk", "kwwwwwwwwk", "kkkkkkkkkk"],
}


def sprite(name, x, y, px, recolor=None):
    """Sprite with its lower-left corner at (x, y); px is the size of one pixel in cm. Runs of one color share a rectangle."""
    rows = SPRITES[name]
    if recolor:
        rows = ["".join(recolor.get(ch, ch) for ch in r) for r in rows]
    L = []
    for i, row in enumerate(rows):
        yy = y + (len(rows) - 1 - i) * px
        j = 0
        while j < len(row):
            ch = row[j]
            k = j
            while k < len(row) and row[k] == ch:
                k += 1
            if ch != ".":
                L.append(f"\\fill[fill={{rgb,255:red,{int(SPRITE_PAL[ch][0:2], 16)};green,{int(SPRITE_PAL[ch][2:4], 16)};blue,{int(SPRITE_PAL[ch][4:6], 16)}}}] "
                         f"({x + j * px:.4f},{yy:.4f}) rectangle ({x + k * px + 0.002:.4f},{yy + px + 0.002:.4f});")
            j = k
    return "\n".join(L)


def design():
    """Figure 2 (one column, pixel style): how Study 1 states the boundary, and Study 2's channels with the character view."""
    L = [r"\begin{figure}[t]", r"\centering",
         r"\begin{tikzpicture}[x=1cm,y=1cm,"
         r"cell/.style={draw=black!70,line width=.6pt,fill=#1,minimum width=1.58cm,minimum height=0.74cm,align=center,font=\sffamily\scriptsize,inner sep=1pt,text width=1.5cm},"
         r"hd/.style={font=\sffamily\scriptsize\bfseries,text=black!60,align=center}]"]
    # (a) Study 1
    L.append(r"\fill[black!3] (0,2.3) rectangle (7.6,5.55);")
    L.append(r"\node[anchor=north west,font=\sffamily\small\bfseries] at (0.12,5.47) {(a) Study 1: how the boundary is stated};")
    for x, t in ((3.12, "state"), (4.82, "utterance flag"), (6.52, "+ sentence")):
        L.append(f"\\node[hd] at ({x},4.67) {{{t}}};")
    L.append(sprite("ask", 0.14, 3.7, 0.05, {"k": "C"}))
    L.append(r"\node[anchor=west,font=\sffamily\scriptsize\bfseries,align=left] at (0.7,3.93) {cannot\\understand};")
    L.append(sprite("mute", 0.14, 2.76, 0.05, {"k": "R", "r": "R"}))
    L.append(r"\node[anchor=west,font=\sffamily\scriptsize\bfseries,align=left] at (0.7,2.93) {cannot\\hear};")
    cells = [(3.12, 3.93, "OIblue!12", r"speaks:\\English", ""), (4.82, 3.93, "OIblue!12", r"understood:\\false", ""),
             (6.52, 3.93, "OIblue!12", r"``does not speak\\Japanese''", r"\tiny"),
             (3.12, 2.93, "black!4", r"---", ""), (4.82, 2.93, "OIorange!14", r"audible:\\false", ""),
             (6.52, 2.93, "OIorange!14", r"``could not\\hear them''", r"\tiny")]
    for x, y, fill, t, f in cells:
        extra = ",draw=black!25,text=black!40" if t == "---" else ""
        L.append(f"\\node[cell={fill}{extra},font=\\sffamily\\scriptsize{f}] at ({x},{y}) {{{t}}};")
    # (b) Study 2
    L.append(r"\fill[black!3] (0,0.15) rectangle (7.6,2.15);")
    L.append(r"\node[anchor=north west,font=\sffamily\small\bfseries] at (0.12,2.07) {(b) Study 2: four channels};")
    chans = [("mute", "Hear", "nothing"), ("ask", "Understand", "``Casey speaks Japanese''"),
             ("eyex", "See", "``Alex puts something away''"), ("mail", "Receive", "``Alex sends a message''")]
    for k, (ic, name, view) in enumerate(chans):
        x = 0.15 + 1.86 * k
        L.append(f"\\draw[black!70,line width=.6pt,fill=white] ({x:.2f},0.28) rectangle ++(1.75,1.3);")
        w, h = len(SPRITES[ic][0]) * 0.055, len(SPRITES[ic]) * 0.055
        L.append(sprite(ic, x + 0.875 - w / 2, 1.33 - h / 2, 0.055, {"k": "R", "r": "R"}))
        L.append(f"\\node[font=\\sffamily\\scriptsize\\bfseries] at ({x + 0.875:.3f},0.91) {{{name}}};")
        L.append(f"\\fill[OIgreen!14] ({x + 0.06:.3f},0.34) rectangle ++(1.63,0.42);")
        L.append(f"\\node[font=\\sffamily\\tiny,text=OIgreen!55!black,align=center,text width=1.6cm] at ({x + 0.875:.3f},0.55) {{{view}}};")
    L += [r"\end{tikzpicture}",
          r"\caption{Design. (a) Study 1 states the boundary in five ways, matched within each row. The sentence is added to the repertoire for comprehension and to the flag for hearing. (b) Study 2 hides content through four channels, and the character view (green) replaces each hidden event with what the character can still observe.}",
          r"\label{fig:design}", r"\end{figure}"]
    return "\n".join(L)


def study1():
    """Figure 3: Study 1. (a) net use per model and statement, (b) state probe against net use, (c) by question."""
    import csv
    from collections import defaultdict
    models = sorted(load(R1 / "model_metrics.json"), key=lambda r: -sum(r[k]["point"] for k in ("language", "flag_understand", "flag_inaudible", "narrated_inaudible", "language_prose")))
    specs = [("language", "reper-\\\\toire"), ("flag_understand", "flag"), ("language_prose", "reper. +\\\\sentence"),
             ("flag_inaudible", "flag"), ("narrated_inaudible", "flag +\\\\sentence")]
    L = [r"\begin{figure*}[t]", r"\centering", r"\begin{tikzpicture}[x=1cm,y=1cm]"]
    # (a) heatmap
    cw, ch = 0.82, 0.27
    n = len(models)
    top = (n + 1) * ch
    L.append(f"\\node[panel] at (-2.0,{top + 1.2:.2f}) {{(a) Net use of inaccessible content (pp)}};")
    L.append(f"\\node[font=\\sffamily\\tiny\\bfseries,text=OIblue] at ({1.5 * cw:.2f},{top + 0.72:.2f}) {{cannot understand}};")
    L.append(f"\\node[font=\\sffamily\\tiny\\bfseries,text=OIorange] at ({4 * cw:.2f},{top + 0.72:.2f}) {{cannot hear}};")
    L.append(f"\\draw[OIblue,line width=.5pt] (0.05,{top + 0.6:.2f})--({3 * cw - 0.05:.2f},{top + 0.6:.2f});")
    L.append(f"\\draw[OIorange,line width=.5pt] ({3 * cw + 0.05:.2f},{top + 0.6:.2f})--({5 * cw - 0.05:.2f},{top + 0.6:.2f});")
    for j, (_, lab) in enumerate(specs):
        L.append(f"\\node[font=\\sffamily\\tiny,align=center,anchor=south] at ({(j + 0.5) * cw:.2f},{top + 0.02:.2f}) {{{lab}}};")
    rows = [(NAMES[r["model"]], [100 * r[k]["point"] for k, _ in specs]) for r in models]
    rows.append(("Mean", [sum(r[1][j] for r in rows) / n for j in range(5)]))
    for i, (name, vals) in enumerate(rows):
        y = top - (i + 1) * ch - (0.08 if name == "Mean" else 0)
        bf = "\\bfseries" if name == "Mean" else ""
        L.append(f"\\node[anchor=east,font=\\sffamily\\tiny{bf}] at (-0.05,{y + ch / 2:.3f}) {{{name}}};")
        for j, v in enumerate(vals):
            fill, txt = heat(v)
            L.append(f"\\fill[{fill}] ({j * cw + 0.012:.3f},{y + 0.012:.3f}) rectangle ({(j + 1) * cw - 0.012:.3f},{y + ch - 0.012:.3f});"
                     f"\\node[text={txt},font=\\sffamily\\tiny{bf}] at ({(j + 0.5) * cw:.3f},{y + ch / 2:.3f}) {{{v:.0f}}};")
    # (b) state probe vs leakage
    probe = defaultdict(list)
    for r in csv.DictReader(open(R1 / "state_probes.csv")):
        if r["D"] == "D0" and r["cell"] in ("C-T-", "Einaud_S"):
            probe[(r["model"], r["cell"])].append(float(r["mean"]))
    w, h = 3.0, top - 0.1
    L.append(r"\begin{scope}[xshift=5.0cm]")
    L.append(f"\\node[panel] at (-0.75,{top + 1.05:.2f}) {{(b) Reads the state, still leaks}};")
    fl, X, Y = frame(w, h, (0, 100), (0, 100), [0, 25, 50, 75, 100], [0, 25, 50, 75, 100], "State probe answered correctly (\\%)", "Net use (pp)", grid="xy")
    L += fl
    L.append(f"\\fill[OIorange!7] ({X(80):.3f},{Y(40):.3f}) rectangle ({X(100):.3f},{Y(100):.3f});")
    L.append(f"\\node[font=\\sffamily\\tiny,text=OIorange!80!black,align=left,anchor=north west] at ({X(3):.3f},{Y(99):.3f}) {{shaded: reads the state\\\\correctly yet leaks}};")
    for r in models:
        for cell, key, col, mk in (("C-T-", "language", "OIblue", "*"), ("Einaud_S", "flag_inaudible", "OIorange", "triangle*")):
            ps = probe[(r["model"], cell)]
            x, y = 100 * sum(ps) / len(ps), 100 * r[key]["point"]
            L.append(f"\\node[{col},inner sep=0pt,opacity=.85] at ({X(x):.3f},{Y(y):.3f}) {{\\pgfuseplotmark{{{mk}}}}};")
            if r["model"] in ("glm47_flash", "phi4") and (cell == "C-T-") == (r["model"] == "glm47_flash"):
                L.append(f"\\node[anchor={'west' if r['model'] == 'glm47_flash' else 'north'},font=\\sffamily\\tiny,text=black!60] at ({X(x) + (0.08 if r['model'] == 'glm47_flash' else 0):.3f},{Y(y) - (0 if r['model'] == 'glm47_flash' else 0.05):.3f}) {{{NAMES[r['model']]}}};")
    L.append(f"\\node[OIblue,inner sep=0pt] at ({X(5):.3f},{Y(17):.3f}) {{\\pgfuseplotmark{{*}}}};\\node[anchor=west,font=\\sffamily\\tiny] at ({X(8):.3f},{Y(17):.3f}) {{repertoire (understand)}};")
    L.append(f"\\node[OIorange,inner sep=0pt] at ({X(5):.3f},{Y(7):.3f}) {{\\pgfuseplotmark{{triangle*}}}};\\node[anchor=west,font=\\sffamily\\tiny] at ({X(8):.3f},{Y(7):.3f}) {{audibility flag (hear)}};")
    L.append(r"\end{scope}")
    # (c) by question
    d = load(RA / "by_question.json")
    qs = [("content", "What did they say?"), ("task", "What is the task?"), ("check", "Did you catch it?"), ("plan", "What do we do next?")]
    L.append(r"\begin{scope}[xshift=10.6cm]")
    L.append(f"\\node[panel] at (-1.9,{top + 1.05:.2f}) {{(c) By the companion's question}};")
    w2 = 3.0
    fl, X, _ = frame(w2, h, (0, 100), (0, 1), [0, 25, 50, 75, 100], [], "Net use, cannot understand (pp)", grid="x")
    L += [l for l in fl if "anchor=east" not in l]
    for i, (q, lab) in enumerate(qs):
        y = h * (0.86 - i * 0.24)
        L.append(f"\\node[anchor=east,font=\\sffamily\\tiny,align=right] at (-0.05,{y:.3f}) {{{lab}}};")
        vals = [100 * d[m][q] for m in d]
        mu = sum(vals) / len(vals)
        L.append(f"\\fill[OIblue!14] (0,{y - 0.13:.3f}) rectangle ({X(mu):.3f},{y + 0.13:.3f});")
        for k, v in enumerate(sorted(vals)):
            L.append(f"\\fill[OIblue!70,opacity=.8] ({X(v):.3f},{y + (k % 3 - 1) * 0.055:.3f}) circle (1.1pt);")
        L.append(f"\\draw[OIblue,line width=1.1pt] ({X(mu):.3f},{y - 0.16:.3f})--({X(mu):.3f},{y + 0.16:.3f});")
        L.append(f"\\node[anchor=south,font=\\sffamily\\tiny\\bfseries,text=OIblue] at ({X(mu):.3f},{y + 0.14:.3f}) {{{mu:.0f}}};")
    L.append(r"\end{scope}")
    L += [r"\end{tikzpicture}",
          r"\caption{Study 1, 11 open models. (a) Net use under the five ways of stating the boundary (96 skeletons in three languages). (b) Each model's state-probe accuracy against its net use. Models that read the boundary correctly still leak. (c) Net use for each of the companion's questions, with models as dots and the mean as a bar. Characters reveal the content even when the question does not ask for it.}",
          r"\label{fig:s1}", r"\end{figure*}"]
    return "\n".join(L)


def study2():
    """Figure 4: Study 2. (a) leakage per model and channel, (b) representation, (c) persistence, (d) search choice."""
    ext = load(RA / "v2-extension.json")["per_model_full_context"]
    order = sorted(ext, key=lambda m: -sum(ext[m].values()))
    ch = ["Hear", "Understand", "See", "Receive"]
    icon = {"Hear": r"\faDeaf", "Understand": r"\faLanguage", "See": r"\faEyeSlash", "Receive": r"\faEnvelope"}
    pd = [l.split(",") for l in (ROOT / "paper/arr/figures/plot-data.csv").read_text().splitlines()[1:]]
    H = 3.0
    L = [r"\begin{figure*}[t]", r"\centering", r"\begin{tikzpicture}[x=1cm,y=1cm]"]
    # (a) heatmap
    cw, rh = 0.6, H / (len(order) + 1.3)
    L.append(f"\\node[panel] at (-1.95,{H + 0.85:.2f}) {{(a) Net use by channel (pp)}};")
    for j, c in enumerate(ch):
        L.append(f"\\node[font=\\sffamily\\tiny,align=center,anchor=south] at ({(j + 0.5) * cw:.2f},{H + 0.02:.2f}) {{{{\\color{{OIorange}}{icon[c]}}}\\\\{c[:4] + '.' if c == 'Understand' else c}}};")
    rows = [(NAMES[m], [100 * ext[m][c] for c in ch]) for m in order]
    rows.append(("Mean", [sum(r[1][j] for r in rows) / len(rows) for j in range(4)]))
    for i, (name, vals) in enumerate(rows):
        y = H - (i + 1) * rh - (0.06 if name == "Mean" else 0)
        bf = "\\bfseries" if name == "Mean" else ""
        L.append(f"\\node[anchor=east,font=\\sffamily\\tiny{bf}] at (-0.05,{y + rh / 2:.3f}) {{{name}}};")
        for j, v in enumerate(vals):
            fill, txt = heat(v)
            L.append(f"\\fill[{fill}] ({j * cw + 0.01:.3f},{y + 0.01:.3f}) rectangle ({(j + 1) * cw - 0.01:.3f},{y + rh - 0.01:.3f});"
                     f"\\node[text={txt},font=\\sffamily\\tiny{bf}] at ({(j + 0.5) * cw:.3f},{y + rh / 2:.3f}) {{{max(v, 0):.0f}}};")
    # (b) representation contrasts
    res = load(ROOT / "analysis/h200-v2-20261002/eleven-model-results.json")["exploratory_paired_contrasts"]
    rep = {r["contrast"]: r for r in res if r["contrast"].startswith("E2")}
    L.append(r"\begin{scope}[xshift=3.15cm]")
    L.append(f"\\node[panel] at (0,{H + 0.85:.2f}) {{(b) State format vs. flag}};")
    w = 2.8
    fl, X, Y = frame(w, H, (-45, 45), (0, 4), [-40, -20, 0, 20, 40], [], "change in net use (pp)", grid="x")
    L += [l for l in fl if "anchor=east" not in l]
    L.append(f"\\draw[black!55] ({X(0):.3f},0)--({X(0):.3f},{H});")
    for i, c in enumerate(ch):
        yc = Y(3.5 - i)
        L.append(f"\\node[anchor=east,font=\\footnotesize,text=OIorange] at (-0.02,{yc:.3f}) {{{icon[c]}}};")
        for key, col, dy in ((f"E2 R1-minus-R2 {c}", "OIblue", 0.11), (f"E2 R3-minus-R2 {c}", "OIgreen", -0.11)):
            r = rep[key]
            v, lo, hi = [100 * a for a in (r["estimate"], *r["ci95"])]
            L.append(f"\\fill[{col}] ({X(0):.3f},{yc + dy - 0.085:.3f}) rectangle ({X(v):.3f},{yc + dy + 0.085:.3f});"
                     f"\\draw[black!60,line width=.35pt] ({X(lo):.3f},{yc + dy:.3f})--({X(hi):.3f},{yc + dy:.3f});")
    L.append(f"\\fill[OIblue] (0.05,-0.92) rectangle (0.2,-0.8);\\node[anchor=west,font=\\sffamily\\tiny] at (0.22,-0.86) {{membership list}};")
    L.append(f"\\fill[OIgreen] (0.05,-1.17) rectangle (0.2,-1.05);\\node[anchor=west,font=\\sffamily\\tiny] at (0.22,-1.11) {{flag + prose rule}};")
    L.append(r"\end{scope}")
    # (c) persistence
    per = {(r[2], r[3], int(r[5])): 100 * float(r[7]) for r in pd if r[0] == "persistence"}
    colors = {"Hear": ("OIorange", "triangle*"), "Understand": ("OIblue", "*"), "See": ("OIpurple", "square*"), "Receive": ("OIsky", "diamond*")}
    L.append(r"\begin{scope}[xshift=6.75cm]")
    L.append(f"\\node[panel] at (-0.4,{H + 0.85:.2f}) {{(c) Persistence}};")
    w = 2.2
    fl, X, Y = frame(w, H, (0, 4), (0, 100), [0, 2, 4], [0, 25, 50, 75, 100], "neutral exchanges", "net use (pp)")
    L += fl
    ends = []
    for c in ch:
        col, mk = colors[c]
        pts = [(t, per[(c, "full", t)]) for t in (0, 2, 4)]
        L.append(f"\\draw[{col},line width=.9pt] " + "--".join(f"({X(t):.3f},{Y(v):.3f})" for t, v in pts) + ";")
        L += [f"\\node[{col},inner sep=0pt] at ({X(t):.3f},{Y(v):.3f}) {{\\pgfuseplotmark{{{mk}}}}};" for t, v in pts]
        ends.append([Y(pts[-1][1]), c, col])
    ends.sort()
    for k in range(1, len(ends)):
        ends[k][0] = max(ends[k][0], ends[k - 1][0] + 0.2)
    for yv, c, col in ends:
        L.append(f"\\node[anchor=west,font=\\sffamily\\tiny,text={col}] at ({w + 0.12:.3f},{yv:.3f}) {{{c}}};")
    vv = max(per[(c, "view", t)] for c in ch for t in (0, 2, 4))
    L.append(f"\\draw[OIgreen,line width=.9pt,densely dashed] (0,{Y(vv):.3f})--({w},{Y(vv):.3f});\\node[anchor=south west,font=\\sffamily\\tiny,text=OIgreen] at (0.05,{Y(vv):.3f}) {{character view, all channels}};")
    L.append(r"\end{scope}")
    # (d) search choice
    dec = {(r[2], r[3]): tuple(100 * float(x) for x in r[7:10]) for r in pd if r[0] == "decision"}
    L.append(r"\begin{scope}[xshift=10.95cm]")
    L.append(f"\\node[panel] at (-0.35,{H + 0.85:.2f}) {{(d) Choosing where to search}};")
    w = 2.75
    fl, X, Y = frame(w, H, (0, 80), (0, 4), [0, 20, 40, 60, 80], [], "change in choosing A (pp)", grid="x")
    L += [l for l in fl if "anchor=east" not in l]
    for i, c in enumerate(ch):
        yc = Y(3.5 - i)
        L.append(f"\\node[anchor=east,font=\\footnotesize,text=OIorange] at (-0.02,{yc:.3f}) {{{icon[c]}}};")
        for meth, col, dy in (("full", "OIorange", 0.11), ("view", "OIgreen", -0.11)):
            v, lo, hi = dec[(c, meth)]
            L.append(f"\\fill[{col}] (0,{yc + dy - 0.085:.3f}) rectangle ({X(max(v, 0)):.3f},{yc + dy + 0.085:.3f});"
                     f"\\draw[black!60,line width=.35pt] ({X(max(lo, 0)):.3f},{yc + dy:.3f})--({X(hi):.3f},{yc + dy:.3f});")
    L.append(f"\\fill[OIorange] (0.05,-0.92) rectangle (0.2,-0.8);\\node[anchor=west,font=\\sffamily\\tiny] at (0.22,-0.86) {{full context}};")
    L.append(f"\\fill[OIgreen] (0.05,-1.17) rectangle (0.2,-1.05);\\node[anchor=west,font=\\sffamily\\tiny] at (0.22,-1.11) {{character view}};")
    L.append(r"\end{scope}")
    L += [r"\end{tikzpicture}",
          r"\caption{Study 2. (a) Net use of hidden content under full context in the confirmation set (96 scenes with invented characters), for 11 open models and four channels. (b) Change in net use when the access flag is replaced by a membership list or supplemented by a prose rule (11 models, 24 scenes). (c) Net use after zero, two and four neutral exchanges (four models, 32 scenes). (d) Change in choosing place A when the hidden fact switches from B to A (four models). Bars show 95\% bootstrap intervals.}",
          r"\label{fig:s2}", r"\end{figure*}"]
    return "\n".join(L)


def frontier():
    """Figure: frontier models and input format. (a) heat table of core cells, (b) all four features, (c) one feature at a time."""
    op = load(RA / "open_content_only.json")
    ho = load(RA / "hosted.json")
    rs = load(RA / "hosted_reasoning.json")
    H = 2.9
    L = [r"\begin{figure*}[t]", r"\centering", r"\begin{tikzpicture}[x=1cm,y=1cm]"]
    # (a) heat table
    cols = [("repertoire", "reper-\\\\toire"), ("understood_flag", "compr.\\\\flag"), ("prose", "+ sen-\\\\tence"),
            ("inaudible_flag", "audib.\\\\flag"), ("fluent_control_use", "control\\\\use (\\%)")]
    rows = [(NAMES[m], ho[m]["study1"]) for m in ["gpt6sol", "gemini38flash", "grok47", "opus55", "gemini31pro", "sonnet55", "deepseekv4pro"]]
    rows.append(("11 open models", {k: sum(v[k] for v in op.values()) / len(op) for k, _ in cols if k in next(iter(op.values()))}))
    cw, rh = 0.66, H / len(rows)
    L.append(f"\\node[panel] at (-2.25,{H + 0.85:.2f}) {{(a) Study 1 core cells, net use (pp)}};")
    for j, (_, lab) in enumerate(cols):
        L.append(f"\\node[font=\\sffamily\\tiny,align=center,anchor=south] at ({(j + 0.5) * cw:.3f},{H + 0.03:.3f}) {{{lab}}};")
    for i, (name, d) in enumerate(rows):
        y = H - (i + 1) * rh - (0.08 if i == len(rows) - 1 else 0)
        L.append(f"\\node[anchor=east,font=\\sffamily\\tiny] at (-0.05,{y + rh / 2:.3f}) {{{name}}};")
        for j, (k, _) in enumerate(cols):
            v = d.get(k)
            if v is None:
                continue
            v = max(0.0, 100 * v)
            fill = f"OIblue!{v * 0.55:.0f}!white" if k == "fluent_control_use" else heat(v)[0]
            L.append(f"\\fill[{fill}] ({j * cw + 0.012:.3f},{y + 0.012:.3f}) rectangle ({(j + 1) * cw - 0.012:.3f},{y + rh - 0.012:.3f});"
                     f"\\node[font=\\sffamily\\tiny,text=black!80] at ({(j + 0.5) * cw:.3f},{y + rh / 2:.3f}) {{{v:.0f}}};")
    L.append(f"\\node[anchor=north west,font=\\sffamily\\tiny\\itshape,text=black!65] at (0,-0.1) {{Claude Sonnet 5.5 with high reasoning: repertoire {100 * rs['sonnet55-high']['net']:.0f}}};")
    # (b) all four features
    br = load(RA / "bridge.json")
    pts = {m: (100 * br[m]["base:inaccessible"]["estimate"], 100 * br[m]["all:inaccessible"]["estimate"]) for m in ("gemma4_31b", "qwen38_27b")}
    for m in ("deepseekv4pro", "gemini31pro", "sonnet55", "opus55", "grok47", "gemini38flash", "gpt6sol"):
        b = ho[m]["bridge"]
        pts[m] = (100 * b["base"]["unheard_net"], 100 * b["all"]["unheard_net"])
    show = ["gemma4_31b", "qwen38_27b", "deepseekv4pro", "gemini31pro", "sonnet55"]
    rest = [m for m in pts if m not in show]
    items = [(NAMES[m], *pts[m]) for m in show] + [(f"other {len(rest)} hosted", max(pts[m][0] for m in rest), max(pts[m][1] for m in rest))]
    L.append(r"\begin{scope}[xshift=5.55cm]")
    L.append(f"\\node[panel] at (-1.75,{H + 0.85:.2f}) {{(b) All four features swapped in}};")
    w = 2.45
    fl, X, _ = frame(w, H, (0, 100), (0, 1), [0, 25, 50, 75, 100], [], "net use of unheard speech (pp)", grid="x")
    L += [l for l in fl if "anchor=east" not in l]
    rh2 = H / len(items)
    for i, (name, a, b) in enumerate(items):
        yc = H - (i + 0.5) * rh2
        L.append(f"\\node[anchor=east,font=\\sffamily\\tiny] at (-0.05,{yc:.3f}) {{{name}}};")
        for v, col, dy in ((a, "black!25", 0.08), (b, "OIorange", -0.08)):
            L.append(f"\\fill[{col}] (0,{yc + dy - 0.065:.3f}) rectangle ({max(X(v), 0.02):.3f},{yc + dy + 0.065:.3f});")
        L.append(f"\\node[anchor=west,font=\\sffamily\\tiny,text=black!70,inner sep=1.5pt] at ({max(X(b), 0.02):.3f},{yc - 0.08:.3f}) {{{b:.0f}}};")
    L.append(r"\end{scope}")
    # (c) one feature at a time
    rep = load(RA / "bridge-replication.json")
    swaps = [("sys", "system"), ("card", "sheet"), ("schema", "state"), ("ask", "question")]
    L.append(r"\begin{scope}[xshift=9.6cm]")
    L.append(f"\\node[panel] at (-0.45,{H + 0.85:.2f}) {{(c) One feature at a time (pp)}};")
    hh = (H - 0.3) / 2
    for k, m in enumerate(("gemma4_31b", "qwen38_27b")):
        y0 = (1 - k) * (hh + 0.3)
        L.append(f"\\begin{{scope}}[yshift={y0:.3f}cm]")
        fl, X, Y = frame(3.3, hh - 0.15, (0, 4), (0, 100), [], [0, 50, 100], "", "")
        L += fl
        L.append(f"\\node[anchor=south west,font=\\sffamily\\tiny\\bfseries] at (0.03,{hh - 0.17:.3f}) {{{NAMES[m]}}};")
        for j, (sw, lab) in enumerate(swaps):
            for data, col, dx in ((br, "OIorange!40", -0.13), (rep, "OIorange", 0.13)):
                v = 100 * data[m][f"{sw}:inaccessible"]["estimate"]
                L.append(f"\\fill[{col}] ({X(j + 0.5) + dx - 0.12:.3f},0) rectangle ({X(j + 0.5) + dx + 0.12:.3f},{Y(max(v, 0.8)):.3f});")
            if k == 1:
                L.append(f"\\node[anchor=north,font=\\sffamily\\tiny] at ({X(j + 0.5):.3f},-0.02) {{{lab}}};")
        L.append(r"\end{scope}")
    L += legend([("box", "OIorange!40", "discovery scenes"), ("box", "OIorange", "new scenes")], 0.0, -0.5)
    L.append(r"\end{scope}")
    L += legend([("box", "black!25", "Study 2 prompt"), ("box", "OIorange", "+ all four")], 4.0, -0.85)
    L += [r"\end{tikzpicture}",
          r"\caption{Frontier models and input format. (a) Study 1 core cells with the content question (288 items per cell). Five of six hosted models stay at or below 9 pp in every cell while using permitted content in the fluent control. (b) Swapping Study 1's system prompt, character sheet, state layout and question into Study 2's hearing prompts. (c) Swapping one feature at a time, on the discovery scenes and on 96 new scenes. A different feature breaks each model, and both effects replicate.}",
          r"\label{fig:frontier}", r"\end{figure*}"]
    return "\n".join(L)


def remedy():
    """Figure: (a) the list-first prompt, (b, c) leakage and permitted use for five methods in Study 2."""
    models = load(R1 / "model_metrics.json")
    H = 3.0
    L = [r"\begin{figure*}[t]", r"\centering", r"\begin{tikzpicture}[x=1cm,y=1cm]"]
    # (a) list-first
    w = 3.4
    L.append(f"\\node[panel] at (-0.75,{H + 0.55:.2f}) {{(a) List-first prompt, Study 1}};")
    fl, X, Y = frame(w, H, (0, 100), (0, 100), [0, 25, 50, 75, 100], [0, 25, 50, 75, 100],
                     "hidden values in the first-step list (\\%)", "net use after the prompt (pp)", grid="xy")
    L += fl
    lab = {("glm47_flash", "language"): ("east", "GLM-4.7-Flash"), ("qwen35_9b", "language"): ("north west", "Qwen3.5-9B"),
           ("mistral_small3", "language"): ("south west", "Mistral-24B")}
    for r in models:
        for key, col, mk in (("language", "OIblue", "*"), ("inaudible", "OIorange", "triangle*")):
            x, y = 100 * r[f"step1_{key}"]["point"], max(0, 100 * r[f"m1g_{key}"]["point"])
            L.append(f"\\node[{col},inner sep=0pt,opacity=.9] at ({X(x):.3f},{Y(y):.3f}) {{\\pgfuseplotmark{{{mk}}}}};")
            if (r["model"], key) in lab:
                a, t = lab[(r["model"], key)]
                dx = {"east": -0.08, "north west": 0.03, "south west": -0.03}[a]
                dy = {"east": 0, "north west": -0.05, "south west": 0.06}[a]
                L.append(f"\\node[anchor={a},font=\\sffamily\\tiny,text=black!60,inner sep=1pt] at ({X(x) + dx:.3f},{Y(y) + dy:.3f}) {{{t}}};")
    L += legend([("*", "OIblue", "cannot understand"), ("triangle*", "OIorange", "cannot hear")], 0.05, H - 0.15)
    # (b, c) leakage and permitted use by method, rows aligned
    est = load(ROOT / "analysis/h200-v2-20261002/method-six-descriptive-results.json")["descriptive_estimates"]
    v = {(r["boundary"], r["method"], r["metric"]): 100 * r["estimate"] for r in est}
    meth = [("full", "OIorange", "full context"), ("prose", "OIpurple", "flag + prose rule"), ("self_filter", "OIsky", "self-filter prompt"),
            ("hard", "black", "event removed"), ("view", "OIgreen", "character view")]
    marks = {"Hear": "triangle*", "Understand": "*", "See": "square*", "Receive": "diamond*"}
    rh = H / len(meth)
    for k, (metric, title, x0, xr, ticks) in enumerate((("D", "(b) Leakage of hidden content (pp)", 5.85, (0, 60), [0, 20, 40, 60]),
                                                        ("hit_t", "(c) Use of permitted content (\\%)", 10.4, (0, 100), [0, 25, 50, 75, 100]))):
        L.append(f"\\begin{{scope}}[xshift={x0}cm]")
        L.append(f"\\node[panel] at ({-1.75 if k == 0 else -0.1},{H + 0.55:.2f}) {{{title}}};")
        fl, X, _ = frame(3.3, H, xr, (0, 1), ticks, [], "", grid="x")
        L += [l for l in fl if "anchor=east" not in l]
        for i, (m, col, lab) in enumerate(meth):
            yc = H - (i + 0.5) * rh
            if k == 0:
                L.append(f"\\node[anchor=east,font=\\sffamily\\tiny] at (-0.05,{yc:.3f}) {{{lab}}};")
            vals = {c: max(0.0, v[(c, m, metric)]) for c in marks}
            mu = sum(vals.values()) / 4
            L.append(f"\\fill[{col}!{22 if col == 'black' else 55}] (0,{yc - 0.14:.3f}) rectangle ({max(X(mu), 0.02):.3f},{yc + 0.14:.3f});")
            for c, mk in marks.items():
                L.append(f"\\node[black!65,inner sep=0pt,scale=.8] at ({X(vals[c]):.3f},{yc:.3f}) {{\\pgfuseplotmark{{{mk}}}}};")
            L.append(f"\\node[anchor=west,font=\\sffamily\\tiny\\bfseries,text=black!70] at ({X(xr[1]) + 0.02:.3f},{yc:.3f}) {{{mu:.0f}}};")
        L.append(r"\end{scope}")
    L += legend([(mk, "black!65", c) for c, mk in marks.items()], 6.0, -0.45, step=0.11)
    L.append(r"\node[anchor=west,font=\sffamily\tiny,text=black!60] at (10.4,-0.45) {bars: mean over channels, number at right};")
    L += [r"\end{tikzpicture}",
          r"\caption{Remedies. (a) The list-first prompt in Study 1. Each point is one model and boundary, and models whose first-step list omits the hidden values also leave them out of the answer. (b, c) Five methods in Study 2 (six models, 48 scenes), with one marker per channel. Self-filtering lowers leakage but also drops permitted content, while removing the event and the character view stop leakage and keep it.}",
          r"\label{fig:remedy}", r"\end{figure*}"]
    return "\n".join(L)


def example():
    """Figure 1: one Study 1 item drawn as a pixel-art scene, with verbatim replies from Gemma-4-31B."""
    L = [r"\begin{figure}[t]", r"\centering",
         r"\begin{tikzpicture}[x=1cm,y=1cm,"
         r"pbub/.style={draw=black!70,line width=.6pt,fill=#1,inner sep=3pt,align=left,font=\sffamily\scriptsize},"
         r"reply/.style={draw=#1,line width=.7pt,fill=white,inner sep=3pt,text width=5.2cm,align=left,font=\sffamily\scriptsize},"
         r"tag/.style={fill=#1,text=white,font=\sffamily\tiny\bfseries,inner sep=1.6pt,anchor=north west}]"]
    # scene
    L.append(r"\fill[black!3] (0,2.3) rectangle (7.6,5.75);")
    L.append(r"\node[fill=OIsky!35,font=\sffamily\tiny\bfseries,inner sep=2pt,anchor=north west] at (0.08,5.68) {SCENE};")
    L.append(sprite("mech1", 0.35, 2.75, 0.06))
    L.append(sprite("mech2", 1.05, 2.75, 0.06))
    L.append(r"\node[pbub=OIorange!12,anchor=south west] (sp) at (0.15,4.05) {\emph{¿Dónde está el \textbf{espejo}?}\\\emph{En el \textbf{almacén}. No se lo}\\\emph{digas a nadie.}};")
    L.append(r"\fill[OIorange!12,draw=black!70,line width=.6pt] (0.75,4.08)--(0.95,3.75)--(1.05,4.08)--cycle;")
    L.append(r"\draw[black!35,densely dashed,line width=.6pt,-{Stealth[length=3pt]}] (1.8,3.2)--(3.55,3.2);")
    L.append(sprite("hero", 3.75, 2.75, 0.06))
    L.append(r"\node[pbub=white,font=\sffamily\scriptsize\bfseries,inner sep=1.5pt] at (4.62,4.1) {???};")
    L.append(r"\fill[black!70] (4.3,3.8) rectangle ++(0.07,0.07);\fill[black!70] (4.22,3.7) rectangle ++(0.05,0.05);")
    L.append(r"\node[fill=OIblue!15,font=\sffamily\tiny,inner sep=1.5pt,align=center] at (4.05,2.5) {\textbf{Mara} $\cdot$ English only};")
    L.append(sprite("comp", 6.6, 2.75, 0.06))
    L.append(r"\node[pbub=OIsky!25,anchor=south east] at (7.5,4.05) {What were those\\two saying?};")
    L.append(r"\fill[OIsky!25,draw=black!70,line width=.6pt] (6.85,4.08)--(6.95,3.75)--(7.1,4.08)--cycle;")
    # model
    L.append(r"\draw[black!40,line width=.6pt,-{Stealth[length=3.5pt]}] (3.8,2.3)--(3.8,2.0);")
    L.append(sprite("robot", 2.55, 1.47, 0.04))
    L.append(r"\node[anchor=west,font=\sffamily\scriptsize,text=black!75] at (3.0,1.68) {model voices Mara};")
    # replies
    rows = [(1.3, "OIorange", r"\faTimes\ A", ("mirror", "house"), None,
             r"``Just some boring shit about a \leak{mirror} being in the \leak{warehouse}. Don't worry about it.''"),
            (0.35, "OIorange", r"\faTimes\ B", ("chair", "church"), None,
             r"``Something about a \leak{chair} being in a \leak{church}. Weird as hell, right?''"),
            (-0.6, "OIgreen", r"\faCheck\ A + flag", ("flag",), None,
             r"``Don't look at me, Jo. I didn't catch a damn word of it.''")]
    for top, col, tag, objs, words, text in rows:
        L.append(f"\\fill[{col}!10] (0,{top - 0.88:.2f}) rectangle (7.6,{top:.2f});")
        L.append(f"\\node[tag={col}] at (0.08,{top - 0.06:.2f}) {{{tag}}};")
        for k, ob in enumerate(objs):
            L.append(sprite(ob, 0.15 + k * 0.5, top - 0.84, 0.045))
        L.append(sprite("hero", 1.35, top - 0.84, 0.05))
        L.append(f"\\node[reply={col},anchor=west] at (2.1,{top - 0.44:.2f}) {{{text}}};")
        L.append(f"\\fill[white,draw={col},line width=.7pt] (2.12,{top - 0.36:.2f})--(1.93,{top - 0.44:.2f})--(2.12,{top - 0.52:.2f});")
        L.append(f"\\fill[white] (2.115,{top - 0.35:.2f}) rectangle (2.15,{top - 0.53:.2f});")
    L += [r"\end{tikzpicture}",
          r"\caption{Gemma-4-31B voicing a character who does not speak Spanish (replies verbatim, names changed). The reply tracks the hidden object and place when version B swaps them. Adding a flag to the same state saying that the character did not understand the speech stops the leak. Each reply is scored for its own version's values and the other version's, so a plausible guess cancels.}",
          r"\label{fig:example}", r"\end{figure}"]
    return "\n".join(L)


def bridge_full():
    """Appendix figure: the bridge on the discovery scenes and on new scenes, all 11 open models."""
    br, rep = load(RA / "bridge.json"), load(RA / "bridge-replication.json")
    cols = [("base", "Base"), ("sys", "Sys."), ("card", "Sheet"), ("schema", "State"), ("ask", "Quest."), ("all", "All")]
    order = sorted(br, key=lambda m: br[m]["base:inaccessible"]["estimate"])
    cw, rh = 0.62, 0.27
    n = len(order)
    L = [r"\begin{figure*}[t]", r"\centering", r"\begin{tikzpicture}[x=1cm,y=1cm]"]
    for k, (data, title, x0) in enumerate(((br, "(a) Discovery scenes", 0.0), (rep, "(b) New scenes, characters renamed", 5.6))):
        L.append(f"\\begin{{scope}}[xshift={x0}cm]")
        L.append(f"\\node[panel] at ({-1.95 if k == 0 else -0.05},{n * rh + 0.75:.2f}) {{{title}}};")
        for j, (_, lab) in enumerate(cols):
            L.append(f"\\node[font=\\sffamily\\tiny,anchor=south] at ({(j + 0.5) * cw:.3f},{n * rh + 0.03:.3f}) {{{lab}}};")
        L.append(f"\\node[font=\\sffamily\\tiny,anchor=south,align=center] at ({6 * cw + 0.45:.3f},{n * rh + 0.03:.3f}) {{audible}};")
        for i, m in enumerate(order):
            y = (n - 1 - i) * rh
            if k == 0:
                L.append(f"\\node[anchor=east,font=\\sffamily\\tiny] at (-0.05,{y + rh / 2:.3f}) {{{NAMES[m]}}};")
            for j, (sw, _) in enumerate(cols):
                v = data[m][f"{sw}:inaccessible"]
                fill, txt = heat(100 * v["estimate"])
                lo, hi = v["delta_ci95"]
                sig = sw != "base" and (lo > 0 or hi < 0)
                L.append(f"\\fill[{fill}] ({j * cw + 0.012:.3f},{y + 0.012:.3f}) rectangle ({(j + 1) * cw - 0.012:.3f},{y + rh - 0.012:.3f});")
                if sig:
                    L.append(f"\\draw[black!60,line width=.35pt] ({j * cw + 0.035:.3f},{y + 0.03:.3f}) rectangle ({(j + 1) * cw - 0.035:.3f},{y + rh - 0.035:.3f});")
                L.append(f"\\node[text={txt},font=\\sffamily\\tiny] at ({(j + 0.5) * cw:.3f},{y + rh / 2:.3f}) {{{100 * v['estimate']:.0f}}};")
            aud = [100 * data[m][f"{sw}:accessible"]["estimate"] for sw, _ in cols]
            L.append(f"\\node[font=\\sffamily\\tiny,text=OIblue] at ({6 * cw + 0.45:.3f},{y + rh / 2:.3f}) {{{(f'{min(aud):.0f}' if round(min(aud)) == round(max(aud)) else f'{min(aud):.0f}--{max(aud):.0f}')}}};")
        L.append(r"\end{scope}")
    L += [r"\end{tikzpicture}",
          r"\caption{Bridge experiment for all 11 open models: net use of unheard speech (pp) under Study 2's hearing prompt (Base), with one Study 1 feature swapped in, and with all four. Outlined cells differ from Base with a paired 95\% skeleton-bootstrap interval that excludes zero. The last column gives the range of target use for the same speech when audible (\%). (a) 96 discovery scenes. (b) 96 confirmation scenes with each character renamed to a Study 1 persona.}",
          r"\label{fig:bridgefull}", r"\end{figure*}"]
    return "\n".join(L)


def listfirst_models():
    """Appendix figure: the list-first prompt per model in Study 1."""
    models = sorted(load(R1 / "model_metrics.json"), key=lambda r: r["base_language"]["point"])
    n = len(models)
    rh = 0.27
    H = n * rh
    L = [r"\begin{figure*}[t]", r"\centering", r"\begin{tikzpicture}[x=1cm,y=1cm]"]
    for k, (key, title, x0, col) in enumerate((("language", "(a) Cannot understand", 0.0, "OIblue"), ("inaudible", "(b) Cannot hear", 4.6, "OIorange"))):
        L.append(f"\\begin{{scope}}[xshift={x0}cm]")
        L.append(f"\\node[panel] at ({-1.95 if k == 0 else -0.1},{H + 0.45:.2f}) {{{title}: net use (pp)}};")
        fl, X, _ = frame(3.3, H, (0, 100), (0, 1), [0, 25, 50, 75, 100], [], "", grid="x")
        L += [l for l in fl if "anchor=east" not in l]
        for i, r in enumerate(models):
            y = (n - 1 - i) * rh + rh / 2
            if k == 0:
                L.append(f"\\node[anchor=east,font=\\sffamily\\tiny] at (-0.05,{y:.3f}) {{{NAMES[r['model']]}}};")
            b, a = 100 * r[f"base_{key}"]["point"], max(0, 100 * r[f"m1g_{key}"]["point"])
            L.append(f"\\draw[{col}!35,line width=1.4pt] ({X(a):.3f},{y:.3f})--({X(b):.3f},{y:.3f});")
            L.append(f"\\fill[black!35] ({X(b):.3f},{y:.3f}) circle (1.5pt);\\fill[{col}] ({X(a):.3f},{y:.3f}) circle (1.7pt);")
        L.append(r"\end{scope}")
    L.append(r"\begin{scope}[xshift=9.25cm]")
    L.append(f"\\node[panel] at (-0.1,{H + 0.45:.2f}) {{(c) Change in translated speech used (pp)}};")
    fl, X, _ = frame(3.3, H, (-30, 20), (0, 1), [-30, -20, -10, 0, 10, 20], [], "", grid="x")
    L += [l for l in fl if "anchor=east" not in l]
    L.append(f"\\draw[black!55] ({X(0):.3f},0)--({X(0):.3f},{H:.3f});\\draw[OIgreen,densely dashed] ({X(-5):.3f},0)--({X(-5):.3f},{H:.3f});")
    for i, r in enumerate(models):
        y = (n - 1 - i) * rh + rh / 2
        v, (lo, hi) = 100 * r["retention"]["point"], [100 * x for x in r["retention"]["ci95"]]
        L.append(f"\\draw[OIgreen!70!black,line width=.5pt] ({X(max(lo, -30)):.3f},{y:.3f})--({X(hi):.3f},{y:.3f});\\fill[OIgreen] ({X(v):.3f},{y:.3f}) circle (1.6pt);")
    L.append(r"\end{scope}")
    L += legend([("box", "black!35", "base prompt"), ("box", "OIblue", "list-first, cannot understand"), ("box", "OIorange", "list-first, cannot hear"),
                 ("box", "OIgreen", "translator change, margin $-5$ pp dashed")], 0.0, -0.55)
    L += [r"\end{tikzpicture}",
          r"\caption{The list-first prompt per model in Study 1 (content and planning questions). (a, b) Net use with the base prompt (gray) and with the list-first prompt. (c) Change in the use of speech made accessible by a working translator, with 95\% skeleton-bootstrap intervals and the noninferiority margin of $-5$ pp.}",
          r"\label{fig:s1m}", r"\end{figure*}"]
    return "\n".join(L)


def factors():
    """Figure: what changes leakage within Study 1. (a, b) model scale, (c, d) format ablation toward Study 2."""
    import math
    sc = {x["model"]: x for x in load(R1 / "scale_all_models.json")}
    val = lambda m, k: 100 * (sc[m][k]["point"] if isinstance(sc[m][k], dict) else sc[m][k])
    fams = [("Qwen3.5", "OIblue", "*", [("qwen35_08b", 0.8), ("qwen35_2b", 2), ("qwen35_4b", 4), ("qwen35_9b", 9)]),
            ("Gemma-4", "OIorange", "square*", [("gemma4_e2b", 2), ("gemma4_12b", 12), ("gemma4_31b", 31)])]
    H = 2.6
    L = [r"\begin{figure*}[t]", r"\centering", r"\begin{tikzpicture}[x=1cm,y=1cm]"]
    for k, (key, title, x0) in enumerate((("language", "(a) Scale: repertoire", 0.0), ("flag_understand", "(b) Scale: comprehension flag", 3.35))):
        L.append(f"\\begin{{scope}}[xshift={x0}cm]")
        L.append(f"\\node[panel] at (-0.55,{H + 0.5:.2f}) {{{title}}};")
        fl, X, Y = frame(2.6, H, (math.log(0.6), math.log(45)), (0, 100), [math.log(v) for v in (1, 3, 10, 30)], [0, 25, 50, 75, 100],
                         "parameters (B, log scale)", "net use (pp)" if k == 0 else "", grid="y", fmt=lambda v: f"{math.exp(v):.0f}")
        L += fl
        for name, col, mk, ms in fams:
            pts = [(X(math.log(b)), Y(val(m, key))) for m, b in ms]
            L.append(f"\\draw[{col},line width=.9pt] " + "--".join(f"({x:.3f},{y:.3f})" for x, y in pts) + ";")
            L += [f"\\node[{col},inner sep=0pt] at ({x:.3f},{y:.3f}) {{\\pgfuseplotmark{{{mk}}}}};" for x, y in pts]
            if k == 1:
                x, y = pts[-1]
                L.append(f"\\node[anchor=west,font=\\sffamily\\tiny,text={col}] at ({x + 0.06:.3f},{y + (0.12 if name == 'Gemma-4' else 0):.3f}) {{{name}}};")
        L.append(r"\end{scope}")
    ab = load(RA / "ablation.json")["cells"]
    combos = [("l0q0c0", "Study 1 prompt"), ("l1q0c0", "+ channel field"), ("l0q1c0", "+ direct question"), ("l0q0c1", "+ minimal context"), ("l1q1c1", "all three")]
    shades = ["black!45", "OIsky", "OIpurple", "OIgreen", "OIorange"]
    models = ["gemma4_31b", "qwen38_27b", "seed_oss_36b", "phi4"]
    for k, (cell, title, x0) in enumerate((("C-T-_flag", "(c) Ablation: comprehension flag", 8.3), ("Einaud_S", "(d) Ablation: audibility flag", 11.2))):
        L.append(f"\\begin{{scope}}[xshift={x0}cm]")
        L.append(f"\\node[panel] at ({-1.6 if k == 0 else -0.1},{H + 0.5:.2f}) {{{title}}};")
        fl, X, Y = frame(2.6, H, (0, 100), (0, 4), [0, 25, 50, 75, 100], [], "net use (pp)", grid="x")
        L += [l for l in fl if "anchor=east" not in l]
        for i, m in enumerate(models):
            y = Y(3.5 - i)
            if k == 0:
                L.append(f"\\node[anchor=east,font=\\sffamily\\tiny] at (-0.05,{y:.3f}) {{{NAMES[m]}}};")
            vs = [100 * ab[m][c][cell] for c, _ in combos]
            L.append(f"\\draw[black!20,line width=1.1pt] ({X(min(vs)):.3f},{y:.3f})--({X(max(vs)):.3f},{y:.3f});")
            for j, v in enumerate(vs):
                L.append(f"\\fill[{shades[j]}] ({X(v):.3f},{y + (j - 2) * 0.045:.3f}) circle (1.5pt);")
        L.append(r"\end{scope}")
    L += legend([("*", "OIblue", "Qwen3.5"), ("square*", "OIorange", "Gemma-4")], 0.0, -0.95)
    L += legend([("box", c, lab) for c, (_, lab) in zip(shades, combos)], 6.55, -0.95, step=0.09)
    L += [r"\end{tikzpicture}",
          r"\caption{What changes leakage within Study~1. (a, b) Net use by model size in two families. Leakage rises from the smallest models to mid-size ones, and Gemma-4-31B falls to 3 pp only when the flag is explicit. (c, d) Adding Study~2's features to Study~1's prompts one at a time (four models, 96 skeletons). The minimal context lowers leakage for most models, the direct question raises it for Seed-OSS-36B, and Gemma-4-31B still repeats unheard speech in half of its replies.}",
          r"\label{fig:factors}", r"\end{figure*}"]
    return "\n".join(L)


def why():
    """Figure: why characters leak. (a) four framings of the same scenes, (b) thinking on and off per model."""
    d = load(ROOT / "analysis/results/added-1009/framing_thinking.json")
    fr, th = d["framing"]["per_model"], d["thinking"]["per_model"]
    conds = [("base", "role-play"), ("author", "author"), ("narrator", "narrator"), ("perspective", "+ perspective rule")]
    def pooled(cond, cell):
        key = "author" if cond == "base" else cond
        vals = [m[f"{key}:{cell}"]["baseline" if cond == "base" else "value"] for m in fr.values() if f"{key}:{cell}" in m]
        return 100 * sum(vals) / len(vals)
    H = 2.0
    L = [r"\begin{figure}[t]", r"\centering", r"\begin{tikzpicture}[x=1cm,y=1cm]"]
    # (a)
    w = 3.6
    L.append(f"\\node[panel] at (-2.1,{H + 0.5:.2f}) {{(a) The same scenes, four framings ({len(fr)} models)}};")
    fl, X, _ = frame(w, H, (0, 100), (0, 1), [0, 25, 50, 75, 100], [], "net use (pp)", grid="x")
    L += [l for l in fl if "anchor=east" not in l]
    rh = H / len(conds)
    L.append(f"\\node[font=\\sffamily\\tiny\\bfseries,text=black!50,anchor=south] at ({w + 0.45:.3f},{H + 0.02:.3f}) {{permitted}};")
    for i, (c, lab) in enumerate(conds):
        yc = H - (i + 0.5) * rh
        bf = "\\bfseries" if c == "base" else ""
        L.append(f"\\node[anchor=east,font=\\sffamily\\tiny{bf}] at (-0.05,{yc:.3f}) {{{lab}}};")
        for cell, col, dy in (("repertoire", "OIblue", 0.07), ("audibility", "OIorange", -0.07)):
            v = pooled(c, cell)
            L.append(f"\\fill[{col}] (0,{yc + dy - 0.055:.3f}) rectangle ({X(v):.3f},{yc + dy + 0.055:.3f});"
                     f"\\node[anchor=west,font=\\sffamily\\tiny,text=black!70,inner sep=1pt] at ({X(v):.3f},{yc + dy:.3f}) {{{v:.0f}}};")
        L.append(f"\\node[font=\\sffamily\\tiny,text=black!60] at ({w + 0.45:.3f},{yc:.3f}) {{{pooled(c, 'control'):.0f}\\%}};")
    # (b)
    models = sorted(th, key=lambda m: -th[m]["thinking:audibility"]["baseline"])
    H2 = 0.27 * len(models)
    y0 = -H2 - 1.25
    L.append(f"\\begin{{scope}}[yshift={y0:.3f}cm]")
    L.append(f"\\node[panel] at (-2.1,{H2 + 0.5:.2f}) {{(b) Thinking off $\\rightarrow$ on}};")
    fl, X, _ = frame(w, H2, (0, 100), (0, 1), [0, 25, 50, 75, 100], [], "net use (pp)", grid="x")
    L += [l for l in fl if "anchor=east" not in l]
    for i, m in enumerate(models):
        yc = H2 - (i + 0.5) * 0.27
        L.append(f"\\node[anchor=east,font=\\sffamily\\tiny] at (-0.05,{yc:.3f}) {{{NAMES[m]}}};")
        for cell, col, dy in (("repertoire", "OIblue", 0.055), ("audibility", "OIorange", -0.055)):
            a, b = 100 * th[m][f"thinking:{cell}"]["baseline"], 100 * th[m][f"thinking:{cell}"]["value"]
            L.append(f"\\draw[{col}!45,line width=1.1pt] ({X(a):.3f},{yc + dy:.3f})--({X(b):.3f},{yc + dy:.3f});"
                     f"\\draw[{col},fill=white,line width=.5pt] ({X(a):.3f},{yc + dy:.3f}) circle (1.3pt);\\fill[{col}] ({X(b):.3f},{yc + dy:.3f}) circle (1.5pt);")
    L.append(r"\end{scope}")
    L += legend([("box", "OIblue", "cannot understand"), ("box", "OIorange", "cannot hear")], -1.2, y0 - 0.85)
    L += [r"\end{tikzpicture}",
          r"\caption{Why characters leak (Study 1 core cells). (a) Pooled net use as narrator, as author and with a perspective rule, against role-play, with permitted use at right. (b) Thinking off (circle) and on (dot).}",
          r"\label{fig:why}", r"\end{figure}"]
    return "\n".join(L)

ALL = {"FIG_EXAMPLE": example, "FIG_DESIGN": design, "FIG_S1": study1, "FIG_S2": study2, "FIG_FRONTIER": frontier, "FIG_REMEDY": remedy, "FIG_BRIDGEFULL": bridge_full, "FIG_S1M": listfirst_models, "FIG_FACTORS": factors, "FIG_WHY": why}

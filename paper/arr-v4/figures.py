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
COLORS = r"""\definecolor{OIblue}{HTML}{0072B2}\definecolor{OIorange}{HTML}{D55E00}\definecolor{OIgreen}{HTML}{009E73}
\definecolor{OIsky}{HTML}{56B4E9}\definecolor{OIpurple}{HTML}{CC79A7}\definecolor{OIgray}{HTML}{7F7F7F}"""


def load(p):
    return json.loads(Path(p).read_text())


def frame(w, h, xr, yr, xticks, yticks, xlabel="", ylabel="", grid="y", fmt=lambda v: f"{v:g}"):
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
    L += [f"\\node[anchor=east,font=\\sffamily\\tiny,text=black!70,inner sep=1.5pt] at (0,{Y(t):.3f}) {{{fmt(t)}}};" for t in yticks]
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
    return f"OIorange!{v * 0.9:.0f}!white", ("white" if v > 58 else "black!85")


def design():
    """Figure 2: measurement, how Study 1 states the boundary, and Study 2's four channels with the character view."""
    return r"""\begin{figure*}[t]
\centering
\begin{tikzpicture}[x=1cm,y=1cm,
  ver/.style={rounded corners=2pt,fill=#1,inner sep=3pt,text width=1.95cm,align=left,font=\sffamily\scriptsize},
  cell/.style={rounded corners=2pt,fill=#1,minimum width=1.5cm,minimum height=0.66cm,align=center,font=\sffamily\tiny,inner sep=1.5pt,text width=1.42cm},
  hd/.style={font=\sffamily\tiny\bfseries,text=black!55,align=center}]
%% (a) measurement
\node[panel] at (0,3.6) {(a) Counterfactual twins};
\node[ver=OIblue!12,anchor=north west] (a) at (0,3.15) {\textbf{Version A}\\the \textbf{coat} is by\\the \textbf{school}};
\node[ver=black!7,anchor=north west] (b) at (0,1.95) {\textbf{Version B}\\the \textbf{glove} is by\\the \textbf{church}};
\node[rounded corners=2pt,draw=black!25,fill=white,inner sep=3pt,text width=1.95cm,align=left,anchor=north west] (r) at (2.6,3.15) {\textbf{Reply to A}\\``He left the \textcolor{OIblue}{\textbf{coat}} by the \textcolor{OIblue}{\textbf{school}}.''};
\draw[black!45,-{Stealth[length=3.5pt]}] (a.east|-r.west)--(r.west);
\node[chip,fill=OIblue,anchor=north west,minimum width=2.25cm,align=left] (t) at (2.6,1.95) {target named \hfill 1};
\node[chip,fill=black!40,anchor=north west,minimum width=2.25cm,align=left] (f) at (2.6,1.55) {foil named \hfill 0};
\draw[black!35,densely dotted,-{Stealth[length=3pt]}] (b.east|-f.west)--(f.west);
\node[anchor=north west,font=\sffamily\scriptsize] at (2.6,1.1) {net use $D = 1 - 0$};
\node[anchor=north west,align=left,font=\sffamily\tiny,text=black!60,text width=4.7cm] at (0,0.55) {A guess such as ``check the basement'' scores in both versions and cancels.};
%% (b) Study 1
\begin{scope}[xshift=5.4cm]
\node[panel] at (0,3.6) {(b) Study 1: how the boundary is stated};
\node[hd] at (1.95,2.98) {in the\\state};
\node[hd] at (3.55,2.98) {per-utterance\\flag};
\node[hd] at (5.15,2.98) {flag and a\\sentence};
\node[anchor=east,align=right,font=\sffamily\tiny\bfseries] at (1.1,2.25) {\faLanguage\ cannot\\understand};
\node[anchor=east,align=right,font=\sffamily\tiny\bfseries] at (1.1,1.45) {\faDeaf\ cannot\\hear};
\node[cell=OIblue!12] at (1.95,2.25) {\texttt{speaks:}\\\texttt{[English]}};
\node[cell=OIsky!22] at (3.55,2.25) {\texttt{understood:}\\\texttt{false}};
\node[cell=OIgreen!15] at (5.15,2.25) {+ ``does not speak Japanese''};
\node[cell=black!4,text=black!35] at (1.95,1.45) {no analogue};
\node[cell=OIorange!14] at (3.55,1.45) {\texttt{audible:}\\\texttt{false}};
\node[cell=OIpurple!16] at (5.15,1.45) {+ ``could not hear them''};
\node[anchor=north west,font=\sffamily\tiny,text=black!60,text width=5.7cm,align=left] at (0.0,0.95) {Speech is in Chinese, Japanese or Spanish, or in English marked inaudible. Controls make the same speech accessible.};
\end{scope}
%% (c) Study 2
\begin{scope}[xshift=11.5cm]
\node[panel] at (0,3.6) {(c) Study 2: four channels};
\foreach \x/\y/\ic/\ch/\full/\view in {0/3.1/\faDeaf/Hear/speech out of earshot/nothing,
  2.22/3.1/\faLanguage/Understand/speech in Japanese/Casey speaks Japanese,
  0/1.48/\faEyeSlash/See/an object is hidden/Alex puts something away,
  2.22/1.48/\faEnvelope/Receive/a private message/Alex sends a message}{
  \node[anchor=north west,rounded corners=2pt,fill=black!3,inner sep=3pt,text width=1.95cm,minimum height=1.3cm,align=left,font=\sffamily\tiny] at (\x,\y)
    {{\color{OIorange}\footnotesize\ic}\ \textbf{\ch}\\[1pt]hidden: \full\\[1pt]\textcolor{OIgreen}{view: \view}};
}
\end{scope}
\end{tikzpicture}
\caption{Design. (a) Every scene has two versions that differ only in a hidden object and place, and a reply is scored for both. (b) Study 1 states the boundary in five ways, matched within each row. (c) Study 2 hides content through four channels. The character view replaces each hidden event with what the character can still observe.}
\label{fig:design}
\end{figure*}"""


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
    L.append(r"\begin{scope}[xshift=5.25cm]")
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
    """Figure 5: frontier models and input format."""
    op = load(RA / "open_content_only.json")
    ho = load(RA / "hosted.json")
    rs = load(RA / "hosted_reasoning.json")
    H = 3.3
    L = [r"\begin{figure*}[t]", r"\centering", r"\begin{tikzpicture}[x=1cm,y=1cm]"]
    # (a) dumbbell of core cells
    rows = []
    for m in ["gpt6sol", "gemini38flash", "grok47", "opus55", "gemini31pro", "sonnet55"]:
        s1 = ho[m]["study1"]
        rows.append(("Hosted", NAMES[m], s1["repertoire"], s1["inaudible_flag"], s1["fluent_control_use"]))
    rows.append(("Hosted", "Sonnet 5.5, high reas.", rs["sonnet55-high"]["net"], None, None))
    s1 = ho["deepseekv4pro"]["study1"]
    rows.append(("Open", NAMES["deepseekv4pro"], s1["repertoire"], s1["inaudible_flag"], s1["fluent_control_use"]))
    mean = lambda k: sum(v[k] for v in op.values()) / len(op)
    rows.append(("Open", "11 open, $\\le$40B", mean("repertoire"), mean("inaudible_flag"), mean("fluent_control_use")))
    n = len(rows)
    rh = H / (n + 0.6)
    w = 2.5
    L.append(f"\\node[panel] at (-2.1,{H + 0.75:.2f}) {{(a) Study 1 core cells}};")
    fl, X, _ = frame(w, H, (0, 100), (0, 1), [0, 25, 50, 75, 100], [], "net use / control use (\\%)", grid="x")
    L += [l for l in fl if "anchor=east" not in l]
    for i, (g, name, rep, aud, ctl) in enumerate(rows):
        y = H - (i + 0.8) * rh - (0.18 if g == "Open" else 0)
        it = "\\itshape" if "reas." in name else ""
        L.append(f"\\node[anchor=east,font=\\sffamily\\tiny{it}] at (-0.05,{y:.3f}) {{{name}}};")
        pts = [v for v in (rep, aud) if v is not None]
        if len(pts) == 2:
            L.append(f"\\draw[black!25,line width=1.2pt] ({X(100 * min(pts)):.3f},{y:.3f})--({X(100 * max(pts)):.3f},{y:.3f});")
        if ctl is not None:
            L.append(f"\\node[OIgray,inner sep=0pt] at ({X(100 * ctl):.3f},{y:.3f}) {{\\pgfuseplotmark{{diamond}}}};")
        L.append(f"\\node[OIblue,inner sep=0pt] at ({X(max(0, 100 * rep)):.3f},{y:.3f}) {{\\pgfuseplotmark{{*}}}};")
        if aud is not None:
            L.append(f"\\node[OIorange,inner sep=0pt] at ({X(max(0, 100 * aud)):.3f},{y:.3f}) {{\\pgfuseplotmark{{triangle*}}}};")
    ysep = H - (7 + 0.8) * rh + rh / 2 - 0.09
    L.append(f"\\draw[black!20,dashed] (-2.0,{ysep:.3f})--({w},{ysep:.3f});")
    L += legend([("*", "OIblue", "repertoire"), ("triangle*", "OIorange", "audibility flag"), ("diamond", "OIgray", "fluent control")], -2.0, -0.85)
    # (b) bridge slope chart
    br = load(RA / "bridge.json")
    pts = {m: (100 * br[m]["base:inaccessible"]["estimate"], 100 * br[m]["all:inaccessible"]["estimate"]) for m in ("gemma4_31b", "qwen38_27b")}
    for m in ("deepseekv4pro", "sonnet55", "gemini31pro", "opus55", "grok47", "gemini38flash", "gpt6sol"):
        b = ho[m]["bridge"]
        pts[m] = (100 * b["base"]["unheard_net"], 100 * b["all"]["unheard_net"])
    flat = [m for m, (a, b) in pts.items() if a < 3 and b < 3]
    L.append(r"\begin{scope}[xshift=3.75cm]")
    L.append(f"\\node[panel] at (-0.45,{H + 0.75:.2f}) {{(b) All four Study 1 features}};")
    w = 1.1
    fl, X, Y = frame(w, H, (0, 1), (0, 100), [], [0, 25, 50, 75, 100], "", "net use of unheard speech (pp)")
    L += fl
    L.append(f"\\node[anchor=north,font=\\sffamily\\tiny,align=center] at (0,-0.02) {{Study 2\\\\prompt}};\\node[anchor=north,font=\\sffamily\\tiny,align=center] at ({w},-0.02) {{+ all\\\\four}};")
    ends = []
    for m, (a, b) in pts.items():
        col = "black!30" if m in flat else ("OIorange" if m in ("gemma4_31b", "qwen38_27b", "deepseekv4pro") else "OIblue")
        L.append(f"\\draw[{col},line width=.9pt] (0,{Y(a):.3f})--({w},{Y(b):.3f});\\fill[{col}] (0,{Y(a):.3f}) circle (1.4pt);\\fill[{col}] ({w},{Y(b):.3f}) circle (1.4pt);")
        if m not in flat:
            ends.append([Y(b), NAMES[m].replace("Claude ", ""), col])
    ends.append([Y(0), f"{len(flat)} hosted near 0", "black!45"])
    ends.sort()
    for k in range(1, len(ends)):
        ends[k][0] = max(ends[k][0], ends[k - 1][0] + 0.2)
    for yv, name, col in ends:
        L.append(f"\\node[anchor=west,font=\\sffamily\\tiny,text={col}] at ({w + 0.06:.3f},{yv:.3f}) {{{name}}};")
    L.append(r"\end{scope}")
    # (c) single swaps, discovery and new scenes
    rep = load(RA / "bridge-replication.json")
    swaps = [("sys", "Sys."), ("card", "Sheet"), ("schema", "State"), ("ask", "Quest.")]
    L.append(r"\begin{scope}[xshift=7.4cm]")
    L.append(f"\\node[panel] at (-0.45,{H + 0.75:.2f}) {{(c) One feature at a time}};")
    hh = (H - 0.35) / 2
    for k, m in enumerate(("gemma4_31b", "qwen38_27b")):
        y0 = (1 - k) * (hh + 0.35)
        L.append(f"\\begin{{scope}}[yshift={y0:.3f}cm]")
        fl, X, Y = frame(2.45, hh - 0.18, (0, 4), (0, 100), [], [0, 50, 100], "", "")
        L += fl
        L.append(f"\\node[anchor=south west,font=\\sffamily\\tiny\\bfseries] at (0.02,{hh - 0.2:.3f}) {{{NAMES[m]}, net use (pp)}};")
        for j, (sw, lab) in enumerate(swaps):
            for d, (data, col, dx) in enumerate(((br, "OIorange!45", -0.11), (rep, "OIorange", 0.11))):
                v = 100 * data[m][f"{sw}:inaccessible"]["estimate"]
                L.append(f"\\fill[{col}] ({X(j + 0.5) + dx - 0.1:.3f},0) rectangle ({X(j + 0.5) + dx + 0.1:.3f},{Y(max(v, 0.6)):.3f});")
            if k == 1:
                L.append(f"\\node[anchor=north,font=\\sffamily\\tiny] at ({X(j + 0.5):.3f},-0.02) {{{lab}}};")
        L.append(r"\end{scope}")
    L += legend([("box", "OIorange!45", "discovery"), ("box", "OIorange", "new scenes")], 0.0, -0.56)
    L.append(r"\end{scope}")
    # (d) framing of leaks
    fr = load(RA / "leak_framing.json")
    opn = [m for m in op if fr[m]["n"]]
    tot = sum(fr[m]["n"] for m in opn)
    pooled = {k: sum(fr[m][k] * fr[m]["n"] for m in opn) / tot for k in ("unframed", "attributed", "tentative")}
    bars = [("11 open models", pooled), (NAMES["deepseekv4pro"], fr["deepseekv4pro"]), ("Sonnet 5.5", fr["sonnet55"])]
    cols = [("unframed", "OIblue", "fact"), ("attributed", "OIsky", "attributed"), ("tentative", "OIorange", "guess")]
    L.append(r"\begin{scope}[xshift=11.5cm]")
    L.append(f"\\node[panel] at (-1.3,{H + 0.75:.2f}) {{(d) How leaks are phrased}};")
    w = 2.0
    fl, X, Y = frame(w, H, (0, 100), (0, 3), [0, 50, 100], [], "share of leaks (\\%)", grid="x")
    L += [l for l in fl if "anchor=east" not in l]
    for i, (name, f) in enumerate(bars):
        yc = Y(2.5 - i)
        L.append(f"\\node[anchor=east,font=\\sffamily\\tiny,align=right,text width=1.2cm] at (-0.05,{yc:.3f}) {{{name}}};")
        x = 0
        for k, c, _ in cols:
            L.append(f"\\fill[{c}] ({X(x):.3f},{yc - 0.22:.3f}) rectangle ({X(x + 100 * f[k]):.3f},{yc + 0.22:.3f});")
            x += 100 * f[k]
    L += legend([("box", c, lab) for _, c, lab in cols], -1.15, -0.9)
    L.append(r"\end{scope}")
    L += [r"\end{tikzpicture}",
          r"\caption{Frontier models and input format. (a) Study 1 core cells with the content question (288 items per cell). Five of six hosted models keep the boundary while using permitted content, and high reasoning effort brings Claude Sonnet 5.5 close to zero. (b) Swapping all four Study 1 features into Study 2's hearing prompts. (c) Swapping one feature at a time, on the discovery scenes and on 96 new scenes. A different feature breaks each model, and both effects replicate. (d) The strongest leaking models present the content as a guess.}",
          r"\label{fig:frontier}", r"\end{figure*}"]
    return "\n".join(L)


def remedy():
    """Figure 6: (a) the list-first prompt, (b) leakage against permitted use for five methods, (c) awareness of the event."""
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
    # (b) trade-off
    est = load(ROOT / "analysis/h200-v2-20261002/method-six-descriptive-results.json")["descriptive_estimates"]
    v = {(r["boundary"], r["method"], r["metric"]): 100 * r["estimate"] for r in est}
    meth = [("full", "OIorange", "full context"), ("prose", "OIpurple", "flag + prose"), ("self_filter", "OIsky", "self-filter"),
            ("hard", "black!45", "remove event"), ("view", "OIgreen", "character view")]
    marks = {"Hear": "triangle*", "Understand": "*", "See": "square*", "Receive": "diamond*"}
    L.append(r"\begin{scope}[xshift=5.05cm]")
    w = 4.3
    L.append(f"\\node[panel] at (-0.75,{H + 0.55:.2f}) {{(b) Leakage against permitted use, Study 2}};")
    fl, X, Y = frame(w, H, (50, 100), (0, 60), [50, 60, 70, 80, 90, 100], [0, 20, 40, 60],
                     "use of permitted content (\\%)", "net use of hidden content (pp)", grid="xy")
    L += fl
    L.append(f"\\fill[OIgreen!8] ({X(85):.3f},0) rectangle ({X(100):.3f},{Y(8):.3f});")
    L.append(f"\\node[anchor=south east,font=\\sffamily\\tiny,text=OIgreen!70!black] at ({X(99.5):.3f},{Y(8):.3f}) {{target region}};")
    for c, mk in marks.items():
        f, vw = v[(c, "full", "hit_t")], v[(c, "view", "hit_t")]
        L.append(f"\\draw[black!15,line width=.5pt] ({X(f):.3f},{Y(v[(c, 'full', 'D')]):.3f})--({X(vw):.3f},{Y(max(0, v[(c, 'view', 'D')])):.3f});")
    for m, col, _ in meth:
        for c, mk in marks.items():
            L.append(f"\\node[{col},inner sep=0pt,opacity=.92] at ({X(v[(c, m, 'hit_t')]):.3f},{Y(max(0, v[(c, m, 'D')])):.3f}) {{\\pgfuseplotmark{{{mk}}}}};")
    L += legend([("box", col, lab) for _, col, lab in meth[:3]], 0.0, -0.85)
    L += legend([("box", col, lab) for _, col, lab in meth[3:]], 0.0, -1.1)
    L += legend([(mk, "black!60", c) for c, mk in marks.items()], 0.0, -1.35, step=0.09)
    L.append(r"\end{scope}")
    # (c) awareness
    pd = [l.split(",") for l in (ROOT / "paper/arr/figures/plot-data.csv").read_text().splitlines()[1:]]
    aw = {r[3]: tuple(100 * float(x) for x in r[7:10]) for r in pd if r[0] == "confirmatory_partial_awareness" and r[6] == "awareness_correct"}
    L.append(r"\begin{scope}[xshift=11.95cm]")
    w = 2.6
    L.append(f"\\node[panel] at (-0.75,{H + 0.55:.2f}) {{(c) Character notices the event}};")
    fl, X, Y = frame(w, H, (0, 3), (0, 100), [], [0, 25, 50, 75, 100], "", "correct awareness (\\%)")
    L += fl
    for k, (m, col, labt) in enumerate((("full", "OIorange", "full\\\\context"), ("hard", "black!45", "remove\\\\event"), ("view", "OIgreen", "character\\\\view"))):
        val, lo, hi = aw[m]
        L.append(f"\\fill[{col}] ({X(k + 0.5) - 0.32:.3f},0) rectangle ({X(k + 0.5) + 0.32:.3f},{Y(val):.3f});"
                 f"\\draw[black!60,line width=.35pt] ({X(k + 0.5):.3f},{Y(lo):.3f})--({X(k + 0.5):.3f},{Y(hi):.3f});"
                 f"\\node[anchor=north,font=\\sffamily\\tiny\\bfseries,text=white] at ({X(k + 0.5):.3f},{Y(val) - 0.02:.3f}) {{{val:.0f}}};"
                 f"\\node[anchor=north,font=\\sffamily\\tiny,align=center] at ({X(k + 0.5):.3f},-0.03) {{{labt}}};")
    L.append(r"\end{scope}")
    L += [r"\end{tikzpicture}",
          r"\caption{Remedies. (a) The list-first prompt in Study 1. Each point is one model and boundary, and models whose first-step list omits the hidden values also leave them out of the answer. (b) Five methods in Study 2 (six models, 48 scenes, one point per channel), with lines joining full context to the character view. Self-filtering lowers leakage but also drops permitted content. (c) Whether the character reports that an event happened (four models, 96 scenes). Removing the event stops leakage, but the character can then no longer tell that anything happened.}",
          r"\label{fig:remedy}", r"\end{figure*}"]
    return "\n".join(L)


def example():
    """Figure 1: one Study 1 item drawn as a scene, with verbatim replies from Gemma-4-31B."""
    return r"""\begin{figure}[t]
\centering
\begin{tikzpicture}[x=1cm,y=1cm,
  bubble/.style={rectangle callout,rounded corners=3pt,fill=#1,inner sep=3pt,align=left,font=\sffamily\scriptsize},
  reply/.style={rounded corners=3pt,draw=#1,line width=.6pt,fill=white,inner sep=3.5pt,text width=5.15cm,align=left,font=\sffamily\scriptsize},
  tag/.style={rounded corners=1.5pt,fill=#1,text=white,font=\sffamily\tiny\bfseries,inner sep=2pt,minimum width=1.9cm,align=center}]
% scene backdrop
\fill[black!3,rounded corners=4pt] (0,2.05) rectangle (7.6,5.3);
\node[font=\sffamily\tiny\bfseries,text=black!45,anchor=north west] at (0.12,5.22) {SCENE};
% mechanics
\node[text=black!55,font=\Large] (m1) at (0.55,3.0) {\faUserCog};
\node[text=black!40,font=\Large] (m2) at (1.25,3.0) {\faUserCog};
\node[font=\sffamily\tiny,text=black!55] at (0.9,2.45) {two mechanics};
\node[bubble=black!10,callout absolute pointer={(1.0,3.3)}] at (1.65,4.15) {\emph{¿Dónde está el espejo?}\\\emph{En el almacén. No se lo}\\\emph{digas a nadie.}};
% Panam
\node[text=OIblue,font=\Large] (pn) at (4.55,3.0) {\faUser};
\node[font=\sffamily\tiny\bfseries,text=OIblue] at (4.55,2.45) {Panam};
\node[rounded corners=1.5pt,draw=OIblue,text=OIblue,font=\sffamily\tiny,inner sep=1.5pt,align=center] at (4.3,4.3) {\faLanguage\ speaks\\only English};
\draw[OIblue!60,line width=.5pt,-{Stealth[length=3pt]}] (4.4,3.98)--(4.52,3.35);
% companion
\node[text=black!60,font=\Large] (v) at (6.85,3.0) {\faUser};
\node[font=\sffamily\tiny,text=black!55] at (6.85,2.45) {companion};
\node[bubble=OIsky!25,callout absolute pointer={(6.8,3.3)}] at (6.6,4.3) {What were\\those two\\saying?};
% generator
\draw[black!35,line width=.6pt,-{Stealth[length=4pt]}] (3.8,2.05)--(3.8,1.62);
\node[font=\sffamily\scriptsize,text=black!70] at (3.8,1.42) {\faRobot\ \ the model voices Panam and reads the full state};
% replies
\node[reply=OIorange,anchor=north west] (r1) at (2.2,1.15) {``Just some boring shit about a \leak{mirror} being in the \leak{warehouse}. Don't worry about it.''};
\node[tag=OIorange,anchor=east] at (2.05,0.83) {\faTimes\ Version A\\mirror, warehouse};
\node[reply=OIorange,anchor=north west] (r2) at (2.2,0.28) {``Something about a \leak{chair} being in a \leak{church}. Weird as hell, right?''};
\node[tag=OIorange,anchor=east] at (2.05,-0.0) {\faTimes\ Version B\\chair, church};
\node[reply=OIgreen,anchor=north west] (r3) at (2.2,-0.6) {``Don't look at me, V. I didn't catch a damn word of it.''};
\node[tag=OIgreen,anchor=east] at (2.05,-0.86) {\faCheck\ A + flag\\understood: false};
\end{tikzpicture}
\caption{Gemma-4-31B voicing a character who does not speak Spanish. The reply tracks the hidden object and place when version B swaps them, and a per-utterance flag stops the leak. Replies are verbatim.}
\label{fig:example}
\end{figure}"""


ALL = {"FIG_EXAMPLE": example, "FIG_DESIGN": design, "FIG_S1": study1, "FIG_S2": study2, "FIG_FRONTIER": frontier, "FIG_REMEDY": remedy}

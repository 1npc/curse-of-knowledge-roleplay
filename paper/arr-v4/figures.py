"""TikZ figures for the two-study manuscript, generated from saved results (standard library only).

Every number drawn here is read from a results file; nothing is typed by hand except labels.
Colors follow Okabe-Ito: blue = cannot understand, orange = cannot hear, green = stated in prose or
character view, sky = per-utterance comprehension flag, gray = accessible control.
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


def design():
    """Figure 2: counterfactual twins and the matched conditions of Study 1."""
    return r"""\begin{figure}[t]
\centering
\begin{tikzpicture}[x=1cm,y=1cm,box/.style={draw=black!35,rounded corners=1.5pt,align=center,inner sep=2pt,font=\scriptsize}]
\node[box,fill=OIblue!8,text width=2.2cm] (a) at (0,1.1) {Version A\\ \emph{coat} by the \emph{school}};
\node[box,fill=OIorange!8,text width=2.2cm] (b) at (0,0.3) {Version B\\ \emph{glove} by the \emph{church}};
\node[box,text width=1.75cm] (r) at (2.75,0.7) {Reply to\\ version A};
\node[box,text width=2.1cm] (d) at (5.3,0.7) {$D = I(\text{A named})$\\ $-\,I(\text{B named})$};
\draw[-latex,black!60] (a.east) -- (r.west);
\draw[-latex,black!60] (r.east) -- (d.west);
\draw[densely dotted,-latex,black!45] (b.east) to[out=0,in=225] node[below,font=\tiny,pos=.55]{scored as foil} (d.south west);
\begin{scope}[yshift=-0.95cm]
\node[font=\scriptsize\bfseries,align=center] at (2.05,0) {Repertoire};
\node[font=\scriptsize\bfseries,align=center] at (3.85,0) {Flag};
\node[font=\scriptsize\bfseries,align=center] at (5.65,0) {Flag and prose};
\node[font=\scriptsize\bfseries,anchor=east,align=right] at (1.15,-0.55) {Cannot\\ understand};
\node[font=\scriptsize\bfseries,anchor=east,align=right] at (1.15,-1.35) {Cannot\\ hear};
\node[box,fill=OIblue!10,text width=1.5cm,minimum height=0.68cm] at (2.05,-0.55) {knows English, speech in Japanese};
\node[box,fill=OIsky!18,text width=1.5cm,minimum height=0.68cm] at (3.85,-0.55) {understood\\ = false};
\node[box,fill=OIgreen!12,text width=1.5cm,minimum height=0.68cm] at (5.65,-0.55) {``does not speak Japanese''};
\node[box,fill=black!3,text width=1.5cm,minimum height=0.68cm,text=black!45] at (2.05,-1.35) {no analogue};
\node[box,fill=OIorange!12,text width=1.5cm,minimum height=0.68cm] at (3.85,-1.35) {audible\\ = false};
\node[box,fill=OIgreen!12,text width=1.5cm,minimum height=0.68cm] at (5.65,-1.35) {``could not hear''};
\end{scope}
\end{tikzpicture}
\caption{Measurement. Each scene has two versions that differ only in a hidden object and place. A reply to version A is scored for A's values and for B's, so plausible guesses cancel in net use $D$ (top). The boundary is stated in one of five ways (bottom), and controls make the same speech accessible.}
\label{fig:design}
\end{figure}"""


def study1():
    """Figure 3: per-model leakage in Study 1 under five ways of stating the boundary."""
    models = sorted(load(R1 / "model_metrics.json"), key=lambda r: r["language"]["point"])
    specs = [("language", "OIblue", "*", "Repertoire only"), ("flag_understand", "OIsky", "square*", "Comprehension flag"),
             ("flag_inaudible", "OIorange", "triangle*", "Audibility flag"), ("narrated_inaudible", "OIpurple", "diamond*", "Flag and narration"),
             ("language_prose", "OIgreen", "pentagon*", "Repertoire and prose")]
    lines = [r"\begin{figure*}[t]", r"\centering", r"\begin{tikzpicture}[x=0.118cm,y=0.39cm,font=\footnotesize]"]
    n = len(models)
    for x in range(0, 101, 20):
        lines.append(f"\\draw[black!12] ({x},-0.6)--({x},{n - 0.4});\\node[anchor=north,font=\\scriptsize] at ({x},-0.6) {{{x}}};")
    for i, r in enumerate(models):
        y = i
        lines.append(f"\\node[anchor=east] at (-2,{y}) {{{NAMES[r['model']]}}};")
        for j, (k, c, mk, _) in enumerate(specs):
            yy = y + (2 - j) * 0.13
            v = 100 * r[k]["point"]
            lo, hi = [100 * a for a in r[k]["ci95"]]
            lines.append(f"\\draw[{c},line width=.5pt] ({lo:.2f},{yy:.2f})--({hi:.2f},{yy:.2f});"
                         f"\\node[{c},inner sep=0pt,font=\\tiny] at ({v:.2f},{yy:.2f}) {{\\pgfuseplotmark{{{mk}}}}};")
    lines.append(r"\node[anchor=north] at (50,-1.45) {Net use of inaccessible content (pp)};")
    xs = [0, 19, 40, 61, 86]
    for j, (_, c, mk, lab) in enumerate(specs):
        lines.append(f"\\node[{c},inner sep=0pt] at ({xs[j]},{n + 0.3}) {{\\pgfuseplotmark{{{mk}}}}};\\node[anchor=west,font=\\scriptsize] at ({xs[j] + 1.2},{n + 0.3}) {{{lab}}};")
    lines += [r"\end{tikzpicture}",
              r"\caption{Study 1. Net use of speech the character cannot understand or cannot hear, for 11 open models, under five ways of stating the boundary. Bars are 95\% skeleton-bootstrap intervals over 96 scene skeletons and three languages.}",
              r"\label{fig:s1}", r"\end{figure*}"]
    return "\n".join(lines)


def study2():
    """Figure 4: (a) leakage per model and channel in the confirmation set, (b) effect on search choices."""
    ext = load(RA / "v2-extension.json")["per_model_full_context"]
    order = sorted(ext, key=lambda m: sum(ext[m].values()))
    ch = ["Hear", "Understand", "See", "Receive"]
    L = [r"\begin{figure*}[t]", r"\centering", r"\begin{tikzpicture}[font=\footnotesize]",
         r"\begin{scope}[x=1.15cm,y=0.36cm]"]
    for j, c in enumerate(ch):
        L.append(f"\\node[font=\\scriptsize\\bfseries] at ({j + 0.5},{len(order) + 0.55}) {{{c}}};")
    for i, m in enumerate(order):
        L.append(f"\\node[anchor=east,font=\\scriptsize] at (-0.08,{i + 0.5}) {{{NAMES[m]}}};")
        for j, c in enumerate(ch):
            v = max(0.0, 100 * ext[m][c])
            txt = "white" if v > 55 else "black"
            L.append(f"\\fill[OIorange!{v * 0.85:.0f}!white] ({j},{i}) rectangle ({j + 1},{i + 1});"
                     f"\\node[{txt},font=\\scriptsize] at ({j + 0.5},{i + 0.5}) {{{v:.0f}}};")
    L.append(f"\\draw[black!25] (0,0) rectangle (4,{len(order)});")
    L.append(f"\\node[font=\\scriptsize] at (2,-0.9) {{(a) Net use under full context (pp)}};")
    L.append(r"\end{scope}")
    rows = [l.split(",") for l in (ROOT / "paper/arr/figures/plot-data.csv").read_text().splitlines()[1:] if l.startswith("decision,")]
    dec = {(r[2], r[3]): (float(r[7]), float(r[8]), float(r[9])) for r in rows}
    L.append(r"\begin{scope}[xshift=7.6cm,x=0.052cm,y=0.95cm]")
    for x in range(0, 81, 20):
        L.append(f"\\draw[black!12] ({x},-0.45)--({x},3.55);\\node[anchor=north,font=\\scriptsize] at ({x},-0.45) {{{x}}};")
    for i, c in enumerate(reversed(ch)):
        L.append(f"\\node[anchor=east,font=\\scriptsize] at (-2,{i}) {{{c}}};")
        for k, (meth, col, dy) in enumerate((("full", "OIorange", 0.17), ("view", "OIgreen", -0.17))):
            v, lo, hi = [100 * a for a in dec[(c, meth)]]
            L.append(f"\\fill[{col}] (0,{i + dy - 0.12}) rectangle ({v:.1f},{i + dy + 0.12});"
                     f"\\draw[black!70] ({lo:.1f},{i + dy})--({hi:.1f},{i + dy});")
    L.append(r"\fill[OIorange] (52,3.95) rectangle (55,4.15);\node[anchor=west,font=\scriptsize] at (56,4.05) {Full context};")
    L.append(r"\fill[OIgreen] (52,3.55) rectangle (55,3.75);\node[anchor=west,font=\scriptsize] at (56,3.65) {Character view};")
    L.append(r"\node[font=\scriptsize,align=center] at (40,-1.45) {(b) Change in choosing place A when the\\ inaccessible fact switches from B to A (pp)};")
    L.append(r"\end{scope}")
    L += [r"\end{tikzpicture}", r"\par\medskip", s2_detail(embed=True),
          r"\caption{Study 2. (a) Net use of inaccessible content in the confirmation set (96 scenes with original characters) for all 11 open models, by channel. (b) Four models choosing where to search between two places. Leaked facts move choices under full context and not under the character view. (c) How the state representation changes leakage relative to a direct access flag (11 models, 24 scenes). A prose rule lowers leakage in every channel except comprehension. (d) Leakage after two and four scripted exchanges (four models, 32 scenes). Bars are 95\% bootstrap intervals.}",
          r"\label{fig:s2}", r"\end{figure*}"]
    return "\n".join(L)


def frontier():
    """Figure 5: (a) Study 1 core cells for open and hosted models, (b) bridge from Study 2's prompt to Study 1's features."""
    op = load(RA / "open_content_only.json")
    ho = load(RA / "hosted.json")
    rows = []
    for m, v in op.items():
        rows.append(("Open, at most 40B", m, v["repertoire"], v["inaudible_flag"], v["fluent_control_use"]))
    for m in ["deepseekv4pro", "sonnet55", "gemini31pro", "opus55", "grok47", "gemini38flash", "gpt6sol"]:
        s = ho[m]["study1"]
        grp = "Open, large" if m == "deepseekv4pro" else "Hosted"
        rows.append((grp, m, s["repertoire"], s["inaudible_flag"], s["fluent_control_use"]))
    groups = ["Hosted", "Open, large", "Open, at most 40B"]
    rows.sort(key=lambda r: (groups.index(r[0]), -(r[2] + r[3])))
    L = [r"\begin{figure*}[t]", r"\centering", r"\begin{tikzpicture}[font=\footnotesize]", r"\begin{scope}[x=0.050cm,y=0.29cm]"]
    y = 0
    ys = []
    prev = None
    for g, m, rep, aud, ctl in reversed(rows):
        if prev is not None and g != prev:
            y += 0.7
        ys.append((y, g, m, rep, aud, ctl))
        prev = g
        y += 1
    top = y
    for x in range(0, 101, 25):
        L.append(f"\\draw[black!12] ({x},-0.7)--({x},{top - 0.3});\\node[anchor=north,font=\\scriptsize] at ({x},-0.7) {{{x}}};")
    for yy, g, m, rep, aud, ctl in ys:
        L.append(f"\\node[anchor=east,font=\\scriptsize] at (-2,{yy}) {{{NAMES[m]}}};")
        L.append(f"\\node[OIgray,inner sep=0pt] at ({100 * ctl:.1f},{yy}) {{\\pgfuseplotmark{{diamond}}}};")
        L.append(f"\\node[OIblue,inner sep=0pt] at ({max(0, 100 * rep):.1f},{yy}) {{\\pgfuseplotmark{{*}}}};")
        L.append(f"\\node[OIorange,inner sep=0pt] at ({max(0, 100 * aud):.1f},{yy}) {{\\pgfuseplotmark{{triangle*}}}};")
    for g in groups:
        gy = [yy for yy, gg, *_ in ys if gg == g]
        L.append(f"\\draw[black!40] (103,{min(gy) - 0.3})--(103,{max(gy) + 0.3});"
                 f"\\node[anchor=west,font=\\scriptsize,rotate=0,text width=1.1cm] at (104,{(min(gy) + max(gy)) / 2}) {{{g}}};")
    L.append(f"\\node[font=\\scriptsize] at (50,-2.6) {{(a) Net use or control use (\\%)}};")
    L.append(f"\\node[OIblue,inner sep=0pt] at (2,{top + 0.6}) {{\\pgfuseplotmark{{*}}}};\\node[anchor=west,font=\\scriptsize] at (4,{top + 0.6}) {{Repertoire only}};")
    L.append(f"\\node[OIorange,inner sep=0pt] at (42,{top + 0.6}) {{\\pgfuseplotmark{{triangle*}}}};\\node[anchor=west,font=\\scriptsize] at (44,{top + 0.6}) {{Audibility flag}};")
    L.append(f"\\node[OIgray,inner sep=0pt] at (82,{top + 0.6}) {{\\pgfuseplotmark{{diamond}}}};\\node[anchor=west,font=\\scriptsize] at (84,{top + 0.6}) {{Fluent control}};")
    L.append(r"\end{scope}")
    br = load(RA / "bridge.json")
    pts = {m: (100 * br[m]["base:inaccessible"]["estimate"], 100 * br[m]["all:inaccessible"]["estimate"]) for m in ("gemma4_31b", "qwen38_27b", "phi4")}
    for m in ("deepseekv4pro", "sonnet55", "gemini31pro", "opus55", "grok47", "gemini38flash", "gpt6sol"):
        b = ho[m]["bridge"]
        pts[m] = (100 * b["base"]["unheard_net"], 100 * b["all"]["unheard_net"])
    flat = [m for m, (a, b) in pts.items() if a < 3 and b < 3]
    L.append(r"\begin{scope}[xshift=8.5cm,x=2.9cm,y=0.042cm]")
    for v in range(0, 101, 25):
        L.append(f"\\draw[black!12] (0,{v})--(1,{v});\\node[anchor=east,font=\\scriptsize] at (-0.03,{v}) {{{v}}};")
    L.append(r"\node[anchor=north,font=\scriptsize,align=center] at (0,-4) {Study 2\\ prompt};\node[anchor=north,font=\scriptsize,align=center] at (1,-4) {Study 1\\ features};")
    ends = []
    for m, (a, b) in pts.items():
        col = "black!35" if m in flat else ("OIorange" if m in ("gemma4_31b", "qwen38_27b", "phi4", "deepseekv4pro") else "OIblue")
        L.append(f"\\draw[{col},line width=.8pt] (0,{a:.1f})--(1,{b:.1f});\\fill[{col}] (0,{a:.1f}) circle (1.3pt);\\fill[{col}] (1,{b:.1f}) circle (1.3pt);")
        if m not in flat:
            ends.append([b, NAMES[m], col])
    ends.sort()
    for i in range(1, len(ends)):  # keep labels at least 6 units apart
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 6.5)
    for yv, name, col in ends:
        L.append(f"\\node[anchor=west,font=\\scriptsize,text={col}] at (1.03,{yv:.1f}) {{{name}}};")
    L.append(f"\\node[anchor=west,font=\\scriptsize,text=black!50,align=left] at (1.03,{-1 if not ends or ends[0][0] > 9 else -7}) {{{len(flat)} hosted models\\\\ stay below 2}};")
    L.append(r"\node[font=\scriptsize,align=center] at (0.55,-26) {(b) Net use of unheard speech (pp)};")
    L.append(r"\end{scope}")
    L += [r"\end{tikzpicture}",
          r"\caption{Frontier models and input format. (a) Study 1 core cells with the content question (288 items per cell). Five of six hosted models almost never use the hidden content while using permitted content in about 99\% of replies. (b) Swapping Study 1's system prompt, character sheet, state layout and question into Study 2's hearing prompts. Orange lines are open models, blue lines hosted models.}",
          r"\label{fig:frontier}", r"\end{figure*}"]
    return "\n".join(L)


def remedy():
    """Figure 6: leakage after the perspective filter against leakage in its first-step list."""
    models = load(R1 / "model_metrics.json")
    L = [r"\begin{figure}[t]", r"\centering", r"\begin{tikzpicture}[x=0.058cm,y=0.028cm,font=\footnotesize]"]
    for v in range(0, 101, 25):
        L.append(f"\\draw[black!12] ({v},0)--({v},100);\\draw[black!12] (0,{v})--(100,{v});"
                 f"\\node[anchor=north,font=\\scriptsize] at ({v},-2) {{{v}}};\\node[anchor=east,font=\\scriptsize] at (-2,{v}) {{{v}}};")
    labels = {"glm47_flash", "qwen35_9b", "mistral_small3"}
    for r in models:
        for key, col, mk in (("language", "OIblue", "*"), ("inaudible", "OIorange", "triangle*")):
            x, y = 100 * r[f"step1_{key}"]["point"], max(0, 100 * r[f"m1g_{key}"]["point"])
            L.append(f"\\node[{col},inner sep=0pt] at ({x:.1f},{y:.1f}) {{\\pgfuseplotmark{{{mk}}}}};")
            if r["model"] in labels and (key == "language" or r["model"] != "mistral_small3"):
                anchor = "west" if r["model"] == "mistral_small3" else "south east"
                dx, dy = (2.0, 0.0) if anchor == "west" else (0.0, 1.5)
                L.append(f"\\node[anchor={anchor},font=\\tiny,text=black!70] at ({x + dx:.1f},{y + dy:.1f}) {{{NAMES[r['model']]}}};")
    L.append(r"\node[anchor=north] at (50,-11) {Hidden values named in the first-step list (\%)};")
    L.append(r"\node[rotate=90,anchor=south] at (-15,50) {Net use after list-first prompt (pp)};")
    L.append(r"\node[OIblue,inner sep=0pt] at (6,93) {\pgfuseplotmark{*}};\node[anchor=west,font=\scriptsize] at (8,93) {Cannot understand};")
    L.append(r"\node[OIorange,inner sep=0pt] at (6,83) {\pgfuseplotmark{triangle*}};\node[anchor=west,font=\scriptsize] at (8,83) {Cannot hear};")
    L += [r"\end{tikzpicture}",
          r"\caption{The list-first prompt in Study 1. Each point is one model and boundary. Models whose first-step list omits the hidden values also leave them out of the answer.}",
          r"\label{fig:remedy}", r"\end{figure}"]
    return "\n".join(L)


def example():
    """Figure 1: one Study 1 item, verbatim replies from Gemma-4-31B."""
    return r"""\begin{figure}[t]
\centering\small
\fbox{\begin{minipage}{0.95\linewidth}\raggedright
\textbf{State.} Panam understands only English. Two mechanics talk quietly in Spanish, \emph{``¿Dónde está el espejo?'' ``En el almacén. No se lo digas a nadie.''} (Where is the mirror? In the warehouse. Don't tell anyone.)\\[3pt]
\textbf{Companion.} Sorry, I was on a holocall and missed that. What were those two saying?\\[3pt]
\textbf{Panam.} ``Just some boring shit about a \underline{mirror} being in the \underline{warehouse}. Don't worry about it.''\\[2pt]
\textbf{Version B} (chair, church). ``Something about a \underline{chair} being in a \underline{church}. Weird as hell, right?''\\[2pt]
\textbf{With} \texttt{understood\_by\_Panam:\,false}. ``Don't look at me, V. I didn't catch a damn word of it.''
\end{minipage}}
\caption{Gemma-4-31B playing a character who does not speak Spanish. The reply follows the hidden values when version B changes them, and a per-utterance flag stops the leak. Replies are verbatim.}
\label{fig:example}
\end{figure}"""


def framing():
    """Figure 7: how leaking replies present the hidden content (repertoire condition, content question)."""
    fr = load(RA / "leak_framing.json")
    ms = sorted([m for m, v in fr.items() if v["n"] >= 100], key=lambda m: fr[m]["tentative"])
    L = [r"\begin{figure}[t]", r"\centering", r"\begin{tikzpicture}[x=0.048cm,y=0.31cm,font=\footnotesize]"]
    cols = [("unframed", "OIblue", "Stated as fact"), ("attributed", "OIsky", "Attributed"), ("tentative", "OIorange", "Hedged as a guess")]
    for i, m in enumerate(ms):
        x = 0
        L.append(f"\\node[anchor=east,font=\\scriptsize] at (-1.5,{i}) {{{NAMES[m]}}};")
        for k, c, _ in cols:
            w = 100 * fr[m][k]
            L.append(f"\\fill[{c}] ({x:.1f},{i - 0.35}) rectangle ({x + w:.1f},{i + 0.35});")
            x += w
    for v in range(0, 101, 25):
        L.append(f"\\node[anchor=north,font=\\scriptsize] at ({v},-0.55) {{{v}}};")
    for j, (_, c, lab) in enumerate(cols):
        x0 = (-38, 0, 33)[j]
        L.append(f"\\fill[{c}] ({x0},{len(ms) + 0.2}) rectangle ({x0 + 3},{len(ms) + 0.7});\\node[anchor=west,font=\\scriptsize] at ({x0 + 3.5},{len(ms) + 0.45}) {{{lab}}};")
    L.append(r"\node[anchor=north] at (50,-1.5) {Share of leaking replies (\%)};")
    L += [r"\end{tikzpicture}",
          r"\caption{How leaks are phrased, for models with at least 100 leaking replies (repertoire condition, content question). The strongest models that still leak tend to present the content as a guess.}",
          r"\label{fig:framing}", r"\end{figure}"]
    return "\n".join(L)


def s2_detail(embed=False):
    """Figure: Study 2 representation contrasts (11 models) and persistence over neutral exchanges (four models)."""
    res = load(ROOT / "analysis/h200-v2-20261002/eleven-model-results.json")["exploratory_paired_contrasts"]
    rep = {r["contrast"]: r for r in res if r["contrast"].startswith("E2")}
    ch = ["Hear", "Understand", "See", "Receive"]
    L = ([] if embed else [r"\begin{figure}[t]", r"\centering"]) + [r"\begin{tikzpicture}[font=\footnotesize]", r"\begin{scope}[x=0.05cm,y=0.5cm]"]
    for x in range(-40, 41, 20):
        L.append(f"\\draw[black!12] ({x},-0.5)--({x},3.6);\\node[anchor=north,font=\\scriptsize] at ({x},-0.5) {{{x}}};")
    L.append(r"\draw[black!50] (0,-0.5)--(0,3.6);")
    for i, c in enumerate(reversed(ch)):
        L.append(f"\\node[anchor=east,font=\\scriptsize] at (-43,{i}) {{{c}}};")
        for key, col, dy in ((f"E2 R1-minus-R2 {c}", "OIblue", 0.16), (f"E2 R3-minus-R2 {c}", "OIgreen", -0.16)):
            r = rep[key]
            v, lo, hi = [100 * a for a in (r["estimate"], *r["ci95"])]
            L.append(f"\\fill[{col}] (0,{i + dy - 0.12}) rectangle ({v:.1f},{i + dy + 0.12});\\draw[black!70] ({lo:.1f},{i + dy})--({hi:.1f},{i + dy});")
    L.append(r"\fill[OIblue] (-40,4.75) rectangle (-37,5.05);\node[anchor=west,font=\scriptsize] at (-36,4.9) {Membership list instead of flag};")
    L.append(r"\fill[OIgreen] (-40,4.1) rectangle (-37,4.4);\node[anchor=west,font=\scriptsize] at (-36,4.25) {Flag plus prose rule};")
    L.append(r"\node[font=\scriptsize] at (0,-1.55) {(c) Change in net use relative to the flag (pp)};")
    L.append(r"\end{scope}")
    rows = [l.split(",") for l in (ROOT / "paper/arr/figures/plot-data.csv").read_text().splitlines()[1:] if l.startswith("persistence,")]
    per = {(r[2], r[3], int(r[5])): 100 * float(r[7]) for r in rows}
    L.append(r"\begin{scope}[xshift=7.2cm,yshift=-0.25cm,x=0.83cm,y=0.026cm]")
    for v in range(0, 101, 25):
        L.append(f"\\draw[black!12] (0,{v})--(4,{v});\\node[anchor=east,font=\\scriptsize] at (-0.08,{v}) {{{v}}};")
    for t in (0, 2, 4):
        L.append(f"\\node[anchor=north,font=\\scriptsize] at ({t},-2) {{{t}}};")
    ends = []
    marks = {"Hear": ("OIorange", "triangle*"), "Understand": ("OIblue", "*"), "See": ("OIpurple", "square*"), "Receive": ("OIsky", "diamond*")}
    for c in ch:
        col, mk = marks[c]
        pts = [(t, per[(c, "full", t)]) for t in (0, 2, 4)]
        L.append(f"\\draw[{col},line width=.8pt] " + "--".join(f"({t},{v:.1f})" for t, v in pts) + ";")
        L += [f"\\node[{col},inner sep=0pt] at ({t},{v:.1f}) {{\\pgfuseplotmark{{{mk}}}}};" for t, v in pts]
        ends.append([pts[-1][1], c, col])
    ends.sort()
    for i in range(1, len(ends)):
        ends[i][0] = max(ends[i][0], ends[i - 1][0] + 9)
    for yv, c, col in ends:
        L.append(f"\\node[anchor=west,font=\\scriptsize,text={col}] at (4.1,{yv:.1f}) {{{c}}};")
    vv = [per[(c, "view", t)] for c in ch for t in (0, 2, 4)]
    L.append(f"\\draw[OIgreen,line width=.8pt,dashed] (0,{max(vv):.1f})--(4,{max(vv):.1f});\\node[anchor=west,font=\\scriptsize,text=OIgreen] at (4.1,4) {{Character view}};")
    L.append(r"\node[font=\scriptsize] at (2,-14) {Neutral exchanges};")
    L.append(r"\node[font=\scriptsize] at (2,-27) {(d) Net use after neutral exchanges (pp)};")
    L.append(r"\end{scope}")
    if embed:
        return "\n".join(L + [r"\end{tikzpicture}"])
    L += [r"\end{tikzpicture}",
          r"\caption{Study 2 details. (a) How the state representation changes leakage relative to a direct access flag (11 models, 24 scenes). A prose rule lowers leakage in every channel except comprehension. (b) Leakage stays high after two and four scripted exchanges and rises for comprehension (four models, 32 scenes).}",
          r"\label{fig:s2detail}", r"\end{figure}"]
    return "\n".join(L)


def questions():
    """Figure: Study 1 leakage by the companion's question (repertoire condition, 11 open models)."""
    d = load(RA / "by_question.json")
    qs = [("content", "What did they say?"), ("task", "What is the task?"), ("check", "Did you catch it?"), ("plan", "What do we do next?")]
    L = [r"\begin{figure}[t]", r"\centering", r"\begin{tikzpicture}[x=0.036cm,y=0.47cm,font=\footnotesize]"]
    for v in range(0, 101, 25):
        L.append(f"\\draw[black!12] ({v},-0.5)--({v},3.5);\\node[anchor=north,font=\\scriptsize] at ({v},-0.5) {{{v}}};")
    for i, (q, lab) in enumerate(reversed(qs)):
        L.append(f"\\node[anchor=east,font=\\scriptsize,text width=1.9cm,align=right] at (-2,{i}) {{{lab}}};")
        vals = [100 * d[m][q] for m in d]
        for v in vals:
            L.append(f"\\fill[OIblue!45] ({v:.1f},{i}) circle (1.2pt);")
        mu = sum(vals) / len(vals)
        L.append(f"\\draw[OIblue,line width=1.2pt] ({mu:.1f},{i - 0.3})--({mu:.1f},{i + 0.3});\\node[anchor=south,font=\\scriptsize,text=OIblue] at ({mu:.1f},{i + 0.28}) {{{mu:.0f}}};")
    L.append(r"\node[anchor=north] at (50,-1.3) {Net use of speech the character cannot understand (pp)};")
    L += [r"\end{tikzpicture}",
          r"\caption{Study 1 by the companion's question (repertoire condition). Dots are the 11 open models and bars their mean. Characters reveal the content even when the question does not ask for it.}",
          r"\label{fig:questions}", r"\end{figure}"]
    return "\n".join(L)


ALL = {"FIG_QUESTIONS": questions, "FIG_EXAMPLE": example, "FIG_FRAMING": framing, "FIG_DESIGN": design, "FIG_S1": study1, "FIG_S2": study2, "FIG_FRONTIER": frontier, "FIG_REMEDY": remedy}

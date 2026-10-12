"""Write the paper into the official ACL template layout (acl_latex.tex, custom.bib, figures/).

Every figure becomes a PDF in figures/ that \\includegraphics loads at its natural size, so the layout matches the
TikZ build. figures/src/ keeps one standalone TikZ file per figure for editing and re-rendering.
Usage: python3 make_acl.py <template_dir> <out_dir> [figure-1 PDF]
The paper is built with: python3 make_acl.py ../acl-template ../arr-acl figure1.pdf
Figure sources are compiled with XeLaTeX in Arial. A supplied Figure 1 PDF replaces the generated one and is set to column width.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import build
import figures

TPL, OUT = Path(sys.argv[1]), Path(sys.argv[2])
FIG1 = Path(sys.argv[3]) if len(sys.argv) > 3 else None
NAMES = {"FIG_EXAMPLE": "fig1-example", "FIG_DESIGN": "fig2-design", "FIG_S1": "fig3-study1", "FIG_FACTORS": "fig4-models",
         "FIG_S2": "fig5-study2", "FIG_FRONTIER": "fig6-format", "FIG_WHY": "fig7-why", "FIG_REMEDY": "fig8-remedies",
         "FIG_S1M": "figA-listfirst-per-model", "FIG_BRIDGEFULL": "figB-bridge-all-models"}
# Main-text figures drawn on a reduced grid, then set to the full text or column width.
SHRINK = {"FIG_S1": (0.88, 0.92), "FIG_FACTORS": (1, 1), "FIG_S2": (0.88, 0.92), "FIG_FRONTIER": (0.88, 0.92), "FIG_WHY": (1, 1),
          "FIG_REMEDY": (0.88, 0.92)}
TIKZ = re.compile(r"\\begin\{tikzpicture\}.*\\end\{tikzpicture\}", re.S)

# preamble for the standalone figure sources: the TikZ set-up of the paper, without the review line numbers
FIG_PRE = (r"\documentclass[border=0pt]{standalone}" "\n" r"\usepackage{fontspec}\setmainfont{Arial}\setsansfont{Arial}"
           r"\usepackage{amsmath,amssymb,xcolor}" "\n"
           + build.PREAMBLE[build.PREAMBLE.index(r"\usepackage{tikz,pgfplots,fontawesome5}"):build.PREAMBLE.index(r"\setcounter{topnumber}")]
           + figures.COLORS + "\n")

# preamble: the template's own lines up to the title block, then what this paper adds
tpl = (TPL / "acl_latex.tex").read_text()
head = tpl[:tpl.index(r"\title{")]
EXTRA = r"""
% Added for this paper: tables, math, colors used in tables, and float placement
\usepackage{booktabs,amsmath,amssymb,tabularx,xcolor}
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
\setcounter{topnumber}{3}\setcounter{bottomnumber}{2}\setcounter{totalnumber}{5}\setcounter{dbltopnumber}{2}
\renewcommand{\topfraction}{0.9}\renewcommand{\bottomfraction}{0.6}\renewcommand{\textfraction}{0.08}
\renewcommand{\floatpagefraction}{0.75}\renewcommand{\dbltopfraction}{0.9}\renewcommand{\dblfloatpagefraction}{0.75}
\newsavebox{\OCtable}
\definecolor{OCblue}{HTML}{5B7FAF}\definecolor{OCorange}{HTML}{D2876C}\definecolor{OCgreen}{HTML}{68A595}
\definecolor{OCpurple}{HTML}{B497B6}\definecolor{OCred}{HTML}{B5635A}

"""


def main():
    (OUT / "figures" / "src").mkdir(parents=True, exist_ok=True)
    for f in ("acl.sty", "acl_natbib.bst", "README.md", "formatting.md"):
        shutil.copy(TPL / f, OUT / f)
    shutil.copy(build.P / "references.bib", OUT / "custom.bib")
    body = (build.P / "body.tex").read_text(encoding="utf-8")
    ins = {**build.study1(), **build.study2(), **build.added()}
    for key, fn in figures.ALL.items():
        code = fn()
        name = NAMES[key]
        tikz = TIKZ.search(code).group(0)
        if key == "FIG_EXAMPLE" and FIG1:
            shutil.copy(FIG1, OUT / "figures" / f"{name}.pdf")
            (OUT / "figures" / "src" / f"{name}.tex").unlink(missing_ok=True)
            ins[key] = code.replace(tikz, f"\\includegraphics[width=\\linewidth]{{figures/{name}.pdf}}")
            continue
        if key in SHRINK:
            # Drawing the figure on a smaller grid and scaling it to the text width enlarges its labels.
            fx, fy = SHRINK[key]
            src = tikz.replace("x=1cm,y=1cm", f"x={fx}cm,y={fy}cm", 1)
            src = re.sub(r"([xy])shift=(-?[\d.]+)cm", lambda m: f"{m.group(1)}shift={float(m.group(2)) * (fx if m.group(1) == 'x' else fy):.3f}cm", src)
        else:
            src = tikz
        (OUT / "figures" / "src" / f"{name}.tex").write_text(FIG_PRE + "\\begin{document}\n" + src + "\n\\end{document}\n")
        subprocess.run(["xelatex", "-interaction=nonstopmode", f"{name}.tex"], cwd=OUT / "figures" / "src", capture_output=True)
        shutil.copy(OUT / "figures" / "src" / f"{name}.pdf", OUT / "figures" / f"{name}.pdf")
        # Appendix figures fill the one-column text width like the appendix tables.
        opt = "[width=\\linewidth]" if key in ("FIG_S1M", "FIG_BRIDGEFULL") or key in SHRINK else ""
        ins[key] = code.replace(tikz, f"\\includegraphics{opt}{{figures/{name}.pdf}}")
    for k, v in ins.items():
        body = body.replace(f"% INSERT {k}\n", v + "\n")
    assert not re.findall(r"^% INSERT (\w+)$", body, re.M)
    for x, y in build.CAPTION_SENTENCES:
        body = body.replace(x, y)
    body = build.twocolumn_appendix(build.style_tables(body))
    body = build.late_fixes(body)
    body = body.replace(r"\bibliography{references}", r"\bibliography{custom}")
    body = body.replace(r"\author{Anonymous ACL submission}", tpl[tpl.index("\n\\author{First Author") + 1:tpl.index(r"\begin{document}")].strip())
    (OUT / "acl_latex.tex").write_text(head + EXTRA + body, encoding="utf-8")
    for f in (OUT / "figures" / "src").glob("*"):
        if f.suffix in (".aux", ".log", ".pdf", ".xdv"):
            f.unlink()
    (OUT / "figures" / "README.txt").write_text(
        "Figures of the paper, one PDF each, loaded by acl_latex.tex with \\includegraphics{figures/<name>.pdf}.\n"
        "Replacing a PDF with another of the same name updates the paper; keep the width to keep the page layout.\n"
        "src/ holds the standalone TikZ source of each figure. Rebuild one with: pdflatex <name>.tex (needs tikz, pgfplots, fontawesome5).\n")
    print("wrote", OUT / "acl_latex.tex")


if __name__ == "__main__":
    main()

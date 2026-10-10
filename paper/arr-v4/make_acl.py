"""Write the paper into the official ACL template layout (acl_latex.tex, custom.bib, figures/).

Every figure becomes a PDF in figures/ that \\includegraphics loads at its natural size, so the layout matches the
TikZ build. figures/src/ keeps one standalone TikZ file per figure for editing and re-rendering.
Usage: python3 make_acl.py <template_dir> <out_dir>
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import build
import figures

TPL, OUT = Path(sys.argv[1]), Path(sys.argv[2])
NAMES = {"FIG_EXAMPLE": "fig1-example", "FIG_DESIGN": "fig2-design", "FIG_S1": "fig3-study1", "FIG_FACTORS": "fig4-scale-ablation",
         "FIG_S2": "fig5-study2", "FIG_FRONTIER": "fig6-frontier-format", "FIG_WHY": "fig7-why", "FIG_REMEDY": "fig8-remedies",
         "FIG_S1M": "figA-listfirst-per-model", "FIG_BRIDGEFULL": "figB-bridge-all-models"}
TIKZ = re.compile(r"\\begin\{tikzpicture\}.*\\end\{tikzpicture\}", re.S)

# preamble for the standalone figure sources: the TikZ set-up of the paper, without the review line numbers
FIG_PRE = (r"\documentclass[border=0pt]{standalone}" "\n" r"\usepackage{times}\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}"
           r"\usepackage{amsmath,amssymb,xcolor}" "\n"
           + build.PREAMBLE[build.PREAMBLE.index(r"\usepackage{tikz,pgfplots,fontawesome5}"):build.PREAMBLE.index(r"\setcounter{topnumber}")]
           + figures.COLORS + "\n")

# preamble: the template's own lines up to the title block, then what this paper adds
tpl = (TPL / "acl_latex.tex").read_text()
head = tpl[:tpl.index(r"\title{")]
EXTRA = r"""
% Added for this paper: tables, math, colors used in tables, and float placement
\usepackage{booktabs,amsmath,amssymb,tabularx,xcolor}
\usepackage{placeins}
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
        (OUT / "figures" / "src" / f"{name}.tex").write_text(FIG_PRE + "\\begin{document}\n" + tikz + "\n\\end{document}\n")
        subprocess.run(["pdflatex", "-interaction=nonstopmode", f"{name}.tex"], cwd=OUT / "figures" / "src", capture_output=True)
        shutil.copy(OUT / "figures" / "src" / f"{name}.pdf", OUT / "figures" / f"{name}.pdf")
        ins[key] = code.replace(tikz, f"\\includegraphics{{figures/{name}.pdf}}")
    for k, v in ins.items():
        body = body.replace(f"% INSERT {k}\n", v + "\n")
    assert not re.findall(r"^% INSERT (\w+)$", body, re.M)
    for x, y in build.CAPTION_SENTENCES:
        body = body.replace(x, y)
    body = build.style_tables(body, build.table_widths(body))
    body = body.replace(r"\bibliography{references}", r"\bibliography{custom}")
    body = body.replace(r"\author{Anonymous ACL submission}", tpl[tpl.index("\n\\author{First Author") + 1:tpl.index(r"\begin{document}")].strip())
    (OUT / "acl_latex.tex").write_text(head + EXTRA + body, encoding="utf-8")
    for f in (OUT / "figures" / "src").glob("*"):
        if f.suffix in (".aux", ".log", ".pdf"):
            f.unlink()
    (OUT / "figures" / "README.txt").write_text(
        "Figures of the paper, one PDF each, loaded by acl_latex.tex with \\includegraphics{figures/<name>.pdf}.\n"
        "Replacing a PDF with another of the same name updates the paper; keep the width to keep the page layout.\n"
        "src/ holds the standalone TikZ source of each figure. Rebuild one with: pdflatex <name>.tex (needs tikz, pgfplots, fontawesome5).\n")
    print("wrote", OUT / "acl_latex.tex")


if __name__ == "__main__":
    main()

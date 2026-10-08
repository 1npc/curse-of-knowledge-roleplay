"""Compile one figure from figures.py on a blank ACL page and render it (for checking layout)."""
import subprocess
import sys
from pathlib import Path

import build
import figures

name = sys.argv[1]
tex = build.PREAMBLE + figures.COLORS + "\n\\begin{document}\\pagestyle{empty}\n" + (("\\onecolumn\n" + figures.ALL[name]().replace("[t]", "[h]")) if "figure*" in figures.ALL[name]() else figures.ALL[name]()) + "\n\\lipsum\n\\end{document}\n"
tex = tex.replace("\\lipsum", "\\null")
d = Path("/private/tmp/claude-501/-Users-xiaozhang-code--OverComprehension/d1dc8212-7705-438e-92a4-9e4e1a63d000/scratchpad/prev")
d.mkdir(exist_ok=True)
for f in ("acl.sty",):
    (d / f).write_bytes(Path(f).read_bytes())
(d / "p.tex").write_text(tex)
r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "p.tex"], cwd=d, capture_output=True, text=True)
log = (d / "p.log").read_text(errors="ignore")
for line in log.splitlines():
    if line.startswith("!") or "Overfull" in line:
        print(line)
subprocess.run(["pdfcrop", "--margins", "6", str(d / "p.pdf"), str(d / "c.pdf")], capture_output=True)
subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=png16m", f"-r{sys.argv[3] if len(sys.argv) > 3 else 200}", "-dFirstPage=1", "-dLastPage=1", f"-sOutputFile={d}/{name}.png", str(d / "c.pdf")])
print(d / f"{name}.png")

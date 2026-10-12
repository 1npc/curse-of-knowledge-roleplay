Figures of the paper, one PDF each, loaded by acl_latex.tex with \includegraphics{figures/<name>.pdf}.
Replacing a PDF with another of the same name updates the paper; keep the width to keep the page layout.
src/ holds the standalone TikZ source of each figure. Rebuild one with: pdflatex <name>.tex (needs tikz, pgfplots, fontawesome5).

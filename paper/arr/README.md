# ARR anonymous manuscript

**Role-Playing Language Models Use Information Their Characters Cannot Access**

`main.tex` is the current English ARR long-paper manuscript. Its central question is whether inaccessible content should remain in a character generator's context. The introduction states three contributions, followed by related work, access evaluation, compilation, experimental setup, five evidence-led result subsections, and a discussion and conclusion. The main text includes an access/shell table, a cohort-scope table, an eleven-model dual-matrix profile with accessible controls and channel means, pooled confirmation statistics, three-panel delayed-use/change/search-choice plots, and the compact method comparison. The main text also explains the net-use score, gives an illustrative compiler transformation and an observed self-filter failure, and reports the lexical-block sensitivity. The appendix retains numerical baselines and the complete six-model method comparison. The verified campaign contains all 220,088 actual generation records and 206,264 scored endpoints including calibration. Seed completed on one Slurm H100 with the original checkpoint pin, software and decoding protocol; the other ten models ran on H200. The four-model confirmation and six-model method contrasts are unchanged. Human certification remains pending.

## Read and compile

Open `main.tex` in the Codex LaTeX editor. The current source compiled successfully with the built-in compiler. The official ACL style is embedded unchanged, all figures are editable TikZ with matching SVG exports, and the formatted bibliography is inline. No additional project files or local TeX installation are required for editor compilation. The PDF export is at `../../deliverables/over-comprehension-arr.pdf`, produced with the existing local TeX Live installation. All 18 pages were visually inspected; the main text with its figures and tables occupies eight full pages, with both columns on page 8 ending near the official bottom boundary. Limitations starts on page 9. The full-width result composites appear on pages 7 and 8 alongside result discussion, and the final appendix tables are stacked with ordinary positive spacing. `pdf-export-receipt.json` binds that PDF to this exact source and records page, font, metadata and reference checks. Ragged-bottom spacing in the measurement column and on Limitations and subsequent pages avoids excessive paragraph stretching; up to three appendix tables can share a page with supporting text.

The latest reporting pass corrects the stimulus units to 24 sentences and 12 A/B pairs, adds accessible positive-control probe accuracy and a complete saved counterfactual case, and specifies the frozen scorer's denial and multi-value behavior. Human error is reported separately by method/access state and for the state-correct full-inaccessible subgroup. The method discussion states the accessible-schema confound and bounded baseline comparison; the occurrence endpoint is an observable-shell retention check. No selective-occurrence, matched-schema or held-out-vocabulary experiment was added.

The latest writing pass presents human-study methods and reporting in final-tense form, with 231 visibly bracketed fields for unsupplied evidence. The abstract is 134 words and reports verified automatic findings. The main human measurement and sensitivity paragraphs link to separate discovery/confirmation confusion matrices, multilingual double review, and a non-speaker guessing study in Appendix D. The completion-template notice is visible in the main footnote and appendix. Actual human observations remain zero; no AI labels have been renamed as human results. Existing machine scores, statistical tests, and the detailed result figures are unchanged.

Use **pdfLaTeX** to reproduce the eight-page submission layout. From the standalone source-package directory, run `latexmk -pdf main.tex` (or run `pdflatex main.tex` until references resolve). The built-in editor uses XeTeX for preview and has different line and page breaks; its preview is not the submission pagination reference. The source emits an explicit warning in that engine. The pdfLaTeX build includes an error guard after flushing the main text and floats and resolving references to check the eight-page bound, and the exported PDF page count is independently verified. All engines retain width guards for generated tables and figures. The abstract is under 200 words. Anonymous review mode, Limitations, Ethical Considerations, AI-assistance disclosure, and double-column appendices are included.

Current policy references, checked 2026-10-03: [ARR call for papers](https://aclrollingreview.org/cfp), [ACLPUB formatting](https://acl-org.github.io/ACLPUB/formatting.html), and [anonymous review version](https://acl-org.github.io/ACLPUB/review-version.html). ARR long papers allow at most eight main-content pages including figures and tables; Limitations, Ethical Considerations, references and appendices are outside that limit. The four template files were checked byte-for-byte against the current official repository. The review PDF contains no Acknowledgments section; anonymous AI-assistance disclosure is under Ethical Considerations, with the Responsible NLP Checklist and final disclosure still to be completed by the authors. This is a complete working draft, not a submission-readiness declaration. Human observations and submission metadata/checklist remain open; final-tense template prose does not establish study completion.

## Evidence and figures

- `evidence-sources.json` binds the primary and descriptive results to source hashes.
- `model-registry.json` stores checkpoint pins and sanitized completed-run metadata.
- `figure_design.py` defines one final-size geometry for every editable TikZ/SVG figure. It preserves exact estimates and saved intervals, uses stable orange/blue/green semantics, and adds shape/number cues for monochrome printing.
- `figures/confirmation.tex` and `.svg` plot the four-boundary confirmation with connected controls, exact numbers and confidence intervals.
- `figures/behavior.tex` and `.svg` align four delay small multiples, the saved paired two-/four-turn changes, and full-versus-view fixed-A choice effects. Filled/open circles distinguish delay contrasts; triangles identify compiled-view estimates.
- `figures/discovery-heatmap.tex` and `.svg` show 44 inaccessible net-use cells and 44 accessible target-use cells, plus 22 equal-channel mean markers. Accessible use is read as `hit_t` from SHA-verified frozen score files, never inferred from net `D`. Both matrices retain labeled linear 0--100 scales; the core roster is marked without changing row order.
- Detailed per-model confirmation values remain in Appendix A after moving their table out of the main text to accommodate the wider result figures.
- `reporting-audit-data.json` binds both-state probe counts, the 24-sentence/12-pair inventory, and all 12 records of a selected real A/B example to saved inputs, raw replies and scores. Probe accuracy is 93.36–99.35% for accessible and 95.18–100% for inaccessible states; all 6,144 replies are valid. The example is independently re-scored and is not a prevalence estimate.
- `secondary-audit-data.json` records the .85 capability-conditioned analysis, state-correct boundary decomposition and order-stratified choice sensitivity. The frozen unconditional primary result is unchanged.
- `figures/plot-data.csv` contains 218 plotting rows: the 100 original descriptive estimates, 88 model/channel cells, 22 channel means, and eight saved paired delay contrasts. Saved confidence intervals and denominators remain attached where applicable; no model-profile uncertainty is invented.
- `verification.json` records what was checked and what remains unverified.
- `snapshot-diagnostics-data.json` retains the original nine-model diagnostic breakdown, accessible controls, self-filter string audit, and post-hoc lexical-block sensitivity, alongside the final eleven-model representation contrasts with their separate source hash. These additions preserve the frozen confirmation tests and are identified as descriptive analyses.

The three frozen confirmation families pass for the four prespecified models. These pooled findings do not mean every model leaks under every boundary: Gemma's comprehension-boundary estimate is zero. Japanese confirmation canary translation rates are below the diagnostic threshold for three models. The representation table covers eleven models; the comprehension prose contrast is -3.98 points [-8.05, -0.09], compared with +5.73 in the four-core subset. The article reports this cohort dependence, allowed-content loss during self-filtering, and the shared 12 lexical pairings underlying both scene sets. A separately labeled 12-block bootstrap gives wider descriptive intervals while leaving the original tests unchanged. The hard-removal distinction between original-scene retention and actual-input correctness is retained.

## Validation

The new v2 packet contains 640 semantic-use responses, 192 event-awareness responses, and 24 deduplicated multilingual stimuli. Two independent AI passes completed all 832 response items each. Seventeen semantic items have primary-label disagreements; 99 items require review when uncertainty is included. Native-stimulus screening flags 5 central meanings and 8 items overall as uncertain. These are AI judgments, not real human or native-speaker validation. The blank human forms are preserved. Two newly commissioned independent AI stimulus reviews cover all 24 sentence stimuli each. They disagree on three meaning labels and flag eleven items for uncertainty in either pass. These are heuristic AI assessments, not native-speaker or non-speaker guessability data.

The appendix labels scorer comparisons against A and B explicitly as AI-proxy metrics and discloses excluded uncertainty. To substitute later human data, use the same blinded schema and keep its provenance distinct. The `--label-type human` evaluator rejects files from the AI-proxy directory. The extended blind package adds 192 diagnostic foil cases, 128 choice responses, two paired stimulus forms, six native reviewer slots and the existing 96-question guessability task. Organizer keys and AI outputs are excluded from the human archive. The diagnostic enrichment is outcome-informed and must not be pooled into population F1.

The secondary comprehension result is 50.98 [48.36, 53.67] pp across nine eligible model-language units, compared with the frozen unconditional 47.20 [44.86, 49.61]. Choice order is deterministic and approximately balanced (18 A-first, 14 A-second); equal-position full-context effects remain 49.11–63.00 pp. No new generation or confirmation test was added.

## Regeneration and preservation

`body.tex` is the current authored source. `make_paper.py` inserts tables and figures from verified result artifacts; it does not change the frozen scorer or hypotheses. Regenerate from the experiment repository with system Python:

```bash
python3 paper/arr/make_paper.py
```

This updates `main.tex`. Keep prose edits in `body.tex` and reference changes in `references.bib` and the formatted `bibonly.bbl`. The self-contained source ZIP compiles without the experiment repository; regeneration requires the linked evidence files.

The previous two-boundary manuscript is preserved in `archive/pre-access-v2-source.zip`. The old 760,508 raw responses and their analysis remain separate from the new four-boundary estimates.

The current visual revision increases supported comparisons while preserving the frozen analysis and the exact eight-page main-text target. Matrix text colors are chosen from their actual fill luminance; data-label contrast is checked numerically. The palette uses dark orange `#B04A00`, blue `#0072B2`, and teal `#007A5E`. Final-size matrix values use 8.8 pt text; secondary ticks use 7.5--8 pt. Both generated-source widths and rendered PDF pages are checked.


## Filling the final-tense human-study report

正文和附录已经按评估完成后的论文口吻写好。蓝色方括号是待填的真实证据字段，不是模拟结果。方法细节、伦理状态和解释性结论也要根据实际工作核对；不能只替换百分比。现有 640 条发现集语义包和 192 条确认集发生性包不等于确认集的语义核验；后者的抽样范围、样本和权重分别填写。

`\HumanField{KEY}` reads an optional `HVKEY` definition placed before `\title` in `body.tex`. If none exists, it prints the visible blue `[KEY]` placeholder. Define the value once to update all mentions, including generated tables, and then run `python3 paper/arr/make_paper.py`. In the portable standalone package, add the same definitions before `\title` in `main.tex`; regeneration is not needed to compile that file. For example, replace the descriptive text below with a verified value:

```latex
\expandafter\def\csname HVN-D\endcsname{[completed discovery audit count]}
\expandafter\def\csname HVFST-f\endcsname{[correct-probe full-inaccessible target F1]}
\expandafter\def\csname HVC-interpretation\endcsname{[supported comparison conclusion]}
```

| Fields | Required evidence |
| --- | --- |
| `N-D`, `N-C`, `N-O`, `C-FRAME`, `C-SAMPLING` | Completed discovery semantic, confirmation semantic, and confirmation occurrence samples; the confirmation semantic sampling frame and inclusion scheme. |
| `ADJ`, `ANN-QUAL`, `U-D`, `U-C`, `U-O` | Adjudication procedure, annotator competence, unresolved counts by audit. |
| `DT`, `DF`, `O`, and `FIT/FIF`, `FAT/FAF`, `HIT/HIF`, `HAT/HAF`, `VIT/VIF`, `VAT/VAF`, `FST/FSF`, with suffixes `-tp`, `-fp`, `-fn`, `-p`, `-r`, `-f`, `-k` | Discovery target/foil and occurrence metrics; confirmation target/foil separately for full/removal/view × inaccessible/accessible. FS is full-inaccessible with a correct independent probe, overlapping FI. Confusion counts, weighted precision/recall/F1 (%), and independent Cohen's kappa. |
| `FI`, `FA`, `HI`, `HA`, `VI`, `VA`, `FS` with `-N`, `-T`, `-F`, `-B`, `-D`, `-L`, `-U`, `-BIAS`; `C-CI`, `C-STRATA`, `C-interpretation`, `C-SCOPE` | Completed count, weighted target/foil/simultaneous-use percentages, net D and interval bounds (pp), and automatic-minus-human bias for each condition. Preserve model/boundary strata and sampling weights. Evaluate union disclosure for view in addition to net D. |
| `O-FULL`, `O-HARD`, `O-VIEW` | Human original-scene occurrence retention by method, reported separately from actual-input correctness. |
| `N-F`, `F-ERRORS`, `F-TYPES` | Enriched foil diagnostic completion, error counts and mechanisms. Do not use this packet for population accuracy. |
| `N-Q`, `Q-AGREE`, `U-Q`, `Q-EFFECT` | Choice decoding audit completion, agreement percentage, unresolved cases and separate human-derived effect. |
| `LANG-QUAL`, `LANG-ADJ`, `LANG-ISSUES`; `ZH`, `JA`, `ES` with `-ok`, `-n`, `-m`, `-c`, `-k` | Real double-reviewer language competence and adjudication; meaning-correct counts out of 8 sentences, mean naturalness over 8 sentences and A/B matchedness over 4 distinct pairs, sentence clue counts, independent meaning agreement; `PAIR-RESOLVE` specifies reconciliation of reciprocal form rows. |
| `G-RECRUIT`, `N-G`, `G-EXCLUDE`, `G-ZH`, `G-JA`, `G-ES`, `G-CI`, `G-ITEMS`, `G-EFFECT` | Recruitment, eligible participant answers, participant/language exclusions, active-word guessing percentages and uncertainty, cue-bearing items and separate sensitivity. |
| `ETHICS`, `CONSENT`, `PAY`, `RECRUIT` | Actual approval/exemption determination, consent, compensation and recruitment. No ethics approval or participant qualification is inferred. |

The blue field convention, footnote and template captions should be replaced with evidence-bound study text only after the observations are supplied. Human tables must have actual sample counts, nonzero/zero positive counts reported as observed, uncertainty handling, and reproducible weights. Interpretive fields do not assume that human correction preserves the automatic conclusion. AI screening metrics remain in Appendix D.5 and are excluded from all human fields. Filling source fields alone does not mark verification as submission-ready.

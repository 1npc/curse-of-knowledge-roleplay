# Analysis plan (draft, to be frozen on 2026-10-03)

Status: draft. Items marked **[open]** need the author's decision before the freeze. At the freeze
this file, the scorer, the alias and mask tables, the regular-expression tables and
`analysis/confirmatory.py` are committed together, and an anonymous OSF registration points to
that commit. After the freeze, any added analysis is labelled post hoc.

## 1. Data

- **Main set.** 96 scenario skeletons (48 direct address, 48 overheard) in Chinese, Japanese and
  Spanish: 288 items. Each item has an A and a B version that differ only in two content canaries,
  one PLACE and one OBJECT, drawn from 12 formal values per type (four backups per type replace
  values that fail the word-form guessability test in a language). Values rotate over skeletons,
  languages and versions so that each value appears 8 times per language and version.
- **Characters.** Kerry, Rogue and Panam, 32 skeletons each; language understanding is declared in
  the state and manipulated within item (declared set). **[open]** Viktor is excluded by default.
- **Cells per item.** 112 main prompts (15 real A cells, 7 swap B cells, 5 noise cells, spoken-only)
  x 4 questions, plus 13 out-of-character probes (proposal 5.1).
- **Other sets.** Non-Cyberpunk arm (16 skeletons, 48 items, 24 prompts each); canon and
  character-layer subset (52 entries, 8 prompts each); mitigation arms M1 and FS on four models;
  prompt-robustness arm on three models.
- **Excluded.** Pilot skeletons P01 to P10 never enter confirmatory analyses; the scorer was tuned on
  them only.
- **Models.** The fixed set listed in `harness/models.json` plus the B-tier and hosted models added
  before the main run. Decoding is greedy (temperature 0, top_p 1, seed 20260916), thinking is
  disabled through the chat template, at most 400 new tokens.

## 2. Scoring

- Rule-based scorer at the frozen commit; no LLM judge produces any reported number.
- Strict canary hits on a normalized copy of the reply (echoes of the foreign forms removed, idioms
  and names masked); a reply naming two or more values of one type is a hedge.
- **Primary handling.** Hedges count 0. Truncated replies and refusals count as not using the content.
  Replies flagged as non-English (L) or as echoes of the stimulus go to human review and stay in the
  primary analysis with L-language alias matching.
- **Sensitivity.** Hedges count 1/k; truncated replies excluded; L and echo replies excluded;
  "attributed" reports counted as admissions.

## 3. Units, conditioning and pooling

- A unit is a (model, language) pair. It enters pooled estimates when the model recovers both
  canaries in at least 85% of that language's translation probes (gate G2).
- Confirmatory statistics use the capability-conditioned subset: item versions whose translation
  probe recovered both canaries for that model. Unconditional estimates are reported alongside.
- Pooled estimate: equal-weight mean over passing units. Conclusions are about the fixed model set,
  not about language models in general.
- Intervals: skeleton bootstrap, B = 2000; each draw resamples skeletons once and applies the same
  draw to all units, keeping every skeleton's languages, cells and A/B versions together.

## 4. Confirmatory hypotheses

OC_swap(cell) = P(hit_t) - P(hit_f), computed on the same replies (target = the reply's own
version's canaries, foil = the other version's). One-sided tests at alpha = 0.05, Holm-corrected
over the seven tests.

| # | Statistic | Supported when | Falsified when |
|---|---|---|---|
| H1 | OC_swap(C-T-, D0), four questions pooled | lower bound > 0.10 | 90% CI within +-0.05 while OC_swap(C+T-, D0) >= 0.6 |
| H1b | OC_swap(C-T-, D0) - LEAK_swap(E_inaud, D0) | lower bound > 0 | 90% CI within +-0.05 |
| H2a | P(hit_t and N_deny) - P(hit_f and N_deny), C-T- D1, content and plan questions, non-refusals | lower bound > 0.05 | not reached |
| H2b | share of hits without A_explicit and not attributed, D1 minus U (paired) | lower bound > 0 | not reached |
| H3 | OC_swap(C-T_off, D1) - OC_swap(C-T-, D1) | pooled lower bound > 0 | 90% CI within +-0.05 (TOST) |
| H4a | OC_swap(C-T-, D0) on items whose state probe was answered correctly | lower bound > 0.10 | not reached |
| H4b | M1: relative reduction of OC_swap(C-T-, D0), and change in C-T+ hit_t | reduction lower bound >= 0.5 and change within +-0.05 | not reached |

- **[open]** H2b uses the definition in proposal 2.2 (no A_explicit and not attributed; tentative
  uses count as unframed). The alternative from the proposal's appendix C (mode = unframed only) is
  reported as a sensitivity analysis.
- H4b is tested only on models whose OC_swap(C-T-, D0) lower bound exceeds 0.10; M1 is
  decomposed into step-1 leakage (the perception list names a canary) and step-2 use.
- Headline per model: "k of K models have an H1 lower bound above 0.10", Holm across models.
- Secondary, outside the family: logit-scale dissociation index on the content question.

## 5. Exploratory analyses (Benjamini-Hochberg, q = 0.10)

E1 reasoning on (Qwen3.8-27B, if run); E2 scale within the Qwen3.5 and Gemma-4 families; E3 direct
address versus overheard (two-sided); E5 spoken-only states; E6 name and identity priors (canon
subset) and the series prior (non-Cyberpunk arm versus the main set); language moderation (models
passing G2 in all three languages); declaration strength U, D0, D1, D2; noise baselines and
wrong-value calibration; cross-language foils in cells without a B version.

## 6. Robustness

- Three alternative system prompts on three models: the sign of OC_swap(C-T-, D0) must match the
  main prompt.
- Leave-one-character-out; two-way skeleton x character bootstrap.
- Per-model GEE (canary level, exchangeable within reply), run remotely with statsmodels.

## 7. Human audit and fallbacks (proposal 6.5)

- Certification: 360 double-annotated replies stratified by cell, blind to cell, model and version;
  thresholds U1 precision >= 0.95 with Wilson lower bound >= 0.90, A_explicit and N_deny precision
  >= 0.90 and F1 >= 0.80; kappa and AC1 reported.
- Miss audit: 220 replies with no hit, stratified by declaration strength; Rogan-Gladen correction
  per cell.
- Fallbacks frozen now: if hit precision or recall fails, report misclassification-corrected
  estimates and make U2 (both canaries) the primary hit measure; if A_explicit or N_deny fails, H2a
  and H2b become descriptive and the family shrinks accordingly.

## 8. Deviations from the proposal (so far)

1. The main set has 96 skeletons (288 items) instead of 64 (192), by the author's decision on 9/28.
2. Local tooling is standard-library Python: explicit inflected aliases instead of a lemmatizer,
   hand-authored readings for transliteration, a heuristic language flag (all flagged replies go to
   humans), a hand familiarity list instead of word-frequency warnings.
3. Echo removal applies to the English matching copy only; replies in the stimulus language are
   matched on a separate copy with only verbatim stimulus runs removed. Replies that mostly repeat
   the stimulus are flagged as echoes and reviewed.
4. Hit mode takes the least framed sentence that names the target.
5. N_unheard is added for the inaudible cell.
6. In M1's second step the speech is replaced by one event holding the step-1 output (for
   overheard scenes, "the two <people>" to "each other").
7. The pilot showed that structured language state barely changes behavior (U close to D0) and that
   one natural-language sentence (D1) removes most use for one model; the hypotheses are unchanged.

## 9. What was seen before the freeze

Only pilot items (P01 to P10) were generated and scored before the freeze: a smoke run (three
models, 54 prompts each), the pilot (three models, 4,350 prompts each), the small-model pilot and the
mitigation pilot. They informed scorer rules and are reported as pilot descriptives only.

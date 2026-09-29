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
- **Cells per item.** 128 main prompts (17 real A cells, 9 swap B cells, 5 noise cells, spoken-only)
  x 4 questions, plus 15 out-of-character probes. Two cells were added on 9/28 after the pilot
  (section 8): E_inaud_S (English speech marked `audible_to_X: false` and nothing else) and
  C-T-_flag (C-T- D0 plus `understood_by_X: false` on each utterance). Both use the same neutral
  scene description ("<speaker> speaks to X in <language>"), which says neither "aloud" nor "could
  not hear".
- **Other sets.** Non-Cyberpunk arm (16 skeletons, 48 items, 24 prompts each); canon and
  character-layer subset (52 entries, 8 prompts each); mitigation arm M1g on every confirmatory
  model (C-T- A and B, C-T+ A, E_inaud_S A and B; content and plan questions); FS on four models
  (exploratory); prompt-robustness arm on three models.
- **Excluded.** Pilot skeletons P01 to P10 never enter confirmatory analyses; the scorer was tuned on
  them only.
- **Models.** **[open]** Proposed confirmatory set, all at most 40B total parameters (author's
  decision 9/28), nine families: Qwen3.8-27B, Qwen3.5-9B, Gemma-4-31B, Gemma-4-12B, GLM-4.7-Flash,
  Mistral-Small-24B-Instruct-2501, gpt-oss-20b, Phi-4, Seed-OSS-36B, Nemotron-3-Nano-30B and
  Falcon-H1-34B. Qwen3.5-4B, 2B and 0.8B and Gemma-4-E2B form the exploratory scale arm. Decoding is greedy (temperature 0, top_p 1, seed 20260916), thinking is
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

The claim: role-playing models use speech their character cannot perceive, whether the character
cannot understand it or cannot hear it; a boundary given only as structured state barely constrains
them; the models can read the state; a two-step perspective filter closes most of the gap.

OC_swap(cell) = P(hit_t) - P(hit_f) on the same replies (target = the reply's own version's
canaries, foil = the other version's). For the inaudible cells the same quantity is called
LEAK_swap. One-sided tests at alpha = 0.05, Holm-corrected over the eight tests. Foreign-language
cells use the capability-conditioned subset; English cells use every item.

| # | Statistic | Supported when | Falsified when |
|---|---|---|---|
| H1 | OC_swap(C-T-, D0) | lower bound > 0.10 | 90% CI within +-0.05 while OC_swap(C+T-, D0) >= 0.6 |
| H1i | LEAK_swap(E_inaud_S, D0) | lower bound > 0.10 | 90% CI within +-0.05 while hit_t(E, D0) >= 0.6 |
| H2a | OC_swap(C-T-, D0) - OC_swap(C-T-, D1) | lower bound > 0 | 90% CI within +-0.05 |
| H2b | LEAK_swap(E_inaud_S, D0) - LEAK_swap(E_inaud, D0) | lower bound > 0 | 90% CI within +-0.05 |
| H3 | OC_swap(C-T-, D0) - OC_swap(C-T-_flag, D0) | lower bound > 0 | 90% CI within +-0.05 |
| H4 | LEAK_swap(E_inaud_S, D0) - OC_swap(C-T-_flag, D0) | lower bound > 0 | upper bound < 0 |
| H5a | OC_swap(C-T-, D0) on items whose state probe was answered correctly | lower bound > 0.10 | not reached |
| H5b | M1g: mean of the relative reductions of OC_swap(C-T-, D0) and LEAK_swap(E_inaud_S, D0), and the change in C-T+ hit_t | reduction lower bound >= 0.5 and change >= -0.05 | not reached |

- H1 and H1i: the phenomenon for each boundary. H2a and H2b: stating the boundary in prose (a D1
  sentence; the E_inaud scene description) reduces use compared with state alone. H3: the models do
  not derive "cannot understand" from the language repertoire as well as from a direct flag. H4: with
  both boundaries given as a direct per-utterance flag, the inaudible one leaks more, so the failure
  is not specific to language (the pilot direction; the original H1b expected the opposite).
- H5b is tested on models whose own OC_swap(C-T-, D0) lower bound exceeds 0.10. M1g is decomposed
  into step-1 leakage (the perception list names a canary) and step-2 use. **[open]** In the pilot
  the pooled C-T+ change was -0.061, just past the one-sided -0.05 margin, while the reduction was
  0.63; the margin stays as set on 9/28 unless the author changes it before the freeze.
- Per-model readout: "k of K models have an H1 lower bound above 0.10", and the same for H1i,
  Holm across models.
- Secondary, outside the family: logit-scale dissociation index on the content question.

## 5. Exploratory analyses (Benjamini-Hochberg, q = 0.10)

Demoted from the confirmatory family on 9/28 to 9/29 (section 8): deny-while-using (the former H2a:
P(hit_t and N_deny) - P(hit_f and N_deny), C-T- D1); the unattributed-use share, D1 minus U (the
former H2b); the offline translator (the former H3: OC_swap(C-T_off, D1) - OC_swap(C-T-, D1)); the
former H1b as specified (C-T- D0 against E_inaud D0, confounded by how the boundary is stated); M1
(the language-only wording) and FS.

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
   one natural-language sentence (D1) removes most use for one model.
8. **Hypotheses revised after the pilot (9/28 to 9/29), before any main-set generation.** The
   proposal's H1b compared C-T- D0 (non-comprehension given only in the state) with E_inaud D0
   (inaudibility stated in the scene description), which confounds the boundary with how it is
   stated. Two matched cells (E_inaud_S, C-T-_flag) were added and run on the pilot items for 13
   models: a bare inaudibility flag leaked as much as or more than the language repertoire, and
   the comprehension-versus-hearing difference was negative for every model. The family was
   rebuilt around both boundaries (section 4); the former H2a, H2b and H3 became exploratory, which
   keeps the family at eight tests.
9. M1's step 1 names only what the character cannot understand, which is unfair to the inaudible
   cell. M1g ("Leave out anything X cannot hear or cannot understand") replaces it as the tested
   mitigation; M1 pilot results are reported as pilot descriptives.
10. Mistral-Small-3.1-24B does not load in the pinned vLLM and transformers pair; the text-only
    Mistral-Small-24B-Instruct-2501 replaces it. Its tokenizer is loaded as the fast tokenizer
    with the regex fix; its ids matched mistral-common's on a pilot prompt.

## 9. What was seen before the freeze

Only pilot items (P01 to P10) were generated and scored before the freeze: a smoke run (three
models, 54 prompts each), the pilot (three models, 4,350 prompts each), the small-model pilot, the
matched-cell runs (13 models), the pilot for the added models (4,890 prompts each) and the
mitigation pilots (M1, FS, M1g). They informed scorer rules and the hypotheses in section 4 and are
reported as pilot descriptives only. No main-set item has been shown to any model.

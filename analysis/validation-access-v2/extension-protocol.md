# Supplemental independent human validation

Use two independent people, A and B, before adjudication. Give each person only
their own blind forms and the original protocol. Keep organizer keys, machine
scores, AI labels, and the other person's answers hidden. Preserve IDs, text,
questions, candidate fields, and row ordering. Blank forms are preparation, not
completed human evidence.

The original 640 content and 192 occurrence responses remain the representative
audit. Fill blind-foil forms using the same semantic-use rules in protocol.md.
This supplemental case review is diagnostically selected; organizers must report
it separately and must not use it as a population precision/recall estimate or
count overlapping source responses twice.

For blind-choice forms, chosen_option is 1, 2, neither, or U. Judge which listed
destination the response actually selects, including a clear verbal paraphrase.
An uncommitted discussion of both options is neither. uncertain is 0, 1, or U;
give a short evidence note. This checks decoding of proposed textual choices.

Each Chinese/Japanese/Spanish stimulus needs two independent fluent/native
reviewers. Use the A/B native-review forms and record reviewer competence and
consent in native-reviewer-profiles.csv. Fill meaning_correct with 0/1/U;
naturalness and A/B matchedness with 1--5 (1 poor, 5 strong); canary_lexical_clue
with 0/1/U; uncertain with 0/1/U. Record whether lexical specificity, spatial
readings, unnatural grammar, or asymmetric A/B difficulty changes the intended
interpretation. Review the eight stimuli in the reviewer's language. A native
review is not a non-speaker guessing experiment.

Counting units: the complete inventory has 24 individual sentences forming
12 reciprocal A/B pairs, with eight sentences and four pairs per language.
Meaning, naturalness, and lexical clues are sentence judgments. A/B matchedness
is a pair judgment: each pair appears twice in a form, once from each sentence
orientation. Preserve both original rows, but reconcile the two orientations
into one distinct pair judgment before averaging or reporting sample size.
Record the reconciliation/adjudication rule and unresolved pairs. Do not report
the 24 sentence rows as 24 independent counterfactual pairs.

For word-form guessability, use the existing guessability-form.md and
guessability-items.csv. Give participants neither the key nor intended stimulus
translations. Record actual participant responses in guessability-responses.csv;
one row per participant, with their eligibility answers and the English option
selected for each qid. All active v2 canary-language pairs are covered by this
questionnaire. Eligibility and analysis remain those of tools/score_guessability.py.
Any suggested stimulus exclusion concerns future designs or a separately
identified sensitivity; it must not overwrite the completed frozen v2 analysis.

Organizers: report target and foil use separately, including positive counts and
unresolved cases; report original-scene occurrence retention separately from
actual-input correctness; report choice decoding separately. Retain both original
annotations and adjudication. Human-derived corrections are additional sensitivity
results. Document recruitment, competence, consent and compensation before calling
these results human-certified.

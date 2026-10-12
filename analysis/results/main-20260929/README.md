# Main analysis artifacts · 2026-09-29

Status: machine-scored, human validation pending. Main inference concerns a fixed roster of 11 models, with 33 passing model–language units. Four other models belong only to scale exploration.

| Artifact | Meaning |
|---|---|
| confirmatory.json / bootstrap_draws.npz | Locked eight-test family; H5b includes reduction and retention jointly. npz row 0 is the point estimate, subsequent rows the 2,000 resamples. |
| model_metrics.json / .csv | Capability-conditioned per-model estimates; JSON includes intervals. Mitigation baselines use content/plan only. |
| capability_gates.* | Both-canary recovery on complete non-refused real translation probes; threshold .85. |
| cells.csv | Descriptive cell × language averages for all models/arms; **not capability-conditioned**. `target`, `foil`, `oc` apply primary failure-zero handling. `U2`, `A`, `N_deny`, `F`, `G` where present, `L`, `echo_only`, `wrong` are raw scorer flags; they are not substitutes for the primary estimands. |
| by_Q.csv / by_mode.csv / by_character.csv | Unconditional main-arm breakdowns, not additional confirmatory tests. |
| state_probes.csv | Complete, non-refused state-answer correctness. H5a only has 30 nonempty units; GLM contributes none. |
| generation_status.csv | Generation-status counts, including four explicitly synthetic missing second steps. Raw original files have four fewer rows. |
| exploratory.* | Sixteen contrasts with one BH correction family at q=.10. Missing-arm models are not treated as zeros. |
| sensitivities.json | Seven scoring/conditioning alternatives; primary family and margins retained. |
| prompt_robustness.json | Content/plan language leakage under the main prompt and nine alternative prompt/model combinations. |
| leave_one_character_out.json / two_way_bootstrap.json | Character sensitivity; only three characters, partly nested with skeletons. |
| by_language_confirmatory.json | Descriptive language-restricted versions of the main family; not additional main claims. |
| gee_* | Initial target/foil binary GEE; 6/11 converged. Preserve failed/nonfinite outputs. |
| gee_target_only_* | Post hoc convergence diagnostic, 11/11 converged; changes the modeled outcome and does not replace original GEE or bootstrap inference. |
| secondary_checks.json | Post-inspection implementation of planned descriptives, original-proposal deny-use definition and DI components; not added to main family. DI suppressed for sparse rates. |
| cross_language_foils.csv / *_units.csv | Descriptive alternate-language foil rates for A-only cells; mean across alternate language references, then equal unit averages. |
| noise_calibration.json | A-version real/noise and wrong-value calibration; no new confirmatory decision. |
| scale_all_models.json | Unconditional checkpoint comparisons; cannot establish a size effect or superior perspective control. |
| capability_normalized_models.csv | Translation recovery, OC, SU and unit-normalized OC/SU. |
| audit/ | Blank, blinded annotation files. Do not fill with AI labels. |
| audit-private/ | Organizer-only keys and inclusion probabilities; **excluded from the distribution ZIP**. |
| delivery-verification.json | Independent stdlib point estimates, denominators, input hashes and blank/stratified audit checks. |
| environment.txt / manifest.json | Remote environment, main code hash, scored source hashes and analysis scope. |
| figures/ | Four scientific figures in PNG, PDF and editable SVG. |

`point`, `ci95`, and `lower95` are fractions unless a report explicitly converts them to percentages or percentage points. `ci95` is an unadjusted two-sided percentile interval, and `lower95` an unadjusted one-sided lower bound. `p_holm` alone carries main-family multiplicity adjustment. Approximate bootstrap tail p-values have minimum resolution 1/2001. A `supported` flag means the numerical decision under this analysis, not human validation or preregistered evidence.

Per-run `runs/*/summary.json` and per-model `score-summary.json` contain additional raw scorer rates including refusals. Neither their raw counts nor the broad descriptive tables should replace the filtered estimates in confirmatory.json.

The analysis dataframe pickle is kept in the remote project space and can be rebuilt from the local scored JSONL files. Local code remains standard-library only; numerical models and plots run in the remote isolated environment.

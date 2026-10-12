# Access-boundary v2 execution

The v2 scientific plan was locked locally at 2026-10-01 22:53:04 UTC, before any
v2 model response. This is a local analysis lock, not an external preregistration.
The original 760,508-response experiment and its human-review packets are kept.

The frozen campaign contains 220,088 generation calls and 206,264 scored endpoints
across the original 11 main models. It uses 20 separate calibration scenes, 96
discovery scenes, and 96 held-out original-world confirmation scenes. Hear,
Understand, See and Receive share the same world-content format; each matched
pair changes only the applicable access field. The extensions cover access
representation, five filtering methods, awareness of partial events, scripted
conversation delays and fixed-choice decisions. Actual completed record counts
must come from the response files and their generation summaries.

## Locks and evidence

- `spec-lock.json` describes the design and interface-only pilot gate.
- `final-lock.json` records frozen input, code and per-model plan hashes.
- `hardware-amendment.json` records the user's later instruction to choose unused
  GPUs and the separate operational source hashes. It changes hardware allocation
  and fixed-weight transport only. The original runner remains preserved; the
  derived runner changes only its GPU UUID allowlist and associated error text.
- All sampling, tokenizer, weight revisions, prompts, scoring and statistical
  endpoints remain as frozen. Failed or unusable planned endpoints retain the
  frozen zero convention; runtime failures are reported separately.

## H200 execution

The new task root is `/data/qianru/over-comprehension-v2-20261001` on
`gpu-server-aiscientist`. It contains isolated runtime, code, operational receipts,
raw replies, scores and analysis folders. The exact old 196-package runtime was
restored and checked, including vLLM 0.29.0, Torch 2.13.0+cu130 and Transformers
5.17.0. Existing NAS model snapshots are read-only.

Two worker slots select a GPU only if no compute process is present, memory use
is below 100 MiB, utilization is at most 5%, and the hardware UUID matches the
recorded inventory. They never terminate another job. The original GPU 6/7-only
controllers were replaced after the user's new instruction; an already running
Gemma discovery child was retained without interrupting or repeating a prompt.

Fixed official weights are fetched through the existing H200 HTTP proxy with
32 parallel HTTPS byte ranges. Each range must match its exact Content-Range;
the assembled file must match the frozen official SHA and pass the original
verifier before a worker can use it. `weight-transport-amendment.json` records
this operational addition. The preliminary local-download/SSH-upload route was
stopped after its slow uplink was measured. No local Python packages, new proxies
or port forwards were installed. New H200 caches may be evicted after their model
finishes; original NAS snapshots, raw replies, scores and receipts are retained.
The finalizer scores all planned endpoints and runs the frozen analysis after all
11 model jobs have finished or failed. A pending job is not a completed experiment.

## Validation status

The user-authorized provisional AI review is available in
`deliverables/ai-validation-proxy-20261002.zip`. It includes two independent AI
reads of 580 blind items, a subsequent adjudication performed by annotator B, a
3,211-item language/echo screen, and qualitative stimulus/guessability screening.
These are AI proxy judgments. Actual human annotations and questionnaire
responses are still absent; the original blank human packets are preserved.
The manuscript must not describe these judgments as human validation.

## Completed core manuscript and fresh validation

The four prespecified core models were verified locally on 2026-10-02: 151,864
actual records, 142,648 scored endpoints including calibration, and 62,208 complete
confirmation responses. All three frozen confirmation families pass with Holm
p = 0.00149925. Detailed results, raw-source bindings and independently reproduced
scores are under `analysis/h200-v2-20261002/`. The reporting layer adds 100
scope-matched descriptive estimates without changing the frozen tests.

`paper/arr/main.tex` now reports this four-model snapshot in anonymous ARR format.
It includes two editable TikZ figures, nine tables, and explicit pending status
for wider cohorts and human certification. The current source and standalone
figure sources passed the native compiler, including main-page and float-width
guards. Visual page inspection and a standalone PDF export remain unverified.
The previous two-boundary source is preserved in
`paper/arr/archive/pre-access-v2-source.zip`.

A distinct new v2 blind packet samples 640 semantic-use responses and 192 event
awareness responses, plus 24 unique active multilingual stimuli. Two independent
AI passes produced 1,664 response annotations; 99 items remain in the review
queue when disagreements and uncertainty are combined. Real human forms are
still blank. AI-only scorer comparisons, including exclusion counts and subgroup
readouts, are saved separately and cannot be relabeled as human certification.

Current deliverables:

- `deliverables/over-comprehension-arr-source.zip`
- `deliverables/access-v2-blind-validation.zip` (blinded forms; organizer mappings and AI labels excluded)
- `deliverables/access-v2-ai-review.zip` (explicit AI proxy provenance)

The GPU background processes were last successfully checked alive at 07:30 UTC.
Later connection checks timed out, then returned `No route to host` for the
existing jump host at 07:46 UTC. This is a loss of status visibility, not evidence
that remote jobs failed. The latest connection diagnostic is in
`analysis/h200-v2-20261002/connection-check.json`; restore the existing network
route before checking or synchronizing further results. Do not restart or repeat
planned generations merely because connectivity was lost.

Connectivity recovered at 14:45 UTC on 2026-10-02. The remote queue now reports
seven finished models and 182,808 actual responses (83.06% of planned calls):
Qwen 27B, GPT-OSS 20B, and Phi-4 completed during the outage. These three new
outputs have not yet been synchronized and independently rescored locally;
the manuscript remains the verified four-core snapshot.

The one-pass weight supplier had skipped Gemma 12B and Falcon after transport
errors. A separately logged operational recovery started at 14:53 UTC, retaining
verified chunks and all old receipts. It invokes the unchanged supplier with up
to three network-only attempts per pending model, prioritizing Gemma 12B and
Falcon before Mistral and Seed. Integrity failures do not trigger automatic
retry. Only the identified old download process group was stopped; the two
idle-GPU workers and finalizer remain active. See `weight-recovery-amendment.json`
and the latest `analysis/h200-v2-20261002/followup-health.json` snapshot.

At the 15:27 UTC heartbeat, Gemma 12B had also finished, bringing the campaign to
eight models and 189,144 actual responses (85.94%). All four discovery extensions
are now synchronized and independently rescored with exact remote-file matches;
Qwen 27B has one retained truncated reply. The combined snapshot contains 177,624
scored endpoints including calibration. `eight-model-verification.json` and
`eight-model-results.json` retain the audit and frozen analysis; confirmation
exactly matches the earlier four-core report.

The current ARR appendix now includes a scope-matched R2 discovery baseline for
all eight completed models and updated execution counts/registry. Main-text
confirmation and behavioral analyses retain the four-model cohort. The amended
source compiled successfully and the source ZIP was regenerated and verified.
Falcon, Mistral, and Seed remain pending. The download recovery is active; all
GPUs had compute processes at the last hardware check, so subsequent inference
must wait for an unused card. The half-hour heartbeat remains active until the
campaign outputs have been collected and verified.


## Latest verified snapshot: 2026-10-02 17:38 UTC

Falcon has completed all 18,272 discovery calls. The nine-model snapshot now
contains 207,416/220,088 actual records (94.24%) and 193,592 scored endpoints
including calibration. Falcon has no missing, duplicate, interrupted or truncated
records; local independent scoring exactly matches the remote score-file SHA.
Archive and run bindings are checked in `falcon-verification.json`; the combined
`nine-model-verification.json` and `nine-model-results.json` preserve the audit
and unchanged frozen analysis. Four-core confirmation is exactly unchanged.

The prespecified six-model method cohort is now complete. Its 40 descriptive
cells use all six models and the same 48 E3 scenes (1,152 endpoints per cell).
`method-six-descriptive-results.json` records the matched estimates and paired
bootstrap intervals; all 32 frozen E3 contrast points agree with their paired
cell differences. View filtering has small accessible-use losses for Understand
and Receive in this cohort, with channel intervals extending below -5 points.
The manuscript explicitly avoids extending the independent four-core pooled
noninferiority finding to each discovery channel.

The canonical ARR source now contains the nine-model baseline and complete
six-model method table, while representation/persistence and confirmation retain
their stated four-core scopes. The native compiler and page/width guards passed;
the verified source ZIP contains 20 files. Human forms and AI labels were not
modified. Human certification, standalone PDF export and visual page review
remain pending.

Mistral and Seed are still pending. At the latest remote check, Mistral had
24,012,839,899/47,176,997,457 weight bytes verified (50.90%); the recovery supplier,
two workers and finalizer were alive. All eight H200s were occupied, so the next
model must await a verified unused card. SSD free space was 105.4 GiB. No new
process was started and no completed generation was repeated. Monitoring stays
active until all planned outputs are collected and verified. The V100 read-only
compatibility findings remain separate; no alternative-precision V100 result is
included in this locked H200 campaign.


## Current GPU authorization: GPU 5 only (2026-10-02 17:45 UTC)

The user's latest instruction supersedes the earlier any-unused-GPU policy.
All subsequent H200 inference must use physical GPU 5, UUID
`GPU-63686987-a70f-607d-9886-af187b67a14a`, and only when no compute process is
present, memory is below 100 MiB and utilization is at most 5%. If GPU 5 is busy,
wait; do not select another card even if it is idle. Never terminate or occupy
another user's task.

`gpu5-only-amendment.json` records this allocation-only change. The wrapper
`harness/h200_queue_gpu5_v2.py` retains the original queue audit and restricts its
returned allowlist to GPU 5. The original queue, generator, plans, runtime,
scorer and analysis remain byte-identical. Existing per-GPU locks serialize the
two waiting slots, permitting at most one inference job on GPU 5 at a time.

The previous controllers were verified idle with no running model or child and
retired under the queue lock. New controller PIDs are 4078039 and 4078040, with
both startup logs confirming `gpu5_only`. Read the current remote
`operations/gpu5-worker-launch.json` rather than relying on these PIDs forever.
Weight recovery and finalization continue untouched. The heartbeat prompt now
requires this restriction. A reusable read-only snapshot helper is saved at
`analysis/h200-v2-20261002/h200-live-health.sh` and discovers worker PIDs from the
launch receipt.


2026-10-02 19:51 Amsterdam：用户将既有 h200 监控间隔调整为每 20 分钟，已通过应用更新同一 heartbeat。仅空闲 GPU 5、状态无变化不重复通知等限制保持不变。


At 19:12 UTC, Mistral weight preparation completed and passed the original
verifier. Its 21-file transport receipt (47,176,997,457 bytes) was synchronized
and checked locally against the fixed revision, all available frozen SHA values,
and range coverage. This is weight readiness, not completed inference: the
campaign remains 9/11, 207,416 actual responses. Mistral awaits unused GPU 5.

Seed's existing supplier is alive but waiting at its original SSD-space gate:
67.35 GiB of files plus the unchanged 20 GiB reserve require 87.35 GiB free;
83.36 GiB was available (3.99 GiB short). Inspection was limited to this task's
own directory. Its installation wheel cache is only about 3.7 GiB, insufficient
alone to satisfy the gate, so no files were deleted. Completed-model caches are
already evicted; the ready Mistral weights must be retained for its pending run.
The existing queue will reclaim that new weight cache after Mistral finishes.
Keep waiting without weakening the reserve, using other GPUs, or restarting the
supplier. See `mistral-weight-ready-receipt.json` and the latest health snapshot.

## Nine-model diagnostic report (2026-10-02)

At the user's request, the waiting period was used to analyze the verified
nine-model snapshot. `analysis/h200-v2-20261002/current-results-analysis/report.html`
contains the readable report; `analysis.json`, ten CSVs, and `manifest.json`
retain numerical results, source hashes, and checks. Regenerate this specific
snapshot with `python3 tools/analyze_access_v2_snapshot.py`. This reporting layer
does not modify frozen science, the manuscript, or any annotation packet.

New descriptive findings to retain in later manuscript revisions:

- Model-level utility controls show that Gemma 31B's low discovery leakage is
  not simply universal failure to use content, although its visual-control
  utility is lower. Low leakage must be reported alongside accessible use.
- Qwen 27B self-filtering loses allowed information: in Understand, 190/192
  accessible first-stage role responses exactly match the public event shell;
  final target use is 0/192. This is an exact-string diagnostic from verified
  raw records, not human annotation or a new semantic scoring rule.
- On the same frozen 24-scene E2 subset, the Understand prose-minus-Boolean
  effect is +5.73 points in the four core models but -5.56 points across nine
  models (95% descriptive interval [-9.38, -1.97]). Cohort scope is essential;
  the original four-model result must not be generalized to the broader roster.
- Both 96-scene sets reuse 12 target/foil lexical pairs, four per language and
  eight active strings per language. Language and lexical pair are not crossed;
  confirmation is not a test of unseen vocabulary. A separately labeled,
  post-hoc 12-block bootstrap widens confirmation intervals while preserving
  the main descriptive directions. It does not replace frozen tests.

All 36 published baseline cells, 40 six-model method cells, and eight nine-model
E2 contrasts match the independently derived diagnostics. Original four-core
confirmation is unchanged. Actual human labels remain zero; Mistral and Seed
are outside this completed-results snapshot.

These findings were subsequently integrated into the canonical ARR manuscript.
The representation table now uses the complete nine-model E2 snapshot while
retaining the original four-core comprehension contrast in prose. Accessible
controls, original self-filter stage-one string counts, lexical reuse and the
post-hoc block sensitivity are reported with their scope. The updated standalone
main source passed the native compiler and its page/width guards; the refreshed
source package contains 21 files, including `snapshot-diagnostics-data.json`.
PDF export, visual page review and real human inputs remain pending.

## Latest verified snapshot: ten models (2026-10-02 21:53 UTC)

Mistral completed 6,336 discovery replies on physical GPU 5. Its archive and all
file SHA values, pinned revision, frozen plan, runtime/protocol, record IDs and
run bindings passed local verification; independent scoring reproduced the
remote score file exactly. All Mistral replies are complete, with no missing,
duplicate, interrupted or truncated records. See `mistral-verification.json`.

`ten-model-verification.json` and `ten-model-results.json` now cover 213,752 of
220,088 actual calls (97.12%) and 199,928 scored endpoints including calibration.
The original four-core confirmation is identical; the six-model method cohort
is unchanged. Prior nine-model audits and diagnostics are preserved. Seed is
the only remaining model. The existing queue evicted its completed Mistral cache,
allowing the original Seed supplier to pass the unchanged space gate and resume
downloading. The latest snapshot shows first-shard ranges completing, 115.86 GiB
SSD free, all registered task processes alive, and GPU 5 occupied by other
compute processes; the GPU 5-only controllers continue to wait.

The canonical ARR source and registry include the ten-model baseline (40 cells)
and E2 contrasts. The comprehension prose contrast is now -4.79 points, while
the four-core +5.73-point result is retained with its scope. Compilation,
page/width guards and source/data package checks passed. The updated source ZIP
contains 21 files. The existing heartbeat remains active every 20 minutes; its
prompt now reflects ten completed models and instructs future runs to rely on
the newest verified files. Human certification and PDF visual review remain
pending.

## Active hardware policy: any verified idle H200 (2026-10-02 22:32 UTC)

The user subsequently cancelled the GPU 5-only restriction and authorized any
unused GPU. `available-gpu-amendment.json` supersedes the prior allocation
restriction while preserving it as historical evidence. The original queue,
generator, supplier and frozen scientific inputs are unchanged. The new
audit-only wrapper, `harness/h200_queue_available_v2.py`, permits registered
physical GPUs 0–7 only when there is no compute process, memory is below 100 MiB
and utilization is at most 5%. Identity and occupancy are checked again before
launch; existing per-GPU and worker-slot locks remain in place.

Only the two verified own childless waiting controllers were replaced. Their
new receipt is `operations/available-gpu-worker-launch.json`; the previous
GPU 5 launch record remains historical. The health helper reads the newest
receipt and checks actual process commands, policy hash and source hashes.
The same heartbeat is active every 20 minutes with the new rule. At the latest
check, all eight cards were occupied, Seed had completed whole-file verification
for 20.44% of its weight bytes, and the original downloader remained running.
Ten-model results and the ARR manuscript are unchanged.

## Seed weights ready: waiting for an idle GPU (2026-10-03 01:08 UTC)

Seed now has all 27 files and 15 weight shards verified (72,314,506,146
bytes), at the frozen revision `497f1dca95ebdec98e41d517b9f060ee753c902f`.
The final offline verifier, transport receipt, frozen official file hashes,
actual sizes and recorded range coverage agree. Local evidence is in
`seed-weight-ready-receipt.json` and `seed-weight-ready-verification.json`.
The original supplier completed automatic attempt 3/3 and exited normally;
its finished recovery state is evidence of expected completion, not a missing
service. It must not be restarted. Prior network failures remain preserved.

Seed inference has not started. Both any-idle worker slots remain healthy, but
all eight H200 cards were occupied at the latest check. The verified ten-model
results and ARR manuscript scope are unchanged. The heartbeat prompt now treats
the supplier as completed and continues to check for an unused registered GPU,
without redownloading weights or repeating generation. The existing automation
was read back and confirmed ACTIVE at the user-requested 20-minute interval.

## Seed migrated to Snellius (2026-10-03 10:18 UTC)

The user authorized Snellius for the final Seed experiment. The existing
27-file Seed snapshot on Snellius matches all H200 verified whole-file hashes,
sizes and frozen official hashes at revision
`497f1dca95ebdec98e41d517b9f060ee753c902f`. Staging job `27482595` completed
with exit code 0. The existing environment has the same PyTorch, Transformers
and vLLM versions; no dependencies or weights were downloaded. See
`snellius-seed-amendment.json` and the local `snellius-weight-verification.json`.

The active generation job is `27483028`, on one Slurm-allocated H100 at
`gcn139`. Its preflight recorded no compute process, zero used memory and
zero utilization before loading. The original frozen generator, plans,
BF16/TP=1 precision and decoding protocol are unchanged. At 10:18 UTC it
was generating, with 1,536 chunk records written and no interrupted markers;
partial records are not included in the completed ten-model results.

Under the H200 queue lock, Seed is `external_reserved` for this Snellius job,
preventing the original waiting workers from starting duplicate inference.
The current reservation update and `snellius-submission.json` identify job
`27483028`; the initial reservation receipt remains historical. The held job
`27482596` was cancelled before execution because Snellius denied its release.
Job `27482695` failed before model loading or prompt attempts because Slurm
global GPU IDs differed from the cgroup-visible index. Only the new hardware
adapter was repaired; both failures and scheduling repairs remain recorded.

The existing monitor remains ACTIVE every 20 minutes and checks Snellius plus
the H200 reservation. After completion, synchronize and independently rescore
Seed, verify every planned ID and binding, then mirror the verified evidence
to H200 before marking its queue record finished. Update the eleven-model
statistics and manuscript only after that audit. Real human inputs remain
pending.

## Campaign complete: eleven audited models (2026-10-03 10:37 UTC)

Seed completed on Snellius job `27483028` with exit code 0: 6,336 raw
records, including 6,325 complete responses and 11 retained truncations.
The 25 chunk results and intent bindings, every planned ID, pinned checkpoint,
template and frozen protocol, archive/file hashes and Slurm GPU allocation
passed local audit. There are no missing or duplicate IDs, interrupted chunks
or retries. Independent scoring exactly reproduces the remote score SHA.
See `seed-verification.json`; the archive SHA is
`b4b4e24758781b07ffdd918200477c07fb7e2494829332162526d47003239edf`.

`eleven-model-verification.json` and `eleven-model-results.json` contain all
220,088 planned raw calls and 206,264 scored endpoints including calibration.
The four-core confirmation and six-model method contrasts exactly preserve
their local saved results. Earlier nine/ten-model snapshots, AI proxy labels
and the old 760,508-response study remain separate. The final representation
comparison uses all eleven models on the original 24-scene subset.

The verified Seed evidence was mirrored to H200 before its locked queue
record was changed to `finished`. The original H200 finalizer then completed
normally, without materializing any missing phase. All fifteen analysis score
hashes and non-floating fields agree with the local aggregate; numerical
differences are confined to floating-point last places, with maximum absolute
difference 2.22e-16. Both reports are retained in
`h200-finalization-verification.json` and `h200-finalized-results.json`.

The canonical ARR manuscript and source archive now include all eleven models,
44 baseline cells, final representation contrasts, and the H100 hardware
disclosure. The current standalone source passed the native compiler, page and
width guards, and source/data package checks. The 21-file source archive is
95,900 bytes, SHA
`bd90996eb790a1f146a94e3dc904ea9af6b4c8f7c0eb0ecaca5e444584f70758`.
The existing monitor was paused through the app and read back as PAUSED; the
chat remains open. Real human labels, native review, guessability responses,
PDF export and visual inspection, and submission metadata/checklist remain
pending. AI proxy annotation is not human certification.

2026-10-03T11:35:27.731480+00:00

## Manuscript revision: capability, position and independent AI stimulus audits

The article now uses the title `Role-Playing Language Models Use Information Their Characters Cannot Access` and four research questions, with an eleven-model discovery heatmap in the main text. Original four-model confirmation and six-model methods remain unchanged. The frozen specification explicitly defines unconditional primary and capability-conditioned secondary estimands. The .85 secondary comprehension result is 50.98 [48.36,53.67] pp over 1152 endpoints and nine eligible model-language units; per-boundary state-correct results and the additional gated pooled 65.93 [64.82,67.14] are retained separately. No item-level eligibility or new confirmation test was invented.

The choice plan is deterministic and only approximately balanced: 18 A-first and 14 A-second scenes, with identical ordering/questions within each A/B pair. New position-stratified and equal-position descriptive sensitivity results preserve the effect (full-context 49.11–63.00 pp). The original effect is unchanged. Audit sources and checks are in `analysis/h200-v2-20261002/revision-audit/results.json`.

At the user's request, two independent subagents each reviewed all 24 paired Chinese/Japanese/Spanish stimuli, producing 48 explicitly AI-only judgments. Meaning labels disagree on three items; eleven are uncertain in either review. No native/human qualification or empirical guessability is claimed. Forms, notes and summary are in `analysis/validation-access-v2/ai-proxy/native-review-*`. Real native forms remain blank.

The human packet preserves the original 832 response items and adds 192 diagnostic foil/ambiguous cases, 128 choice responses, paired native forms with six reviewer slots, and a 96-question guessability task covering all 48 active canary-language units. Enriched samples are outcome-informed diagnostics, not population F1. Three evaluator runs on blank foil/choice/occurrence forms correctly return pending labels without human estimates. All original packet files remain byte-identical.

Current main source and standalone heatmap compiled successfully with the native editor; page and float width guards passed. The new SVG preview was visually inspected. Source/AI/human archives are rebuilt and validated. Whole-PDF export and visual page QA, real human annotations, native validation and guessability responses remain pending. No further generation or GPU usage was required; the completed experiment monitor remains paused.

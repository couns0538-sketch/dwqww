# Astra R8 Job 2 — UNPROVEN

## Six-hour continuation — active

New authorization starts 2026-11-02 21:51 UTC; final review reserved for
2026-11-03 03:21–03:51 UTC. Scope, storage and no-training limits remain unchanged.
Plan: `QUALITY6H_PLAN.md` at repository root. Milestone approvals below cover
their pinned source files; final refreshed handoff is still pending.

Saved the three user-requested future engine skills under `skills/`: build proof,
exact SIMD parity and ABBA timing. All twelve payloads (including complete MIT
licences) exactly match source Git blobs at crew-skills commit 27752e05. Python
AST parsing, frontmatter and local-link checks pass. The generic Skill Creator
validator is unavailable in the pinned runtime because PyYAML is absent; no
installed package was changed. No build/SIMD/timing job launched.

Strict PGN milestone: 20 failures reproduced before fixes, plus invalid UTF-8
reproduced separately. Frozen suite: 165 tests + 11 subtests PASS. Focused reviewer
approved five pinned source files before actual corpus validation. The strict
1M-position gate-PGN freeze passed in 225.243 seconds and reproduced
`803daf0fd7e5d01d18ec182d5117e7c1d5133534a288b92e7d674a710b50ee66`.
The 100k legacy train/validation hashes remain identical. No-flag parser behavior
is unchanged. Prior handoff requires refresh for the changed local records module.

Broader descriptive audit: `profile_corpus.py` passes 11 focused checks. Second
narrow review approved its frozen source and the 15-source plan. A 100k-row
benchmark on shard 003 passes in 5.690 seconds including hashing the complete
645 MB source. Planned full scan: closed shards 001,002,003,006,009,012,015,018,
021,024,027,030,033,036,039, one CPU at BelowNormal. Every inspected data row gets
a full-board check; reservoir samples are audit evidence only. No training data
or holdout/game-separation claim. Complete results pending.

Converter admission milestone: 15 failures reproduced before repairs, then an
actual Windows alias-retargeting failure reproduced and fixed. Full suite: 192
tests + 11 subtests PASS; 23 focused checks pass after expanding legacy output
identity to filenames and stats.json. Small focused review approved the frozen
converter before the next 100k/all-artifact and 1000-mirror reruns. Both now PASS:
all three legacy artifacts (train, validation, stats) match exactly; 1,000 actual
result records and 1,000 mirrors pass the literal orientation oracle.
The no-flag configuration/parser path remains unchanged. Corpus audit has
completed 13,593,220 rows in its first three sources without malformed positions;
their score/result correlations are 0.6647, 0.6614 and 0.6599. Remaining sources
are still being inspected; these are descriptive data statistics, not strength.

Metadata admission milestone: 22 malformed-field cases failed before repair.
The full frozen CPU suite passes 222 tests + 11 subtests. One narrow read-only
review approved records.py SHA256
`85e065c4727e28569fd6b8685fa347e5aa7e9337c9cbb74a2d78485a395ee2fb`.
Actual read-only replay then accepted all 999,953 cleared training rows and all
1,000,000 separate capture-cohort rows, with unchanged payload/source hashes.
Malformed provenance, optional depth, raw-score types and Lichess result claims
are rejected; existing valid metadata is preserved. No training has run.

Handoff completeness milestone: 20 regression failures reproduced omitted or
inconsistent evidence being accepted. Fixed required tooling/source accounting,
clearance conservation and original-cohort binding, attached sign/mirror proof,
integer types and historical migration restrictions. Full suite: 242 tests +
11 subtests PASS; 41 focused checks then pass including historical compatibility
and manifest mutation. The reused reviewer APPROVED the exact frozen change for
refreshing the original pinned handoff. Actual refresh follows this checkpoint.
The first seven fully profiled sources contain 45,255,639 valid rows, zero invalid,
zero in-check and zero mate-score rows. The same frozen audit will inspect the
other 22 closed 001–039 sources in a separate run after handoff preflights, within
the two-worker limit. Complete corpus results remain pending and UNPROVEN.

Actual refreshed handoff PASS, source 5012035c: both CPU recipe preflights, strict
verification before publication and again using the published path. New manifest:
`C:/astra8_data/quality6h_20261102/handoff_v1/manifest.json`, SHA256
`818008e05d581bbcef5e3332840f5e7eb208b0ce84e085fef90aff0f57c67fd8`.
Same 999,953 rows and sample hash; Pearson 0.6635950368 and 1,000 mirrors PASS.
The complementary 22-source scan is now running as the second CPU worker.

Aggregate CPU-budget correction: the prior `workers=2` filter created two pool
processes while its parent parsed/wrote rows. A red allocation test reproduced
the budget violation. It now uses one parent plus one child, with both counts in
the receipt. Filter changes independently APPROVED; fresh million-row timings
are pending after both profile scans finish. Earlier keep counts/hashes remain
valid, but their two-pool-worker times do not qualify a two-total-worker claim.
The v1 handoff above is now historical for source 5012035c; a new tooling-bound
manifest must follow the filter correction before current-source crew use.

Descriptive report milestone: full pre-review-fix suite 255 tests + 11 subtests
PASS. Reviewer found impossible moments and contradictory outcome marginals could
pass the new reporter. Five red cases reproduced both findings. Exact integer
variance/covariance and outcome-marginal checks fix them; 14 reporter tests PASS,
then two positive zero-variance/unknown-result checks PASS. Focused recheck
APPROVED reporter SHA256
`01e8b6ac924cba16205809ef405040e1cfafd404aef94bf102b335834d7a3a4c`.
The reporter requires complete disjoint coverage of all 37 intended sources and
does not grant training readiness. Actual combined report awaits both scans.

Tests used only one temporarily yielded owned audit worker, verified by exact
command, ancestry and frozen runtime. Every slot receipt records successful
resume and zero CPU use while suspended. No crew process was changed; profile
elapsed times include these recorded yields and are not filter benchmarks.

Native data-compatibility helper milestone: sample identity is now pinned before
and after UCI execution. Empty, invalid-board, multiline and fullmove-zero FEN
samples are refused before engine launch. Default24 source rows remain unchanged;
an explicit bounded 1..10,000 limit supports the later corpus-reservoir check.
Ten initial failing cases cover four proof/input defects and six new interface
checks; reviewer found the library's fullmove-zero normalization, reproduced as
one additional failure and fixed. Final12 helper tests PASS; focused recheck
APPROVED source3480854bfbab2291967f88fdf192b6502d73172bbe72637581010b74011c391e.
Actual expanded Forge proof is pending the complete reservoir. No engine code,
binary, network or running crew process has changed. UNPROVEN.

First complete descriptive scan PASS: 118,341,318 rows across15 sources, finished
2026-11-03 00:19:29 UTC. The wrapper confirms unchanged runtime and successful
exit. Full original logs, summaries and bounded reservoirs are preserved in
evidence/quality6h/profile_first/. The complementary22-source scan continues.

Abrupt interruption proof PASS on5,000 authored normalized rows through the
actual filter: only its exact owned fixture process tree was terminated after
flushed partial output. Existing partial output is preserved/refused; fresh retry
and uninterrupted hashes match. Reviewer identified a launcher-exit cleanup race;
one red mocked case reproduced it, disappearance is now tolerated and wait is
guaranteed. Focused recheck APPROVED. Current frozen full suite:274 tests +
11 subtests PASS in123.98 seconds. This is fixture failure-handling proof, not
production-cohort crash qualification or a resumable-loader claim.

## 30-minute follow-up audit — complete and independently approved

2026-11-02 21:04–21:40 UTC (36 minutes). User requested an additional 30-minute bug/integration audit. Confirmed and fixed:
entrypoint readiness bypass and missing output admission; late RNG seeding in
installed npt (locally preseed before delegation); malformed/conflicting PGNs;
boolean Lichess labels; mid-read input mutation; converter partial publication;
incomplete verifier bindings and nonfinite/impossible correlations.
Source candidate `be2246d6718ab199a0cf7f11618673bef3d257e0` independently approved
before fresh validation. Evidence: `evidence/audit30/`; full files under
`C:/astra8_data/audit30_20261102`. No training/GPU or engine changes.

| Check | Fresh audit result |
|---|---|
| Frozen CPU suite | PASS: 133 tests + 11 subtests; installed small-model initial parameters match after pre-seeding |
| Legacy converter | PASS: 100,000 source rows, separate train/val SHA256 equality |
| STM results | PASS: 1,000 actual records and 1,000 mirrors |
| Determinism | PASS: 1M check/mate rows twice, same payload hash; 84.300/84.410 seconds, 11,862/11,847 positions/s, two workers |
| Strict PGN parser | PASS: separately pinned 1M capture cohort reproduces prior hash; 176.250 seconds, one worker |
| Forge compatibility | PASS: exact FD3A5190 SHA256; 62 FEN/perft2 checks including edge positions and mirrors; all five baseline benches |
| Handoff | PASS: strict published verification, both actual CPU preflights, Pearson 0.6635950368 and 1,000 mirrors |

Lock counts d11/13/16/20/22: 312866 / 862329 / 3024920 / 12389307 / 34048354.
The first native probe used an incorrect `UseNNUE=false` assumption and failed
bench identity. Its logs are preserved. Reproducing the recorded crew OFF options
(`UseNNUE=true`, Threads=1, Hash=16) passes; no engine or net was changed.
Perft proves state/move compatibility, not evaluation quality or net export.

New manifest SHA256: `7afdcb408bc25b01644b81e7e2f89d78298de7c1d7139547cc99e90e405a8c1d`.
It binds the reviewed local runtime migration, unchanged installed npt, complete
holdouts and 999,953 training rows. Prior handoffs remain historical evidence and
deliberately fail current runtime identity checks. The 10,000-row sample is unchanged.
Final retained artifacts: 9,299,020,702 bytes (<15 GB); C free 150,323,085,312
bytes, D free 63,237,668,864 bytes. F remains read-only.
True qsearch remains BLOCKED because the lock UCI lacks the required oracle.
Original self-play best moves remain unavailable; capture uses a separate cohort.
Final focused review APPROVED `de96deb145a7228c115b1b4461da43e153b8eff6` after
two closeout fixes: timeout diagnostic preservation and exclusion of the packaging
process's then-open log from a separate corrected inventory. Original receipts
remain intact. The additional timeout regression passes and the final native
probe repeats all 62 perfts and five pins. Reviewer independently verified 31
final candidate/evidence pins, 696 small inventory hashes, six large lengths and
the separately disclosed packaging-log hash; main rehashed all 702 inventory
payloads. No remaining review blocker. Current record:
`evidence/audit30/correctness_record_final.json`; Forge evidence checker PASS,
no issues (`forge_check_final.log`). This checks record consistency, not strength.
Only documentation/evidence closeout follows the approved source. Strength remains
UNPROVEN; Engine NNUE and Engine QA retain the training and gate work.

## 2026-11-02 STM-format follow-up — reviewed handoff

Execution base: `7a8e22e8e2dad094f383ded125572d28aef10ace`. User selected STM
results in both binary and JSONL and subsequently authorized C: output with a
50 GB reserve. New artifacts: `C:/astra8_data/stm_v1_20261102`; no old data moved.
Version 1 uses byte29 mask, byte30 STM L/D/W=0/1/2, byte31=1. Legacy no-flag
records remain unchanged. Historical evidence below applies to the old candidate.

| Success test | Fresh result |
|---|---|
| 1 Legacy identity | PASS:100,000 source rows; train and val separately byte-identical; small PGN comparison also passes |
| 2 STM result round-trip | PASS:1000 actual converter records plus1000 mirrors, independently reviewed literal oracle; version0 decode covered |
| 3 Determinism | PASS:two million-row check/mate runs have identical payload hashes |
| 4 Deliberate failures | PASS:check,capture,en passant,promotion,mate,ply,quiet,all-off; malformed version/mask and output-safety regressions |
| 5 Million-row keep rates | PASS for measurable rules; capture measured on a separately pinned million-row gate cohort; qsearch BLOCKED |
| 6 Sign and mirror | PASS:Pearson0.6635950368 on999,953 cleared rows;1000 mirrors; unknowns excluded |
| 7 Handoff | PASS:sample,90-output hash inventory,both CPU preflights,post-publication verification,final independent review and evidence checker |

Expanded CPU suite: **89 tests + 11 subtests PASS** (`evidence/stm_v1/full89_cpu.log`).
All-off/check/mate/recipe A/B each keep1,000,000; ply<=160 keeps909,569.
Separate capture cohort keeps849,465/1,000,000 (84.9465%),80.579s,12,410positions/s
with2 workers. README contains each single-rule timing; original self-play has
no best moves and its capture rate remains unavailable. No cohorts are pooled.
Two converter/resource review findings and refresher boundary regressions were
fixed with preserved red/green evidence; see REVIEW_LOG. Warnings are existing
Torch deprecations and the no-optimizer-update checkpoint/scheduler test warning.
Exact FD3A5190 binary/hash and matching build-source receipts now verified;
bounded UCI handshake PASS, no search. True qsearch remains BLOCKED.
Completed gate PGNs passed provenance/source review and complete before/after
hash checks; the measurement-only freeze completed in154.903s. It is not mixed
into either training recipe. Handoff manifest SHA256:
`67beceef2a033d62d6d8cf75dce8284b1935e5dfa65c75c6f2fde253c7b4a8df`.
Sample:10,000 rows,3,139,111 bytes, SHA256
`c7394f11aebf2e76a2e5a1b8e834c8b5b92676180f5896e8ac30062472f7462c`.
Retained C/D/F artifacts:7,577,399,368 bytes (<15GB); latest C free156,717,297,664
bytes and D free63,678,509,056 bytes. F stayed read-only under the C override.
Production converter/helpers, engine, npt adapter/trainer and records module are
unchanged. No training, GPU, net export or strength match ran. All strength UNPROVEN.

Final fresh read-only reviewer APPROVED source candidate
`555cfb9b0aaec4699362dfc2c8acdc1fe9027967` with no blocking findings. It checked all
65 runtime/tooling hashes,11 reviewed-source pins,74 small inventory hashes and
the lengths of16 large files, both manifest copies, sample, exact lock/oracle
references and gate provenance. Full large-payload hashing was performed by the
main validation, not repeated by the reviewer. Forge evidence checker PASS with
no issues (`evidence/stm_v1/forge_final_check.log`); this is record consistency,
not a playing-strength verdict. Closeout changes only documentation/evidence.
Next owners: Code Review, then Engine NNUE for training and Engine QA for separate
FD3A5190/UHO,8moves_v3 and WAC300 gates. No crew messages or training were sent/run.

Ruling: latest explicit C: authorization supersedes the earlier F-only output
rule and historical D-only exception. Old D/F roots remain read-only and count
toward the aggregate 15 GB limit. User's milestone reviews supersede the generic
executing-plans skill's one-review default. No training/loader/engine changes.

## Historical candidate and evidence (preserved)

Base: 9761eb367c3ae4e541fc316380699f78eb493a3c. Isolated branch astra-r8-datafilter.
Implementation, CPU validation, final independent review and evidence checker complete.
The cleared cohort has data/adapter clearance only. Training and strength are UNPROVEN.

| Success test | Status |
|---|---|
| 1 Legacy identity, 100,000 rows | PASS — train and val hashes separately identical |
| 2 Result orientation, 1,000 rows | PASS — reviewed table, 1000 mirror checks |
| 3 Determinism | PASS — two 2-worker runs, identical record/metadata hashes |
| 4 Deliberate failures | PASS — enabled-rule and malformed-input fixtures |
| 5 Million-row audit | PASS for measurable rules; capture/qsearch BLOCKED |
| 6 Sign audit | PASS — Pearson 0.6635962860, unknowns excluded |
| 7 Handoff integrity | PASS — manifests, sample, both preflights, checker and final review |

Capture measurement BLOCKED: production self-play lacks stored best moves.
Qsearch measurement BLOCKED: FD3A5190 exposes no static/root-qsearch oracle.

Initial disk check: C: 174030757888 bytes free; D: 83882475520 bytes free.
Production converter and two helpers copied unchanged into baseline and SHA256 recorded.

## Execution ledger

Source of intent: user-supplied Job 2 plan. No separate spec supplied.
Interfaces: normalization precedes legacy filtering/clipping; metadata follows identical
dedup/shuffle indices; adapter consumes full FEN and signed STM targets, not REC binary.
Ruling: user-required four milestone reviews override executing-plans' one-review default.
Ruling: use supplied plan's policy pending missing separate policy/exclusion text.
Milestone 1 reviewed: result bytes and legacy selection inspected; validation gaps
fixed with four failing regression tests, then green. Lichess/normalized converter
routes added; baseline byte preservation pinned with .gitattributes.
Milestone 2 resource guard fixes under focused recheck before million filtering.
15 CPU tests pass using installed npt native FEN API (no GPU/training).
Frozen cohort: shard001 rows 1..466506, shard002 rows 1..533494.
User enlarged working budget to approximately six hours. User explicitly permits
D-only validation while F has 47.46 GB free; F remains read-only.
Next: legacy100k/orientation audits, two-worker million filter, adapter integration.

Latest: legacy identity and orientation audits complete. Default filter keeps
1,000,000/1,000,000; optional ply<=160 keeps 909,569, drops 90,431. Check/mate
counts are zero in this preselected self-play cohort. First 2-worker run:
71.186 seconds, 14047.70 positions/s. No best-move metadata; all results known.
Full holdout013/014 scans still running; training readiness remains pending.
Milestone3 review found missing npt logger interface and incorrect nonzero GPU
dispatch acceptance. Fixed; 37 CPU tests now pass including installed entrypoint
construction (stops before training) and real CPU checkpoint/scheduler round trips.
Warnings: installed Torch deprecation notices and expected scheduler-before-step
warning in a no-optimizer-update checkpoint test. No training/GPU work performed.

## Final measured candidate

- 41 CPU tests passed (`evidence/final_cpu.log`), including actual installed
  entry-point construction stopped before training, native feature/forward/loss
  checks, exception cleanup, sampler and real checkpoint/scheduler restoration.
- Legacy train SHA256: `f7892da3e661415af787015313d1720231a76a5c0b3f063a07d9f830c7ec874f`.
  Legacy validation SHA256: `b9db9883acadecad421a09d61242334898b0bbe8614a91766e1e2b59766f3eaa`.
  Old/new match separately; 91,519 train + 924 validation metadata rows align.
- The 1000-case reviewed orientation table and mirrors pass. An additional
  independent literal oracle checks 1000 original raw self-play source rows.
- Million-row independent audit: check=0, mate=0, ply>160=90,431; default retains
  all million, optional ply<=160 retains909,569. Repeated two-worker payload hash
  `dc360134f1a195fccb91349474a4beb008b444ac69249257ba8dfa7e18f92dc0` for both streams.
- Original complete holdout audit **FAIL**: 24 board+STM matches in013 and23 in014.
  Original failure preserved. A separately reviewed, explicit split stage excludes
  their47-key union, preserving all other rows/order/duplicates. Complete scans:
  013=10,000,000 rows;014=6,388,575 rows. Cleared overlap is zero for both.
- Final matched-recipe selection: **999,953** self-play rows, 0 Lichess; separate
  validation:16,384 rows from013 only. Cleared score/result Pearson **0.6635950368**.
  Unknown-result exclusion is tested; this production cohort has no unknown results.
- Sample:10,000 rows, **3,139,111 bytes**, `sample/positions.jsonl`.
  Final manifest SHA256 `0b75136d5d3ead9881b8dc78f0b46ee55d918de499884272c790356f8001d4bb`.
- Both recipe CPU `--check` preflights PASS. Runtime pins include actual imported
  npt files, adapter files and native DLL SHA256
  `88c0146804524af31cc724af39b122b5cd07e61833349c1a2cb66a28feb3939c`.
- Latest reserve reading: C167,813,480,448 bytes; D83,613,192,192 bytes;
  F47,239,548,928 bytes. User authorized D-only validation with F read-only.

Ruling: explicit holdout split exclusion is necessary to preserve holdout separation;
it is separately named/reported, never hidden inside the independent filter.
Ruling: recipes are bounded-cohort recipes with baseline hyperparameters, not a
claim to recreate the full305M-row baseline within the15GB artifact budget.
Epoch-boundary training resume only; sampler-row resume is independently tested.

Windows checkout limitation: the pinned tree includes both `source/a` and
`source/A/child.txt` under validation/astra-a1-data/final_review/package_casefold_boundary.
The case-insensitive checkout cannot materialize both. Its unstaged omission is
not included in this branch's commits; no unrelated fixture was edited.

Final independent reviewer APPROVED candidate
`415dcce34d6b40119ba6972ec0310d7a03d2d2be` for the documented CPU-verified
data/adapter handoff, with no blocking defects. It independently checked frozen
source hashes, manifest/sample equality, checkpoint ordering and complete holdout
evidence. Forge correctness evidence checker PASS with no issues
(`evidence/forge_evidence_check.log`); this checks record consistency, not Elo.
Production converter/helper hashes remain unchanged and match pinned Git blobs.
New artifacts measured **2,799,406,584 bytes**, below15GB. Final closeout changes
only documentation/evidence; the approved implementation remains unchanged.

Handoff order: Code Review (approved) → Engine NNUE → Engine QA. Engine NNUE owns
any training; Engine QA owns FD3A5190/UHO/8moves_v3/WAC300 gates. No training, GPU,
engine, production data/network or crew process changes. All strength UNPROVEN.

# Astra R8 Job 2 — UNPROVEN

## 30-minute follow-up audit — in progress (2026-11-02 21:04 UTC)

User requested an additional30-minute bug/integration audit. Confirmed and fixed:
entrypoint readiness bypass and missing output admission; late RNG seeding in
installed npt (locally preseed before delegation); malformed/conflicting PGNs;
boolean Lichess labels; mid-read input mutation; converter partial publication;
incomplete verifier bindings and nonfinite/impossible correlations.
Frozen CPU suite:133 tests+11subtests PASS. Regression failures and fixes are
under `C:/astra8_data/audit30_20261102`. No training/GPU or engine changes.
Independent re-review, native Forge FEN/bench smoke and refreshed handoff pending.
The prior handoff remains preserved historical evidence; changed local runtime
files deliberately invalidate it until the new strict handoff is published.

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

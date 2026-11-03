# Astra R8 Job 2 — UNPROVEN

## Current continuation — active, UNPROVEN

User extended again at 2026-11-03 04:22 UTC: four further hours of improvements,
then a full review/fix hour. Current schedule: 04:23–08:23 UTC improvements,
08:23–09:23 UTC deep review, repairs and verification. The earlier 05:37–06:37
review window had not started and is superseded.
The previous pause preserved all work. Current queue: EXTENSION5H_QUEUE.md;
the repository-root QUALITY6H_PLAN.md preserves the earlier plan.
No engine changes, training, GPU or crew-process interference is authorized.

Latest observation at 06:16:39 UTC: 209,163,894 rows checked, 26 source files
closed, zero rejections reported. Both workers remain BelowNormal/one thread;
D: has 57,465,634,816 bytes free. This is IN_PROGRESS, not full-corpus proof.
The observation is preserved as extension5h_20261103/progress_20261103_0616.json.
The exact audited records.py snapshot is retained with SHA256 a8ef0f43...7360be
for later function attribution. All 12 saved build/SIMD/timing package files
match their recorded Git source blobs, including the full MIT licences.

At 06:00:23 UTC the two strict source-admission scans have checked
172,413,894 rows, with zero rejections so far. This corrects the prior checkpoint's
premature 05:56 timestamp for the rounded progress count. They remain in progress
and occupy both allowed CPU slots. Entrypoint regressions now also cover
manifest replacement after verification, during runtime initialization, and
immediately before delegation. These authored tests have not run yet. Focused
review confirmed one additional draft union-receipt race: parsed JSON and its
recorded digest must come from the same bytes. That repair is queued with its
regression; it does not affect the running scans. No pending fix is accepted.

User correction recorded in R12_HANDOFF.md: use only FD3A5190 and bench
312866/862329/3024920/12389307/34048354; startpos/Kiwipete perft5 are
4865609/193690690. Existing R8 native checks use the corrected bench pins;
no rejected sequence was found in R8 tools/evidence or saved engine skills.
The protected v7 manifest hash was rechecked and matches. R12 must be based on
the final reviewed R8 tip (d080df79 or later), not e526fc12. The two cleared
JSONL streams are intentionally identical; both are 315,036,094 bytes with the
same recorded full SHA256. Fresh file hashing and perft5 are queued until a
compute slot is free. D: had 58,082,119,680 bytes free at this checkpoint.

Developer-tool milestone: Ruff exposed a confirmed false PASS under Python
-O/-OO in audit proof checks. Six failures were reproduced before explicit
runtime validation replaced the assertions. The focused reviewer APPROVED the
seven-file repair; 56 affected tests and all 16 optimization tests PASS. A fresh
full run PASSES 360 tests and 11 subtests in 340.70 seconds, with unchanged
source/runtime pins. Fresh v7 verification PASSES: 100k legacy identity, 1,000
binary outcomes and 1,000 mirrors, three bounded 10k filter passes, both CPU
preflights and strict published verification. Manifest SHA256:
`52f39e0ceeb6fc6c63422514296b928b308ede862754e8d69addde1aa44fc720`.
Older v6 evidence remains attributed to its original source.
The two quick runs briefly overlapped and are excluded from resource evidence;
full verification runs alone. No crew process was touched.

The unchanged baseline passed all 344 tests with branch instrumentation in
390.47 seconds. Measured main-process coverage is 73% statements and 66% branches
(71% combined), including audit utilities;
untraced child/earlier standalone experiments are not included in that percentage.
All 1,200 original generated chess/metadata/PGN examples PASS on the pre-fix
source. Hypothesis 6.170.14/Coverage.py 7.17.0 are isolated under C: (3.02 MB
expanded), with full licences and no installed npt changes. CodeRabbit 0.9.2
is authenticated with ten included reviews reported; no remote review yet.
Research: DEV_TOOLS_RESEARCH.md. GitHub searches found no branch PR or open
datafilter issue at this checkpoint.

Additional generated checks PASS: 500 one-to-four-game PGN streams; 2,735 unique
native fixtures, including 218 in check, three legal en-passant states, ten
castling states and fourteen promotion states. Adding seven fixed edges and all
mirrors gives 5,484 exact-lock perft2 checks; all five bench pins match. This took
29.234 seconds overall. The first harness attempt failed only in its category
counter on an intentionally missing best move; its source/logs are retained,
and the corrected counter records missing values separately. No tool bug or
training-data result is inferred from that harness repair.

Isolated Pyright 1.1.414 analyzed all 23 core Python files in 5.434 seconds and
reported 30 diagnostics. Focused inspection found typing/interface limitations
with no reachable runtime defect established; individual dispositions are saved.
Its first configuration
analyzed zero files because absolute config include paths were ignored; that
attempt is preserved and explicitly is not clean evidence. No global tool or
installed npt environment was changed. About 250 MB remains under the output cap.

New current-parser corpus audit: 38 affected tests PASS after focused review
found and main fixed two false-proof risks. The audit now matches the filter's
universal-newline input handling, hashes the original bytes, and verifies complete
reference coverage instead of trusting a flag. The pilot PASSES all 466,506 rows
in 25.329 seconds (18,418 positions/s), matching complete SHA256/producer MD5.
Reviewed full-source execution started at about 04:42 UTC: two single-worker
BelowNormal partitions covering 143,016,179 and 161,983,394 rows respectively.
Expected duration is about 2.4 hours, allowing three hours conservatively.
Only receipts/logs are emitted. Both are in progress; no full-corpus admission
claim is made until their disjoint 37-source union is independently verified.

At the 05:10 UTC checkpoint the two scans have passed more than 45 million
rows with zero rejected rows so far. A draft union verifier and adversarial
tests are prepared but not executed while both CPU slots are occupied. Focused
inspection found a runtime-provenance gap in the draft; main required the actual
Python/chess versions and added a consistent-substitution regression plus a
real tiny 37-source integration fixture. This is not yet an accepted milestone.

Official Lichess-format research found two repair targets: selecting the deepest
evaluation and decoding UCI_Chess960 castling notation. The complete-FEN parser
also rejects the public export's missing counters; that restriction stays
explicit rather than inventing known ply/rule-50 state. Design and licence
sources are in LICHESS_INPUT_REVIEW.md. No Lichess corpus or training was added.
Core files remain frozen until the two admission scans finish.

Native consumer inspection found a separate concrete input defect: the installed
npt FEN parser splits only literal single spaces and stores rule-50/internal ply
in uint8/uint16 fields. The local adapter currently forwards Forge-valid text
unchanged. The focused reviewer confirmed the mismatch; a minimal Python ABI
argument normalization and counter-range repair is planned, with original FEN
metadata preserved and all installed npt code unchanged. Adversarial tests are
authored but not executed. NATIVE_INPUT_REVIEW.md records the exact contract.
Protected v7 remains unchanged; a reviewed repaired adapter will require a new
v8 handoff and both CPU preflights. At 05:20 UTC D: has 54,594,408,448 bytes free.
Further focused inspection confirmed data-index and manifest-reload races in
the original adapter. Planned identity checks bind hashes to actual read handles
and parsed manifest bytes before referenced files are opened. Fixture-only
regressions are prepared; no original dataset is modified. D: recovered to
57,670,012,928 bytes at 05:31 UTC. The two scans continue without rejected rows.

Latest progress checkpoint: 110,694,940 rows in closed per-source receipts and
18,000,000 further rows in current progress logs, about 128.7M observed, with no
rejections so far. This is not a complete-union claim. New tools/regressions are
backed up as explicitly unexecuted `.py.txt` drafts under
evidence/extension5h/draft_20261103_0542; DRAFT.json records exact source/copy
hashes and capture time. They are not imported by pytest or treated as accepted
code. Active audit logs remain outside this closed draft snapshot.

The material-admission repair is verified on source de1de94b: **344 tests +
11 subtests PASS in 261.15 seconds**, runtime unchanged. Twenty actual native
material boundary cases pass. Fresh 100k old/new identity, 1,000 results and
1,000 mirrors, both complete 1M cohorts with serialized byte identity, all 9,486
native perft2 vectors and five lock bench pins PASS. Both v6 CPU preflights and
strict published verification PASS. The reviewed final pack hashes 9,797 retained
files and the Forge checker passes all 85 references. Final handoff approval
remains pending the additional review hour. Older proofs remain historical.

| Success test | Current evidence |
|---|---|
| 1 Legacy identity | PASS: fresh 100k old/new train, validation and stats artifacts match exactly |
| 2 Result orientation | PASS: fresh 1,000 converter records and 1,000 mirrors against literal oracle |
| 3 Determinism | PASS: two million-row check/mate runs, identical full payload/metadata hashes |
| 4 Deliberate failures | PASS: 360 CPU tests + 11 subtests; rule fixtures, optimized audit failures, malformed input and publication failures |
| 5 Keep rates and timing | PASS for measurable rules at two total computing processes; separate PGN capture cohort; true qsearch BLOCKED |
| 6 Sign and mirror | PASS: Pearson 0.6635950368 on 999,953 cleared rows; 1,000 mirrors |
| 7 Handoff | v7 manifest/sample/CPU preflights PASS; historical corpus/native proof and 9,797-file inventory retained; final review and extension inventory pending |

The original self-play shards have no stored best moves; their capture rate is
unavailable. No game-ID or full-corpus holdout separation claim is made. No net
was trained, exported or strength-tested. All recipes remain UNPROVEN.

Completed corpus evidence: 304,999,573 rows across all 37 closed non-holdout
sources, zero invalid boards under the historical Python profiler check, zero
check/mate rows, Pearson 0.6567069235. Current strict Forge admission has not been
replayed over every corpus row. Optional
ply<=160 retains 285,511,513 (93.6105%). All 4,736 original-line reservoir checks
PASS. Exact FD3A5190 matches all 9,486 perft2 results and five bench pins, using
Threads=1, Hash=16, OwnBook=false and the recorded UseNNUE=true setting. The
latest native engine phase takes 26.802 seconds; reference plus engine takes 37.360.
Full profiles are descriptive only; recipes/holdout clearance remain bounded.

Fresh packaging PASS on source de1de94b: all 9,797 retained output files hashed,
seven million-row payload pairs match their measured receipts, source/runtime
pins remain stable, production converter/helpers and all twelve saved skill
payloads unchanged. See evidence/quality6h/corpus_report, reservoir_audit,
material_validation and final_pack_v3. The Forge consistency checker passes all 85
artifact references. Its scope is declared-record consistency and actual hashes,
not independent reproduction or strength. Current v6 manifest SHA256:
`669e11db6c1117191b73f9734096095bb5b99b7eefe615ef739b103a07278d5c`.
Inventory SHA256:
`cd198d5165b40dad8b0869d8e5555d7be47149fad30d8c8fce8b5e00a68650cb`.
Aggregate retained outputs remain below 15 GB (14.565 GB after packaging),
C:135.60 GB and D:58.48 GB free. All older proofs and failed attempts remain.

Timing scope: per-rule times cover processing and final input verification,
excluding initial fingerprinting and final output hashing. Complete six-case
self-play execution is 875.000 seconds (6M visits,6,857 positions/s); capture
execution is 156.812 seconds (1M,6,377 positions/s), excluding the separately
reported 225.243-second PGN freeze. Measurements belong to source 88b7c6b1;
later CR/LF admission/verifier fixes are not new throughput measurements.

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

Corrected million-row measurements PASS, source88b7c6b1: all seven outputs use
one coordinator plus one pool process. All-off/check/mate keep1,000,000; ply<=160
keeps909,569; repeated check+mate outputs have identical full payload/metadata
hashes. Separate capture keeps849,465 and reproduces preserved hash62e41480...
Full measured times/rates are now in README; complete receipts and code pins are
under evidence/quality6h/filter_budget_million/. The exact owned complementary
profiler resumed successfully after1031.812 seconds, with zero CPU use during
the yield. Retained artifacts are14.259 GB, below15 GB; old outputs preserved.

Extended the existing raw-label audit for the later complete corpus reservoir:
full-source rehash plus original-line full-FEN/score/literal-outcome comparison.
Five red cases caught Boolean/float labels masquerading as integer outcomes or
scores; explicit types now reject them. Eleven focused tests PASS. One reused
reviewer APPROVED sourcec4e786682e571d94a6a5bd320ecdc3a9b4a821058e0567f9fbc88eb1728b1743.
The actual4,736-row replay and expanded Forge proof remain pending completion of
the complementary source scan. No training-readiness claim attaches to reservoirs.

Current handoff v2 PASS, source 8ed37659: both CPU recipe preflights, strict
verification before publication and again at the published path. Manifest SHA256
`ec3d391f42eaf0cf630a7257237e03b32ca3024c84b0d393912c5565192a0604`;
path `C:/astra8_data/quality6h_20261102/handoff_v2/manifest.json`.
All 16 required tooling pins include the corrected filter and extended raw-label
auditor. Rows/sample remain unchanged; Pearson 0.6635950368, 1,000 mirrors PASS.
README/MIX_SPEC now point to v2 and an existing authorized temporary directory.
Older manifest copies remain historical evidence. No training or GPU work ran.

Single-line FEN milestone: main reproduced five failures where CR/LF inside a
JSON FEN passed board validation and was published by the all-off filter, yet
could not be used as one UCI command. Shared result-aware admission now rejects
such input without rewriting valid original text. All 81 affected metadata,
filter, converter and native-helper tests PASS. The reused focused reviewer
APPROVED records.py SHA256
`6b57af56f7b1da7161ce8c61d41a52014bfaa5b92c80f318315f92e1a77e66ac`.
Legacy no-flag routing remains unchanged. Fresh actual 100k all-artifact identity
and 1,000-result/1,000-mirror reruns both PASS in 47.035 seconds; the runtime files
remained unchanged. All three no-flag artifacts match the old converter exactly.
Evidence: quality6h/converter_line_validation. Next: refresh the current handoff.

Current-candidate closure at 01:27 UTC: full suite **290 tests + 11 subtests PASS**
in 155.93 seconds. The exact owned complementary profiler yielded 156.547 seconds,
used zero CPU during the yield and resumed successfully. No crew process changed.
Warnings are the installed Torch deprecation and the deliberate no-optimizer-update
scheduler/checkpoint test. Both recipe CPU preflights and strict published v3
verification PASS on source 7ba94a6c. New manifest SHA256
`9a7f019d757976955662381207efeededf8cc55181142271c5ae80552eef80be`,
at `C:/astra8_data/quality6h_20261102/handoff_v3/manifest.json`.
The selected payload/sample hashes, correlation and 1,000 mirrors are unchanged.

Runtime proof milestone: nine RED cases reproduced standalone verification
accepting omitted runtime pins/versions, duplicate or substituted paths, and
changed installed fixture bytes with recomputed hashes. The verifier now binds
the complete runtime set and versions to the exact immutable original manifest.
Only already authorized local modules may differ, and their current hashes still
must match. Installed npt, native DLL, loader and trainer remain unchanged.
Fifty related tests then eleven focused boundary tests PASS. The reused reviewer
APPROVED verifier SHA256
`123e38a45bd14300e14ba9eb5cddf02f2269d55a4d5b0d85b7e5959c19ec3432`.
Current-source v4 refresh follows; the original v3 proof remains preserved.

V4 closure, source 87963077: **301 tests + 11 subtests PASS** in 171.84 seconds;
runtime invariant PASS. Both actual CPU recipe preflights and published-path
verification PASS. Manifest SHA256
`ae0c454cf84c0ca30f4711afffc5854f6aa6b382dbef884e3b6e7c8e74ed95b5`,
path `C:/astra8_data/quality6h_20261102/handoff_v4/manifest.json`.
The owned complementary profiler resumed after a 172.5-second yield, with zero
CPU use while suspended. All previous data and evidence remain preserved.

At 02:01 UTC, completed descriptive reports cover 264,999,573 rows across 33
sources, with zero invalid boards, in-check positions or mate scores. Four
remaining sources are still being scanned; no full-corpus result is claimed yet.
The sequential report/original-reservoir/native runner is queued behind successful
closed profile receipts. One reused reviewer APPROVED its frozen orchestration
and the final closed-output packager; execution evidence remains pending.
Production converter/helpers and all three sample copies retain their pinned
hashes. Git ignore checks confirm __pycache__/ and *.pyc are excluded.

Evidence collection fix: broad pytest discovery previously tried to import the
archived test_with_owned_slot.py execution script. A safe reproducer failed at
its path guard before file creation or process lookup. Evidence-local collection
exclusions now preserve the archive while broad collection finds all 301 real
tests. The reused reviewer APPROVED the scoped change. Both archived/original
script copies remain byte-identical; no runtime/tooling or v4 manifest pin changed.

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

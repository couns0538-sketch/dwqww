# Review log — UNPROVEN

## Six-hour continuation: saved future skills

User explicitly requested preserving build qualification, SIMD and timing skills
for later. Main inspected the crew catalog and the three exact skill bundles at
27752e05d80d7280d7d9a83495052c03ef4ead15. All twelve saved files match upstream
Git blob identities, including each full MIT notice. Helpers parse as Python;
frontmatter and relative references checked. No implementation was changed and
no engine job ran. This is a structured self-check, not independent review.
Generic quick_validate.py could not import PyYAML in the pinned environment;
preserved that limitation instead of altering the installed environment.
Next: focused parser review after new boundary tests pass.

## Six-hour continuation: strict PGN milestone

Candidate: `evidence/quality6h/pgn_candidate.json` (five source hashes, base fe06dc87).
Original lexical preflight wraps the installed parser API without copying parser
implementation. It rejects ignored garbage, incomplete comments/variations,
missing termination, non-standard variants and conflicting semantic headers.
Result-aware conversion now decodes UTF-8 strictly; no-flag behavior is preserved.
Main self-review found an overly permissive pawn token pattern and tightened it
with regression cases. Five special-move tests initially used the library's
collection as an iterator; corrected the assertions and preserved the failed log.
Initial source tests: 20 RED failures; UTF-8 test RED; final 165 tests + 11 subtests
PASS. Native npt test warnings remain the previously recorded warnings.

One narrow read-only final_review subagent inspected the frozen five files,
immediate callers and actual installed parser interaction; no further agents or
expensive tests. All hashes matched and no blocking defect was found. APPROVED
actual PGN and legacy reruns. Main then completed the 1M real-PGN freeze with the
same historical hash and 100k separate train/val byte identity. Sources remained
frozen throughout. Next: converter configuration/source identity and broader data
profile. No refreshed handoff or strength acceptance is claimed at this checkpoint.

## Six-hour continuation: descriptive corpus audit

Reviewed profiler SHA256 730f59b003eb583bf5b4e694930fe648277c8a9f2a84062eb5aef50a6f29a41a,
tests dcddbb809816a163841a73a9f3be8224ebf05a0a59a92754408be117b70c6907.
Eleven focused checks pass: exact outcome orientation/accounting, malformed rows,
source/sidecar changes, same-metadata digest mismatch, duplicate/holdout rejection,
bounded-prefix disclosure, mirror/rule/native boundaries, empty source and UTF-8.
Second narrow read-only review inspected only those files and the resource guard.
No blocking defect; APPROVED 100k benchmark followed by the stated 15-source scan.
Main's 100k run passed. Its elapsed time includes hashing the entire source, as
explicitly recorded; it is not a pure decoding throughput measurement.
New outputs are descriptive summaries and bounded reservoir evidence, never
training inputs. One CPU leaves one available for the authorized main-agent work.

## Six-hour continuation: converter admission and complete legacy output

Initial 15 regression failures cover result-aware invalid settings, silently
skipped malformed self-play, and unbound/changing source data. Fixes affect only
--keep-result behavior. Main self-review identified an alias flaw in the initial
fix: rehashing only the resolved target missed retargeting of the original input
path. An actual Windows symlink fixture failed first, then passed after checking
the original argument again. Both fixture targets are retained.
Full suite passed 192 tests + 11 subtests. The additional all-output comparison
now checks every filename/hash, including stats.json; 23 focused tests pass.
One reused reviewer inspected only converter, audit and their two test files;
no new agent or CPU validation. APPROVED for actual legacy/orientation reruns.
Reviewed converter SHA256 2c63fd8be1a1254f1f0a58ac7bf7cb476cbe668635c0736422079ad1a9e8be4b.
Source remains frozen during the reruns. Next: source metadata and handoff
completeness checks while the separately frozen one-CPU corpus audit continues.

Actual converter reruns PASS: all three legacy artifacts match on 100,000 input
rows; actual binary outcome checks pass 1,000 cases and 1,000 mirrors. Receipts
are in evidence/quality6h/converter_identity_receipt.json and
converter_orientation_receipt.json. No converter changes after review.

## Six-hour continuation: metadata schema admission

Reviewed records.py SHA256
85e065c4727e28569fd6b8685fa347e5aa7e9337c9cbb74a2d78485a395ee2fb.
New regressions reproduced 22 failures before fixes. Main tightened malformed
FEN/provenance, optional depth/raw-score types, unknown input-kind dispatch and
Lichess evaluation rows claiming game results. Leading-zero source identifiers,
valid game:ply identifiers, and original raw label text remain unchanged.
Raw labels need not numerically equal a deliberately transformed encoded label.
Full frozen suite: 222 tests + 11 subtests PASS. One reused read-only reviewer
APPROVED the two-file milestone without running duplicate expensive validation.
Main then replayed 1,999,953 existing normalized rows through strict validation:
all pass, complete input hashes unchanged, source code hash unchanged. Evidence:
metadata_real_replay.json. Next: reproduce handoff completeness gaps while the
separately frozen corpus profiler continues. No handoff readiness claimed yet.

## Six-hour continuation: complete handoff admission

Reviewed verifier SHA256 5a8adb373d67d90ee154e595e28132f220e546e6e69e716d8373ba1dc6881c23,
refresher b4977ff26923d325dc66ac26bc8c308018a267403aadb97f128196f8f54e7221.
Twenty red reproductions showed omissions or inconsistent accounting could pass.
Main now requires the complete tooling set, ordered nonempty source accounting,
clearance conservation/original hash, bound sign/mirror proof and exact count
types. Only the exact approved historical manifest may omit the newer proof
fields during the narrowly allowed local migration. Manifest bytes are rechecked
before returning a successful receipt. This schema covers the fixed existing
cohort; future cohorts with different filtering/split accounting need an explicit
new contract, not arbitrary reuse of its readiness flag.

Full frozen suite: 242 tests + 11 subtests PASS. Two further historical/mutation
cases added; focused verifier/refresher suite 41 PASS. Reused read-only reviewer
APPROVED all four changed files and checked the actual prior manifest/clearance:
1,000,000 = 999,953 + 47, original cohort hash and both complete holdouts bound.
No new agents or repeated expensive test run. Main accepted the findings (none
blocking) and will run the real refresh and both CPU preflights next. Prior
handoff links are explicitly marked historical until the replacement passes.

Actual refresh then PASS on frozen source 5012035c. Both CPU-only recipe preflights
passed; final published-path verification passed with manifest SHA256
818008e05d581bbcef5e3332840f5e7eb208b0ce84e085fef90aff0f57c67fd8.
The selected payload/sample hashes are unchanged; 1,000 mirrors and correlation
0.6635950368 pass. Receipts are copied under evidence/quality6h/handoff_v1/.
Main inspected the complementary source plan: exactly the other 22 closed shards,
no duplicates with the first 15, neither holdout included, same frozen profiler,
one owned BelowNormal child and bounded 03:11 UTC deadline. It started only after
the CPU preflights completed, retaining the two-worker total. This source-list
extension used a structured self-check; no repeated code review was needed.

## Six-hour continuation: aggregate filter budget and descriptive reporting

Filter SHA256 b3fdda81f293dc240a68d8a129143c3db75ed4a96da8ada8202cf9a1864ea7ac.
Main identified parent computation omitted from pool sizing. Red test confirms
parent1+pool2 exceeded the requested total2. Fixed pool size to one for budget2;
receipt explicitly reports coordinator/pool counts. One reused reviewer APPROVED
this change. Payload predicates and ordering are unchanged. Prior timings remain
historical; fresh actual two-total-worker runs are required before the final claim.

New report_corpus.py combines disjoint complete source inspections, checks local
report/sample identities and source metadata, sums raw moments and writes data
composition tables. Initial 22 focused checks passed, then the full worktree
suite passed 255 tests + 11 subtests. Reviewer found two concrete issues in the
initial reporter: impossible moments accepted as undefined correlation, and
score/outcome marginals inconsistent with known/unknown coverage. Main accepted
both, reproduced five RED cases and added exact integer second-moment, variance,
covariance and marginal checks. Fourteen reporter checks pass after fixes; two
additional positive boundary checks pass for real zero variance and unknown-only
outcomes. Reused reviewer APPROVED the focused recheck; no unresolved finding.
Final reporter SHA256 01e8b6ac924cba16205809ef405040e1cfafd404aef94bf102b335834d7a3a4c;
tests 226e1e8131c55f1fd6b429c9b4c0ecc652c40e64eae0a75537a8e8ec8c144782.

Main's owned slot controller identifies only complementary audit child8776 via
exact command, parent9460, launch-script ancestry and pinned runtime. It yields
that worker while CPU tests run and resumes it in finally; every preserved
slot_receipt records resumed=true and zero CPU seconds during suspension. No
crew process or STOP/PAUSE file was touched. Profiling wall times retain this
elapsed time. Next: combined data report after both scans; corrected filter
million-row runs, refreshed handoff and final review. No report or timing result
is claimed before those actual runs complete.

## Six-hour continuation: native sample attribution and input admission

Main reproduced four existing proof/input defects: a changed sample could be
hashed after execution and attributed to earlier tested FENs; empty, invalid-board
and multiline samples could reach the engine. A before/after full input identity
now binds tested FENs, and those invalid inputs fail before launch. Six new tests
also establish the bounded --max-positions interface while preserving default24.
Ten red failures were recorded, then11 focused tests passed.

Reused reviewer found one further concrete boundary: python-chess repairs an
original fullmove0 to1 before is_valid. Main reproduced that failure and now
checks the original sixth FEN field first. Final12 helper tests PASS. Focused
recheck APPROVED source3480854bfbab2291967f88fdf192b6502d73172bbe72637581010b74011c391e
for the bounded actual corpus-reservoir run. Exact FD3 executable, UCI options,
five bench pins and120-second owned-child timeout remain unchanged. No engine
invocation occurred in these mocked regression checks. Next: actual complete
reservoir proof once both descriptive scans close, preserving any failure.

## Six-hour continuation: abrupt owned-filter interruption

Actual filter implementation on5,000 authored normalized rows: one owned child
blocks after its first flushed partial window; only its exact Popen process tree
is terminated, including Windows venv's worker. Partial records and metadata
survive, no final output is published, same-destination retry is refused, and
fresh retry payload hashes equal an uninterrupted run. Original fixture identity
remains unchanged. Initial real proof passed.

Reused reviewer found a cleanup race: a launcher can exit between is_running and
cmdline/kill after its worker dies. Main reproduced NoSuchProcess with a mocked
disappearance, then tolerates disappearance around both ancestry and individual
termination and guarantees child.wait in finally. Fresh frozen full suite:
274 tests +11 subtests PASS, including the real interruption again. Focused
recheck APPROVED test source64e8ee67e1da1b70877b535fbe545cae1b588f32b22ccc70134955c5c97c9918.
No production implementation changed in this milestone. This proves the actual
filter's fixture failure path and fresh retry, not resumable output or an unrun
production-data interruption. Next: corrected full-cohort timing runs and handoff.

## Six-hour continuation: corrected two-worker million-row execution

Previously approved filter b3fdda81... and source88b7c6b1 executed all seven fresh
million-row measurements. One parent plus one pool worker is recorded in every
receipt. All required counts/hashes match preserved evidence, including the
separate capture payload62e41480... and both repeated default selections. Complete
commands, source/code pins, reports and logs are saved in filter_budget_million/.
The original sources remained unchanged. Main's exact owned complementary audit
yielded its slot for1031.812 seconds, zero CPU consumption, then resumed. No crew
process changed. This actual run replaces historical three-process timing claims.

## Six-hour continuation: original-source reservoir verification

Extended audit_raw_labels.py rather than making another label-checking tool.
The new optional profile mode requires all complete disjoint source profiles,
rehashes full original sources, checks each selected source line with the literal
outcome table and exact full FEN/score, and publishes a bounded audit-only reservoir
after final source/profile/tool checks. Main's strict-type review reproduced five
Boolean/float equality failures, then fixed them. All11 focused tests PASS.
Reused read-only reviewer APPROVED sourcec4e786682e571d94a6a5bd320ecdc3a9b4a821058e0567f9fbc88eb1728b1743
and testsb8f0bd68abfa45630cc3d9d471f0daae59e74f19a42f4982fe27310d169be2ef.
No further findings or duplicate expensive tests. Approval covers implementation;
the full original-source replay and subsequent native proof are still pending.

## 30-minute audit: findings and first fixes

Base f05c5533. Independent read-only audit_npt_boundary and audit_data_integrity
reviewers reproduced admission/provenance failures using tiny owned fixtures.
Main accepted the findings, delegated scoped fixes and reviewed the diffs.
Red evidence: verifier_red.log (9 failures), entry_admission_red (15 failures),
integrity_red.log (13 failures), capture_result_red.log (1 failure).
One focused data-suite teardown detected concurrent code edits; preserved as
failed evidence, then reran the complete frozen suite:133 tests+11subtests PASS.
Native installed L1=8 model construction now has bit-identical parameters after
explicit pre-seeding; no training step or optimizer update executed. Exact current
diff was approved by independent final_review before refreshed large validation.

Read-only reviewer APPROVED candidate `be2246d6718ab199a0cf7f11618673bef3d257e0`:
seven changed modules and three regression files, no blocking defect. It confirmed
installed train.py creates the model before its own seed call, strict legacy
parsing isolation, input binding, admission and the two-file migration allowlist.
Main assessed the review and executed the approved identity/orientation/handoff
reruns. All passed; both published CPU recipe preflights and strict verification
pass. The strict real-PGN million-row freeze reproduces the historical payload
hash. Fresh two-worker filter repeats match, including complete input identity.

Native helper is verification-only and added after the source commit; exact hash
is in `evidence/audit30/correctness_record.json`. First probe failed because main
assumed OFF meant UseNNUE=false. The archived crew transcript proves default true;
correcting only the probe reproduces all five pins and all 62 perft2 counts.
Both probes remain in evidence; no failed result is attributed to the correction.
Focused native-helper/current-evidence review is now requested; no source edits
while that review runs. Full test and failed regression logs are packaged.

Final focused review confirmed all 65 runtime/tooling pins, 26 candidate/proof
pins, both manifest copies and both approved local runtime migrations. It parsed
the actual successful native transcript and checked the archived lock options.
It checked 696 small inventory hashes and six large lengths. Main accepted both
findings: timeout diagnostics were lost before log writes, and the then-open
package.log was inventoried at zero bytes before finishing at 529 bytes. Added
owned-child timeout capture/FAIL receipt and regression (RED then GREEN). Original
inventory is retained; a corrected inventory excludes only the active packaging
log. A fresh native probe will bind the final helper; focused recheck requested.

Final recheck APPROVED `de96deb145a7228c115b1b4461da43e153b8eff6`, no remaining
blocker. Both findings resolved; timeout RED/GREEN evidence preserved. Reviewer
independently checked 31 final candidate/evidence pins, 696 small payload hashes,
six large lengths and the excluded log's final hash. Main fully rehashed all 702
remaining inventory payloads. Reviewer reparsed the final native stdout: all 62
perft2 results and all five frozen bench counts match. Manifest remains
`7afdcb408bc25b01644b81e7e2f89d78298de7c1d7139547cc99e90e405a8c1d`.
The final helper ran after its timeout fix; no earlier result is attributed to a
changed helper. Final correctness record/checker PASS, no issues. No further source
changes; closeout only documents and preserves evidence. Audit ran 21:04–21:40 UTC,
over the requested 30 minutes. No training/GPU/export/strength run. Qsearch and
original-cohort missing best moves remain explicit limitations, not open bugs.

## 2026-11-02 follow-up: converter and resource milestone

Base `7a8e22e8`; candidate source hashes will be bound in the review receipt.
Read-only converter_audit reviewer inspecting frozen converter/codec/audits and
resource/filter files. Quick suite: 72 tests + 11 subtests PASS in
`C:/astra8_data/stm_v1_20261102/full1.log`. New assertions first failed on old
White-relative bytes; codec and resource red/green receipts are preserved.
Reviewer confirmed STM/legacy oracle, mirror transform, unchanged no-flag
selection, byte allowance and bounded filter writes. Two findings accepted:
strict C reserve must reject equality; direct legacy audit must refuse old/new/
result destinations before launching the baseline converter. Regressions failed
first (`review1_red.log`), then 16 tests + 11 subtests passed
(`review1_green2.log`). An intermediate green attempt exposed an obsolete test
expecting equality to pass; corrected that assertion and retained its log.
Reviewer rechecked both fixes and approved large validation. The 100k byte
identity and actual 1000+1000 mirrored converter round-trips now PASS.

Separate capture measurement preflight: read-only converter_audit reviewed
`audit_capture_cohort.py` SHA256
`c5d0f33ac436baeb3db37dc2de779e1c365346ddf94f854b0547356969720c75`
and its eight passing fixture tests. It independently checked gate receipts,
exact FD baseline identity, genuine Fastchess searched-move semantics and source
pins, bounded new output and post-read hashes. Approved the measurement-only
million-row freeze. This cohort is excluded from both training recipes.

## 2026-11-02 follow-up: handoff publication review

Read-only converter_audit approved `refresh_handoff.py` SHA256
`82b3faed3f0e4a9888b3f6ee976fd0906e05e7b95d05891b2d96af46550647a7`
and seven passing tests before actual refresh. Review covered the approved old
manifest pin, complete payload/source/holdout and receipt checks, fresh correlation
and1000 mirrors, CPU environment before native import, both actual preflights,
final runtime/tooling/lineage rechecks and publication. No blocking defects.
The unpublished draft's true readiness flag is required by the unchanged
`--check` interface; only the final renamed directory is the handoff.
The reviewer also parsed the guarded test launcher and confirmed adapter,
trainer and records code remain unchanged. Whole CPU suite:89 tests+11 subtests
PASS. Actual refresh and both CPU preflights subsequently passed, followed by
verification using the published manifest path. Correlation0.6635950368 and1000
mirrors passed; unchanged complete holdouts were rehashed. No training has run.

## 2026-11-02 follow-up: final independent review

Fresh `final_review` subagent APPROVED candidate
`555cfb9b0aaec4699362dfc2c8acdc1fe9027967`, no blocking defects or missing
implementation checks. Reviewed exact diff, surrounding code and unchanged
training entry point. Independently verified65 runtime/tooling hashes,11 reviewed
source hashes,74 inventory files up to10MB and lengths of16 large files; both
manifest copies and sample; exact FD lock/oracle references; Fastchess semantics
and gate receipt hashes. Both training output destinations remain absent.
It read the89-test/11-subtest log and all acceptance receipts without rerunning
expensive datasets/tests. Qsearch unsupported and original-cohort best moves
absent remain explicit limitations. No code changed during or after final review.
Closeout finding was pending-review prose only, now updated. Forge correctness
evidence checker PASS, no issues; raw logs retain original whitespace/line endings.
Next: publish final documentation/evidence checkpoint; crew handoff, UNPROVEN.

## Milestone 1: converter compatibility and result semantics

Reviewer: read-only review_converter subagent. Candidate hashes:
evidence/milestones12_candidate.json; fixed candidate evidence/milestone2_candidate.json.
Findings accepted: unknown producer bypassed mate threshold; noninteger scores
accepted; malformed PGN results silently unknown; converter lacked Lichess route;
PGN identity global across files; baseline checkout newline risk.
Fixes: strict normalization, bad-result rejection, normalized/Lichess routes,
per-source game/ply provenance, byte-preserving .gitattributes.
Validation: evidence/review1_red.log (four regressions), review1_green.log (10 pass).
Focused reviewer recheck approved substantive fixes by inspection. Large identity
test remains pending. Reviewer supplied literal 8-cell outcome oracle for 1000 cases.

## Milestone 2: filter before million-row execution

Candidate: evidence/milestone2_candidate.json. Read-only same reviewer.
Rules/order/overlap/metadata alignment and bounded ordered workers approved by
inspection. Confirmed defects: disk guard after allocation and variable subtree;
orientation audit could overwrite evidence. Both fixed; tightened derived field
types and source-row constraints as well. Regression evidence/review2_red.log.
Fixed candidate evidence/review2_fixed_candidate.json; CPU suite 15 pass in
evidence/adapter_green_attempt2.log. Focused recheck requested; million run held.

Existing freeze: started with >80 GB D free and <1 GB new outputs; completed
before guard review. Original source hashes remained stable. It is preserved.

Focused resource recheck: APPROVED for million-row run, candidate hashes matched.
Two identical runs now match hashes; default cohort counts independently agree.

## Milestone 3: adapter contracts and masked loss

Candidate evidence/milestone3_candidate.json; reviewer inspected actual installed
npt contracts. Confirmed: eight clones/finally free, signed STM semantics, lambda
shape/device/dtype, inherited loss/scaling, transient cleanup, manifest/sampler pins.
Accepted findings: missing `train.dataset`/HLL logger interface; nonzero cuda device
selector not honored by installed local_rank dispatch; missing integration test for
checkpoint scheduler repair; unequal mask lengths could bypass validation.
Fixes: explicit unavailable-HLL facade; cpu/logical cuda:0 only and LOCAL_RANK=0;
all metadata lengths checked; epoch-boundary checkpoint subclass validated through
real npt model/optimizer/checkpoint load, pre-step and already-stepped scheduler
states plus missing/malformed state. No optimizer updates performed.
Evidence: review3_red.log, integration_attempt.log (37 passed). Test model forward
uses L1=8 to bound CPU memory; exact recipe config remains L1024. Complete recipe
commands now in MIX_SPEC.md. Fixed candidate review3_fixed_candidate.json.

Focused milestone3 recheck: APPROVED for CPU-verified adapter handoff, pending
manifest/preflights. Both final recipe preflights subsequently PASS. Latest full
CPU suite:41 pass. Runtime imported-file hashes remain stable across CPU tests.

## Holdout finding and focused split-stage review

Complete audit found24/23 matching keys against complete013/014 (16,388,575 rows
combined). Added explicit separate clearance stage; original failure preserved.
Reviewer required exactly both pinned complete holdouts, post-selection source
rehash, and delayed publication until proof/receipt completion. All accepted/fixed.
Regression red:clearance_review_red.log; green:clearance_review_green.log(3 pass),
including source mutation and unpublished failed output. Candidate identity:
evidence/clearance_candidate.json. Focused recheck APPROVED actual execution.
Actual run:47 rows excluded;999,953 retained; zero complete-holdout intersection.
Both recipes share those rows. Manifests and3,139,111-byte sample verified.

## Milestone4: final evidence and handoff

Fresh read-only final_review subagent approved candidate
`415dcce34d6b40119ba6972ec0310d7a03d2d2be` with no blocking defects. It reviewed all
seven acceptance claims, converter/filter, native ownership, inherited masked loss,
installed checkpoint ordering, manifest binding and complete holdout evidence.
It independently checked every final_candidate.json source hash, repository versus
delivered manifest SHA256 `0b75136d5d3ead9881b8dc78f0b46ee55d918de499884272c790356f8001d4bb`,
and both sample copies SHA256 `c7394f11aebf2e76a2e5a1b8e834c8b5b92676180f5896e8ac30062472f7462c`.
Only closeout finding: stale pending-review/checker prose, now resolved here and in
RESULTS.md. No code changes after final review. Forge evidence checker PASS, no
issues; both recipe preflights PASS;41 CPU tests PASS. Original failed overlap
evidence and all failed test attempts retained. Approval excludes training,
training throughput and playing strength; capture/qsearch production measurements
remain BLOCKED. No unresolved implementation finding or deferred minor remains.
Next: authorized final checkpoint, then Engine NNUE and Engine QA handoff.

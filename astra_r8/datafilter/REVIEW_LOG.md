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

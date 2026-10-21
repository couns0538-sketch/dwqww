# Separate 6.4.21 capture-support review

The sealed support passed **728 independent read-only checks**: 675 evidence,
actual-schema and source checks, plus 53 capture-lifecycle checks. All 283
selected inputs were rehashed with sizes and file modes unchanged. No support
driver, helper or tests were imported or executed; no captures, engine builds,
benchmarks, timing jobs, Git or network operations ran in this review.

The capture driver is `6584ec98e24d74be636e208bfc30097a67543b992c929236405ffbddadb972fc`.
The 24-record support seal is
`b66919d52a5eaf8eb1e03b62bf766bba1d9062e416b9e33bdce460cd10284734`.
The frozen helper remains the exact executed `461a65` implementation. Static
review confirms source/proof/driver/helper authorization binding precedes output
creation, a NEW fixed output is required, and two sequential five-command
captures use the existing canonical parser, process cleanup, deadlines and final
byte/mode/helper/affinity gates. Preserve launcher stdout/stderr and the first
exit even for faults before PROVENANCE creation or during setup/storage.

Actual native 20 and 21 schemas were read directly: respectively 36 and 39
CTests, 8 active-UCI checks and 56 exact parity searches. Native20's
`engine_tests_builds_failed` field is required only for revision20; native21 uses
its actual source-mutation/retention fields and explicit first-attempt profiles.
All three candidate profiles and the root proof have 791,680 nearest checks,
395,840 target sets and 6 constexpr assertions.

The Windows20 proof matches 72 source files and 11 Wine checks. At this review,
the actual Windows21 root proof is **missing**, and no actual root capture
authorization or capture output exists. The driver requires the genuine
Windows21 status, source identity, 73 source files and 12 Wine checks. It must
remain blocked until that proof and explicit hash-bound root authorization exist.
This review is not that authorization.

The source-correspondence audit authenticated all 160 original inputs: 76 files
per tree, 74 unchanged files, two single version-label edits and 19 protected
production inputs. Historical 95-row / 61,465-integer-field probe evidence retains
`source_commit:null` and version20; no historical trace was relabelled or rerun
as frozen21. Bind the correspondence receipt and its originals when using it in
later proof metadata.

Original support preparation outputs are retained: 8/9 with the inherited-field
failure, corrected 9/9, and final 10/10. These were run by the preparer and were
authenticated without repetition. Derived positive Windows/root mocks are
explicitly unit fixtures. A reviewer-only source-string construction error
occurred before any checker file or producer mutation; its exact diagnostic and
scope are recorded in CHECKER-CONSTRUCTION-ERROR.json, with the original command
and traceback retained in the tool conversation.

[REVIEW.json](REVIEW.json) is the final verdict.
[EVIDENCE-REVIEW.json](EVIDENCE-REVIEW.json) and
[CAPTURE-LIFECYCLE-REVIEW.json](CAPTURE-LIFECYCLE-REVIEW.json) retain full checks,
identities and limitations. Initial disabled packet and its earlier review remain
unchanged. Actual captures and the later READY/enabled workflow phase require
separate source-bound reviews. No speed or Elo result is claimed.

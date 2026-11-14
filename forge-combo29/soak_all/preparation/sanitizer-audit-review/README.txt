D/E/F READ-ONLY AUDIT AND SCRATCH AUDITOR PROPOSAL

No native workloads were run. No controller, active state, production helper,
engine source, branch, tag, or repository file was changed by this task. Synthetic
fixtures use their own state/repository directories under this scratch folder;
only those isolated test fixtures exercise --apply.

Original production helper / reconstructed baseline SHA256:
69e27105d35b86040ec9363decbfb09f8f42f9e65058809f619eade710f458d0
Scratch proposed helper SHA256:
c1c1f67cb74dbd28826609418a1932b1de6beb915b418e0a3334713d7663a75d

PREPARED SCOPE
2D: ASan+UBSan, all candidates false, Threads1/2 x nodes2000/20000.
2E: TSan, all candidates false, Threads2/4, depth9, nodes0.
2F: ASan+UBSan, all three candidates true, Threads1/2 x nodes2000/20000.
Only old2D1 omits --trace. Future specifications include full trace and the final
trigger artifact. TSan has halt_on_error=0:exitcode=66 and no suppressions.
ASan/UBSan stop on the first diagnostic. No all-three-true TSan spec is present.
These are direct Searcher self-play workloads with8 seeded opening plies,
300-ply cap,Hash16,NNUEtrue,MultiPV1 and300-second game-boundary budgets.
They are separate from fastchess match coverage. OwnBookfalse is an explicitly
reported condition; this direct Searcher driver does not invoke the UCI book path.
prepared-specifications.json retains exact inspected specs and their hashes.

CONFIRMED GAPS
Production audit preserves sanitizer marker text but does not materialize a bare
exit66 when a chess SUMMARY says faults0. The before-after-exit66-frozen-baseline.txt synthetic comparison demonstrates
baseline faultPlans0 versus proposed faultPlans1.
Marker lines do not count warning events: WARNING, SUMMARY and a reported-N
footer may all describe one warning, and mirrors duplicate the evidence.
Production also does not validate actual play CONFIG/options against argv.
Its opening_moves==8*games check is not universally valid: the driver permits
an opening to end before8plies when no legal move remains.

PROPOSED BEHAVIOR
Completed chess counters remain unchanged and exact. Independent processStatus
and sanitizerCounts prevent chess faults0 being mistaken for a clean sanitizer
outcome. Nonzero exit66 without a diagnostic is explicitly unresolved; no race
is invented. A timeout/forced termination is distinguished from an engine crash.

TSan warning blocks are counted once from the primary merged runtime log.
Conflicting access stacks supply an unordered source-file/line pair; engine
frames are preferred over library wrapper frames. Creation/location/summary
stacks cannot supply a missing access location. Unsymbolized blocks stay
unresolved. Same pair across repeated/reversed reports groups together; distinct
pairs at one trigger remain distinct. Mirrored text adds provenance, not warning
counts or duplicate pair fault files. A source-pair group is an evidence bucket,
not proof of one distinct underlying bug. Runtime deduplication may suppress
repeat manifestations, so reported block counts are not reproduction frequency.
Full blocks, full runtime log, options and temporally nearest trigger remain in
fault evidence. Ten additional reproduction attempts remain pending.

Play argv/defaults are checked against CONFIG, SUMMARY and every TRIGGER.
Search count is enumerated when traced; moves are checked by the exact invariant
searches=moves+faults. Game and opening totals are labelled self-reported with
terminal-accounting and bounded-opening checks. All integer checks remain exact.

VERIFICATION
synthetic-check-reviewed.txt: passing synthetic assertions covering exit66 without
markers; faults0 with3 TSan warning blocks grouped into2 pairs; reversed/repeated
pair count2; mirrored artifact deduplication; footer-only evidence; unsymbolized
access followed by creation stack; incomplete report; diagnostics despite exit0;
timeout classification; wrong-depth rejection; legitimate short opening; full
fault artifacts and pending reproduction status.
finished-readonly-check.txt: proposed helper audited a snapshot containing only
completed real2D1, zero errors and the known no-trace limitation. Original active
2C state/workload was not audited or changed by this check.
The initial synthetic-check.txt logged4 fault files because mirrored logs still
created redundant trigger faults; this was corrected before the reviewed check,
which has2 source-pair files for3 warnings. No native race findings are claimed.

REVIEW ARTIFACTS
- audit-results-proposed.mjs: scratch full proposal; root subsequently adopted it.
- audit-results-proposal.diff.txt: diff against unchanged production helper.
- def-synthetic-test.mjs: synthetic checks, no native workload.
- before-after-exit66-frozen-baseline.txt: verified original baseline/new behavior.
- before-after-exit66.txt: check raced root adoption, saw new helper on both sides,
  and failed its expected-old-behavior assertion; no state/native work occurred.
- synthetic-check-reviewed.txt: final synthetic output.
- finished-selfplay-readonly-report.json: real finished2D1 read-only result.
Root owns any production adoption, state apply, report integration, and commits.

COORDINATOR ADOPTION UPDATE
After scratch validation, root independently hash-verified and adopted the
c1c1f67... proposal. This agent did not edit the production helper. An optional
comparison reading the live helper then saw the adopted implementation on both
sides and failed its old-behavior expectation. The preserved proposal diff was
reversed into a new scratch-only baseline; its SHA256 exactly matches69e27105...
and the repeated comparison correctly produced baseline0 versus proposed1
fault plan. Both command outputs remain retained.

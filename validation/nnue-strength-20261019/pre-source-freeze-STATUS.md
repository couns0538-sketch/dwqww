# NNUE strength package preparation

PENDING_REVIEW; candidateSHA PENDING_ROOT_SOURCE_FREEZE. No builds, engine
execution, games, job launch, commit or push were performed by package preparation.

The new bounded protocol is stored in`.github/hosted-nnue-strength/` and its
separate workflow. It tests6.4.11 versus6.4.9 at equal2+0.02 with native0/+5SPRT,
1024pairs/2048games natural cap and300minute emergency failure guard. A/A and
SPRT reserve1028fresh positions from the legally replayed original Stockfish
archive. Preparation tests are mocks and archive bytes only, never Elo evidence.

Before launch root must freeze the actual candidate fullSHA after source tests,
update protocol/workflow together, record independent review and refresh the
package SHA registry. Review gate must remain closed until all requirements pass.
See packageREADME and protocol for full conditions and failure preservation.

Validation:40/40 mocked runner tests passed (2.275s);8/8 archive tests passed,
including101MiBlog streaming. The initial39-test run hit a test-fixture startup
assumption before its250ms deadline, not a runner cleanup defect; that failure
is retained separately. The fixture now starts its simulated deadline only after
the actual mocked parent/child handshake. No engine or Fastchess was executed.
WorkflowYAML, each shell step withbash-n, PythonAST, both pool sizes/disjointness,
strictEPnone and exact separately frozen runtime order/SHA checks passed.

`PACKAGE-SHA256SUMS` currently freezes the pending-review package and workflow;
root must refresh after sourceSHA/review-state edits. Final evidence files are
runner-tests.stdout/.stderr, archive-tests.stdout/.stderr, static-check.json,
and retained runner-tests-first-attempt.stdout/.stderr.

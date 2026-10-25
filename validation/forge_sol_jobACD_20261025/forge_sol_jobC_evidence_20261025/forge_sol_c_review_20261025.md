# Job C independent source review, 20261025

Verdict: no material source-contract issue found in the bounded test-only relabel.

Reviewed exact `tests/tests.cpp` candidate against supplied h256_e12 lock. No code, engine, Git or native process was changed/executed by this reviewer.

- Only known-failure reporting and two case-specific relabel paths were added. All unrelated tests and the global ordinary-failure exit rule remain unchanged.
- WAC001 original move/alternative and minimum-score predicates remain verbatim, and the original tactical-table g3g6 / MateValue-3 expectations remain unchanged. Relabel requires exact case label, full FEN, d12, original expectations, no alternative, f6h5, score661, completed depth12 and nonempty PV starting with best_move. A changed move/score/depth/PV does not enter this known path.
- The original rook-underpromotion condition is preserved as a named Boolean. Alternate acceptance requires the exact legal c6d7/c3d2 king move, matching nonempty PV, winning score>100 and depth1. Original restricted promotion/PV, rook-win and queen-stalemate checks are untouched. A different alternative or non-winning score does not enter this known path.
- Genuine old expected outcomes remain ordinary passes. The new path does not require a particular net hash; it describes a strictly guarded observed outcome. Thus it should not be represented as network-identity verification.
- Labels retain old expectations and observed values. Comments record old6.4.24 lower bound and explicitly state exact historical mate score is unrecorded.
- Known assertions are separately counted/reported; no global failure counter is cleared and unrelated/null-pruning failures remain fatal.

Native validation was running independently. I inspected already-written candidate/unrelated-expectation log rows only; this review does not assert completion of remaining native controls, full CTest or patch applicability. Those need their own actual evidence.

Base SHA256: `93c56defd68beb9812b734594f3395b3296bb9aea81ed680ee600c528e94a7b9`
Candidate SHA256: `f74c959f6a157605f24f63309f531a822f1462ef9cae4cf46afd5bfc4eaabff1`
Review UTC: 2026-10-25T07:48:10.655474+00:00

# Native helper / UCI crosscheck

The 32 completed helper results match the UCI engine's actual completed-iteration score, depth and returned bestmove. The additional budget-exhausted root remains unlabeled by the helper.

The initial checker incorrectly treated every final `info depth` line as a completed iteration and therefore reported 3 failures. Those original results and raw streams are preserved, not replaced. Inspection of `src/search/iterative.inc:204` through line 220 explains them: an aborted iteration may emit a revised PV using its attempted depth and the previous completed score, without updating `SearchInfo.depth` or `SearchInfo.score`.

- Samples 57 and 131: completed depth 5 and helper score match; final UCI revision says depth 6 with the same score. Returned bestmoves match.
- Original row 27772: no iteration completes within 1024 nodes. UCI prints attempted depth 1, its initial cp 0 and a revised fallback move; the helper correctly returns `insufficient_budget` with null score/bestmove.
- UCI completed-info node totals and final `SearchInfo.nodes` describe different stopping points. The former do not exceed the latter; revised lines at the cap show 1024.

This exposes an existing UCI metadata ambiguity and documents why a data pipeline must not blindly relabel from the final info line. No engine code or label was changed to force agreement. `source_grounded_addendum.json` records each comparison and the source excerpt/hash. Timings are not performance evidence.

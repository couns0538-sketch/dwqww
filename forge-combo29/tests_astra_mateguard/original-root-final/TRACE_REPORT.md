# Original-root observational trace

The narrow guard has a live, non-vacuous bypass on the original ancestry at **depth 4**. Exact same-ancestry mate-window **depth-5 coverage is absent with the option on** and is not claimed as passing. The unguarded depth-5 omissions reproduce. No behavior was widened to force the guarded search through the old depth-5 visits.

Both trace passes use a private copy of current search.cpp, gate=1, and the unchanged guard-enabled build's other objects. Logging reads only existing state, computed lmr_depth, FEN, and current-move ancestry; it adds no TT probes, move generation, or search-state writes. The extra second-pass predicate calculation uses only existing integer values. No production source, frozen binary, experiment state, ref, or push was changed. No Python was used in this tracing task.

For **both off and on**, in **both passes**, instrumented and uninstrumented full UCI stdout is identical after removing only numeric `time` and `nps` fields. All eight original-root runs completed with exit 0. Compile/link commands are bounded by 180/30 seconds; each search has a 45-second termination timer. Exact commands, options/traffic, exits, raw stdout/stderr, source/object/binary input hashes and transformation records are retained. Second-pass inputs still match their recorded hashes after the runs.

Settings: original root `8/8/8/8/8/1R6/2k5/5K2 w - - 0 1`, Threads 1, Hash 16, OwnBook false, UseNNUE false, depth 13, fresh process and ucinewgame each run. Only MateAlphaGuard varies. Final off: mate 17, 25,568 nodes, b3f3. Final on: mate 11, 36,063 nodes, b3f3. These are node counts, not speed/Elo claims or exact-DTM claims.

## Exact live guarded predicate

Second-pass raw evidence: `pass2/runs/observed-on/stderr.txt`, lines 39–45. The relevant event sequence is NODE_ENTER, d3d2 BEFORE_PRUNING, d1c1 BEFORE_PRUNING, QUIET_FUTILITY_TEST, D1C1_CALL_LMR, actual D1C1_CHILD_ENTER, D1C1_RESULT_LMR. Frame IDs are the private logger's entry local-node count.

| Field | Observed value |
|---|---|
| Parent frame | 24765 |
| Parent FEN | `8/8/8/8/8/3R4/8/k2K4 w - - 8 5` |
| Exact ancestry | `b3f3 c2b2 f1e2 b2c2 f3d3 c2b2 e2d1 b2a1` |
| Root iteration / ply | 13 / 8 |
| Entry / current depth | 4 / 4 |
| Entry / current alpha; beta | 31982 / 31982; 31983 |
| Candidate / ordinal | d1c1 / 2 |
| Prior best score / skip_quiets | 31979 / false |
| Location | inside original outer pruning block and quiet, non-checking branch |
| In check / option on / mate alpha | false / true / true |
| lmr_depth / FutilityDepth | 3 / 7 |
| Static eval / base / multiplier | 518 / 100 / 110 |
| Ungated quiet-futility predicate | **true**, since `518 + 100 + 110 * 3 = 948 <= 31982` |
| Actual child frame / ply / depth | 24772 / 9 / 3 |
| Actual child window | [-31983, -31982] |
| Child FEN | `8/8/8/8/8/3R4/8/k1K5 b - - 9 5` |
| Actual child ancestry | original eight moves followed by d1c1 |
| Returned parent score | 31987 |

Because this predicate event is emitted **inside** the outer block, its other gates are satisfied. The move is ordinal 2 with an existing best score; this is not a first-move exemption. The logged true ungated predicate and the immediate actual child entry prove the narrow guard bypassed a live futility prune. `pass2/live-witness.json` records and checks the exact event chain and input hashes.

## Depth-5 distinction

Off reproduces two d1c1 futility skips on the exact ancestry at depth 5: frame 24348 enters alpha 31982; frame 24357 enters alpha 441 and raises current alpha to 31979 before skipping d1c1. Both have beta 31983. This retains the dynamic-alpha regression evidence.

On visits the exact ancestry at depth 4, bypasses the live predicate above, and obtains 31987. The subsequent old mate-window depth-5 visits are absent. There is an earlier same-ancestry depth-5 entry with ordinary alpha 476 and no d1c1 move-loop event. Separately, the on search reaches the same FEN/ply/depth 5 through `b3f3 c2b2 f1e2 b2b1 e2d1 b1b2 f3d3 b2a1`; there d1c1 is the first TT move and returns 31987. That different-ancestry, first-move search is **not** counted as direct guard coverage.

The observed depth-4 success and disappearance of the old depth-5 re-searches should be assessed against Fable's acceptance wording. This report does not silently replace the strict depth-5 requirement. Original-root ten-repeat certification was not performed in this focused trace task.

Files: `pass2/comparison.json`, `pass2/live-witness.json`, parsed `pass2/events-{off,on}.json`, raw per-run evidence under `pass2/runs/`, and `pass2/transformations.json`. The first pass remains intact for comparison.

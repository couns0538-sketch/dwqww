# Required low-clock search equality failure: corpus index 3228

**The user's under-80 equality check failed and remains failed.** The root halfmove clock is 76. The merged engine searches 31,749 nodes and the unchanged lock searches 32,435 nodes at depth 9. Both return `b5c4`, score `cp -1689`, and the same PV. Identifying the requested t23 change responsible for the difference does not change the expected equality criterion or turn this comparison into a pass.

The failure is caused by the t23 rule-50 transposition-table gates introduced in commit `affb2cb97302870751ea727a96a533c5d5baa5aa`, present in requested merge input `91103a012c8f77f528606935dcff7184123617eb`. Descendants reach halfmove clock 90 even though the root clock is below 80. The scratch-only counterfactual that restores the three previous TT behaviors reproduces the lock's exact node count while retaining every other merged production change. No production source, option, compile switch, branch or expected result was changed for this investigation.

## Reproducer and observed results

```text
FEN: 5k2/8/7p/1K5P/8/8/8/7q w - - 76 136
Threads: 1
Hash: 16
OwnBook: false
UseNNUE: true
MultiPV: 1
ContHist4PlyRead: false
NonPawnCorrection: false
LmrDeeperShallower: false
Fresh process, ucinewgame, isready, position fen, go depth 9

Lock:   info depth 9 seldepth 23 score cp -1689 nodes 32435 ...
Merged: info depth 9 seldepth 23 score cp -1689 nodes 31749 ...
Both bestmove: b5c4
Both PV: b5c4 h1h5 c4d3 h5f3 d3d2 h6h5 d2e1 f3f6 e1e2 h5h4 e2e3
```

The original comparator's initial pair plus ten additional fresh pairs all reproduce the difference. Its complete pending-fault record is retained as [original-comparator-pending.txt](search_equality_evidence/original-comparator-pending.txt). This investigation also ran one fresh production pair; both processes exited 0 with empty stderr. Depths 1 through 8 have identical node counts; depth 8 is 14,457 nodes in both engines. The difference first appears in the depth-9 iteration. Raw output, including timing fields, is retained; no speed conclusion is drawn.

## Attribution and descendant conditions

Source line references below describe the frozen merged production `forge-combo29/src/search.cpp`, SHA256 `2b14b62cd675b047478e70b738932ce4c2c699239b3c0de4ec43551464dc8819`.

| Source location | t23 behavior |
| --- | --- |
| `src/search.cpp:1069` and `:1217` | `near50` is evaluated for each current board: `board.halfmove_clock() >= 90`. It is not a root-only condition. |
| `src/search.cpp:1070` and `:1218` | At `near50`, suppress the TT move if the entry's stored clock differs from the current board clock. |
| `src/search.cpp:1074` and `:1224` | At `near50`, suppress inherited TT PV status. An actual PV node still has PV status. |
| `src/search.cpp:1075` | Disable the early quiescence TT cutoff at `near50`. |
| `src/search.cpp:1483` through `:1493` | TT PV status affects late-move reduction: `if (ss->tt_pv) r -= 1`, then the child searches at `clamp(new_depth - r, 1, new_depth)`. |
| `src/search.cpp:1357` | TT move suppression can also affect internal iterative reduction when its other conditions hold. This is a source-level consequence; this investigation did not enumerate every such return. |

The corresponding requested t23 source lines are 1022–1028 and 1170–1177. The exact introducing patch and surrounding source are retained in [t23-delta-and-build-flags.txt](search_equality_evidence/t23-delta-and-build-flags.txt) and [group-ablation-and-lines.txt](search_equality_evidence/group-ablation-and-lines.txt).

The lock already has clock-aware `TTEntry::score_usable(...)` and the main-search TT cutoff condition `board.halfmove_clock() < 90`; these are not newly introduced by this merge. Comparing the permitted base `fca0fb40c7e66fdf01e36f4b95ceb179ffee2fca` with the lock shows no change to those conditions. t12's bare-king mode requires multiple workers and is false here with Threads 1. The three t22 options remain false. This attribution is supported by the exact t23 patch and the counterfactual results below; no standalone build of every input revision was needed or claimed.

The first logged `near50` descendant in the production-equivalent scratch run is:

```text
C3228 S depth=5 root_depth=9 node=24866 ply=14 clock=90 alpha=-1690 beta=-1689 tt_hit=1 tt_clock=84 tt_move=a7b7 tt_depth=0 tt_pv=1 tt_bound=2 tt_score=-1229 pv=0 fen=5k2/K7/7p/2q4P/8/8/8/8 w - - 90 143
```

Thus the root clock 76 has advanced to 90 after fourteen reversible plies. Requested search depth is not a maximum path length: this search reaches selective depth 23. At the first logged node the older TT move and PV flag are suppressed by t23, while the clock-mismatched TT score was already unusable under the lock's score rule.

The first differing logged child depth is reached after this common parent:

```text
C3228 S depth=4 root_depth=9 node=24869 ply=15 clock=91 alpha=1689 beta=1690 tt_hit=1 tt_clock=83 tt_move=a1a1 tt_depth=1 tt_pv=1 tt_bound=1 tt_score=1229 pv=0 fen=5k2/1K6/7p/7P/q7/8/8/8 b - - 91 143
```

For the child with queen on b4, at local node 24,871 / ply 16 / clock 92, the merged gates search depth 3; restoring only TT PV inheritance searches depth 4. The parent is not a PV node, its entry has a PV bit, and t23 clears the inherited bit at clock 91. The source's PV-dependent reduction and the PV-only counterfactual explain the observed one-ply child-depth change. The trace logs search entries, not every reduction arithmetic intermediate or every return instruction. The exact PV-only run is retained in [pvtrace-transcript.txt](search_equality_evidence/pvtrace-transcript.txt).

## Scratch-only controlled changes

The diagnostic executable substitutes only a scratch copy of `search.cpp` into the already built merged object set. Its runtime mask is a private diagnostic mechanism in that scratch copy, not a production option or proposed fix. The patch, complete scratch source as text, compiler/link commands, and hashes are retained. All native compile, link and search commands were restricted to CPU 4 with `taskset -c 4`; builds were sequential, and every command had a timeout below eight minutes.

| Scratch mask | Prior t23 behavior restored | Measured nodes at depth 9 |
| --- | --- | ---: |
| 0 | None; merged behavior plus diagnostic logging | 31,749 |
| 1 | Keep TT move despite near-50 clock mismatch | 31,859 |
| 2 | Keep inherited TT PV status at near-50 clocks | 32,156 |
| 4 | Permit previous quiescence TT cutoff | 31,610 |
| 8 | Restore previous early-pruning clock guard | 31,749 |
| 16 | Restore previous shallow-pruning clock guard | 31,749 |
| 32 | Restore previous LMR clock guard | 31,749 |
| 7 | Restore all three TT behaviors, retain new pruning guards | **32,435** |
| 56 | Restore all three pruning guards, retain new TT behaviors | **31,749** |
| 63 | Restore all six families | **32,435** |

All listed runs exit 0 and return the same move, score, PV and selective depth as above. The changes interact; their individual node differences are not additive. Mask 7 is sufficient to reproduce the lock's exact nodes, while mask 56 retains the merged nodes. This identifies the three TT behavior changes as the cause of this counterexample rather than the new `clock + depth < 100` pruning guards. The t23 TT conditions act in descendants, so a root-only `halfmove < 80` selection does not guarantee unchanged search traversal.

## Evidence and limits

- [Run commands and actual results](search_equality_evidence/run-diag-transcript.txt), [group counterfactuals](search_equality_evidence/group-ablation-and-lines.txt), and every submitted UCI command, stdout and stderr are retained separately.
- [Scratch patch](search_equality_evidence/search-diag.patch.txt), [complete scratch source](search_equality_evidence/search-diag.cpp.txt), [build transcript](search_equality_evidence/build-diag-transcript.txt), [source and binary hashes](search_equality_evidence/final-provenance.txt), and [trace comparison](search_equality_evidence/analyze-trace-transcript.txt) permit review of the attribution.
- Instrumented stderr contains intentional `C3228` trace lines. No sanitizer build was performed for this diagnostic; this is not a sanitizer-clean claim. Production stderr was empty.
- The original logging attempt placed `mkdir` and `tee` in the same pipeline, allowing `tee` to open before the directory existed. That read-only inspection returned 1 because of the logging race. Its tool-output transcript is retained in `initial-logging-failure.txt`; subsequent evidence used the existing directory. A scratch logging newline escape was corrected before the successful compile; both creation and correction commands are retained. Neither incident is an engine failure.
- This investigation proves the measured equality failure and its cause for this FEN/options/depth. It does not establish a wrong evaluation, illegal move, false mate bound, universal equivalence, strength change or speed change. No production repair was attempted. The required under-80 equality result remains a failure.

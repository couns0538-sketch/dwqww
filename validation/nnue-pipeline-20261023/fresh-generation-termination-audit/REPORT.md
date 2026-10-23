# Fresh-generation termination and outcome-label audit

**PASS:** both original worker traces were replayed incrementally, and all **256 original game IDs and 21,000 saved rows** were verified. The actual audit process exited 0 with empty stderr. No engine, generation, training or match process was started.

Worker 0’s 128 `ucinewgame` segments mapped to the original even-index manifest game IDs; worker 1’s 128 segments mapped to odd IDs. All eight opening moves per game were legal and matched the documented attempt-0 seed. Every later full `position startpos moves ...` command exactly equaled the accepted opening/bestmove history. The audit checked 33,334 legal engine bestmoves, or 35,382 legal moves including openings. It did not repeatedly replay full histories. Incrementally counted repetitions matched the library’s full-history repetition test on every final board.

For each search, the final raw UCI score and bound flag were tracked. The original quiet-position filtering was independently reconstructed. All saved FENs, ply numbers, bestmoves, cp scores, engine hashes and White result labels matched exactly, including exact per-game retained-row counts. No original PGN was invented.

| Exclusive termination reason | Games | Fraction of games | Saved rows | Fraction of rows |
|---|---:|---:|---:|---:|
| four_ply_score_adjudication | 167 | 65.2344% | 12850 | 61.1905% |
| max_ply_adjudicated_draw | 4 | 1.5625% | 790 | 3.7619% |
| natural_actual_fifty_move_threshold | 12 | 4.6875% | 1707 | 8.1286% |
| natural_actual_threefold_repetition | 55 | 21.4844% | 3955 | 18.8333% |
| natural_checkmate | 2 | 0.7812% | 156 | 0.7429% |
| natural_insufficient_material | 15 | 5.8594% | 1451 | 6.9095% |
| natural_stalemate | 1 | 0.3906% | 91 | 0.4333% |

The source checks checkmate first, then actual current-position draw thresholds, then the 300-ply limit, then score adjudication. All final-board flags are retained to expose coincident reasons. Exactly four games reached ply 300, and all four were max-ply-only draws with no coincident natural terminal. They account for 1.5625% of games and 3.7619% of saved rows. The original generator treats current threefold and 50-move claim thresholds as draws; this is not a future-move draw claim.

The score-adjudication rule compares `chess.engine.Score` against ±2,000 cp in White’s perspective for four consecutive plies, so mate scores also qualify. Among 167 score-adjudicated endings, 108 final UCI scores are `mate`, and 59 are `cp`. These are predicted outcomes, distinct from the two games actually ending in checkmate. All streaks, bound flags and final four score lines are retained per game.

Overall saved game results are 110 White wins, 59 Black wins and 87 draws. These labels match the documented source rules; they do not prove the eventual game-theoretic result.

| Original max-ply game ID | Saved rows | Final halfmove clock | Last White-perspective score | Decisive streak |
|---|---:|---:|---:|---:|
| ede90bb90c97428c972de42ec62bdf19:45 | 205 | 76 | -11 cp | 0 |
| ede90bb90c97428c972de42ec62bdf19:89 | 255 | 84 | -259 cp | 0 |
| ede90bb90c97428c972de42ec62bdf19:98 | 86 | 92 | -216 cp | 0 |
| ede90bb90c97428c972de42ec62bdf19:101 | 244 | 56 | +121 cp | 0 |

The four max-ply draws can truncate positions that are not established draws. The larger outcome-label limitation is the 65.2344% of games ended by same-engine, 5,000-node score adjudication. A result-weight ramp learns these adjudicated labels. This audit found no result/history/label corruption and made no relabeling or data-selection decision; it does not certify adjudication accuracy, generalization or Elo.

Evidence includes the exact executed `audit.py`, command/environment/exit receipts and original stdout/stderr, input SHA256 identities checked before and after replay, every reconstructed search with original trace-line references, and all per-game termination flags, final FENs, accepted UCI moves, final four scores and original saved-row line references. `DERIVED-SUMMARY.json` binds the additional count summary to the per-game file. The checkpoint archive also retains copies of the original raw worker traces, original game rows/manifest/process receipts and the three exact frozen generator source files. Engine/network artifacts remain referenced by exact hashes and their original preserved paths; no engine was executed by this audit.

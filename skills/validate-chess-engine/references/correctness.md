# Focused correctness investigations

Select the relevant rows; do not run every expensive test for every change. A new regression should fail on the observed defect and pass on the fix. Keep the independent expected result or oracle provenance alongside it.

| Area | Evidence to establish |
| --- | --- |
| Move generation | Exact perft/divide on the same FEN and depth; trusted legal-move oracle; matching move order for exact-speed tasks |
| State restoration | Snapshot and compare board/bitboards, piece lists, kings, rights, EP, clocks, side, hash, repetition, evaluation and NNUE state before/after make/unmake |
| Special moves | EP exposing a rook/bishop line; king safety; castling through attacks; capture promotions and underpromotions; pinned moves; check evasions |
| Hashing | Incremental key versus independent full recomputation after every tested transition, including null/EP/castling/promotions |
| Repetition | Supplied game history versus in-search history; irreversible boundaries; null moves; declared in-tree draw heuristic versus game adjudication |
| Rule 50 / TT | Controlled score-reuse tests at relevant halfmove clocks, incompatible histories, and terminal/mate cases; investigate score eligibility separately from move ordering |
| SEE | Exact versus threshold callers; equality boundary; legal king recaptures, pins, x-rays, EP and promotion recaptures |
| Quiescence | In-check evasions, terminal mate/stalemate behavior, safe stand-pat conditions and tactical pruning cases |
| PVS / aspiration / TT | Window and bound meaning, mate ply conversion, reduced/full re-searches, interrupted iterations, TT depth/age/collision paths |
| Evaluation / NNUE | Correct score perspective, color transforms, incremental versus full-refresh parity, clipping/rounding/ranges, network version/width/export compatibility |
| UCI / timing | Initialization, concurrent readiness/stop, supported go limits, position history, terminal bestmove, ponderhit, new game and reconfiguration behavior |

## Reproduction discipline

Preserve the shortest failure with the complete state needed to produce it. A FEN does not encode repetition history. Keep both an isolated example and the discovered failing sequence when the bug depends on TT/history reuse.

Reproduce baseline nondeterminism before blaming a candidate. Fix-depth single-thread search with controlled TT/history is useful for exact comparisons. A normal warm TT can change move ordering, pruning, and finite-depth search behavior; do not require all warm/cold scores to match. Construct a test for the specific score reuse rule or a position with an independently known result.

Use ablations diagnostically: disable one suspected mechanism, compare its effect, then restore unrelated selectivity. A changed score is evidence to investigate; it is not automatically proof that every selective cutoff is invalid. Conversely, passing perft does not excuse an incorrect draw, illegal move, or broken protocol.

Keep bug-fix acceptance and strength acceptance separate. An intentionally corrected score may change the benchmark signature. Record a new signature only after the correct baseline and expected behavior are established; do not modify the benchmark or expected result merely to make a failing candidate pass.

## Protocol checks

Read the engine's actual `uci` output and test only advertised/required features, reporting missing requirements explicitly. The [Stockfish UCI manual](https://official-stockfish.github.io/docs/stockfish-wiki/UCI-Protocol-and-Stockfish-Commands.html) is a useful primary reference for standard command behavior, but Stockfish-specific options do not automatically exist in GrokChess.

Measure `isready` and `stop` while a real search is running, not only after it finishes. Check `go infinite`, `movetime`, clock/increment allocation, `nodes`, `depth`, `searchmoves`, `mate`, `ponder` and `ponderhit` as required. Test `ucinewgame`, long move histories, malformed inputs under the engine's declared policy, paths with spaces, and missing network errors. Keep diagnostics off protocol stdout.

Verify the engine is safe to reuse after aborting a search or changing options. Ensure one completed go request produces its required bestmove, and keep ponder behavior aligned with the UCI state machine. A synchronous JavaScript event-loop blockage is not solved by merely adding a new message handler.


# Forge 6.4 search audit — 2026-10-19

## Scope and status

- Repository: `/workspace/scratch/41fe08b6f73a/forge64`.
- Verified revision: `24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b`, branch `forge/6.4-hourly-20261019`.
- Read-only audit of search, transposition-table and time-management source and the 6.x experiment record. No engine edits, compilations, benchmarks, or tests were performed by this reviewer.
- Source line numbers below refer to this exact baseline. Findings are source-supported hypotheses or diagnosed mechanisms, not measured speed/Elo gains. Reproduction and acceptance remain the implementer's responsibility.

## Recommended experiments

### 1. Compute move-picker check masks only when their consumer is reached

**Contract:** exact search behavior, measured speed improvement. **Risk:** low. **Start here for a bounded speed candidate.**

`src/search.cpp:266-275` computes pawn, knight, bishop and rook check masks in every `MovePicker` constructor. `direct_check()` (`392-395`) only consumes those masks in `generate_quiets()` (`449`) and quiet evasions in `generate_evasions()` (`466`). Ordinary non-check quiescence and ProbCut pickers never reach either consumer. Main-search TT/capture/killer/counter cutoffs can also avoid quiet generation entirely.

Move the existing computations into a helper called at the beginning of `generate_quiets()` and `generate_evasions()`. Both consumers observe the same board position as the constructor: searched children are unmade before the next move is requested. Keep the formulas, move scores, tie handling, pseudo-legality checks and stage transitions unchanged. Do not alter `board.gives_check()`, which serves other pruning/extension purposes.

Validation: exact per-position depth/nodes/score/bestmove/PV at one thread, including ordinary qsearch, check evasions, quiet checks, promotions, castling and en passant. First confirm the documented `bench 11` baseline signature of 417491 in the actual build. Compare multiple paired timings, single job with stable resource allocation, and preserve all samples. A speed difference within noise remains inconclusive. Nodes or moves changing rejects this exact-behavior patch pending diagnosis.

The 6.x record already adopted lazy sorting (`EXPERIMENTS.md:130`); this is a different experiment and does not repeat that work.

### 2. Separate the TT index bits from the TT signature bits

**Contract:** targeted TT identity correction, then strength/performance follow-up. **Risk:** medium. **Best concrete TT opportunity.**

`include/forge/search.hpp:106-111` uses multiply-high indexing when `__SIZEOF_INT128__` is available. `src/search.cpp:197,218` uses the upper 32 key bits as the stored signature. For normal power-of-two sizes, multiply-high indexing itself uses the highest key bits. The index and signature therefore duplicate information.

At 32 MiB, the 64-byte clusters give 2^19 clusters. The cluster index is the top 19 key bits, all already inside `key >> 32`; only 13 signature bits distinguish positions within a cluster. At 64 MiB, only 12 bits remain. This is substantially weaker than 32 independent signature bits. Scores are consumed directly before hash-move legality can help (`search.cpp:692-695,813-817`).

A bounded repair can use the low 32 bits for the multiply-high path. The fallback index is `key % cluster_count`; for power-of-two counts that consumes low bits, so it should retain an independent high-bit signature. Centralize signature selection so `probe()` and `store()` cannot disagree, and assess non-power-of-two sizes as well.

Minimal deterministic test: in a fresh power-of-two-size table, store key `0x123456789abcdef0`, then probe `0x123456789abcdef1`. On the multiply-high baseline, they share cluster and upper-32 signature; the latter is returned as a hit. A corrected independent signature distinguishes them. Also test normal hit, empty tag value, genuine same-cluster replacement, same-position depth preservation, aging and non-power-of-two allocation.

This changes which accidental collisions the engine observes, so an unchanged bench signature is not the correct acceptance requirement. Verify intended TT behavior, existing chess tests, tactical searches and time limits, then conduct a predeclared equal-time fastchess SPRT before claiming playing-strength improvement. Measure NPS separately.

### 3. Associate root effort with a stable move identity

**Contract:** time-management accounting correction; equal-time strength testing. **Risk:** low to medium.

`src/search.cpp:1048` adds each root move's nodes to `root_move_nodes_[move_count - 1]`. The array is cleared once for the entire iterative-deepening search (`1239`), while TT moves and histories can reorder the root list between iterations and aspiration passes. `root_best_index_` records the best move's current ordinal (`1059`), and the soft-time factor reads the accumulated nodes from that ordinal (`1303-1306`). Thus one slot can contain work on different moves, which is then attributed to the current best move.

Use a stable mapping from full `Move` identity to root slot, constructed from the legal root candidates once, for both accounting and best-move lookup. Preserve the current allocation constants initially. This is distinct from the already inconclusive `TmSoftDivisor=18` experiment (`EXPERIMENTS.md:148`).

Validation: an accounting regression with two root moves whose order swaps between simulated/observed iterations must keep their node totals separate. Test aspiration re-searches and `searchmoves` restrictions. One-thread fixed-depth search results should stay identical because accounting only affects time management. Then verify hard/soft limits and run equal-time SPRT; fixed-node matches cannot validate this change's benefit.

### 4. Reproduce near-rule-50 TT score leakage in quiescence

**Contract:** minimal failing correctness reproducer, targeted policy repair, related strength testing. **Risk:** medium; avoid broad changes without reproduction.

`Board::compute_key()` (`src/board.cpp:896-905`) excludes halfmove clock. Main-search direct TT cutoff is guarded by `halfmove_clock() < 90` (`search.cpp:813-817`), but qsearch cutoff (`692-695`) is unguarded. Qsearch score-to-eval substitution (`708-711`) and main score-to-eval substitution (`830-833`) are also unguarded. Disabling only a direct cutoff is not a complete context policy if the same incompatible score can trigger stand-pat or another pruning decision.

Controlled reproducer design, not run by this reviewer: `1R5k/8/8/8/8/8/8/K7 b - - 99 1`. Black is checked by the rook; all legal evasions are quiet king moves. Every child reaches halfmove 100 with legal moves available, so a clean qsearch returns draw. Seed an exact nonzero TT entry for the identical clock-zero position, or use an explicitly controlled test entry, then query the clock-99 position through a null-window qsearch. The baseline can return the incompatible seeded score before searching the forced draw.

If reproduced, design explicit score-context compatibility covering both cutoffs and score-based static-eval substitution. Keep legal hash moves usable for ordering and raw position-only evaluation reusable where valid. Do not make every search path unique or remove unrelated pruning. Add mate-on-the-hundredth-halfmove and irreversible-reset cases, plus ordinary lower-clock reuse. Report correctness separately from Elo.

## Separate SMP design issue

`TTEntry` fields are ordinary non-atomic objects (`include/forge/search.hpp:60-68`), while helpers share the table (`search.cpp:1363-1366`) and access it concurrently through `probe()`/`store()` (`195-227`). These accesses have no synchronization. The comment at `search.hpp:80-81` asserting that key checks and move legality catch torn entries does not establish a C++ memory-model guarantee or a coherent score snapshot. Treat this as an independent multi-threading task: define a coherent atomic publication/snapshot design, validate it with an appropriate sanitizer/stress test, and measure one-thread overhead plus multi-thread performance/strength. Do not mix a broad locking change into the first speed patch.

## Existing work and evidence to preserve

The 6.4 record rejects or leaves unadopted changes to `FutilityBase/Multiplier`, `SeeQuietMultiplier`, `QsSeeMargin`, `HistoryPruneMultiplier` and `NullMoveEvalDivisor` (`EXPERIMENTS.md:156-161`). Earlier records cover qsearch quiet checks, shallower ProbCut/null move, stronger LMR history weighting, capture futility, fail-low continuation bonuses and the time divisor (`142-153`). Do not repeat unchanged variants without a documented reason.

Forge 6.0 rewrote the source and tests (`CHANGELOG.md:203-232`). The current TT tests (`tests/tests.cpp:465-482`) cover basic store/probe, same-position depth protection and clear. Old tools such as `tools/audit/see_and_tt_probe.cpp` call removed 5.x search interfaces; archived 5.x passes are not evidence that 6.4 has those protections. Reintroduce specific meaningful regressions when their defects are reproduced, preserving the effective selective search.

## Additional exact-speed idea for later profiling

`material_key()` (`search.cpp:504-511`) recomputes ten popcounts and a polynomial hash in `corrected_eval()` and again in some `update_correction()` calls (`545,558`). Maintaining the identical material key incrementally or caching it while material is unchanged may help, but it touches board restoration or cache ownership and should follow the simpler move-picker experiment. Likewise, picker arrays zero-initialize substantial per-call storage, but removing braces alone is insufficient because `Move` has default member initializers; pursue only with code-generation evidence and carefully scoped ownership.

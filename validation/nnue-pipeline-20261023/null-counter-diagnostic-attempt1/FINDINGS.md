# Original null-pruning assertion: bounded old/new-core diagnosis

The original full Linux Release qualification remains failed: all fourteen tests ran, thirteen passed, and `forge_tests` reported only `null pruning is active with non-pawn material`. Its source assertion requires both null attempts and cutoffs to be positive after a pawn-only depth8 search, `clear()`, and a start-position depth8 search. No production source, original test, tuning value or network was changed to investigate this.

The same evidence-only wrapper included the unchanged original `tests/tests.cpp` with its main renamed, reused its existing friend `SearcherTestProbe`, and linked separately against the hash-pinned accepted core and selected-network core. Identical strict GCC14/C++20 flags were used. The protocol declared only the original pawn→start depth8 sequence and one fresh start-position depth10 case, before execution. Session55633 actually exited0; compiler commands, binaries, original streams and return codes are retained.

| Case | Accepted core attempts/cutoffs | Selected-network core attempts/cutoffs |
| --- | --- | --- |
| Original pawn-only, depth8 | 0 / 0 | 0 / 0 |
| Original start after cleared pawn search, depth8 | 22 / 22 | 0 / 0 |
| Predeclared fresh start, depth10 | 83 / 62 | 45 / 25 |

Every reported best move was legal and every board remained unchanged. The new core demonstrably reaches null-move pruning and makes null cutoffs at depth10. Its zero depth8 counter is therefore not evidence that null pruning was globally disabled. Counts and fixed-depth node differences are diagnostic observations, not speed or Elo evidence.

The unchanged search source evaluates null pruning only inside the non-PV, not-in-check, non-excluded, non-mate-beta path, after earlier razoring/reverse-futility returns. It additionally requires minimum depth, `eval >= beta`, the static-evaluation beta margin, `null_move_allowed`, a preceding non-null move, non-pawn material and no disqualifying upper TT score. Changing evaluation changes both reached search nodes and these conditions. This bounded probe did not trace which exact predicate prevented each depth8 attempt; it does not establish that deeper search is a universally robust fixture for every future network.

Root owns a separate robust test design and any source/test integration. The original failed qualification and its source commit remain intact. A separately authorized fresh ASan/UBSan profile runs all fourteen unchanged tests for safety observations; it neither retries Release nor bypasses this assertion. No bench, match, NPS or Elo conclusion is included here.

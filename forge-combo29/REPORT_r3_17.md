# r3-17: legal position prefix and helper node budget

Base is `origin/integrate/combo29-all` at `e04556ddc3a430b2e751159b0d46111ef56c8b89`. No new UCI option. `CMakeLists.txt` is unchanged.

## The two commits

1. `cursor/position-legal-prefix-712a` at `0d692396ffa145568f40d79e33973831bbf8a937`.
   The tip only rewrites `REPORT_position_prefix.md`. The behavior is the parent, `1f14c76593e6f308f0a03100d6f1c1eab81e7eb8` (`Keep a legal position prefix when a move token is rejected`).
2. `cursor/helper-node-limit-eea5` at `375e183c33576a1a1a0f3d1b46b01ace19417c1b`.
   The tip only rewrites `REPORT_t11.md`. The behavior is the two parents:
   - `d16ab008916156ab318a3ba1a22293ce2c83ce9e` stops helper threads when the node budget is spent.
   - `c34ebf0c9ece260fa6d6920d82fab5a5f196f8bd` clears worker node counts before a new search starts.

The helper branch also contains earlier merges of the t1, t3, t6, and t8 fixes. Those are already in this base. They were not copied again. The two source reports were not copied. This file is the only report added here.

## Position command

`apply_position` in `forge-combo29/src/uci.cpp` used to return without touching the board when the token after `startpos` or a FEN was not `moves`, and when `parse_uci` rejected a later token. Both returns now keep the candidate.

A word other than `moves` is skipped until `moves` appears or the command ends. If the command ends, the parsed position stands. An illegal or unrecognized move token still prints `info string illegal move <token>`, and the position plus every legal move before that token stands. A later token is not played. An invalid FEN still leaves the previous position alone.

`parse_uci` only accepts a token that is a legal move, so a bad word and an illegal move take the same path.

## How the `Worker::should_stop` conflict was kept

The helper patch edited the single `Worker::should_stop` that existed on its parent. This base split that function for MultiPV.

What the base already did:

- `should_stop` publishes `local_nodes_`, then, when `parent_worker_` is set, calls `parent_worker_->should_stop_with(local_nodes_)`. Otherwise it calls `should_stop_with(0)`.
- `should_stop_with` returned immediately for a non-main worker, before the node budget. The budget test was `total_nodes() + extra_nodes_ + pending_nodes >= node_limit_`, and it set `stopped_by_nodes_` on that path. Only the main worker reached it.
- The alternate MultiPV worker copies `node_limit_specified_` from its parent. Its own limits clear the node budget. Other workers set the flag only when `is_main()` was true, so helpers never checked the budget.
- Above MultiPV 1, helper threads are not started. The counted set is the main worker. Finished alternate lines are added through `extra_nodes_`. The line still in progress is `pending_nodes`.

What the helper branch did, on the old function:

- Test the node budget before `if (!is_main()) return false`, using `total_nodes()`.
- Set `stopped_by_nodes_` only on the main worker.
- Set `node_limit_specified_` for every worker, so a small `go nodes` is checked every node.
- Zero every worker's published count on the launching thread before any worker enters `search`.

Both behaviors are in `should_stop_with` and in the flag assignment. `should_stop` itself is the base version, including the parent hand-off.

1. The budget test now runs before `if (!is_main()) return false`, and it still adds `extra_nodes_` and `pending_nodes`. A helper stops when the shared count reaches the budget, instead of waiting until the main worker has unwound and raised the shared stop flag. The clock test stays after the helper return. Helpers still ignore the clock and still stop on time only through `shared_.stop`.
2. `stopped_by_nodes_` is set only when `is_main()` is true. The search result that is returned is the main worker's, so a node-limit stop still keeps the last finished iteration and does not take a best move from the iteration the limit cut off. A helper abort does not set the flag. The alternate MultiPV worker has id 0 in its own search, but it does not run this check on itself. It asks the parent. The parent is the main worker, so the flag still lands on the result that is returned.
3. `node_limit_specified_` still copies the parent's flag when `parent_worker_` is set. For every other worker, including helpers, it is `limits.nodes_specified || limits.nodes != 0`, without the old `is_main()` guard. Helpers therefore call `should_stop` on every node when a budget was given. With no budget the flag stays false, and the depth-only search path is unchanged.
4. `Searcher::search` calls `reset_node_count()` on every worker before it starts any of them. A helper can otherwise read the budget before another worker clears the count it published last time. MultiPV above 1 still does not start those workers. Zeroing them does not change the main-worker total, because they are not in the counted set.

## Default engine

Threads 1, Hash 16, OwnBook false, and every other option left at default. The same three commands were run before any source edit and again after the rebuild.

`/usr/bin/c++` is Clang 18.1.3. Configure with that compiler stops in the compiler test: `ld: cannot find -lstdc++`. The build used `CXX=g++` (g++ 13.3.0) and the required flags:

`cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build build -j`

| | before | after |
| --- | ---: | ---: |
| bench 11 | 312866 | 312866 |
| bench 13 | 862329 | 862329 |
| `go perft 5` from the start position | 4865609 | 4865609 |

The per-move perft 5 split matched the pre-change run. `tests_t22` printed `defaults_after bench13 862329` after it had turned the three default-off search options on and back off.

## Tests

Release objects from that build. Test binaries were linked with the same `FORGE_*` defines and `-march=x86-64-v3`. Each row is exit 0 unless the note says otherwise.

Branch tests, copied byte-for-byte into `forge-combo29/tests_r3_17/` and run from there:

- `commands.txt` and `expected.txt` from `0d692396`. Fed to `./build/forge`. Marker lines were `nodes 0`, illegal `NOTAMOVE`, `nodes 20`, illegal `NOTAMOVE`, `nodes 600`, `nodes 400`, `nodes 600`, `invalid FEN: invalid FEN fields`, `nodes 600`, `nodes 400`. That is the expected file.
- `tests_r3_17/position_prefix.cpp` runs that script through `uci_loop` and checks the same lines, then checks `e2e5` after `e2e4 e7e5` and `foo` after `e2e4`. PASS.
- `tests_r3_17/thread_node_limit.cpp` from `375e183c` (`tests_t11/thread_node_limit.cpp`). PASS. One thread stopped on 1, 50, 200, and 1000 exactly, on the start position and on the rook ending. Eight threads, budget 1: worst 1. Four threads, budget 10000: worst 10003. Eight threads, budget 10 on the rook ending: worst 10. A searcher reused after a 20000-node warm search stayed within 500..532 on ten searches at budget 500.
- `tests_r3_17/multipv_node_budget.cpp`. MultiPV 3 at 4000 nodes was 4000 nodes and `d2d4` for both 1 and 4 threads. MultiPV 1 with 4 threads at 4000 nodes was 4003. A reused MultiPV 3 searcher stopped at 8000, then at 1500. PASS.

Base folders:

| folder | result |
| --- | --- |
| tests_t1 | PASS, `bestmove d3b1`, nodes 176 |
| tests_t3 | `clock_parse_test passed` |
| tests_t6 | `PASS fixed-node score and move agree` |
| tests_t8 | converted lock net, `PASS` |
| tests_t12 | `misses=0 / 400` on 40 positions, 10 runs, 2 threads, depth 14 |
| tests_t13 | `PASS failures 0` and `PASS startup` |
| tests_t14 | 30 positions, 10 mirrors |
| tests_t15 | `RESULT passed`, including depth 12 against the lock and threads 4 falling back to threads 1 |
| tests_t16 | see below |
| tests_t17 | `RESULT PASS fails=0` |
| tests_t18 | 200000 lines, `part_b ... ok`, `SANITIZERS clean`, exit 0 |
| tests_t19 | widened net matches `nnue_weights_512.inc` (`cmp` exit 0); eval parity `static_equal 100000`, exit 0 |
| tests_t20 | `t20 result: PASS` |
| tests_t21 | `multipv1_bench PASS` |
| tests_t22 | `PASS t22 search_candidates_test`, bench 13 still 862329 |
| tests_t23 | mate solver `missed_mates=0 false_mates=0 illegal=0`; fifty-move `cases=20 failures=0` |

`tests_t16` own-book spec: `ok 54 lines`. Search spec: `ok 7 lines`. The raw `diff` of `options.expected.txt` and `clamp.expected.txt` fails. The only extra lines are the five option advertisements the fixtures never listed: `MultiPV`, `NnueFile`, `ContHist4PlyRead`, `NonPawnCorrection`, and `LmrDeeperShallower`. Each appears twice in a transcript. Filtering those five lines makes both diffs empty. That gap is already described in `forge-combo29/INTEGRATION_ALL.md`. This merge does not add an option, and the fixtures were not edited.

## Recheck

The same branch was built and run again. No source file changed.

Release `./build/forge`, configured with `CXX=g++` and `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`, printed bench 11 = 312866, bench 13 = 862329, and start-position perft 5 = 4865609. The per-move split matched the first run.

An ASan/UBSan engine was configured with the same flags plus `-fsanitize=address,undefined -fno-sanitize-recover=address,undefined -fno-omit-frame-pointer`. CMake still appends `-O3`, so the engine objects are sanitized at `-O3`. The harnesses were compiled at `-O1` with the same sanitizers and linked to those objects. `ASAN_OPTIONS=halt_on_error=1:abort_on_error=1:detect_leaks=1` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1:abort_on_error=1`. That binary printed the same three totals and the same per-move split. Its stderr had no sanitizer diagnostic.

Both builds then ran every base test folder and both branch suites. Every program exited 0 except the known raw `tests_t16` options diff.

| check | Release | ASan/UBSan |
| --- | --- | --- |
| tests_t1 | exit 0, `d3b1`, 176 nodes | same |
| tests_t3 | passed | passed |
| tests_t6 | fixed-node score and move agree | same |
| tests_t8 | PASS | PASS |
| tests_t12 | misses 0 / 400 | misses 0 / 400 |
| tests_t13 | race PASS, startup PASS | race PASS, startup PASS |
| tests_t14 | 30 positions | 30 positions |
| tests_t15 | RESULT passed | RESULT passed |
| tests_t16 | filtered options and clamp match; own-book 54 lines; search 7 lines | same, and no sanitizer diagnostic |
| tests_t17 | fails=0 | fails=0 |
| tests_t18 | 200000 lines, exit 0 | 200000 lines, `SANITIZERS clean`, 173841 ms |
| tests_t19 | `static_equal 100000`, widen `cmp` 0 | same, hashes match |
| tests_t20 | PASS | PASS |
| tests_t21 | `multipv1_bench PASS` | `multipv1_bench PASS` |
| tests_t22 | PASS, bench 11/13/perft 312866 / 862329 / 4865609, bench 13 after 862329 | same node counts |
| tests_t23 | mate missed 0, false 0, illegal 0; fifty-move 20 cases, 0 failures | same |
| position prefix and `commands.txt` | PASS, marker lines match `expected.txt` | same |
| thread node limit | PASS | PASS. One thread exact. Eight threads, budget 1: worst 1. Four threads, budget 10000: worst 10002. Rook budget 10: worst 10. Warm 20001. |
| MultiPV node budget | PASS | PASS. MultiPV 3 at 4000 nodes was 4000 and `d2d4` on 1 and 4 threads. MultiPV 1 with 4 threads was 4000. Reused searcher stopped at 8000, then 1500. |

The raw `tests_t16` options diff still exits 1 on both builds. The only extra lines are `MultiPV`, `NnueFile`, `ContHist4PlyRead`, `NonPawnCorrection`, and `LmrDeeperShallower`. Filtering those lines makes the options and clamp diffs empty. `tests_t22` under ASan also reproduced the three default-off candidates: bench 13 moved to 989877, 775585, and 813907, then returned to 862329.

After that, the helper-budget test, the MultiPV budget test, and both `tests_t13` programs were repeated 8 times on each build. All 64 runs exited 0. No AddressSanitizer, LeakSanitizer, or undefined-behavior report was written.

The same four programs, on both builds, kept running after that. At 14:24 UTC the extra loop had finished 80 rounds (640 runs) with 0 failures and no sanitizer report. The loop is scheduled through 14:48 UTC; the count above is the checkpoint, not the final tally.

## Not verified

- `forge-combo29/soak_all`. It is not one of the `tests_*` folders.
- A Clang-linked binary. `/usr/bin/c++` is Clang 18.1.3 and still fails configure with `cannot find -lstdc++`.
- A non-portable `-march`, and the Windows lock build.
- `./build/forge` was not started under a GUI.

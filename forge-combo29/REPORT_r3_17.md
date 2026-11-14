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

A second pass is running on this same branch. It does not replace the numbers above until it finishes.

Release `./build/forge`, rebuilt with `CXX=g++` and the same portable flags, printed bench 11 = 312866, bench 13 = 862329, and start-position perft 5 = 4865609 again. The per-move split matched.

The same three commands on an ASan/UBSan binary (`-fsanitize=address,undefined -fno-sanitize-recover=address,undefined`, `halt_on_error=1`) printed the same three totals and the same per-move split. No sanitizer diagnostic on that run.

The Release suite was run again: tests_t1, t3, t6, t8, t12, t13, t14, t15, t17, t18, t19, t20, t21, t22, t23, plus `tests_r3_17` position prefix, thread node limit, MultiPV budget, and `commands.txt`. Every one exited 0.

ASan/UBSan has passed tests_t1, t3, t6, t8, t13, t14, t15, t17, t18 (200000 lines), t19, t20, t21, and the fifty-move half of tests_t23. `tests_t12` under ASan was still running when this note was written. tests_t16, tests_t22, the mate half of tests_t23, and the branch suites under ASan had not been reached yet.

## Not verified yet

- The rest of the ASan/UBSan suite listed above.
- `forge-combo29/soak_all`. It is not one of the `tests_*` folders.
- A Clang-linked binary, a non-portable `-march`, and the Windows lock build.
- `./build/forge` was not started under a GUI.

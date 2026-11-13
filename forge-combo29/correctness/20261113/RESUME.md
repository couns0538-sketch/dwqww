# Forge correctness resume (2026-11-13)

Starting revision: `fable/standalone-h512-20261111` at `efb2ff960037087299332bc6a44baea69441a17a`.
Work branch: `cursor/forge-correctness-20261113-e6b6` (not the Fable branch, not a lock branch).

Other agents, read and not modified:

- History index `cursor/forge-history-index-20261113-712a` at `b39453901cd47c654f94bb7ec0283fc7c7f0ceb0`. Its correctness note points at two unread investigator tips. Both were read here. The qsearch stalemate probe was never run on a native binary. The nodes-0 report was source-only.
- NNUE eval `cursor/forge-nnue-eval-20261113-22cc` at `aba085b7137b40b10af9561398f1c2b59831671d`. That work is the v3 cache and the trainer scorer. This branch does not touch those files. The default binary has `FORGE_NNUE_V2`, `FORGE_NNUE_V3`, and `FORGE_NNUE_HALFKA` off, so those loaders are not in the tested executable.

## Build

- CPU: 4-thread Intel Xeon, family 6 model 207. `avx512f` and `bmi2` are present. `nproc` = 4.
- Compiler: g++ 13.3.0. `/usr/bin/c++` is Clang 18.1.3 and cannot link (`-lstdc++` missing), so CMake is invoked with `-DCMAKE_CXX_COMPILER=g++`.
- Flags from `flags.make`: `-O3 -DNDEBUG -std=c++20 -ffp-contract=off -fno-fast-math -march=x86-64-v4`
- Defines: `FORGE_NNUE_HIDDEN=256 FORGE_EXPOSE_TUNABLES=1 FORGE_SPD_TT_NOTLS=1 FORGE_SPD_NO_ZERO_MOVELISTS=2 FORGE_SEARCH_SPEED2=1 FORGE_SPD_PREFETCH_EARLY=1 FORGE_SPD_SLIDER_PEXT=1 FORGE_SPD_NNUE_ZMM=1`
- `FORGE_PORTABLE` is off. The regression targets also pass `-D_GLIBCXX_ASSERTIONS`.
- Build directory: `/tmp/forge-correctness-build` (not in the repo).

## Fixed and tested

### Deferred-capture buffer overrun

`MovePicker::bad_captures_` was `std::array<Move, 64>`. The same defect was recorded on `fable-review-buffix` (`ab2aa56b`) and called unfixed in the lock (`5f29788c`).

Before the fix, FEN `3r4/Pn1Q1p2/1Q1n1QpN/1p1Q1pRB/1Qbp1QpN/2bQ1pRB/3r1QpK/2k2q2 w - - 0 1` aborted with `std::array<forge::Move, 64>::operator[]` (69 noisy moves, 68 SEE-losing). After sizing the buffer to `MoveList::Capacity` (256): `bestmove=d3b1 depth=3 nodes=396`.

### Position command

`position startpos moves NOTAMOVE` from a checkmate used to leave the engine in mate (`bestmove 0000`). The legal prefix is now kept, and the engine reports `info string illegal move NOTAMOVE`. A following `go depth 1` played `e2e3`.

`position startpos extra` did the same discard. Tokens before `moves` are skipped and the position stands. `position startpos extra moves e2e4` from a checkmate then played `e7e6` (Black to move).

### Perft stop

`go perft` used to ignore `stop`. A later `stop` now prints `info string perft stopped` and omits the `nodes` line. A script that queues `quit` with the request still receives `nodes 4865609`. Windows builds do not start the watcher. An already-queued byte does not abort the count, which is what the pin script requires.

### Zero-node budget at a terminal root

`validation/hourly/2026-10-20-1300-investigator/REPORT.md` (`7d4974f3ba613b8e50290ff6db05a3d9a98831f3`) predicted that `go nodes 0` on a stalemate prints `info depth 1` while `go nodes 0 searchmoves e2e4` prints no depth line. Reproduced on this binary: stalemate printed `info depth 1 ... score cp 0 nodes 0` and `bestmove 0000`. The zero-node return now happens before that report. The UCI test sees `bestmove 0000` and no `info depth` line. `go depth 1` on the same stalemate still prints a depth line. A live `go nodes 0 searchmoves e2e4` still returns `e2e4` with no depth line. Checkmate at nodes 0 keeps score `-MateValue` and depth 0.

## Tested, not a bug on this tree

The 6.4 qsearch-stalemate probe (`ab9c56000235bfbf3c1aaa1814111d264d3f0823`) was never run on a native binary. `is_draw` already treats a quiet stalemate as a draw before stand-pat. `go depth 1 searchmoves g5g6` on `7k/5K2/8/6Q1/8/8/8/8 w - - 0 1` printed `score cp 0` and `bestmove g5g6`.

## Pins

`scripts/check_pins.sh` on the perft-stop binary and again after the nodes-0 change:

- net on: 312866, 862329, 3024920, 12389307, 34048354
- net off: 375354, 907205, 2448617, 13573040, 24506465
- startpos perft 5: 4865609

Both runs printed `PINS MATCH combo29`. Logs: `pins_after_perft.txt`, `pins_after_nodes0.txt`. No Elo claim. The benches do not reach 65 deferred captures, and they do not use `go nodes 0`.

Commands that passed after the last edit:

- `/tmp/forge-correctness-build/forge_rules_tests` (failures=0)
- `/tmp/forge-correctness-build/forge_bad_capture_tests` (failures=0, nodes=396)
- `python3 forge-combo29/tests/uci_protocol_tests.py /tmp/forge-correctness-build/forge` (failures=0)
- `forge-combo29/scripts/check_pins.sh /tmp/forge-correctness-build/forge` (match)

## Not changed

`opus-r5d-matefix` is a different search. No KRK miss has been measured on `forge-combo29/src/search.cpp`. The bare-king pruning change is not ported.

The stop flag in `Searcher::search` is saved around helper shutdown and restored. A stop in that window is overwritten. The CPU-lane note treated this as harmless because the main worker has already returned and UCI keeps its own flag. No failing test yet.

Opposite-colored bishops are not an automatic draw. Not changed.

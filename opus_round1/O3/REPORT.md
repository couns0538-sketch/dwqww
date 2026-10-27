# O3 [Engine QA] search.cpp no-op refactor for maintainability — DONE

Branch `opus-O3` = base commit `294dbed` (verbatim AL1 s198 lock tree) + `[BASELINE]` evidence/CI commit + `[O3]` commits.
Patch vs lock: `patch.diff` (engine tree only; excludes `opus_round1/` and `.github/`).
O3 was done first because it makes O1 easier (and the prompt allows it): the per-thread state is now one
documented struct (`ThreadData`) next to the shared state (`SharedSearchState`), and TT, time management and the
per-node stop checks are separate modules that O1 audits one by one.

## What changed (no behaviour change)

`src/search.cpp` (1531 lines) is now a 40-line composition of 14 modules under `src/search/`; the 408-line
`include/forge/search.hpp` is split into 6 headers.

| module | content (moved verbatim unless noted) | lock search.cpp lines |
|---|---|---|
| `include/forge/search_types.hpp` | SearchLimits, SearchInfo, score constants, Bound | search.hpp 19-65 |
| `include/forge/tt.hpp` / `src/search/tt.inc` | TT interface / TT implementation | search.hpp 67-183 / 181-314 |
| `include/forge/search_tune.hpp` / `src/search/tune.inc` | tunables + LMR/LMP tables | search.hpp 185-249 / 13-103, 125-151, 179 |
| `include/forge/history.hpp` | history table types, `HistoryTables` (the 4 move-ordering tables + clear), `history_bonus`, `apply_history` (now `inline`) | search.hpp 251-260 / 107, 153-160 |
| `include/forge/thread_data.hpp` | `SearchStack`, `SharedSearchState`, **new `ThreadData`** (all per-worker members, lock order, with a thread-ownership contract) | search.hpp 262-293, 315-346 |
| `include/forge/search.hpp` | `Worker` (now `: private ThreadData`, no own data), `Searcher` | search.hpp 295-406 |
| `src/search/scores.inc` | mate scores, TT score encoding | 109-123 |
| `src/search/uci_info.inc` | score formatting of the UCI info line | 168-175 |
| `src/search/movepicker.hpp` | staged MovePicker (+ `capture_value`, now `inline`) | 316-556, 162-166 |
| `src/search/worker.inc` | worker construction / clear | 561-584 |
| `src/search/evaluation.inc` | lazy NNUE + residual eval glue, pawn/material correction history | 586-656 |
| `src/search/timeman.hpp` | **time management module**: `allocate()` budgets, soft-stop pieces (`stability_factor`, `effort_scale`, `eval_fell`/`falling_eval_scale`, `factor_floor`), inline | 1249-1275, 1433-1457 |
| `src/search/checks.inc` | per-node checks: `elapsed_ms`, `total_nodes`, `should_stop`, `is_draw` | 658-702 |
| `src/search/history.inc` | history scoring and update rules (Worker members over `histories_`) | 704-766 |
| `src/search/qsearch.inc` | quiescence search | 768-870 |
| `src/search/alphabeta.inc` | main alpha-beta search | 872-1225 |
| `src/search/iterative.inc` | root setup, iterative deepening, aspiration, UCI info emission | 1227-1467 |
| `src/search/searcher.inc` | Searcher facade: helper threads, TT lifecycle | 1469-1529 |

The only non-verbatim edits are mechanical: `main_history_` etc. -> `histories_.main_history`, the
time-allocation / soft-stop statements expressed through the inline `timeman::` functions (same statements in the
same order once inlined), the Worker constructor delegating to `ThreadData`. The complete list of non-verbatim
lines is `logs/moved_code_check.log` (script `moved_code_check.sh`).

**Why one translation unit.** The modules are `#include`d by `src/search.cpp` exactly once each, so
(1) the build recipe is unchanged: CMake, `2_build/build_windows.ps1` and the PC gate scripts still compile the
same 8 .cpp files (adding .cpp files would break every candidate build script on the PC), and (2) code generation
of the hot paths is unchanged (see NPS below). CMakeLists.txt only gains 3 test targets.

## Acceptance

| # | acceptance line | result |
|---|---|---|
| 1 | bench all 5 depths exact | **PASS** |
| 2 | `go depth 18` bestmove + node count identical on 50 positions (list + diff) | **PASS** (50/50, also score + depth) |
| 3 | no measurable slowdown: bench NPS within 1% (10 runs each) | **PASS** (hot code machine-code identical; d20 +0.24% wall / −0.18% CPU) |
| 4 | unit tests for move-picker stages and history update math, wired into CTest | **PASS** (3 new tests, 8/8 planted bugs caught) |
| 5 | Windows build still compiles | **PASS** (built on Windows with the unmodified `build_windows.ps1` and the PC recipe) |
| §3 | default behaviour, perft, kiwipete, FMA 0, known test failures only, determinism | **PASS** |
| §3 | sanitizers | **PASS**: ASan+UBSan and TSan on Linux (CI run 40362958451): 0 reports, only the 4 known lines; UBSan trap mode locally: no trap |
| §3 | Linux box recipe (g++-14.2, CMake, x86-64-v3) | **PASS**: bench x5 exact, perft, kiwipete, FMA 0 (CI) |

### 1. Bench (PC recipe build, `logs/identity_pc_recipe.log`)
```
$ build_pc.sh <tree> forge_o3.exe   (g++ 15.2 ucrt64, exact build_windows.ps1 flags)
$ python 2_build/uci_check.py forge_o3.exe --full
bench d11 nodes 312866 ref 312866 OK
bench d13 nodes 862329 ref 862329 OK
bench d16 nodes 3024920 ref 3024920 OK
bench d20 nodes 12389307 ref 12389307 OK
bench d22 nodes 34048354 ref 34048354 OK
perft5 startpos 4865609 ref 4865609 OK
perft5 kiwipete 193690690 ref 193690690 OK
ALL OK
FMA (vfn?m(add|sub)) count: 0
```
The exe built by the unmodified `build_windows.ps1` gives the same (`logs/build_windows_ps1.log`).

### 2. depth 18 on 50 positions (`positions50.fen`, `depth_compare.py`, `logs/depth18_*`)
50 positions = 8 bench FENs + 14 WAC300 (incl. WAC.008) + 14 ECM + 14 forge-10000 openings
(`make_positions50.py`, deterministic picks). Fresh `ucinewgame` per position, Threads 1, Hash 16, OwnBook false.
```
$ python depth_compare.py <lock.exe> positions50.fen 18 depth18_lock.tsv
$ python depth_compare.py <o3.exe>   positions50.fen 18 depth18_o3.tsv
$ diff depth18_lock.tsv depth18_o3.tsv      -> empty (exit 0); 33,380,402 nodes in total
```

### 3. NPS (`nps_ab.py`, `logs/nps_*`, `logs/codegen_identity.log`)
Measured on the busy PC (fastchess gate + datagen + training, ~80% CPU; this job ran at BelowNormal priority),
10 runs per build per depth, ABBA-interleaved fresh processes; `wall` = engine-reported nps, `cpu` = nodes / process
CPU seconds.

| build pair | depth | wall B/A (95% CI of diff) | cpu B/A (95% CI of diff) |
|---|---|---|---|
| A/A control: lock vs a copy of the lock | 16 | −1.77% (−4.38 .. +0.83) | — |
| A/A control | 20 | −1.04% (−3.49 .. +1.41) | — |
| first O3 version (rejected) vs lock | 16 | −3.47% (−6.19 .. −0.76) | — |
| first O3 version (rejected) vs lock | 20 | −4.92% (−7.55 .. −2.30) | — |
| **final O3 vs lock** | 16 | +2.26% (−2.91 .. +7.42) | −0.66% (−4.60 .. +3.28) |
| **final O3 vs lock** | 20 | **+0.24% (−0.81 .. +1.29)** | **−0.18% (−1.30 .. +0.95)** |

The first version of the split was measurably slower (d20 −4.9%). Root cause (machine-code diff): GCC placed new
out-of-line helpers (`write_iteration_info`, `history_bonus`, `apply_history`, `ThreadData`/`HistoryTables`
constructors) at the start of search.cpp's `.text` and the MovePicker held `&histories_` instead of the Worker,
which changed register allocation of alpha-beta and moved every hot function to a different 64-byte alignment.
The final version keeps the Worker layout identical (ThreadData holds all members in the lock's order), keeps small
helpers header-`inline`, the history rules as Worker members, the MovePicker holding the Worker, the time module
inline with the original statement order, an out-of-line `~ThreadData`, and the modules in the original function
order. Result (`logs/codegen_identity.log`): **every hot function is instruction-identical to the lock and starts at
the same address mod 64** — alpha-beta (2413 insns), qsearch, MovePicker::next, TT probe/store, static_evaluate,
should_stop, is_draw, correction history, all history updates, record_move, NNUE update/evaluate/refresh,
make/unmake, SEE. The only changed function is the once-per-iteration driver `Worker::search(Board, ...)`
(same 2119-instruction length, register-allocation differences). The 1% criterion therefore holds by construction;
the measured d20 numbers agree. QA should still repeat `nps_ab.py` on an idle machine.

### 4. Unit tests (`tests/movepicker_tests.cpp`, `tests/history_tests.cpp`, `tests/timeman_tests.cpp`)
- `forge_movepicker_tests`: picker output vs an independent reference built from the generator, SEE and the
  history tables (TT -> good captures by score with SEE>=0 -> killer1 -> killer2 -> counter -> quiets by score ->
  bad captures; quiescence; evasions; skip_quiets at start and mid-stage; non pseudo-legal / quiet TT move
  handling; `last_move_see_nonnegative`). 12 positions (incl. promotions, en passant, castling, 2 in-check) x 60
  seeded random configurations of history tables, killers, counter moves and TT moves:
  `positions=12 main_runs=1200 qs_runs=600 evasion_runs=240 checks=66774 failures=0`.
- `forge_history_tests`: `history_bonus` vs reference (default and tuned shape), gravity formula on a grid and its
  bound/saturation, killer shift, counter-move slot, butterfly reward/penalty, continuation plies 1/2/4 (half bonus at
  ply 4, ply 3 untouched, plies without a move skipped), capture reward/penalty, quiet-history sum: 130 checks.
- `forge_timeman_tests`: `allocate()` vs the lock formulas on 885 limit combinations and the soft-stop factor
  composition on 15120 inputs (bit-exact doubles).
- Mutation check (`mutation_check.sh`, `logs/mutation_check.log`): 8 planted bugs (killer order, SEE threshold
  off-by-one, check bonus, gravity divisor, continuation half-bonus ply, counter-move slot, soft divisor, effort clamp)
  are all caught.

### 5. Windows build
This machine is Windows 11: `2_build/build_windows.ps1` (unmodified, run on a copy of the archive layout with the
O3 tree) builds `forge_h256_s198.exe`; the identity check passes (`logs/build_windows_ps1.log`).

### Section 3 checks
- ctest (CMake Release, g++ 15.2): 16/17, only `forge_tests` fails with exactly the 4 known lines
  (`logs/ctest_release.log`, `logs/ctest_release_known_failures.log`). The 3 new tests are the extra entries.
- UBSan (GCC `-fsanitize=undefined -fsanitize-trap=undefined`, 4959 trap sites in forge.exe): same ctest result,
  no trap (`logs/ctest_ubsan_trap*.log`). MinGW has no ASan/TSan runtime and the VS 2026 STL rejects the installed
  clang 18, so ASan+UBSan with diagnostics and TSan run on Linux in `.github/workflows/opus-ci.yml`
  (`opus_round1/ci/run_ci.sh`). GitHub Actions run 40362958451 on commit a0bbc53 (`logs/ci/`):
  - release (box recipe, ubuntu-24.04 g++-14.2.0): bench 312866/862329/3024920/12389307/34048354, perft 4865609,
    kiwipete 193690690, FMA 0; ctest 16/17 with only the 4 known lines;
  - asan (`-DFORGE_ENABLE_SANITIZERS=ON`, `-fno-sanitize-recover=all`): ctest 16/17 with only the 4 known lines,
    0 ASan/UBSan reports (forge_tests 1.45 s vs 0.15 s release: instrumented);
  - tsan (`-fsanitize=thread`): ctest 16/17 with only the 4 known lines, 0 TSan reports (forge_tests 9.0 s).
- Compiler warnings: the same 6 pre-existing `-Wconversion` warnings as the lock, now at their new file locations
  (`logs/compiler_warnings.log`); no new warning.
- Determinism: Threads=1 output identical across builds and runs (bench, depth-18 list).

## Addendum: MovePicker::next pinned to 64 bytes (commit after the CI evidence)
`MovePicker::next` is hot and, being defined in the class body, is emitted out of line as a COMDAT
section. The PE linker places all COMDAT sections after every object's `.text`, so its address moves
whenever *any* translation unit changes size — e.g. a later job adding UCI options to `uci.cpp`
(observed while building C3: 0 -> 32 mod 64). It now carries `gnu::aligned(64)`: always at a 64-byte
boundary, which is exactly its AL1 s198 placement (0 mod 64). Its instructions are unchanged
(`codegen_compare.sh` lists 32 "differing" lines: only the NOP padding after the function, up to the
next 64-byte boundary); bench x5 / perft / kiwipete unchanged, FMA 0.

## Files
`REPORT.md`, `IDEA_SOURCE.md`, `patch.diff`, `positions50.fen`, `make_positions50.py`, `depth_compare.py`,
`nps_ab.py`, `codegen_compare.sh`, `moved_code_check.sh`, `mutation_check.sh`, `logs/`, `SHA256SUMS`.
Shared: `opus_round1/00_baseline/` (lock reproduction), `opus_round1/ci/` (Linux CI scripts).

## Notes
- No gate needed (no behaviour change). No Elo or speed claim beyond "no slowdown measured".
- Rule for later jobs on top of O3: keep hot helpers inline and the Worker data layout stable, or re-run
  `codegen_compare.sh` + `nps_ab.py`; this is how the first version's −4.9% was caught.

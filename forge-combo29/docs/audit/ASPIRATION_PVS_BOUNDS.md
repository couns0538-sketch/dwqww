# What was wrong, what was found, and what changed

Branch `cursor/search-bound-audit-9cd5`, commit `f46e8d24`, based on `fable/standalone-h512-20261111` at `efb2ff96`. `main`, the lock branch, and the base branch were not modified. This branch is not merged.

The code under audit is `Worker::search` and `Worker::qsearch` in `forge-combo29/src/search.cpp`. Scores: `Infinite = 32001`, `MateValue = 32000`, `MateInMaxPly = 31872`, `ValueNone = 32002`. A mate of distance D plies is stored as `32000 - D`. A loss of distance D is stored as `-32000 + D`. Bounds: upper = 1, lower = 2, exact = 3.

Every number below is from GCC 13 (`CXX=g++`), CMake Release, `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`, and the lock compile defines. `/usr/bin/c++` on this machine is Clang 18 and cannot link (`cannot find -lstdc++`), so Clang was not used. Hand-crafted eval means `forge::nnue::enabled = false`. No Elo was measured. A node rate from this container is not a speed result.

`forge::search_fixes()` is one process-wide struct. Tests turn one field off to run the old behaviour in the same binary. UCI has no option for it.

| Switch | Default on this branch | What it changes |
| --- | --- | --- |
| `mate_horizon` | on | Rejects a TT mate the 50-move rule cannot deliver |
| `aspiration` | on | Opens a stuck aspiration window, and stops an aborted re-search from publishing the wrong root move or the wrong score |
| `qsearch_shallow_bound` | **off** | Drops a depth-0 quiescence bound that is below stand-pat. Off because turning it on changes the lock node counts |

The late-move-reduction guard is unconditional. There is no defined old path to keep: the old call was undefined behaviour.

---

## 1. The aspiration window could get stuck and spin

### What was wrong

From depth 4 on, the next iteration searches a window around the previous score: `[score - delta, score + delta]`. `AspirationDelta` starts at 18. If the search fails low (`score <= alpha`), the old update was:

```text
beta  = (alpha + beta) / 2
alpha = max(score - delta, -32001)
delta = delta + delta / 2 + 4
```

C++ integer division truncates toward zero. On the floor window `alpha = -32001`, `beta = -32000`, `score = -32001`:

```text
(-32001 + -32000) / 2 = -64001 / 2 = -32000
```

`beta` stays `-32000`. `alpha` stays `-32001` because `score - delta` is below `-32001` and the `max` clamps it. The window does not move. The old loop searched that same window again, then did the same update, forever.

Fail-high only raises `beta`. It does not raise `alpha`. That part was left as it is. A re-search that finishes can still come back with a lower score than the fail-high. The overflow on `score + delta` was also tightened to 64-bit arithmetic; the scores that actually occur fit in 32 bits, so that was not a reproduced bug.

### What was found

A grid of windows (alpha from -200 to 200, widths 2 through 80, deltas 4, 18, 50, and 200, fail-low and fail-high scores) matched the old formula on every window the old formula actually moved. The one window it does not move is the floor above. The fixed step opens that window to `[-32001, 32001]`. A second failure on the full window stops.

No bench position was seen returning the sentinel `-32001`. The spin is in the arithmetic. The loop can no longer repeat it.

On the start position at depth 5, hand-crafted eval, the old window update and the new one searched the same tree: 1275 nodes, `d2d3`. The window change does not touch a search whose score sits inside a normal window.

### What changed

`widen_aspiration` in `src/search.cpp` does the old update, then if alpha and beta did not change, or if alpha ended up at least beta, it opens `[-32001, 32001]`. If the window is already the full range and the score is still outside it, the iterative-deepening loop stops. A sentinel outside `[-32000, 32000]` is replaced with the last proven score, or with 0 when there is none.

---

## 2. An aborted re-search published a worse move with the old score

### What was wrong

If the search is stopped in the middle of an iteration, the old handler did this: if the partial PV's first move differed from the completed best move, replace the best move with the partial move, and leave the published score as the previous iteration's score.

The comment next to that code said the partial move was at least as good. That is false once aspiration is on. At depth 4 the floor is `previous score - delta`, which is below the completed score. A move only has to beat that floor to be written into the root PV. It can be much worse than the move that already finished.

The search really does write that move into the PV before anyone can tell. The move is made, searched, unmade, and copied into `ss->pv`. Then the abort returns 0. The handler sees a new first move and trusts it.

### What was found

Start position, hand-crafted eval, `AspirationDelta = 1000` so the floor is far below the real score. Depth 3 finishes as `d2d4` at +16. Forcing only `a2a3` at depth 3 scores -56. Depth 4 is told to try `a2a3` first and to abort once that move raises alpha.

| Run | Move | Score | Depth recorded |
| --- | --- | --- | --- |
| Depth 3, completed | `d2d4` | +16 | 3 |
| Depth 3, only `a2a3` | `a2a3` | -56 | 3 |
| Depth 4 aborted, old handler | `a2a3` | +16 | 3 |
| Depth 4 aborted, new handler | `d2d4` | +16 | 3 |

The old handler reports `a2a3` and the score +16. Those two numbers do not belong together. +16 is `d2d4`. `a2a3` is -56. The new handler keeps `d2d4` and +16.

The hook that forces this abort is off unless a test sets it. Bench and UCI do not set it. The path they share with the test is the abort handler itself.

### What changed

With `aspiration` on, a different partial PV is kept only when the aspiration floor is already at least the completed score. In that case any move that raised alpha did beat a floor at least as high as the finished result. Otherwise the completed move and score stay. The `a2a3` case takes the second path.

---

## 3. A fail-high move was kept, and the previous iteration's score was glued onto it

### What was wrong

A fail-high means "this move scores at least beta." The engine then widens beta and searches again. Alpha stays where it was. If that re-search is aborted, the first attempt has already finished: it has a move and a lower bound.

The old abort handler still did the partial-PV rule from bug 2. The fail-high move differs from the previous best move, so the handler takes the new move. It does not take the new score. The number printed next to the fail-high move is the previous iteration's score, which was computed for a different move.

### What was found

Position after 1.e4 e5 (`rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2`), hand-crafted eval, `AspirationDelta = 4`.

Depth 4 finishes as `g1f3` at +18. Depth 5's first attempt fail-highs. The test aborts before the second attempt.

| Handler | Move | Score | Depth recorded |
| --- | --- | --- | --- |
| Old | `f1c4` | +18 | 4 |
| New | `f1c4` | +22 | 5 |

Both handlers saw `f1c4`. The old one prints +18, which is the score of `g1f3` at depth 4. The new one prints +22, the fail-high value, and records depth 5.

+22 is a lower bound. The info line has no bound field, so it is printed as an exact `cp` score. A re-search that runs to completion still replaces it, and that finished score can be lower than +22, because alpha was not raised. That completed-re-search case was left unchanged.

### What changed

While `aspiration` is on, a fail-high that returns a PV and a score above the last finished score is saved before the window is widened. If a later attempt at that depth aborts, and nothing better was proved, that saved move and score are what gets published.

---

## 4. A transposition-table mate was replayed after the 50-move rule had made it impossible

### What was wrong

The table stores mate distance from the node that searched it, then the probe shifts by the current ply. Nothing asked whether that many plies still fit in the 50-move clock.

The 50-move rule draws at 100 half-moves, except checkmate on the move that reaches 100, which still wins (`is_draw` returns false when the side to move is in check and has no legal move). From a node whose clock is C, the room is `100 - min(C, 100)` plies. A stored mate with distance D is deliverable only when `D <= room`, and only if the line does not need a capture to reset the clock. The stored score does not say whether the line captures.

The main search already refuses a TT cutoff when `halfmove_clock() >= 90`. Clock 80 still gets through. That is the interesting case: 20 plies of room, and a stored mate that needs 29.

Distance 0 must be kept. It means "already mated at the node that stored the score," not "a long mate."

### What was found

The probe is a non-PV search at ply 1, depth 3, beta 1, so an exact TT hit is allowed to cut off. The public root is a PV node and would not cut off on it. The entry is exact, depth 8, stored with rule-50 clock 0. The position is the start position with the halfmove clock set to 80.

| Stored score | Clock | Fix | Value returned |
| --- | --- | --- | --- |
| Win in 29 plies, stored as 31971 | 80 | off | 31970 |
| Same win | 80 | on | -5, not a mate |
| Win in 5 plies, stored as 31995 | 80 | on | 31994 |
| Loss in 29 plies | 80 | on | -5 |
| Loss in 0 plies, stored as -32000 | 80 | on | -31999 |
| Win in 29 plies | 0 | on | 31970 |

31970 is `31971` minus the one ply of the probe. The engine was willing to treat a 29-ply mate as a cutoff with only 20 plies left on the clock. With the check on, that search returns -5, the ordinary score of the position once the mate is ignored. The 5-ply mate still fits (5 <= 20) and still returns 31994. An immediate loss is not thrown away. The same 29-ply mate is kept when the clock is 0, because the room is 100.

A real mate in one still works with the check on: `r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4` at depth 2 is `h5f7` at 31999. Qxf7 is a capture, so the clock resets; the test only checks that a short mate is still found.

`is_draw` was not changed. Mate on the 100th half-move still wins. The check can also drop a mate that is still legal because a later capture would reset the clock. The stored number does not record those captures.

Depths 11 and 13 were measured with this switch alone. The node counts matched the lock. The shipping binary (this switch on, the quiescence switch off) matches every lock pin through depth 22.

### What changed

`score_from_tt` takes the halfmove clock. For a mate or a mated score it computes D and returns `ValueNone` when `D < 0` or `D > 100 - min(clock, 100)`. Both quiescence and the main search pass `board.halfmove_clock()`. A rejected mate does not cut off, and it is not copied into the evaluation.

---

## 5. Quiescence returned an upper bound that stand-pat had already beaten

### What was wrong

In quiescence, when the side to move is not in check, the score starts at stand-pat (the static eval, after correction). Stand-pat is a lower bound: the side can stop capturing and take that evaluation. A depth-0 table entry is itself a previous quiescence result. An upper bound or an exact bound below the current stand-pat cannot be true. The evaluation has moved, usually because correction history changed, and the old bound is describing a different number.

The old quiescence returned that bound as a cutoff. Even if the cutoff had been skipped, the next block copies a TT score into the eval when the bound is upper and the score is below the eval. Leaving the bad score in `tt_score` would put it back.

A deeper upper bound below stand-pat was left in place. A main-search bound can legally sit below stand-pat, because the main search has to move. A depth-0 quiescence bound cannot.

### What was found

KQ vs K, `4k3/8/8/8/8/8/8/4KQ2 w - - 0 1`. A depth-0 upper bound of -400 is stored, then a non-PV quiescence probe runs.

| Switch | Score |
| --- | --- |
| off | -400 |
| on | 832 |

832 is the stand-pat of that position. -400 is the stale bound.

This is not only a poisoned-entry trick. With the switch forced on, the start position at depth 5, hand-crafted eval, changes from `d2d3` (1275 nodes) to `d2d4` (867 nodes). The bench positions change too. Each switch was measured on its own at depths 11 and 13; only this one moves the counts.

| Depth | Eval | Switch off (the lock pin) | Switch on |
| --- | --- | --- | --- |
| 11 | hand-crafted | 375354 | 376782 |
| 11 | NNUE | 312866 | 300010 |
| 13 | hand-crafted | 907205 | 830513 |
| 13 | NNUE | 862329 | 793816 |

Depths 16, 20, and 22 were not re-run with the switch on.

### What changed

The correction is in `qsearch`. When the switch is on, the side is not in check, the entry depth is <= 0, and the bound is upper or exact, stand-pat is computed first. If the table score is below stand-pat, it is not returned, and `tt_score` is set to `ValueNone` so the later eval block cannot copy it.

The switch defaults off. The default binary still has this bug. It is off so `scripts/check_pins.sh` still matches combo29. There is no UCI option. Turning it on needs a new pin record and a strength test. This branch does not turn it on.

---

## 6. Late-move reduction called `std::clamp` with the bounds backwards

### What was wrong

`std::clamp(value, lo, hi)` is undefined when `lo > hi`. The reduced depth was:

```text
std::clamp(new_depth - r, 1, new_depth)
```

`new_depth` is `depth - 1 + extension`. A singular search that fails high gives extension -2. At depth 2, `new_depth = -1`. The clamp is then `std::clamp(..., 1, -1)`. That is undefined.

At the default `SingularDepth` of 7 the singular search does not start before depth 7, so `new_depth` for a -2 extension is at least 4. The undefined call does not happen in the lock configuration. It can happen when `SingularDepth` is lowered. The UCI minimum is 2.

### What was found

The reduced search is now entered only when `new_depth >= 1` (and the old `depth >= 2` condition). A negative `new_depth` falls through to the unreduced `search`. `search` at depth <= 0 is quiescence, which is defined.

`SingularDepth = 2`, start position, depth 4, returns `d2d4`. That shows the search finishes with the guard in place. It does not show that an extension of -2 was actually taken. The precondition (`new_depth >= 1`) is what the unit test checks directly.

The guard does not change the lock pins. Depths 11 through 22 match with it compiled in.

### What changed

The condition on the late-move-reduction block in `Worker::search` starts with `new_depth >= 1`. The full-depth null-window re-search is also skipped when the reduced search already aborted.

---

## What was read and left unchanged

The PVS ladder is the usual one. On a PV node the first move is searched with `(-beta, -alpha)`. Later moves go through a null window `(-alpha - 1, -alpha)`. A move that raises alpha is searched again on the full window. Late-move reduction, when it applies, is a null window at the reduced depth and, if that beats alpha and the search was not aborted, a null window at the full depth before the PV re-search. No wrong score was reproduced from that ladder.

These were also read. No wrong score was reproduced, so they were not changed:

- Null-move verification, from depth 14, searches the same stack frame with `null_move_allowed` cleared, then restores the inherited double-extension count. That verification search writes history and cutoff state on the frame.
- ProbCut searches at `depth - 4` and stores the cutoff as depth `depth - 3`. That is the usual formula, and it does claim one ply more than the search that produced the bound.
- The TT store writes a non-empty move even when the depth check keeps the previous score. A shallower store can replace the move of a deeper entry and leave that entry's score.
- Mate-distance pruning uses `alpha = max(alpha, mated_in(ply))` and `beta = min(beta, mate_in(ply + 1))`.
- `score_to_tt` / `score_from_tt` agree on the ply shift. The stored value is the distance from the node that stored it. The probe shifts by the current ply. The bug in section 4 is the missing clock check, not the ply shift.

---

## Files that changed

- `forge-combo29/src/search.cpp`. The six behaviours above. The old abort handler and the old window update are still in the binary, behind `search_fixes().aspiration == false`, so the tests can show the old result.
- `forge-combo29/include/forge/search.hpp`. `SearchFixes`, `widen_aspiration`, and three test hooks on `SearchLimits`: `audit_abort_after_worse_pv`, `audit_abort_on_attempt`, `audit_first_move`. All three stay off in UCI and bench.
- `forge-combo29/tests/search_bounds_test.cpp`. One process. Each test runs the old switch and the new switch. `./search_bounds_test isolate 11` prints bench nodes for all eight combinations of the three switches.
- `forge-combo29/CMakeLists.txt`. `src/*.cpp` except `uci.cpp` goes into `forge_lib`. The `forge` binary and `search_bounds_test` both link it, with the same flags and defines. That is how the test and the bench binary are the same search.
- This file.

`forge-combo29/build/` is a local build directory and is not part of the commit.

---

## Evidence

`./build/search_bounds_test`:

```text
PASS window arithmetic (stuck floor and normal steps)
PASS reduction clamp precondition
PASS mate horizon (stale 31970, rejected -5, kept 31994, loss -5, already -31999, early 31970)
PASS qsearch shallow bound (stale -400, stand 832)
PASS partial PV (depth3 d2d4 cp 16, a2a3 cp -56, buggy a2a3, fixed d2d4)
PASS fail-high preserve (Nf3 cp 18 kept as Bc4 cp 18 by the old handler; fixed publishes cp 22)
PASS aspiration node match (1275 nodes, d2d3)
PASS shallow singular search (d2d4)
PASS mate in one (h5f7 score 31999)
ALL PASS
```

`scripts/check_pins.sh build/forge`, with the shipping defaults (mate horizon on, aspiration on, quiescence correction off):

```text
net-on : 312866 862329 3024920 12389307 34048354
net-off: 375354 907205 2448617 13573040 24506465
perft5 : 4865609
PINS MATCH combo29
```

Those are depths 11, 13, 16, 20, and 22, net on then net off, then start-position perft 5. They are the combo29 lock counts.

How to rebuild:

```bash
cd forge-combo29
CXX=g++ cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4 --target search_bounds_test forge
./build/search_bounds_test
bash scripts/check_pins.sh build/forge
```

---

## What this branch does not claim

- The quiescence correction is compiled and tested, and the default binary does not use it. Enabling it changes move choice.
- A finished aspiration re-search can still publish a score below the fail-high. Alpha is not raised on fail-high.
- The mate check can drop a mate whose later captures would reset the 50-move clock.
- The stuck window was shown as arithmetic. No bench search returned the `-32001` sentinel.
- The reduction test does not prove a search took the -2 extension.
- The partial-PV and fail-high numbers are hand-crafted eval, driven by hooks that stay off in play. They go through the real abort handler. They are not timed UCI games.
- `search_fixes()` is process-wide. It is not safe to flip from another thread during a search.
- Do not merge this into the lock on the pin match alone. Defaulting the quiescence correction on needs its own pins and a strength test.

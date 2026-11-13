# Search audit: aspiration, PVS, bounds, re-searches

Branch `cursor/search-bound-audit-9cd5`, based on `fable/standalone-h512-20261111` at `efb2ff96`. The lock branch, `main`, and every other branch were left untouched. This branch is not merged.

The search under audit is `Worker::search` / `Worker::qsearch` in `src/search.cpp`. Scores use `Infinite = 32001`, `MateValue = 32000`, `MateInMaxPly = 31872`, `ValueNone = 32002`. Bounds are `BoundNone = 0`, `BoundUpper = 1`, `BoundLower = 2`, `BoundExact = 3`.

Build used for every number below: GCC 13 (`CXX=g++`), CMake Release, `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`, and the lock defines (`NDEBUG`, `FORGE_NNUE_HIDDEN=256`, `FORGE_EXPOSE_TUNABLES=1`, `FORGE_SPD_TT_NOTLS=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SEARCH_SPEED2=1`, `FORGE_SPD_PREFETCH_EARLY=1`, `SLIDER_PEXT=1`, `NNUE_ZMM=1`). `/usr/bin/c++` on this machine is Clang 18 and does not link (`cannot find -lstdc++`). The engine was not rebuilt with Clang.

Container node-per-second figures are not a speed result. No Elo was measured.

## What shipped

`forge::search_fixes()` is one process-wide struct. Tests flip individual fields so the old and new behaviour run in the same binary. UCI has no option for it. The fields stay put for the whole of a search.

| Switch | Default | Effect on the combo29 pins |
| --- | --- | --- |
| `mate_horizon` | on | none at depths 11 and 13 measured alone, and none in the shipping combination through depth 22 |
| `aspiration` | on | same as above |
| `qsearch_shallow_bound` | **off** | changes the bench. See the table below |

The LMR guard is unconditional. `std::clamp(new_depth - r, 1, new_depth)` is undefined when `new_depth < 1`, so there is no defined lock path to keep behind `#else`. At the default `SingularDepth` of 7 the negative extension cannot produce `new_depth < 1` (`new_depth = depth - 3` and singular search starts at depth 7). The guard does not change the pin counts.

The project note in `README.md` asks for a default-0 `#else` switch. This branch uses a runtime switch instead, so one binary can reproduce the old bug and the fix. `mate_horizon` and `aspiration` default on because the lock pins still match. `qsearch_shallow_bound` defaults off because they do not.

`SearchLimits` gained three test hooks (`audit_abort_after_worse_pv`, `audit_abort_on_attempt`, `audit_first_move`). All three are off unless a test sets them. Bench and UCI leave them unset.

## Bugs reproduced and fixed

Hand-crafted eval (`forge::nnue::enabled = false`) unless a row says otherwise. `search_bounds_test` prints one `PASS` line per case and `ALL PASS` at the end.

### 1. Aspiration window that cannot move

Fail-low used `beta = (alpha + beta) / 2` and `alpha = max(score - delta, -Infinite)`. C++ division truncates toward zero. The window `alpha = -32001`, `beta = -32000`, `score = -32001`, `delta = 18` is unchanged by that update: `(-32001 + -32000) / 2` is `-32000`. The old loop would search the same window again.

`widen_aspiration` keeps the old arithmetic whenever that arithmetic changes the window and does not invert it. A grid over alpha in [-200, 200], widths 2..80, deltas 4/18/50/200, and several fail-low and fail-high scores matched the old update on every window the old update could actually move. The stuck floor opens to `[-32001, 32001]`. A second failure on that full window sets `give_up` and the iterative-deepening loop stops. A sentinel outside `[-32000, 32000]` is replaced with the last proven score, or with 0 when there is none.

A finished bench search that returns the `-Infinite` sentinel was not observed. The spin is a property of the arithmetic, and the loop can no longer repeat it.

On a normal start position, depth 5, hand-crafted eval, aspiration off and aspiration on searched the same tree: **1275 nodes, `d2d3`**. That is the shipping default (`qsearch_shallow_bound` off). With the qsearch correction forced on, the same comparison was **867 nodes, `d2d4`**, still identical between aspiration off and on. The move change belongs to the qsearch switch, not to the window arithmetic.

### 2. Aborted re-search publishing a worse root move

The old abort path adopted any partial root PV whose first move differed from the completed move, and it kept the previous iteration's score. The aspiration floor at depth >= 4 is `previous - delta`, so a move that only beat the floor can be worse than the completed move.

Start position, hand-crafted eval, `AspirationDelta = 1000`:

| Search | Move | Score | Depth |
| --- | --- | --- | --- |
| Depth 3, completed | `d2d4` | +16 | 3 |
| Depth 3, only `a2a3` | `a2a3` | -56 | 3 |
| Depth 4 aborted after `a2a3` raised alpha, fix off | `a2a3` | +16 | 3 |
| Same abort, fix on | `d2d4` | +16 | 3 |

The abort is the test hook, after the move has been made, searched, unmade, and written into the root PV. The old handler pairs `a2a3` with the +16 that belongs to `d2d4`. The new handler keeps the completed move. A partial PV is still adopted when its first move differs and the aspiration floor is already at least the completed score. That case was not given its own test.

### 3. Fail-high score dropped when the re-search is aborted

Fail-high still does not raise alpha. The re-search uses the old floor and a higher beta. If that re-search is aborted, the attempt already finished is a lower bound and a PV.

Position after 1.e4 e5, hand-crafted eval, `AspirationDelta = 4`. Depth 4 completes as `g1f3` at +18. Depth 5 fail-highs on the first attempt; the test aborts before the second attempt.

| Handler | Move | Score | Depth |
| --- | --- | --- | --- |
| Old | `f1c4` | +18 | 4 |
| New | `f1c4` | +22 | 5 |

The old handler takes the fail-high move and prints the depth-4 score of `g1f3`. The new handler publishes the fail-high value +22 and records depth 5.

+22 is a lower bound. `emit` prints `cp` or `mate` and has no bound field, so the info line shows that lower bound as an exact score. A re-search that finishes inside the wider window still replaces it, and that finished score can be lower than the fail-high. Search instability on a completed re-search was left as it is.

### 4. TT mate the 50-move rule cannot deliver

`score_to_tt` stores a win of distance D as `MateValue - D` and a loss as `-MateValue + D`. `score_from_tt` then adds or subtracts the current ply. With `mate_horizon` on, a mate is ignored when `D < 0` or `D > 100 - min(clock, 100)`. Distance 0 (already mated, or mate already on the board from the stored node's point of view) is kept.

The probe is a non-PV search at ply 1 (`beta = 1`, depth 3), so an exact TT hit can cut off. The public root search is a PV node and would not. The entry is exact, depth 8, stored with rule-50 clock 0. The position is the start position with the halfmove clock set to 80, which is still under the existing main-search cutoff requirement `halfmove_clock() < 90`. Room at clock 80 is 20 plies.

| Stored score | Clock | Fix | Returned |
| --- | --- | --- | --- |
| win in 29 plies (`31971`) | 80 | off | `31970` |
| win in 29 plies | 80 | on | `-5` (not a mate) |
| win in 5 plies (`31995`) | 80 | on | `31994` |
| loss in 29 plies | 80 | on | `-5` |
| loss in 0 plies (`-32000`) | 80 | on | `-31999` |
| win in 29 plies | 0 | on | `31970` |

`is_draw` is unchanged. At clock >= 100 it returns a draw unless the side to move is in check with no legal move, so mate on the hundredth half-move still wins. Distance equal to the remaining room is kept for that reason.

The stored distance does not say whether the mating line captures. A capture resets the clock, so this check can drop a mate that is still playable. The in-tree draw test is still `is_draw` before the TT cutoff.

### 5. Depth-0 qsearch bound below stand-pat

Stand-pat is a lower bound. A depth-0 upper or exact TT score below the current stand-pat contradicts it (the static eval moved, usually through correction history). The old qsearch returned that score. The later block `BoundUpper && tt_score < eval` would also copy it back into eval if the cutoff itself were skipped and `tt_score` were left in place. The fix clears `tt_score` to `ValueNone` after rejecting the bound.

KQ vs K, `4k3/8/8/8/8/8/8/4KQ2 w - - 0 1`, a depth-0 upper bound of -400 stored in the TT, non-PV probe at depth 0:

| Fix | Score |
| --- | --- |
| off | -400 |
| on | 832 |

The correction applies only when the entry depth is <= 0, the side is not in check, and the bound is upper or exact. A deeper upper bound below stand-pat is still used.

**This switch is off in the default binary.** Turning it on changes real searches, not only a poisoned entry. Start position, depth 5, hand-crafted eval, moves from `d2d3` (1275 nodes) to `d2d4` (867 nodes). Bench, same 8 positions and hash 16 as `scripts/check_pins.sh`, each switch measured on its own:

| Depth | Eval | Fix off (lock pin) | Qsearch fix on |
| --- | --- | --- | --- |
| 11 | hand-crafted | 375354 | 376782 |
| 11 | NNUE | 312866 | 300010 |
| 13 | hand-crafted | 907205 | 830513 |
| 13 | NNUE | 862329 | 793816 |

At both depths the other two switches, alone and together, reproduced the lock pins. Depths 16, 20, and 22 were not re-run with the qsearch correction enabled.

### 6. LMR clamp

`std::clamp` requires `lo <= hi`. The reduced-depth call used `std::clamp(new_depth - r, 1, new_depth)`. A singular extension of -2 at depth 2 sets `new_depth = -1`. The reduced search is now entered only when `new_depth >= 1` (and the previous `depth >= 2` condition). A negative `new_depth` still falls through to the unreduced `search`, and `search` at depth <= 0 is qsearch, which is defined.

`SingularDepth = 2`, start position, depth 4, returns `d2d4`. That run shows the search finishes with the guard in place. It does not show that an extension of -2 was taken.

## PVS and the other re-searches

The PVS ladder was left as it is. On a PV node the first move is searched with `(-beta, -alpha)`. Later moves go through a null window `(-alpha - 1, -alpha)`. A move that raises alpha is searched again with the full window. LMR, when it applies, is a null window at the reduced depth and, if that score exceeds alpha and the search was not aborted, a null window at `new_depth` before the PV re-search. The full-depth null-window re-search is skipped when the reduced search already aborted.

These were read and not changed. No wrong score was reproduced from them:

- Null-move verification at depth >= 14 searches the same stack frame with `null_move_allowed` cleared, then restores the inherited double-extension count. The verification search writes history and cutoff state on that frame.
- ProbCut searches at `depth - 4` and stores the cutoff with depth `depth - 3`.
- TT store writes a non-empty move even when the depth check keeps the previous score. A shallower store can replace the move of a deeper entry and leave that entry's score.
- Mate-distance pruning (`alpha = max(alpha, mated_in(ply))`, `beta = min(beta, mate_in(ply + 1))`) matches the usual formula.
- `score_to_tt` / `score_from_tt` ply adjustment is consistent: the stored value is the distance from the node that stored it, and the probe shifts by the current ply.

## Tests

`forge-combo29/tests/search_bounds_test.cpp`, linked to the same `forge_lib` and the same compile flags as the `forge` binary.

```bash
cd forge-combo29
CXX=g++ cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4 --target search_bounds_test forge
./build/search_bounds_test
./build/search_bounds_test isolate 11   # optional: 8 switch masks, hand-crafted and NNUE
bash scripts/check_pins.sh build/forge
```

`isolate` prints `mask N hce <nodes> nnue <nodes>`. Bit 0 is `mate_horizon`, bit 1 is `aspiration`, bit 2 is `qsearch_shallow_bound`. Mask 0 is every switch off. Mask 7 is every switch on.

Last run of `./build/search_bounds_test`:

```
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

Mate in one (`r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4`, depth 2) is `h5f7` at `31999` with the horizon check on. Qxf7 is a capture and resets the clock; the test only checks that a short mate is still found.

## Lock pins

`scripts/check_pins.sh` against `build/forge`, shipping defaults (`qsearch_shallow_bound` off, the other two on):

```
net-on : 312866 862329 3024920 12389307 34048354
net-off: 375354 907205 2448617 13573040 24506465
perft5 : 4865609
PINS MATCH combo29
```

Depths are 11, 13, 16, 20, 22. Those are the combo29 lock counts.

## Limitations

- The qsearch stand-pat correction is compiled and tested, and the default binary does not use it. There is no UCI option. Depths 16, 20, and 22 were not measured with it on. Enabling it changes move choice in ordinary search (start position, depth 5, hand-crafted eval, `d2d3` vs `d2d4`).
- A completed aspiration re-search can publish a score below the fail-high from the previous attempt. Alpha is not raised on fail-high. Only an aborted re-search keeps the fail-high value, and that value is printed as an exact `cp` score.
- The mate-horizon check can reject a mate whose later captures would reset the 50-move clock. It does not change `is_draw`.
- The stuck-window result is an arithmetic test plus the loop's `give_up` path. No bench position was seen returning `-Infinite`.
- The LMR test proves the precondition and that a `SingularDepth = 2` search returns a move. It does not prove the extension of -2 was executed.
- The partial-PV and fail-high cases use the audit hooks and the hand-crafted eval. They go through the real abort handler. They are not UCI time-loss traces, and the centipawn numbers are not NNUE scores.
- `search_fixes()` is process-wide. Flipping it on another thread during a search is not supported.
- No Elo, and no claim that the container's node rate says anything about the lock's speed.
- Do not merge this into the lock on the strength of the pin match alone. The qsearch correction, if it is ever defaulted on, needs its own pin update and a strength test on Couns's machine.

# THE REPAIR'S PRICE UNDER REAL CLOCKS, AND THE MERGE QUESTION

Seat 25. A = PC r15 (original), B = PC r15 + refusable-aware fifty-move test (my S-F22 narrow repair).
PC20, Threads 1, Hash 16, `go wtime T btime T winc 0 binc 0`, T in {1000, 5000, 10000} ms, 3 runs per position.
Groups: BUG = my two clock-99 boards; RISK = the ten pawnless positions from the risk grid.

## The price, measured

| group | clock | A depth | B depth | change | A clock% | B clock% | change |
|---|---|---|---|---|---|---|---|
| BUG | 1000 | 22 | **12** | **-11 plies** | 4.6% | 11.5% | +6.9 pts |
| BUG | 5000 | 32 | **14** | **-18 plies** | 4.3% | 7.8% | +3.5 pts |
| BUG | 10000 | 36 | **15** | **-20 plies** | 3.6% | 8.1% | +4.5 pts |
| RISK | 1000 | 64 | 64 | 0 | 0.5% | 1.7% | +1.2 pts |
| RISK | 5000 | 64 | 64 | 0 | 0.1% | 0.3% | +0.2 pts |
| RISK | 10000 | 64 | 64 | 0 | 0.1% | 0.2% | +0.1 pts |

**The repair is not nearly free. It costs 11 to 20 plies of depth and roughly doubles the clock fraction, on
exactly the positions it touches.** At `wtime 10000` an 18-20 ply loss is the difference between a searched
position and a much shallower one. On the RISK group it costs nothing measurable (depth saturates at 64), which is
consistent with the narrow repair only touching positions where a reset exists.

Note the moves also change (A: d1c1 at 5s/10s, B: e2c3), so this is not a cosmetic depth difference.

## Combined with file 6: the repair should NOT be merged and should NOT be applied

Two independent reasons, and the second is decisive:

1. **Price:** 11-20 plies of depth at every clock tried. Even if it fixed a real bug, that is a large permanent
   cost on the endings it touches.
2. **There is no bug to fix.** File 6 established that a cp 0 at a high counter is correct, because the owner's
   match program ends the game at the 100th half-move. My whole S-F3..S-F20 thread is reclassified as not a
   defect (0 of 8 boards survive file 6's inequality). So the repair buys nothing and costs 11-20 plies.

## Task 2: merge inside the root-drawn guard, or apply on its own?

**Neither - it should not be merged and not be applied.** Since you asked for the choice stated plainly: if it
ever were to be revived, it must be applied **on its own and not inside `FORGE_FIX_ROOT_DRAWN`**, because the two
touch different things:

- `FORGE_FIX_ROOT_DRAWN` changes only the ROOT classification (`root_drawn`, src/search.cpp:2571-2580) and, with
  the flag on, already reduces that test to `is_insufficient_material()` alone on the PC build.
- My patch changes `Worker::is_draw`, which runs at EVERY interior node (search.cpp:1426-1436).

Layering them would put a per-node predicate inside a root-only guard's conditional compilation, so the flag that
turns on the root fix would silently change interior-node behaviour too. That is exactly the "layering fails"
failure mode another seat proved. They are independent switches and must stay independent.

## Status of the two candidate changes, final
| change | verdict |
|---|---|
| remove the fifty-move test from `is_draw` (S-F19) | **refuted by my own A/B**: 323 cp mean score change, median 408x nodes |
| refusable-aware test (S-F22/S-F23) | **not to be pursued**: fixes a non-defect, costs 11-20 plies at every clock |
| merge into `FORGE_FIX_ROOT_DRAWN` | **no** - different scope (root vs every node); keep as separate text patches only |

All three remain EXPERIMENT text patches in my folder and were never applied to the repository tree.

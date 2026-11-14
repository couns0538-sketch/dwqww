# R4-09 finding 9: 50-move horizon on hash scores

Base `e04556ddc3a430b2e751159b0d46111ef56c8b89`. Implementation `bf4154454ddc7b226bc1734bfc84d75569cdfc07`.

## What was wrong

`TTEntry::score_usable` treated every stored clock below 90 as usable at every current clock below 90:

```text
(rule50_clock < 90 && current_clock < 90) || rule50_clock == capped
```

A depth-16 entry written at clock 0, including a 15-ply mate (`score = 31985`), was therefore a legal hash score at clock 88. From clock 88 that mate needs 15 more plies and lands at clock 103, which is a 50-move draw, not a win. The same was true of a non-mate whose stored depth itself reaches clock 100 (`88 + 16 = 104`).

Main search and quiescence both build `tt_score` from `score_usable` before a hash cutoff (`src/search.cpp` quiescence cutoff, and the main-search cutoff that also requires `halfmove_clock() < 90`). On this base, quiescence already refuses the cutoff when `halfmove_clock() >= 90` (`!near50`). It did not have a separate horizon test. A below-90 cutoff used whatever `score_usable` accepted, so the missing horizon was the quiescence hole as well as the main-search hole. Clocks at or above 90 were already gated.

## Reproduction on the base

Before the edit, direct calls on a `TTEntry` returned usable:

| Entry | Clock | `score_usable` | Intended |
| --- | ---: | --- | --- |
| mate 31985, depth 16, stored clock 0 | 88 | true | false (`88 + 15 = 103`) |
| cp 400, depth 16, stored clock 0 | 88 | true | false (`88 + 16 = 104`) |
| cp 400, depth 5, stored clock 0 | 88 | true | true (`88 + 5 = 93`) |
| mate 31985, depth 16, stored clock 0 | 0 | true | true |

Search check, same binary, `8/8/8/3k4/8/8/2Q5/3K4 w - - 87 50`, depth 5, Hash 16, one thread. The child after `c2b2` is that position at clock 88. An empty table searched 2852 nodes and scored 969. Storing mate 31985, depth 16, rule-50 clock 0 on that child, with eval `ValueNone` and no hash move, searched 2939 nodes. The bad score was being read. The root score stayed 969 because the root is a PV node and re-searches a fail-high; the cutoff still changed the tree.

`check_pins.sh` on the unfixed release binary is the combo29 lock (312866 / 862329 / 4865609). The bug is outside those low-clock benches.

## Fix

`score_usable` now does two things, and nothing else moved.

1. A mate whose ply distance from the current clock passes 100 is not usable, even when the clocks match. Checkmate on the move that makes the clock 100 is still a win, so the test is `>` 100. An 11-ply mate from clock 80 ends at clock 91 and stays a win.
2. The below-90 shortcut applies only when `stored clock + depth < 100` and `current clock + depth < 100`. An exact clock match stays usable for a non-mate, because that search already applied the draw. A depth-5 score from clock 0 remains usable at clock 88.

Quiescence did not need its own edit. Its hash cutoff already requires `halfmove_clock() < 90`, and it only cuts off when `tt_score` is present. `tt_score` is now `ValueNone` for a horizon-crossing entry, so the cutoff cannot return it. The same predicate feeds the main-search cutoff and the static-eval override in both routines.

A same-clock non-mate at clock 95 is still usable. Quiescence does not cut off on it, because of `!near50`. Depth 4 from `8/8/8/3k4/8/8/2Q5/3K4 w - - 95 50` has no capture and no pawn move, so every line meets the draw. The search scores 0 and returns a legal move. That did not require a second code change.

No `CMakeLists.txt` edit and no `FORGE_*` change. Default benches stay on the lock, so the horizon rule is not behind an option.

## Astra's eight depth-9 differences

These are soak faults 084 through 091. Root clocks are 72, 74, 76, or 79. All eight differ from the unchanged lock at depth 9 with Threads 1, Hash 16, OwnBook false, UseNNUE true, and the three t22 options false. This fix does not change any of them. They remain equality failures. Restoring the lock's node counts would mean dropping the per-node rule-50 gates.

The gates are not a root test. `near50` is `board.halfmove_clock() >= 90` at the node being searched. From root clock 76 the depth-9 search of fault 084 reaches selective depth 23, and a descendant at ply 14 is already at clock 90 (`5k2/K7/7p/2q4P/8/8/8/8 w - - 90 143` in the soak trace). Requested depth is not a maximum path length: checks and other extensions walk into the gates from roots below 80. Masking those gates off to match the lock is the wrong result. The inequality is the intended behaviour.

| Index | Fault | Root clock | Move | Lock score / nodes | This engine | Still differs |
| ---: | --- | ---: | --- | --- | --- | --- |
| 3228 | 084 | 76 | `b5c4` | cp -1689 / 32435 | cp -1689 / 31749 | nodes |
| 9834 | 088 | 74 | `f3e2` | cp -1117 / 43672 | cp -1164 / 49669 | score, nodes, PV |
| 10567 | 085 | 76 | `c1b2` | mate -8 / 7581 | mate -8 / 7582 | nodes |
| 11000 | 089 | 79 | `g8g2` | cp 460 / 14618 | cp 460 / 14025 | nodes, PV |
| 12276 | 086 | 79 | `f6f5` | cp 443 / 8682 | cp 443 / 8688 | nodes |
| 12999 | 087 | 79 | `f6e5` | cp 1181 / 12873 | cp 1187 / 12663 | score, nodes, PV |
| 14002 | 090 | 79 | `a5c7` | cp -1214 / 36360 | cp -1178 / 26217 | score, nodes, PV |
| 25354 | 091 | 72 | `c4d4` | cp -1812 / 29685 | cp -1812 / 29687 | nodes |

Best moves agree. Three scores differ (9834, 12999, 14002) and four PVs differ (those three plus 11000). Fault 090 needs the pruning-clock guards as well as the transposition gates; turning only the transposition gates off does not reproduce the lock. None of that is a reason to weaken the guards or to treat lock equality as the expected result.

`tests_r4_09/horizon_test.cpp` searches each root and prints `EQUALITY_FAIL` with the lock and engine figures. The process exits non-zero if a root starts matching the lock on both score and nodes, or if the safeguarded score, nodes, or move changes. The printed failure is the equality criterion. It is not a pass.

## Pins and sanitizers

Release `check_pins.sh` on the built `forge` binary:

```text
net-on : 312866 862329 3024920 12389307 34048354
net-off: 375354 907205 2448617 13573040 24506465
perft5 : 4865609
PINS MATCH combo29
```

The same three required counts are checked inside the sanitizer run: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

`horizon_test` was compiled with `-O3 -DNDEBUG -fsanitize=address,undefined -fno-sanitize-recover=undefined` and the same `FORGE_*` definitions the root `CMakeLists.txt` already uses (`FORGE_NNUE_HIDDEN=256`, the speed switches, march `x86-64-v4`). No file under `CMakeLists.txt` was edited. The run printed `ALL CHECKS PASSED` and exited 0. It covered the predicate cases above, the stored-entry probe, the clock-95 draw, the clock-87/88 poison (score stays 969), the eight depth-9 roots, the pins, and 200 depth-10 searches. Every depth-10 best move was legal. A failed check returns 1.

R4 DONE bf4154454ddc7b226bc1734bfc84d75569cdfc07

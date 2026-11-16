# Three patches from seat 27 — each verified alone AND all three together

Base commit `6b98f217`. Every patch applies with plain `patch -p1` from the root of `forge-combo29/`,
with **no fuzz**, in any order, and the three together build Release with g++ 13.3.

| # | file | what it changes | finding | verified alone | verified in the set |
|---|---|---|---|---|---|
| 1 | `job1/drawn_root_reporting.patch.txt` | a drawn root reports ONE `info depth 1` line instead of one per depth up to the limit | S-F1 | honesty identical, 10 info lines → 1 | yes |
| 2 | `job2/clear_hash.patch.txt` | `Searcher::clear_hash()` calls `worker->clear()` so `Clear Hash` also drops the histories | S-F4 | 9/20 → 0/20 differing bestmoves | yes |
| 3 | `job3/halfmove_clock.patch.txt` | refuses a FEN half-move clock above 100 instead of clamping it to 65535 | S-C3 (seat 01's 01-F5/01-F8) | clocks > 100 refused, clock 100 still a draw | yes |

## The combined build

```
$ cd /tmp/allthree && for p in job1/drawn_root_reporting job2/clear_hash job3/halfmove_clock; do
    patch -p1 < forge-combo29/swarm/27/$p.patch.txt; done
job1/drawn_root_reporting apply=0
job2/clear_hash apply=0
job3/halfmove_clock apply=0
$ cmake -S /tmp/allthree -B build-all -DCMAKE_BUILD_TYPE=Release && cmake --build build-all -j4
build=0        sha256 d3f1a40fbae0593e3da3ad56d55b9c5938e33e4876639f7172de1070dd7cb53a
```

## Honesty numbers, base vs all three patches (raw in `job5/honesty_all3/`)

| check | required | base `e06310ec` | all three `d3f1a40f` |
|---|---|---|---|
| bench 11 | 312866 | 312866 | 312866 |
| bench 13 | 862329 | 862329 | 862329 |
| bench 16 | 3024920 | 3024920 | 3024920 |
| go perft 5 | 4865609 | 4865609 | 4865609 |

## Behaviour in the combined build (`job5/f3_all3/`)

| case | base | all three |
|---|---|---|
| drawn root (threefold) `go depth 10` | 10 info lines claiming depth 10, nodes 0, `a2a3` | **1** info line at depth 1, nodes 0, `a2a3` |
| same position, one repetition fewer (control) | 10 info lines, real search | 10 info lines, real search, `d2d4` |
| fifty-move root `go depth 10` | 10 info lines claiming depth 10 | **1** info line |
| clock 101 / 150 / 65535 in a FEN | accepted, scored `cp 0` with 0 nodes | **refused**: `info string invalid FEN: … half-move clock above 100` |
| clock 100 in a FEN | draw, 0 nodes | draw, 0 nodes (correctly unchanged) |
| `setoption name Clear Hash` then the same position | 9 of 20 bestmoves differ from a fresh game | **0 of 20** |

## What none of these patches does

- **No strength change is claimed or measured.** Patch 1 and 3 change reporting/validation only; patch 2 changes
  what a GUI command clears. None touches the search's decisions on a legal position.
- **No speed change is claimed.** Node counts are identical on all four honesty checks, so `bench` speed is
  comparable, but I did not time them.
- Patch 3 is seat 01's finding, not mine (see S-C3 in `FINDINGS.md`); my contribution there is independent
  confirmation on the release build plus this patch.

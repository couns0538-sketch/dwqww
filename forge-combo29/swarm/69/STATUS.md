# Swarm seat 69 — status

Seat 69, area 10 (checking the others) assigned as a determinism seat.
Branch `for-fable-and-opus/swarm-69`, base `6b98f217`.
Work folder `forge-combo29/swarm/69/`.

## 2026-11-17T03:47Z — start

Assignment received: the properties a harness author relies on (fixed-budget
determinism across machine inputs, memory pressure, TT initial state, Hash size,
cross-build on non-lone-king roots). Two FEN-correction messages received from the
coordinator during the turn; both incorporated before any measurement.

## Build

| build | how | pins |
|---|---|---|
| base | `6b98f217`, Release, g++ 13.3, `-march=x86-64-v4` | 4/4 match |
| PC | `6b98f217` + `pc_r15.patch` (sha256 `d6bd72c5…`) | 4/4 match |
| base-B | base source again, `-g`, different directory | 3/3 bench pins match |

The default `/usr/bin/c++` on this machine is clang 18 and cannot find `libstdc++`;
both builds pin `-DCMAKE_CXX_COMPILER=g++`.

## Done

* `ucih.py` — interactive UCI driver (stdin held open, `bestmove` with timeout, both
  streams scanned for `invalid FEN`, python-chess validation before every send).
* `fault_proof.py` — 7 planted faults, 7 caught, 0 uncaught.
* `job1/wrapper_proof.py` — 9 checks that the environment wrappers actually bite, 0 failed.
* `job1_env_matrix.py` — 12 environment variants × 2 budgets × 40 positions.
* `job3_tt_state.py`, `job3b_tt_reproducible.py`, `job3c_game_walk.py` — TT initial state,
  reproducibility of the carried state, and the game-walking pattern.
* `job4_hash_size.py`, `job4b_hash_sensitivity.py` — Hash size across four budgets plus 2M.
* `job5_cross_build.py` — base vs PC, 200 + 341 non-lone-king positions and 12 lone-king.
* `job6_second_build.py` — a second build of the same source as the machine proxy.

## Headline results

1. **Nine machine-environment inputs change nothing** (0/40 each, two budgets), and a
   second build of the same source changes nothing (0/40). Fixed-budget answers are not
   environment-dependent on this machine.
2. **`Clear Hash` is not a reset**: 24/25 cells differ from a fresh process, reproducibly
   (3/3 independent processes identical), because it leaves the histories in place.
   `ucinewgame` is a true reset: 0/25.
3. **Hash size matters above ~200k nodes**: Hash 16 vs 64 differs on 17/24 positions at
   500k, 24/24 at 1M, 40/40 at 2M, and 15 of 178 differing cells also moved the bestmove.
4. **Cross-build node counts are identical outside lone-king roots**: 0/200 (set O) and
   0/341 (set G) at `go depth 12`, with the 12/12 lone-king control differing.
5. **A piped harness measures nothing**: EOF during the search yields 0 `info depth` lines
   and a fabricated, perfectly reproducible `bestmove`.

## Next command

```
cd /agent/repos/dwqww/forge-combo29/swarm/69 && python3 job2_memory_pressure.py
```

(the dedicated memory-pressure sweep: `ulimit -v` stepped down toward the 16 MB table,
to find the point where the answer or the process changes, and to report it as a cliff
rather than a single point.)

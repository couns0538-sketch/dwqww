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
* `job1/pc_env_check.raw.txt` — 4 environment variants repeated on the PC build.
* `job2_memory_pressure.py` — `ulimit -v` stepped 1 GB → 16 MB at Hash 16 and Hash 256,
  plus a bisected cliff (`job2/boundary.raw.txt`).
* `job3_tt_state.py`, `job3b_tt_reproducible.py`, `job3c_game_walk.py` — TT initial state,
  reproducibility of the carried state, and the game-walking pattern.
* `job4_hash_size.py`, `job4b_hash_sensitivity.py` — Hash size across four budgets plus 2M.
* `job5_cross_build.py` — base vs PC, 200 + 341 non-lone-king positions and 12 lone-king.
* `job6_second_build.py` — a second build of the same source as the machine proxy.

All five assigned questions are answered. Nothing is left running.

## Headline results

1. **Nine machine-environment inputs change nothing** (0/40 each, two budgets), and a
   second build of the same source changes nothing (0/40). Fixed-budget answers are not
   environment-dependent on this machine. Confirmed on the PC build too (0/20 for four of
   the variants).
2. **Memory pressure never changes an answer; it kills the process.** Above the cliff the
   answer is bit-identical; below it the engine dies. Hash 16 cliff: 56 MB dies, 60 MB
   works. Hash 256: 290 MB dies, 300 MB works. No silent middle band.
3. **`Clear Hash` is not a reset**: 24/25 cells differ from a fresh process, reproducibly
   (3/3 independent processes identical), because it leaves the histories in place.
   `ucinewgame` is a true reset: 0/25, and 0/6 on a game-walking harness.
4. **Hash size matters above ~200k nodes**: Hash 16 vs 64 differs on 17/24 positions at
   500k, 24/24 at 1M, 40/40 at 2M, and 15 of 178 differing cells also moved the bestmove.
5. **Cross-build node counts are identical outside lone-king roots**: 0/200 (set O) and
   0/341 (set G) at `go depth 12`, with the 12/12 lone-king control differing.
6. **A piped harness measures nothing**: EOF during the search yields 0 `info depth` lines
   and a fabricated, perfectly reproducible `bestmove`.

## Next command

Nothing is pending. If more time is granted, the open question worth the instrument is
why Hash 16 and Hash 64 diverge at 1,000,000 nodes: it needs a build printing TT
collision/overwrite counts, which is a source change this seat may only submit as a
`.patch.txt` and has not written.

## 2026-11-17T04:35Z — four follow-ups answered

Coordinator asked four questions raised by the first report. All answered, one produced a
correction to my own earlier finding.

| # | question | answer | evidence |
|---|---|---|---|
| 1 | is the piped fabrication always the same move? | **no** — 13 distinct / 60 positions, all legal, 0/60 equal to the real answer; detectable only by `info depth` == 0 | `job8/` |
| 2 | does the Clear Hash drift move the bestmove? | **yes** — 70 / 200 at `go nodes 50000`, budget-stable | `job9/` |
| 3 | Hash 128 vs 256 threshold? | **`go nodes 1,000,000`** (2/24), and 64 vs 256 is 0/24 at 500k — earlier 17/24 was Hash 16 too small | `job10/` |
| 4 | does history leak across `ucinewgame`? | **no** — 4/4 sequences identical; the state comes from the `position` command, not from process state | `job11/` |

**Correction issued:** finding 69-F8b claimed `position fen` and `position startpos moves`
were interchangeable. They are not — they diverge once a threefold repetition is in the move
list (0/4 at 0–1 repetitions, 4/4 at 2–3). Job 3c could not detect this because its random
games had no threefold. Recorded as 69-F8c.

Also answered incidentally: why job 7 stalled — my drain logic issued a second `isready`
after already reading to `readyok`; fixed, and the job now completes in under a second.

## Time

`stamps.txt` files in `job1/` … `job11/` each hold a `date -u` line after that job's last
part.


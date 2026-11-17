# REPORT — swarm seat 69, determinism of fixed-budget searches

## What was asked

The properties a harness author relies on: (1) is a fixed `go nodes N` answer identical
across machines, tested through every proxy available on one machine; (2) is it stable
under memory pressure; (3) does the transposition table's initial state matter, and is
`ucinewgame` a cold reset while `Clear Hash` is not; (4) is `Hash 16` vs `Hash 64`
identical for a fixed node budget; (5) cross-build node counts at `go depth 12` on
non-lone-king roots, 200 positions.

## The answer

1. **Across machines, as far as one machine can test it: yes.** Every environment input a
   harness could plausibly vary leaves the answer untouched, and so does a second build of
   the same source. No second machine was available; that limit is stated, not glossed.
2. **Memory pressure: it never changes an answer, it kills the process.** Clean cliff,
   bisected.
3. **The table's initial state matters, and `Clear Hash` is not a reset** — exactly as the
   docs said. This is the largest trap found: 24 of 25 cells.
4. **`Hash 16` vs `Hash 64` is identical only below ~200k nodes.** Above that it is not.
5. **Cross-build node counts on non-lone-king roots: 0 differing of 200** (set O) and
   **0 of 341** (set G), with a 12/12 lone-king control differing.

## How sure

High on 1–5 as measurements on this machine and these two builds; the cross-machine claim
in (1) rests on proxies and is explicitly bounded below. Nothing here is extrapolated to
`Threads > 1` or to wall-clock searches.

## Honesty numbers

| build | bench 11 | bench 13 | bench 16 | perft 5 |
|---|---|---|---|---|
| base | 312,866 | 862,329 | 3,024,920 | 4,865,609 |
| PC | 312,866 | 862,329 | 3,024,920 | 4,865,609 |
| base-B (`-g`) | 312,866 | 862,329 | 3,024,920 | not run |

`base-B` is the second build used in job 6; its perft was not run, so no cell depends on it.

## Steps

| step | done/partly/not | evidence file | result |
|---|---|---|---|
| build base + PC, verify pins | done | this report | 4/4 both builds |
| interactive UCI driver | done | `ucih.py` | holds stdin, `bestmove` timeout |
| plant faults, prove the harness can fail | done | `job1/fault_proof.raw.txt` | 7 checks, 7 caught |
| prove the env wrappers bite | done | `job1/wrapper_proof.raw.txt` | 9 checks, 0 failed |
| (1) environment matrix | done | `job1/env_matrix.raw.txt` | 0/40 all 12 variants, 2 budgets |
| (1) same on PC build | done | `job1/pc_env_check.raw.txt` | 0/20 all 4 variants |
| (1) second build proxy | done | `job6/second_build.raw.txt` | 0/40 both budgets |
| (2) memory pressure | done | `job2/memory_pressure.raw.txt` | 0/12 above cliff, death below |
| (2) bisect the cliff | done | `job2/boundary.raw.txt` | 56→60 MB, 290→300 MB |
| (3) TT initial state | done | `job3/tt_state.raw.txt` | 0/25 ucinewgame, 24/25 Clear Hash |
| (3) is the drift reproducible | done | `job3/tt_reproducible.raw.txt` | 3/3 processes identical |
| (3) game-walking pattern | done | `job3/game_walk.raw.txt` | 5/6 differ, 0/6 with ucinewgame |
| (4) Hash size, 4 budgets | done | `job4/hash_sensitivity.raw.txt` | 17/24 at 500k, 24/24 at 1M |
| (4) Hash size at 2M | done | `job4/hash_2m.json` | 40/40 |
| (5) cross-build, 200 positions | done | `job5/cross_build.raw.txt` | 0/200 node, 0/200 bestmove |
| (5) lone-king control | done | `job5/cross_build.raw.txt` | 12/12 differ |

## Findings

Each with the file that shows it again; the full list with ids is in `FINDINGS.md`.

* **A piped harness measures nothing.** `fault_proof.py` F3. 0 info lines, fabricated
  `bestmove a2a3`, perfectly reproducible.
* **The `invalid FEN` diagnostic moves between two streams** depending on whether `isready`
  follows `position`. `fault_proof.py` F2a/F2b.
* **`4k3/8/8/8/8/8/8/R3K2R w K - 0 0` is python-chess VALID and engine-REFUSED**, so a
  python-chess validator alone does not protect a harness. `fault_proof.py` F2.
* **`Clear Hash` is not a cold reset.** `job3_tt_state.py`. Source: `src/search.cpp:2667`
  vs `:2679`, `include/forge/search.hpp:452`.
* **The carried state is reproducible, so the wrong answer is stable.** `job3b`.
* **Hash size changes the answer above ~200k nodes.** `job4b`, `job4/hash_2m.json`.
* **Memory pressure kills rather than corrupts.** `job2/boundary.raw.txt`.
* **Cross-build divergence is confined to lone-king roots in node counts too, not only
  bestmoves.** `job5_cross_build.py`.

Command to see the Hash result again:

```
cd forge-combo29/swarm/69 && python3 job4b_hash_sensitivity.py
```

Command to see the TT result again:

```
cd forge-combo29/swarm/69 && python3 job3_tt_state.py
```

## Suspicions, not proven

* **Why Hash 16 and Hash 64 diverge at 1,000,000 nodes is not established.** "Fewer
  collisions in a bigger table" is a plausible account and nothing more; the instrument
  that would settle it is a build printing TT overwrite counts, which this seat did not
  write. It is a guess and is not presented as a result.
* **The exact per-position pattern of the carried-state drift is not characterised.** The
  direction and reproducibility are measured; which history table dominates is not.
* **A different CPU may still change a fixed-budget answer.** Nothing here tests a second
  machine, a different `-march`, or clang. The second-build experiment varies layout and
  debug info only.

## What I did NOT do

* No second physical machine, no different CPU, no clang build, no `FORGE_PORTABLE` build.
* No `Threads > 1` measurement, and no wall-clock (`movetime`) measurement.
* No source change and no patch — the task did not ask for one, and the Hash mechanism
  would need one to explain.
* No ASan/UBSan/TSan runs; this seat's questions did not require them and the brief's
  sanitizer standard was not invoked.
* Did not re-derive the previously measured facts (40/40 depth determinism, 120-position
  evaluation identity, 11/40 vs 0/60 bestmove divergence); they are used as given.

## What I am NOT sure about

* Whether the 24/25 and 5/6 reuse-trap rates hold for position sets other than the ones
  used here (first 5 of O, and 6 seeded random games). The rates are large enough that the
  direction is safe; the exact fractions are sample-dependent.
* Whether `ucinewgame` is *sufficient* as well as necessary on every command path — I
  tested `position fen` and `position startpos moves`, not every ordering a harness could
  produce with interspersed `setoption`.
* The claim "no band where memory pressure silently changes an answer" is tested at
  `Hash 16` and `Hash 256` at `go nodes 50000` only.

## Times

See `job1/stamps.txt`, `job2/stamps.txt`, `job3/stamps.txt`, `job4/stamps.txt`,
`job5/stamps.txt`, `job6/stamps.txt` — each a `date -u` line written after that job's last
part.

## Last command output

```
$ git status --short
(clean)

$ ls forge-combo29/swarm/69/
DETERMINISM.md  FINDINGS.md  STATUS.md  fault_proof.py  job1  job1_env_matrix.py
job2  job2_memory_pressure.py  job3  job3_tt_state.py  job3b_tt_reproducible.py
job3c_game_walk.py  job4  job4_hash_size.py  job4b_hash_sensitivity.py  job5
job5_cross_build.py  job6  job6_second_build.py  matrix.py  ucih.py
```

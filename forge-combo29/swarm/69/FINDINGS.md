# Swarm seat 69 — findings

Every line is a finding or a check. The command column names the committed file that
shows it again.

## Fault-proof (the harness itself)

| id | area | finding | evidence | state |
|---|---|---|---|---|
| 69-F1 | determinism | **A piped harness measures nothing.** `printf '...go depth 8\n' \| forge` prints 0 `info depth` lines and answers a fabricated `bestmove a2a3`; EOF during the search aborts it. The fabricated answer is perfectly reproducible. | `fault_proof.py` (F3a/F3b) | NEW |
| 69-F2 | determinism | The `invalid FEN` diagnostic appears in the **position reply** when `isready` follows `position`, and in the **`go` output** when it does not. Both were planted and caught; a harness that reads only one misses it half the time. | `fault_proof.py` (F2a/F2b) | NEW |
| 69-F3 | determinism | `4k3/8/8/8/8/8/8/R3K2R w K - 0 0` (fullmove 0) is **python-chess VALID** and **engine-REFUSED**. A validator built on python-chess therefore does not protect a harness here; the reply must be scanned. | `fault_proof.py` (F2) | NEW |
| 69-F4 | determinism | The environment wrappers bite: `taskset` pins the core, `nice -n 19` changes the nice value, `ulimit -v 65536` kills a `Hash 512` allocation while `Hash 16` fits, `ulimit -v 4096` kills the engine. 9 checks, 0 failed. | `job1/wrapper_proof.py`, `job1/wrapper_proof.raw.txt` | NEW |

## Machine-environment inputs (job 1)

| id | area | finding | evidence | state |
|---|---|---|---|---|
| 69-F5 | determinism | **Nine machine-environment inputs change nothing** at a fixed budget (0/40 each, two budgets): working directory, `LANG`/`LC_ALL`/`LC_NUMERIC` + `TZ`, environment-variable order, CPU affinity (cores 0/1/2), `nice -n 19`, `ulimit -v` 2 GB, `ulimit -v` 64 MB, `ulimit -s` 8 MB, `ulimit -n` 256. A fixed-budget answer is a property of the (build, position, budget) triple, not of the process environment. | `job1_env_matrix.py`, `job1/env_matrix.json` | NEW |
| 69-F5b | determinism | **Memory pressure never changes an answer; it kills the process.** Stepped `ulimit -v` from 1 GB down to 16 MB: every cap that let the engine run gave 0 / 12 differing cells, and below the cliff the engine died on 12 / 12. At `Hash 16` the cliff is between 56 MB (dies) and 60 MB (works); at `Hash 256` between 290 MB (dies) and 300 MB (works), i.e. roughly the table size plus ~40 MB. **The dangerous middle band does not exist here** — the failure is loud, not silent. | `job2_memory_pressure.py`, `job2/memory_pressure.json`, `job2/boundary.raw.txt` | NEW |
| 69-F5c | determinism | The environment invariance is not a base-build artifact: locale + TZ, `taskset -c 1`, `nice -n 19` and `ulimit -v 65536` each give **0 / 20** differing cells on the **PC** build as well. | `job1/pc_env_check.raw.txt` | NEW |

## Transposition-table state (jobs 3, 3b)

| id | area | finding | evidence | state |
|---|---|---|---|---|
| 69-F6 | determinism | **`ucinewgame` is a true cold reset (0/25 cells differ from a fresh process); `Clear Hash` is not (24/25 differ).** Read from the source: `ucinewgame` -> `Searcher::clear()` (`src/search.cpp:2679`) wipes histories *and* table; `Clear Hash` -> `Searcher::clear_hash()` (`:2667`) wipes the table then calls `Worker::clear_caches()`, which is only `evaluator_.clear()` (`include/forge/search.hpp:452`). | `job3_tt_state.py`, `job3/tt_state.json` | NEW |
| 69-F7 | determinism | **The divergence from `Clear Hash` is reproducible, not noise.** Three independent processes replaying the same sequence produced identical cells for all three reset regimes; within one process the two replays differed. So a harness that reuses a process gets a *stable-looking wrong* number and can reproduce it indefinitely. | `job3b_tt_reproducible.py`, `job3/tt_reproducible.json` | NEW |
| 69-F8 | determinism | The same position searched four times in a row in one process drifts away from its fresh-process answer deterministically: 37135 cp72, 41762 cp37, 39116 cp44, 30366 cp35. The error grows with the number of prior searches in the process. | `job3b_tt_reproducible.py` | NEW |
| 69-F8b | determinism | The reuse trap reproduces on the pattern a real harness uses — **walking games**: 5 / 6 positions reached by random legal games differ from a fresh process, under both `position startpos moves` and `position fen`, with and without `Clear Hash`. `ucinewgame` restores 0 / 6. `position fen X` and `position startpos moves <moves reaching X>` agree 0 / 6 in a fresh process, so the two command forms are interchangeable. | `job3c_game_walk.py`, `job3/game_walk.json` | NEW |

## Hash size (job 4)

| id | area | finding | evidence | state |
|---|---|---|---|---|
| 69-F9 | determinism | **On a FRESH process, `Hash 16`, `64` and `256` are bit-identical at `go nodes 50000` and `go depth 12` (0/40 and 0/24). At `go nodes 1,000,000` they are not: 24/24 positions differ between Hash 16 and Hash 256, and 9/24 between Hash 64 and 256.** The dependence is a function of the budget, so "Hash does not matter" is true only at small budgets. | `job4b_hash_sensitivity.py`, `job4/hash_sensitivity.json` | NEW |
| 69-F10 | determinism | `Hash 1` differs from `Hash 16` even at `go nodes 50000` (11/24), and 24/24 at every larger budget. A harness that shrinks Hash to save memory silently changes the measurement. | `job4b_hash_sensitivity.py` | NEW |
| 69-F11 | determinism | Of 178 differing (budget, Hash pair, position) cells, **15 also moved the BESTMOVE** and 13 differ by exactly one node. Both classes are real: a single node is enough to change a downstream ratio, and the bestmove changes are what a strength comparison would see. | `job4/hash_sensitivity.json`, `job4/hash_sensitivity.raw.txt` | NEW |
| 69-F12 | determinism | A warm process differs from a fresh process at **every** Hash size (40/40, both budgets), so table size does not rescue the reuse trap: warm-16 vs fresh-16 is 40/40 apart. | `job4_hash_size.py`, `job4/hash_size.json` | NEW |

## Cross-build (job 5)

| id | area | finding | evidence | state |
|---|---|---|---|---|
| 69-F13 | cross-build | **Cross-build node counts at `go depth 12`, Threads 1, are identical on non-lone-king roots: 0 differing of 200 on set O and 0 differing of 341 on set G — and 0 differing bestmoves as well.** The lone-king control differs 12/12 on the same run, so the predicate separates the classes cleanly. | `job5_cross_build.py`, `job5/cross_build.json` | NEW |
| 69-F14 | cross-build | The cross-build divergence is confined to lone-king roots **in node counts as well as in bestmoves**, and it is large when it happens: +161,907 nodes at `8/6qk/8/8/8/1p4p1/4K3/8 b - - 0 1`, -94,836 at `go nodes 200000` on the same FEN. | `job5/cross_build.json` | NEW |
| 69-F15 | cross-build | The same divergence reproduces under a different budget (`go nodes 200000`): 12/12 lone-king roots differ, 0/200 and 0/341 non-lone-king differ. It is a property of the position class, not of `go depth`. | `job5_cross_build.py` | NEW |

## Second build as a machine proxy (job 6)

| id | area | finding | evidence | state |
|---|---|---|---|---|
| 69-F16 | determinism | **A second build of the identical source, in a different directory, with `-g` added (different binary, 4,869,512 vs 794,944 bytes), gives identical answers: 0/40 differing at both budgets, and it passes all three bench pins.** No build-address, allocation-order, uninitialised-read or timestamp dependence was detected. This is a proxy, not a second machine. | `job6_second_build.py`, `job6/second_build.json` | NEW |

## Not established by this seat

* **A genuinely different machine was not tested.** No second CPU, no second compiler, no
  second OS. Job 6 varies the build only. A different ISA path (`-march` below
  `x86-64-v4`, i.e. `FORGE_PORTABLE`), a different compiler (clang), or a different CPU
  could still change a fixed-budget answer; nothing here rules that out.
* **Wall-clock searches are outside this file.** The brief already established they are not
  reproducible; this seat did not re-measure them and no number here should be read as
  applying to a `movetime` search.
* **Threads > 1 is outside this file.** Every cell is `Threads 1`.
* **Why Hash 16 and Hash 64 diverge at 1,000,000 nodes is not explained.** The count moves
  and the mechanism was not instrumented; "fewer collisions in a bigger table" is a guess,
  not a measurement.

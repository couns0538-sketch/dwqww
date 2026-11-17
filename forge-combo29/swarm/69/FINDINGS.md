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
| 69-F8b | determinism | The reuse trap reproduces on the pattern a real harness uses — **walking games**: 5 / 6 positions reached by random legal games differ from a fresh process, under both `position startpos moves` and `position fen`, with and without `Clear Hash`. `ucinewgame` restores 0 / 6. | `job3c_game_walk.py`, `job3/game_walk.json` | NEW |
| 69-F8c | determinism | **CORRECTION to 69-F8b.** That line said the two command forms are interchangeable; they are **not**, and job 3c could not see it because its 40-ply games contained no threefold repetition. `position fen` and `position startpos moves` agree at 0 and 1 repetitions (0 / 4 cells) and **diverge at 2 and 3 repetitions (4 / 4 cells)**. A FEN cannot carry repetition history; a move list can. | `job11b_fen_vs_moves.py`, `job11/fen_vs_moves_repetition.raw.txt` | NEW |

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

## Four follow-ups requested by the coordinator

| id | area | finding | evidence | state |
|---|---|---|---|---|
| 69-F17 | determinism | **The piped-EOF fabrication is per-position, not one fixed move.** 13 distinct fabricated moves across 60 positions at `go depth 8`, 0 of 60 equal to the real answer, and **all 60 legal**: a legality check accepts 60 / 60 of them. A piped run is therefore NOT detectable by its move. It IS detectable by `info depth` lines == 0, which held 60 / 60. | `job8_piped_fabrication.py`, `job8/piped_fabrication.raw.txt` | NEW |
| 69-F18 | determinism | The fabrication is also budget-independent: at `go depth 4`, `depth 8`, `depth 12`, `nodes 50000` and `nodes 500000` the same 6 distinct fabrications appear for the same 20 positions, with 20 / 20 zero-info lines every time. So the fabricated move is a function of the position only. | `job8/budget_variation.raw.txt` | NEW |
| 69-F19 | determinism | **The `Clear Hash` drift changes the BEST MOVE, not only the score: 70 / 200 at `go nodes 50000`** (score differs 195 / 200, depth 132 / 200, nodes-only 129 / 200). It is budget-stable: 12 / 40 at 50k and 11 / 40 at 500k on a 40-position prefix. `ucinewgame` is 0 / 200 on every field. So the reuse trap corrupts exactly the quantity a strength comparison measures. | `job9_clearhash_bestmove.py`, `job9/clearhash_bestmove.raw.txt` | NEW |
| 69-F20 | determinism | **Extending the ladder: Hash 128 vs 256 first differs at `go nodes 1,000,000` (2 / 24), then 15 / 24 at 2M and 24 / 24 at 4M.** 64 vs 128 matches that exactly (9 / 24 at 1M). **But at 500,000 nodes, Hash 64 vs 256 is 0 / 24** — so the earlier 17 / 24 at 500k was the 16 MB table being too small, not table growth in general. The safe floor is ~64 MB, not ~16 MB, at 500k. | `job10_hash_ladder.py`, `job10/hash_ladder.json` | NEW |
| 69-F21 | determinism | **History does NOT leak across `ucinewgame`, and does not leak across searches at all.** A repetition-laden position followed by another search with or without `ucinewgame` gives the identical cell (4 / 4 sequences). The repetition state is carried by the `position startpos moves` command itself, and is rebuilt per command. | `job11_history_leak.py`, `job11/history_leak.raw.txt` | NEW |
| 69-F22 | cross-build | The base build's drawn-root bail appears on a threefold root reached **by move list**: base answers `0 nodes, cp 0, a2a3`; PC answers `34,047 nodes, cp 22, e2e4`. Via `position fen` both builds answer `56,720 / e2e4 / cp 30`, so the divergence is reachable only through the move-list form. | `job11b_fen_vs_moves.py`, `job11/fen_vs_moves_repetition.raw.txt` | NEW |
| 69-F23 | determinism | **The threshold is THREE occurrences, not two.** With exactly 2 prior occurrences of the final position the two command forms agree on both builds; at 3 they diverge. So the trigger is a genuine threefold, not any repetition. A 2-fold is common in play (14.5% of 200-ply random games contain one) and is harmless here. | `job12_repetition_threshold.py`, `job12/repetition_threshold.raw.txt` | NEW |
| 69-F24 | cross-build | **The bail is not an endgame artifact: it fires on a 32-piece middlegame threefold.** Real opening (`e2e4 … e8g8`) plus a legal knight/queen cycle, 32 pieces on the board, 24 plies: base answers `0 nodes, cp 0, a2a3` at every budget tested (`go depth 8/12/14`, `go nodes 50000`, `go nodes 500000`); PC answers `b3e6` with a real search every time. The FEN form of the same board gives `b3e6 cp 32` on both builds. **The base's answer is off by 32 cp and is the wrong move.** | `job12/middlegame_threefold.raw.txt`, `job12/middlegame_repeat_check.raw.txt` | NEW |
| 69-F25 | determinism | The bailing cell is fully deterministic — 3 runs on each build give 1 distinct result. It is not noise; it is a stable wrong answer. | `job12/middlegame_repeat_check.raw.txt` | NEW |
| 69-F25b | determinism | **The bail has a loud signature a harness can filter on:** the base emits **64 info lines** each `score cp 0 nodes 0 nps 0 hashfull 0 time 0` with an **empty `pv`**, climbing to `depth 64` — while a real search emits 11 lines with populated nodes/pv. A cell with `nodes 0` and an empty PV is the bail, not a search. | `job12/bail_signature.raw.txt` | NEW |
| 69-F26 | determinism | **Exposure bound: a random-position harness is essentially never affected** — 0 threefolds in 600 random games of 60/120/200 plies, and 0 in 4,000 further 160-ply seeds. A harness that replays **real games** to a threefold is affected and gets a silently wrong move, not an error. | `job12/threshold_rate.raw.txt`, `job12/real_game_threefold.raw.txt` | NEW |

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

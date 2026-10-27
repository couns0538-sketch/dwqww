# O1-LTT [Engine QA, test plan G-B5] Lockless TT (UCI LocklessTT, default false) — DONE

**Branch.** `opus-O1-LTT` = `opus-O1` (with its SmpBestThread review fix) + `opus-O3` with the 64-byte pins +
[O1-LTT] commits:
- `1ca23f8`: option, lockless entries, tests
- `df4d437`: dispatch first, CI, TSan hook
- `60b0375`: CI fix
- `c06eef2`: cheaper lockless probe (key checks only for occupied slots until a match; one-multiply check hash);
  CI adds a same-binary LocklessTT off/on bench A/B at Threads 1
- follow-up (2026-10-27, the commit that adds this line): `setoption name LocklessTT value true` answers
  `info string LocklessTT active` (section "Follow-up" below)

**Patch.** `patch.diff` = `git diff origin/opus-O1 HEAD` over the engine tree, tests and `tools/`; it also
contains the O3 pins it merged. Ideas: `IDEA_SOURCE.md` (Hyatt & Mann 2002 lockless hashing; CPW "Shared Hash Table"; own variant).

**Status.** UNPROVEN until gated; no Elo claim. The gate is SMP-only (Threads > 1).

## What it does
UCI `option name LocklessTT type check default false`. With the option on, the shared transposition table
is probed and written without its 1024 striped mutexes:
- **Two words.** Each 16-byte entry is two 64-bit words, read and written with one relaxed atomic access each
  (`__atomic` builtins). The second word is bytes 8-15 of the entry, unchanged: score, eval, depth,
  generation/bound, rule-50 clock.
- **The key check.** The first word holds the move in its high half. Its low half holds the 32-bit key tag XOR a
  32-bit check hash of the move and the whole second word: the high half of one 64-bit product
  `(second ^ spread(move)) * 0x9E3779B97F4A7C15` (odd multiplier, so two writes with different data give
  different products). A read that sees the two words of different writes recovers a tag that is off by the
  difference of two hashes, so the probe misses (and a store sees another position) instead of returning a torn
  entry. A false match needs the high halves to collide (about 2^-32).
- **Same rules as locked.** `probe_lockless` / `store_lockless` / `hashfull_lockless`
  (`src/search/tt_lockless.inc`) make exactly the locked functions' decisions: hit test, replacement victim,
  admission, generation refresh, hashfull. The probe reads the four slots' words, takes occupancy, depth and
  generation straight from the payload word, and computes the key check only for occupied slots, in slot order,
  until one matches (the locked probe's decision order); the hit or victim slot is decoded once. A search with
  Threads=1 is therefore unchanged, and bench with the option on equals the lock pins (below).
- **What is lost.** Concurrent writes to one slot can leave it combining two writes. Such a slot matches no key
  and is replaced like any other entry. That is the only loss compared with the locked table.
- **Mode switch.** `Searcher::search` applies the option once per search, while no worker runs. A change clears
  the table, because the two modes store entries differently. `uci_stress.py --toggle-options` toggles it
  between searches.

**Default build.** The option is off, and `probe`, `store` and `hashfull` gained one test of `lockless_`:
- **Where the lockless code sits.** The lockless functions are `noinline` and live in section `.text.forge_ltt`,
  which the PE linker places after all `.text`.
- **The dispatch.** `store` tests the flag first and, with GCC 15+, tail-calls `store_lockless`
  (`[[gnu::musttail]]`). `probe` returns a structure in memory, so it uses an ordinary call. Its dispatch still
  costs only a compare and a branch on the default path.
- **Placement.** With O3's review-fix pins merged, alpha-beta and qsearch are instruction-identical to O3 with
  pins at 0 mod 64; only probe and store differ (section "Default build").

## Acceptance

| # | acceptance line | result |
|---|---|---|
| 1 | OFF -> bench exact | **PASS**: PC recipe build of `c06eef2`, exe sha256 `5e187b15…`, d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, FMA 0, ALL OK (`logs/identity_pc_recipe.log`); Linux CI release identity ALL OK, FMA 0 (`logs/ci/opus_ci_40474683617_c06eef2a/release_identity.log`) |
| 2 | tests/tt_coherence_tests.cpp extended | **PASS**: every one of the 12 existing groups runs with the locked and with the lockless table (concurrent groups: misses allowed when lockless, hits always fully correlated), + 4 new lockless groups: encode/decode identity on 200,000 random entries; 1,750,000 torn mixes of two writes, 0 decoded to a written key; lockless == locked on a 300,000-operation random sequence (hits, entries, victims, hashfull); a mode switch clears. 28 groups pass (`logs/tt_coherence_tests_local.log`; CI) |
| 3 | new multi-thread TT stress test (Threads 2/4/8, TSan clean, 0 corrupted moves after 10M probes/stores) | **PASS**: 24 runs (Threads 2/4/8 × lockless/locked × 2 key shapes × release/TSan build), 10M operations each, **0 corrupted** in all 24, **TSan reports: 0** (CI run 40474683529, `logs/ci/run_40474683529_c06eef2a/stress.log`; the same on `60b0375`, run 40471171993) |
| 4 | ON Threads=1 bench recorded | **PASS**: with LocklessTT=true, bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, identical to OFF (`logs/identity_pc_recipe.log`) |
| 5 | SMP NPS and time-to-depth Threads 1/2/4/8 OFF vs ON | **DONE** (numbers in "Scaling"): no significant time-to-depth difference at any thread count on a 4-vCPU runner; same-binary Threads=1 bench NPS with the option on −2.25% (d16) / −2.06% (d20), both 95% intervals below 0 |
| §3 | ctest only known failures; ASan+UBSan; TSan | **PASS**: CI opus-ci run 40474683617 (`c06eef2`): release, ASan+UBSan and TSan ctest each "KNOWN-FAILURE CHECK: PASS (only the 4 known forge_tests lines; no sanitizer report)"; TSan hook `tsan_extra.sh` (engine searches with LocklessTT at Threads 2/4, option toggled between searches): TSan 0 reports, uci_stress 60 go / 60 bestmove, 0 illegal, 0 hangs (`logs/ci/opus_ci_40474683617_c06eef2a/`) |
| — | planted bug: the key check disabled | **caught**: `forge_tt_tests` fails ("FAIL: concurrent aged-hit refresh tore payload, lost recency or mutated snapshot"), and the stress test returns corrupted entries: locally 156-191 per 4M operations at 2 threads (`logs/planted_bug_local.log`); on CI 5,341 (T4) and 6,296 (T8) per 10M on `c06eef2` (run 40474683529), 5,151 and 4,431 on `60b0375` (run 40471171993) (`planted_stress.log` in each run folder) |

### Follow-up (2026-10-27): "info string LocklessTT active"
Every `setoption name LocklessTT value true` answers `info string LocklessTT active`, so engine logs (fastchess
`engine_io.log`, gate logs) show that the lockless table is on. The table switches at the next search, as before.
`false` and invalid values print no such line; invalid values keep their "invalid value" message. Output only:
no search or table code changed.

| check | result | evidence |
|---|---|---|
| line on `true`, none on `false` / invalid | **PASS**. New `tools/uci_regression.py` check: it waits for the line after `true`, searches depth 6 with the option on, then asserts that `false` and `maybe` print nothing before `readyok`. `uci_regression` passes (box-recipe exe sha256 `08094b31…`). A manual probe gives `info string LocklessTT active` once, for the `true` line only | `logs/followup_uci_regression.log`, `logs/followup_probe.log` |
| OFF = AL1 | **PASS**. Box recipe: bench 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690, ALL OK; FMA 0 | `logs/followup_identity_pc_recipe.log` |
| Linux release/ASan/TSan ctest | the opus-ci run on this push | — |

## TT stress (tests/tt_stress_tests.cpp)
- **Method.** N threads probe and store one shared table with a small, colliding key set: 64 keys over 4
  clusters, and a harder shape with 8 keys in 1 cluster. The data of every stored entry is a function of its
  key (score, eval, depth, move, bound, pv, clock), so any probe hit whose data does not match its key is a
  corrupted entry.
- **Local** (2 threads, the PC's limit): lockless and locked, both shapes, 4M operations each: 0 corrupted.
  Lockless ran 2M operations in 0.045 s against 0.094 s locked (`logs/tt_stress_local_t2.log`).
- **CI** (run 40474683529, `c06eef2`): Threads 2/4/8 × lockless/locked × both shapes × release and TSan builds,
  10M operations each: 24/24 PASS with 0 corrupted entries; TSan reports: 0. Speed on the TSan build at Threads 8,
  for scale only: lockless 1.5 s, locked 17.7 s (4 clusters) and 34.4 s (1 cluster) per 10M operations.

## Scaling (CI, 36 positions, depth 20, 5 runs per thread count and mode, interleaved)
GitHub runner with 4 vCPUs (2 cores), so Threads 8 is oversubscribed. `scaling_summary.py` output, `c06eef2`
(run 40474683529, `logs/ci/run_40474683529_c06eef2a/scaling_summary.log`, raw `scaling_t*_{off,on}.tsv`):

| threads | mode | time-to-depth mean (sd) | nodes mean | NPS | on/off time | on/off NPS |
|---:|---|---|---:|---:|---:|---:|
| 1 | off | 36.61 s (0.21) | 54,933,743 | 1,500,459 | | |
| 1 | on | 37.38 s (0.20) | 54,933,743 | 1,469,475 | 1.021 | 0.979 |
| 2 | off | 31.03 s (1.73) | 87,807,452 | 2,829,435 | | |
| 2 | on | 32.21 s (2.22) | 90,188,264 | 2,799,944 | 1.038 | 0.990 |
| 4 | off | 34.94 s (1.95) | 135,426,142 | 3,876,029 | | |
| 4 | on | 34.26 s (1.62) | 134,667,551 | 3,931,312 | 0.980 | 1.014 |
| 8 | off | 49.07 s (4.08) | 195,961,608 | 3,993,274 | | |
| 8 | on | 45.97 s (2.25) | 185,887,392 | 4,043,810 | 0.937 | 1.013 |

- **Threads 1:** nodes are identical (same search). The same-binary bench A/B (`nps_ab_options.py`, 10 runs
  each, interleaved, `logs/ci/run_40474683529_c06eef2a/nps_ab_ltt_off_vs_on_t1.log`) puts the option-on cost at
  **−2.25% (d16; 95% CI −2.86% .. −1.64%) and −2.06% (d20; −3.28% .. −0.83%)**: with one thread the stripe
  mutex is uncontended and cheap, while every lockless probe computes key checks.
- **Threads 2/4/8:** the on/off time-to-depth ratios (1.038, 0.980, 0.937) are inside one standard deviation of
  the runs (sd 1.6-4.1 s on 31-49 s), so no time-to-depth difference is shown either way. NPS on/off is 0.990,
  1.014, 1.013.
- **Earlier version** (`60b0375`, run 40471171993, a faster runner: T1 NPS 1.79M): on/off NPS 0.959 / 0.876 /
  0.955 / 1.012 at T1/T2/T4/T8. The `c06eef2` probe (key checks only where needed, one multiply) removed most of
  that cost (`logs/ci/run_40471171993_60b0375/`).
- Not done: scaling on a machine with at least 8 idle cores (the PC is busy with gates; local runs are limited
  to 2 threads).

## Default build: hot code and speed
- **Codegen vs O3 with pins** (`logs/codegen_vs_o3pins.log`; the `c06eef2` exe gives a byte-identical table to
  `df4d437`, re-checked 2026-10-27):
  - alpha-beta, qsearch, MovePicker::next, static_evaluate, the history and correction functions, NNUE and
    board functions: identical at the same address mod 64;
  - `TranspositionTable::probe` 200 → 217 and `store` 129 → 156 instructions: the dispatch, and GCC's register
    allocation around it. `store` builds two more saved registers and loads three more stack arguments before
    the test. Its common path is otherwise unchanged;
  - the per-iteration driver differs in 8 lines.
- **Codegen vs the lock** (`logs/codegen_vs_lock.log`, also unchanged on `c06eef2`): the same, plus the O3 pins
  (alpha-beta, qsearch, probe and store start at 0 mod 64).
- **NPS of the default build vs O3 with pins** (quiet runner, `nps_ab.py`, 10 runs, d16/d20, run 40474683529,
  `nps_ab_o3pins_vs_ltt_off.log`): **d16 +0.29% (95% CI −0.85% .. +1.44%), d20 −0.56% (−1.14% .. +0.01%)**, both
  intervals include 0. (On `60b0375` it was −1.24% and −2.31%, also with intervals including 0.)

## Self-play
500 games at Threads 4, 1+0.01, Hash 16, engine A with LocklessTT on against B with it off (fastchess, CI run
40474683529): **500 games, 67,968 plies, 0 illegal moves, 0 crashes, 0 stalls/missing bestmove, 0 time forfeits,
0 unfinished; PGN LEGALITY: PASS** (`selfplay_pgn_legality.log`, `selfplay_games.pgn.xz`,
`selfplay_fastchess_stdout.log`). The score is not a strength result (1+0.01 on a shared runner) and is not
claimed.

## Proposed gate (G-B5; SMP-only)
- **Candidate:** the opus-O1-LTT exe (PC lock recipe) with `option.LocklessTT=true`. **Opponent:** the same
  exe with the option off, so only the TT access differs.
- **Settings:** both at Threads 4 (or the gate machine's SMP setting), Hash 64, OwnBook false; SPRT [0,10] at
  10+0.1 with the test plan's G-B5 srand (QA).
- **Counting:** it does not count toward the single-thread gate. At Threads=1 the option does not change the
  search (identical bench) but costs about 2% NPS, so it should stay off for single-thread play.

No Elo claim.

## Files
- **Engine:** `src/search/tt_lockless.inc` (new), `src/search/tt.inc` (dispatch), `include/forge/tt.hpp`,
  `include/forge/search_options.hpp`, `src/search/options.inc`, `src/search/searcher.inc`, `src/search.cpp`,
  `src/uci.cpp`.
- **Tests:** `tests/tt_coherence_tests.cpp` (extended), `tests/tt_stress_tests.cpp` (new; CTest
  `forge_tt_stress_lockless`, `forge_tt_stress_locked`), `CMakeLists.txt`.
- **CI:** `.github/workflows/opus-o1-ltt.yml`.
- **`opus_round1/O1-LTT`:** `REPORT.md`, `IDEA_SOURCE.md`, `patch.diff`, `tsan_extra.sh`, `scaling_summary.py`,
  `nps_ab_options.py`, `logs/` (local logs; `logs/ci/run_40474683529_c06eef2a/`,
  `logs/ci/opus_ci_40474683617_c06eef2a/` and the earlier `logs/ci/run_40471171993_60b0375/`), `SHA256SUMS`.
- **`opus_round1/O1/uci_stress.py`:** `--toggle-options` now also toggles LocklessTT.
- Machine exclusive: no (the PC ran gates, self-play and NNUE training during the local runs).

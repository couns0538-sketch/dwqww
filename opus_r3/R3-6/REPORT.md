# R3-6 Lazy SMP scaling: Threads 1/2/3 time-to-depth, stack OFF vs ON, one scaling bug fixed behind an option — PARTIAL (1 of 3 repetitions)

**Branch.** `opus-r3-smp` = base `2432670b` → stack head `2047348a` (fast-forward) → **final stack head `330237f3`** (merge `f6d49dab`), plus the [R3-6] commits:
- `c44c3dc8`: UCI `SmpHelpersPastDepth` (default false), `forge_smp_tests` checks, job tools.
- `5163797d`: tools (trace-summary ratios, `make_summaries.sh`, README). This is the final engine commit.
- `79ea4437`: evidence `[skip ci]`.

**Machine exclusive: no.** The PC ran a fastchess gate (16 engine processes at BelowNormal), NNUE training and other idle-priority jobs throughout. The rest of the PC was 87-95 % busy during the runs (recorded per run).
- Every engine ran at IDLE priority. It got 0.8 CPU at Threads 1, 1.4-1.5 at Threads 2 and 2.0-2.2 at Threads 3.
- All wall-clock numbers are advisory. The node and CPU columns are more robust.
- No Elo claims.

## Summary
- **Setup.** 30 positions (10 opening, 12 middlegame, 8 endgame), each at a fixed depth of 20-32 where Threads=1 takes 2.2-7.6 s. Threads 1/2/3, Hash 64, a fresh process plus `ucinewgame` per run.
- **Five configs**, all on the final head:
  - `off` (all defaults)
  - `on` (SmpExactNodes + SmpBestThread + LocklessTT)
  - `on2` (`on` + CorrHistPlus=7, CorrMargins=1, CorrExt=1, CuckooRep, HistRework=2, MaterialKeyTable)
  - `offP` and `onP` (`off` / `on` + the new SmpHelpersPastDepth)
- **Volume.** 464 runs: one full repetition of all 13 (config, threads) combinations × 30 positions, plus 74 runs of a second.
- **Stack OFF.** Suite time-to-depth speedup is 0.95× at T2 and 1.14× at T3. Per-position geometric means are 1.07 and 1.24.
  - Node inflation is 1.71× and 2.03×, NPS scaling 1.86× and 2.43×.
  - Helpers mostly duplicate the main thread (same depth sequence, in lockstep). At T2 the main thread still needs 0.80× of its Threads=1 nodes to complete the depth.
- **Stack ON.** No significant difference from OFF:
  - Paired wall ratio on/off is 0.84 [0.67..1.04] at T2 and 0.97 [0.80..1.15] at T3.
  - At T1 the searches are identical: nodes equal, wall 1.00.
- **ON2 (search options).** These options do not break scaling; they scale better at fixed depth.
  - Speedup is 1.47× at T2 and 1.94× at T3, with node inflation 1.34× and 1.61×.
  - At T1 the same depths take 1.68× the time of OFF, with 1.52× the nodes.
- **Bug found.** In a `go depth N` search every helper returned once it had completed iteration N. Its core then sat idle until the main thread completed N.
  - Trace build: helpers are idle for 6.6 % (T2) and 9.2 % (T3) of the search.
  - 53 % and 43 % of helpers return by themselves.
- **Fix.** UCI `SmpHelpersPastDepth` (check, default false). Helpers keep deepening until the main thread stops them and still report their depth-N result.
  - Idle time and self-returning helpers both drop to 0 %.
  - The time-to-depth gain is not measurable on this PC: offP/off wall is 0.99 [0.80..1.21] at T2 and 1.03 [0.86..1.20] at T3.
  - NPS rises 6.5 % (T2) and 10.6 % (T3) because the helpers stay busy.
  - With the option off, bench and perft are identical (ALL OK). With it on, bench at Threads=1 equals the pins and the hot code is instruction-identical.
- **No other scaling bug** (see "Other things checked").
- **CI green** on the final engine commit: 40575802130.

## Acceptance
| # | line | result | evidence |
|---|---|---|---|
| 1 | 30 positions, fixed depth (T1 about 2-10 s), Threads 1/2/3, fixed Hash, fresh process + `ucinewgame`, ≥3 repetitions, medians, nice 19, load recorded | **PARTIAL.** 30 positions, depths 20-32, T1 2.2-7.6 s, Hash 64, one fresh IDLE-priority process per run, load per run. Only 464 runs: 1 full repetition plus 74 runs of a second (deadline; about 8 s per run on the loaded PC). Medians are over 1-2 runs. A preliminary partial pass on 2047348a (94 runs) is kept but not pooled. | `positions30.tsv`, `logs/calibration.{log,jsonl}`, `logs/ttd_main_final_330237f3.jsonl.xz`, `logs/ttd_per_position.tsv`, `logs/ttd_main_prelim_2047348a.jsonl.xz` |
| 2 | stack OFF vs ON vs ON2 (search options) | **DONE** (tables below) | `logs/ttd_summary.md` |
| 3 | speedups, NPS scaling, node inflation; scaling-bug search (idle or duplicating helpers, main waiting, stop/join latency, ignored helper results, TT thrashing, wrong node counts, T3 slower than T2) | **DONE.** Advisory wall numbers, plus a per-worker trace build (150 runs). | `logs/ttd_summary.md`, `logs/trace_summary.md`, `logs/trace_per_run.tsv`, `logs/ttd_trace_final_f6d49dab.jsonl.xz` |
| 4 | fix behind a new option (default OFF); OFF bench/perft identical; T1 identical with the option ON; CTest test; before/after; full local CMake + ctest; CI green | **DONE.** `SmpHelpersPastDepth`. OFF: ALL OK. ON: bench equals the pins; 71/71 Threads=1 runs have the calibration nodes. `forge_smp_tests` +109 lines; planted bugs M1 5/5, M2 5/5, M3 4/5. Before/after: offP/onP. Local CMake 108/108 targets; ctest 43/45 (the known `forge_tests` lines plus O1's pre-existing load flake). CI 40573133772 and **40575802130** success. | see "Fix verification" |
| 5 | report: per (config, threads) median time-to-depth, speedup, nodes, NPS with spread; per-position TSV; findings; fix | **DONE** (this report) | `logs/ttd_per_position.tsv` |
| — | final comparison on the newest head | **DONE.** Every number below comes from the 330237f3 head exe (`399577cc…`) and the fix exe (`a89631f9…`, merge `f6d49dab`). | `logs/identity_head_330237f3.log`, `logs/identity_fix_f6d49dab_off.log` |

## Method
- **Positions** (`calibrate_positions.py`, `positions30.tsv`):
  - Openings: bench.0/4/7 and 7 forge-10000 openings from `opus_round1/O3/positions50.fen`.
  - Middlegames: bench.1/2 and 10 ECM positions. bench.5 was screened out by its mate score; the spare ECM.1009 replaced it.
  - Endgames: bench.3/6 and 6 low-material WAC/ECM positions (≤4 non-pawn pieces, no queens).
  - Depth per position: the deepest depth whose Threads=1 search takes ≤5.5 s in a calibration run. A Threads=1 fixed-depth search is deterministic, and all 71 Threads=1 runs on the final head have exactly the calibration nodes.
- **Runs** (`smp_ttd.py`, `run_matrix.sh`):
  - One fresh engine process per run at IDLE priority: `uci`, Hash 64, OwnBook false, the config's options, `ucinewgame`, `position fen`, `go depth D`, `quit`.
  - Time-to-depth = wall time from sending `go` to reading `bestmove`.
  - CPU = the engine's user+kernel time over the same interval (GetProcessTimes).
  - Nodes = the main thread's `info depth D` line.
  - Load = the rest of the PC's busy fraction (GetSystemTimes minus the engine's CPU).
  - The 13 (config, threads) runs of each (repetition, position) are shuffled, so load drift hits every config alike.
- **Executables** (PC lock recipe; FMA 0; no warnings):
  - Head 330237f3: sha256 `399577cc…`, ALL OK.
  - Fix f6d49dab: sha256 `a89631f9…`, ALL OK with the option off.
  - offP/onP have no T1 runs: the option is inert there, so their speedup reference is off/on at T1.
- **Diagnostic build** (`make_trace_src.py` writes a scratch copy built with `-DFORGE_SMP_TRACE=1`; the branch's sources contain no trace code; exe `6d90de81…`):
  - After each search it prints, per worker: completed iterations (time and nodes), exit time, thread CPU time, TT probes/hits/cutoffs. It also prints the stop/join latency.
  - Run set: one run per position for `off` at Threads 1/2/3 and `offP` at Threads 2/3 (150 runs).
- **Paired comparisons:** geometric mean over positions of the per-position median ratio B/A, with a 95 % bootstrap interval over positions (`summarize.py --pair`).

## Results (final head 330237f3; all 30 positions)
In the speedup and node columns, the values in brackets are the 25th..75th percentiles over positions. "Load-free speedup" = Threads / (CPU Tn / CPU T1): the speedup if every thread had run uninterrupted. It overstates the speedup when helpers sit idle. "CPUs got" = CPU / wall.

| config | T | time-to-depth sum (s) | speedup (sum) | per-position speedup gmean [p25..p75] | nodes Tn/T1 gmean [p25..p75] | NPS | NPS scaling | CPU Tn/T1 | load-free speedup | CPUs got | hashfull ‰ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 1 | 127.6 | 1.00 | — | 1.00 | 1.303 M | 1.00 | 1.00 | 1.00 | 0.81 | 558 |
| off | 2 | 133.6 | 0.95 | 1.07 [0.75..1.48] | 1.71 [1.21..2.36] | 2.428 M | 1.86 | 1.68 | 1.19 | 1.43 | 787 |
| off | 3 | 112.1 | 1.14 | 1.24 [0.80..1.77] | 2.03 [1.41..2.90] | 3.165 M | 2.43 | 1.99 | 1.51 | 2.04 | 824 |
| on | 1 | 127.9 | 1.00 | — | 1.00 | 1.300 M | 1.00 | 1.00 | 1.00 | 0.80 | 558 |
| on | 2 | 113.8 | 1.12 | 1.28 [0.85..1.59] | 1.51 [1.21..2.27] | 2.521 M | 1.94 | 1.46 | 1.37 | 1.48 | 699 |
| on | 3 | 116.3 | 1.10 | 1.28 [0.90..2.10] | 2.08 [1.41..2.78] | 3.537 M | 2.72 | 2.02 | 1.49 | 2.13 | 821 |
| on2 | 1 | 278.2 | 1.00 | — | 1.00 | 1.160 M | 1.00 | 1.00 | 1.00 | 0.79 | 664 |
| on2 | 2 | 188.8 | 1.47 | 1.44 [1.11..2.02] | 1.34 [0.97..1.81] | 2.236 M | 1.93 | 1.29 | 1.55 | 1.50 | 858 |
| on2 | 3 | 143.7 | 1.94 | 1.69 [1.01..2.74] | 1.61 [1.11..2.70] | 3.249 M | 2.80 | 1.53 | 1.96 | 2.10 | 912 |
| offP | 2 | 131.7 | 0.97 | 1.08 [0.75..1.45] | 1.83 [1.35..2.63] | 2.586 M | 1.98 | 1.78 | 1.12 | 1.54 | 853 |
| offP | 3 | 120.1 | 1.06 | 1.21 [0.87..1.91] | 2.18 [1.38..3.04] | 3.502 M | 2.69 | 2.13 | 1.41 | 2.03 | 902 |
| onP | 2 | 118.5 | 1.08 | 1.21 [0.82..1.55] | 1.64 [1.22..2.26] | 2.536 M | 1.95 | 1.57 | 1.27 | 1.51 | 774 |
| onP | 3 | 107.5 | 1.19 | 1.40 [0.98..1.61] | 2.06 [1.76..3.11] | 3.604 M | 2.77 | 1.96 | 1.53 | 2.19 | 892 |

**Paired comparisons.** Ratio < 1 means B needs less. Brackets are 95 % bootstrap intervals over positions.

| B vs A | T | wall B/A | CPU B/A | nodes B/A | positions B faster |
|---|---|---|---|---|---|
| on vs off | 1 | 0.999 [0.981..1.015] | 0.994 | 1.000 (identical) | 11/30 |
| on vs off | 2 | 0.837 [0.665..1.041] | 0.861 [0.690..1.066] | 0.886 [0.719..1.090] | 17/30 |
| on vs off | 3 | 0.973 [0.803..1.153] | 1.010 [0.841..1.196] | 1.028 [0.849..1.222] | 13/30 |
| on2 vs off | 1 | 1.682 [1.349..2.134] | 1.674 | 1.517 [1.218..1.932] | 6/30 |
| on2 vs off | 2 | 1.252 [0.984..1.650] | 1.281 | 1.192 | 11/30 |
| on2 vs off | 3 | 1.235 [0.985..1.537] | 1.292 | 1.206 | 12/30 |
| offP vs off | 2 | 0.989 [0.798..1.210] | 1.058 [0.853..1.296] | 1.073 [0.873..1.311] | 14/30 |
| offP vs off | 3 | 1.025 [0.862..1.198] | 1.073 [0.884..1.276] | 1.075 [0.892..1.274] | 15/30 |
| onP vs on | 2 | 1.060 [0.883..1.287] | 1.080 | 1.082 | 15/30 |
| onP vs on | 3 | 0.910 [0.691..1.178] | 0.969 | 0.989 | 18/30 |
| onP vs off | 2 | 0.888 [0.733..1.072] | 0.930 | 0.959 | 18/30 |
| onP vs off | 3 | 0.885 [0.727..1.055] | 0.979 | 1.016 | 16/30 |

**By class, off** (per-position speedup gmean, T2 / T3; node inflation in parentheses):

| class | T2 | T3 |
|---|---|---|
| opening (10) | 0.92 (1.96) | 0.92 (2.58) |
| middlegame (12) | 1.20 (1.57) | 1.52 (1.76) |
| endgame (8) | 1.10 (1.64) | 1.34 (1.86) |

Openings scale worst. Full per-class tables, including the other configs, are in `logs/ttd_summary.md`.

## Diagnostics (trace build of f6d49dab; one run per position and config)

| config | T | main returns (s) | join latency median / max | helper idle | helpers that returned by themselves | helper completions ahead of main | lead (ply) | main share of nodes | TT hit / cutoff | main nodes vs T1 | main CPU vs T1 | all nodes vs T1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 1 | 4.55 | — | — | — | — | — | 100 % | 33.0 % / 13.3 % | 1.000 | 1.000 | 1.000 |
| off | 2 | 4.54 | 126 µs / 7.9 ms | **6.6 %** | **53.3 %** | 59.3 % | 0.64 | 51.7 % | 35.4 % / 15.2 % | 0.803 | 0.782 | 1.557 |
| off | 3 | 3.70 | 574 µs / 2.8 ms | **9.2 %** | **43.3 %** | 50.9 % | 0.54 | 37.8 % | 36.1 % / 15.6 % | 0.679 | 0.661 | 1.823 |
| offP | 2 | 4.49 | 1.06 ms / 10.3 ms | **0.0 %** | **0.0 %** | 50.1 % | 0.47 | 50.3 % | 35.8 % / 15.5 % | 0.815 | 0.792 | 1.621 |
| offP | 3 | 3.63 | 1.19 ms / 30.1 ms | **0.0 %** | **0.0 %** | 46.9 % | 0.46 | 34.9 % | 36.5 % / 16.0 % | 0.630 | 0.610 | 1.808 |

Column notes:
- "Helper idle" = helper wall time spent finished-and-waiting.
- "Ahead" = helper iterations (depth ≥8) completed before the main thread completed the same depth.
- "Main nodes / CPU vs T1" = the main thread's own work to complete depth D, relative to the position's Threads=1 run. This is the critical path and the load-robust measure of how much the helpers help.
- The info-line node count equals the exact per-worker sum (≥99.95 %) in every run.
- At Threads 1 the engine thread got 0.77 CPU (3.49 s CPU over 4.55 s).

## The bug: helpers idle at the `go depth` limit
- **Cause** (`src/search/iterative.inc`, AL1 code): every worker, helpers included, runs `for (depth = 1; depth <= max_depth; ++depth)` with `max_depth` = the `go depth` limit.
  - A helper that completes depth N first returns, and its thread ends.
  - Until the main thread completes N too, that core does nothing for the search.
- **Evidence** (trace, final head, 30 positions):
  - 53 % (T2) and 43 % (T3) of helpers returned by themselves.
  - That is 6.6 % and 9.2 % of all helper time spent idle.
  - In a smoke run on kiwipete at depth 13 (T2), the helper idled for 40 % of the search (`logs/smoke_trace_2047348a_fix_v1.jsonl.xz`).
- **Scope:** clocked, infinite and node searches already let helpers run to depth 64, so only `go depth` searches are affected: analysis, fixed-depth tests, time-to-depth measurement. `go mate` is left unchanged on purpose.
- **Fix:** UCI `SmpHelpersPastDepth` (check, default false; acts only with Threads > 1 and a `go depth` limit).
  - A helper keeps deepening (up to 64) until the main thread raises the stop flag, as Stockfish's helpers do (only its main thread checks `Limits.depth`).
  - Iterations past N only fill the shared table.
  - The helper still returns exactly its iteration-N result, so SmpBestThread chooses among the same depths. An aborted iteration past N does not replace the move either.
  - Code: `last_depth` loop bound, a `depth <= max_depth` guard in the abort block, and `if (depth > max_depth) continue;`.
- **Effect:**
  - Helper idle time and self-returning helpers drop to 0 % (trace).
  - NPS rises 6.5 % at T2 and 10.6 % at T3 (paired, all 30 positions).
  - The main thread's work to depth is unchanged within noise: 0.80 → 0.82 (T2) and 0.68 → 0.63 (T3).
  - Wall time-to-depth shows no measurable change on this loaded PC: offP/off 0.99 [0.80..1.21] at T2 and 1.03 [0.86..1.20] at T3.
  - A gain, if any, is below this PC's noise floor. It needs a quiet machine with ≥3 free cores.

## Other things checked (no bug)
- **Helpers duplicating the main thread.** Yes, by design: there is no depth skipping.
  - Helpers run the same depth sequence in lockstep (lead 0.5-0.6 ply; about half their completions come before the main thread's).
  - At T2 the main thread still needs 0.80× of its single-thread nodes to complete the depth, so the second thread shortens the critical path by only about 20 %. That matches the measured T2 speedups of about 1.0-1.3.
  - Not changed here: depth diversification (Stockfish 7-10 skip blocks) would be a search-design option and needs an SMP gate. Proposed as a follow-up.
- **Main thread waiting on helpers / stop-join latency:**
  - Median 0.1-1.2 ms; maximum 30 ms, which matches a helper preempted on the loaded PC (helpers check the stop flag every 1024 nodes).
  - Helper start latency was 3-7 ms under load (smoke trace).
- **Helper results ignored:** by design without SmpBestThread. With it, helper results are used (O1), and `SmpHelpersPastDepth` keeps them at the requested depth (tested).
- **Wrong reported nodes:** the final info line equals the exact per-worker total (≥99.95 %). O1's stale-counter bug only affects reused processes and is handled by SmpExactNodes.
- **3 threads slower than 2:** no. The suite time-to-depth is lower at T3 than at T2 for off (112 s vs 134 s), on2 and onP.
- **TT pressure:** hashfull rises from 558 ‰ (T1) to 790-910 ‰ at T2/T3 with Hash 64. TT hit and cutoff rates rise slightly with threads (33 → 36 %, 13 → 16 %), so there is no sign of thrashing. A larger Hash was not tested.
- **Locked TT vs LocklessTT on Windows:**
  - On this g++ (posix thread model, winpthreads 14) each stripe `std::mutex` is a small heap-allocated object.
  - Per-thread CPU efficiency (nodes per CPU second relative to T1) is the same for off and on: 1.02 vs 1.04 at T2, 1.02 vs 1.03 at T3. The stripe locks cost nothing measurable here.
- **Search options (on2):** they don't break scaling. on2 scales better at fixed depth (1.47× / 1.94×, node inflation 1.34× / 1.61×), but its single-thread depth-D search is 1.68× slower.

## Fix verification
- **Option off is identical to AL1** (`logs/identity_head_330237f3.log`, `logs/identity_fix_f6d49dab_off.log`, earlier `logs/identity_fix_v1_off.log`):
  - Bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354; perft5 4865609; kiwipete 193690690; ALL OK.
  - FMA 0 and no warnings for both the head and the fix exe.
- **Option on, Threads=1 is identical:**
  - Bench with `SmpHelpersPastDepth=true` equals the five pins (`logs/bench_fix_f6d49dab_option_on.log`).
  - `forge_smp_tests` "options are inert at Threads=1" now includes the new option.
- **Codegen** (`logs/codegen_head330237f3_vs_fix_f6d49dab.log`):
  - alpha-beta, qsearch, MovePicker::next, static_evaluate, TT probe/store, should_stop and the NNUE and board functions are instruction-identical at the same address mod 64.
  - Only the per-iteration driver `Worker::search(Board, …)` differs (2157 → 2165 instructions).
- **CTest** (`tests/smp_tests.cpp`, +109 lines):
  - A helper Worker with no main thread gives deterministic checks: it searches on until the stop flag, deepens past the limit, and reports exactly the result of the limit iteration (equal to the option-off run).
  - Those checks run on 3 positions at depth 4, plus bench.2 at depth 2 and the start position at depth 4, each stopped at 5 node counts.
  - Threads 3 + SmpBestThread reports exactly the requested depth.
- **Planted bugs** (`logs/mutation_check_v2.log`, 5 runs each):

  | mutant | result |
  |---|---|
  | control | 0/5 fail |
  | M1 helpers stop at the limit | 5/5 killed |
  | M2 result not capped | 5/5 killed |
  | M3 aborted iteration past the limit replaces the move | killed 4/5; the effect depends on where the stop lands |

- **Local CMake + full ctest** on the merged tree: 108/108 targets built.
  - ctest 43/45 (`logs/ctest_final.log`). `forge_tests` shows the 4 known lines.
  - `forge_smp_tests` failed one round of O1's "SmpExactNodes: overshoot bounded by the publish cadence" check: 26,518 nodes against a bound of 26,300.
  - That check is load-sensitive: helpers keep searching while the main thread is preempted. It fails at the same rate without this change. Interleaved -O3 builds:
    - pure head 330237f3: 3/10 runs (4/100 rounds);
    - branch: 5/10 runs (5/100 rounds);
    - never any other line (`logs/smp_tests_o3_head_vs_branch_x10.log`, `logs/cmake_smp_tests_x5.log`, `logs/ctest_full.log`).
- **CI** (`logs/ci/`):
  - 40573133772 on c44c3dc8: success.
  - **40575802130 on 5163797d: success.** Release identity ALL OK; known-failure check PASS in release, ASan and TSan; TSan 0 reports. `forge_smp_tests` 3.3 s / 22.0 s / 258.7 s (TSan +60-90 s over O1's 196 s; timeout 600 s).

## UNVERIFIED / left
- **Repetitions.** Only 1 full repetition (+74 runs of a second) instead of ≥3; the 23:45 deadline stopped the run. Per-position medians are over 1-2 runs, and every wall-clock comparison here has 95 % intervals of about ±20 %.
- **Fix benefit.** The fix's time-to-depth gain is unproven (below this PC's noise floor). It needs a quiet machine with ≥3 free cores. No gate was run, and none is needed for clocked play: the option changes only `go depth` searches at Threads > 1.
- **Trace coverage.** On the final head the trace covers `off` and `offP` only. A trace of on/onP/on2 was not run there; a 2047348a smoke trace showed the same idle pattern.
- **Not tested:** a larger Hash (TT pressure), Threads > 3 (PC rule), and depth diversification (a proposed follow-up behind an option, with an SMP gate).
- **Not fixed (out of scope):** O1's overshoot check stays load-sensitive on the PC.

## Files (`opus_r3/R3-6/`; index in `FILES.txt`, `SHA256SUMS`)
- **Docs and data:** `README.md`, `IDEA_SOURCE.md`, `positions30.tsv`.
- **Tools:**
  - `smp_ttd.py` (harness), `calibrate_positions.py`, `run_matrix.sh`
  - `make_trace_src.py` (trace build, scratch copy only)
  - `summarize.py`, `trace_summary.py`, `make_summaries.sh`
  - `sysload.py`, `mutation_check.py`
- **Logs** (`logs/`):
  - Identity, bench, build, codegen, mutation, CMake and ctest logs.
  - `ttd_summary.md`, `ttd_per_position.tsv`, `trace_summary.md`, `trace_per_run.tsv`.
  - Raw runs as `.jsonl.xz`, with `raw_sha256.txt`.
  - `ci/run_40573133772`, `ci/run_40575802130`.
- **Engine files on the branch:**
  - `include/forge/search_options.hpp`
  - `src/search/options.inc`
  - `src/search/iterative.inc`
  - `src/uci.cpp`
  - `tests/smp_tests.cpp`
- **Scratch:**
  - Raw runs: `F:\opus_scratch\r3\R3-6\final\`.
  - Builds: `F:\opus_scratch\build\r3_R3-6\` (head_330237f3.exe, fix_f6d49dab.exe, trace_f6d49dab.exe, cmake).

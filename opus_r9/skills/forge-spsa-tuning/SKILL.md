---
name: forge-spsa-tuning
description: SPSA tuning of Forge's search parameters on the PC (R9, branch opus-r9-spsa) - the R9Tune switch (74 tunables = the lock's 51 forge::tune constants + 23 former literals, default off, lock bench identical off AND on-at-defaults), how to add a parameter, the option check, the own SPSA tuner r9_spsa.py driving fastchess (Fishtest-style schedule in game pairs, load governor for the 70% CPU cap, append-only resumable state, history CSV), the report with a null-gradient noise level per parameter, the simulated tests, configs, the QA gate line. Use for any search-parameter tuning, SPSA run, R9Tune option, tuned .ini, or a gate of tuned values.
---

# Forge SPSA tuning (R9, 2026-10-29)

Rules first: [[forge-pc-rules]] (R9: <= 4 threads, BelowNormal, CPUs 0-3 (`run_pinned.py --mask 0x000F`), total PC CPU
< 70%, free RAM > 8 GB, push every 10 minutes, never touch gates / self-play / trainer). Engine checks: [[forge-engine-verify]].

## The engine side (opus-r9-spsa = lock d4f4312 + CI baseline 0d99f02 + R9 commits)
- The lock already keeps 51 search constants in `forge::tune` (`src/search.cpp` top, table `tune::parameters()` with
  min/max; `tune::refresh()` rebuilds the LMR table) and its `setoption` accepted them silently.
- R9 adds 23 former literals as parameters at their lock values (null move `NmpEvalDepthMargin/NmpEvalBase/
  NullMoveEvalMax/NullMoveVerifyDepth`, `ProbcutImproving/ProbcutReduction`, `SingularTtDepth/SingularDoubleMargin/
  SingularDoubleLimit`, LMR adjustments in 1/1024 ply `LmrTtPv/LmrNotImproving/LmrCutNode/LmrTtCapture/LmrGivesCheck/
  LmrInCheck/LmrCutoffCount` (summed, then `(r1024 + 512) >> 10` = nearest ply; exact for multiples of 1024),
  `HistoryBonusOffset/HistoryMalusPercent/HistoryDepthBonusMargin`, `AspirationMinDepth/AspirationGrowPercent (>= 10)/
  AspirationGrowAdd (>= 1)`, `QuietCheckBonus`).
- `R9Tune` (check, default false): `tune::r9_set_enabled(on)` copies the R9 option values (on) or the lock defaults
  captured at static init (off) into the live variables; `tune::r9_set(name, v)` stores (clamped) and applies only
  while on. `uci` ALWAYS advertises R9Tune + all 74 tunables with the lock defaults (the gate runner checks that every
  option it sets is advertised: ENGINE_OPTIONS_CHECK "options advertised").
- Adding a parameter: an `int` in `namespace tune` at the exact old literal, a table row, an `extern` in
  `include/forge/search.hpp`, replace the literal with the same arithmetic (watch integer division order, bool*int,
  truncation vs floor), then: identity OFF and ON-at-defaults must both print ALL OK, and the option check must show it
  changes bench when moved (a planted check that it is wired).
- Checks (all logged in `opus_r9/logs/`): `uci_check.py <exe> --full` (lock pins 312866/862329/3024920/12389307/34048354,
  perft5 4865609, kiwipete 193690690), `opus_r9/tools/identity_opts.py <exe> --full --opt R9Tune=true`,
  `opus_r9/tools/r9_option_check.py <exe> --depth 11 [--probe Name=value ...]` (advertised, gated off, each one moves
  bench when on, off restores), CMake all targets + CTest via `opus_r9/tools/run_ctest_r9.sh` under
  `bash_run.py` (KNOWN-FAILURE CHECK: PASS = only the 4 forge_tests lines), then CI (opus-ci release/asan/tsan).
- Build: `python -I -B run_pinned.py --mask 0x000F -- opus_r9/tools/build_r9.py <tree> <out.exe>` (box recipe, 15 s).
  Build c = `F:\opus_scratch\r9\build\forge_r9_c.exe` sha256 `cad98f31...`.

## The tuner (`opus_r9/tuner/`, own code; ideas: Fishtest / OpenBench / Weather Factory, see opus_r9/IDEA_SOURCE.md)
- `r9_spsa.py run <config.json> <run_dir> [--resume] [--max-pairs N] [--max-hours H] [--until HH:MM]` under
  `run_pinned.py --mask 0x000F` (fastchess + engines inherit CPUs 0-3 and BelowNormal). `status <run_dir>`.
- Schedule in game pairs: `c_i = c_end N^0.101`, `a_i = r_end c_end^2 (A+N)^0.602`, `A = 0.1 N`; batch of
  `pairs_per_batch` pairs per +-delta; update `theta += a_k/c_k * (W-L of plus) * delta`; values rounded to ints.
- Governor (user rule 2026-10-29 23:3x, configs `cap_percent 80, pause_percent 90, pause_after 60`): samples system
  CPU % for 2-3 s between batches (no own games running); a batch starts only while that load is <= 80% and free RAM
  >= 8 GB, with as many games as keep the expected total <= 90% (load 62% -> 4, 68% -> 3, 72-75% -> 2, 78-80% -> 1);
  `BatchWatch` samples CPU/RAM every 10 s during the batch and, if the total stayed > 90% for 60 s or RAM < 8 GB, the
  tuner pauses after the batch (never stops a game, never kills). The earlier 70% cap (floor((cap - load) * 16 / 100))
  never ran while the conc-4 Threads-2 gate + self-play + trainer kept the PC at 72-82%; it started only when the owner
  paused self-play (62%). A resumed run may change only its `governor` section (`governor_changes.jsonl`).
- Stop: create `<run_dir>/STOP` (TaskStop does not stop processes on this PC). Resume: same config (checked) + `--resume`.
- Evidence: `iterations.jsonl` (append-only, fsync per batch), `history.csv`, `tuner.log`, `games/b<batch>_a<n>.{pgn,out,
  config.json}` (fastchess `-config outname=` so nothing is overwritten).
- fastchess 1.8.2 line: `-engine name=plus cmd=EXE option.R9Tune=true option.X=v ... -engine name=minus ... -each
  tc=8+0.08 timemargin=1000 proto=uci option.Threads=1 option.Hash=16 option.OwnBook=false -openings file=8moves_v3.pgn
  format=pgn order=sequential start=<k%34700+1> -games 2 -repeat -rounds P -concurrency C -recover -pgnout ...`.
- `test_r9_spsa_sim.py <scratch>`: no games, simulated Elo with known optimum: both directions move (z ~ +-8.5), an
  at-optimum parameter stays within 3 sigma, killed+resumed == uninterrupted. Run it after any tuner change.

## Reading a run (`r9_spsa_report.py <run_dir> --out <dir> --exe <path>`)
- Noise sigma per parameter = sqrt(sum_b (a_k/c_k)^2 * games_b * v), v = (W+L)/G - ((W-L)/G)^2: the spread of the same
  run under NO true gradient. |z| >= 2 = "likely real" (1 in 20 by chance per parameter); halves "same way" helps.
- Budget reality: 8+0.08 at conc 4 = ~280 pairs/h. Fishtest tunes use 20k-200k pairs; with ~1k pairs only clearly
  mis-set parameters move beyond noise. r_end 0.002 (Fishtest/OpenBench) moves nothing in 1k pairs; R9 used 0.012
  (noise ~0.5 c_end) for STC and 0.06 for the 200-pair sanity run. Many random +-1 c_end moves of near-optimal
  parameters cost Elo: prefer gating only the likely-real subset when the run was short.
- QA gate line: tuned options vs the same exe at defaults, SPRT [0,10] nElo, cap 3000 (copy the queue's tc/threads/book).

## R9 outcome (2026-10-30, use it to size the next run)
- stc1: 16 parameters from the lock values, 8+0.08, 832 pairs = 1,664 games, played 00:53-04:46 (+203 -207 =1254, 75.4% draws):
  **0 of 16 beyond 2 sigma** (largest |z| 1.49). HistoryMalusPercent was beyond 2 sigma at 01:55 and ended z +1.22:
  never act on mid-run z. Sanity runs (one parameter set far off) did move back toward the lock value (z +1.27, +1.48).
- So at this budget only far-off parameters show; the lock's values look near a local optimum at 8+0.08. Next time:
  3,000+ pairs (about 11 h at conc 4 when the PC is free), or 4-6 parameters with larger c, and plan for the gate and
  other jobs taking CPU (the governor dropped to conc 2-3 for 36 of 65 batches while R10 ran beside it).
- `opus_r9/tools/write_report.py --final` writes the verdict itself (empty likely-real set = no second gate).

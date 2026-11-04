---
name: forge-o30-spsa
description: SPSA tuning of Forge search constants on the lock (Opus 30-h job, branch opus-30h-20261103) - the 41 constants the lock already advertises under kit -Expose, the 22 more exposed by opus_30h/b/o30_expose.py (defaults = the lock's literals, pins identical, all live), the tuner tune_spsa.py + tune_spsa.ps1 (params CSV name,start,min,max,c,a; fastchess pairs; per-iteration CSV; resume after crash / reboot; thread cap, CPU mask, gate-overlap check, busy threshold; deadline; stop event), selftest_10min.ps1, the run config, and how to package a tuned set for one SPRT. Use for any search-parameter tuning, a new tunable option, a resumed / stopped SPSA run, or a tuned-set gate line.
---

# SPSA for Forge (Opus 30-h job)

Files: `D:\o30\wt\opus_30h\b\` (branch copy `opus_30h/b/`), runs under `D:\o30\spsa\`. Rules: forge-pc-rules latest
round; own processes Idle on CPUs 0-1 (<= 8 threads, never on cores of a running gate), no STOP files, never kill.

## Options
- The lock exe FD3A5190 (kit -Expose) advertises 41 search + 10 time-management constants at its own values: with only
  those, the lock exe itself is the tuning engine and the tuned set is just option values.
- `python -I -B o30_expose.py <fresh lock copy>` exposes 22 more (NmpEvalDepthMargin, NmpEvalBase, NullMoveEvalMax,
  NullMoveVerifyDepth, ProbcutImproving, ProbcutReduction, SingularTtDepth, SingularDoubleMargin, SingularDoubleLimit,
  LmrTtPv, LmrNotImproving, LmrCutNode, LmrTtCapture, LmrGivesCheck, LmrInCheck, LmrCutoffCount, HistoryMalusPercent,
  HistoryDepthBonusMargin, AspirationMinDepth, AspirationGrowPercent, AspirationGrowAdd, QuietCheckBonus) at the
  lock's literals: pin_check -Full PASS, 22 / 22 live. LMR terms are in 1/1024 ply: a lone half-ply change is dead
  (rounds away) while the other terms are whole plies - test liveness with whole-ply steps.
- Kit exe of that patch: `kit_build_o30.sh <repo> <tag>` (kit v2.3; the OFF profile covers the same code).

## Tuner
- `tune_spsa.ps1 -Config <json> -RunDir <dir> [-Until 'YYYY-MM-DD HH:MM'] [-Threads 2] [-Cpus '0,1']` starts or
  resumes (the run's own config.json / params.csv copies; only threads / cpus may change). `-Stop` ends after the
  playing batch (named event the tuner holds), `-Status` prints theta.
- Config keys: engine, fastchess, book (UHO epd), book_openings, tc, hash, pairs_planned, pairs_per_batch, alpha,
  gamma, A_ratio, seed, threads, cpus, params_csv, fixed_options, max_busy_percent (default 80: the npt trainer keeps
  CPUs 0-3 at ~50-60 %, a 50 % threshold starved the tuner).
- Schedule (R9's): c_i = c_end * N^gamma, a_i = r_end * c_end^2 * (A + N)^alpha; per batch c_k, a_k, delta +-1 seeded
  by k; theta += a_k / c_k * (W - L) * delta. Evidence: iterations.jsonl (fsynced), history.csv, games/*.pgn / .out.
- Self-test: `selftest_10min.ps1 -Out <new dir> [-Cpus 1 -Threads 1]` (3 sessions: deadline, stop event, max pairs;
  checks record = CSV rows, k / batch continuity, ranges, normal terminations) -> SELFTEST PASS.
- The busy test counts every process on the CPUs, own trainers included: run the tuner on CPUs no own trainer uses.

## Packaging a tuned set
Final theta rounded to integers -> TUNED_OPTIONS.txt (Name=Value lines) + the one exe; gate line = that exe with the
options (or a single switch built in after the run, bench(switch) == bench(explicit options)). Report z vs the
null-gradient sigma per parameter (R9 method); no Elo claim - the crew's UHO [0,5] SPRT + 8moves_v3 confirm decide.

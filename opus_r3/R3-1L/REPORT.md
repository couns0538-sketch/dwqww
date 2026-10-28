# R3-1L Linux self-play double-check on GitHub ubuntu-24.04 — DONE

Branch opus-r3-sp-linux = origin/opus-r3-stack@cae5e6bf + merge origin/opus-r3-selfplay@49a2361a (3c3984a9)
+ afd3ae98 (workflow + job tools) + c7e8f6ce (docs, PC smoke; [skip ci]) + 5bdf14a1 (merge final stack head
34ef8a70) + 6f4067c3 (final-head configs, job selection) + b94cd4fd (interim results of run 40582392767; [skip ci])
+ the main session's evidence commits (a7b4a8dd: run 40582392767 complete; this REPORT with run 40585589600).
Agent text; the rows that were PARTIAL at hand-back were updated by the main session from the collect.sh tables.
No engine/CMake/test change: `git diff --stat origin/opus-r3-stack HEAD -- src include tests CMakeLists.txt tools` = empty.
Engine source of run 40582392767 = the PC run's 330237f3 (no src/include/CMakeLists change 330237f3..cae5e6bf).

## Acceptance
| line | result | evidence |
|---|---|---|
| workflow on push to opus-r3-sp-linux + workflow_dispatch; paths-ignore docs/logs only | done | .github/workflows/opus-r3-sp-linux.yml |
| 36 configs split for ~45 min wall | done: 29 jobs; release job 6-11 min, TSan job 8 min. Real wall time is longer: the account's 20-job limit was shared with other runs | jobs.json; run 40582392767 |
| CMake Release g++-14 Ninja --target forge, run_ci.sh flags, -D<SWITCH>=ON (allsw = opus-r3-switches.yml set) | done | run_job.sh; logs/run_40582392767/sp-*/builds.txt |
| identity: uci_check quick ALL OK for every build | ALL OK for every finished build (release base/allsw/int16/initonce, FMA 0; TSan base/allsw) | builds.txt per job |
| python-chess pinned to the PC venv's 1.11.2 | done | workflow Toolchain step |
| nets: make_nets.py on the runner; PureNnue net | O4 smoke net committed (394922 B, sha256 70f91587...a982f); the 7 regenerated nets are byte-identical to the PC run's | logs/smoke_pc/nets_*.sha256 |
| Syzygy 3-4-5 same bytes as the PC copy | 290 files, 939 MB, all sha256 match | syzygy345.sha256; plan job of run 40582392767 |
| ASan+UBSan all-ON | PASS: 2 x 250 games (seeds 1, 2), 0 errors, 0 sanitizer reports; 1432 HardDeadline watchdog answers, 0 late lines | logs/run_40582392767/SUMMARY.md |
| TSan on every Threads>1 config (100 games) | 6/6 PASS (all_on, all_on_pure, all_on_v1net, smp_best_thread, smp_exact_nodes, lockless_tt): 600 games, 0 errors, 0 TSan reports; 1721 watchdog answers in the all-ON variants, 0 late lines | logs/run_40582392767/SUMMARY.md |
| logs artifact per job; summary table; pass = 500 games + 0 errors | done | sp-<job> and sp-summary artifacts; summarize.py |
| bash -n + local smoke (1 config, 10 games, nice 19) before the first push | done: pure_nnue 10/10, 0 errors | logs/smoke_pc/ |
| R3-1 acceptance on Linux: 36 configs x 500 games, 0 errors | **PASS: 36/36 configs, 18000 games, 0 errors** (0 crashes, illegal moves, double bestmoves, timeouts, malformed lines); identity ALL OK + FMA 0 for every release build; run 40582392767 success | logs/run_40582392767/SUMMARY.md |
| final-head configs (all_on_final, smp_helpers_past_depth, spsa_plus10, spsa_minus10) x 500 + TSan of the 2 SMP ones | **PASS on the final engine head 064af732**: 4 x 500 = 2000 games, 0 errors; TSan all_on_final and smp_helpers_past_depth 2 x 100 games, 0 errors, 0 TSan reports (500 watchdog answers, 0 late lines); run 40585589600 success | configs_final_head.json; logs/run_40585589600/SUMMARY.md |
| opus-ci green | afd3ae98: 40582392592 success; 6f4067c3: 40585589643 success (release, ASan, TSan) | gh run list --branch opus-r3-sp-linux |

## Findings
- 0 errors in every finished row: no crash, illegal move, double bestmove, timeout, malformed output or info after bestmove.
- The HardDeadline watchdog never fires on quiet Linux release runners. Watchdog answers were 0 in hard_deadline10, all_on and all_on_v1net, against 1017 for all_on on the loaded PC.
  - The TSan runs do exercise it: all_on 559, all_on_pure 644, all_on_v1net 518 answers, 0 late lines, 0 TSan reports.
  - So the release watchdog path is covered by the PC run, and the race check by Linux TSan.
- Syzygy tables load the same on both platforms ("Syzygy: 145 WDL and 145 DTZ tables"). But info tbhits stayed 0 in every game on both PC and Linux. These runs show the tables load and play cleanly; they give no evidence of hits during search.
- Configs that set NNUEKingBuckets/OutputBuckets/PureNnue before NNUEFile print transient "info string ERROR NNUE v2: ... no v2 net is loaded" lines. The net loads at the next setoption, and the checker does not count these lines as errors (same on the PC). Sending NNUEFile first would avoid them.
- Speed: Linux release all_on took 564 s for 500 games (PC 788 s); single-thread configs about 360 s.
- The first run started 5 minutes late behind opus-r3-quietnps's 16 jobs and ran 8-16 jobs at a time.

## UNVERIFIED / left
- The full 36-config matrix ran on the engine of 330237f3 (= the PC run's head); the final head 064af732 was
  checked with the 4 configs that cover what changed after it (SmpHelpersPastDepth alone and in all-ON, the 20
  SPSA spins at +10% / -10%). A full 36-config re-run on 064af732: `gh workflow run opus-r3-sp-linux --ref
  opus-r3-sp-linux -f jobs=all` (README.md).
- 500 games per config on quiet runners is evidence, not proof, for timing-dependent defects; the release
  watchdog path fires only on the loaded PC (PC run) and under TSan here.

Machine exclusive: no (games on GitHub runners; the PC ran only the smokes, one build_pc.sh build and a 4-table download test at nice 19).

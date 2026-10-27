# S08fix — profile counters on AL1: per-worker banks + merge (S08-2), OFF proof + overhead (S08-3), dead-feature table (S08-4) — DONE on the PC (Linux CI recorded below)

Branch `opus-sol-S08fix` = AL1 base `d4f4312` + CI baseline `0d99f02` (`e41596a0`) + `990cbb18` (Sol's
`forge_sol_S08_profcounters_TLS_v2_20261026.patch`, verbatim, clean apply) + `c64199f2` (S08-2 + Linux CI) +
`dad28839` (evidence/tools) + the REPORT commit. `FORGE_PROF` stays default OFF. Machine exclusive: no (Idle priority,
JOBS=1). Work and results by a sub-agent; this report text is its hand-back (status was PARTIAL at hand-back because the
Linux CI was still queued).

## Acceptance

| Item | Command | Result | Evidence |
|---|---|---|---|
| S08-2 per-worker banks + merge | code; `tests/prof_tests.cpp` via ctest | each Worker owns a 64-byte-aligned plain-uint64 bank bound in its own thread; banks reset before helpers start; `Searcher::profile_snapshot()` merges after the join. forge_prof_tests (Threads 1/2/4: each worker bank == that worker's nodes; merge == sum; main+qs == nodes) PASS | `logs/ctest_on_full_mingw.log` |
| S08-2 planted bugs | `make_prof_mutant.py` on a copy | merge_main_only: FAIL "merged == sum" (T2, T4); shared_bank: helper banks 0, worker 0 holds 17110 = all workers minus 100 lost updates (17210): FAIL; green control PASS | `logs/prof_mutants.log` |
| ON full ctest (PC) | `ctest` + `check_known_failures.py` | 14/15, only the 4 known forge_tests lines: PASS | `logs/known_on_full_mingw.log` |
| S08-3 OFF = lock | `build_pc.sh` OFF; `cmp -l`; `uci_check --full` | 6 differing bytes (PE timestamp/checksum 137-139, 217-219); ALL OK; FMA 0; OFF has no Profile option / bench_prof | `logs/pc_builds.log`, `logs/identity_off_on.log` |
| ON identity | `uci_check --full`; `bench_prof 11..22` | ALL OK; bench_prof nodes == pins == counter-packet nodes at all 5 depths; FMA 0 | `logs/identity_off_on.log` |
| S08-3 same-machine NPS (>= 5 runs, median) | `nps_prof_ab.py --runs 7 --depth 16 --depth 20` | CPU-time median vs lock: OFF +0.90% / 0.00%; ON with Profile off -13.85% / -10.66%; ON counting (bench_prof) -11.11% / -11.38%; nodes identical in all arms. Advisory (PC 90-97% busy) | `logs/nps_s08_3_pc.log` |
| S08-4 dead-feature table | `forge_sol_S08_collect_profiles_v2.py --nodes 10000` on the 2,000-position substitute corpus | PASS 2000/2000, 19.88M nodes, no overflow. Rare (< 0.1%): nnue_refresh 2000/12,076,007 (0.0166%), history_prunes 1108/7,794,309 (0.0142%); bench d20 nnue_refresh 8/6,931,060. capture_futility_prunes (0/3,723,977) moved to "disabled by default (CaptureFutilityBase = 0)" | `logs/forge_sol_S08_deadfeature_table_v2.md`, `logs/collect_v2_AL1_report.json` |
| S08-4 corpus limit stated | IDEA_SOURCE.md + table header | no STS file exists on the PC; Sol's sealed substitute corpus (300 WAC + 7 bench + 1,693 openings) is not the specified WAC/STS set | `IDEA_SOURCE.md` |
| Linux CI: ON release/ASan/TSan, runner NPS, Threads 4/1 skew (Sol's shared bank 990cbb18 vs per-worker), collector v1 RED / v2 Linux vs PC | opus-sol-s08fix-ci 40517299746, opus-ci 40517299539 | see "Linux CI" below | — |

## Findings
- MinGW implements `thread_local` with emulated TLS: every count site in the ON build calls `__emutls_get_address`, also
  with Profile=false (35 vs 11 such calls in OFF), which costs ~11-14% CPU-time NPS on the PC whether counting or not;
  the counting itself is cheap (add + setb/or) (`logs/on_build_emutls.log`). Follow-up idea: pass the worker's bank
  explicitly instead of TLS in FORGE_PROF builds.
- Sharing one non-atomic bank loses updates under Threads > 1 (mutant: 100 of 17210); Sol's shared atomics avoided that
  but put all threads on the same counter lines. Per-worker banks avoid both.
- Sol's v1 collector cannot run on Windows (select() on pipes, WinError 10093) and hard-codes Sol's base pins
  (308972/11901452), so it can never accept an AL1 build; v2 takes AL1 pins (configurable) and reads pipes with
  threads on Windows.

## Linux CI
Recorded by the main session after the hand-back: see the section appended below when the runs complete.

## Left / UNVERIFIED
- No Elo or speed claim; the PC NPS figures are advisory.

# R3-6Q Lazy SMP time-to-depth on quiet GitHub runners — DONE

- Branch `opus-r3-smpq`, from origin/opus-r3-stack 34ef8a70. Workflow commit a702c4f8; head eb66f6c6.
- Workflow `.github/workflows/opus-r3-smpq.yml`, run **40586326969** (prep → ttd rep 1/2/3 → summary).
- opus-ci on the push: run **40586326892** (success).
- Agent text; the rows that were pending at hand-back and the results section were filled in by the main session
  from run 40586326969 (all jobs success; `logs/gh_40586326969/`).

## Acceptance
| item | result | evidence |
|---|---|---|
| Linux harness with the R3-6 output format | **DONE.** `smp_ttd_linux.py` follows the R3-6 protocol. Wall time runs from `go` to `bestmove`. CPU is utime+stime of the whole engine process from /proc/<pid>/stat. System load and steal come from /proc/stat, and whole-process CPU from os.wait4. It writes the same JSONL fields plus steal_frac, cpu_total_s, nproc, base_depth and depth_offset. `summarize.py` reads it unchanged; `report_q.py` imports it. | `smp_ttd_linux.py` |
| Smoke test before the push | **DONE.** `bash -n` passes on the 4 scripts and `py_compile` on the 3 .py files. On the PC (nice 19, IDLE priority, Windows fallback for CPU and system times) I ran 6 short runs: bench.0 and bench.4 at depth-9, off at T1/T2 and offP at T2. `report_q.py` ran on synthetic repetitions built from them, including one incomplete position, and `choose_depth.py` ran too. | `logs/SMOKE.txt`, `logs/pc_smoke.{log,jsonl}`, `logs/pc_smoke_report_q_on_synthetic_reps.md` |
| Build recipe + uci_check quick ALL OK | **DONE on the runner** (prep job): g++-14 14.2.0, CMake Release, Ninja, `--target forge`, the given CMAKE_CXX_FLAGS. sha256 d6190041a7578485149f5802d75ce16a14028adde1c7fa4cb7308c625e97bcfd, FMA count 0. bench 11/13/16 and both perft5 match the pins: ALL OK. `uci` lists all 4 SMP options. All three repetitions use this one binary and re-ran uci_check on it: success. | `logs/gh_40586326969_prep/identity.log`, `uci_options.txt` |
| Runner speed check; lower depths only if needed | **DONE: no reduction (depth_offset=0).** Threads=1 at full depth on 6 positions: runner/PC wall ratio **0.991** (0.92-1.06 per position). T1 nodes are **identical to the PC on 6/6 positions**. Job estimate 1288 s, under the 2520 s limit. | `logs/gh_40586326969_prep/speed_check.md`, `speed_t1.jsonl` |
| 3 independent repetitions, each running every (config, threads, position) once in shuffled order | **DONE**: 3 x 300 runs, 30/30 positions complete in every repetition, no cutoff; Threads=1 nodes identical in all 60 (position, config) cells across repetitions. Each ttd matrix job covers all 30 positions: off/on at T1-3 and offP/onP at T2-3, which is 300 runs per job. Hash 64, a fresh process per run. Position order is shuffled per repetition and (config, threads) within a position. No new position starts after 2700 s. Job timeout 60 min, step timeout 54 min. | `logs/gh_40586326969/ttd_rep{1,2,3}.jsonl.xz`, `ttd_rep*.log`, `raw_sha256.txt` |
| R3-6 tables, offP vs off and onP vs on at T2/T3 with 95 % bootstrap CIs, pooled and per repetition, PC numbers beside | `report_q.py` is ready. It runs in the summary job (`needs: [prep, ttd]`, `if: always()`) and can also be run locally through `collect.sh`. **DONE**: the summary job's table and the local `report_q.py` run are byte-identical (results below). | `logs/gh_40586326969/summary_runner.md`, `summary_local.md` |
| nproc and lscpu recorded in each job | done: nproc 4 everywhere (2 cores x 2 SMT threads); reps 1-2 on AMD EPYC 7763, rep 3 on AMD EPYC 9V74 (faster: T1 1.55 vs 1.30 Mnps; comparisons are paired within a repetition) | `logs/gh_40586326969_prep/runner_prep.txt`, `logs/gh_40586326969/runner_rep*.txt` |
| opus-ci stays green | success (release, ASan, TSan; run 40586326892) | gh run list --branch opus-r3-smpq |

## Findings so far
- On a single thread the runner is as fast as the loaded PC was (ratio 0.991). So R3-6's depths run unchanged, and the GitHub T1 cells compare directly with the PC's.
- Threads=1 fixed-depth searches give identical node counts across platforms (Linux g++-14 vs the PC build) on 6/6 positions.
- The runner was quiet during the prep sample: other load 0.1-0.4 %, steal 0, and T1 got a full CPU (cpu = wall).
- Topology caveat: the runner is an AMD EPYC 7763 whose **4 vCPUs are 2 physical cores × 2 SMT threads**, as O1/O1-LTT found. T2 can run on two physical cores. T3 must share a core with an SMT sibling, so read T3 as "3 threads on 2 cores + SMT", not as 3 free cores.

## Results (run 40586326969; pooled over 3 repetitions, per-position medians; `logs/gh_40586326969/summary_local.md`)
The engine got its threads (CPUs got: T1 1.00, T2 2.00, T3 2.9-3.0; other load 0.2-0.3%, steal 0).

| config | T | TTD sum s | per-position speedup gmean [p25..p75] | nodes Tn/T1 | NPS scaling | PC (R3-6) speedup gmean |
|---|---|---|---|---|---|---|
| off | 1 | 125.8 | 1.00 | 1.00 | 1.00 | 1.00 |
| off | 2 | 107.7 | 1.28 [0.88..1.71] | 1.57 | 1.95 | 1.07 |
| off | 3 | 121.8 | 1.14 [0.90..1.47] | 2.13 | 2.40 | 1.24 |
| on | 2 | 103.6 | 1.39 [0.86..1.65] | 1.51 | 2.02 | 1.28 |
| on | 3 | 111.9 | 1.26 [0.92..1.78] | 1.92 | 2.37 | 1.28 |
| offP | 2 | 115.0 | 1.16 [0.75..1.46] | 1.81 | 2.10 | 1.08 |
| offP | 3 | 122.4 | 1.11 [0.75..1.66] | 2.22 | 2.44 | 1.21 |
| onP | 2 | 114.2 | 1.20 [0.78..1.61] | 1.77 | 2.09 | 1.21 |
| onP | 3 | 129.8 | 1.08 [0.68..1.55] | 2.33 | 2.51 | 1.40 |

Paired wall time-to-depth B/A (gmean over 30 positions, 95% bootstrap CI; < 1 = B faster):

| B vs A | T | pooled | rep 1 | rep 2 | rep 3 | PC (R3-6) |
|---|---|---|---|---|---|---|
| offP vs off | 2 | 1.105 [0.948..1.286] | 1.196 | 0.987 | 1.057 | 0.989 [0.798..1.210] |
| offP vs off | 3 | 1.019 [0.893..1.157] | 0.839 | 1.190 | 1.280 | 1.025 [0.862..1.198] |
| onP vs on | 2 | **1.157 [1.034..1.308]** | 1.180 | 1.131 | 1.162 | 1.060 [0.883..1.287] |
| onP vs on | 3 | **1.168 [1.005..1.366]** | 1.066 | 1.202 | 1.242 | 0.910 [0.691..1.178] |
| on vs off | 1 | **1.022 [1.019..1.025]** (nodes identical) | 1.022 | 1.023 | 1.018 | 0.999 [0.981..1.015] |
| on vs off | 2 | 0.947 [0.859..1.049] | 0.968 | 0.960 | 0.906 | 0.837 [0.665..1.041] |
| on vs off | 3 | 0.919 [0.801..1.061] | 0.906 | 0.899 | 1.025 | 0.973 [0.803..1.153] |

## Findings (results)
- **SmpHelpersPastDepth does not shorten time-to-depth on quiet runners.** Alone (offP vs off) the ratio is
  1.105 [0.948..1.286] at T2 and 1.019 [0.893..1.157] at T3 (no effect resolved). With the SMP options on
  (onP vs on) it is **slower: 1.157 [1.034..1.308] at T2 and 1.168 [1.005..1.366] at T3**, with 17-21% more nodes
  to complete the depth. The helpers no longer idle (R3-6's trace), but their deeper iterations do not help the
  main thread finish depth N. The option stays default off; it should not be turned on or gated for speed.
- The "on" set (SmpExactNodes + SmpBestThread + LocklessTT) costs 2.2% wall at Threads=1 with identical nodes
  (1.022 [1.019..1.025] in every repetition): the per-node cost of LocklessTT on this Linux build (the PC's R3-2
  measured -0.55% [-1.27, +0.16] NPS for LocklessTT at T1). At T2/T3 "on" is not significantly different from off.
- Stack OFF on quiet runners: per-position speedup 1.28x (T2) and 1.14x (T3), node inflation 1.57x / 2.13x, NPS
  scaling 1.95x / 2.40x. T3 is worse than T2 here, but T3 shares a physical core with an SMT sibling (4 vCPUs = 2
  cores x 2 threads), so T3 is not "3 free cores".

## UNVERIFIED / left
- One runner type per repetition (EPYC 7763 twice, EPYC 9V74 once); the PC's Zen 5 was not covered.
- Fixed-depth time-to-depth only: clocked play is not affected by SmpHelpersPastDepth (helpers already run to
  depth 64 there), and no gate was run.
- If a repetition hits the 2700 s cutoff it covers fewer positions. `report_q.py` then uses only complete positions in that repetition's tables. The pooled table uses every position that has all 10 cells in at least one repetition.
- I had no local YAML linter. The workflow is shown valid only by GitHub accepting it and running prep and all three ttd jobs.

Machine exclusive: no. The PC only ran the smoke test (nice 19); the measurement runs on GitHub runners.


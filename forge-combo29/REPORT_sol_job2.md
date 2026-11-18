# Sol — Job 2 search events by remaining depth and node budget

1. **Step 0 met.** All eight PC r15 pins matched. [Raw inputs and outputs](sol/job2/step0.raw.txt)
2. **Depth-12 identity met.** Plain and counting builds matched in node count and best move on every O and G position under PC20.

   | Set | Exact positions | Total nodes | First three nodes | Node SHA-256 prefix | Best-move SHA-256 prefix |
   |---|---:|---:|---|---|---|
   | O | 200/200 | 8315168 | 21812 / 26844 / 35173 | fd609b7b1a8dd179 | 14583c86b5f56cb6 |
   | G | 353/353 | 17611204 | 31779 / 46086 / 84457 | 60b6916f01395e99 | 0846f027e7e9b77e |

3. **All three controls met.** Counting build, first 20 O positions, 400,000 actual search nodes per arm at `go nodes 20000`, PC20 with one option changed per arm. `RfpDepth=0` gave 0 reverse-futility returns at every depth (112,034 under PC20). `EvalSwingMult=16` gave 166,417 updates (0 under PC20). `NullMoveMinDepth=10` gave 0 tries below depth 10 and 22 at depth 10 or above (4,777 below depth 10 under PC20). [Identity evidence](sol/job2/identities.txt) · [Control evidence](sol/job2/controls.txt)
4. **Prediction graded.** The [prediction](sol/job2/prediction.txt) was pushed at `2bbfe429c7d79904ab471cc22229f723c85599c4` before the first Step 3 search. The tolerance was a factor of 1.5 on the exact ratio in either direction. Zero forecasts required zero occurrences in both runs.

| Event | O guess | O measured | O outcome | G guess | G measured | G outcome |
|---|---:|---:|---|---:|---:|---|
| razor_taken | 1.10 | 0.6239 | KILLED | 1.05 | 0.7810 | survives |
| rfp_taken | 0.85 | 1.0333 | survives | 0.85 | 0.9662 | survives |
| null_move_taken | 0.40 | 0.4307 | survives | 0.45 | 0.4319 | survives |
| null_move_tested | 0.40 | 0.3779 | survives | 0.45 | 0.4092 | survives |
| probcut_taken | 0.25 | 0.1738 | survives | 0.35 | 0.2457 | survives |
| probcut_tested | 0.30 | 0.1966 | KILLED | 0.40 | 0.2379 | KILLED |
| iir_no_tt_taken | 1.15 | 0.9050 | survives | 1.10 | 0.8744 | survives |
| iir_tt_taken | 0.35 | 0.7120 | KILLED | 0.40 | 0.8025 | KILLED |
| lmp_taken | 0.95 | 1.0223 | survives | 0.90 | 1.0701 | survives |
| quiet_futility_taken | 1.00 | 0.7102 | survives | 1.00 | 0.8122 | survives |
| history_pruning_taken | 0.70 | 0.0648 | KILLED | 0.75 | 0.1628 | KILLED |
| quiet_see_taken | 0.80 | 0.8935 | survives | 0.85 | 1.0028 | survives |
| capture_futility_taken | zero | zero / zero | survives | zero | zero / zero | survives |
| noisy_see_taken | 0.85 | 0.9697 | survives | 0.90 | 1.1299 | survives |
| singular_taken | 0.25 | 0.3892 | KILLED | 0.30 | 0.4182 | survives |
| singular_double | 0.20 | 0.2931 | survives | 0.25 | 0.3425 | survives |
| singular_negative | 0.20 | 0.1996 | survives | 0.30 | 0.1968 | KILLED |
| check_extension_taken | 0.80 | 0.9126 | survives | 0.80 | 0.8897 | survives |
| lmr_taken | 0.75 | 0.9070 | survives | 0.80 | 0.8309 | survives |
| lmr_plies | 0.65 | 0.7484 | survives | 0.70 | 0.6897 | survives |
| aspiration_taken | 3.00 | 4.1809 | survives | 2.60 | 3.4584 | survives |
| q_futility_taken | 1.05 | 0.7069 | survives | 1.00 | 0.9586 | survives |
| fail_low_bonus_taken | zero | zero / zero | survives | zero | zero / zero | survives |
| eval_swing_taken | zero | zero / zero | survives | zero | zero / zero | survives |
| draw_jitter_taken | zero | zero / zero | survives | zero | zero / zero | survives |

Outcomes: 41 survive and 9 killed.

O below 0.5: null_move_taken, null_move_tested, probcut_taken, probcut_tested, history_pruning_taken, singular_taken, singular_double, singular_negative. Above 2: aspiration_taken.

G below 0.5: null_move_taken, null_move_tested, probcut_taken, probcut_tested, history_pruning_taken, singular_taken, singular_double, singular_negative. Above 2: aspiration_taken.

5. **Step 3 completed.** All four groups used the counting build and PC20 defined below. The O and G rows are in fixture order. The rates include all nodes, including work in an unfinished hard-budget iteration. Root depth is the last `info depth` line.

Summed 553 CNT lines per budget (hard: 553, soft: 553).

| Set | Budget | CNT lines | Total nodes | Root depth median / min / max | CNT nodes median | Last info nodes median | Rows with extra CNT nodes |
|---|---|---:|---:|---|---:|---:|---:|
| O | nodes 20000 | 200 | 4000000 | 10 / 8 / 13 | 20000 | 15944.5 | 200 |
| O | softnodes 2000 | 200 | 590929 | 7 / 6 / 8 | 2754 | 2754 | 0 |
| G | nodes 20000 | 353 | 7007212 | 10 / 8 / 64 | 20000 | 15171 | 348 |
| G | softnodes 2000 | 353 | 1071475 | 7 / 5 / 64 | 2765 | 2765 | 0 |

Remaining-depth shares (%): 0–2 / 3–5 / 6–8 / 9+. Rates use actual main plus qsearch nodes.
The lmr_plies row counts plies rather than events. Tested rows are tries for null move and ProbCut.

| Set | Counter | Hard / 1k | Soft / 1k | Soft / hard | Hard depth shares (%) | Soft depth shares (%) |
|---|---|---:|---:|---:|---|---|
| O | razor_taken | 1.9935 | 1.2438 | 0.6239 | 100.0 / 0.0 / 0.0 / 0.0 | 100.0 / 0.0 / 0.0 / 0.0 |
| O | rfp_taken | 269.0507 | 278.0216 | 1.0333 | 96.9 / 2.9 / 0.2 / 0.0 | 98.0 / 2.0 / 0.0 / 0.0 |
| O | null_move_taken | 8.3845 | 3.6113 | 0.4307 | 0.0 / 81.5 / 18.0 / 0.5 | 0.0 / 95.7 / 4.3 / 0.0 |
| O | null_move_tested | 11.2703 | 4.2594 | 0.3779 | 0.0 / 70.2 / 27.6 / 2.2 | 0.0 / 93.3 / 6.7 / 0.0 |
| O | probcut_taken | 1.1298 | 0.1963 | 0.1738 | 0.0 / 53.2 / 44.9 / 1.9 | 0.0 / 73.3 / 26.7 / 0.0 |
| O | probcut_tested | 1.4033 | 0.2758 | 0.1966 | 0.0 / 53.4 / 44.9 / 1.7 | 0.0 / 76.1 / 23.9 / 0.0 |
| O | iir_no_tt_taken | 45.2140 | 40.9186 | 0.9050 | 60.6 / 38.3 / 1.1 / 0.0 | 71.3 / 28.6 / 0.1 / 0.0 |
| O | iir_tt_taken | 1.0315 | 0.7344 | 0.7120 | 0.0 / 60.7 / 38.3 / 1.0 | 0.0 / 91.0 / 9.0 / 0.0 |
| O | lmp_taken | 70.9808 | 72.5637 | 1.0223 | 71.4 / 26.0 / 2.6 / 0.0 | 77.4 / 22.0 / 0.7 / 0.0 |
| O | quiet_futility_taken | 10.5840 | 7.5170 | 0.7102 | 80.3 / 18.8 / 0.8 / 0.1 | 84.4 / 15.1 / 0.5 / 0.0 |
| O | history_pruning_taken | 0.4440 | 0.0288 | 0.0648 | 95.8 / 4.2 / 0.0 / 0.0 | 100.0 / 0.0 / 0.0 / 0.0 |
| O | quiet_see_taken | 116.5285 | 104.1225 | 0.8935 | 44.0 / 49.3 / 6.6 / 0.2 | 49.1 / 47.4 / 3.5 / 0.0 |
| O | capture_futility_taken | 0.0000 | 0.0000 | n/a | n/a | n/a |
| O | noisy_see_taken | 62.5667 | 60.6740 | 0.9697 | 87.9 / 12.1 / 0.0 / 0.0 | 89.9 / 10.1 / 0.0 / 0.0 |
| O | singular_taken | 2.1738 | 0.8461 | 0.3892 | 0.0 / 0.0 / 93.9 / 6.1 | 0.0 / 0.0 / 100.0 / 0.0 |
| O | singular_double | 0.5890 | 0.1726 | 0.2931 | 0.0 / 0.0 / 96.1 / 3.9 | 0.0 / 0.0 / 100.0 / 0.0 |
| O | singular_negative | 1.1783 | 0.2352 | 0.1996 | 0.0 / 0.0 / 87.6 / 12.4 | 0.0 / 0.0 / 100.0 / 0.0 |
| O | check_extension_taken | 14.1645 | 12.9271 | 0.9126 | 43.0 / 48.1 / 8.2 / 0.7 | 49.2 / 47.3 / 3.5 / 0.0 |
| O | lmr_taken | 300.7072 | 272.7367 | 0.9070 | 0.9 / 63.0 / 32.0 / 4.0 | 1.0 / 78.1 / 20.9 / 0.0 |
| O | lmr_plies | 715.4578 | 535.4146 | 0.7484 | 0.4 / 44.5 / 48.5 / 6.6 | 0.5 / 66.9 / 32.6 / 0.0 |
| O | aspiration_taken | 0.1360 | 0.5686 | 4.1809 | 0.0 / 33.6 / 44.1 / 22.2 | 0.0 / 54.5 / 45.5 / 0.0 |
| O | q_futility_taken | 45.1700 | 31.9294 | 0.7069 | 100.0 / 0.0 / 0.0 / 0.0 | 100.0 / 0.0 / 0.0 / 0.0 |
| O | fail_low_bonus_taken | 0.0000 | 0.0000 | n/a | n/a | n/a |
| O | eval_swing_taken | 0.0000 | 0.0000 | n/a | n/a | n/a |
| O | draw_jitter_taken | 0.0000 | 0.0000 | n/a | n/a | n/a |
| G | razor_taken | 7.7006 | 6.0141 | 0.7810 | 100.0 / 0.0 / 0.0 / 0.0 | 100.0 / 0.0 / 0.0 / 0.0 |
| G | rfp_taken | 268.0035 | 258.9421 | 0.9662 | 89.0 / 9.6 / 1.4 / 0.0 | 91.6 / 8.1 / 0.3 / 0.0 |
| G | null_move_taken | 11.5271 | 4.9791 | 0.4319 | 0.0 / 69.7 / 26.7 / 3.6 | 0.0 / 89.8 / 9.6 / 0.6 |
| G | null_move_tested | 15.7277 | 6.4351 | 0.4092 | 0.0 / 64.0 / 31.2 / 4.8 | 0.0 / 88.0 / 11.5 / 0.5 |
| G | probcut_taken | 2.4161 | 0.5936 | 0.2457 | 0.0 / 48.0 / 45.8 / 6.2 | 0.0 / 73.4 / 26.6 / 0.0 |
| G | probcut_tested | 3.2719 | 0.7784 | 0.2379 | 0.0 / 46.3 / 47.8 / 5.9 | 0.0 / 69.2 / 30.6 / 0.2 |
| G | iir_no_tt_taken | 37.4146 | 32.7156 | 0.8744 | 52.5 / 45.0 / 2.4 / 0.1 | 64.8 / 34.5 / 0.7 / 0.0 |
| G | iir_tt_taken | 1.2176 | 0.9772 | 0.8025 | 0.0 / 57.0 / 41.0 / 2.0 | 0.0 / 86.5 / 13.5 / 0.0 |
| G | lmp_taken | 59.2261 | 63.3799 | 1.0701 | 72.6 / 25.5 / 1.9 / 0.0 | 78.9 / 20.6 / 0.5 / 0.0 |
| G | quiet_futility_taken | 12.5502 | 10.1934 | 0.8122 | 60.5 / 34.7 / 4.3 / 0.6 | 66.9 / 30.1 / 2.9 / 0.1 |
| G | history_pruning_taken | 0.8142 | 0.1325 | 0.1628 | 90.5 / 9.4 / 0.1 / 0.0 | 100.0 / 0.0 / 0.0 / 0.0 |
| G | quiet_see_taken | 120.7176 | 121.0518 | 1.0028 | 40.8 / 47.6 / 11.3 / 0.4 | 49.9 / 44.5 / 5.6 / 0.0 |
| G | capture_futility_taken | 0.0000 | 0.0000 | n/a | n/a | n/a |
| G | noisy_see_taken | 79.3552 | 89.6596 | 1.1299 | 82.4 / 17.5 / 0.0 / 0.0 | 85.6 / 14.3 / 0.0 / 0.0 |
| G | singular_taken | 6.0609 | 2.5348 | 0.4182 | 0.0 / 0.0 / 86.7 / 13.3 | 0.0 / 0.0 / 97.8 / 2.2 |
| G | singular_double | 3.3271 | 1.1396 | 0.3425 | 0.0 / 0.0 / 87.7 / 12.3 | 0.0 / 0.0 / 95.1 / 4.9 |
| G | singular_negative | 1.2190 | 0.2399 | 0.1968 | 0.0 / 0.0 / 77.6 / 22.4 | 0.0 / 0.0 / 83.3 / 16.7 |
| G | check_extension_taken | 35.4403 | 31.5322 | 0.8897 | 40.1 / 48.7 / 8.5 / 2.8 | 47.0 / 47.6 / 4.0 / 1.5 |
| G | lmr_taken | 327.5461 | 272.1697 | 0.8309 | 1.8 / 60.5 / 30.8 / 6.8 | 2.1 / 74.5 / 22.8 / 0.6 |
| G | lmr_plies | 732.3069 | 505.0617 | 0.6897 | 0.8 / 43.2 / 45.2 / 10.8 | 1.1 / 63.7 / 34.2 / 1.0 |
| G | aspiration_taken | 0.4134 | 1.4298 | 3.4584 | 0.0 / 23.4 / 43.4 / 33.3 | 0.0 / 44.2 / 55.4 / 0.5 |
| G | q_futility_taken | 53.0595 | 50.8645 | 0.9586 | 100.0 / 0.0 / 0.0 / 0.0 | 100.0 / 0.0 / 0.0 / 0.0 |
| G | fail_low_bonus_taken | 0.0000 | 0.0000 | n/a | n/a | n/a |
| G | eval_swing_taken | 0.0000 | 0.0000 | n/a | n/a | n/a |
| G | draw_jitter_taken | 0.0000 | 0.0000 | n/a | n/a | n/a |

## Facts

- Reverse futility and LMP kept close to their hard-budget rates on both sets. Their soft/hard ratios were 1.0333 and 1.0223 on O, and 0.9662 and 1.0701 on G. Null-move cuts, ProbCut cuts, history pruning and positive singular extensions were below half their hard-budget rates on both sets. Aspiration retries were above twice the hard-budget rate on both sets.
- The largest rate drop was history pruning at 0.0648 on O and 0.1628 on G. In the hard-budget rows, 95.8% on O and 90.5% on G of those events were already at remaining depth 0–2. These are event shares. A cause would require conditioning on eligible moves, depth, and the history values at the test.
- The hard cap was reached by all 200 O searches and 348 of 353 G searches. The five G searches that finished below 20,000 nodes reached depth 64 with mate scores. No soft run reached its 8,000-node ceiling. The O soft runs used 2,002–6,280 nodes. The G soft runs used 1,264–7,129 nodes. Raw `CNT` totals matched the engine's final reported node accounting, checked at the source of each `CNT` line. The saved soft-budget final line agrees independently.
- Job 1 follow-up. I independently recalculated the latest completed helper report, Kimi5 Job 23, from its committed stdout. The [Sol note](NOTES_sol.md) identifies its build, options, node totals and checks.

## Build, settings and evidence

- Case A. GPT-6 (Codex), Linux x86_64. Forge base `6b98f2170a3210e71beed04bbd2553972c253ed7` plus the PC r15 patch in `forge-combo29/soak_all/FABLE_TO_swarm_5.md` on handoff commit `cea646630ab27e64dfee92c1bb334277c717c79d`. Extracted patch SHA-256 `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`; the scratch directory application used `patch -p1 -F0`. The first scratch attempt used the parent directory and failed before applying any file. The clean application from `forge-combo29` passed zero fuzz.
- Both binaries used CMake 4.2.3, Release, GCC 14.2.0 (Debian 14.2.0-19), libstdc++ `libstdc++.so.6.0.33`, glibc 2.41 (Debian 2.41-12+deb13u4), `x86-64-v4`, portable OFF, PEXT and ZMM enabled, strict FP, and `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`. Plain executable SHA-256 `9279d02c2ea8c42875ec83a55399aeb588b72a3ae13e8067969be2cee8219306`. Counting executable SHA-256 `906bf28e2afd7a694efb3897995ca292b9a922f636f6c22f311d5b9597371445`. The applied [counter patch](sol/job2/count.patch.txt) SHA-256 is `ff3c25aa634966aa62cd9ce75326a6c148d03b2c24eb36d279a00d68b7a75488`. It applies with zero fuzz to the plain PC r15 source.
- Default built-in evaluation. No external network file was loaded. The compiled-in AL1 s198 weights source SHA-256 in both builds was `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. The v3 code path was compiled out.
- PC20 was S14 plus `CuckooRep true`, `HistRework 2`, `TtPruneV2 true`, `CorrHistV2 true`, `MateAlphaGuard true`, `OwnBook false`. S14 was `LmrQuietBase 93`, `LmrQuietDivisor 205`, `LmrNoisyBase 13`, `LmrNoisyDivisor 333`, `LmrHistoryDivisor 5643`, `NullMoveBase 5`, `LmpBase 8`, `HistoryPruneMultiplier 2220`, `HistoryBonusQuadratic 24`, `HistoryBonusLinear 54`, `HistoryBonusMax 2212`, `SingularDepth 6`, `IirDepth 2`, `NonPawnCorrection true`. Depth-12, control and Step 3 runs used Threads 1, Hash 16 MiB, one PV and `ucinewgame` plus `isready` before each search. Step 0 used a fresh process and only each named settings profile. Step 0 full settings, output and timings are in the raw file. [Raw rows and metadata](sol/job2/raw)
- O read from `forge-combo29/tests_kimi5_job4/first200.fens` at `8f316b85a04bd4f2dedd6e15eefe8b3a18f1832f`. `git hash-object` gave `e967e8327ec2be34eaf6df7f1763fa13b00e6497`. G read from `forge-combo29/tests_deepseek5_job10/set_G.epd` at `731fc808e3e0770805cb67654dea498d3bcdb6c6`. `git hash-object` gave `827bda196bb7dea0df27f6d78fb3039e31c58f75`. [Counter sites and settings](sol/job2/sites.txt) · [Clock stamps](sol/job2/stamps.txt)

To reproduce the gates and the table from the checked-in text logs, run these commands from `forge-combo29/sol/job2`:

```sh
python3 verify_gates.py identities raw
python3 verify_gates.py controls raw
python3 summarize.py raw/O-hard.jsonl raw/O-soft.jsonl raw/G-hard.jsonl raw/G-soft.jsonl
```

## Suspicions

On the smaller budget the set of opportunities for history pruning may change faster than the remaining-depth mix. The report alone cannot tell whether that comes from fewer eligible moves, less training of the history values during the search, or different moves reaching the test.

## What I did not do

No live 512/768 net, owner-PC execution, training, tuning, games, Elo or timing comparison. The instrumentation stayed in a scratch build. The branch contains text evidence and the unified counter patch.

## What I am not sure about

The changes in event frequency may differ with the active PC network, with a warm history from actual play, or on the tuner’s own position distribution. The counters describe the path through this build and these fixed positions.

## Pre-commit readback

```text
M  forge-combo29/NOTES_sol.md
AM forge-combo29/REPORT_sol_job2.md
A  forge-combo29/sol/job2/controls.txt
A  forge-combo29/sol/job2/count.patch.txt
A  forge-combo29/sol/job2/identities.txt
A  forge-combo29/sol/job2/raw/G-hard.jsonl
A  forge-combo29/sol/job2/raw/G-hard.jsonl.meta
A  forge-combo29/sol/job2/raw/G-soft.jsonl
A  forge-combo29/sol/job2/raw/G-soft.jsonl.meta
A  forge-combo29/sol/job2/raw/O-hard.jsonl
A  forge-combo29/sol/job2/raw/O-hard.jsonl.meta
A  forge-combo29/sol/job2/raw/O-soft.jsonl
A  forge-combo29/sol/job2/raw/O-soft.jsonl.meta
A  forge-combo29/sol/job2/raw/control-eval-swing.jsonl
A  forge-combo29/sol/job2/raw/control-eval-swing.jsonl.meta
A  forge-combo29/sol/job2/raw/control-null-min10.jsonl
A  forge-combo29/sol/job2/raw/control-null-min10.jsonl.meta
A  forge-combo29/sol/job2/raw/control-pc20.jsonl
A  forge-combo29/sol/job2/raw/control-pc20.jsonl.meta
A  forge-combo29/sol/job2/raw/control-rfp-off.jsonl
A  forge-combo29/sol/job2/raw/control-rfp-off.jsonl.meta
A  forge-combo29/sol/job2/raw/identity-count-G.jsonl
A  forge-combo29/sol/job2/raw/identity-count-G.jsonl.meta
A  forge-combo29/sol/job2/raw/identity-count-O.jsonl
A  forge-combo29/sol/job2/raw/identity-count-O.jsonl.meta
A  forge-combo29/sol/job2/raw/identity-plain-G.jsonl
A  forge-combo29/sol/job2/raw/identity-plain-G.jsonl.meta
A  forge-combo29/sol/job2/raw/identity-plain-O.jsonl
A  forge-combo29/sol/job2/raw/identity-plain-O.jsonl.meta
A  forge-combo29/sol/job2/run_matrix.py
A  forge-combo29/sol/job2/sites.txt
A  forge-combo29/sol/job2/stamps.txt
A  forge-combo29/sol/job2/step0.raw.txt
A  forge-combo29/sol/job2/summarize.py
A  forge-combo29/sol/job2/verify_gates.py
forge-combo29/sol/job2:
controls.txt
count.patch.txt
identities.txt
prediction.txt
raw
run_matrix.py
sites.txt
stamps.txt
step0.raw.txt
summarize.py
verify_gates.py

forge-combo29/sol/job2/raw:
G-hard.jsonl
G-hard.jsonl.meta
G-soft.jsonl
G-soft.jsonl.meta
O-hard.jsonl
O-hard.jsonl.meta
O-soft.jsonl
O-soft.jsonl.meta
control-eval-swing.jsonl
control-eval-swing.jsonl.meta
control-null-min10.jsonl
control-null-min10.jsonl.meta
control-pc20.jsonl
control-pc20.jsonl.meta
control-rfp-off.jsonl
control-rfp-off.jsonl.meta
identity-count-G.jsonl
identity-count-G.jsonl.meta
identity-count-O.jsonl
identity-count-O.jsonl.meta
identity-plain-G.jsonl
identity-plain-G.jsonl.meta
identity-plain-O.jsonl
identity-plain-O.jsonl.meta
```

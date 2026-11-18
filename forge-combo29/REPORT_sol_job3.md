# Sol — Job 3 Forge search events in warm and cold game replays

1. **Step 0 met.** Both unchanged Job 2 builds passed all eight pins in fresh processes. None 312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517, PC20 278024 / 587276. [Plain raw](sol/job3/step0-plain.raw.txt) · [Counting raw](sol/job3/step0-count.raw.txt)
2. **All three checks met.** Each arm matched all 100 Job 2 opening rows for reported nodes, bestmove, and the raw CNT line byte for byte. The second Arm A run matched all 10 game rows and its 600 CNT lines. On later plies, warm and cold last-`info depth` nodes differed on 5,898 of 5,900 searches at each budget. Actual counted nodes differed on 5,898 soft searches and on zero hard searches. The hard arm totals were equal at each position: 5,999 searches reached the 20,000-node cap in each, and both ended at the same count on the remaining search. The last completed iteration is the node field compared in the gate. Hard warm and cold had different CNT lines on 5,899 of 5,900 later plies. [Gate output](sol/job3/gates.txt)
3. **Prediction graded.** All three checks completed before the [prediction](sol/job3/prediction.txt) was pushed at `aae6c12169be6ea1647b04f18be9f837377c8539`. Aggregation started after the push.

## Prediction grades

A numeric guess survives when the exact ratio is within a factor of 1.5. A zero guess requires zero events in both arms. An undefined ratio kills a numeric guess.

| Counter | Ratio | Guess | Measured | Outcome |
|---|---|---:|---:|---|
| razor_taken | A/C | 1.05 | 1.1380 | survives |
| razor_taken | B/D | 1.00 | 0.9298 | survives |
| razor_taken | A/B | 0.735 | 0.8040 | survives |
| razor_taken | C/D | 0.70 | 0.6569 | survives |
| rfp_taken | A/C | 1.00 | 0.9353 | survives |
| rfp_taken | B/D | 0.98 | 0.9958 | survives |
| rfp_taken | A/B | 1.020 | 0.9628 | survives |
| rfp_taken | C/D | 1.00 | 1.0252 | survives |
| null_move_taken | A/C | 1.15 | 1.9609 | KILLED |
| null_move_taken | B/D | 1.05 | 1.3410 | survives |
| null_move_taken | A/B | 0.471 | 0.6511 | survives |
| null_move_taken | C/D | 0.43 | 0.4453 | survives |
| null_move_tested | A/C | 1.15 | 1.9471 | KILLED |
| null_move_tested | B/D | 1.05 | 1.4069 | survives |
| null_move_tested | A/B | 0.427 | 0.5846 | survives |
| null_move_tested | C/D | 0.39 | 0.4224 | survives |
| probcut_taken | A/C | 1.20 | 2.7403 | KILLED |
| probcut_taken | B/D | 1.08 | 1.4522 | survives |
| probcut_taken | A/B | 0.233 | 0.4595 | KILLED |
| probcut_taken | C/D | 0.21 | 0.2435 | survives |
| probcut_tested | A/C | 1.15 | 2.5968 | KILLED |
| probcut_tested | B/D | 1.08 | 1.4171 | survives |
| probcut_tested | A/B | 0.234 | 0.4598 | KILLED |
| probcut_tested | C/D | 0.22 | 0.2509 | survives |
| iir_no_tt_taken | A/C | 0.72 | 0.9072 | survives |
| iir_no_tt_taken | B/D | 0.84 | 0.8356 | survives |
| iir_no_tt_taken | A/B | 0.763 | 0.9186 | survives |
| iir_no_tt_taken | C/D | 0.89 | 0.8461 | survives |
| iir_tt_taken | A/C | 1.30 | 1.0854 | survives |
| iir_tt_taken | B/D | 1.15 | 0.8100 | survives |
| iir_tt_taken | A/B | 0.859 | 1.1013 | survives |
| iir_tt_taken | C/D | 0.76 | 0.8219 | survives |
| lmp_taken | A/C | 1.15 | 0.9735 | survives |
| lmp_taken | B/D | 1.07 | 0.9408 | survives |
| lmp_taken | A/B | 1.129 | 1.0549 | survives |
| lmp_taken | C/D | 1.05 | 1.0195 | survives |
| quiet_futility_taken | A/C | 1.10 | 1.1103 | survives |
| quiet_futility_taken | B/D | 1.05 | 0.9518 | survives |
| quiet_futility_taken | A/B | 0.796 | 0.9144 | survives |
| quiet_futility_taken | C/D | 0.76 | 0.7838 | survives |
| history_pruning_taken | A/C | 4.00 | 45.3058 | KILLED |
| history_pruning_taken | B/D | 1.55 | 16.4407 | KILLED |
| history_pruning_taken | A/B | 0.258 | 0.2219 | survives |
| history_pruning_taken | C/D | 0.10 | 0.0805 | survives |
| quiet_see_taken | A/C | 1.03 | 1.1341 | survives |
| quiet_see_taken | B/D | 1.02 | 0.9049 | survives |
| quiet_see_taken | A/B | 0.959 | 1.1584 | survives |
| quiet_see_taken | C/D | 0.95 | 0.9242 | survives |
| capture_futility_taken | A/C | zero | n/a | survives |
| capture_futility_taken | B/D | zero | n/a | survives |
| capture_futility_taken | A/B | zero | n/a | survives |
| capture_futility_taken | C/D | zero | n/a | survives |
| noisy_see_taken | A/C | 1.00 | 0.9177 | survives |
| noisy_see_taken | B/D | 1.00 | 0.8925 | survives |
| noisy_see_taken | A/B | 1.050 | 1.0797 | survives |
| noisy_see_taken | C/D | 1.05 | 1.0502 | survives |
| singular_taken | A/C | 1.75 | 2.4900 | survives |
| singular_taken | B/D | 1.25 | 1.2946 | survives |
| singular_taken | A/B | 0.560 | 0.7500 | survives |
| singular_taken | C/D | 0.40 | 0.3899 | survives |
| singular_double | A/C | 1.60 | 2.6132 | KILLED |
| singular_double | B/D | 1.25 | 1.2609 | survives |
| singular_double | A/B | 0.410 | 0.6332 | KILLED |
| singular_double | C/D | 0.32 | 0.3055 | survives |
| singular_negative | A/C | 1.70 | 3.3388 | KILLED |
| singular_negative | B/D | 1.25 | 1.6306 | survives |
| singular_negative | A/B | 0.272 | 0.4040 | survives |
| singular_negative | C/D | 0.20 | 0.1973 | survives |
| check_extension_taken | A/C | 1.02 | 1.1638 | survives |
| check_extension_taken | B/D | 1.00 | 1.0331 | survives |
| check_extension_taken | A/B | 0.918 | 0.9219 | survives |
| check_extension_taken | C/D | 0.90 | 0.8184 | survives |
| lmr_taken | A/C | 1.12 | 1.1782 | survives |
| lmr_taken | B/D | 1.06 | 1.0630 | survives |
| lmr_taken | A/B | 0.919 | 0.9839 | survives |
| lmr_taken | C/D | 0.87 | 0.8877 | survives |
| lmr_plies | A/C | 1.18 | 1.3228 | survives |
| lmr_plies | B/D | 1.08 | 1.1544 | survives |
| lmr_plies | A/B | 0.787 | 0.8350 | survives |
| lmr_plies | C/D | 0.72 | 0.7287 | survives |
| aspiration_taken | A/C | 0.80 | 0.2449 | KILLED |
| aspiration_taken | B/D | 0.90 | 0.3443 | KILLED |
| aspiration_taken | A/B | 3.378 | 2.6004 | survives |
| aspiration_taken | C/D | 3.80 | 3.6548 | survives |
| q_futility_taken | A/C | 1.00 | 0.9581 | survives |
| q_futility_taken | B/D | 1.00 | 0.9415 | survives |
| q_futility_taken | A/B | 0.820 | 0.9119 | survives |
| q_futility_taken | C/D | 0.82 | 0.8961 | survives |
| fail_low_bonus_taken | A/C | zero | n/a | survives |
| fail_low_bonus_taken | B/D | zero | n/a | survives |
| fail_low_bonus_taken | A/B | zero | n/a | survives |
| fail_low_bonus_taken | C/D | zero | n/a | survives |
| eval_swing_taken | A/C | zero | n/a | survives |
| eval_swing_taken | B/D | zero | n/a | survives |
| eval_swing_taken | A/B | zero | n/a | survives |
| eval_swing_taken | C/D | zero | n/a | survives |
| draw_jitter_taken | A/C | zero | n/a | survives |
| draw_jitter_taken | B/D | zero | n/a | survives |
| draw_jitter_taken | A/B | zero | n/a | survives |
| draw_jitter_taken | C/D | zero | n/a | survives |

13 KILLED, 87 survive.

Summed CNT lines: A 6000, B 6000, C 6000, D 6000.
Each arm matches the number and order of plies in games.txt. Rates use actual main plus qsearch nodes.

## Table 1

| Counter | A / 1k | B / 1k | C / 1k | D / 1k | A/C | B/D | A/B | C/D |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| razor_taken | 4.6040 | 5.7264 | 4.0456 | 6.1588 | 1.1380 | 0.9298 | 0.8040 | 0.6569 |
| rfp_taken | 244.8520 | 254.3032 | 261.7985 | 255.3663 | 0.9353 | 0.9958 | 0.9628 | 1.0252 |
| null_move_taken | 7.9879 | 12.2674 | 4.0736 | 9.1477 | 1.9609 | 1.3410 | 0.6511 | 0.4453 |
| null_move_tested | 10.2356 | 17.5099 | 5.2569 | 12.4457 | 1.9471 | 1.4069 | 0.5846 | 0.4224 |
| probcut_taken | 1.4166 | 3.0825 | 0.5170 | 2.1227 | 2.7403 | 1.4522 | 0.4595 | 0.2435 |
| probcut_tested | 1.7107 | 3.7205 | 0.6588 | 2.6254 | 2.5968 | 1.4171 | 0.4598 | 0.2509 |
| iir_no_tt_taken | 34.1268 | 37.1497 | 37.6171 | 44.4599 | 0.9072 | 0.8356 | 0.9186 | 0.8461 |
| iir_tt_taken | 1.0890 | 0.9888 | 1.0033 | 1.2207 | 1.0854 | 0.8100 | 1.1013 | 0.8219 |
| lmp_taken | 63.8961 | 60.5734 | 65.6343 | 64.3820 | 0.9735 | 0.9408 | 1.0549 | 1.0195 |
| quiet_futility_taken | 13.4746 | 14.7366 | 12.1357 | 15.4823 | 1.1103 | 0.9518 | 0.9144 | 0.7838 |
| history_pruning_taken | 2.8112 | 12.6664 | 0.0620 | 0.7704 | 45.3058 | 16.4407 | 0.2219 | 0.0805 |
| quiet_see_taken | 160.5337 | 138.5862 | 141.5484 | 153.1579 | 1.1341 | 0.9049 | 1.1584 | 0.9242 |
| capture_futility_taken | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | n/a |
| noisy_see_taken | 95.7624 | 88.6896 | 104.3528 | 99.3692 | 0.9177 | 0.8925 | 1.0797 | 1.0502 |
| singular_taken | 3.2314 | 4.3084 | 1.2977 | 3.3279 | 2.4900 | 1.2946 | 0.7500 | 0.3899 |
| singular_double | 1.0521 | 1.6616 | 0.4026 | 1.3177 | 2.6132 | 1.2609 | 0.6332 | 0.3055 |
| singular_negative | 0.4484 | 1.1098 | 0.1343 | 0.6806 | 3.3388 | 1.6306 | 0.4040 | 0.1973 |
| check_extension_taken | 11.6850 | 12.6751 | 10.0406 | 12.2693 | 1.1638 | 1.0331 | 0.9219 | 0.8184 |
| lmr_taken | 326.8567 | 332.2111 | 277.4148 | 312.5161 | 1.1782 | 1.0630 | 0.9839 | 0.8877 |
| lmr_plies | 731.4353 | 876.0105 | 552.9445 | 758.8452 | 1.3228 | 1.1544 | 0.8350 | 0.7287 |
| aspiration_taken | 0.2762 | 0.1062 | 1.1277 | 0.3086 | 0.2449 | 0.3443 | 2.6004 | 3.6548 |
| q_futility_taken | 87.5192 | 95.9753 | 91.3450 | 101.9379 | 0.9581 | 0.9415 | 0.9119 | 0.8961 |
| fail_low_bonus_taken | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | n/a |
| eval_swing_taken | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | n/a |
| draw_jitter_taken | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | n/a |

| Arm | Searches | Total nodes | Root depth median / min / max | Median actual nodes |
|---|---:|---:|---|---:|
| A | 6000 | 22579075 | 8 / 5 / 64 | 3330 |
| B | 6000 | 119980128 | 10 / 7 / 64 | 20000 |
| C | 6000 | 18436984 | 7 / 2 / 64 | 2812 |
| D | 6000 | 119980128 | 10 / 7 / 64 | 20000 |

## Table 2

| Counter | Plies | A / 1k | B / 1k | Searches per arm | A nodes | B nodes |
|---|---|---:|---:|---:|---:|---:|
| history_pruning_taken | 0 | 0.0239 | 0.4065 | 100 | 293374 | 2000000 |
| history_pruning_taken | 1–9 | 0.3847 | 2.6197 | 900 | 3192315 | 18000000 |
| history_pruning_taken | 10–29 | 1.4276 | 8.2989 | 2000 | 7603154 | 40000000 |
| history_pruning_taken | 30–59 | 4.4721 | 19.0028 | 3000 | 11490232 | 59980128 |
| lmr_taken | 0 | 273.6746 | 302.0935 | 100 | 293374 | 2000000 |
| lmr_taken | 1–9 | 314.8370 | 311.2148 | 900 | 3192315 | 18000000 |
| lmr_taken | 10–29 | 320.2837 | 324.0634 | 2000 | 7603154 | 40000000 |
| lmr_taken | 30–59 | 335.9033 | 344.9499 | 3000 | 11490232 | 59980128 |
| quiet_futility_taken | 0 | 6.8854 | 9.9320 | 100 | 293374 | 2000000 |
| quiet_futility_taken | 1–9 | 10.2600 | 11.9355 | 900 | 3192315 | 18000000 |
| quiet_futility_taken | 10–29 | 14.2974 | 15.4778 | 2000 | 7603154 | 40000000 |
| quiet_futility_taken | 30–59 | 13.9916 | 15.2430 | 3000 | 11490232 | 59980128 |
| lmp_taken | 0 | 74.2977 | 71.7235 | 100 | 293374 | 2000000 |
| lmp_taken | 1–9 | 68.7620 | 65.1484 | 900 | 3192315 | 18000000 |
| lmp_taken | 10–29 | 62.9943 | 60.2129 | 2000 | 7603154 | 40000000 |
| lmp_taken | 30–59 | 62.8753 | 59.0692 | 3000 | 11490232 | 59980128 |
| singular_taken | 0 | 0.7806 | 2.1200 | 100 | 293374 | 2000000 |
| singular_taken | 1–9 | 1.9102 | 2.7135 | 900 | 3192315 | 18000000 |
| singular_taken | 10–29 | 2.6553 | 3.5417 | 2000 | 7603154 | 40000000 |
| singular_taken | 30–59 | 4.0421 | 5.3712 | 3000 | 11490232 | 59980128 |

## Facts

- **Retaining tables changed history pruning most.** At the 2,000 soft budget it rose from 1,144 taken events in 18,436,984 cold nodes to 63,474 in 22,579,075 warm nodes. At the 20,000 hard budget it rose from 92,436 to 1,519,712 taken events with 119,980,128 nodes in each arm. The increases were 45.3058× and 16.4407× per node. In the warm arms, the rates rose from 0.0239 and 0.4065 per 1,000 on the opening position to 4.4721 and 19.0028 per 1,000 on plies 30–59. Table 2 gives the denominators.
- Retaining tables at the soft budget more than doubled the per-node rates for ProbCut cuts and positive singular extensions, and increased null-move cuts to 1.9609×. Aspiration retries per node fell with warm tables at both budgets, to 0.2449× at the soft budget and 0.3443× at the hard budget.
- The soft target produced more actual nodes with retained tables. Arm A's median was 3,330 nodes and root depth 8 versus 2,812 nodes and root depth 7 for C. The 8,000-node ceiling fired on 206 of 6,000 A searches and 16 of 6,000 C searches. The normal soft stop is checked at a completed iteration. The separate hard ceiling can interrupt an iteration, so the tables use actual CNT nodes and the retained UCI line provides the last reported root depth.
- Arm A generated 100 games from the first 100 rows of O. Python-chess 1.11.2 replayed all 6,000 moves and checked the first end condition. Ninety-nine ended at the 60-ply limit and one at threefold repetition on ply 60. All four arms searched the exact positions before those moves. Only A supplied the moves played. [Games](sol/job3/games.txt) · [Verification](sol/job3/game-verification.txt)

## Build, protocol and evidence

- Case A. GPT-6 (Codex), Linux x86_64. Both binaries came unchanged from Job 2, base `6b98f2170a3210e71beed04bbd2553972c253ed7` plus PC r15 patch SHA-256 `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`. The counting copy also used `count.patch.txt` SHA-256 `ff3c25aa634966aa62cd9ce75326a6c148d03b2c24eb36d279a00d68b7a75488`. Plain executable SHA-256 `9279d02c2ea8c42875ec83a55399aeb588b72a3ae13e8067969be2cee8219306`. Counting executable SHA-256 `906bf28e2afd7a694efb3897995ca292b9a922f636f6c22f311d5b9597371445`. CMake 4.2.3 Release, GCC 14.2.0, libstdc++ `6.0.33`, glibc 2.41, x86-64-v4, `FORGE_MATE_ALPHA_GUARD=1`. [Job 2 build record and PC20 definition](REPORT_sol_job2.md)
- The four arms used the counting binary with the unchanged PC20 settings, Threads 1, Hash 16 MiB, OwnBook false, one PV, and the built-in AL1 s198 net, weights source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. No external NNUE file. O was `forge-combo29/tests_kimi5_job4/first200.fens` at `8f316b85a04bd4f2dedd6e15eefe8b3a18f1832f`, blob `e967e8327ec2be34eaf6df7f1763fa13b00e6497`. Game-list SHA-256 `6d3343843f1bd6e9597f1e54ea64779fab78a1df64abb2431c749151e5a060a1`.
- A and B sent `ucinewgame` plus `isready` once per game. C and D did that before each search. All arms sent the original FEN and preceding moves. A and C used `go softnodes 2000`; B and D used `go nodes 20000`. Each arm's sidecar records every setting sent, binary hash, UCI engine ID, and start and end times. [Raw rows and metadata](sol/job3/raw) · [Clock stamps](sol/job3/stamps.txt)

From `forge-combo29/sol/job3`, the committed commands reproduce the readbacks and tables:

```sh
python3 verify_gates.py raw ../job2/raw games.txt
python3 summarize.py games.txt raw --prediction prediction.txt
```

The game driver reuses the Job 2 UCI reader. With python-chess 1.11.2 and the pinned O fixture, run `python3 run_games.py verify /path/to/O.fens games.txt` to recheck moves and game end reasons.

## Suspicions

Retained histories are a plausible contributor to the history-pruning increase. The experiment retains history and the transposition table together. The per-ply trend also changes the positions and the mix of moves available. Neither source is isolated here.

## What I did not do

No owner-PC run, active standalone v3 net, tuner run, match or Elo test. The 100 self-play traces supply positions for the four-arm comparison. The branch contains text evidence and replay tools.

## What I am not sure about

The warm/cold ratios may move under the PC's live network or other game distributions. This run does not estimate the effect of keeping history while clearing the hash, or the converse.

## Pre-commit readback

```text
M  forge-combo29/NOTES_sol.md
AM forge-combo29/REPORT_sol_job3.md
A  forge-combo29/sol/job3/game-verification.txt
A  forge-combo29/sol/job3/games-repeat10.txt
A  forge-combo29/sol/job3/games.txt
A  forge-combo29/sol/job3/gates.txt
A  forge-combo29/sol/job3/raw/A-repeat10.jsonl
A  forge-combo29/sol/job3/raw/A-repeat10.jsonl.meta
A  forge-combo29/sol/job3/raw/A-soft-warm.jsonl
A  forge-combo29/sol/job3/raw/A-soft-warm.jsonl.meta
A  forge-combo29/sol/job3/raw/B-hard-warm.jsonl
A  forge-combo29/sol/job3/raw/B-hard-warm.jsonl.meta
A  forge-combo29/sol/job3/raw/C-soft-cold.jsonl
A  forge-combo29/sol/job3/raw/C-soft-cold.jsonl.meta
A  forge-combo29/sol/job3/raw/D-hard-cold.jsonl
A  forge-combo29/sol/job3/raw/D-hard-cold.jsonl.meta
A  forge-combo29/sol/job3/run_games.py
A  forge-combo29/sol/job3/stamps.txt
A  forge-combo29/sol/job3/step0-count.raw.txt
A  forge-combo29/sol/job3/step0-plain.raw.txt
A  forge-combo29/sol/job3/step0.summary.txt
A  forge-combo29/sol/job3/summarize.py
A  forge-combo29/sol/job3/verify_gates.py
?? forge-combo29/sol/job2/__pycache__/
forge-combo29/sol/job3:
game-verification.txt
games-repeat10.txt
games.txt
gates.txt
prediction.txt
raw
run_games.py
stamps.txt
step0-count.raw.txt
step0-plain.raw.txt
step0.summary.txt
summarize.py
verify_gates.py

forge-combo29/sol/job3/raw:
A-repeat10.jsonl
A-repeat10.jsonl.meta
A-soft-warm.jsonl
A-soft-warm.jsonl.meta
B-hard-warm.jsonl
B-hard-warm.jsonl.meta
C-soft-cold.jsonl
C-soft-cold.jsonl.meta
D-hard-cold.jsonl
D-hard-cold.jsonl.meta
```

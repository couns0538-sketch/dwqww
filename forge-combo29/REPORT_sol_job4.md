# Sol — Job 4 Forge hash and worker-state isolation

1. **Step 0 met.** The unchanged plain build and the counting build with the two buttons each passed eight fresh-process pins. Defaults 312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517, PC20 278024 / 587276. Only the counting build advertised the two new buttons. [Plain raw](sol/job4/step0-plain.raw.txt) · [Counting raw](sol/job4/step0-count.raw.txt)
2. **Source check met.** In uninstrumented PC r15, `src/uci.cpp:386–389` makes `ucinewgame` stop the search, call `Searcher::clear()` and reset the UCI board. `src/search.cpp:3056–3059` clears the shared TT and calls `Worker::clear()` for each worker. Its implementation empties the evaluator cache, move and correction histories, counter moves, threat maps and search stack. Pawn history is conditional on compile-time and runtime switches. `src/search.cpp:1116–1137`.

   The existing `Clear Hash` button calls `Searcher::clear_hash()`, which clears the shared TT and each worker's evaluator cache. `clear_caches()` only calls `evaluator_.clear()`, which fills the pawn cache with empty entries. `src/uci.cpp:390–391,431–433`, `src/search.cpp:3044–3047`, `include/forge/search.hpp:474`, `src/eval.cpp:569–571`.

   The scratch patch calls each existing worker method through its new UCI button. `ClearWorkers` calls `clear()`. `ClearPawnCache` calls `clear_caches()`. Both preserve the shared TT. Counting copy with patch, `src/uci.cpp:367–370,433–441` and `src/search.cpp:3272–3278`. [Zero-fuzz patch](sol/job4/buttons.patch.txt)

3. **Known answers and controls met.**

   - A2, B2, C2 and D2 each matched 6,000/6,000 original Job 3 rows in position order, last-info nodes, bestmove and raw CNT bytes. [Exact baseline gate](sol/job4/baseline-gate.txt)
   - G equaled A2 on 6,000/6,000 rows with zero differences. The pawn-cache-only clearing control preserved the measured search behavior on this replay.
   - H equaled C2 on 6,000/6,000 rows with zero differences. Both buttons together reproduced the cold search path in the replay. [G and H control gate](sol/job4/control-gate.txt)
   - Before any new engine run, the six independent Job 3 common-depth ratios matched Opus to three decimals. In handoff order they were 1.222, 1.402, 0.993, 41.226, 0.636 and 0.704. The Job 3 source was the old counting binary with PC20 and built-in evaluation, 6,000 rows per arm, 22,579,075 A nodes and 18,436,984 C nodes. [Legacy gate](sol/job4/depth-mix-gate.txt)

4. **Prediction graded.** The [prediction](sol/job4/prediction.txt) was pushed alone at `eb2b9622f609be73130597d290998d33d59f4232` after all controls and before aggregation.

## Prediction grades

A numeric guess survives when the exact ratio is within a factor of 1.5. A zero guess requires zero events in both arms. An undefined ratio kills a numeric guess.

| Counter | Comparison | Mix | Guess | Measured | Outcome |
|---|---|---|---:|---:|---|
| history_pruning_taken | E/C2 | plain | 35.00 | 25.5779 | survives |
| history_pruning_taken | F/C2 | plain | 1.50 | 1.3016 | survives |
| history_pruning_taken | E/C2 | cold | 32.00 | 25.1120 | survives |
| history_pruning_taken | F/C2 | cold | 1.10 | 1.2427 | survives |
| history_pruning_taken | EH/D2 | plain | 12.00 | 13.8751 | survives |
| history_pruning_taken | FH/D2 | plain | 1.20 | 0.6835 | KILLED |
| history_pruning_taken | EH/D2 | cold | 11.00 | 13.7542 | survives |
| history_pruning_taken | FH/D2 | cold | 1.00 | 0.6687 | survives |
| null_move_taken | E/C2 | plain | 1.20 | 1.1670 | survives |
| null_move_taken | F/C2 | plain | 1.50 | 1.5280 | survives |
| null_move_taken | E/C2 | cold | 1.05 | 1.0636 | survives |
| null_move_taken | F/C2 | cold | 1.10 | 1.1819 | survives |
| null_move_taken | EH/D2 | plain | 1.12 | 1.0419 | survives |
| null_move_taken | FH/D2 | plain | 1.22 | 1.3539 | survives |
| null_move_taken | EH/D2 | cold | 1.03 | 1.0290 | survives |
| null_move_taken | FH/D2 | cold | 1.10 | 1.0957 | survives |
| probcut_taken | E/C2 | plain | 1.25 | 1.4936 | survives |
| probcut_taken | F/C2 | plain | 1.70 | 1.6749 | survives |
| probcut_taken | E/C2 | cold | 1.00 | 1.2707 | survives |
| probcut_taken | F/C2 | cold | 1.23 | 1.1554 | survives |
| probcut_taken | EH/D2 | plain | 1.10 | 1.1382 | survives |
| probcut_taken | FH/D2 | plain | 1.32 | 1.2874 | survives |
| probcut_taken | EH/D2 | cold | 1.02 | 1.1013 | survives |
| probcut_taken | FH/D2 | cold | 1.18 | 0.9788 | survives |
| singular_taken | E/C2 | plain | 1.15 | 1.4108 | survives |
| singular_taken | F/C2 | plain | 2.00 | 1.7929 | survives |
| singular_taken | E/C2 | cold | 0.95 | 1.0745 | survives |
| singular_taken | F/C2 | cold | 1.05 | 1.0485 | survives |
| singular_taken | EH/D2 | plain | 1.03 | 1.0960 | survives |
| singular_taken | FH/D2 | plain | 1.25 | 1.2205 | survives |
| singular_taken | EH/D2 | cold | 0.97 | 1.0166 | survives |
| singular_taken | FH/D2 | cold | 1.04 | 0.8708 | survives |
| iir_no_tt_taken | E/C2 | plain | 0.95 | 1.0576 | survives |
| iir_no_tt_taken | F/C2 | plain | 0.80 | 0.9100 | survives |
| iir_no_tt_taken | E/C2 | cold | 0.90 | 0.9949 | survives |
| iir_no_tt_taken | F/C2 | cold | 0.72 | 0.7934 | survives |
| iir_no_tt_taken | EH/D2 | plain | 0.98 | 0.9531 | survives |
| iir_no_tt_taken | FH/D2 | plain | 0.86 | 0.8671 | survives |
| iir_no_tt_taken | EH/D2 | cold | 0.95 | 0.9419 | survives |
| iir_no_tt_taken | FH/D2 | cold | 0.79 | 0.7923 | survives |
| lmr_taken | E/C2 | plain | 1.05 | 0.9984 | survives |
| lmr_taken | F/C2 | plain | 1.04 | 1.1313 | survives |
| lmr_taken | E/C2 | cold | 0.92 | 0.8678 | survives |
| lmr_taken | F/C2 | cold | 0.73 | 0.8098 | survives |
| lmr_taken | EH/D2 | plain | 1.02 | 0.9625 | survives |
| lmr_taken | FH/D2 | plain | 1.02 | 1.0942 | survives |
| lmr_taken | EH/D2 | cold | 0.95 | 0.9312 | survives |
| lmr_taken | FH/D2 | cold | 0.85 | 0.8606 | survives |
| aspiration_taken | E/C2 | plain | 0.95 | 0.5616 | KILLED |
| aspiration_taken | F/C2 | plain | 0.40 | 0.5730 | survives |
| aspiration_taken | E/C2 | cold | 0.90 | 0.4395 | KILLED |
| aspiration_taken | F/C2 | cold | 0.42 | 0.3202 | survives |
| aspiration_taken | EH/D2 | plain | 0.92 | 0.4868 | KILLED |
| aspiration_taken | FH/D2 | plain | 0.42 | 0.5009 | survives |
| aspiration_taken | EH/D2 | cold | 0.88 | 0.4458 | KILLED |
| aspiration_taken | FH/D2 | cold | 0.44 | 0.3049 | survives |

5 KILLED, 51 survive.

Summed CNT lines: A2 6000, C2 6000, E 6000, F 6000, G 6000, H 6000, B2 6000, D2 6000, EH 6000, FH 6000.
Each arm matches the 6,000 positions in games.txt. Rates use actual main plus qsearch nodes.

| Arm | CNT lines | Main nodes | Total nodes |
|---|---:|---:|---:|
| A2 | 6000 | 13643438 | 22579075 |
| C2 | 6000 | 9849490 | 18436984 |
| E | 6000 | 10395016 | 18968065 |
| F | 6000 | 11891834 | 20466757 |
| G | 6000 | 13643438 | 22579075 |
| H | 6000 | 9849490 | 18436984 |
| B2 | 6000 | 72324153 | 119980128 |
| D2 | 6000 | 68050593 | 119980128 |
| EH | 6000 | 68668141 | 119980128 |
| FH | 6000 | 71885678 | 119980128 |

## Table 1. Plain rates

| Counter | A2 / 1k | C2 / 1k | E / 1k | F / 1k | E/C2 | F/C2 | A2/C2 | Interaction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| razor_taken | 4.6040 | 4.0456 | 4.7282 | 4.2317 | 1.1687 | 1.0460 | 1.1380 | 0.9309 |
| rfp_taken | 244.8520 | 261.7985 | 264.6905 | 255.7706 | 1.0110 | 0.9770 | 0.9353 | 0.9469 |
| null_move_taken | 7.9879 | 4.0736 | 4.7538 | 6.2246 | 1.1670 | 1.5280 | 1.9609 | 1.0997 |
| null_move_tested | 10.2356 | 5.2569 | 6.3261 | 7.7678 | 1.2034 | 1.4776 | 1.9471 | 1.0950 |
| probcut_taken | 1.4166 | 0.5170 | 0.7721 | 0.8658 | 1.4936 | 1.6749 | 2.7403 | 1.0954 |
| probcut_tested | 1.7107 | 0.6588 | 0.9676 | 1.0658 | 1.4688 | 1.6178 | 2.5968 | 1.0928 |
| iir_no_tt_taken | 34.1268 | 37.6171 | 39.7824 | 34.2319 | 1.0576 | 0.9100 | 0.9072 | 0.9427 |
| iir_tt_taken | 1.0890 | 1.0033 | 0.8757 | 1.1383 | 0.8728 | 1.1346 | 1.0854 | 1.0960 |
| lmp_taken | 63.8961 | 65.6343 | 65.0357 | 64.1813 | 0.9909 | 0.9779 | 0.9735 | 1.0047 |
| quiet_futility_taken | 13.4746 | 12.1357 | 14.1614 | 12.2647 | 1.1669 | 1.0106 | 1.1103 | 0.9415 |
| history_pruning_taken | 2.8112 | 0.0620 | 1.5871 | 0.0808 | 25.5779 | 1.3016 | 45.3058 | 1.3608 |
| quiet_see_taken | 160.5337 | 141.5484 | 157.5165 | 132.5666 | 1.1128 | 0.9365 | 1.1341 | 1.0882 |
| capture_futility_taken | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | n/a |
| noisy_see_taken | 95.7624 | 104.3528 | 101.4174 | 98.2321 | 0.9719 | 0.9413 | 0.9177 | 1.0031 |
| singular_taken | 3.2314 | 1.2977 | 1.8308 | 2.3267 | 1.4108 | 1.7929 | 2.4900 | 0.9844 |
| singular_double | 1.0521 | 0.4026 | 0.5990 | 0.7262 | 1.4877 | 1.8036 | 2.6132 | 0.9739 |
| singular_negative | 0.4484 | 0.1343 | 0.2327 | 0.2606 | 1.7328 | 1.9403 | 3.3388 | 0.9931 |
| check_extension_taken | 11.6850 | 10.0406 | 10.8734 | 11.0247 | 1.0829 | 1.0980 | 1.1638 | 0.9787 |
| lmr_taken | 326.8567 | 277.4148 | 276.9694 | 313.8492 | 0.9984 | 1.1313 | 1.1782 | 1.0431 |
| lmr_plies | 731.4353 | 552.9445 | 582.6843 | 657.6124 | 1.0538 | 1.1893 | 1.3228 | 1.0555 |
| aspiration_taken | 0.2762 | 1.1277 | 0.6334 | 0.6462 | 0.5616 | 0.5730 | 0.2449 | 0.7611 |
| q_futility_taken | 87.5192 | 91.3450 | 97.6708 | 85.1525 | 1.0693 | 0.9322 | 0.9581 | 0.9612 |
| fail_low_bonus_taken | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | n/a |
| eval_swing_taken | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | n/a |
| draw_jitter_taken | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | n/a |

| Counter | B2 / 1k | D2 / 1k | EH / 1k | FH / 1k | EH/D2 | FH/D2 | B2/D2 | Interaction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| razor_taken | 5.7264 | 6.1588 | 6.1327 | 5.9112 | 0.9958 | 0.9598 | 0.9298 | 0.9729 |
| rfp_taken | 254.3032 | 255.3663 | 262.9415 | 251.8171 | 1.0297 | 0.9861 | 0.9958 | 0.9808 |
| null_move_taken | 12.2674 | 9.1477 | 9.5311 | 12.3852 | 1.0419 | 1.3539 | 1.3410 | 0.9506 |
| null_move_tested | 17.5099 | 12.4457 | 13.9445 | 16.5199 | 1.1204 | 1.3274 | 1.4069 | 0.9460 |
| probcut_taken | 3.0825 | 2.1227 | 2.4160 | 2.7327 | 1.1382 | 1.2874 | 1.4522 | 0.9911 |
| probcut_tested | 3.7205 | 2.6254 | 3.0264 | 3.2693 | 1.1527 | 1.2453 | 1.4171 | 0.9872 |
| iir_no_tt_taken | 37.1497 | 44.4599 | 42.3739 | 38.5534 | 0.9531 | 0.8671 | 0.8356 | 1.0110 |
| iir_tt_taken | 0.9888 | 1.2207 | 0.9368 | 1.1437 | 0.7674 | 0.9369 | 0.8100 | 1.1266 |
| lmp_taken | 60.5734 | 64.3820 | 62.1948 | 61.2023 | 0.9660 | 0.9506 | 0.9408 | 1.0245 |
| quiet_futility_taken | 14.7366 | 15.4823 | 15.8195 | 14.6064 | 1.0218 | 0.9434 | 0.9518 | 0.9874 |
| history_pruning_taken | 12.6664 | 0.7704 | 10.6898 | 0.5266 | 13.8751 | 0.6835 | 16.4407 | 1.7336 |
| quiet_see_taken | 138.5862 | 153.1579 | 138.5669 | 137.3712 | 0.9047 | 0.8969 | 0.9049 | 1.1151 |
| capture_futility_taken | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | n/a |
| noisy_see_taken | 88.6896 | 99.3692 | 92.5595 | 92.1766 | 0.9315 | 0.9276 | 0.8925 | 1.0330 |
| singular_taken | 4.3084 | 3.3279 | 3.6474 | 4.0617 | 1.0960 | 1.2205 | 1.2946 | 0.9678 |
| singular_double | 1.6616 | 1.3177 | 1.4671 | 1.5275 | 1.1133 | 1.1592 | 1.2609 | 0.9770 |
| singular_negative | 1.1098 | 0.6806 | 0.9030 | 0.8751 | 1.3268 | 1.2858 | 1.6306 | 0.9558 |
| check_extension_taken | 12.6751 | 12.2693 | 12.5046 | 12.4827 | 1.0192 | 1.0174 | 1.0331 | 0.9963 |
| lmr_taken | 332.2111 | 312.5161 | 300.7824 | 341.9528 | 0.9625 | 1.0942 | 1.0630 | 1.0094 |
| lmr_plies | 876.0105 | 758.8452 | 763.6241 | 850.1648 | 1.0063 | 1.1203 | 1.1544 | 1.0240 |
| aspiration_taken | 0.1062 | 0.3086 | 0.1502 | 0.1546 | 0.4868 | 0.5009 | 0.3443 | 1.4118 |
| q_futility_taken | 95.9753 | 101.9379 | 105.3608 | 94.6691 | 1.0336 | 0.9287 | 0.9415 | 0.9809 |
| fail_low_bonus_taken | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | n/a |
| eval_swing_taken | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | n/a |
| draw_jitter_taken | 0.0000 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | n/a |

## Table 2. Ratios on the cold main-node depth mix

Source events per main node at each depth are weighted by cold main nodes at that depth, then divided by all cold events. Depths with zero source main nodes are skipped.

| Counter | E/C2 | F/C2 | A2/C2 | Interaction |
|---|---:|---:|---:|---:|
| history_pruning_taken | 25.1120 | 1.2427 | 41.2263 | 1.3210 |
| null_move_taken | 1.0636 | 1.1819 | 1.2216 | 0.9718 |
| probcut_taken | 1.2707 | 1.1554 | 1.4019 | 0.9548 |
| singular_taken | 1.0745 | 1.0485 | 0.9929 | 0.8813 |
| iir_no_tt_taken | 0.9949 | 0.7934 | 0.7037 | 0.8915 |
| lmr_taken | 0.8678 | 0.8098 | 0.6359 | 0.9049 |
| aspiration_taken | 0.4395 | 0.3202 | 0.0587 | 0.4172 |

| Counter | EH/D2 | FH/D2 | B2/D2 | Interaction |
|---|---:|---:|---:|---:|
| history_pruning_taken | 13.7542 | 0.6687 | 15.2276 | 1.6556 |
| null_move_taken | 1.0290 | 1.0957 | 1.0772 | 0.9554 |
| probcut_taken | 1.1013 | 0.9788 | 1.0677 | 0.9905 |
| singular_taken | 1.0166 | 0.8708 | 0.8666 | 0.9790 |
| iir_no_tt_taken | 0.9419 | 0.7923 | 0.7575 | 1.0151 |
| lmr_taken | 0.9312 | 0.8606 | 0.8097 | 1.0103 |
| aspiration_taken | 0.4458 | 0.3049 | 0.1862 | 1.3699 |

## Table 3. Main-node depth shares and history pruning by depth

| Arm | Main-node share d1–8 (%) | History pruning per 1k main nodes d1–5 |
|---|---|---|
| A2 | 57.272 / 20.114 / 11.418 / 5.811 / 2.863 / 1.577 / 0.690 / 0.207 | 4.417 / 8.554 / 2.944 / 0.861 / 0.366 |
| C2 | 64.635 / 18.895 / 9.192 / 4.303 / 1.863 / 0.820 / 0.256 / 0.033 | 0.160 / 0.063 / 0.010 / 0.000 / 0.000 |
| E | 62.954 / 19.457 / 9.645 / 4.457 / 2.043 / 1.029 / 0.354 / 0.057 | 3.038 / 4.554 / 0.880 / 0.201 / 0.089 |
| F | 61.541 / 19.192 / 10.132 / 5.019 / 2.322 / 1.186 / 0.469 / 0.115 | 0.191 / 0.101 / 0.013 / 0.008 / 0.018 |
| G | 57.272 / 20.114 / 11.418 / 5.811 / 2.863 / 1.577 / 0.690 / 0.207 | 4.417 / 8.554 / 2.944 / 0.861 / 0.366 |
| H | 64.635 / 18.895 / 9.192 / 4.303 / 1.863 / 0.820 / 0.256 / 0.033 | 0.160 / 0.063 / 0.010 / 0.000 / 0.000 |
| B2 | 57.531 / 17.606 / 10.722 / 6.038 / 3.442 / 2.226 / 1.285 / 0.651 | 12.648 / 33.970 / 37.569 / 37.707 / 24.523 |
| D2 | 60.513 / 17.554 / 10.091 / 5.514 / 2.956 / 1.760 / 0.941 / 0.422 | 1.662 / 1.635 / 0.566 / 0.121 / 0.048 |
| EH | 60.319 / 17.642 / 10.176 / 5.354 / 2.914 / 1.837 / 1.012 / 0.464 | 11.762 / 32.212 / 33.042 / 30.314 / 18.595 |
| FH | 57.725 / 17.501 / 10.685 / 6.193 / 3.480 / 2.157 / 1.200 / 0.591 | 1.146 / 0.980 / 0.364 / 0.086 / 0.032 |

All 20 history-pruning depth rates for A2, B2, C2 and D2 match the Job 3 known answers.

## Reading question

`HistoryPruneDepth` defaults to 3 in PC r15, and the predicate checks the candidate's `lmr_depth`. That value is `max(0, depth - reduction(quiet, depth, move_count))`. A reduction of 1 at node depth 4 or 2 at depth 5 makes the candidate depth 3. The meaningful prerequisites still include a quiet prunable move that gives no check, and a history value below the threshold. The counter credits the event at the local node depth after any IIR. `src/search.cpp:116,2122,2126–2131,2143–2146` in plain PC r15, and `src/search.cpp:2332–2333` in the counting copy.

## Facts

- History pruning tracked retained worker state. Against cold, keeping worker state only raised its per-node rate 25.5779× soft and 13.8751× hard. Keeping only TT state yielded 1.3016× and 0.6835×. On the matching cold main-node depth mix, the worker-only ratios were 25.1120× and 13.7542×. The TT-only ratios were 1.2427× and 0.6687×.
- Both states together changed history-pruning rates more than the product of the single-state ratios in this replay. The interaction was 1.3608× soft and 1.7336× hard in the plain rates, and 1.3210× and 1.6556× on the cold depth mix.
- Both single-state arms reduced aspiration retries. Their plain soft rates relative to cold were 0.5616× with worker state kept and 0.5730× with TT state kept. The hard ratios were 0.4868× and 0.5009×. The warm soft arm was 0.2449× plain and 0.0587× on the cold main-node depth mix.
- Depth adjustment materially changed the soft comparison. With both states retained, positive singular extensions went from 2.4900× cold in the plain rate to 0.9929× on the cold mix, and late-move reductions went from 1.1782× to 0.6359×. The 20 history-pruning depth rates in the four baseline arms matched Opus's Job 3 readback.
- Main-node buckets use entry depth. Event buckets use the local depth at the event site, which can change after IIR. The common-mix table is the requested reweighting using those recorded buckets. Counting patch, `src/search.cpp:1923–1924,2203–2215,2332–2333`.

## Build, protocol and evidence

- Case A. GPT-6 (Codex), Linux x86_64. PC r15 on base `6b98f2170a3210e71beed04bbd2553972c253ed7`, PC r15 patch SHA-256 `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`, Job 2 counter patch `ff3c25aa634966aa62cd9ce75326a6c148d03b2c24eb36d279a00d68b7a75488`, and new buttons patch `fb219e959e7e988cbc10ae1c235ce1894c226a06c57c61cde3669dfc0f4d9183`. GCC 14.2.0, CMake 4.2.3 Release, libstdc++ `6.0.33`, glibc 2.41, x86-64-v4, and `FORGE_MATE_ALPHA_GUARD=1`. Plain SHA-256 `9279d02c2ea8c42875ec83a55399aeb588b72a3ae13e8067969be2cee8219306`. Counting-with-buttons SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. [PC20 options and original build record](REPORT_sol_job2.md)
- All ten measured arms used the buttons counting build and built-in AL1 s198 evaluation, weights source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`, with no external net file. PC20, Threads 1, Hash 16 MiB, one PV, OwnBook false. The exact 6,000 positions and prior moves came from Job 3's 100-game file, SHA-256 `6d3343843f1bd6e9597f1e54ea64779fab78a1df64abb2431c749151e5a060a1`. No reply move was played in these replays. [Job 3 games](sol/job3/games.txt)
- Before each game every arm sent `ucinewgame`, then waited for `isready`. Before each ply every arm sent its listed command or button sequence, then waited for `isready` before setting the recorded position and moves. A2/B2 kept both states, C2/D2 sent `ucinewgame`, E/EH sent `Clear Hash`, F/FH sent `ClearWorkers`, G sent `ClearPawnCache`, H sent `ClearWorkers` then `Clear Hash`. A2/C2/E/F/G/H used `go softnodes 2000`; B2/D2/EH/FH used `go nodes 20000`. Each raw file has a sidecar with the build and exact settings. [Raw rows and metadata](sol/job4/raw) · [Clock stamps](sol/job4/stamps.txt)

From `forge-combo29/sol/job4`, run the committed readback commands:

```sh
python3 summarize.py old-gate ../job3/games.txt ../job3/raw
python3 verify_gates.py baselines raw --job3-raw ../job3/raw
python3 verify_gates.py controls raw
python3 summarize.py tables ../job3/games.txt raw --prediction prediction.txt
```

## Suspicions

The history-pruning rate follows retained worker state in this protocol. Within that state, move history is the direct input to the threshold. The reset also clears corrections, counter moves and other worker state, so their contributions remain unresolved.

## What I did not do

No owner-PC run, active standalone v3 net, tuning, timed match or Elo measurement. The buttons exist in a scratch build and in a unified text patch.

## What I am not sure about

The reported interactions describe states that evolved under different reset policies. Their effect sizes may change with the PC's active net, game mix or tuned settings.

## Pre-commit readback

```text
M  forge-combo29/NOTES_sol.md
AM forge-combo29/REPORT_sol_job4.md
A  forge-combo29/sol/job4/baseline-gate.txt
A  forge-combo29/sol/job4/buttons.patch.txt
A  forge-combo29/sol/job4/control-gate.txt
A  forge-combo29/sol/job4/depth-mix-gate.txt
A  forge-combo29/sol/job4/raw/A2.jsonl
A  forge-combo29/sol/job4/raw/A2.jsonl.meta
A  forge-combo29/sol/job4/raw/B2.jsonl
A  forge-combo29/sol/job4/raw/B2.jsonl.meta
A  forge-combo29/sol/job4/raw/C2.jsonl
A  forge-combo29/sol/job4/raw/C2.jsonl.meta
A  forge-combo29/sol/job4/raw/D2.jsonl
A  forge-combo29/sol/job4/raw/D2.jsonl.meta
A  forge-combo29/sol/job4/raw/E.jsonl
A  forge-combo29/sol/job4/raw/E.jsonl.meta
A  forge-combo29/sol/job4/raw/EH.jsonl
A  forge-combo29/sol/job4/raw/EH.jsonl.meta
A  forge-combo29/sol/job4/raw/F.jsonl
A  forge-combo29/sol/job4/raw/F.jsonl.meta
A  forge-combo29/sol/job4/raw/FH.jsonl
A  forge-combo29/sol/job4/raw/FH.jsonl.meta
A  forge-combo29/sol/job4/raw/G.jsonl
A  forge-combo29/sol/job4/raw/G.jsonl.meta
A  forge-combo29/sol/job4/raw/H.jsonl
A  forge-combo29/sol/job4/raw/H.jsonl.meta
A  forge-combo29/sol/job4/run_buttons.py
A  forge-combo29/sol/job4/stamps.txt
A  forge-combo29/sol/job4/step0-count.raw.txt
A  forge-combo29/sol/job4/step0-plain.raw.txt
A  forge-combo29/sol/job4/step0.summary.txt
A  forge-combo29/sol/job4/summarize.py
A  forge-combo29/sol/job4/verify_gates.py
?? forge-combo29/sol/job2/__pycache__/
forge-combo29/sol/job4:
baseline-gate.txt
buttons.patch.txt
control-gate.txt
depth-mix-gate.txt
prediction.txt
raw
run_buttons.py
stamps.txt
step0-count.raw.txt
step0-plain.raw.txt
step0.summary.txt
summarize.py
verify_gates.py

forge-combo29/sol/job4/raw:
A2.jsonl
A2.jsonl.meta
B2.jsonl
B2.jsonl.meta
C2.jsonl
C2.jsonl.meta
D2.jsonl
D2.jsonl.meta
E.jsonl
E.jsonl.meta
EH.jsonl
EH.jsonl.meta
F.jsonl
F.jsonl.meta
FH.jsonl
FH.jsonl.meta
G.jsonl
G.jsonl.meta
H.jsonl
H.jsonl.meta
```

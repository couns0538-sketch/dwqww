# Sol — Job 6 sensitivity of 40 Forge settings in warm and cold replay

1. **Step 0 met.** The unchanged Job 4 counting binary passed the eight fresh-process pins. Defaults 312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517, PC20 278024 / 587276. All 45 starts, ranges and one-step values matched the handoff before the runs. Five were untuned controls. No setting was skipped. For DrawJitter, CaptureFutilityBase, FailLowContinuationBonus and EvalSwingMult the downward value was below the allowed range, so each uses only the upward arm. The start-value file gives the observed value and the exact PC20 or UCI line for every setting. [Step 0 raw](sol/job6/step0-count.raw.txt) · [All 45 start values and origins](sol/job6/settings.tsv)

2. **Known answers 1 to 5 met.**
   - Both new warm baselines matched Job 5 on 1,800/1,800 rows each. The new cold-soft baseline matched the first 1,800 Job 3 C rows exactly. [Baseline gates](sol/job6/base-gate.txt)
   - The 16 repeated Job 5 warm-soft arms each matched 1,800/1,800 rows, 28,800 matches in total. [Warm-repeat gate](sol/job6/repeat-gate.txt)
   - All ten untuned setting-direction controls matched their respective bases on 1,800/1,800 rows in both warm and cold soft searches, 36,000 matches in total. [Untuned controls](sol/job6/controls-gate.txt)
   - For each of the 86 setting-directions, the warm and cold opening-only runs matched 30/30 first plies, 2,580 matches in total. This gave the opening gate without measuring the full A and B blocks before the forecast. The same equality held on all 86 full-run opening readbacks. Identity includes the raw CNT string and all stable fields in the retained UCI last-info line. Time and NPS vary by run. [Opening-only gate](sol/job6/openings-gate.txt) · [Full opening readback](sol/job6/full-openings-gate.txt)

3. **Prediction graded.** I pushed the [prediction](sol/job6/prediction.txt) alone at `bf91d7aa29e68fab43edb110e98d358f2ac675d5` after the gates. The remaining warm-soft arms ran first, then the remaining cold-soft arms, then the 60 new warm-hard arms. The 16 Job 5 hard arms completed the hard comparison. All required arms completed, with 1,800 positions per arm. [Read-counts and actual node totals](sol/job6/read-counts.txt)

## Prediction grades

A numerical guess survives within a factor of 1.5. A zero guess requires zero changed moves.

| Setting | Protocol | Guess % | Observed % | Outcome |
|---|---|---:|---:|---|
| DrawJitter | warm-soft | 12.00 | 0.0000 | KILLED |
| DrawJitter | cold-soft | 1.50 | 0.0000 | KILLED |
| LmrQuietBase | warm-soft | 38.00 | 39.8611 | survives |
| LmrQuietBase | cold-soft | 24.00 | 25.6944 | survives |
| LmrQuietDivisor | warm-soft | 38.00 | 39.5833 | survives |
| LmrQuietDivisor | cold-soft | 20.00 | 27.5833 | survives |
| LmrNoisyBase | warm-soft | 32.00 | 21.5833 | survives |
| LmrNoisyBase | cold-soft | 13.00 | 0.3056 | KILLED |
| LmrNoisyDivisor | warm-soft | 33.00 | 27.0278 | survives |
| LmrNoisyDivisor | cold-soft | 14.00 | 0.8056 | KILLED |
| NullMoveMinDepth | warm-soft | 35.00 | 20.5000 | KILLED |
| NullMoveMinDepth | cold-soft | 13.00 | 3.6667 | KILLED |
| NullMoveBase | warm-soft | 9.00 | 25.2778 | KILLED |
| NullMoveBase | cold-soft | 1.30 | 0.2778 | KILLED |
| NullMoveDepthDivisor | warm-soft | 4.00 | 24.5556 | KILLED |
| NullMoveDepthDivisor | cold-soft | 0.50 | 0.2778 | KILLED |
| NullMoveEvalDivisor | warm-soft | 3.00 | 0.8056 | KILLED |
| NullMoveEvalDivisor | cold-soft | 0.30 | 0.0000 | KILLED |
| RfpDepth | warm-soft | 1.50 | 2.5000 | KILLED |
| RfpDepth | cold-soft | 0.20 | 0.0000 | KILLED |
| RfpMargin | warm-soft | 38.75 | 38.7500 | survives |
| RfpMargin | cold-soft | 24.00 | 36.2500 | KILLED |
| RfpImproving | warm-soft | 35.00 | 40.0556 | survives |
| RfpImproving | cold-soft | 16.00 | 37.3889 | KILLED |
| RazorDepth | warm-soft | 12.00 | 26.8056 | KILLED |
| RazorDepth | cold-soft | 1.20 | 2.1944 | KILLED |
| RazorBase | warm-soft | 18.00 | 28.6389 | KILLED |
| RazorBase | cold-soft | 2.60 | 0.5556 | KILLED |
| RazorMultiplier | warm-soft | 18.00 | 29.1667 | KILLED |
| RazorMultiplier | cold-soft | 2.50 | 0.8611 | KILLED |
| FutilityDepth | warm-soft | 1.20 | 1.6667 | survives |
| FutilityDepth | cold-soft | 0.15 | 0.0000 | KILLED |
| FutilityBase | warm-soft | 31.00 | 24.2500 | survives |
| FutilityBase | cold-soft | 9.00 | 0.1944 | KILLED |
| FutilityMultiplier | warm-soft | 28.00 | 26.5000 | survives |
| FutilityMultiplier | cold-soft | 6.50 | 0.2222 | KILLED |
| LmpBase | warm-soft | 38.00 | 40.8333 | survives |
| LmpBase | cold-soft | 20.00 | 35.1944 | KILLED |
| HistoryPruneDepth | warm-soft | 0.31 | 0.3056 | survives |
| HistoryPruneDepth | cold-soft | 0.17 | 0.0000 | KILLED |
| HistoryPruneMultiplier | warm-soft | 21.81 | 21.8056 | survives |
| HistoryPruneMultiplier | cold-soft | 4.00 | 0.0278 | KILLED |
| SeeQuietMultiplier | warm-soft | 37.00 | 36.7500 | survives |
| SeeQuietMultiplier | cold-soft | 18.00 | 10.9444 | KILLED |
| SeeNoisyMultiplier | warm-soft | 36.00 | 27.6389 | survives |
| SeeNoisyMultiplier | cold-soft | 15.00 | 1.0833 | KILLED |
| SingularDepth | warm-soft | 25.00 | 39.3333 | KILLED |
| SingularDepth | cold-soft | 3.80 | 27.1667 | KILLED |
| SingularMargin | warm-soft | 15.00 | 39.8333 | KILLED |
| SingularMargin | cold-soft | 1.50 | 8.7222 | KILLED |
| IirDepth | warm-soft | 39.00 | 40.8889 | survives |
| IirDepth | cold-soft | 25.00 | 43.9167 | KILLED |
| ProbcutDepth | warm-soft | 29.00 | 34.5000 | survives |
| ProbcutDepth | cold-soft | 5.00 | 2.8333 | KILLED |
| ProbcutMargin | warm-soft | 29.69 | 29.6944 | survives |
| ProbcutMargin | cold-soft | 6.00 | 0.4444 | KILLED |
| QsFutilityMargin | warm-soft | 36.00 | 38.3333 | survives |
| QsFutilityMargin | cold-soft | 17.00 | 14.6944 | survives |
| AspirationDelta | warm-soft | 30.00 | 40.2778 | survives |
| AspirationDelta | cold-soft | 8.00 | 29.3611 | KILLED |
| HistoryBonusQuadratic | warm-soft | 38.81 | 38.8056 | survives |
| HistoryBonusQuadratic | cold-soft | 14.00 | 5.8056 | KILLED |
| HistoryBonusLinear | warm-soft | 38.75 | 38.7500 | survives |
| HistoryBonusLinear | cold-soft | 13.00 | 10.9444 | survives |
| HistoryBonusMax | warm-soft | 11.31 | 11.3056 | survives |
| HistoryBonusMax | cold-soft | 0.80 | 0.0278 | KILLED |
| LmrHistoryDivisor | warm-soft | 37.17 | 37.1667 | survives |
| LmrHistoryDivisor | cold-soft | 12.00 | 1.2500 | KILLED |
| CheckExtensionDepth | warm-soft | 38.00 | 39.5000 | survives |
| CheckExtensionDepth | cold-soft | 21.00 | 14.8889 | survives |
| LmrCutoffThreshold | warm-soft | 22.00 | 39.2778 | KILLED |
| LmrCutoffThreshold | cold-soft | 1.80 | 26.7500 | KILLED |
| MaterialCorrectionWeight | warm-soft | 30.00 | 38.9722 | survives |
| MaterialCorrectionWeight | cold-soft | 4.00 | 10.0833 | KILLED |
| CaptureFutilityBase | warm-soft | 28.00 | 28.8889 | survives |
| CaptureFutilityBase | cold-soft | 8.00 | 0.3333 | KILLED |
| FailLowContinuationBonus | warm-soft | 30.00 | 39.2222 | survives |
| FailLowContinuationBonus | cold-soft | 7.00 | 16.3889 | KILLED |
| EvalSwingMult | warm-soft | 33.00 | 39.9444 | survives |
| EvalSwingMult | cold-soft | 9.00 | 47.7222 | KILLED |

47 KILLED, 33 survive, 0 ungraded.

## Table 1. All tuned settings

Pooled comparisons include all in-range directions. One-sided settings use 1,800 searches and two-sided settings use 3,600. Node and counter rates use actual main plus qsearch nodes.

| Setting | Warm soft changed | Cold soft changed | Warm hard changed | Warm soft/hard | Cold nodes/base | Counter | Cold/base counter rate ratio | Cold counter / 1k | Base cold counter / 1k |
|---|---|---|---|---:|---:|---|---:|---:|---:|
| DrawJitter | 0/1800 (0.0000%) | 0/1800 (0.0000%) | 0/1800 (0.0000%) | n/a | 1.0000 | draw_jitter_taken | n/a (base zero) | 0.0000 | 0.0000 |
| LmrQuietBase | 1435/3600 (39.8611%) | 925/3600 (25.6944%) | 1205/3600 (33.4722%) | 1.1909 | 1.0095 | lmr_plies | 0.9962 | 553.6115 | 555.7151 |
| LmrQuietDivisor | 1425/3600 (39.5833%) | 993/3600 (27.5833%) | 1186/3600 (32.9444%) | 1.2015 | 1.0066 | lmr_plies | 0.9930 | 551.8282 | 555.7151 |
| LmrNoisyBase | 777/3600 (21.5833%) | 11/3600 (0.3056%) | 1091/3600 (30.3056%) | 0.7122 | 1.0006 | lmr_plies | 1.0001 | 555.7787 | 555.7151 |
| LmrNoisyDivisor | 973/3600 (27.0278%) | 29/3600 (0.8056%) | 1200/3600 (33.3333%) | 0.8108 | 1.0010 | lmr_plies | 0.9998 | 555.6259 | 555.7151 |
| NullMoveMinDepth | 738/3600 (20.5000%) | 132/3600 (3.6667%) | 900/3600 (25.0000%) | 0.8200 | 1.0045 | null_move_taken | 0.8046 | 3.0155 | 3.7479 |
| NullMoveBase | 910/3600 (25.2778%) | 10/3600 (0.2778%) | 1215/3600 (33.7500%) | 0.7490 | 1.0004 | null_move_taken | 1.0017 | 3.7543 | 3.7479 |
| NullMoveDepthDivisor | 884/3600 (24.5556%) | 10/3600 (0.2778%) | 1159/3600 (32.1944%) | 0.7627 | 1.0005 | null_move_taken | 1.0010 | 3.7518 | 3.7479 |
| NullMoveEvalDivisor | 29/3600 (0.8056%) | 0/3600 (0.0000%) | 840/3600 (23.3333%) | 0.0345 | 1.0000 | null_move_taken | 1.0000 | 3.7479 | 3.7479 |
| RfpDepth | 90/3600 (2.5000%) | 0/3600 (0.0000%) | 928/3600 (25.7778%) | 0.0970 | 1.0000 | rfp_taken | 1.0000 | 265.0985 | 265.0996 |
| RfpMargin | 1395/3600 (38.7500%) | 1305/3600 (36.2500%) | 1211/3600 (33.6389%) | 1.1519 | 1.0039 | rfp_taken | 0.9986 | 264.7345 | 265.0996 |
| RfpImproving | 1442/3600 (40.0556%) | 1346/3600 (37.3889%) | 1203/3600 (33.4167%) | 1.1987 | 1.0045 | rfp_taken | 0.9975 | 264.4486 | 265.0996 |
| RazorDepth | 965/3600 (26.8056%) | 79/3600 (2.1944%) | 1083/3600 (30.0833%) | 0.8910 | 1.0008 | razor_taken | 0.9307 | 4.0714 | 4.3743 |
| RazorBase | 1031/3600 (28.6389%) | 20/3600 (0.5556%) | 1148/3600 (31.8889%) | 0.8981 | 1.0010 | razor_taken | 1.0015 | 4.3811 | 4.3743 |
| RazorMultiplier | 1050/3600 (29.1667%) | 31/3600 (0.8611%) | 1145/3600 (31.8056%) | 0.9170 | 1.0014 | razor_taken | 1.0065 | 4.4030 | 4.3743 |
| FutilityDepth | 60/3600 (1.6667%) | 0/3600 (0.0000%) | 722/3600 (20.0556%) | 0.0831 | 1.0000 | quiet_futility_taken | 1.0000 | 11.4602 | 11.4603 |
| FutilityBase | 873/3600 (24.2500%) | 7/3600 (0.1944%) | 1166/3600 (32.3889%) | 0.7487 | 1.0004 | quiet_futility_taken | 1.0017 | 11.4796 | 11.4603 |
| FutilityMultiplier | 954/3600 (26.5000%) | 8/3600 (0.2222%) | 1158/3600 (32.1667%) | 0.8238 | 0.9999 | quiet_futility_taken | 1.0009 | 11.4706 | 11.4603 |
| LmpBase | 1470/3600 (40.8333%) | 1267/3600 (35.1944%) | 1229/3600 (34.1389%) | 1.1961 | 1.0148 | lmp_taken | 0.9864 | 65.4132 | 66.3145 |
| HistoryPruneDepth | 11/3600 (0.3056%) | 0/3600 (0.0000%) | 760/3600 (21.1111%) | 0.0145 | 1.0000 | history_pruning_taken | 1.0000 | 0.0632 | 0.0632 |
| HistoryPruneMultiplier | 785/3600 (21.8056%) | 1/3600 (0.0278%) | 1112/3600 (30.8889%) | 0.7059 | 0.9999 | history_pruning_taken | 1.0474 | 0.0662 | 0.0632 |
| SeeQuietMultiplier | 1323/3600 (36.7500%) | 394/3600 (10.9444%) | 1207/3600 (33.5278%) | 1.0961 | 0.9990 | quiet_see_taken | 0.9650 | 131.0725 | 135.8212 |
| SeeNoisyMultiplier | 995/3600 (27.6389%) | 39/3600 (1.0833%) | 1128/3600 (31.3333%) | 0.8821 | 0.9996 | noisy_see_taken | 1.0133 | 110.1298 | 108.6820 |
| SingularDepth | 1416/3600 (39.3333%) | 978/3600 (27.1667%) | 1239/3600 (34.4167%) | 1.1429 | 0.9923 | singular_taken | 1.4495 | 1.9333 | 1.3338 |
| SingularMargin | 1434/3600 (39.8333%) | 314/3600 (8.7222%) | 1195/3600 (33.1944%) | 1.2000 | 1.0021 | singular_taken | 1.0082 | 1.3447 | 1.3338 |
| IirDepth | 1472/3600 (40.8889%) | 1581/3600 (43.9167%) | 1216/3600 (33.7778%) | 1.2105 | 1.0138 | iir_no_tt_taken | 1.3973 | 52.8518 | 37.8233 |
| ProbcutDepth | 1242/3600 (34.5000%) | 102/3600 (2.8333%) | 1183/3600 (32.8611%) | 1.0499 | 1.0028 | probcut_taken | 1.9564 | 0.8809 | 0.4503 |
| ProbcutMargin | 1069/3600 (29.6944%) | 16/3600 (0.4444%) | 1172/3600 (32.5556%) | 0.9121 | 1.0009 | probcut_taken | 1.0083 | 0.4540 | 0.4503 |
| QsFutilityMargin | 1380/3600 (38.3333%) | 529/3600 (14.6944%) | 1162/3600 (32.2778%) | 1.1876 | 1.0078 | q_futility_taken | 1.0012 | 84.6536 | 84.5524 |
| AspirationDelta | 1450/3600 (40.2778%) | 1057/3600 (29.3611%) | 1202/3600 (33.3889%) | 1.2063 | 1.0093 | aspiration_taken | 0.9954 | 1.0957 | 1.1008 |
| HistoryBonusQuadratic | 1397/3600 (38.8056%) | 209/3600 (5.8056%) | 1198/3600 (33.2778%) | 1.1661 | 1.0009 | history_pruning_taken | 1.0534 | 0.0666 | 0.0632 |
| HistoryBonusLinear | 1395/3600 (38.7500%) | 394/3600 (10.9444%) | 1196/3600 (33.2222%) | 1.1664 | 1.0043 | history_pruning_taken | 1.0142 | 0.0641 | 0.0632 |
| HistoryBonusMax | 407/3600 (11.3056%) | 1/3600 (0.0278%) | 1161/3600 (32.2500%) | 0.3506 | 1.0000 | history_pruning_taken | 1.0000 | 0.0632 | 0.0632 |
| LmrHistoryDivisor | 1338/3600 (37.1667%) | 45/3600 (1.2500%) | 1211/3600 (33.6389%) | 1.1049 | 1.0018 | lmr_plies | 1.0002 | 555.8373 | 555.7151 |
| CheckExtensionDepth | 1422/3600 (39.5000%) | 536/3600 (14.8889%) | 1196/3600 (33.2222%) | 1.1890 | 0.9978 | check_extension_taken | 1.3110 | 16.0222 | 12.2212 |
| LmrCutoffThreshold | 1414/3600 (39.2778%) | 963/3600 (26.7500%) | 1215/3600 (33.7500%) | 1.1638 | 1.0176 | lmr_plies | 1.0063 | 559.2205 | 555.7151 |
| MaterialCorrectionWeight | 1403/3600 (38.9722%) | 363/3600 (10.0833%) | 1202/3600 (33.3889%) | 1.1672 | 0.9962 | none | n/a | n/a | n/a |
| CaptureFutilityBase | 520/1800 (28.8889%) | 6/1800 (0.3333%) | 565/1800 (31.3889%) | 0.9204 | 0.9984 | capture_futility_taken | n/a (base zero) | 4.1274 | 0.0000 |
| FailLowContinuationBonus | 706/1800 (39.2222%) | 295/1800 (16.3889%) | 587/1800 (32.6111%) | 1.2027 | 1.0045 | fail_low_bonus_taken | n/a (base zero) | 44.1578 | 0.0000 |
| EvalSwingMult | 719/1800 (39.9444%) | 859/1800 (47.7222%) | 613/1800 (34.0556%) | 1.1729 | 0.9960 | eval_swing_taken | n/a (base zero) | 365.4436 | 0.0000 |

## Table 2. Cold-soft sensitivity ranking, lowest first

| Setting | Cold soft changed | Warm soft changed |
|---|---|---|
| DrawJitter | 0/1800 (0.0000%) | 0/1800 (0.0000%) |
| NullMoveEvalDivisor | 0/3600 (0.0000%) | 29/3600 (0.8056%) |
| RfpDepth | 0/3600 (0.0000%) | 90/3600 (2.5000%) |
| FutilityDepth | 0/3600 (0.0000%) | 60/3600 (1.6667%) |
| HistoryPruneDepth | 0/3600 (0.0000%) | 11/3600 (0.3056%) |
| HistoryPruneMultiplier | 1/3600 (0.0278%) | 785/3600 (21.8056%) |
| HistoryBonusMax | 1/3600 (0.0278%) | 407/3600 (11.3056%) |
| FutilityBase | 7/3600 (0.1944%) | 873/3600 (24.2500%) |
| FutilityMultiplier | 8/3600 (0.2222%) | 954/3600 (26.5000%) |
| NullMoveBase | 10/3600 (0.2778%) | 910/3600 (25.2778%) |
| NullMoveDepthDivisor | 10/3600 (0.2778%) | 884/3600 (24.5556%) |
| LmrNoisyBase | 11/3600 (0.3056%) | 777/3600 (21.5833%) |
| CaptureFutilityBase | 6/1800 (0.3333%) | 520/1800 (28.8889%) |
| ProbcutMargin | 16/3600 (0.4444%) | 1069/3600 (29.6944%) |
| RazorBase | 20/3600 (0.5556%) | 1031/3600 (28.6389%) |
| LmrNoisyDivisor | 29/3600 (0.8056%) | 973/3600 (27.0278%) |
| RazorMultiplier | 31/3600 (0.8611%) | 1050/3600 (29.1667%) |
| SeeNoisyMultiplier | 39/3600 (1.0833%) | 995/3600 (27.6389%) |
| LmrHistoryDivisor | 45/3600 (1.2500%) | 1338/3600 (37.1667%) |
| RazorDepth | 79/3600 (2.1944%) | 965/3600 (26.8056%) |
| ProbcutDepth | 102/3600 (2.8333%) | 1242/3600 (34.5000%) |
| NullMoveMinDepth | 132/3600 (3.6667%) | 738/3600 (20.5000%) |
| HistoryBonusQuadratic | 209/3600 (5.8056%) | 1397/3600 (38.8056%) |
| SingularMargin | 314/3600 (8.7222%) | 1434/3600 (39.8333%) |
| MaterialCorrectionWeight | 363/3600 (10.0833%) | 1403/3600 (38.9722%) |
| SeeQuietMultiplier | 394/3600 (10.9444%) | 1323/3600 (36.7500%) |
| HistoryBonusLinear | 394/3600 (10.9444%) | 1395/3600 (38.7500%) |
| QsFutilityMargin | 529/3600 (14.6944%) | 1380/3600 (38.3333%) |
| CheckExtensionDepth | 536/3600 (14.8889%) | 1422/3600 (39.5000%) |
| FailLowContinuationBonus | 295/1800 (16.3889%) | 706/1800 (39.2222%) |
| LmrQuietBase | 925/3600 (25.6944%) | 1435/3600 (39.8611%) |
| LmrCutoffThreshold | 963/3600 (26.7500%) | 1414/3600 (39.2778%) |
| SingularDepth | 978/3600 (27.1667%) | 1416/3600 (39.3333%) |
| LmrQuietDivisor | 993/3600 (27.5833%) | 1425/3600 (39.5833%) |
| AspirationDelta | 1057/3600 (29.3611%) | 1450/3600 (40.2778%) |
| LmpBase | 1267/3600 (35.1944%) | 1470/3600 (40.8333%) |
| RfpMargin | 1305/3600 (36.2500%) | 1395/3600 (38.7500%) |
| RfpImproving | 1346/3600 (37.3889%) | 1442/3600 (40.0556%) |
| IirDepth | 1581/3600 (43.9167%) | 1472/3600 (40.8889%) |
| EvalSwingMult | 859/1800 (47.7222%) | 719/1800 (39.9444%) |

Below 2% cold-soft (19): DrawJitter, LmrNoisyBase, LmrNoisyDivisor, NullMoveBase, NullMoveDepthDivisor, NullMoveEvalDivisor, RfpDepth, RazorBase, RazorMultiplier, FutilityDepth, FutilityBase, FutilityMultiplier, HistoryPruneDepth, HistoryPruneMultiplier, SeeNoisyMultiplier, ProbcutMargin, HistoryBonusMax, LmrHistoryDivisor, CaptureFutilityBase.

Below 5% warm-soft (5): DrawJitter, NullMoveEvalDivisor, RfpDepth, FutilityDepth, HistoryPruneDepth.

## Table 3. Untuned control identity

| Control | Direction | Warm soft equal | Cold soft equal | First differences (up to five per protocol) |
|---|---|---|---|---|
| QsSeeMargin | minus | 1800/1800 | 1800/1800 |  |
| QsSeeMargin | plus | 1800/1800 | 1800/1800 |  |
| CaptureFutilityMultiplier | minus | 1800/1800 | 1800/1800 |  |
| CaptureFutilityMultiplier | plus | 1800/1800 | 1800/1800 |  |
| CaptureFutilityDepth | minus | 1800/1800 | 1800/1800 |  |
| CaptureFutilityDepth | plus | 1800/1800 | 1800/1800 |  |
| AspFailHighMaxReduce | minus | 1800/1800 | 1800/1800 |  |
| AspFailHighMaxReduce | plus | 1800/1800 | 1800/1800 |  |
| EvalSwingMax | minus | 1800/1800 | 1800/1800 |  |
| EvalSwingMax | plus | 1800/1800 | 1800/1800 |  |


## Facts

- Nineteen of 40 tuned settings changed fewer than 2% of cold-soft bestmoves. Five of 40 changed fewer than 5% warm: DrawJitter, NullMoveEvalDivisor, RfpDepth, FutilityDepth and HistoryPruneDepth. The largest cold-soft responses were EvalSwingMult `859/1800` (47.7222%), IirDepth `1581/3600` (43.9167%) and RfpImproving `1346/3600` (37.3889%). Both thresholds and the complete ordering are in Table 2.
- SingularDepth had the largest hard-budget fraction (1,239/3,600, 34.4167%). IirDepth had the largest defined warm-soft/hard ratio (1.2105). None exceeded 1.5. DrawJitter had no hard-budget bestmove changes (0/1,800), but two last-info node counts and seven CNT rows differed.
- Three zero-cold-bestmove settings, DrawJitter, HistoryPruneDepth and NullMoveEvalDivisor, also preserved both the last-info node count and the full CNT string in every cold comparison. Cold FutilityDepth preserved every bestmove but changed 34 last-info node counts and 35 CNT rows. Cold RfpDepth preserved every bestmove but changed five node counts and five CNT rows.
- Warm DrawJitter changed no bestmoves and no last-info node counts. At search 585, game 10 ply 44, it incremented the depth-2 draw-jitter counter once with 1,527 reported nodes and bestmove `c7d6` in both runs. This is a counted path effect with identical reported move and node count. [Warm variant](sol/job6/raw/DrawJitter-plus-warm-soft.jsonl) · [Warm baseline](sol/job6/raw/base-warm-soft.jsonl)
- The history setting pairs illustrate why both reset protocols matter. HistoryPruneMultiplier changed 785/3,600 warm-soft recommendations and 1/3,600 cold-soft recommendations. LmrHistoryDivisor changed 1,338/3,600 warm soft and 45/3,600 cold soft. Each test reset warm tables only between games and cold tables before each search, using identical recorded moves.
- Where a cold baseline counter was zero, Table 1 reports the variant's absolute rate beside an undefined ratio. For example, EvalSwingMult generated 365.4436 updates per 1,000 cold nodes after its one upward step. The node denominator for every ratio is the engine's actual credited main plus quiescence nodes.

## Build, settings and evidence

- Case A. GPT-6 (Codex), Linux x86_64. Unchanged Job 4 counting executable SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`, PC r15 from base `6b98f2170a3210e71beed04bbd2553972c253ed7` with the recorded PC, count and buttons patches, GCC 14.2.0, CMake 4.2.3 Release, libstdc++ `6.0.33`, glibc 2.41, x86-64-v4 and `FORGE_MATE_ALPHA_GUARD=1`. [Job 4 build details](REPORT_sol_job4.md)
- Built-in AL1 s198 weights source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`, PC20, Threads 1, Hash 16 MiB, OwnBook false, one PV, no external net. Each variant sent exactly one override after the PC20 settings and kept the acknowledgment lines. Reset buttons were unused. The arm sidecars record the executable, settings, protocol and timestamps. [PC20 recipe](REPORT_sol_job2.md) · [Full raw rows and sidecars](sol/job6/raw)
- First 30 of Job 3's games, 1,800 positions, full file SHA-256 `6d3343843f1bd6e9597f1e54ea64779fab78a1df64abb2431c749151e5a060a1`. Warm used `ucinewgame` then `isready` per game. Cold did so before every search. All arms replayed the original FEN and the recorded preceding moves. The warm-soft, cold-soft and warm-hard bases used 6,753,665, 5,523,343 and 36,000,000 actual nodes respectively. [Game list](sol/job3/games.txt) · [Clock stamps](sol/job6/stamps.txt)

From `forge-combo29/sol/job6`, these commands reproduce the readbacks and tables:

```sh
for gate in bases repeat controls openings full-openings; do
  python3 verify_gates.py "$gate" --job3 ../job3/raw --job5 ../job5/raw
done
python3 summarize.py ../job3/games.txt raw --settings settings.tsv --job5-raw ../job5/raw --prediction prediction.txt
```

## Suspicions

Warm recommendations can diverge through retained search state even when the cold effect of a single step is rare. The warm and cold fractions establish that difference for this replay. A larger warm fraction still permits multiple mechanisms involving the TT, histories, move ordering and within-search learning.

## What I did not do

No owner-PC runs, active standalone v3 net, tune update, timed match or Elo test. These variants supplied recommendations for fixed positions. All later replay moves came from the recorded game list.

## What I am not sure about

The live PC network, different replay data or larger steps may move the threshold lists. The fractions do not give the sign of a strength effect.

## Pre-commit readback

```text
M  forge-combo29/NOTES_sol.md
AM forge-combo29/REPORT_sol_job6.md
A  forge-combo29/sol/job6/base-gate.txt
A  forge-combo29/sol/job6/block-A-run.txt
A  forge-combo29/sol/job6/block-B-run.txt
A  forge-combo29/sol/job6/block-C-run.txt
A  forge-combo29/sol/job6/controls-gate.txt
A  forge-combo29/sol/job6/controls-run.txt
A  forge-combo29/sol/job6/full-openings-gate.txt
A  forge-combo29/sol/job6/opening-raw/AspFailHighMaxReduce-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/AspFailHighMaxReduce-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/AspFailHighMaxReduce-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/AspFailHighMaxReduce-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/AspFailHighMaxReduce-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/AspFailHighMaxReduce-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/AspFailHighMaxReduce-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/AspFailHighMaxReduce-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/AspirationDelta-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/AspirationDelta-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/AspirationDelta-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/AspirationDelta-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/AspirationDelta-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/AspirationDelta-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/AspirationDelta-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/AspirationDelta-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityMultiplier-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityMultiplier-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityMultiplier-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityMultiplier-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityMultiplier-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityMultiplier-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityMultiplier-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CaptureFutilityMultiplier-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CheckExtensionDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CheckExtensionDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CheckExtensionDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CheckExtensionDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CheckExtensionDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CheckExtensionDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/CheckExtensionDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/CheckExtensionDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/DrawJitter-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/DrawJitter-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/DrawJitter-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/DrawJitter-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/EvalSwingMax-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/EvalSwingMax-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/EvalSwingMax-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/EvalSwingMax-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/EvalSwingMax-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/EvalSwingMax-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/EvalSwingMax-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/EvalSwingMax-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/EvalSwingMult-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/EvalSwingMult-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/EvalSwingMult-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/EvalSwingMult-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FailLowContinuationBonus-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FailLowContinuationBonus-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FailLowContinuationBonus-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FailLowContinuationBonus-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FutilityBase-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FutilityBase-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FutilityBase-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FutilityBase-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FutilityBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FutilityBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FutilityBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FutilityBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FutilityDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FutilityDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FutilityDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FutilityDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FutilityDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FutilityDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FutilityDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FutilityDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FutilityMultiplier-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FutilityMultiplier-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FutilityMultiplier-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FutilityMultiplier-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FutilityMultiplier-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FutilityMultiplier-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/FutilityMultiplier-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/FutilityMultiplier-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryBonusLinear-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryBonusLinear-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryBonusLinear-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryBonusLinear-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryBonusLinear-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryBonusLinear-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryBonusLinear-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryBonusLinear-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryBonusMax-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryBonusMax-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryBonusMax-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryBonusMax-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryBonusMax-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryBonusMax-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryBonusMax-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryBonusMax-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryBonusQuadratic-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryBonusQuadratic-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryBonusQuadratic-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryBonusQuadratic-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryBonusQuadratic-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryBonusQuadratic-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryBonusQuadratic-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryBonusQuadratic-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryPruneDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryPruneDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryPruneDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryPruneDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryPruneDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryPruneDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryPruneDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryPruneDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryPruneMultiplier-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryPruneMultiplier-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryPruneMultiplier-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryPruneMultiplier-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryPruneMultiplier-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryPruneMultiplier-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/HistoryPruneMultiplier-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/HistoryPruneMultiplier-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/IirDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/IirDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/IirDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/IirDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/IirDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/IirDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/IirDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/IirDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmpBase-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmpBase-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmpBase-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmpBase-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmpBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmpBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmpBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmpBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrCutoffThreshold-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrCutoffThreshold-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrCutoffThreshold-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrCutoffThreshold-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrCutoffThreshold-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrCutoffThreshold-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrCutoffThreshold-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrCutoffThreshold-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrHistoryDivisor-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrHistoryDivisor-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrHistoryDivisor-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrHistoryDivisor-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrHistoryDivisor-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrHistoryDivisor-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrHistoryDivisor-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrHistoryDivisor-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrNoisyBase-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrNoisyBase-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrNoisyBase-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrNoisyBase-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrNoisyBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrNoisyBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrNoisyBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrNoisyBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrNoisyDivisor-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrNoisyDivisor-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrNoisyDivisor-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrNoisyDivisor-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrNoisyDivisor-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrNoisyDivisor-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrNoisyDivisor-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrNoisyDivisor-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrQuietBase-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrQuietBase-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrQuietBase-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrQuietBase-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrQuietBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrQuietBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrQuietBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrQuietBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrQuietDivisor-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrQuietDivisor-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrQuietDivisor-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrQuietDivisor-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrQuietDivisor-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrQuietDivisor-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/LmrQuietDivisor-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/LmrQuietDivisor-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/MaterialCorrectionWeight-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/MaterialCorrectionWeight-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/MaterialCorrectionWeight-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/MaterialCorrectionWeight-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/MaterialCorrectionWeight-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/MaterialCorrectionWeight-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/MaterialCorrectionWeight-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/MaterialCorrectionWeight-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveBase-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveBase-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveBase-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveBase-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveDepthDivisor-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveDepthDivisor-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveDepthDivisor-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveDepthDivisor-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveDepthDivisor-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveDepthDivisor-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveDepthDivisor-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveDepthDivisor-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveEvalDivisor-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveEvalDivisor-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveEvalDivisor-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveEvalDivisor-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveEvalDivisor-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveEvalDivisor-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveEvalDivisor-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveEvalDivisor-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveMinDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveMinDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveMinDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveMinDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveMinDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveMinDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/NullMoveMinDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/NullMoveMinDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/ProbcutDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/ProbcutDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/ProbcutDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/ProbcutDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/ProbcutDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/ProbcutDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/ProbcutDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/ProbcutDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/ProbcutMargin-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/ProbcutMargin-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/ProbcutMargin-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/ProbcutMargin-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/ProbcutMargin-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/ProbcutMargin-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/ProbcutMargin-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/ProbcutMargin-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/QsFutilityMargin-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/QsFutilityMargin-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/QsFutilityMargin-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/QsFutilityMargin-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/QsFutilityMargin-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/QsFutilityMargin-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/QsFutilityMargin-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/QsFutilityMargin-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/QsSeeMargin-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/QsSeeMargin-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/QsSeeMargin-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/QsSeeMargin-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/QsSeeMargin-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/QsSeeMargin-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/QsSeeMargin-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/QsSeeMargin-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RazorBase-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RazorBase-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RazorBase-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RazorBase-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RazorBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RazorBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RazorBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RazorBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RazorDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RazorDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RazorDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RazorDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RazorDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RazorDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RazorDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RazorDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RazorMultiplier-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RazorMultiplier-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RazorMultiplier-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RazorMultiplier-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RazorMultiplier-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RazorMultiplier-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RazorMultiplier-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RazorMultiplier-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RfpDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RfpDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RfpDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RfpDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RfpDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RfpDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RfpDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RfpDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RfpImproving-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RfpImproving-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RfpImproving-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RfpImproving-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RfpImproving-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RfpImproving-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RfpImproving-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RfpImproving-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RfpMargin-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RfpMargin-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RfpMargin-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RfpMargin-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RfpMargin-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RfpMargin-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/RfpMargin-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/RfpMargin-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SeeNoisyMultiplier-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SeeNoisyMultiplier-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SeeNoisyMultiplier-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SeeNoisyMultiplier-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SeeNoisyMultiplier-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SeeNoisyMultiplier-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SeeNoisyMultiplier-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SeeNoisyMultiplier-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SeeQuietMultiplier-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SeeQuietMultiplier-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SeeQuietMultiplier-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SeeQuietMultiplier-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SeeQuietMultiplier-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SeeQuietMultiplier-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SeeQuietMultiplier-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SeeQuietMultiplier-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SingularDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SingularDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SingularDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SingularDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SingularDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SingularDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SingularDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SingularDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SingularMargin-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SingularMargin-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SingularMargin-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SingularMargin-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SingularMargin-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SingularMargin-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/opening-raw/SingularMargin-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/opening-raw/SingularMargin-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/openings-gate.txt
A  forge-combo29/sol/job6/openings-run.txt
A  forge-combo29/sol/job6/raw/AspFailHighMaxReduce-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/AspFailHighMaxReduce-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/AspFailHighMaxReduce-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/AspFailHighMaxReduce-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/AspFailHighMaxReduce-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/AspFailHighMaxReduce-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/AspFailHighMaxReduce-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/AspFailHighMaxReduce-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/AspirationDelta-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/AspirationDelta-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/AspirationDelta-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/AspirationDelta-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/AspirationDelta-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/AspirationDelta-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/AspirationDelta-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/AspirationDelta-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/AspirationDelta-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/AspirationDelta-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/AspirationDelta-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/AspirationDelta-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CaptureFutilityBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/CaptureFutilityBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CaptureFutilityBase-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/CaptureFutilityBase-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/CaptureFutilityBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/CaptureFutilityBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CaptureFutilityDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/CaptureFutilityDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CaptureFutilityDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/CaptureFutilityDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CaptureFutilityDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/CaptureFutilityDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CaptureFutilityDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/CaptureFutilityDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CaptureFutilityMultiplier-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/CaptureFutilityMultiplier-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CaptureFutilityMultiplier-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/CaptureFutilityMultiplier-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CaptureFutilityMultiplier-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/CaptureFutilityMultiplier-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CaptureFutilityMultiplier-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/CaptureFutilityMultiplier-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CheckExtensionDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/CheckExtensionDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CheckExtensionDepth-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/CheckExtensionDepth-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/CheckExtensionDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/CheckExtensionDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CheckExtensionDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/CheckExtensionDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/CheckExtensionDepth-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/CheckExtensionDepth-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/CheckExtensionDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/CheckExtensionDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/DrawJitter-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/DrawJitter-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/DrawJitter-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/DrawJitter-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/DrawJitter-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/DrawJitter-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/EvalSwingMax-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/EvalSwingMax-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/EvalSwingMax-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/EvalSwingMax-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/EvalSwingMax-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/EvalSwingMax-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/EvalSwingMax-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/EvalSwingMax-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/EvalSwingMult-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/EvalSwingMult-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/EvalSwingMult-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/EvalSwingMult-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/EvalSwingMult-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/EvalSwingMult-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FailLowContinuationBonus-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/FailLowContinuationBonus-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FailLowContinuationBonus-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/FailLowContinuationBonus-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/FailLowContinuationBonus-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/FailLowContinuationBonus-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityBase-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/FutilityBase-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityBase-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/FutilityBase-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityBase-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/FutilityBase-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/FutilityBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityBase-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/FutilityBase-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/FutilityBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/FutilityDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityDepth-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/FutilityDepth-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/FutilityDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/FutilityDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityDepth-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/FutilityDepth-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/FutilityDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityMultiplier-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/FutilityMultiplier-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityMultiplier-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/FutilityMultiplier-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityMultiplier-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/FutilityMultiplier-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityMultiplier-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/FutilityMultiplier-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityMultiplier-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/FutilityMultiplier-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/FutilityMultiplier-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/FutilityMultiplier-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryBonusLinear-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryBonusLinear-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryBonusLinear-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryBonusLinear-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryBonusLinear-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryBonusLinear-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryBonusLinear-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryBonusLinear-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryBonusMax-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryBonusMax-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryBonusMax-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryBonusMax-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryBonusMax-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryBonusMax-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryBonusMax-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryBonusMax-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryBonusQuadratic-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryBonusQuadratic-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryBonusQuadratic-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryBonusQuadratic-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryBonusQuadratic-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryBonusQuadratic-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryBonusQuadratic-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryBonusQuadratic-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryPruneDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryPruneDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryPruneDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryPruneDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryPruneDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryPruneDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryPruneDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryPruneDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryPruneMultiplier-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryPruneMultiplier-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryPruneMultiplier-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryPruneMultiplier-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryPruneMultiplier-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryPruneMultiplier-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/HistoryPruneMultiplier-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/HistoryPruneMultiplier-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/IirDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/IirDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/IirDepth-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/IirDepth-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/IirDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/IirDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/IirDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/IirDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/IirDepth-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/IirDepth-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/IirDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/IirDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmpBase-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmpBase-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmpBase-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/LmpBase-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/LmpBase-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmpBase-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmpBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmpBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmpBase-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/LmpBase-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/LmpBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmpBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrCutoffThreshold-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrCutoffThreshold-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrCutoffThreshold-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/LmrCutoffThreshold-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrCutoffThreshold-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrCutoffThreshold-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrCutoffThreshold-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrCutoffThreshold-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrCutoffThreshold-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/LmrCutoffThreshold-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrCutoffThreshold-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrCutoffThreshold-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrHistoryDivisor-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrHistoryDivisor-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrHistoryDivisor-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrHistoryDivisor-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrHistoryDivisor-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrHistoryDivisor-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrHistoryDivisor-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrHistoryDivisor-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrNoisyBase-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrNoisyBase-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrNoisyBase-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/LmrNoisyBase-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrNoisyBase-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrNoisyBase-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrNoisyBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrNoisyBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrNoisyBase-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/LmrNoisyBase-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrNoisyBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrNoisyBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrNoisyDivisor-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrNoisyDivisor-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrNoisyDivisor-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/LmrNoisyDivisor-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrNoisyDivisor-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrNoisyDivisor-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrNoisyDivisor-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrNoisyDivisor-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrNoisyDivisor-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/LmrNoisyDivisor-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrNoisyDivisor-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrNoisyDivisor-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrQuietBase-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrQuietBase-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrQuietBase-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/LmrQuietBase-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrQuietBase-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrQuietBase-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrQuietBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrQuietBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrQuietBase-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/LmrQuietBase-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrQuietBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrQuietBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrQuietDivisor-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrQuietDivisor-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrQuietDivisor-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/LmrQuietDivisor-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrQuietDivisor-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrQuietDivisor-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrQuietDivisor-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrQuietDivisor-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrQuietDivisor-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/LmrQuietDivisor-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/LmrQuietDivisor-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/LmrQuietDivisor-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/MaterialCorrectionWeight-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/MaterialCorrectionWeight-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/MaterialCorrectionWeight-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/MaterialCorrectionWeight-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/MaterialCorrectionWeight-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/MaterialCorrectionWeight-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/MaterialCorrectionWeight-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/MaterialCorrectionWeight-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/MaterialCorrectionWeight-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/MaterialCorrectionWeight-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/MaterialCorrectionWeight-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/MaterialCorrectionWeight-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveBase-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveBase-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveBase-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/NullMoveBase-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveBase-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveBase-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveBase-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/NullMoveBase-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveDepthDivisor-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveDepthDivisor-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveDepthDivisor-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/NullMoveDepthDivisor-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveDepthDivisor-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveDepthDivisor-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveDepthDivisor-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveDepthDivisor-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveDepthDivisor-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/NullMoveDepthDivisor-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveDepthDivisor-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveDepthDivisor-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveEvalDivisor-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveEvalDivisor-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveEvalDivisor-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/NullMoveEvalDivisor-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveEvalDivisor-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveEvalDivisor-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveEvalDivisor-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveEvalDivisor-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveEvalDivisor-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/NullMoveEvalDivisor-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveEvalDivisor-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveEvalDivisor-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveMinDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveMinDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveMinDepth-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/NullMoveMinDepth-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveMinDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveMinDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveMinDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveMinDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveMinDepth-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/NullMoveMinDepth-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/NullMoveMinDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/NullMoveMinDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/ProbcutDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/ProbcutDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/ProbcutDepth-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/ProbcutDepth-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/ProbcutDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/ProbcutDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/ProbcutDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/ProbcutDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/ProbcutDepth-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/ProbcutDepth-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/ProbcutDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/ProbcutDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/ProbcutMargin-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/ProbcutMargin-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/ProbcutMargin-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/ProbcutMargin-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/ProbcutMargin-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/ProbcutMargin-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/ProbcutMargin-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/ProbcutMargin-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/QsFutilityMargin-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/QsFutilityMargin-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/QsFutilityMargin-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/QsFutilityMargin-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/QsFutilityMargin-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/QsFutilityMargin-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/QsFutilityMargin-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/QsFutilityMargin-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/QsFutilityMargin-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/QsFutilityMargin-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/QsFutilityMargin-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/QsFutilityMargin-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/QsSeeMargin-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/QsSeeMargin-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/QsSeeMargin-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/QsSeeMargin-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/QsSeeMargin-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/QsSeeMargin-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/QsSeeMargin-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/QsSeeMargin-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorBase-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/RazorBase-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorBase-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/RazorBase-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorBase-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/RazorBase-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorBase-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/RazorBase-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorBase-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/RazorBase-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorBase-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/RazorBase-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/RazorDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorDepth-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/RazorDepth-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/RazorDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/RazorDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorDepth-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/RazorDepth-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/RazorDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorMultiplier-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/RazorMultiplier-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorMultiplier-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/RazorMultiplier-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorMultiplier-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/RazorMultiplier-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorMultiplier-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/RazorMultiplier-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorMultiplier-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/RazorMultiplier-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/RazorMultiplier-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/RazorMultiplier-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/RfpDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpDepth-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/RfpDepth-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/RfpDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/RfpDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpDepth-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/RfpDepth-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/RfpDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpImproving-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/RfpImproving-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpImproving-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/RfpImproving-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpImproving-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/RfpImproving-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpImproving-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/RfpImproving-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpImproving-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/RfpImproving-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpImproving-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/RfpImproving-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpMargin-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/RfpMargin-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpMargin-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/RfpMargin-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpMargin-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/RfpMargin-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/RfpMargin-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/RfpMargin-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SeeNoisyMultiplier-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/SeeNoisyMultiplier-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SeeNoisyMultiplier-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/SeeNoisyMultiplier-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/SeeNoisyMultiplier-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/SeeNoisyMultiplier-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SeeNoisyMultiplier-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/SeeNoisyMultiplier-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SeeNoisyMultiplier-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/SeeNoisyMultiplier-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/SeeNoisyMultiplier-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/SeeNoisyMultiplier-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SeeQuietMultiplier-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/SeeQuietMultiplier-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SeeQuietMultiplier-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/SeeQuietMultiplier-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/SeeQuietMultiplier-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/SeeQuietMultiplier-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SeeQuietMultiplier-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/SeeQuietMultiplier-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SeeQuietMultiplier-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/SeeQuietMultiplier-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/SeeQuietMultiplier-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/SeeQuietMultiplier-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SingularDepth-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/SingularDepth-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SingularDepth-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/SingularDepth-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/SingularDepth-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/SingularDepth-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SingularDepth-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/SingularDepth-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SingularDepth-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/SingularDepth-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/SingularDepth-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/SingularDepth-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SingularMargin-minus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/SingularMargin-minus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SingularMargin-minus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/SingularMargin-minus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/SingularMargin-minus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/SingularMargin-minus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SingularMargin-plus-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/SingularMargin-plus-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/SingularMargin-plus-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/SingularMargin-plus-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/SingularMargin-plus-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/SingularMargin-plus-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/base-cold-soft.jsonl
A  forge-combo29/sol/job6/raw/base-cold-soft.jsonl.meta
A  forge-combo29/sol/job6/raw/base-warm-hard.jsonl
A  forge-combo29/sol/job6/raw/base-warm-hard.jsonl.meta
A  forge-combo29/sol/job6/raw/base-warm-soft.jsonl
A  forge-combo29/sol/job6/raw/base-warm-soft.jsonl.meta
A  forge-combo29/sol/job6/read-counts.txt
A  forge-combo29/sol/job6/repeat-gate.txt
A  forge-combo29/sol/job6/repeat-run.txt
A  forge-combo29/sol/job6/run_batches.py
A  forge-combo29/sol/job6/run_sweep.py
A  forge-combo29/sol/job6/settings.tsv
A  forge-combo29/sol/job6/stamps.txt
A  forge-combo29/sol/job6/start-values-independent.txt
A  forge-combo29/sol/job6/step0-count.raw.txt
A  forge-combo29/sol/job6/step0.summary.txt
A  forge-combo29/sol/job6/summarize.py
A  forge-combo29/sol/job6/verify_gates.py
?? forge-combo29/sol/job2/__pycache__/
forge-combo29/sol/job6:
base-gate.txt
block-A-run.txt
block-B-run.txt
block-C-run.txt
controls-gate.txt
controls-run.txt
full-openings-gate.txt
opening-raw
openings-gate.txt
openings-run.txt
prediction.txt
raw
read-counts.txt
repeat-gate.txt
repeat-run.txt
run_batches.py
run_sweep.py
settings.tsv
stamps.txt
start-values-independent.txt
step0-count.raw.txt
step0.summary.txt
summarize.py
verify_gates.py

forge-combo29/sol/job6/opening-raw:
AspFailHighMaxReduce-minus-cold-soft.jsonl
AspFailHighMaxReduce-minus-cold-soft.jsonl.meta
AspFailHighMaxReduce-minus-warm-soft.jsonl
AspFailHighMaxReduce-minus-warm-soft.jsonl.meta
AspFailHighMaxReduce-plus-cold-soft.jsonl
AspFailHighMaxReduce-plus-cold-soft.jsonl.meta
AspFailHighMaxReduce-plus-warm-soft.jsonl
AspFailHighMaxReduce-plus-warm-soft.jsonl.meta
AspirationDelta-minus-cold-soft.jsonl
AspirationDelta-minus-cold-soft.jsonl.meta
AspirationDelta-minus-warm-soft.jsonl
AspirationDelta-minus-warm-soft.jsonl.meta
AspirationDelta-plus-cold-soft.jsonl
AspirationDelta-plus-cold-soft.jsonl.meta
AspirationDelta-plus-warm-soft.jsonl
AspirationDelta-plus-warm-soft.jsonl.meta
CaptureFutilityBase-plus-cold-soft.jsonl
CaptureFutilityBase-plus-cold-soft.jsonl.meta
CaptureFutilityBase-plus-warm-soft.jsonl
CaptureFutilityBase-plus-warm-soft.jsonl.meta
CaptureFutilityDepth-minus-cold-soft.jsonl
CaptureFutilityDepth-minus-cold-soft.jsonl.meta
CaptureFutilityDepth-minus-warm-soft.jsonl
CaptureFutilityDepth-minus-warm-soft.jsonl.meta
CaptureFutilityDepth-plus-cold-soft.jsonl
CaptureFutilityDepth-plus-cold-soft.jsonl.meta
CaptureFutilityDepth-plus-warm-soft.jsonl
CaptureFutilityDepth-plus-warm-soft.jsonl.meta
CaptureFutilityMultiplier-minus-cold-soft.jsonl
CaptureFutilityMultiplier-minus-cold-soft.jsonl.meta
CaptureFutilityMultiplier-minus-warm-soft.jsonl
CaptureFutilityMultiplier-minus-warm-soft.jsonl.meta
CaptureFutilityMultiplier-plus-cold-soft.jsonl
CaptureFutilityMultiplier-plus-cold-soft.jsonl.meta
CaptureFutilityMultiplier-plus-warm-soft.jsonl
CaptureFutilityMultiplier-plus-warm-soft.jsonl.meta
CheckExtensionDepth-minus-cold-soft.jsonl
CheckExtensionDepth-minus-cold-soft.jsonl.meta
CheckExtensionDepth-minus-warm-soft.jsonl
CheckExtensionDepth-minus-warm-soft.jsonl.meta
CheckExtensionDepth-plus-cold-soft.jsonl
CheckExtensionDepth-plus-cold-soft.jsonl.meta
CheckExtensionDepth-plus-warm-soft.jsonl
CheckExtensionDepth-plus-warm-soft.jsonl.meta
DrawJitter-plus-cold-soft.jsonl
DrawJitter-plus-cold-soft.jsonl.meta
DrawJitter-plus-warm-soft.jsonl
DrawJitter-plus-warm-soft.jsonl.meta
EvalSwingMax-minus-cold-soft.jsonl
EvalSwingMax-minus-cold-soft.jsonl.meta
EvalSwingMax-minus-warm-soft.jsonl
EvalSwingMax-minus-warm-soft.jsonl.meta
EvalSwingMax-plus-cold-soft.jsonl
EvalSwingMax-plus-cold-soft.jsonl.meta
EvalSwingMax-plus-warm-soft.jsonl
EvalSwingMax-plus-warm-soft.jsonl.meta
EvalSwingMult-plus-cold-soft.jsonl
EvalSwingMult-plus-cold-soft.jsonl.meta
EvalSwingMult-plus-warm-soft.jsonl
EvalSwingMult-plus-warm-soft.jsonl.meta
FailLowContinuationBonus-plus-cold-soft.jsonl
FailLowContinuationBonus-plus-cold-soft.jsonl.meta
FailLowContinuationBonus-plus-warm-soft.jsonl
FailLowContinuationBonus-plus-warm-soft.jsonl.meta
FutilityBase-minus-cold-soft.jsonl
FutilityBase-minus-cold-soft.jsonl.meta
FutilityBase-minus-warm-soft.jsonl
FutilityBase-minus-warm-soft.jsonl.meta
FutilityBase-plus-cold-soft.jsonl
FutilityBase-plus-cold-soft.jsonl.meta
FutilityBase-plus-warm-soft.jsonl
FutilityBase-plus-warm-soft.jsonl.meta
FutilityDepth-minus-cold-soft.jsonl
FutilityDepth-minus-cold-soft.jsonl.meta
FutilityDepth-minus-warm-soft.jsonl
FutilityDepth-minus-warm-soft.jsonl.meta
FutilityDepth-plus-cold-soft.jsonl
FutilityDepth-plus-cold-soft.jsonl.meta
FutilityDepth-plus-warm-soft.jsonl
FutilityDepth-plus-warm-soft.jsonl.meta
FutilityMultiplier-minus-cold-soft.jsonl
FutilityMultiplier-minus-cold-soft.jsonl.meta
FutilityMultiplier-minus-warm-soft.jsonl
FutilityMultiplier-minus-warm-soft.jsonl.meta
FutilityMultiplier-plus-cold-soft.jsonl
FutilityMultiplier-plus-cold-soft.jsonl.meta
FutilityMultiplier-plus-warm-soft.jsonl
FutilityMultiplier-plus-warm-soft.jsonl.meta
HistoryBonusLinear-minus-cold-soft.jsonl
HistoryBonusLinear-minus-cold-soft.jsonl.meta
HistoryBonusLinear-minus-warm-soft.jsonl
HistoryBonusLinear-minus-warm-soft.jsonl.meta
HistoryBonusLinear-plus-cold-soft.jsonl
HistoryBonusLinear-plus-cold-soft.jsonl.meta
HistoryBonusLinear-plus-warm-soft.jsonl
HistoryBonusLinear-plus-warm-soft.jsonl.meta
HistoryBonusMax-minus-cold-soft.jsonl
HistoryBonusMax-minus-cold-soft.jsonl.meta
HistoryBonusMax-minus-warm-soft.jsonl
HistoryBonusMax-minus-warm-soft.jsonl.meta
HistoryBonusMax-plus-cold-soft.jsonl
HistoryBonusMax-plus-cold-soft.jsonl.meta
HistoryBonusMax-plus-warm-soft.jsonl
HistoryBonusMax-plus-warm-soft.jsonl.meta
HistoryBonusQuadratic-minus-cold-soft.jsonl
HistoryBonusQuadratic-minus-cold-soft.jsonl.meta
HistoryBonusQuadratic-minus-warm-soft.jsonl
HistoryBonusQuadratic-minus-warm-soft.jsonl.meta
HistoryBonusQuadratic-plus-cold-soft.jsonl
HistoryBonusQuadratic-plus-cold-soft.jsonl.meta
HistoryBonusQuadratic-plus-warm-soft.jsonl
HistoryBonusQuadratic-plus-warm-soft.jsonl.meta
HistoryPruneDepth-minus-cold-soft.jsonl
HistoryPruneDepth-minus-cold-soft.jsonl.meta
HistoryPruneDepth-minus-warm-soft.jsonl
HistoryPruneDepth-minus-warm-soft.jsonl.meta
HistoryPruneDepth-plus-cold-soft.jsonl
HistoryPruneDepth-plus-cold-soft.jsonl.meta
HistoryPruneDepth-plus-warm-soft.jsonl
HistoryPruneDepth-plus-warm-soft.jsonl.meta
HistoryPruneMultiplier-minus-cold-soft.jsonl
HistoryPruneMultiplier-minus-cold-soft.jsonl.meta
HistoryPruneMultiplier-minus-warm-soft.jsonl
HistoryPruneMultiplier-minus-warm-soft.jsonl.meta
HistoryPruneMultiplier-plus-cold-soft.jsonl
HistoryPruneMultiplier-plus-cold-soft.jsonl.meta
HistoryPruneMultiplier-plus-warm-soft.jsonl
HistoryPruneMultiplier-plus-warm-soft.jsonl.meta
IirDepth-minus-cold-soft.jsonl
IirDepth-minus-cold-soft.jsonl.meta
IirDepth-minus-warm-soft.jsonl
IirDepth-minus-warm-soft.jsonl.meta
IirDepth-plus-cold-soft.jsonl
IirDepth-plus-cold-soft.jsonl.meta
IirDepth-plus-warm-soft.jsonl
IirDepth-plus-warm-soft.jsonl.meta
LmpBase-minus-cold-soft.jsonl
LmpBase-minus-cold-soft.jsonl.meta
LmpBase-minus-warm-soft.jsonl
LmpBase-minus-warm-soft.jsonl.meta
LmpBase-plus-cold-soft.jsonl
LmpBase-plus-cold-soft.jsonl.meta
LmpBase-plus-warm-soft.jsonl
LmpBase-plus-warm-soft.jsonl.meta
LmrCutoffThreshold-minus-cold-soft.jsonl
LmrCutoffThreshold-minus-cold-soft.jsonl.meta
LmrCutoffThreshold-minus-warm-soft.jsonl
LmrCutoffThreshold-minus-warm-soft.jsonl.meta
LmrCutoffThreshold-plus-cold-soft.jsonl
LmrCutoffThreshold-plus-cold-soft.jsonl.meta
LmrCutoffThreshold-plus-warm-soft.jsonl
LmrCutoffThreshold-plus-warm-soft.jsonl.meta
LmrHistoryDivisor-minus-cold-soft.jsonl
LmrHistoryDivisor-minus-cold-soft.jsonl.meta
LmrHistoryDivisor-minus-warm-soft.jsonl
LmrHistoryDivisor-minus-warm-soft.jsonl.meta
LmrHistoryDivisor-plus-cold-soft.jsonl
LmrHistoryDivisor-plus-cold-soft.jsonl.meta
LmrHistoryDivisor-plus-warm-soft.jsonl
LmrHistoryDivisor-plus-warm-soft.jsonl.meta
LmrNoisyBase-minus-cold-soft.jsonl
LmrNoisyBase-minus-cold-soft.jsonl.meta
LmrNoisyBase-minus-warm-soft.jsonl
LmrNoisyBase-minus-warm-soft.jsonl.meta
LmrNoisyBase-plus-cold-soft.jsonl
LmrNoisyBase-plus-cold-soft.jsonl.meta
LmrNoisyBase-plus-warm-soft.jsonl
LmrNoisyBase-plus-warm-soft.jsonl.meta
LmrNoisyDivisor-minus-cold-soft.jsonl
LmrNoisyDivisor-minus-cold-soft.jsonl.meta
LmrNoisyDivisor-minus-warm-soft.jsonl
LmrNoisyDivisor-minus-warm-soft.jsonl.meta
LmrNoisyDivisor-plus-cold-soft.jsonl
LmrNoisyDivisor-plus-cold-soft.jsonl.meta
LmrNoisyDivisor-plus-warm-soft.jsonl
LmrNoisyDivisor-plus-warm-soft.jsonl.meta
LmrQuietBase-minus-cold-soft.jsonl
LmrQuietBase-minus-cold-soft.jsonl.meta
LmrQuietBase-minus-warm-soft.jsonl
LmrQuietBase-minus-warm-soft.jsonl.meta
LmrQuietBase-plus-cold-soft.jsonl
LmrQuietBase-plus-cold-soft.jsonl.meta
LmrQuietBase-plus-warm-soft.jsonl
LmrQuietBase-plus-warm-soft.jsonl.meta
LmrQuietDivisor-minus-cold-soft.jsonl
LmrQuietDivisor-minus-cold-soft.jsonl.meta
LmrQuietDivisor-minus-warm-soft.jsonl
LmrQuietDivisor-minus-warm-soft.jsonl.meta
LmrQuietDivisor-plus-cold-soft.jsonl
LmrQuietDivisor-plus-cold-soft.jsonl.meta
LmrQuietDivisor-plus-warm-soft.jsonl
LmrQuietDivisor-plus-warm-soft.jsonl.meta
MaterialCorrectionWeight-minus-cold-soft.jsonl
MaterialCorrectionWeight-minus-cold-soft.jsonl.meta
MaterialCorrectionWeight-minus-warm-soft.jsonl
MaterialCorrectionWeight-minus-warm-soft.jsonl.meta
MaterialCorrectionWeight-plus-cold-soft.jsonl
MaterialCorrectionWeight-plus-cold-soft.jsonl.meta
MaterialCorrectionWeight-plus-warm-soft.jsonl
MaterialCorrectionWeight-plus-warm-soft.jsonl.meta
NullMoveBase-minus-cold-soft.jsonl
NullMoveBase-minus-cold-soft.jsonl.meta
NullMoveBase-minus-warm-soft.jsonl
NullMoveBase-minus-warm-soft.jsonl.meta
NullMoveBase-plus-cold-soft.jsonl
NullMoveBase-plus-cold-soft.jsonl.meta
NullMoveBase-plus-warm-soft.jsonl
NullMoveBase-plus-warm-soft.jsonl.meta
NullMoveDepthDivisor-minus-cold-soft.jsonl
NullMoveDepthDivisor-minus-cold-soft.jsonl.meta
NullMoveDepthDivisor-minus-warm-soft.jsonl
NullMoveDepthDivisor-minus-warm-soft.jsonl.meta
NullMoveDepthDivisor-plus-cold-soft.jsonl
NullMoveDepthDivisor-plus-cold-soft.jsonl.meta
NullMoveDepthDivisor-plus-warm-soft.jsonl
NullMoveDepthDivisor-plus-warm-soft.jsonl.meta
NullMoveEvalDivisor-minus-cold-soft.jsonl
NullMoveEvalDivisor-minus-cold-soft.jsonl.meta
NullMoveEvalDivisor-minus-warm-soft.jsonl
NullMoveEvalDivisor-minus-warm-soft.jsonl.meta
NullMoveEvalDivisor-plus-cold-soft.jsonl
NullMoveEvalDivisor-plus-cold-soft.jsonl.meta
NullMoveEvalDivisor-plus-warm-soft.jsonl
NullMoveEvalDivisor-plus-warm-soft.jsonl.meta
NullMoveMinDepth-minus-cold-soft.jsonl
NullMoveMinDepth-minus-cold-soft.jsonl.meta
NullMoveMinDepth-minus-warm-soft.jsonl
NullMoveMinDepth-minus-warm-soft.jsonl.meta
NullMoveMinDepth-plus-cold-soft.jsonl
NullMoveMinDepth-plus-cold-soft.jsonl.meta
NullMoveMinDepth-plus-warm-soft.jsonl
NullMoveMinDepth-plus-warm-soft.jsonl.meta
ProbcutDepth-minus-cold-soft.jsonl
ProbcutDepth-minus-cold-soft.jsonl.meta
ProbcutDepth-minus-warm-soft.jsonl
ProbcutDepth-minus-warm-soft.jsonl.meta
ProbcutDepth-plus-cold-soft.jsonl
ProbcutDepth-plus-cold-soft.jsonl.meta
ProbcutDepth-plus-warm-soft.jsonl
ProbcutDepth-plus-warm-soft.jsonl.meta
ProbcutMargin-minus-cold-soft.jsonl
ProbcutMargin-minus-cold-soft.jsonl.meta
ProbcutMargin-minus-warm-soft.jsonl
ProbcutMargin-minus-warm-soft.jsonl.meta
ProbcutMargin-plus-cold-soft.jsonl
ProbcutMargin-plus-cold-soft.jsonl.meta
ProbcutMargin-plus-warm-soft.jsonl
ProbcutMargin-plus-warm-soft.jsonl.meta
QsFutilityMargin-minus-cold-soft.jsonl
QsFutilityMargin-minus-cold-soft.jsonl.meta
QsFutilityMargin-minus-warm-soft.jsonl
QsFutilityMargin-minus-warm-soft.jsonl.meta
QsFutilityMargin-plus-cold-soft.jsonl
QsFutilityMargin-plus-cold-soft.jsonl.meta
QsFutilityMargin-plus-warm-soft.jsonl
QsFutilityMargin-plus-warm-soft.jsonl.meta
QsSeeMargin-minus-cold-soft.jsonl
QsSeeMargin-minus-cold-soft.jsonl.meta
QsSeeMargin-minus-warm-soft.jsonl
QsSeeMargin-minus-warm-soft.jsonl.meta
QsSeeMargin-plus-cold-soft.jsonl
QsSeeMargin-plus-cold-soft.jsonl.meta
QsSeeMargin-plus-warm-soft.jsonl
QsSeeMargin-plus-warm-soft.jsonl.meta
RazorBase-minus-cold-soft.jsonl
RazorBase-minus-cold-soft.jsonl.meta
RazorBase-minus-warm-soft.jsonl
RazorBase-minus-warm-soft.jsonl.meta
RazorBase-plus-cold-soft.jsonl
RazorBase-plus-cold-soft.jsonl.meta
RazorBase-plus-warm-soft.jsonl
RazorBase-plus-warm-soft.jsonl.meta
RazorDepth-minus-cold-soft.jsonl
RazorDepth-minus-cold-soft.jsonl.meta
RazorDepth-minus-warm-soft.jsonl
RazorDepth-minus-warm-soft.jsonl.meta
RazorDepth-plus-cold-soft.jsonl
RazorDepth-plus-cold-soft.jsonl.meta
RazorDepth-plus-warm-soft.jsonl
RazorDepth-plus-warm-soft.jsonl.meta
RazorMultiplier-minus-cold-soft.jsonl
RazorMultiplier-minus-cold-soft.jsonl.meta
RazorMultiplier-minus-warm-soft.jsonl
RazorMultiplier-minus-warm-soft.jsonl.meta
RazorMultiplier-plus-cold-soft.jsonl
RazorMultiplier-plus-cold-soft.jsonl.meta
RazorMultiplier-plus-warm-soft.jsonl
RazorMultiplier-plus-warm-soft.jsonl.meta
RfpDepth-minus-cold-soft.jsonl
RfpDepth-minus-cold-soft.jsonl.meta
RfpDepth-minus-warm-soft.jsonl
RfpDepth-minus-warm-soft.jsonl.meta
RfpDepth-plus-cold-soft.jsonl
RfpDepth-plus-cold-soft.jsonl.meta
RfpDepth-plus-warm-soft.jsonl
RfpDepth-plus-warm-soft.jsonl.meta
RfpImproving-minus-cold-soft.jsonl
RfpImproving-minus-cold-soft.jsonl.meta
RfpImproving-minus-warm-soft.jsonl
RfpImproving-minus-warm-soft.jsonl.meta
RfpImproving-plus-cold-soft.jsonl
RfpImproving-plus-cold-soft.jsonl.meta
RfpImproving-plus-warm-soft.jsonl
RfpImproving-plus-warm-soft.jsonl.meta
RfpMargin-minus-cold-soft.jsonl
RfpMargin-minus-cold-soft.jsonl.meta
RfpMargin-minus-warm-soft.jsonl
RfpMargin-minus-warm-soft.jsonl.meta
RfpMargin-plus-cold-soft.jsonl
RfpMargin-plus-cold-soft.jsonl.meta
RfpMargin-plus-warm-soft.jsonl
RfpMargin-plus-warm-soft.jsonl.meta
SeeNoisyMultiplier-minus-cold-soft.jsonl
SeeNoisyMultiplier-minus-cold-soft.jsonl.meta
SeeNoisyMultiplier-minus-warm-soft.jsonl
SeeNoisyMultiplier-minus-warm-soft.jsonl.meta
SeeNoisyMultiplier-plus-cold-soft.jsonl
SeeNoisyMultiplier-plus-cold-soft.jsonl.meta
SeeNoisyMultiplier-plus-warm-soft.jsonl
SeeNoisyMultiplier-plus-warm-soft.jsonl.meta
SeeQuietMultiplier-minus-cold-soft.jsonl
SeeQuietMultiplier-minus-cold-soft.jsonl.meta
SeeQuietMultiplier-minus-warm-soft.jsonl
SeeQuietMultiplier-minus-warm-soft.jsonl.meta
SeeQuietMultiplier-plus-cold-soft.jsonl
SeeQuietMultiplier-plus-cold-soft.jsonl.meta
SeeQuietMultiplier-plus-warm-soft.jsonl
SeeQuietMultiplier-plus-warm-soft.jsonl.meta
SingularDepth-minus-cold-soft.jsonl
SingularDepth-minus-cold-soft.jsonl.meta
SingularDepth-minus-warm-soft.jsonl
SingularDepth-minus-warm-soft.jsonl.meta
SingularDepth-plus-cold-soft.jsonl
SingularDepth-plus-cold-soft.jsonl.meta
SingularDepth-plus-warm-soft.jsonl
SingularDepth-plus-warm-soft.jsonl.meta
SingularMargin-minus-cold-soft.jsonl
SingularMargin-minus-cold-soft.jsonl.meta
SingularMargin-minus-warm-soft.jsonl
SingularMargin-minus-warm-soft.jsonl.meta
SingularMargin-plus-cold-soft.jsonl
SingularMargin-plus-cold-soft.jsonl.meta
SingularMargin-plus-warm-soft.jsonl
SingularMargin-plus-warm-soft.jsonl.meta

forge-combo29/sol/job6/raw:
AspFailHighMaxReduce-minus-cold-soft.jsonl
AspFailHighMaxReduce-minus-cold-soft.jsonl.meta
AspFailHighMaxReduce-minus-warm-soft.jsonl
AspFailHighMaxReduce-minus-warm-soft.jsonl.meta
AspFailHighMaxReduce-plus-cold-soft.jsonl
AspFailHighMaxReduce-plus-cold-soft.jsonl.meta
AspFailHighMaxReduce-plus-warm-soft.jsonl
AspFailHighMaxReduce-plus-warm-soft.jsonl.meta
AspirationDelta-minus-cold-soft.jsonl
AspirationDelta-minus-cold-soft.jsonl.meta
AspirationDelta-minus-warm-hard.jsonl
AspirationDelta-minus-warm-hard.jsonl.meta
AspirationDelta-minus-warm-soft.jsonl
AspirationDelta-minus-warm-soft.jsonl.meta
AspirationDelta-plus-cold-soft.jsonl
AspirationDelta-plus-cold-soft.jsonl.meta
AspirationDelta-plus-warm-hard.jsonl
AspirationDelta-plus-warm-hard.jsonl.meta
AspirationDelta-plus-warm-soft.jsonl
AspirationDelta-plus-warm-soft.jsonl.meta
CaptureFutilityBase-plus-cold-soft.jsonl
CaptureFutilityBase-plus-cold-soft.jsonl.meta
CaptureFutilityBase-plus-warm-hard.jsonl
CaptureFutilityBase-plus-warm-hard.jsonl.meta
CaptureFutilityBase-plus-warm-soft.jsonl
CaptureFutilityBase-plus-warm-soft.jsonl.meta
CaptureFutilityDepth-minus-cold-soft.jsonl
CaptureFutilityDepth-minus-cold-soft.jsonl.meta
CaptureFutilityDepth-minus-warm-soft.jsonl
CaptureFutilityDepth-minus-warm-soft.jsonl.meta
CaptureFutilityDepth-plus-cold-soft.jsonl
CaptureFutilityDepth-plus-cold-soft.jsonl.meta
CaptureFutilityDepth-plus-warm-soft.jsonl
CaptureFutilityDepth-plus-warm-soft.jsonl.meta
CaptureFutilityMultiplier-minus-cold-soft.jsonl
CaptureFutilityMultiplier-minus-cold-soft.jsonl.meta
CaptureFutilityMultiplier-minus-warm-soft.jsonl
CaptureFutilityMultiplier-minus-warm-soft.jsonl.meta
CaptureFutilityMultiplier-plus-cold-soft.jsonl
CaptureFutilityMultiplier-plus-cold-soft.jsonl.meta
CaptureFutilityMultiplier-plus-warm-soft.jsonl
CaptureFutilityMultiplier-plus-warm-soft.jsonl.meta
CheckExtensionDepth-minus-cold-soft.jsonl
CheckExtensionDepth-minus-cold-soft.jsonl.meta
CheckExtensionDepth-minus-warm-hard.jsonl
CheckExtensionDepth-minus-warm-hard.jsonl.meta
CheckExtensionDepth-minus-warm-soft.jsonl
CheckExtensionDepth-minus-warm-soft.jsonl.meta
CheckExtensionDepth-plus-cold-soft.jsonl
CheckExtensionDepth-plus-cold-soft.jsonl.meta
CheckExtensionDepth-plus-warm-hard.jsonl
CheckExtensionDepth-plus-warm-hard.jsonl.meta
CheckExtensionDepth-plus-warm-soft.jsonl
CheckExtensionDepth-plus-warm-soft.jsonl.meta
DrawJitter-plus-cold-soft.jsonl
DrawJitter-plus-cold-soft.jsonl.meta
DrawJitter-plus-warm-hard.jsonl
DrawJitter-plus-warm-hard.jsonl.meta
DrawJitter-plus-warm-soft.jsonl
DrawJitter-plus-warm-soft.jsonl.meta
EvalSwingMax-minus-cold-soft.jsonl
EvalSwingMax-minus-cold-soft.jsonl.meta
EvalSwingMax-minus-warm-soft.jsonl
EvalSwingMax-minus-warm-soft.jsonl.meta
EvalSwingMax-plus-cold-soft.jsonl
EvalSwingMax-plus-cold-soft.jsonl.meta
EvalSwingMax-plus-warm-soft.jsonl
EvalSwingMax-plus-warm-soft.jsonl.meta
EvalSwingMult-plus-cold-soft.jsonl
EvalSwingMult-plus-cold-soft.jsonl.meta
EvalSwingMult-plus-warm-hard.jsonl
EvalSwingMult-plus-warm-hard.jsonl.meta
EvalSwingMult-plus-warm-soft.jsonl
EvalSwingMult-plus-warm-soft.jsonl.meta
FailLowContinuationBonus-plus-cold-soft.jsonl
FailLowContinuationBonus-plus-cold-soft.jsonl.meta
FailLowContinuationBonus-plus-warm-hard.jsonl
FailLowContinuationBonus-plus-warm-hard.jsonl.meta
FailLowContinuationBonus-plus-warm-soft.jsonl
FailLowContinuationBonus-plus-warm-soft.jsonl.meta
FutilityBase-minus-cold-soft.jsonl
FutilityBase-minus-cold-soft.jsonl.meta
FutilityBase-minus-warm-hard.jsonl
FutilityBase-minus-warm-hard.jsonl.meta
FutilityBase-minus-warm-soft.jsonl
FutilityBase-minus-warm-soft.jsonl.meta
FutilityBase-plus-cold-soft.jsonl
FutilityBase-plus-cold-soft.jsonl.meta
FutilityBase-plus-warm-hard.jsonl
FutilityBase-plus-warm-hard.jsonl.meta
FutilityBase-plus-warm-soft.jsonl
FutilityBase-plus-warm-soft.jsonl.meta
FutilityDepth-minus-cold-soft.jsonl
FutilityDepth-minus-cold-soft.jsonl.meta
FutilityDepth-minus-warm-hard.jsonl
FutilityDepth-minus-warm-hard.jsonl.meta
FutilityDepth-minus-warm-soft.jsonl
FutilityDepth-minus-warm-soft.jsonl.meta
FutilityDepth-plus-cold-soft.jsonl
FutilityDepth-plus-cold-soft.jsonl.meta
FutilityDepth-plus-warm-hard.jsonl
FutilityDepth-plus-warm-hard.jsonl.meta
FutilityDepth-plus-warm-soft.jsonl
FutilityDepth-plus-warm-soft.jsonl.meta
FutilityMultiplier-minus-cold-soft.jsonl
FutilityMultiplier-minus-cold-soft.jsonl.meta
FutilityMultiplier-minus-warm-hard.jsonl
FutilityMultiplier-minus-warm-hard.jsonl.meta
FutilityMultiplier-minus-warm-soft.jsonl
FutilityMultiplier-minus-warm-soft.jsonl.meta
FutilityMultiplier-plus-cold-soft.jsonl
FutilityMultiplier-plus-cold-soft.jsonl.meta
FutilityMultiplier-plus-warm-hard.jsonl
FutilityMultiplier-plus-warm-hard.jsonl.meta
FutilityMultiplier-plus-warm-soft.jsonl
FutilityMultiplier-plus-warm-soft.jsonl.meta
HistoryBonusLinear-minus-cold-soft.jsonl
HistoryBonusLinear-minus-cold-soft.jsonl.meta
HistoryBonusLinear-minus-warm-soft.jsonl
HistoryBonusLinear-minus-warm-soft.jsonl.meta
HistoryBonusLinear-plus-cold-soft.jsonl
HistoryBonusLinear-plus-cold-soft.jsonl.meta
HistoryBonusLinear-plus-warm-soft.jsonl
HistoryBonusLinear-plus-warm-soft.jsonl.meta
HistoryBonusMax-minus-cold-soft.jsonl
HistoryBonusMax-minus-cold-soft.jsonl.meta
HistoryBonusMax-minus-warm-soft.jsonl
HistoryBonusMax-minus-warm-soft.jsonl.meta
HistoryBonusMax-plus-cold-soft.jsonl
HistoryBonusMax-plus-cold-soft.jsonl.meta
HistoryBonusMax-plus-warm-soft.jsonl
HistoryBonusMax-plus-warm-soft.jsonl.meta
HistoryBonusQuadratic-minus-cold-soft.jsonl
HistoryBonusQuadratic-minus-cold-soft.jsonl.meta
HistoryBonusQuadratic-minus-warm-soft.jsonl
HistoryBonusQuadratic-minus-warm-soft.jsonl.meta
HistoryBonusQuadratic-plus-cold-soft.jsonl
HistoryBonusQuadratic-plus-cold-soft.jsonl.meta
HistoryBonusQuadratic-plus-warm-soft.jsonl
HistoryBonusQuadratic-plus-warm-soft.jsonl.meta
HistoryPruneDepth-minus-cold-soft.jsonl
HistoryPruneDepth-minus-cold-soft.jsonl.meta
HistoryPruneDepth-minus-warm-soft.jsonl
HistoryPruneDepth-minus-warm-soft.jsonl.meta
HistoryPruneDepth-plus-cold-soft.jsonl
HistoryPruneDepth-plus-cold-soft.jsonl.meta
HistoryPruneDepth-plus-warm-soft.jsonl
HistoryPruneDepth-plus-warm-soft.jsonl.meta
HistoryPruneMultiplier-minus-cold-soft.jsonl
HistoryPruneMultiplier-minus-cold-soft.jsonl.meta
HistoryPruneMultiplier-minus-warm-soft.jsonl
HistoryPruneMultiplier-minus-warm-soft.jsonl.meta
HistoryPruneMultiplier-plus-cold-soft.jsonl
HistoryPruneMultiplier-plus-cold-soft.jsonl.meta
HistoryPruneMultiplier-plus-warm-soft.jsonl
HistoryPruneMultiplier-plus-warm-soft.jsonl.meta
IirDepth-minus-cold-soft.jsonl
IirDepth-minus-cold-soft.jsonl.meta
IirDepth-minus-warm-hard.jsonl
IirDepth-minus-warm-hard.jsonl.meta
IirDepth-minus-warm-soft.jsonl
IirDepth-minus-warm-soft.jsonl.meta
IirDepth-plus-cold-soft.jsonl
IirDepth-plus-cold-soft.jsonl.meta
IirDepth-plus-warm-hard.jsonl
IirDepth-plus-warm-hard.jsonl.meta
IirDepth-plus-warm-soft.jsonl
IirDepth-plus-warm-soft.jsonl.meta
LmpBase-minus-cold-soft.jsonl
LmpBase-minus-cold-soft.jsonl.meta
LmpBase-minus-warm-hard.jsonl
LmpBase-minus-warm-hard.jsonl.meta
LmpBase-minus-warm-soft.jsonl
LmpBase-minus-warm-soft.jsonl.meta
LmpBase-plus-cold-soft.jsonl
LmpBase-plus-cold-soft.jsonl.meta
LmpBase-plus-warm-hard.jsonl
LmpBase-plus-warm-hard.jsonl.meta
LmpBase-plus-warm-soft.jsonl
LmpBase-plus-warm-soft.jsonl.meta
LmrCutoffThreshold-minus-cold-soft.jsonl
LmrCutoffThreshold-minus-cold-soft.jsonl.meta
LmrCutoffThreshold-minus-warm-hard.jsonl
LmrCutoffThreshold-minus-warm-hard.jsonl.meta
LmrCutoffThreshold-minus-warm-soft.jsonl
LmrCutoffThreshold-minus-warm-soft.jsonl.meta
LmrCutoffThreshold-plus-cold-soft.jsonl
LmrCutoffThreshold-plus-cold-soft.jsonl.meta
LmrCutoffThreshold-plus-warm-hard.jsonl
LmrCutoffThreshold-plus-warm-hard.jsonl.meta
LmrCutoffThreshold-plus-warm-soft.jsonl
LmrCutoffThreshold-plus-warm-soft.jsonl.meta
LmrHistoryDivisor-minus-cold-soft.jsonl
LmrHistoryDivisor-minus-cold-soft.jsonl.meta
LmrHistoryDivisor-minus-warm-soft.jsonl
LmrHistoryDivisor-minus-warm-soft.jsonl.meta
LmrHistoryDivisor-plus-cold-soft.jsonl
LmrHistoryDivisor-plus-cold-soft.jsonl.meta
LmrHistoryDivisor-plus-warm-soft.jsonl
LmrHistoryDivisor-plus-warm-soft.jsonl.meta
LmrNoisyBase-minus-cold-soft.jsonl
LmrNoisyBase-minus-cold-soft.jsonl.meta
LmrNoisyBase-minus-warm-hard.jsonl
LmrNoisyBase-minus-warm-hard.jsonl.meta
LmrNoisyBase-minus-warm-soft.jsonl
LmrNoisyBase-minus-warm-soft.jsonl.meta
LmrNoisyBase-plus-cold-soft.jsonl
LmrNoisyBase-plus-cold-soft.jsonl.meta
LmrNoisyBase-plus-warm-hard.jsonl
LmrNoisyBase-plus-warm-hard.jsonl.meta
LmrNoisyBase-plus-warm-soft.jsonl
LmrNoisyBase-plus-warm-soft.jsonl.meta
LmrNoisyDivisor-minus-cold-soft.jsonl
LmrNoisyDivisor-minus-cold-soft.jsonl.meta
LmrNoisyDivisor-minus-warm-hard.jsonl
LmrNoisyDivisor-minus-warm-hard.jsonl.meta
LmrNoisyDivisor-minus-warm-soft.jsonl
LmrNoisyDivisor-minus-warm-soft.jsonl.meta
LmrNoisyDivisor-plus-cold-soft.jsonl
LmrNoisyDivisor-plus-cold-soft.jsonl.meta
LmrNoisyDivisor-plus-warm-hard.jsonl
LmrNoisyDivisor-plus-warm-hard.jsonl.meta
LmrNoisyDivisor-plus-warm-soft.jsonl
LmrNoisyDivisor-plus-warm-soft.jsonl.meta
LmrQuietBase-minus-cold-soft.jsonl
LmrQuietBase-minus-cold-soft.jsonl.meta
LmrQuietBase-minus-warm-hard.jsonl
LmrQuietBase-minus-warm-hard.jsonl.meta
LmrQuietBase-minus-warm-soft.jsonl
LmrQuietBase-minus-warm-soft.jsonl.meta
LmrQuietBase-plus-cold-soft.jsonl
LmrQuietBase-plus-cold-soft.jsonl.meta
LmrQuietBase-plus-warm-hard.jsonl
LmrQuietBase-plus-warm-hard.jsonl.meta
LmrQuietBase-plus-warm-soft.jsonl
LmrQuietBase-plus-warm-soft.jsonl.meta
LmrQuietDivisor-minus-cold-soft.jsonl
LmrQuietDivisor-minus-cold-soft.jsonl.meta
LmrQuietDivisor-minus-warm-hard.jsonl
LmrQuietDivisor-minus-warm-hard.jsonl.meta
LmrQuietDivisor-minus-warm-soft.jsonl
LmrQuietDivisor-minus-warm-soft.jsonl.meta
LmrQuietDivisor-plus-cold-soft.jsonl
LmrQuietDivisor-plus-cold-soft.jsonl.meta
LmrQuietDivisor-plus-warm-hard.jsonl
LmrQuietDivisor-plus-warm-hard.jsonl.meta
LmrQuietDivisor-plus-warm-soft.jsonl
LmrQuietDivisor-plus-warm-soft.jsonl.meta
MaterialCorrectionWeight-minus-cold-soft.jsonl
MaterialCorrectionWeight-minus-cold-soft.jsonl.meta
MaterialCorrectionWeight-minus-warm-hard.jsonl
MaterialCorrectionWeight-minus-warm-hard.jsonl.meta
MaterialCorrectionWeight-minus-warm-soft.jsonl
MaterialCorrectionWeight-minus-warm-soft.jsonl.meta
MaterialCorrectionWeight-plus-cold-soft.jsonl
MaterialCorrectionWeight-plus-cold-soft.jsonl.meta
MaterialCorrectionWeight-plus-warm-hard.jsonl
MaterialCorrectionWeight-plus-warm-hard.jsonl.meta
MaterialCorrectionWeight-plus-warm-soft.jsonl
MaterialCorrectionWeight-plus-warm-soft.jsonl.meta
NullMoveBase-minus-cold-soft.jsonl
NullMoveBase-minus-cold-soft.jsonl.meta
NullMoveBase-minus-warm-hard.jsonl
NullMoveBase-minus-warm-hard.jsonl.meta
NullMoveBase-minus-warm-soft.jsonl
NullMoveBase-minus-warm-soft.jsonl.meta
NullMoveBase-plus-cold-soft.jsonl
NullMoveBase-plus-cold-soft.jsonl.meta
NullMoveBase-plus-warm-hard.jsonl
NullMoveBase-plus-warm-hard.jsonl.meta
NullMoveBase-plus-warm-soft.jsonl
NullMoveBase-plus-warm-soft.jsonl.meta
NullMoveDepthDivisor-minus-cold-soft.jsonl
NullMoveDepthDivisor-minus-cold-soft.jsonl.meta
NullMoveDepthDivisor-minus-warm-hard.jsonl
NullMoveDepthDivisor-minus-warm-hard.jsonl.meta
NullMoveDepthDivisor-minus-warm-soft.jsonl
NullMoveDepthDivisor-minus-warm-soft.jsonl.meta
NullMoveDepthDivisor-plus-cold-soft.jsonl
NullMoveDepthDivisor-plus-cold-soft.jsonl.meta
NullMoveDepthDivisor-plus-warm-hard.jsonl
NullMoveDepthDivisor-plus-warm-hard.jsonl.meta
NullMoveDepthDivisor-plus-warm-soft.jsonl
NullMoveDepthDivisor-plus-warm-soft.jsonl.meta
NullMoveEvalDivisor-minus-cold-soft.jsonl
NullMoveEvalDivisor-minus-cold-soft.jsonl.meta
NullMoveEvalDivisor-minus-warm-hard.jsonl
NullMoveEvalDivisor-minus-warm-hard.jsonl.meta
NullMoveEvalDivisor-minus-warm-soft.jsonl
NullMoveEvalDivisor-minus-warm-soft.jsonl.meta
NullMoveEvalDivisor-plus-cold-soft.jsonl
NullMoveEvalDivisor-plus-cold-soft.jsonl.meta
NullMoveEvalDivisor-plus-warm-hard.jsonl
NullMoveEvalDivisor-plus-warm-hard.jsonl.meta
NullMoveEvalDivisor-plus-warm-soft.jsonl
NullMoveEvalDivisor-plus-warm-soft.jsonl.meta
NullMoveMinDepth-minus-cold-soft.jsonl
NullMoveMinDepth-minus-cold-soft.jsonl.meta
NullMoveMinDepth-minus-warm-hard.jsonl
NullMoveMinDepth-minus-warm-hard.jsonl.meta
NullMoveMinDepth-minus-warm-soft.jsonl
NullMoveMinDepth-minus-warm-soft.jsonl.meta
NullMoveMinDepth-plus-cold-soft.jsonl
NullMoveMinDepth-plus-cold-soft.jsonl.meta
NullMoveMinDepth-plus-warm-hard.jsonl
NullMoveMinDepth-plus-warm-hard.jsonl.meta
NullMoveMinDepth-plus-warm-soft.jsonl
NullMoveMinDepth-plus-warm-soft.jsonl.meta
ProbcutDepth-minus-cold-soft.jsonl
ProbcutDepth-minus-cold-soft.jsonl.meta
ProbcutDepth-minus-warm-hard.jsonl
ProbcutDepth-minus-warm-hard.jsonl.meta
ProbcutDepth-minus-warm-soft.jsonl
ProbcutDepth-minus-warm-soft.jsonl.meta
ProbcutDepth-plus-cold-soft.jsonl
ProbcutDepth-plus-cold-soft.jsonl.meta
ProbcutDepth-plus-warm-hard.jsonl
ProbcutDepth-plus-warm-hard.jsonl.meta
ProbcutDepth-plus-warm-soft.jsonl
ProbcutDepth-plus-warm-soft.jsonl.meta
ProbcutMargin-minus-cold-soft.jsonl
ProbcutMargin-minus-cold-soft.jsonl.meta
ProbcutMargin-minus-warm-soft.jsonl
ProbcutMargin-minus-warm-soft.jsonl.meta
ProbcutMargin-plus-cold-soft.jsonl
ProbcutMargin-plus-cold-soft.jsonl.meta
ProbcutMargin-plus-warm-soft.jsonl
ProbcutMargin-plus-warm-soft.jsonl.meta
QsFutilityMargin-minus-cold-soft.jsonl
QsFutilityMargin-minus-cold-soft.jsonl.meta
QsFutilityMargin-minus-warm-hard.jsonl
QsFutilityMargin-minus-warm-hard.jsonl.meta
QsFutilityMargin-minus-warm-soft.jsonl
QsFutilityMargin-minus-warm-soft.jsonl.meta
QsFutilityMargin-plus-cold-soft.jsonl
QsFutilityMargin-plus-cold-soft.jsonl.meta
QsFutilityMargin-plus-warm-hard.jsonl
QsFutilityMargin-plus-warm-hard.jsonl.meta
QsFutilityMargin-plus-warm-soft.jsonl
QsFutilityMargin-plus-warm-soft.jsonl.meta
QsSeeMargin-minus-cold-soft.jsonl
QsSeeMargin-minus-cold-soft.jsonl.meta
QsSeeMargin-minus-warm-soft.jsonl
QsSeeMargin-minus-warm-soft.jsonl.meta
QsSeeMargin-plus-cold-soft.jsonl
QsSeeMargin-plus-cold-soft.jsonl.meta
QsSeeMargin-plus-warm-soft.jsonl
QsSeeMargin-plus-warm-soft.jsonl.meta
RazorBase-minus-cold-soft.jsonl
RazorBase-minus-cold-soft.jsonl.meta
RazorBase-minus-warm-hard.jsonl
RazorBase-minus-warm-hard.jsonl.meta
RazorBase-minus-warm-soft.jsonl
RazorBase-minus-warm-soft.jsonl.meta
RazorBase-plus-cold-soft.jsonl
RazorBase-plus-cold-soft.jsonl.meta
RazorBase-plus-warm-hard.jsonl
RazorBase-plus-warm-hard.jsonl.meta
RazorBase-plus-warm-soft.jsonl
RazorBase-plus-warm-soft.jsonl.meta
RazorDepth-minus-cold-soft.jsonl
RazorDepth-minus-cold-soft.jsonl.meta
RazorDepth-minus-warm-hard.jsonl
RazorDepth-minus-warm-hard.jsonl.meta
RazorDepth-minus-warm-soft.jsonl
RazorDepth-minus-warm-soft.jsonl.meta
RazorDepth-plus-cold-soft.jsonl
RazorDepth-plus-cold-soft.jsonl.meta
RazorDepth-plus-warm-hard.jsonl
RazorDepth-plus-warm-hard.jsonl.meta
RazorDepth-plus-warm-soft.jsonl
RazorDepth-plus-warm-soft.jsonl.meta
RazorMultiplier-minus-cold-soft.jsonl
RazorMultiplier-minus-cold-soft.jsonl.meta
RazorMultiplier-minus-warm-hard.jsonl
RazorMultiplier-minus-warm-hard.jsonl.meta
RazorMultiplier-minus-warm-soft.jsonl
RazorMultiplier-minus-warm-soft.jsonl.meta
RazorMultiplier-plus-cold-soft.jsonl
RazorMultiplier-plus-cold-soft.jsonl.meta
RazorMultiplier-plus-warm-hard.jsonl
RazorMultiplier-plus-warm-hard.jsonl.meta
RazorMultiplier-plus-warm-soft.jsonl
RazorMultiplier-plus-warm-soft.jsonl.meta
RfpDepth-minus-cold-soft.jsonl
RfpDepth-minus-cold-soft.jsonl.meta
RfpDepth-minus-warm-hard.jsonl
RfpDepth-minus-warm-hard.jsonl.meta
RfpDepth-minus-warm-soft.jsonl
RfpDepth-minus-warm-soft.jsonl.meta
RfpDepth-plus-cold-soft.jsonl
RfpDepth-plus-cold-soft.jsonl.meta
RfpDepth-plus-warm-hard.jsonl
RfpDepth-plus-warm-hard.jsonl.meta
RfpDepth-plus-warm-soft.jsonl
RfpDepth-plus-warm-soft.jsonl.meta
RfpImproving-minus-cold-soft.jsonl
RfpImproving-minus-cold-soft.jsonl.meta
RfpImproving-minus-warm-hard.jsonl
RfpImproving-minus-warm-hard.jsonl.meta
RfpImproving-minus-warm-soft.jsonl
RfpImproving-minus-warm-soft.jsonl.meta
RfpImproving-plus-cold-soft.jsonl
RfpImproving-plus-cold-soft.jsonl.meta
RfpImproving-plus-warm-hard.jsonl
RfpImproving-plus-warm-hard.jsonl.meta
RfpImproving-plus-warm-soft.jsonl
RfpImproving-plus-warm-soft.jsonl.meta
RfpMargin-minus-cold-soft.jsonl
RfpMargin-minus-cold-soft.jsonl.meta
RfpMargin-minus-warm-soft.jsonl
RfpMargin-minus-warm-soft.jsonl.meta
RfpMargin-plus-cold-soft.jsonl
RfpMargin-plus-cold-soft.jsonl.meta
RfpMargin-plus-warm-soft.jsonl
RfpMargin-plus-warm-soft.jsonl.meta
SeeNoisyMultiplier-minus-cold-soft.jsonl
SeeNoisyMultiplier-minus-cold-soft.jsonl.meta
SeeNoisyMultiplier-minus-warm-hard.jsonl
SeeNoisyMultiplier-minus-warm-hard.jsonl.meta
SeeNoisyMultiplier-minus-warm-soft.jsonl
SeeNoisyMultiplier-minus-warm-soft.jsonl.meta
SeeNoisyMultiplier-plus-cold-soft.jsonl
SeeNoisyMultiplier-plus-cold-soft.jsonl.meta
SeeNoisyMultiplier-plus-warm-hard.jsonl
SeeNoisyMultiplier-plus-warm-hard.jsonl.meta
SeeNoisyMultiplier-plus-warm-soft.jsonl
SeeNoisyMultiplier-plus-warm-soft.jsonl.meta
SeeQuietMultiplier-minus-cold-soft.jsonl
SeeQuietMultiplier-minus-cold-soft.jsonl.meta
SeeQuietMultiplier-minus-warm-hard.jsonl
SeeQuietMultiplier-minus-warm-hard.jsonl.meta
SeeQuietMultiplier-minus-warm-soft.jsonl
SeeQuietMultiplier-minus-warm-soft.jsonl.meta
SeeQuietMultiplier-plus-cold-soft.jsonl
SeeQuietMultiplier-plus-cold-soft.jsonl.meta
SeeQuietMultiplier-plus-warm-hard.jsonl
SeeQuietMultiplier-plus-warm-hard.jsonl.meta
SeeQuietMultiplier-plus-warm-soft.jsonl
SeeQuietMultiplier-plus-warm-soft.jsonl.meta
SingularDepth-minus-cold-soft.jsonl
SingularDepth-minus-cold-soft.jsonl.meta
SingularDepth-minus-warm-hard.jsonl
SingularDepth-minus-warm-hard.jsonl.meta
SingularDepth-minus-warm-soft.jsonl
SingularDepth-minus-warm-soft.jsonl.meta
SingularDepth-plus-cold-soft.jsonl
SingularDepth-plus-cold-soft.jsonl.meta
SingularDepth-plus-warm-hard.jsonl
SingularDepth-plus-warm-hard.jsonl.meta
SingularDepth-plus-warm-soft.jsonl
SingularDepth-plus-warm-soft.jsonl.meta
SingularMargin-minus-cold-soft.jsonl
SingularMargin-minus-cold-soft.jsonl.meta
SingularMargin-minus-warm-hard.jsonl
SingularMargin-minus-warm-hard.jsonl.meta
SingularMargin-minus-warm-soft.jsonl
SingularMargin-minus-warm-soft.jsonl.meta
SingularMargin-plus-cold-soft.jsonl
SingularMargin-plus-cold-soft.jsonl.meta
SingularMargin-plus-warm-hard.jsonl
SingularMargin-plus-warm-hard.jsonl.meta
SingularMargin-plus-warm-soft.jsonl
SingularMargin-plus-warm-soft.jsonl.meta
base-cold-soft.jsonl
base-cold-soft.jsonl.meta
base-warm-hard.jsonl
base-warm-hard.jsonl.meta
base-warm-soft.jsonl
base-warm-soft.jsonl.meta
```

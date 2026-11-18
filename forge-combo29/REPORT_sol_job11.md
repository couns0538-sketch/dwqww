# Sol — Job 11 independent Stockfish reference

## Step 0, repeat and controls

1. **Both Forge executables passed all eight fresh-process pins.** Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. The counting and tables SHA-256 values matched their previous jobs. [Forge Step 0 receipt](sol/job11/step0.summary.txt)
2. **The official Stockfish 19 build matched its pin.** Tag `sf_19` resolves to `edb0d9db6731067ec50ce619ff372b463bc4dd5d`. The fixed AVX2 build printed `Nodes searched  : 2497913` at `./stockfish bench`. The official script downloaded and validated the single default net, `nn-1a298aa575a0.nnue`. [Compiler, executable and net digests](sol/job11/build.txt) · [Bench stdout](sol/job11/stockfish-bench.raw.txt)
3. **S1 passed 300/300.** The fresh Stockfish process had the same last UCI node count and bestmove at every repeated position, with a summed count of 300,094,246. An independent check also matched depth and last info after removing only time and NPS. The 12 original shards supplied 1,800 searches and 1,800,585,677 summed last-info nodes. [Raw S and S1](sol/job11/S-raw) · [Independent reference check](sol/job11/independent-S.txt)
4. **Both reduced-budget controls passed.** Softnodes 500 against softnodes 2000 lost 240 matches and gained 153, z = −4.3886. Hard nodes 5,000 against 20,000 lost 218 matches and gained 99, z = −6.6837. The matching Forge doubling gained 71 agreements at soft and 51 at hard. Each arm contained 1,800 searches. [Ruler, counts and gates](sol/job11/ruler-readback.txt)

The [prediction](sol/job11/prediction.txt) was the sole file in commit `e326435c12a6f084e8f28122a8928da036689909`, after Step 0, S1 and both controls and before reading A′ or B′ agreement. R means Forge’s 400,000-node reference from Job 10. S means the Stockfish 19 reference at the million-node command. Each doubling column uses the ruler calibrated to its own reference. [UTC sequence](sol/job11/stamps.txt)

## Prediction grades

A nonzero forecast requires the observed sign and a magnitude within a factor of 1.5. A zero forecast requires zero. Incomplete totals and undefined ruler effects remain ungraded.

| Table | Arm or statistic | Budget | Guess | Observed | Grade |
|---|---|---|---:|---:|---|
| A' | warm-base | soft | +0.65 | +1.5493 | KILLED |
| A' | warm-base | hard | +0.50 | +1.5490 | KILLED |
| A' | W1 | soft | -0.30 | -0.4085 | survives |
| A' | W1 | hard | -0.32 | -0.5294 | KILLED |
| A' | W2 | soft | -0.38 | -0.4789 | survives |
| A' | W2 | hard | -0.30 | -0.4314 | survives |
| A' | S-5 | soft | -0.05 | +0.0563 | KILLED (sign) |
| A' | S-5 | hard | +0.04 | +0.0980 | KILLED |
| B' | Arms reaching abs(z) ≥ 3 | soft | 2 | 1/76 measured | KILLED |
| B' | Arms reaching abs(z) ≥ 3 | hard | 3 | 0/76 measured | KILLED (zero) |
| B' | Negative deltas | both | 84 | 57/152 measured | survives |

7 KILLED, 4 survive, 0 ungraded.

## Table R′

| Forge budget | Agree with S | Agree % | a | b | z | Actual nodes | Median actual nodes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| softnodes 500 | 622 | 34.56% | 240 | 153 | -4.3886 | 1409372 | 700.5 |
| softnodes 1000 | 672 | 37.33% | 137 | 100 | -2.4034 | 2835091 | 1427.5 |
| softnodes 2000 | 709 | 39.39% | 0 | 0 | 0.0000 | 5523343 | 2777.0 |
| softnodes 4000 | 780 | 43.33% | 69 | 140 | 4.9112 | 10661486 | 5458.0 |
| softnodes 8000 | 836 | 46.44% | 103 | 230 | 6.9596 | 20882019 | 10629.5 |
| nodes 5000 | 725 | 40.28% | 218 | 99 | -6.6837 | 9000000 | 5000.0 |
| nodes 10000 | 797 | 44.28% | 124 | 77 | -3.3151 | 18000000 | 10000.0 |
| nodes 20000 | 844 | 46.89% | 0 | 0 | 0.0000 | 36000000 | 20000.0 |
| nodes 40000 | 895 | 49.72% | 77 | 128 | 3.5620 | 72000000 | 40000.0 |
| R (nodes 400000) | 1041 | 57.83% | 117 | 314 | 9.4892 | 720000000 | 400000.0 |

Ruler units: U′_soft = 71, U′_hard = 51.
softnodes 500 negative control: a=240, b=153, z=-4.3886, PASS.
nodes 5000 negative control: a=218, b=99, z=-6.6837, PASS.
## Table A'. Replay-arm agreement against Forge R and Stockfish S

| Arm | Budget | Matched base | Agree R | a R | b R | z R | Doublings R | Agree S | a S | b S | z S | Doublings S |
|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| warm-base | soft | cold soft | 953/1800 (52.9444%) | 212 | 314 | +4.4474 | +0.9189 | 819/1800 (45.5000%) | 162 | 272 | +5.2802 | +1.5493 |
| S-1 | soft | warm soft | 948/1800 (52.6667%) | 197 | 192 | -0.2535 | -0.0450 | 825/1800 (45.8333%) | 173 | 179 | +0.3198 | +0.0845 |
| S-2 | soft | warm soft | 929/1800 (51.6111%) | 212 | 188 | -1.2000 | -0.2162 | 794/1800 (44.1111%) | 180 | 155 | -1.3659 | -0.3521 |
| S-5 | soft | warm soft | 949/1800 (52.7222%) | 217 | 213 | -0.1929 | -0.0360 | 823/1800 (45.7222%) | 187 | 191 | +0.2057 | +0.0563 |
| S-7 | soft | warm soft | 923/1800 (51.2778%) | 216 | 186 | -1.4963 | -0.2703 | 795/1800 (44.1667%) | 205 | 181 | -1.2216 | -0.3380 |
| S-3 | soft | warm soft | 948/1800 (52.6667%) | 192 | 187 | -0.2568 | -0.0450 | 812/1800 (45.1111%) | 174 | 167 | -0.3791 | -0.0986 |
| S-4 | soft | warm soft | 946/1800 (52.5556%) | 214 | 207 | -0.3412 | -0.0631 | 821/1800 (45.6111%) | 187 | 189 | +0.1031 | +0.0282 |
| S-6 | soft | warm soft | 944/1800 (52.4444%) | 205 | 196 | -0.4494 | -0.0811 | 818/1800 (45.4444%) | 176 | 175 | -0.0534 | -0.0141 |
| W1 | soft | warm soft | 911/1800 (50.6111%) | 232 | 190 | -2.0445 | -0.3784 | 790/1800 (43.8889%) | 197 | 168 | -1.5179 | -0.4085 |
| W2 | soft | warm soft | 903/1800 (50.1667%) | 263 | 213 | -2.2917 | -0.4505 | 785/1800 (43.6111%) | 218 | 184 | -1.6958 | -0.4789 |
| keep-896 | soft | warm soft | 924/1800 (51.3333%) | 220 | 191 | -1.4305 | -0.2613 | 816/1800 (45.3333%) | 180 | 177 | -0.1588 | -0.0423 |
| keep-768 | soft | warm soft | 957/1800 (53.1667%) | 197 | 201 | +0.2005 | +0.0360 | 805/1800 (44.7222%) | 175 | 161 | -0.7638 | -0.1972 |
| keep-512 | soft | warm soft | 932/1800 (51.7778%) | 230 | 209 | -1.0023 | -0.1892 | 784/1800 (43.5556%) | 206 | 171 | -1.8026 | -0.4930 |
| keep-256 | soft | warm soft | 948/1800 (52.6667%) | 217 | 212 | -0.2414 | -0.0450 | 809/1800 (44.9444%) | 190 | 180 | -0.5199 | -0.1408 |
| keep-0 | soft | warm soft | 918/1800 (51.0000%) | 241 | 206 | -1.6554 | -0.3153 | 774/1800 (43.0000%) | 212 | 167 | -2.3115 | -0.6338 |
| warm-base | hard | cold hard | 1166/1800 (64.7778%) | 206 | 299 | +4.1384 | +0.6691 | 923/1800 (51.2778%) | 168 | 247 | +3.8780 | +1.5490 |
| S-1 | hard | warm hard | 1159/1800 (64.3889%) | 186 | 179 | -0.3664 | -0.0504 | 948/1800 (52.6667%) | 139 | 164 | +1.4362 | +0.4902 |
| S-2 | hard | warm hard | 1164/1800 (64.6667%) | 202 | 200 | -0.0998 | -0.0144 | 948/1800 (52.6667%) | 150 | 175 | +1.3868 | +0.4902 |
| S-5 | hard | warm hard | 1174/1800 (65.2222%) | 200 | 208 | +0.3961 | +0.0576 | 928/1800 (51.5556%) | 160 | 165 | +0.2774 | +0.0980 |
| S-7 | hard | warm hard | 1163/1800 (64.6111%) | 195 | 192 | -0.1525 | -0.0216 | 916/1800 (50.8889%) | 156 | 149 | -0.4008 | -0.1373 |
| S-3 | hard | warm hard | 1127/1800 (62.6111%) | 206 | 167 | -2.0193 | -0.2806 | 911/1800 (50.6111%) | 156 | 144 | -0.6928 | -0.2353 |
| S-4 | hard | warm hard | 1119/1800 (62.1667%) | 214 | 167 | -2.4079 | -0.3381 | 939/1800 (52.1667%) | 156 | 172 | +0.8835 | +0.3137 |
| S-6 | hard | warm hard | 1143/1800 (63.5000%) | 217 | 194 | -1.1345 | -0.1655 | 916/1800 (50.8889%) | 167 | 160 | -0.3871 | -0.1373 |
| W1 | hard | warm hard | 1109/1800 (61.6111%) | 239 | 182 | -2.7780 | -0.4101 | 896/1800 (49.7778%) | 190 | 163 | -1.4371 | -0.5294 |
| W2 | hard | warm hard | 1118/1800 (62.1111%) | 253 | 205 | -2.2429 | -0.3453 | 901/1800 (50.0556%) | 187 | 165 | -1.1726 | -0.4314 |
| keep-896 | hard | warm hard | 1140/1800 (63.3333%) | 211 | 185 | -1.3065 | -0.1871 | 939/1800 (52.1667%) | 145 | 161 | +0.9147 | +0.3137 |
| keep-768 | hard | warm hard | 1148/1800 (63.7778%) | 197 | 179 | -0.9283 | -0.1295 | 923/1800 (51.2778%) | 158 | 158 | +0.0000 | +0.0000 |
| keep-512 | hard | warm hard | 1127/1800 (62.6111%) | 220 | 181 | -1.9476 | -0.2806 | 927/1800 (51.5000%) | 163 | 167 | +0.2202 | +0.0784 |
| keep-256 | hard | warm hard | 1144/1800 (63.5556%) | 206 | 184 | -1.1140 | -0.1583 | 909/1800 (50.5000%) | 168 | 154 | -0.7802 | -0.2745 |
| keep-0 | hard | warm hard | 1133/1800 (62.9444%) | 233 | 200 | -1.5859 | -0.2374 | 905/1800 (50.2778%) | 178 | 160 | -0.9791 | -0.3529 |

## Table B'. One-step tuning arms against Forge R and Stockfish S

Each comparison cell gives agreement-count delta, z and effect in doublings. † marks exact abs(z) ≥ 3 before rounding.

| Setting | Soft minus R | Soft minus S | Soft plus R | Soft plus S | Hard minus R | Hard minus S | Hard plus R | Hard plus S |
|---|---|---|---|---|---|---|---|---|
| DrawJitter | out of range | out of range | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | out of range | out of range | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 |
| LmrQuietBase | +9, +0.5170, +0.0811 | +26, +1.6510, +0.3662 | -14, -1.0157, -0.1261 | +11, +0.8563, +0.1549 | -39, -1.9524, -0.2806 | +12, +0.6606, +0.2353 | -34, -1.8385, -0.2446 | +20, +1.2172, +0.3922 |
| LmrQuietDivisor | -27, -1.8766, -0.2432 | -7, -0.5203, -0.0986 | -3, -0.1696, -0.0270 | +14, +0.8616, +0.1972 | -19, -1.0028, -0.1367 | +17, +0.9799, +0.3333 | -25, -1.2547, -0.1799 | +8, +0.4472, +0.1569 |
| LmrNoisyBase | +1, +1.0000, +0.0090 | -1, -0.5774, -0.0141 | +3, +1.7321, +0.0270 | +1, +0.5774, +0.0141 | -2, -0.4082, -0.0144 | -4, -0.9428, -0.0784 | -2, -0.4082, -0.0144 | -6, -1.2792, -0.1176 |
| LmrNoisyDivisor | +3, +1.0000, +0.0270 | +0, +0.0000, +0.0000 | -2, -0.7071, -0.0180 | +1, +0.3333, +0.0141 | -9, -1.6164, -0.0647 | -7, -1.4000, -0.1373 | -1, -0.1325, -0.0072 | -3, -0.4376, -0.0588 |
| NullMoveMinDepth | +2, +1.4142, +0.0180 | +1, +1.0000, +0.0141 | +7, +0.8819, +0.0631 | +6, +0.8165, +0.0845 | +2, +1.4142, +0.0144 | +2, +1.4142, +0.0392 | +5, +0.3319, +0.0360 | +10, +0.7372, +0.1961 |
| NullMoveBase | +0, +0.0000, +0.0000 | -1, -0.4472, -0.0141 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | -29, -2.5938, -0.2086 | -7, -0.6831, -0.1373 | -5, -0.7625, -0.0360 | +3, +0.5222, +0.0588 |
| NullMoveDepthDivisor | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | -1, -0.4472, -0.0141 | -3, -0.4685, -0.0216 | +2, +0.3536, +0.0392 | -20, -2.0000, -0.1439 | -7, -0.7259, -0.1373 |
| NullMoveEvalDivisor | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 |
| RfpDepth | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +2, +0.5774, +0.0144 | +4, +1.1547, +0.0784 | -2, -1.4142, -0.0144 | -2, -1.4142, -0.0392 |
| RfpMargin | -24, -1.3172, -0.2162 | -1, -0.0588, -0.0141 | +9, +0.4917, +0.0811 | +26, +1.5164, +0.3662 | -30, -1.4467, -0.2158 | -6, -0.3207, -0.1176 | -27, -1.3351, -0.1942 | +8, +0.4276, +0.1569 |
| RfpImproving | -7, -0.3825, -0.0631 | +12, +0.7096, +0.1690 | -37, -2.0096, -0.3333 | +0, +0.0000, +0.0000 | -19, -0.9173, -0.1367 | +15, +0.8052, +0.2941 | -35, -1.7392, -0.2518 | -4, -0.2085, -0.0784 |
| RazorDepth | +5, +0.9285, +0.0450 | +2, +0.3922, +0.0282 | -2, -0.4472, -0.0180 | -2, -0.4714, -0.0282 | -13, -1.3200, -0.0935 | -10, -1.1471, -0.1961 | -9, -1.2857, -0.0647 | -6, -0.9487, -0.1176 |
| RazorBase | -1, -0.4472, -0.0090 | +0, +0.0000, +0.0000 | -3, -1.3416, -0.0270 | +0, +0.0000, +0.0000 | +9, +1.2362, +0.0647 | +7, +1.1508, +0.1373 | -6, -0.9487, -0.0432 | -3, -0.5388, -0.0588 |
| RazorMultiplier | -2, -0.7071, -0.0180 | +1, +0.5774, +0.0141 | -2, -0.8165, -0.0180 | +1, +0.3780, +0.0141 | +3, +0.3612, +0.0216 | +7, +0.9615, +0.1373 | -14, -1.9415, -0.1007 | -9, -1.4056, -0.1765 |
| FutilityDepth | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +1, +0.5774, +0.0072 | -1, -0.5774, -0.0196 | -1, -1.0000, -0.0072 | -1, -1.0000, -0.0196 |
| FutilityBase | -2, -1.4142, -0.0180 | -2, -1.4142, -0.0282 | +1, +1.0000, +0.0090 | +1, +1.0000, +0.0141 | -2, -0.5774, -0.0144 | +4, +1.2649, +0.0784 | +2, +0.5345, +0.0144 | -2, -0.7071, -0.0392 |
| FutilityMultiplier | -1, -0.5774, -0.0090 | -1, -0.5774, -0.0141 | +1, +1.0000, +0.0090 | +0, +0.0000, +0.0000 | -2, -0.5345, -0.0144 | +4, +1.2649, +0.0784 | +4, +1.0000, +0.0288 | +3, +0.9045, +0.0588 |
| LmpBase | -6, -0.3333, -0.0541 | -1, -0.0610, -0.0141 | +14, +0.7638, +0.1261 | +12, +0.7276, +0.1690 | -51, -2.5532, -0.3669 | -15, -0.8220, -0.2941 | -58, -2.8369, -0.4173 | -24, -1.3252, -0.4706 |
| HistoryPruneDepth | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 |
| HistoryPruneMultiplier | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | -3, -0.6547, -0.0216 | -2, -0.4714, -0.0392 | +2, +0.4264, +0.0144 | +0, +0.0000, +0.0000 |
| SeeQuietMultiplier | -1, -0.1925, -0.0090 | -2, -0.4714, -0.0282 | -4, -0.2902, -0.0360 | -1, -0.0793, -0.0141 | -7, -0.5013, -0.0504 | +10, +0.7956, +0.1961 | -9, -0.4874, -0.0647 | -8, -0.4869, -0.1569 |
| SeeNoisyMultiplier | +2, +0.5774, +0.0180 | +7, +1.9415, +0.0986 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +7, +0.6965, +0.1373 | -3, -0.6255, -0.0216 | -6, -1.2247, -0.1176 |
| SingularDepth | -39, -2.1836, -0.3514 | -4, -0.2357, -0.0563 | -44, -3.0656, -0.3964 † | -17, -1.2925, -0.2394 | -69, -3.3314, -0.4964 † | -8, -0.4252, -0.1569 | -63, -3.0925, -0.4532 † | -1, -0.0553, -0.0196 |
| SingularMargin | -8, -0.8944, -0.0721 | +3, +0.3511, +0.0423 | -11, -1.1406, -0.0991 | +0, +0.0000, +0.0000 | -29, -1.5704, -0.2086 | +19, +1.1176, +0.3725 | -10, -0.5439, -0.0719 | -2, -0.1204, -0.0392 |
| IirDepth | -8, -0.3849, -0.0721 | +24, +1.2649, +0.3380 | -15, -0.7491, -0.1351 | +38, +2.0254, +0.5352 | -75, -3.4268, -0.5396 † | -1, -0.0494, -0.0196 | -36, -1.6933, -0.2590 | +2, +0.1023, +0.0392 |
| ProbcutDepth | +1, +0.1601, +0.0090 | +3, +0.5222, +0.0423 | +2, +0.5000, +0.0180 | +4, +1.1547, +0.0563 | -23, -1.5909, -0.1655 | -2, -0.1525, -0.0392 | +8, +0.6405, +0.0576 | +12, +1.0366, +0.2353 |
| ProbcutMargin | +0, +0.0000, +0.0000 | -2, -1.0000, -0.0282 | -4, -2.0000, -0.0360 | +2, +1.4142, +0.0282 | +7, +0.9113, +0.0504 | +10, +1.4142, +0.1961 | +1, +0.1302, +0.0072 | +6, +0.8321, +0.1176 |
| QsFutilityMargin | -6, -0.5345, -0.0541 | +4, +0.3885, +0.0563 | -8, -0.7016, -0.0721 | +15, +1.5076, +0.2113 | -4, -0.2243, -0.0288 | +4, +0.2425, +0.0784 | +8, +0.4500, +0.0576 | +5, +0.3131, +0.0980 |
| AspirationDelta | -35, -2.1420, -0.3153 | +20, +1.3423, +0.2817 | -2, -0.1260, -0.0180 | +0, +0.0000, +0.0000 | -11, -0.5387, -0.0791 | +22, +1.2038, +0.4314 | -52, -2.6000, -0.3741 | +0, +0.0000, +0.0000 |
| HistoryBonusQuadratic | -6, -0.7746, -0.0541 | -4, -0.5774, -0.0563 | +4, +0.6172, +0.0360 | +5, +0.9285, +0.0704 | -14, -0.8307, -0.1007 | -2, -0.1307, -0.0392 | -21, -1.2528, -0.1511 | -8, -0.5275, -0.1569 |
| HistoryBonusLinear | -9, -0.8868, -0.0811 | +12, +1.2377, +0.1690 | -5, -0.5241, -0.0450 | +3, +0.3612, +0.0423 | -24, -1.3997, -0.1727 | +14, +0.8552, +0.2745 | -32, -1.9547, -0.2302 | -10, -0.6623, -0.1961 |
| HistoryBonusMax | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | -3, -0.7746, -0.0216 | -5, -1.5076, -0.0980 | -3, -0.7746, -0.0216 | -8, -2.3094, -0.1569 |
| LmrHistoryDivisor | -1, -0.2774, -0.0090 | +2, +0.6325, +0.0282 | -3, -0.8321, -0.0270 | -2, -0.6325, -0.0282 | -25, -1.8185, -0.1799 | -16, -1.2271, -0.3137 | -13, -1.0060, -0.0935 | -9, -0.7634, -0.1765 |
| CheckExtensionDepth | -10, -0.8165, -0.0901 | +2, +0.1796, +0.0282 | -12, -0.9931, -0.1081 | -2, -0.1841, -0.0282 | -39, -2.3691, -0.2806 | -6, -0.3857, -0.1176 | -26, -1.5707, -0.1871 | -9, -0.5871, -0.1765 |
| LmrCutoffThreshold | -22, -1.3439, -0.1982 | +24, +1.5965, +0.3380 | -28, -1.9415, -0.2523 | -2, -0.1499, -0.0282 | -42, -2.1213, -0.3022 | +10, +0.5556, +0.1961 | -31, -1.5924, -0.2230 | -9, -0.5055, -0.1765 |
| MaterialCorrectionWeight | -13, -1.3480, -0.1171 | -12, -1.3416, -0.1690 | -5, -0.5241, -0.0450 | -8, -0.9177, -0.1127 | -6, -0.3651, -0.0432 | +18, +1.1717, +0.3529 | -18, -1.0835, -0.1295 | +11, +0.7176, +0.2157 |
| CaptureFutilityBase | out of range | out of range | -2, -1.0000, -0.0180 | +0, +0.0000, +0.0000 | out of range | out of range | -8, -1.0690, -0.0576 | +1, +0.1400, +0.0196 |
| FailLowContinuationBonus | out of range | out of range | -13, -1.0796, -0.1171 | +14, +1.2675, +0.1972 | out of range | out of range | -26, -1.4184, -0.1871 | -3, -0.1759, -0.0588 |
| EvalSwingMult | out of range | out of range | +23, +1.0553, +0.2072 | +76, +3.7443, +1.0704 † | out of range | out of range | -33, -1.6160, -0.2374 | +28, +1.4716, +0.5490 |

### Arms reaching abs(z) ≥ 3 against either reference

| Setting | Budget | Direction | Flagged against | Delta R | z R | Delta S | z S | Higher agreement direction R | Higher agreement direction S |
|---|---|---|---|---:|---:|---:|---:|---|---|
| SingularDepth | soft | plus | R | -44 | -3.0656 | -17 | -1.2925 | minus (+5 agreements) | – |
| SingularDepth | hard | minus | R | -69 | -3.3314 | -8 | -0.4252 | plus (+6 agreements) | – |
| SingularDepth | hard | plus | R | -63 | -3.0925 | -1 | -0.0553 | plus (+6 agreements) | – |
| IirDepth | hard | minus | R | -75 | -3.4268 | -1 | -0.0494 | plus (+39 agreements) | – |
| EvalSwingMult | soft | plus | S | +23 | +1.0553 | +76 | +3.7443 | – | plus only (minus out of range) |

### Negative deltas and threshold totals

| Reference | Budget | Negative deltas | Flagged arms | Measured arms |
|---|---|---:|---:|---:|
| R | soft | 41 | 1 | 76/76 |
| R | hard | 57 | 3 | 76/76 |
| R | both | 98 | 4 | 152/152 |
| S | soft | 20 | 1 | 76/76 |
| S | hard | 37 | 0 | 76/76 |
| S | both | 57 | 1 | 152/152 |


## Facts

- The Forge warm base matched Stockfish on 110 more soft-budget positions and 79 more hard-budget positions than the cold base, out of 1,800 each. Those gains were +1.5493 and +1.5490 doublings on this ruler, with z of +5.2802 and +3.8780. Actual soft node totals were 6,753,665 warm and 5,523,343 cold. Both hard arms used 36,000,000 actual nodes.
- Clearing either state group reduced Stockfish agreement against warm. W1, clearing hash and evaluator cache, lost 29 soft and 27 hard matches. W2, clearing workers, lost 34 and 22. Neither comparison crossed the absolute z threshold. Mask 5 at keep 729 gave four more soft and five more hard matches than warm, +0.0563 and +0.0980 doublings. The two arms used 6,354,543 and 36,000,000 actual nodes. Its pruning reduction remains the measured Job 9 result. [Job 9 state and history protocols](REPORT_sol_job9.md) · [Per-arm readback](sol/job11/read-counts.txt)
- Negative tuning deltas fell from 98/152 against Forge to 57/152 against Stockfish. None of the four Forge-reference flags repeated against Stockfish. The only Stockfish flag was the cold-soft `EvalSwingMult` plus arm, 0 to 3, with 76 additional matches and z of +3.7443. That arm used 5,501,352 actual nodes versus 5,523,343 at the cold default. Against Forge R, the same arm gained 23 matches and had z of +1.0553. [Setting bounds and start values](sol/job6/settings.tsv) · [Reused soft replay](sol/job6/raw/EvalSwingMult-plus-cold-soft.jsonl)
- Forge R at 400,000 cold nodes agreed with Stockfish S on 1,041/1,800 positions, compared with 895/1,800 at 40,000 hard nodes. The Stockfish command requested 1,000,000 nodes each time. Its last published nodes ranged from 1,000,000 to 1,000,982 because the stop check runs periodically. In the pinned source, `src/search.cpp:2103–2129` checks the limit and `src/search.cpp:2273–2278` takes the PV reporting snapshot. [Pinned Stockfish source](https://github.com/official-stockfish/Stockfish/blob/edb0d9db6731067ec50ce619ff372b463bc4dd5d/src/search.cpp#L2103-L2129)

## Suspicions

- Changing reference appears to remove much of the same-engine preference for default tuning. Warm-state agreement improved with both references, including the equal-node hard comparison. The larger doubling-normalized value against Stockfish partly reflects its smaller ruler increments. The gained-match counts give a direct view alongside the doublings.
- The positive `EvalSwingMult` signal is specific to this cold-soft replay and remains a candidate for a separately gated warm check. Mask 5 kept near-default agreement against both references while reducing pruning in Job 9.

## What I did not do

This job ran the pinned Stockfish build, its bench, the cold reference and its repeat, plus the eight Forge pins per binary. All evaluated Forge arms came from prior raw rows. Matches, training, tuning and PC tests were outside this job.

## What I am not sure about

One Stockfish bestmove is a single judge choice. Multiple good moves can disagree with it, and a different engine, budget or test fixture can change the ordering of arms. The 152 tuning comparisons share game trajectories and baselines. Their threshold flags are descriptive. Match results and strength changes remain unmeasured.

## Reproduction

Forge was PC r15 at `6b98f2170a3210e71beed04bbd2553972c253ed7`, GCC 14.2.0, CMake 4.2.3 Release, libstdc++ `6.0.33`, glibc 2.41, x86-64-v4, `FORGE_MATE_ALPHA_GUARD=1`. Both Forge binaries used the recorded PC20 preset, Threads 1, Hash 16 MiB, one PV, OwnBook false and built-in AL1 s198 with weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. Counting SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`, tables SHA-256 `1a1cd00fdea3fefa446f48034fc34699edbc54703712484ea2e9c8627bbcf8cd`. [Forge build receipt](sol/job9/build.txt)

Stockfish used GCC 14.2.0, GNU Make 4.4.1, x86-64-avx2, Threads 1, Hash 16 MiB and the release net. It issued a cold reset before every search and used the same original FEN and played-move prefix as Forge. Every S and S1 sidecar binds the binary, default NNUE name and build receipt SHA-256 to the settings, fixture and UTC window. [Stockfish build receipt](sol/job11/build.txt) · [Job 3 game fixture](sol/job3/games.txt)

From `forge-combo29/sol/job11`, these commands verify S1 and regenerate the three tables and the per-arm read counts.

```sh
python3 agreement_independent.py --games ../job3/games.txt --s-dir S-raw \
  --r-dir ../job10/R-raw --ruler-dir ../job10/ruler-raw \
  --soft-base ../job6/raw/base-cold-soft.jsonl --hard-base ../job8/raw/base-cold-hard.jsonl
python3 agreement_independent_ab.py ../job3/games.txt --s-dir S-raw \
  --r-dir ../job10/R-raw --units-json ruler-units.json --forge-units-json ../job10/ruler-units.json \
  --job6-raw ../job6/raw --job8-raw ../job8/raw --job8-age ../job8/age-raw \
  --job9-s ../job9/S-raw --job9-w ../job9/W-raw --job10-s2 ../job10/S2-raw \
  --settings ../job6/settings.tsv --prediction prediction.txt
```

[Per-arm and baseline row counts](sol/job11/read-counts.txt) · [UTC stamps](sol/job11/stamps.txt) · [Precommit tree readback](sol/job11/precommit-readback.txt)

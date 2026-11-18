# Sol — Job 10 deep reference agreement

## Step 0, reference identities and controls

1. **Step 0 passed on both unchanged executables.** Fresh processes matched all eight pins. Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 gave 242796 and 656517 bench nodes. PC20 gave 278024 and 587276. The candidate retained both advertised history settings and defaults. [Counting stdout](sol/job10/step0-count.raw.txt) · [Tables stdout](sol/job10/step0-tables.raw.txt)
2. **R1 passed 300/300.** The 12-shard reference searched all 1,800 positions at 400,000 actual nodes each, 720,000,000 in total. A fresh repeat of the first 300 positions matched on reported nodes, actual nodes and bestmove at 120,000,000 actual nodes. The independent readback matched CNT bytes and timing-normalized last info as well.
3. **R2 passed 300/300.** The fresh cold softnodes-2000 prefix matched Job 6 on reported nodes, actual nodes, bestmove and CNT, at 896,581 actual nodes. [Formal R checks](sol/job10/gates-R.txt) · [Independent R readback](sol/job10/independent-R.txt)
4. **Both ruler controls passed.** At 500 softnodes there were 302 lost and 164 new agreements against softnodes 2000, for z = −6.3927. At 5,000 hard nodes there were 297 lost and 104 new against 20,000 hard nodes, for z = −9.6380. Each arm contained 1,800 searches. The test sets and actual node totals are in Table R.

The [prediction](sol/job10/prediction.txt) was the sole file in commit `308e1b33aed42360484e6e968ac976b1b3be014c`. R1, R2 and both controls passed before it. The Table A and B comparisons began after the push. For each base and arm, `a` counts agreement lost and `b` counts agreement gained against the same 400,000-node bestmove. The paired score is `(b-a)/sqrt(a+b)`, with zero when both counts are zero. A doubling is the count change from 2,000 to 4,000 softnodes or from 20,000 to 40,000 hard nodes at the same cold reset. [UTC sequence](sol/job10/stamps.txt)

## Prediction grades

A sign must agree, and a nonzero magnitude must be within a factor of 1.5. A zero forecast requires zero. Incomplete totals and undefined ruler effects stay ungraded.

| Table | Arm or statistic | Budget | Guess | Measured | Grade |
|---|---|---|---:|---:|---|
| A | warm-base | soft | +0.30 | +0.9189 | KILLED |
| A | warm-base | hard | +0.30 | +0.6691 | KILLED |
| A | S-5 | soft | +0.10 | -0.0360 | KILLED (sign) |
| A | S-5 | hard | +0.10 | +0.0576 | KILLED |
| A | W2 | soft | -0.25 | -0.4505 | KILLED |
| A | keep-0 | soft | -0.15 | -0.3153 | KILLED |
| A | keep-0 | hard | -0.20 | -0.2374 | survives |
| B | Arms reaching abs(z) ≥ 3 | soft | 2 | 1/76 measured | KILLED |
| B | Arms reaching abs(z) ≥ 3 | hard | 2 | 3/76 measured | survives |

7 KILLED, 2 survive, 0 ungraded.

## Table R

| Budget | Agree | Agree % | a | b | z | Actual nodes | Median actual nodes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| softnodes 500 | 713 | 39.61% | 302 | 164 | -6.3927 | 1409372 | 700.5 |
| softnodes 1000 | 751 | 41.72% | 191 | 91 | -5.9549 | 2835091 | 1427.5 |
| softnodes 2000 | 851 | 47.28% | 0 | 0 | 0.0000 | 5523343 | 2777.0 |
| softnodes 4000 | 962 | 53.44% | 69 | 180 | 7.0343 | 10661486 | 5458.0 |
| softnodes 8000 | 1059 | 58.83% | 105 | 313 | 10.1736 | 20882019 | 10629.5 |
| nodes 5000 | 880 | 48.89% | 297 | 104 | -9.6380 | 9000000 | 5000.0 |
| nodes 10000 | 971 | 53.94% | 173 | 71 | -6.5299 | 18000000 | 10000.0 |
| nodes 20000 | 1073 | 59.61% | 0 | 0 | 0.0000 | 36000000 | 20000.0 |
| nodes 40000 | 1212 | 67.33% | 64 | 203 | 8.5067 | 72000000 | 40000.0 |

Ruler units: U_soft = 111, U_hard = 139.
softnodes 500 negative control: a=302, b=164, z=-6.3927, PASS.
nodes 5000 negative control: a=297, b=104, z=-9.6380, PASS.
## Table A. Deep cold reference agreement by replay arm

| Arm | Budget | Matched base | Agree with R | a, base only | b, arm only | z | Node doublings |
|---|---|---|---|---:|---:|---:|---:|
| warm-base | soft | cold soft | 953/1800 (52.9444%) | 212 | 314 | +4.4474 | +0.9189 |
| S-1 | soft | warm soft | 948/1800 (52.6667%) | 197 | 192 | -0.2535 | -0.0450 |
| S-2 | soft | warm soft | 929/1800 (51.6111%) | 212 | 188 | -1.2000 | -0.2162 |
| S-5 | soft | warm soft | 949/1800 (52.7222%) | 217 | 213 | -0.1929 | -0.0360 |
| S-7 | soft | warm soft | 923/1800 (51.2778%) | 216 | 186 | -1.4963 | -0.2703 |
| W1 | soft | warm soft | 911/1800 (50.6111%) | 232 | 190 | -2.0445 | -0.3784 |
| W2 | soft | warm soft | 903/1800 (50.1667%) | 263 | 213 | -2.2917 | -0.4505 |
| keep-896 | soft | warm soft | 924/1800 (51.3333%) | 220 | 191 | -1.4305 | -0.2613 |
| keep-768 | soft | warm soft | 957/1800 (53.1667%) | 197 | 201 | +0.2005 | +0.0360 |
| keep-512 | soft | warm soft | 932/1800 (51.7778%) | 230 | 209 | -1.0023 | -0.1892 |
| keep-256 | soft | warm soft | 948/1800 (52.6667%) | 217 | 212 | -0.2414 | -0.0450 |
| keep-0 | soft | warm soft | 918/1800 (51.0000%) | 241 | 206 | -1.6554 | -0.3153 |
| warm-base | hard | cold hard | 1166/1800 (64.7778%) | 206 | 299 | +4.1384 | +0.6691 |
| S-1 | hard | warm hard | 1159/1800 (64.3889%) | 186 | 179 | -0.3664 | -0.0504 |
| S-2 | hard | warm hard | 1164/1800 (64.6667%) | 202 | 200 | -0.0998 | -0.0144 |
| S-5 | hard | warm hard | 1174/1800 (65.2222%) | 200 | 208 | +0.3961 | +0.0576 |
| S-7 | hard | warm hard | 1163/1800 (64.6111%) | 195 | 192 | -0.1525 | -0.0216 |
| W1 | hard | warm hard | 1109/1800 (61.6111%) | 239 | 182 | -2.7780 | -0.4101 |
| W2 | hard | warm hard | 1118/1800 (62.1111%) | 253 | 205 | -2.2429 | -0.3453 |
| keep-896 | hard | warm hard | 1140/1800 (63.3333%) | 211 | 185 | -1.3065 | -0.1871 |
| keep-768 | hard | warm hard | 1148/1800 (63.7778%) | 197 | 179 | -0.9283 | -0.1295 |
| keep-512 | hard | warm hard | 1127/1800 (62.6111%) | 220 | 181 | -1.9476 | -0.2806 |
| keep-256 | hard | warm hard | 1144/1800 (63.5556%) | 206 | 184 | -1.1140 | -0.1583 |
| keep-0 | hard | warm hard | 1133/1800 (62.9444%) | 233 | 200 | -1.5859 | -0.2374 |

## Table B. One-step tuning-arm agreement against cold

Each arm cell gives the signed agreement-count delta, z and effect in doublings. † marks the exact threshold abs(z) ≥ 3 before rounding.

| Setting | Soft minus | Soft plus | Hard minus | Hard plus |
|---|---|---|---|---|
| DrawJitter | out of range | +0, +0.0000, +0.0000 | out of range | +0, +0.0000, +0.0000 |
| LmrQuietBase | +9, +0.5170, +0.0811 | -14, -1.0157, -0.1261 | -39, -1.9524, -0.2806 | -34, -1.8385, -0.2446 |
| LmrQuietDivisor | -27, -1.8766, -0.2432 | -3, -0.1696, -0.0270 | -19, -1.0028, -0.1367 | -25, -1.2547, -0.1799 |
| LmrNoisyBase | +1, +1.0000, +0.0090 | +3, +1.7321, +0.0270 | -2, -0.4082, -0.0144 | -2, -0.4082, -0.0144 |
| LmrNoisyDivisor | +3, +1.0000, +0.0270 | -2, -0.7071, -0.0180 | -9, -1.6164, -0.0647 | -1, -0.1325, -0.0072 |
| NullMoveMinDepth | +2, +1.4142, +0.0180 | +7, +0.8819, +0.0631 | +2, +1.4142, +0.0144 | +5, +0.3319, +0.0360 |
| NullMoveBase | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | -29, -2.5938, -0.2086 | -5, -0.7625, -0.0360 |
| NullMoveDepthDivisor | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | -3, -0.4685, -0.0216 | -20, -2.0000, -0.1439 |
| NullMoveEvalDivisor | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 |
| RfpDepth | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +2, +0.5774, +0.0144 | -2, -1.4142, -0.0144 |
| RfpMargin | -24, -1.3172, -0.2162 | +9, +0.4917, +0.0811 | -30, -1.4467, -0.2158 | -27, -1.3351, -0.1942 |
| RfpImproving | -7, -0.3825, -0.0631 | -37, -2.0096, -0.3333 | -19, -0.9173, -0.1367 | -35, -1.7392, -0.2518 |
| RazorDepth | +5, +0.9285, +0.0450 | -2, -0.4472, -0.0180 | -13, -1.3200, -0.0935 | -9, -1.2857, -0.0647 |
| RazorBase | -1, -0.4472, -0.0090 | -3, -1.3416, -0.0270 | +9, +1.2362, +0.0647 | -6, -0.9487, -0.0432 |
| RazorMultiplier | -2, -0.7071, -0.0180 | -2, -0.8165, -0.0180 | +3, +0.3612, +0.0216 | -14, -1.9415, -0.1007 |
| FutilityDepth | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +1, +0.5774, +0.0072 | -1, -1.0000, -0.0072 |
| FutilityBase | -2, -1.4142, -0.0180 | +1, +1.0000, +0.0090 | -2, -0.5774, -0.0144 | +2, +0.5345, +0.0144 |
| FutilityMultiplier | -1, -0.5774, -0.0090 | +1, +1.0000, +0.0090 | -2, -0.5345, -0.0144 | +4, +1.0000, +0.0288 |
| LmpBase | -6, -0.3333, -0.0541 | +14, +0.7638, +0.1261 | -51, -2.5532, -0.3669 | -58, -2.8369, -0.4173 |
| HistoryPruneDepth | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 |
| HistoryPruneMultiplier | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | -3, -0.6547, -0.0216 | +2, +0.4264, +0.0144 |
| SeeQuietMultiplier | -1, -0.1925, -0.0090 | -4, -0.2902, -0.0360 | -7, -0.5013, -0.0504 | -9, -0.4874, -0.0647 |
| SeeNoisyMultiplier | +2, +0.5774, +0.0180 | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | -3, -0.6255, -0.0216 |
| SingularDepth | -39, -2.1836, -0.3514 | -44, -3.0656, -0.3964 † | -69, -3.3314, -0.4964 † | -63, -3.0925, -0.4532 † |
| SingularMargin | -8, -0.8944, -0.0721 | -11, -1.1406, -0.0991 | -29, -1.5704, -0.2086 | -10, -0.5439, -0.0719 |
| IirDepth | -8, -0.3849, -0.0721 | -15, -0.7491, -0.1351 | -75, -3.4268, -0.5396 † | -36, -1.6933, -0.2590 |
| ProbcutDepth | +1, +0.1601, +0.0090 | +2, +0.5000, +0.0180 | -23, -1.5909, -0.1655 | +8, +0.6405, +0.0576 |
| ProbcutMargin | +0, +0.0000, +0.0000 | -4, -2.0000, -0.0360 | +7, +0.9113, +0.0504 | +1, +0.1302, +0.0072 |
| QsFutilityMargin | -6, -0.5345, -0.0541 | -8, -0.7016, -0.0721 | -4, -0.2243, -0.0288 | +8, +0.4500, +0.0576 |
| AspirationDelta | -35, -2.1420, -0.3153 | -2, -0.1260, -0.0180 | -11, -0.5387, -0.0791 | -52, -2.6000, -0.3741 |
| HistoryBonusQuadratic | -6, -0.7746, -0.0541 | +4, +0.6172, +0.0360 | -14, -0.8307, -0.1007 | -21, -1.2528, -0.1511 |
| HistoryBonusLinear | -9, -0.8868, -0.0811 | -5, -0.5241, -0.0450 | -24, -1.3997, -0.1727 | -32, -1.9547, -0.2302 |
| HistoryBonusMax | +0, +0.0000, +0.0000 | +0, +0.0000, +0.0000 | -3, -0.7746, -0.0216 | -3, -0.7746, -0.0216 |
| LmrHistoryDivisor | -1, -0.2774, -0.0090 | -3, -0.8321, -0.0270 | -25, -1.8185, -0.1799 | -13, -1.0060, -0.0935 |
| CheckExtensionDepth | -10, -0.8165, -0.0901 | -12, -0.9931, -0.1081 | -39, -2.3691, -0.2806 | -26, -1.5707, -0.1871 |
| LmrCutoffThreshold | -22, -1.3439, -0.1982 | -28, -1.9415, -0.2523 | -42, -2.1213, -0.3022 | -31, -1.5924, -0.2230 |
| MaterialCorrectionWeight | -13, -1.3480, -0.1171 | -5, -0.5241, -0.0450 | -6, -0.3651, -0.0432 | -18, -1.0835, -0.1295 |
| CaptureFutilityBase | out of range | -2, -1.0000, -0.0180 | out of range | -8, -1.0690, -0.0576 |
| FailLowContinuationBonus | out of range | -13, -1.0796, -0.1171 | out of range | -26, -1.4184, -0.1871 |
| EvalSwingMult | out of range | +23, +1.0553, +0.2072 | out of range | -33, -1.6160, -0.2374 |

### Arms reaching abs(z) ≥ 3

| Setting | Budget | Direction | Agreement delta | a | b | z | Doublings | Higher-agreement direction |
|---|---|---|---:|---:|---:|---:|---:|---|
| SingularDepth | soft | plus | -44 | 125 | 81 | -3.0656 | -0.3964 | minus (+5 agreements) |
| SingularDepth | hard | minus | -69 | 249 | 180 | -3.3314 | -0.4964 | plus (+6 agreements) |
| SingularDepth | hard | plus | -63 | 239 | 176 | -3.0925 | -0.4532 | plus (+6 agreements) |
| IirDepth | hard | minus | -75 | 277 | 202 | -3.4268 | -0.5396 | plus (+39 agreements) |

soft: 1 of 76 measured arms reach the threshold. 0 of 76 unavailable.

hard: 3 of 76 measured arms reach the threshold. 0 of 76 unavailable.

## Table S2. Additional history-age masks at keep 729

Rates use actual main plus quiescence nodes. Ply groups are 0, 1–9, 10–29 and 30–59. Signed doublings compare with the warm base at the same budget.

| Mask | Budget | Pruning / 1k | Pruning / default | Changed vs default | Changed vs cold | Soft actual nodes | Soft nodes/default | Soft median depth | Changes by ply group | Largest non-opening group | Agree with R | Doublings vs warm |
|---:|---|---:|---:|---|---|---:|---:|---:|---|---|---:|---:|
| 3 | soft | 1.3082 | 0.4966 | 681/1800 (37.8333%) | 856/1800 (47.5556%) | 6492956 | 0.9614 | 8.0 | 0 / 99 / 227 / 355 | 30–59 | 948/1800 (52.6667%) | -0.0450 |
| 4 | soft | 0.5069 | 0.1924 | 720/1800 (40.0000%) | 877/1800 (48.7222%) | 6545601 | 0.9692 | 8.0 | 0 / 105 / 242 / 373 | 30–59 | 946/1800 (52.5556%) | -0.0631 |
| 6 | soft | 0.2518 | 0.0956 | 706/1800 (39.2222%) | 847/1800 (47.0556%) | 6482272 | 0.9598 | 8.0 | 0 / 101 / 246 / 359 | 30–59 | 944/1800 (52.4444%) | -0.0811 |
| 3 | hard | 6.7844 | 0.5368 | 578/1800 (32.1111%) | 766/1800 (42.5556%) | – | – | – | 0 / 107 / 191 / 280 | 30–59 | 1127/1800 (62.6111%) | -0.2806 |
| 4 | hard | 3.4003 | 0.2690 | 584/1800 (32.4444%) | 747/1800 (41.5000%) | – | – | – | 0 / 95 / 203 / 286 | 30–59 | 1119/1800 (62.1667%) | -0.3381 |
| 6 | hard | 1.8400 | 0.1456 | 587/1800 (32.6111%) | 741/1800 (41.1667%) | – | – | – | 0 / 93 / 204 / 290 | 30–59 | 1143/1800 (63.5000%) | -0.1655 |

## Facts

- The cold ruler was monotone over all tested commands within each budget type. One doubling added 111 reference matches in soft and 139 in hard. The 400,000-node reference finished at median reported depth 17 and used all 400,000 counted nodes at every position. [R rows and their sidecars](sol/job10/R-raw) · [Ruler rows](sol/job10/ruler-raw)
- The warm base added 102 reference matches over cold soft and 93 over cold hard, +0.9189 and +0.6691 ruler doublings. The soft arms used 6,753,665 and 5,523,343 actual nodes respectively. Both hard arms used 36,000,000. W1 and W2 each reduced agreement versus warm at both budgets.
- At keep 729, mask 5 ages main and rework. It changed reference agreement by −4 soft and +8 hard out of 1,800 versus warm default. Those counts correspond to −0.0360 and +0.0576 doublings, with z of −0.1929 and +0.3961. The mask used 6,354,543 and 36,000,000 actual nodes. Its pruning rates were 10.57% and 16.14% of default in Job 9. [Job 9 report](REPORT_sol_job9.md)
- The three new masks all passed each of the six 30/30 opening gates before full replay and on readback. Rework alone, mask 4, produced 19.24% of default soft pruning and 26.90% of hard pruning, the lowest rate among the three single-table masks. It recorded seven fewer soft and 47 fewer hard reference agreements than warm default. [Opening-only gate](sol/job10/S2-openings-gate.txt) · [Full opening gate](sol/job10/S2-full-openings.txt) · [S2 raw rows](sol/job10/S2-raw)
- All 76 in-range one-step settings arms per budget were available. One soft arm and three hard arms met the absolute z threshold. All four agreed less often than their respective cold base. The directions and discordant-pair counts are under Table B.

## Suspicions

- Mask 5 remains the butterfly-age configuration to test in a match. Its agreement stayed close to default at both budgets while its pruning rate fell. The drop in hard agreement for rework alone suggests that changing the balance between main and rework matters in this position set.
- Retained state may improve agreement through both worker ordering and the TT. Each single-clear arm scored below warm while the unchanged combined-state hard arm gained 93 matches at the same node count as cold. Separate additive contributions remain unmeasured.

## What I did not do

I used the two already-built Cloud executables and ran no matches, training, tuning or PC programs. I left source code and the PC tune untouched.

## What I am not sure about

The reference is a deeper cold search of the same engine and net. Equally good moves can be counted as disagreements. The 1,800 positions occur in 30 games, so the stated z threshold is descriptive across tested arms. Elo, match noninferiority and a deployment margin for mask 5 remain unmeasured.

## Reproduction

Both builds are Forge PC r15 from `6b98f2170a3210e71beed04bbd2553972c253ed7`, GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and `FORGE_MATE_ALPHA_GUARD=1`. The Job 4 counting binary SHA-256 is `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. The Job 9 tables binary with `HistoryAgeKeep` and `HistoryAgeTables` is `1a1cd00fdea3fefa446f48034fc34699edbc54703712484ea2e9c8627bbcf8cd`. Both used PC20, Threads 1, Hash 16 MiB, one PV, OwnBook false and embedded AL1 s198, weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. The shared fixture is the first 30 Job 3 games. The R and ruler runners issued `ucinewgame` and `isready` before each search. S2 resets were once per game. Exact settings, clocks and executable and input hashes are in each raw file's sidecar. [Job 3 fixture](sol/job3/games.txt) · [Job 9 build receipt](sol/job9/build.txt)

From `forge-combo29/sol/job10`, the following commands regenerate the gates, tables and per-arm read counts.

```sh
python3 agreement_r.py --games ../job3/games.txt --r-dir R-raw --ruler-dir ruler-raw \
  --soft-base ../job6/raw/base-cold-soft.jsonl --hard-base ../job8/raw/base-cold-hard.jsonl
python3 agreement_ab.py ../job3/games.txt --reference-dir R-raw --units-json ruler-units.json \
  --job6-raw ../job6/raw --job8-raw ../job8/raw --job8-age ../job8/age-raw \
  --job9-s ../job9/S-raw --job9-w ../job9/W-raw --settings ../job6/settings.tsv \
  --prediction prediction.txt
python3 agreement_s2.py table ../job3/games.txt --job9-openings ../job9/opening-raw \
  --job6-raw ../job6/raw --job8-raw ../job8/raw --r-dir R-raw --units ruler-units.json
```

[Per-arm and baseline read counts](sol/job10/read-counts.txt) · [UTC stamps](sol/job10/stamps.txt) · [Precommit tree readback](sol/job10/precommit-readback.txt)

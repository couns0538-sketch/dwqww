# Sol — Job 30 whole-search pruning calibration and matches

## Step 0. Reused H and HC

H (`3cf1903d4713ed00acf61965bd20ef6fe01c71db994dbc34f3886faba5a4411c`) and HC (`2c664f4e0f6099a4bed0a3db162d2a07fd479d175fedf5ae7c90e4c1ef875875`) each matched all eight fresh-process pins with `HistoryAgeKeep 1024` explicitly set. Defaults returned 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. The S14 bench pins were 242796 and 656517, and PC20's were 278024 and 587276. [H raw pins](sol/job30/pins/H/step0-count.raw.txt) · [HC raw pins](sol/job30/pins/HC/step0-count.raw.txt) · [Build hashes, library and net receipt](sol/job30/builds.txt)

H is the Job 28 engine with the ageing option. HC is Job 29's pinned telemetry build of H. I reused the two verified executable files. Both used GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and embedded AL1 s198. The weights source SHA-256 is `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. [H build](sol/job28/h-build-receipt.txt) · [HC build](sol/job29/hc-build-receipt.txt)

## Step 2. HC known-answer replays

HC with PC20, Threads 1, Hash 16 and HistoryAgeKeep 896 replayed the first 20 Job 3 games with one `ucinewgame` and `isready` per game. HP27 and last-depth equality is descriptive.

| Replay | Count and move fields matching Kimi | HP27 lines | Last depth nodes | HP27 prunes | HP27 whole-search nodes | HP27 nodes equal last depth | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `go softnodes 2000` | 1,200/1,200 | 1,200 | 4,080,162 | 1,567 | 4,221,357 | 1,178/1,200 | PASS |
| `go nodes 20000` | 1,200/1,200 | 1,200 | 16,285,974 | 63,861 | 24,000,000 | 0/1,200 | PASS |

The hard replay reported exactly 20,000 HP27 nodes on all 1,200 rows.

## Step 3. Restore the soft whole-search prune rate

The corrected baseline `r0` is 11,633 / 4,561,961 × 1,000 = 2.550000, from the Job 29 HC1024 soft replay. The denominator is the HP27 whole-search node count.

HC used PC20, Threads 1, Hash 16, HistoryAgeKeep 896 and `go softnodes 2000`. The m=2220 row reuses Step 2 after verifying the binary, settings, search, fixture and raw SHA-256.

| Multiplier m | HP27 lines | HP27 prunes | HP27 whole-search nodes | Rate per 1,000 | Absolute difference from r0 |
|---:|---:|---:|---:|---:|---:|
| 2220 | 1,200 | 1,567 | 4,221,357 | 0.371208 | 2.178792 |
| 1600 | 1,200 | 3,794 | 4,235,040 | 0.895859 | 1.654141 |
| 1200 | 1,200 | 6,961 | 4,229,865 | 1.645679 | 0.904321 |
| 900 | 1,200 | 15,003 | 4,217,281 | 3.557505 | 1.007506 |
| 600 | 1,200 | 45,747 | 4,293,451 | 10.655065 | 8.105065 |
| 400 | 1,200 | 103,976 | 4,316,200 | 24.089709 | 21.539709 |
| 250 | 1,200 | 203,587 | 4,178,360 | 48.724141 | 46.174141 |

**m* = 1200.** Exact fraction comparison chose the closest rate. The conditional 150 and 80 extension did not trigger.

At `go nodes 20000`, HC keep 896 and m=1200 had 300,080 HP27 prunes over 24,000,000 HP27 whole-search nodes in 1,200 lines, 12.503333 prunes per 1,000 nodes. Kimi5's archived keep 1024 hard rate was 13.059292 from 313,423 HP27 prunes over 24,000,000 HP27 nodes. Archived `ka2_hard_dfl.jsonl` SHA-256 `9e4f140465bf027ddc8e6ec5e970583b16b05cbc13dfb32b60c76643d6f74d9e`.

The prediction was the sole file in commit `752cb12`, after the calibration and before K19. [Frozen prediction](sol/job30/prediction.txt)

## Prediction grades

Ranges are inclusive. A cut uses the complete pairs actually played.

| Match | Forecast Elo | Observed / grade | Forecast unequal pairs | Observed / grade | Forecast reading | Observed / grade |
|---|---|---|---|---|---|---|
| M3 | [-12.00, +10.00] | +1.30 / met | [2000, 2750] | 2447 / met | LEVEL | LEVEL / met |
| M4 | [-16.00, +12.00] | -12.51 / met | [460, 710] | 592 / met | LEVEL | WORSE / missed |

## K19 known-answer control

K19 PASS. H on both sides with PC20, HistoryAgeKeep 896 and HistoryPruneMultiplier 1200. Embedded evaluation, Threads 1, Hash 16, 2,000 nodes per move. All 50 reversed-color pairs had identical ordered UCI moves and scored 1–1. A W-L-D 31-31-38, pentanomial (0, 0, 50, 0, 0), Elo +0.00 [+0.00, +0.00].

## Part B. Ageing with a rescaled pruning threshold

Both sides used H with PC20, embedded evaluation, Threads 1, Hash 16 and OwnBook false. A used HistoryAgeKeep 896 with HistoryPruneMultiplier 1200, and B 1024 with 2220. The two-sided exact sign test is descriptive. The reading uses the symmetric 95% Elo interval computed at full precision from the pentanomial counts.

| Match | Nodes per move | Status | Games | A W-L-D | Pentanomial | Exact same moves / pairs | Better | Worse | Exact two-sided p | Elo [95%] | Reading |
|---|---:|---|---:|---|---|---|---:|---:|---:|---|---|
| M3 | 2,000 | complete | 8000 | 2736-2706-2558 | 387, 819, 1553, 859, 382 | 0/4000 | 1241 | 1206 | 0.491886 | +1.30 [-4.57, +7.17] | **LEVEL** |
| M4 | 20,000 | complete | 2000 | 525-597-878 | 66, 254, 408, 230, 42 | 0/1000 | 272 | 320 | 0.0533062 | -12.51 [-22.81, -2.22] | **WORSE** |

## Descriptive comparison with Job 28 M1

M1 from `f77d7951f36f7cf2bc76fbcd5e40c3f0891555f4` gave +3.74 Elo [-4.69, +12.16] over 2,000 independent opening pairs. Both matches used H with PC20 at 2,000 nodes per move. Their opening sets were disjoint.
M3 minus M1 is **-2.43 Elo [-12.70, +7.84]**. I subtracted the unrounded Elo centers and combined the symmetric 95% halfwidths in quadrature because the two samples were independent.

## What this check cannot see

The PC's engine (its net, its build, its other settings), keep values other than 896, other ways to restore
pruning (depth, the improving factor), budgets other than 2,000 and 20,000 nodes.

## Facts

- The opening books contain 5,050 positions from the pinned official UHO source. I reused Job 29's prepared books after confirming Job 29 had no games and its previous archive inventory still matched all 110 prior PGNs. All selected positions are disjoint from those PGNs and the 100 Job 3 starts. The reserved sets are also disjoint from each other. [Manifest](sol/job30/openings/manifest.json) · [Opening reuse and readback](sol/job30/openings-reuse.txt)
- The chosen soft rate is about 65% of the keep-1024 baseline. The selected hard replay reached about 96% of its corresponding archived baseline. The same multiplier closes different fractions of the rate gap at the two replay budgets. [Exact sweep and hard comparison](sol/job30/step3.txt)
- The M3 archive reached the remote at 20:09:51 UTC before the M4 wrapper started. The split kept all 4,000 pairs together. The largest part is 19,975,565 bytes, and both restore the original 31,266,024-byte PGN. The independent contrast also re-read the committed Job 28 M1 PGN and found no opening overlap. [M3 byte comparison](sol/job30/independent-M3-published.txt) · [Independent M3 minus M1](sol/job30/independent-M3-M1.txt)
- M4 completed all 1,000 pairs at 20:29:54 UTC, before the 20:35:25 cutoff. The 8,077,511-byte PGN, stdout and metadata reached the remote at 20:29:58. Neither measured match required a clock cut. [UTC stamps](sol/job30/stamps.txt) · [M4 byte comparison](sol/job30/independent-M4-published.txt)
- Five of the six forecast cells matched. M4's 95% Elo interval lies wholly below zero, so its declared reading is WORSE. Its descriptive sign test gives p = 0.0533062 from the 272 better and 320 worse pairs. The Elo interval also uses how much each pair's score differed. [M3 independent recount](sol/job30/independent-M3-full.txt) · [M4 independent recount](sol/job30/independent-M4-full.txt)

## Suspicions

The selected multiplier brought the aggregate hard-replay pruning rate close to baseline. The poorer M4 score suggests that the aggregate rate can hide changes in which quiet moves the rule actually drops. This match changes ageing and multiplier together, so it cannot attribute the score to either setting alone. [Calibration](sol/job30/step3.txt) · [Match readback](sol/job30/readback.txt)

## What I did not do

I used HC for replay telemetry and H for match play. All work ran in the cloud. I made no tracked engine-source edits and ran no training or tests on the owner's PC.

## What I am not sure about

The soft replay's coarse grid brackets the target. A multiplier between 900 and 1200 could match it more closely, and this job gives no comparative game result for another multiplier. The whole-search rates describe these replay positions and search commands. [Sweep](sol/job30/step3.txt)

## Reproduction

The recorded matches used four fastchess workers, the pinned official UHO opening source, reversed colors, one PV, and a 300-move ceiling. Both engines used H with PC20, Threads 1, Hash 16, OwnBook false and the same embedded AL1 s198 evaluation. [Raw UCI, fastchess and PGN records](sol/job30/raw)

From `forge-combo29/sol/job30`, use Python 3 and python-chess 1.11.2. For a split PGN, join its ordered parts with Job 27's splitter before running the readback. Set `restored_m3_pgn` to an unused scratch path.

```sh
python3 ../job27/split_pgn.py join raw/M3.pgn.manifest.json "$restored_m3_pgn"
python3 analyze_matches30.py raw --manifest openings/manifest.json --m-star 1200 \
  --history-root .. --prediction prediction.txt --m3-pgn "$restored_m3_pgn"
```

[UTC stamps](sol/job30/stamps.txt) · [Final readback](sol/job30/readback.txt) · [Precommit tree](sol/job30/precommit-readback.txt)

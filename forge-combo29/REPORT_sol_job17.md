# Sol — Job 17 EvalSwingMax and dose-24 replication

## Step 0 and gates

1. **The counting executable passed all eight fresh-process pins.** Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. Counting SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. UCI advertised `option name EvalSwingMax type spin default 200 min 50 max 400`. Fastchess printed `fastchess alpha 1.8.3 20261107-d7b47e8` and the opening EPD SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. [Step 0 stdout](sol/job17/step0-count.raw.txt) · [Build and book receipt](sol/job17/build.txt)
2. **K6 passed 50/50.** At 2,000 nodes with PC20, Mult 3 and Max 400 explicitly on both sides, every reversed-color pair had the same ordered moves and scored 1–1. Both UCI preflights ended at `readyok` with zero refusals. W-L-D was 33–33–34 and pentanomial `[0, 0, 50, 0, 0]` in 100 games. [K6 PGN](sol/job17/raw/K6.pgn) · [Both UCI preflights](sol/job17/raw/K6.meta)
3. **C6 passed.** On 200 games with plain PC20 at 10,000 versus 20,000 nodes, A scored 23–112–65 and pentanomial `[26, 43, 25, 6, 0]`. Elo was −166.23 and the 95% interval was [−202.92, −129.54]. It met the −100 threshold and the upper bound was below zero. [C6 PGN](sol/job17/raw/C6.pgn) · [C6 output](sol/job17/raw/C6.out) · [Gate readback](sol/job17/gates-K6C6.txt)

The [prediction](sol/job17/prediction.txt) was the sole file in commit `30708ac9d7d95409f0c4c147c9b4d3f501ff7b0f`. Both gates passed before it, and the two measured slots started after the push. Slot 1 ran X400r, E24kr, X400m3, X100m3 and E48k sequentially at 2,000 nodes. Slot 2 ran X400w at 20,000 nodes. Each slot used two workers. [UTC stamps](sol/job17/stamps.txt)

## Prediction grades

The observed Elo must have the forecast sign and fall within a factor of 1.5 of its magnitude. A zero forecast requires zero. Replication forecasts use exact yes/no matching.

| Forecast | Guess | Observed | Grade | Evidence status |
|---|---:|---:|---|---|
| X400r Elo | -7.00 | +1.56 | KILLED (sign) | complete |
| E24kr Elo | +14.00 | +28.90 | KILLED | complete |
| X400m3 Elo | -4.00 | +7.30 | KILLED (sign) | complete |
| X100m3 Elo | -2.00 | -2.78 | survives | complete |
| E48k Elo | +13.00 | +40.48 | KILLED | complete |
| X400w Elo | +4.00 | -1.95 | KILLED (sign) | complete |
| X400 REPLICATED | yes | no | KILLED | complete: interval reconstructed from summed penta counts |
| E24k REPLICATED | yes | yes | survives | complete: interval reconstructed from summed penta counts |

6 KILLED, 2 survive, 0 ungraded.

## Table M. EvalSwing moves and paired games

W-L-D is from A's perspective. The 95% intervals use the fastchess pentanomial Elo ± halfwidth convention. Same moves compare the complete ordered UCI sequence within a color-reversed pair.

| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Reading |
|---|---|---:|---|---|---|---:|---|
| X400 | complete | 2000 | 648-707-645 | 57, 162, 598, 149, 34 | -10.25 [-19.08, -1.42] | 50/1000 | two-seed LOSS comparison |
| X400r | complete | 2000 | 675-666-659 | 48, 158, 585, 155, 54 | +1.56 [-7.58, +10.70] | 57/1000 | two-seed LOSS comparison |
| X400 + X400r pooled | complete: interval reconstructed from summed penta counts | 4000 | 1323-1373-1304 | 105, 320, 1183, 304, 88 | -4.34 [-10.70, +2.02] | 107/2000 | two-seed LOSS comparison |
| E24k | complete | 2000 | 748-632-620 | 79, 200, 371, 226, 124 | +20.17 [+8.21, +32.13] | 0/1000 | two-seed gain comparison |
| E24kr | complete | 2000 | 765-599-636 | 78, 184, 359, 252, 127 | +28.90 [+16.88, +40.92] | 0/1000 | two-seed gain comparison |
| E24k + E24kr pooled | complete: interval reconstructed from summed penta counts | 4000 | 1513-1231-1256 | 157, 384, 730, 478, 251 | +24.53 [+16.06, +33.01] | 0/2000 | two-seed gain comparison |
| X400m3 | complete | 2000 | 698-656-646 | 40, 148, 594, 166, 52 | +7.30 [-1.59, +16.19] | 71/1000 | exploratory, interval includes zero |
| X100m3 | complete | 2000 | 672-688-640 | 102, 222, 369, 204, 103 | -2.78 [-14.80, +9.24] | 0/1000 | exploratory, interval includes zero |
| E48k | complete | 2000 | 806-574-620 | 63, 174, 378, 238, 147 | +40.48 [+28.53, +52.43] | 0/1000 | exploratory, earns a fresh seed (above zero) |
| X400w | complete | 1600 | 444-453-703 | 34, 201, 354, 162, 49 | -1.95 [-13.17, +9.27] | 3/800 | exploratory, interval includes zero |

E24k (job 16 + E24kr) gets a verdict by the rule of file 15: REPLICATED when its fresh seed alone gives Elo above 0 AND the pool of its two seeds (pentanomial counts added) has a 95 % interval whose lower end is above 0. X400 (job 16 + X400r) is a LOSS, so the same rule mirrored: REPLICATED when its fresh seed alone gives Elo below 0 AND the pooled interval's upper end is below 0. Every other cell is exploratory: no verdict, a row each; one whose 95 % interval lies wholly above or wholly below 0 earns a fresh seed in a later job before anything is said about it.
X400 REPLICATED: no. Fresh Elo +1.5600, pooled upper 95% bound +2.0164. Evidence complete: interval reconstructed from summed penta counts.
E24k REPLICATED: yes. Fresh Elo +28.9000, pooled lower 95% bound +16.0573. Evidence complete: interval reconstructed from summed penta counts.

## Shared openings

Counts are distinct exact FEN tags shared by two files. Each file contributes one opening per complete color-reversed pair. The inventory shows complete pairs and distinct FEN tags.

| File | Status | Complete pairs | Distinct exact FENs |
|---|---|---:|---:|
| K6 | saved | 50 | 50 |
| C6 | saved | 100 | 100 |
| X400r | complete | 1000 | 1000 |
| E24kr | complete | 1000 | 1000 |
| X400m3 | complete | 1000 | 1000 |
| X100m3 | complete | 1000 | 1000 |
| E48k | complete | 1000 | 1000 |
| X400w | complete | 800 | 800 |
| Job 13 E2 | saved | 1000 | 1000 |
| Job 13 E3k | saved | 1000 | 1000 |
| Job 13 E6 | saved | 500 | 500 |
| Job 14 E3k2 | saved | 1000 | 1000 |
| Job 14 E6b | saved | 1000 | 1000 |
| Job 14 E6k | saved | 1000 | 1000 |
| Job 14 E12k | saved | 1000 | 1000 |
| Job 15 E6k2 | saved | 1000 | 1000 |
| Job 15 E12k2 | saved | 1000 | 1000 |
| Job 15 D12v3 | saved | 1000 | 1000 |
| Job 15 E6m | saved | 1000 | 1000 |
| Job 15 E6t | saved | 1000 | 1000 |
| Job 16 X400 | saved | 1000 | 1000 |
| Job 16 X100 | saved | 1000 | 1000 |
| Job 16 X50 | saved | 1000 | 1000 |
| Job 16 D12v3b | saved | 1000 | 1000 |
| Job 16 E24k | saved | 1000 | 1000 |
| Job 16 X400t | saved | 1000 | 1000 |
| Job 16 E12t | saved | 1000 | 1000 |

| File A | File B | Shared exact FENs |
|---|---|---:|
| K6 | C6 | 0 |
| K6 | X400r | 0 |
| K6 | E24kr | 0 |
| K6 | X400m3 | 0 |
| K6 | X100m3 | 0 |
| K6 | E48k | 0 |
| K6 | X400w | 0 |
| C6 | X400r | 0 |
| C6 | E24kr | 0 |
| C6 | X400m3 | 1 |
| C6 | X100m3 | 0 |
| C6 | E48k | 0 |
| C6 | X400w | 0 |
| X400r | E24kr | 1 |
| X400r | X400m3 | 1 |
| X400r | X100m3 | 0 |
| X400r | E48k | 1 |
| X400r | X400w | 0 |
| E24kr | X400m3 | 1 |
| E24kr | X100m3 | 0 |
| E24kr | E48k | 1 |
| E24kr | X400w | 1 |
| X400m3 | X100m3 | 0 |
| X400m3 | E48k | 0 |
| X400m3 | X400w | 0 |
| X100m3 | E48k | 0 |
| X100m3 | X400w | 1 |
| E48k | X400w | 1 |
| K6 | Job 13 E2 | 0 |
| K6 | Job 13 E3k | 0 |
| K6 | Job 13 E6 | 0 |
| K6 | Job 14 E3k2 | 0 |
| K6 | Job 14 E6b | 0 |
| K6 | Job 14 E6k | 0 |
| K6 | Job 14 E12k | 0 |
| K6 | Job 15 E6k2 | 0 |
| K6 | Job 15 E12k2 | 0 |
| K6 | Job 15 D12v3 | 0 |
| K6 | Job 15 E6m | 0 |
| K6 | Job 15 E6t | 0 |
| K6 | Job 16 X400 | 0 |
| K6 | Job 16 X100 | 0 |
| K6 | Job 16 X50 | 0 |
| K6 | Job 16 D12v3b | 0 |
| K6 | Job 16 E24k | 0 |
| K6 | Job 16 X400t | 0 |
| K6 | Job 16 E12t | 0 |
| C6 | Job 13 E2 | 0 |
| C6 | Job 13 E3k | 0 |
| C6 | Job 13 E6 | 0 |
| C6 | Job 14 E3k2 | 0 |
| C6 | Job 14 E6b | 0 |
| C6 | Job 14 E6k | 0 |
| C6 | Job 14 E12k | 0 |
| C6 | Job 15 E6k2 | 0 |
| C6 | Job 15 E12k2 | 0 |
| C6 | Job 15 D12v3 | 0 |
| C6 | Job 15 E6m | 0 |
| C6 | Job 15 E6t | 0 |
| C6 | Job 16 X400 | 0 |
| C6 | Job 16 X100 | 0 |
| C6 | Job 16 X50 | 0 |
| C6 | Job 16 D12v3b | 0 |
| C6 | Job 16 E24k | 0 |
| C6 | Job 16 X400t | 0 |
| C6 | Job 16 E12t | 0 |
| X400r | Job 13 E2 | 0 |
| X400r | Job 13 E3k | 0 |
| X400r | Job 13 E6 | 0 |
| X400r | Job 14 E3k2 | 0 |
| X400r | Job 14 E6b | 0 |
| X400r | Job 14 E6k | 0 |
| X400r | Job 14 E12k | 1 |
| X400r | Job 15 E6k2 | 0 |
| X400r | Job 15 E12k2 | 0 |
| X400r | Job 15 D12v3 | 0 |
| X400r | Job 15 E6m | 1 |
| X400r | Job 15 E6t | 1 |
| X400r | Job 16 X400 | 0 |
| X400r | Job 16 X100 | 0 |
| X400r | Job 16 X50 | 0 |
| X400r | Job 16 D12v3b | 2 |
| X400r | Job 16 E24k | 1 |
| X400r | Job 16 X400t | 1 |
| X400r | Job 16 E12t | 0 |
| E24kr | Job 13 E2 | 0 |
| E24kr | Job 13 E3k | 0 |
| E24kr | Job 13 E6 | 0 |
| E24kr | Job 14 E3k2 | 1 |
| E24kr | Job 14 E6b | 1 |
| E24kr | Job 14 E6k | 0 |
| E24kr | Job 14 E12k | 0 |
| E24kr | Job 15 E6k2 | 0 |
| E24kr | Job 15 E12k2 | 0 |
| E24kr | Job 15 D12v3 | 0 |
| E24kr | Job 15 E6m | 1 |
| E24kr | Job 15 E6t | 0 |
| E24kr | Job 16 X400 | 0 |
| E24kr | Job 16 X100 | 0 |
| E24kr | Job 16 X50 | 0 |
| E24kr | Job 16 D12v3b | 0 |
| E24kr | Job 16 E24k | 0 |
| E24kr | Job 16 X400t | 0 |
| E24kr | Job 16 E12t | 0 |
| X400m3 | Job 13 E2 | 0 |
| X400m3 | Job 13 E3k | 0 |
| X400m3 | Job 13 E6 | 1 |
| X400m3 | Job 14 E3k2 | 0 |
| X400m3 | Job 14 E6b | 0 |
| X400m3 | Job 14 E6k | 1 |
| X400m3 | Job 14 E12k | 0 |
| X400m3 | Job 15 E6k2 | 1 |
| X400m3 | Job 15 E12k2 | 0 |
| X400m3 | Job 15 D12v3 | 0 |
| X400m3 | Job 15 E6m | 1 |
| X400m3 | Job 15 E6t | 0 |
| X400m3 | Job 16 X400 | 1 |
| X400m3 | Job 16 X100 | 0 |
| X400m3 | Job 16 X50 | 0 |
| X400m3 | Job 16 D12v3b | 0 |
| X400m3 | Job 16 E24k | 0 |
| X400m3 | Job 16 X400t | 0 |
| X400m3 | Job 16 E12t | 0 |
| X100m3 | Job 13 E2 | 0 |
| X100m3 | Job 13 E3k | 0 |
| X100m3 | Job 13 E6 | 0 |
| X100m3 | Job 14 E3k2 | 0 |
| X100m3 | Job 14 E6b | 0 |
| X100m3 | Job 14 E6k | 1 |
| X100m3 | Job 14 E12k | 0 |
| X100m3 | Job 15 E6k2 | 0 |
| X100m3 | Job 15 E12k2 | 0 |
| X100m3 | Job 15 D12v3 | 0 |
| X100m3 | Job 15 E6m | 0 |
| X100m3 | Job 15 E6t | 0 |
| X100m3 | Job 16 X400 | 0 |
| X100m3 | Job 16 X100 | 0 |
| X100m3 | Job 16 X50 | 1 |
| X100m3 | Job 16 D12v3b | 2 |
| X100m3 | Job 16 E24k | 0 |
| X100m3 | Job 16 X400t | 0 |
| X100m3 | Job 16 E12t | 0 |
| E48k | Job 13 E2 | 0 |
| E48k | Job 13 E3k | 2 |
| E48k | Job 13 E6 | 0 |
| E48k | Job 14 E3k2 | 0 |
| E48k | Job 14 E6b | 0 |
| E48k | Job 14 E6k | 0 |
| E48k | Job 14 E12k | 1 |
| E48k | Job 15 E6k2 | 0 |
| E48k | Job 15 E12k2 | 0 |
| E48k | Job 15 D12v3 | 0 |
| E48k | Job 15 E6m | 0 |
| E48k | Job 15 E6t | 0 |
| E48k | Job 16 X400 | 0 |
| E48k | Job 16 X100 | 0 |
| E48k | Job 16 X50 | 1 |
| E48k | Job 16 D12v3b | 0 |
| E48k | Job 16 E24k | 0 |
| E48k | Job 16 X400t | 0 |
| E48k | Job 16 E12t | 1 |
| X400w | Job 13 E2 | 0 |
| X400w | Job 13 E3k | 1 |
| X400w | Job 13 E6 | 0 |
| X400w | Job 14 E3k2 | 0 |
| X400w | Job 14 E6b | 1 |
| X400w | Job 14 E6k | 0 |
| X400w | Job 14 E12k | 0 |
| X400w | Job 15 E6k2 | 1 |
| X400w | Job 15 E12k2 | 0 |
| X400w | Job 15 D12v3 | 1 |
| X400w | Job 15 E6m | 0 |
| X400w | Job 15 E6t | 0 |
| X400w | Job 16 X400 | 0 |
| X400w | Job 16 X100 | 0 |
| X400w | Job 16 X50 | 1 |
| X400w | Job 16 D12v3b | 0 |
| X400w | Job 16 E24k | 0 |
| X400w | Job 16 X400t | 1 |
| X400w | Job 16 E12t | 0 |

## Facts

- All eight scheduled matches completed before 10:50:42Z, with 11,900 scored games in whole color-reversed pairs. The two slots started at 10:03:56Z. Slot 1's later starts were 10:10:01Z, 10:16:13Z, 10:22:33Z and 10:28:53Z. Slot 2's X400w finished last at 10:35:12Z. [Independent PGN, sidecar and opening readback](sol/job17/independent-Job17.txt)
- At 2,000 nodes, Mult 24 versus zero met the declared gain rule. The fresh seed gave +28.90 Elo [+16.88, +40.92]. The 4,000-game pool gave +24.53 [+16.06, +33.01]. The Mult-6 clip-400 loss at the same node budget did not meet the mirrored rule. Its fresh seed gave +1.56 [−7.58, +10.70] and its 4,000-game pool gave −4.34 [−10.70, +2.02].
- Mult 48 versus zero at 2,000 nodes gave +40.48 Elo [+28.53, +52.43] in 2,000 games. It was the only exploratory cell whose interval excluded zero, and it earns a fresh seed under the declared rule. Both Mult-3 clip comparisons and the 20,000-node clip comparison had intervals that included zero.
- The clip-400 loss pool had 107/2,000 pairs with identical ordered moves, and the dose-24 pool had 0/2,000. At Mult 3 and 2,000 nodes, clip 400 gave 71/1,000 identical pairs and clip 100 gave 0/1,000. The Mult-6 clip arm at 20,000 nodes gave 3/800. Table M counts complete move sequences in each pair.
- There were 36 nonzero opening intersections across 180 file comparisons. The largest shared two exact FENs. Each replication pool's two source files had zero opening overlap. The two forecast grades that survived were X100m3's magnitude and the E24k replication verdict. [Full reproducible readback](sol/job17/readback.txt)

## Suspicions

The multiplier-48 arm may extend the low-budget gains seen with dose 24. It used one seed against zero, leaving a direct dose-48 versus dose-24 comparison open. The clip comparisons leave the response to changing Max 200 uncertain at either multiplier.

## What I did not do

Every game used Codex Cloud and the unchanged counting executable. Engine source, weights, training and the owner's running tune were outside this job.

## What I am not sure about

The effects apply to this Forge build, net, preset and these openings. Same-move pairs establish equality of the played move lists. Search-state differences and the number of clip-limited history updates within those games remain unmeasured. Each exploratory cell uses one seed.

## Reproduction

Both sides used Forge PC r15 at `6b98f2170a3210e71beed04bbd2553972c253ed7` with the Job 2 counters and Job 4 buttons, GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and `FORGE_MATE_ALPHA_GUARD=1`. Options were PC20, one thread, Hash 16 MiB, one PV, OwnBook false and embedded AL1 s198 with weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. Both ends of each X arm explicitly set the same multiplier and their prescribed clips. The E arms used the default clip. Each engine's explicit options and preflight reply are in the sidecar. [Forge build](REPORT_sol_job4.md) · [Raw match files](sol/job17/raw)

Fastchess played each sampled FEN in both colors at the declared fixed node budget with a 300-move ceiling and no separate resign or draw adjudication flags. Each measured match logged the rating after every completed pair. The play cutoff was 10:50:42Z. [Build receipt](sol/job17/build.txt) · [UTC and slot evidence](sol/job17/stamps.txt)

From `forge-combo29/sol/job17`, with Python 3 and python-chess 1.11.2, these commands regenerate both gates, Table M's counts and both replication decisions, and the opening table.

```sh
python3 analyze_matches17.py gates raw
python3 analyze_matches17.py table raw --job13-raw ../job13/raw --job14-raw ../job14/raw \
  --job15-raw ../job15/raw --job16-raw ../job16/raw --prediction prediction.txt
```

[Table and opening readback](sol/job17/readback.txt) · [Precommit tree readback](sol/job17/precommit-readback.txt)

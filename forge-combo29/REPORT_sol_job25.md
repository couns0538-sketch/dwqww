# Sol — Job 25 DrawJitter replication and first move differences

## Step 0 and controls

1. **The Job 4 executable matched the eight pins in fresh processes.** Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. The binary SHA-256 was `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. Fastchess printed `fastchess alpha 1.8.3 20261107-d7b47e8`. The official opening EPD SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. [Raw pins](sol/job25/step0-count.raw.txt) · [Build and book receipt](sol/job25/build.txt) · [Independent build check](sol/job25/independent-build.txt)
2. **K14 passed 50/50.** PC20 on both sides at 2,000 nodes gave A 29–29–42 and pentanomial `[0, 0, 50, 0, 0]` over 100 games. Each reversed-color pair had the identical ordered moves and a 1–1 score. Both preflights accepted the complete PC20 settings. [K14 PGN](sol/job25/raw/K14.pgn) · [K14 preflights](sol/job25/raw/K14.meta)
3. **C14 passed.** PC20 at 10,000 versus 20,000 nodes gave A 13–113–74 and pentanomial `[24, 55, 18, 3, 0]` in 200 games. Elo was −190.85 with a 95% interval of [−224.39, −157.31]. [C14 PGN](sol/job25/raw/C14.pgn) · [Independent controls](sol/job25/independent-gates.txt)

The [prediction](sol/job25/prediction.txt) was the sole file in commit `3ca8a41c86a380d0c64f8018dd634f1e12bf285e` after both controls and before measured play. Slot 1 assigned D2r then D2q at 2,000 nodes, followed by D2o if time allowed. Slot 2 assigned D20 at 20,000 nodes. Each slot used two workers. [UTC stamps](sol/job25/stamps.txt)

## Prediction grades

The observed Elo sign and inclusive range are checked separately. The overall Elo forecast survives when both pass. A cut D2r leaves the full 2,000-pair forecast ungraded.

| Match | Elo forecast | Predicted range | Observed | Sign | Range | Overall | Evidence status |
|---|---:|---|---:|---|---|---|---|
| D2r | +1.40 | [-0.60, +3.40] | +0.09 | met | met | survives | complete |
| D2q | +0.60 | [-2.00, +3.20] | +0.00 | missed | met | KILLED | complete |
| D2o | +0.20 | [-2.00, +2.40] | +0.00 | missed | met | KILLED | complete |
| D20 | +1.00 | [-6.00, +8.00] | +0.43 | met | met | survives | complete |

| Count forecast | Forecast | Observed non-1–1 / played | Exact match | Status |
|---|---:|---|---|---|
| D2r non-1–1 | 28 | 9/2000 | missed | complete |

## Table P. Job 25 paired games

All rows use Job 4, PC20, embedded evaluation, Threads 1, Hash 16 and the pinned book. W-L-D is from A's perspective. Intervals use the fastchess symmetric 95% pentanomial Elo ± halfwidth convention. Only complete color-reversed pairs contribute.

| Match | Nodes per move | DrawJitter A/B | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Reading |
|---|---:|---|---|---:|---|---|---|---:|---|
| D2r | 2,000 | 8/0 | complete | 4000 | 1352-1351-1297 | 0, 4, 1991, 5, 0 | +0.09 [-0.42, +0.60] | 1637/2000 | fresh-seed decision |
| D2q | 2,000 | 4/0 | complete | 2000 | 677-677-646 | 0, 2, 996, 2, 0 | +0.00 [-0.68, +0.68] | 818/1000 | exploratory, interval includes zero |
| D2o | 2,000 | 1/0 | complete | 2000 | 694-694-612 | 0, 5, 990, 5, 0 | +0.00 [-1.08, +1.08] | 823/1000 | exploratory, interval includes zero |
| D20 | 20,000 | 8/0 | complete | 1600 | 454-452-694 | 1, 15, 766, 17, 1 | +0.43 [-2.26, +3.12] | 528/800 | exploratory, interval includes zero |
| D2 | 2,000 | 8/0 | complete | 2000 | 701-691-608 | 0, 2, 986, 12, 0 | +1.74 [+0.47, +3.01] | 826/1000 | Job 24 first seed |
| D2 + D2r pooled | 2,000 | 8/0 | complete: interval reconstructed from summed pentanomial counts | 6000 | 2053-2042-1905 | 0, 6, 2977, 17, 0 | +0.64 [+0.09, +1.18] | 2463/3000 | descriptive pool, verdict uses D2r |

## Shared openings

Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct FEN strings. The two tables cover every new-file pair and every new file against every prior measurement.

| File | Status | Complete pairs | Distinct exact FENs |
|---|---|---:|---:|
| K14 | complete | 50 | 50 |
| C14 | complete | 100 | 100 |
| D2r | complete | 2000 | 2000 |
| D2q | complete | 1000 | 1000 |
| D2o | complete | 1000 | 1000 |
| D20 | complete | 800 | 800 |
| Job 17 X400r | complete | 1000 | 1000 |
| Job 17 E24kr | complete | 1000 | 1000 |
| Job 17 X400m3 | complete | 1000 | 1000 |
| Job 17 X100m3 | complete | 1000 | 1000 |
| Job 17 E48k | complete | 1000 | 1000 |
| Job 17 X400w | complete | 800 | 800 |
| Job 18 E48kr | complete | 1000 | 1000 |
| Job 18 D48v24 | complete | 1000 | 1000 |
| Job 18 E64k | complete | 1000 | 1000 |
| Job 18 X400k48 | complete | 1000 | 1000 |
| Job 18 X100k48 | complete | 1000 | 1000 |
| Job 18 E48t | complete | 1000 | 1000 |
| Job 18 E24t | complete | 1000 | 1000 |
| Job 19 E64kr | complete | 1000 | 1000 |
| Job 19 E48tr | complete | 1000 | 1000 |
| Job 19 E64t | incomplete (interrupted) | 944 | 944 |
| Job 19 E48w | complete | 1000 | 1000 |
| Job 20 F7k | complete | 1000 | 1000 |
| Job 20 F7t | complete | 1000 | 1000 |
| Job 20 E64tr | incomplete (interrupted) | 802 | 802 |
| Job 20 F7w | complete | 1000 | 1000 |
| Job 21 E64tr2 | complete | 1000 | 1000 |
| Job 21 F7kr | complete | 1000 | 1000 |
| Job 21 F3k | complete | 1000 | 1000 |
| Job 21 F1k | complete | 1000 | 1000 |
| Job 21 E64w | complete | 1000 | 1000 |
| Job 22 F1kr | complete | 1000 | 1000 |
| Job 22 F3kr | complete | 1000 | 1000 |
| Job 22 F2k | complete | 1000 | 1000 |
| Job 22 F4k | complete | 1000 | 1000 |
| Job 22 F5k | complete | 1000 | 1000 |
| Job 22 F6k | complete | 1000 | 1000 |
| Job 22 E64wr | complete | 1000 | 1000 |
| Job 23 F5kr | complete | 1000 | 1000 |
| Job 23 M128k | complete | 1000 | 1000 |
| Job 23 X400k | complete | 1000 | 1000 |
| Job 23 M96k | complete | 1000 | 1000 |
| Job 23 M128w | complete | 800 | 800 |
| Job 24 L1 | complete | 500 | 500 |
| Job 24 L2 | complete | 500 | 500 |
| Job 24 D2 | complete | 1000 | 1000 |
| Job 24 H2k | complete | 1000 | 1000 |
| Job 24 H20 | complete | 800 | 800 |

### Within Job 25

| File A | File B | Shared exact FENs |
|---|---|---:|
| K14 | C14 | 0 |
| K14 | D2r | 1 |
| K14 | D2q | 0 |
| K14 | D2o | 0 |
| K14 | D20 | 0 |
| C14 | D2r | 1 |
| C14 | D2q | 0 |
| C14 | D2o | 0 |
| C14 | D20 | 0 |
| D2r | D2q | 0 |
| D2r | D2o | 0 |
| D2r | D20 | 2 |
| D2q | D2o | 0 |
| D2q | D20 | 1 |
| D2o | D20 | 1 |

### Job 25 against Jobs 17–24

| File A | File B | Shared exact FENs |
|---|---|---:|
| K14 | Job 17 X400r | 0 |
| K14 | Job 17 E24kr | 0 |
| K14 | Job 17 X400m3 | 1 |
| K14 | Job 17 X100m3 | 0 |
| K14 | Job 17 E48k | 0 |
| K14 | Job 17 X400w | 0 |
| K14 | Job 18 E48kr | 0 |
| K14 | Job 18 D48v24 | 0 |
| K14 | Job 18 E64k | 0 |
| K14 | Job 18 X400k48 | 0 |
| K14 | Job 18 X100k48 | 0 |
| K14 | Job 18 E48t | 0 |
| K14 | Job 18 E24t | 0 |
| K14 | Job 19 E64kr | 0 |
| K14 | Job 19 E48tr | 0 |
| K14 | Job 19 E64t (incomplete) | 0 |
| K14 | Job 19 E48w | 0 |
| K14 | Job 20 F7k | 0 |
| K14 | Job 20 F7t | 0 |
| K14 | Job 20 E64tr (incomplete) | 0 |
| K14 | Job 20 F7w | 0 |
| K14 | Job 21 E64tr2 | 0 |
| K14 | Job 21 F7kr | 0 |
| K14 | Job 21 F3k | 0 |
| K14 | Job 21 F1k | 0 |
| K14 | Job 21 E64w | 0 |
| K14 | Job 22 F1kr | 0 |
| K14 | Job 22 F3kr | 0 |
| K14 | Job 22 F2k | 0 |
| K14 | Job 22 F4k | 0 |
| K14 | Job 22 F5k | 0 |
| K14 | Job 22 F6k | 0 |
| K14 | Job 22 E64wr | 0 |
| K14 | Job 23 F5kr | 0 |
| K14 | Job 23 M128k | 0 |
| K14 | Job 23 X400k | 0 |
| K14 | Job 23 M96k | 0 |
| K14 | Job 23 M128w | 0 |
| K14 | Job 24 L1 | 0 |
| K14 | Job 24 L2 | 0 |
| K14 | Job 24 D2 | 0 |
| K14 | Job 24 H2k | 0 |
| K14 | Job 24 H20 | 0 |
| C14 | Job 17 X400r | 0 |
| C14 | Job 17 E24kr | 0 |
| C14 | Job 17 X400m3 | 0 |
| C14 | Job 17 X100m3 | 0 |
| C14 | Job 17 E48k | 0 |
| C14 | Job 17 X400w | 0 |
| C14 | Job 18 E48kr | 0 |
| C14 | Job 18 D48v24 | 0 |
| C14 | Job 18 E64k | 0 |
| C14 | Job 18 X400k48 | 0 |
| C14 | Job 18 X100k48 | 0 |
| C14 | Job 18 E48t | 0 |
| C14 | Job 18 E24t | 0 |
| C14 | Job 19 E64kr | 0 |
| C14 | Job 19 E48tr | 0 |
| C14 | Job 19 E64t (incomplete) | 0 |
| C14 | Job 19 E48w | 0 |
| C14 | Job 20 F7k | 0 |
| C14 | Job 20 F7t | 0 |
| C14 | Job 20 E64tr (incomplete) | 0 |
| C14 | Job 20 F7w | 0 |
| C14 | Job 21 E64tr2 | 0 |
| C14 | Job 21 F7kr | 0 |
| C14 | Job 21 F3k | 0 |
| C14 | Job 21 F1k | 0 |
| C14 | Job 21 E64w | 0 |
| C14 | Job 22 F1kr | 0 |
| C14 | Job 22 F3kr | 0 |
| C14 | Job 22 F2k | 0 |
| C14 | Job 22 F4k | 0 |
| C14 | Job 22 F5k | 0 |
| C14 | Job 22 F6k | 0 |
| C14 | Job 22 E64wr | 0 |
| C14 | Job 23 F5kr | 0 |
| C14 | Job 23 M128k | 0 |
| C14 | Job 23 X400k | 0 |
| C14 | Job 23 M96k | 0 |
| C14 | Job 23 M128w | 0 |
| C14 | Job 24 L1 | 0 |
| C14 | Job 24 L2 | 0 |
| C14 | Job 24 D2 | 0 |
| C14 | Job 24 H2k | 0 |
| C14 | Job 24 H20 | 0 |
| D2r | Job 17 X400r | 0 |
| D2r | Job 17 E24kr | 0 |
| D2r | Job 17 X400m3 | 1 |
| D2r | Job 17 X100m3 | 0 |
| D2r | Job 17 E48k | 0 |
| D2r | Job 17 X400w | 1 |
| D2r | Job 18 E48kr | 0 |
| D2r | Job 18 D48v24 | 0 |
| D2r | Job 18 E64k | 0 |
| D2r | Job 18 X400k48 | 0 |
| D2r | Job 18 X100k48 | 0 |
| D2r | Job 18 E48t | 0 |
| D2r | Job 18 E24t | 0 |
| D2r | Job 19 E64kr | 0 |
| D2r | Job 19 E48tr | 0 |
| D2r | Job 19 E64t (incomplete) | 0 |
| D2r | Job 19 E48w | 1 |
| D2r | Job 20 F7k | 2 |
| D2r | Job 20 F7t | 2 |
| D2r | Job 20 E64tr (incomplete) | 0 |
| D2r | Job 20 F7w | 0 |
| D2r | Job 21 E64tr2 | 1 |
| D2r | Job 21 F7kr | 0 |
| D2r | Job 21 F3k | 2 |
| D2r | Job 21 F1k | 2 |
| D2r | Job 21 E64w | 0 |
| D2r | Job 22 F1kr | 0 |
| D2r | Job 22 F3kr | 0 |
| D2r | Job 22 F2k | 2 |
| D2r | Job 22 F4k | 1 |
| D2r | Job 22 F5k | 0 |
| D2r | Job 22 F6k | 1 |
| D2r | Job 22 E64wr | 1 |
| D2r | Job 23 F5kr | 1 |
| D2r | Job 23 M128k | 1 |
| D2r | Job 23 X400k | 3 |
| D2r | Job 23 M96k | 4 |
| D2r | Job 23 M128w | 1 |
| D2r | Job 24 L1 | 0 |
| D2r | Job 24 L2 | 0 |
| D2r | Job 24 D2 | 0 |
| D2r | Job 24 H2k | 1 |
| D2r | Job 24 H20 | 0 |
| D2q | Job 17 X400r | 0 |
| D2q | Job 17 E24kr | 0 |
| D2q | Job 17 X400m3 | 0 |
| D2q | Job 17 X100m3 | 0 |
| D2q | Job 17 E48k | 1 |
| D2q | Job 17 X400w | 0 |
| D2q | Job 18 E48kr | 0 |
| D2q | Job 18 D48v24 | 0 |
| D2q | Job 18 E64k | 0 |
| D2q | Job 18 X400k48 | 0 |
| D2q | Job 18 X100k48 | 0 |
| D2q | Job 18 E48t | 1 |
| D2q | Job 18 E24t | 1 |
| D2q | Job 19 E64kr | 0 |
| D2q | Job 19 E48tr | 1 |
| D2q | Job 19 E64t (incomplete) | 0 |
| D2q | Job 19 E48w | 0 |
| D2q | Job 20 F7k | 1 |
| D2q | Job 20 F7t | 0 |
| D2q | Job 20 E64tr (incomplete) | 0 |
| D2q | Job 20 F7w | 0 |
| D2q | Job 21 E64tr2 | 0 |
| D2q | Job 21 F7kr | 0 |
| D2q | Job 21 F3k | 1 |
| D2q | Job 21 F1k | 0 |
| D2q | Job 21 E64w | 0 |
| D2q | Job 22 F1kr | 1 |
| D2q | Job 22 F3kr | 0 |
| D2q | Job 22 F2k | 0 |
| D2q | Job 22 F4k | 0 |
| D2q | Job 22 F5k | 0 |
| D2q | Job 22 F6k | 0 |
| D2q | Job 22 E64wr | 0 |
| D2q | Job 23 F5kr | 0 |
| D2q | Job 23 M128k | 1 |
| D2q | Job 23 X400k | 0 |
| D2q | Job 23 M96k | 0 |
| D2q | Job 23 M128w | 0 |
| D2q | Job 24 L1 | 0 |
| D2q | Job 24 L2 | 0 |
| D2q | Job 24 D2 | 0 |
| D2q | Job 24 H2k | 0 |
| D2q | Job 24 H20 | 0 |
| D2o | Job 17 X400r | 0 |
| D2o | Job 17 E24kr | 0 |
| D2o | Job 17 X400m3 | 0 |
| D2o | Job 17 X100m3 | 0 |
| D2o | Job 17 E48k | 1 |
| D2o | Job 17 X400w | 1 |
| D2o | Job 18 E48kr | 0 |
| D2o | Job 18 D48v24 | 0 |
| D2o | Job 18 E64k | 0 |
| D2o | Job 18 X400k48 | 0 |
| D2o | Job 18 X100k48 | 0 |
| D2o | Job 18 E48t | 0 |
| D2o | Job 18 E24t | 0 |
| D2o | Job 19 E64kr | 0 |
| D2o | Job 19 E48tr | 0 |
| D2o | Job 19 E64t (incomplete) | 1 |
| D2o | Job 19 E48w | 0 |
| D2o | Job 20 F7k | 0 |
| D2o | Job 20 F7t | 1 |
| D2o | Job 20 E64tr (incomplete) | 0 |
| D2o | Job 20 F7w | 0 |
| D2o | Job 21 E64tr2 | 1 |
| D2o | Job 21 F7kr | 0 |
| D2o | Job 21 F3k | 2 |
| D2o | Job 21 F1k | 1 |
| D2o | Job 21 E64w | 0 |
| D2o | Job 22 F1kr | 0 |
| D2o | Job 22 F3kr | 0 |
| D2o | Job 22 F2k | 0 |
| D2o | Job 22 F4k | 0 |
| D2o | Job 22 F5k | 0 |
| D2o | Job 22 F6k | 0 |
| D2o | Job 22 E64wr | 0 |
| D2o | Job 23 F5kr | 1 |
| D2o | Job 23 M128k | 0 |
| D2o | Job 23 X400k | 0 |
| D2o | Job 23 M96k | 2 |
| D2o | Job 23 M128w | 0 |
| D2o | Job 24 L1 | 1 |
| D2o | Job 24 L2 | 0 |
| D2o | Job 24 D2 | 0 |
| D2o | Job 24 H2k | 1 |
| D2o | Job 24 H20 | 0 |
| D20 | Job 17 X400r | 1 |
| D20 | Job 17 E24kr | 0 |
| D20 | Job 17 X400m3 | 0 |
| D20 | Job 17 X100m3 | 0 |
| D20 | Job 17 E48k | 0 |
| D20 | Job 17 X400w | 1 |
| D20 | Job 18 E48kr | 0 |
| D20 | Job 18 D48v24 | 0 |
| D20 | Job 18 E64k | 0 |
| D20 | Job 18 X400k48 | 0 |
| D20 | Job 18 X100k48 | 0 |
| D20 | Job 18 E48t | 0 |
| D20 | Job 18 E24t | 1 |
| D20 | Job 19 E64kr | 0 |
| D20 | Job 19 E48tr | 0 |
| D20 | Job 19 E64t (incomplete) | 0 |
| D20 | Job 19 E48w | 0 |
| D20 | Job 20 F7k | 0 |
| D20 | Job 20 F7t | 0 |
| D20 | Job 20 E64tr (incomplete) | 0 |
| D20 | Job 20 F7w | 0 |
| D20 | Job 21 E64tr2 | 0 |
| D20 | Job 21 F7kr | 0 |
| D20 | Job 21 F3k | 0 |
| D20 | Job 21 F1k | 1 |
| D20 | Job 21 E64w | 2 |
| D20 | Job 22 F1kr | 0 |
| D20 | Job 22 F3kr | 0 |
| D20 | Job 22 F2k | 0 |
| D20 | Job 22 F4k | 0 |
| D20 | Job 22 F5k | 0 |
| D20 | Job 22 F6k | 0 |
| D20 | Job 22 E64wr | 0 |
| D20 | Job 23 F5kr | 1 |
| D20 | Job 23 M128k | 0 |
| D20 | Job 23 X400k | 0 |
| D20 | Job 23 M96k | 0 |
| D20 | Job 23 M128w | 1 |
| D20 | Job 24 L1 | 0 |
| D20 | Job 24 L2 | 0 |
| D20 | Job 24 D2 | 0 |
| D20 | Job 24 H2k | 0 |
| D20 | Job 24 H20 | 1 |

## Table D. Draw terminations

The counts use each PGN's last comment and retain complete pairs. Other includes all remaining draws, including comments without one of the four listed terminal reasons.

| Match | Status | Paired games | Draws | Threefold repetition | Fifty-move rule | Insufficient material | Stalemate | Other |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Job 24 D2 | complete | 2000 | 608 | 312 | 172 | 111 | 13 | 0 |
| K14 | complete | 100 | 42 | 22 | 10 | 10 | 0 | 0 |
| C14 | complete | 200 | 74 | 49 | 10 | 14 | 0 | 1 |
| D2r | complete | 4000 | 1297 | 699 | 334 | 253 | 11 | 0 |
| D2q | complete | 2000 | 646 | 323 | 191 | 117 | 15 | 0 |
| D2o | complete | 2000 | 612 | 353 | 146 | 104 | 9 | 0 |
| D20 | complete | 1600 | 694 | 448 | 113 | 127 | 4 | 2 |

## Table J. D2r pairs with an unequal score

D2r uses Job 4, PC20, built-in evaluation, Threads 1, Hash 16, 2,000 nodes and DrawJitter 8/0. Ply 1 is the first move from the supplied opening FEN, the first known position. Game order follows the PGN within its Round. Repeated means the position immediately after that move occurred earlier in the recorded game, with the same pieces, side to move, castling rights and legal en-passant availability. Clocks are ignored. The ended marker gives the side on move if play had continued.

D2r had 9 non-1–1 scores in 2000 complete pairs.

| Match | Round | Score A–B | First divergent ply | Exact pre-move FEN | Game 1 move | Game 1 engine | Game 1 repeated | Game 2 move | Game 2 engine | Game 2 repeated |
|---|---:|---|---:|---|---|---|---|---|---|---|
| D2r | 65 | 1.5–0.5 | 246 | `8/8/8/3kr3/8/2K5/8/8 b - - 23 129` | d5e4 | A | no | d5d6 | B | no |
| D2r | 318 | 1.5–0.5 | 85 | `7k/6p1/P7/8/2BPp2p/1P1nQ3/3K3q/8 w - - 11 48` | e3e2 | B | yes | d2d1 | A | no |
| D2r | 817 | 0.5–1.5 | 70 | `3r2k1/5p2/5q1p/1p4p1/1P1n4/2Q3PP/5P2/4RBK1 w - - 8 41` | e1e3 | A | no | g1g2 | B | no |
| D2r | 1126 | 1.5–0.5 | 44 | `q2rB1k1/5Qp1/1n1Np2p/2p1P3/1nP5/7b/1P3P1P/4R1K1 b - - 11 29` | g8h7 | B | yes | g8h8 | A | no |
| D2r | 1202 | 1.5–0.5 | 197 | `8/8/6p1/7k/R7/8/6K1/1r6 b - - 5 104` | b1b3 | B | no | b1b5 | A | no |
| D2r | 1283 | 1.5–0.5 | 248 | `8/6k1/6p1/3R3p/7P/5KP1/r4P2/8 w - - 94 132` | d5b5 | B | no | f3g2 | A | no |
| D2r | 1486 | 0.5–1.5 | 81 | `8/2P2pkp/p2RP1p1/1p3bP1/7P/r3K1P1/8/8 w - - 7 48` | e3d2 | B | yes | e3e2 | A | no |
| D2r | 1693 | 0.5–1.5 | 93 | `4Q3/6pk/7p/8/2p5/p1P1K3/q3N1P1/8 w - - 10 55` | e8e4 | B | yes | e8b5 | A | no |
| D2r | 1835 | 0.5–1.5 | 55 | `5rk1/4Qpp1/p2p4/3Bp2P/4P3/P4P2/4q1PK/8 w - - 7 36` | e7g5 | B | yes | h5h6 | A | no |

## Declared verdict

D2r is the second seed of D2: REPLICATED (a gain) when D2r's 95 % interval lies wholly above 0; NOT REPLICATED when its point estimate is at or below 0; otherwise OPEN. The pool D2 + D2r (counts added) is a row, not a verdict.
D2q, D2o and D20 are exploratory, one seed each: no verdict, a row each; one whose 95 % interval lies wholly above or below 0 earns a fresh seed in a later job.
A cut match gives no verdict.

D2r verdict: OPEN. Fresh Elo +0.0900, 95% interval [-0.4200, +0.6000], complete.

## What this check cannot see

The PC's own net (its engine plays with a net, your tree with the built-in evaluation), its compiler and processor; more than one search thread; time controls other than fixed nodes; the soft node limit of the PC's self-play.

## Facts

- All six matches finished before the 18:14:23Z cutoff. D20 finished last at 18:00:01Z. The saved PGNs contain 9,600 measured and 300 control games in complete reversed-color pairs. D2o started with 1,658.5 seconds left and an estimate of 419.8 seconds, using the slowest normalized same-slot run plus 30 seconds. [Independent audit](sol/job25/independent-Job25.txt) · [Optional launch decision](sol/job25/slot-runs.txt)
- The fresh 4,000-game DrawJitter 8 versus zero seed at 2,000 nodes scored +0.09 Elo [−0.42, +0.60]. Its verdict is **OPEN** under the declared fresh-seed rule. The 6,000-game descriptive pool scored +0.64 [+0.09, +1.18] with no shared opening FEN between the two seeds. [Fresh PGN](sol/job25/raw/D2r.pgn) · [Original PGN](sol/job24/raw/D2.pgn)
- D2r had 1,637 identical move lists out of 2,000 pairs. Nine pairs scored something other than 1–1, compared with 28 forecast. Five gave A 1.5 points and four gave A 0.5. Table J's nine rows matched the independent replay. In five of those first differences, B's move returned to a previously recorded position and A's move did not. In the other four, neither move returned to a recorded position. [Rendered-table verification](sol/job25/independent-Tables-DJ-crosscheck.txt) · [Independent position recurrence check](sol/job25/independent-J-recurrence-crosscheck.txt)
- DrawJitter 4 versus zero gave 0.00 Elo [−0.68, +0.68], and 1 versus zero gave 0.00 [−1.08, +1.08]. Each used 2,000 games at 2,000 nodes. At 20,000 nodes, DrawJitter 8 versus zero gave +0.43 [−2.26, +3.12] in 1,600 games. These were the three exploratory comparisons, and their intervals included zero. [PC20 match receipts](sol/job25/raw)
- Table D's seven game and termination totals matched independently recorded PGN terminal comments and fastchess output. D2r recorded 699 threefolds, 334 fifty-move draws, 253 insufficient-material draws and 11 stalemates. All 273 opening intersections matched an independent readback. Two of four Elo signs and all four Elo ranges met the forecast. [Opening audit](sol/job25/openings-audit.txt) · [Full readback](sol/job25/readback.txt)

## Suspicions

In the Job 4 scratch `forge-combo29/src/search.cpp:1580–1587`, the jitter changes repetition and fifty-move leaf scores using the local node count. The fresh seed had few score-changing pairs, and five first differences involved an immediate return to a prior position in the zero-jitter game. The played PGN alone cannot tell how many draw leaves changed score before that move.

## What I did not do

I reused the pinned Job 4 binary. Source and weights in the repository, the owner's PC and tune, and the training loop were outside this job.

## What I am not sure about

Table J can observe previous positions in the recorded game from its supplied opening FEN. It has no earlier opening moves. These replays expose the first played difference and the ensuing position. The evaluations and other positions searched before that decision remain unmeasured. The exploratory settings and deeper budget each use one seed.

## Reproduction

All matches used Forge PC r15 at base `6b98f2170a3210e71beed04bbd2553972c253ed7` plus the PC patch, Job 2 counters and Job 4 buttons. The binary used GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4, `FORGE_MATE_ALPHA_GUARD=1` and embedded AL1 s198 (weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`). [Job 4 build](REPORT_sol_job4.md) · [Build and book receipt](sol/job25/build.txt)

Fastchess used PC20, Threads 1, Hash 16 MiB, one PV, OwnBook false and a 300-move ceiling. Each measured side explicitly set its DrawJitter and played each opening in both colors. Both preflights and exact command are in each sidecar. [PGNs and match receipts](sol/job25/raw)

From `forge-combo29/sol/job25`, with Python 3 and python-chess 1.11.2, these commands regenerate the gates, Tables P, D and J and the opening intersections.

```sh
python3 analyze_matches25.py gates raw
python3 analyze_matches25.py table raw \
  --job17-raw ../job17/raw --job18-raw ../job18/raw --job19-raw ../job19/raw \
  --job20-raw ../job20/raw --job21-raw ../job21/raw --job22-raw ../job22/raw \
  --job23-raw ../job23/raw --job24-raw ../job24/raw --prediction prediction.txt
```

[Full readback](sol/job25/readback.txt) · [UTC stamps](sol/job25/stamps.txt) · [Precommit tree readback](sol/job25/precommit-readback.txt)

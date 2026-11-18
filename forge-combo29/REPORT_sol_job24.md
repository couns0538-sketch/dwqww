# Sol — Job 24 full-game option equivalence and history pruning

## Step 0 and controls

1. **The Job 4 executable matched the eight pins in fresh processes.** Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. The binary SHA-256 was `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. Fastchess printed `fastchess alpha 1.8.3 20261107-d7b47e8`. The official opening EPD SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. [Raw pins](sol/job24/step0-count.raw.txt) · [Build and book receipt](sol/job24/build.txt) · [Independent build check](sol/job24/independent-build.txt)
2. **K13 passed 50/50.** PC20 on both sides at 2,000 nodes gave A 36–36–28 and pentanomial `[0, 0, 50, 0, 0]` over 100 games. Each reversed-color pair had the identical ordered moves and a 1–1 score. Both preflights accepted the complete PC20 settings. [K13 PGN](sol/job24/raw/K13.pgn) · [K13 preflights](sol/job24/raw/K13.meta)
3. **C13 passed.** PC20 at 10,000 versus 20,000 nodes gave A 24–108–68 and pentanomial `[23, 42, 31, 4, 0]` in 200 games. Elo was −155.54 with a 95% interval of [−189.66, −121.42]. [C13 PGN](sol/job24/raw/C13.pgn) · [Independent controls](sol/job24/independent-gates.txt)

The [prediction](sol/job24/prediction.txt) was the sole file in commit `d6b57fe2f6119626740b15fdc673d4455ec57748` after both controls and before measured play. Slot 1 assigned L1, L2 and D2 at 2,000 nodes, followed by H2k if time allowed. Slot 2 assigned H20 at 20,000 nodes. Each slot used two workers. [UTC stamps](sol/job24/stamps.txt)

## Prediction grades

Same-move count ranges apply to all 500 planned pairs in L1 and L2. A cut pair-count forecast is ungraded. For Elo forecasts, the observed sign and inclusive range are checked separately.

| Match | Same-pair forecast | Observed same / played | Range | Status |
|---|---|---:|---|---|
| L1 | [425, 500] | 500/500 | met | complete |
| L2 | [0, 75] | 491/500 | missed | complete |

| Match | Elo forecast | Predicted range | Observed | Sign | Range | Overall | Evidence status |
|---|---:|---|---:|---|---|---|---|
| D2 | +1.00 | [-12.00, +14.00] | +1.74 | met | met | survives | complete |
| H2k | -4.00 | [-18.00, +10.00] | +1.22 | missed | met | KILLED | complete |
| H20 | +8.00 | [-6.00, +22.00] | +1.52 | met | met | survives | complete |

## Table P. Job 24 paired games

All rows use the Job 4 executable, PC20, embedded evaluation, Threads 1, Hash 16 and the pinned book. W-L-D is from A's perspective. Identical pairs share the complete ordered UCI move sequence.

| Match | Nodes per move | Explicit options A/B | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Reading |
|---|---:|---|---|---:|---|---|---|---:|---|
| L1 | 2,000 | HistoryPruneDepth 0/3, HistoryPruneMultiplier 2220/20000 | complete | 1000 | 352-352-296 | 0, 0, 500, 0, 0 | +0.00 [+0.00, +0.00] | 500/500 | move-sequence comparison |
| L2 | 2,000 | NullMoveBase 6/5, NullMoveDepthDivisor 3/1 | complete | 1000 | 331-331-338 | 0, 0, 500, 0, 0 | +0.00 [+0.00, +0.00] | 491/500 | move-sequence comparison |
| D2 | 2,000 | DrawJitter 8/0 | complete | 2000 | 701-691-608 | 0, 2, 986, 12, 0 | +1.74 [+0.47, +3.01] | 826/1000 | exploratory, earns a fresh seed (above zero) |
| H2k | 2,000 | HistoryPruneDepth 0/3, HistoryPruneMultiplier 2220/2220 | complete | 2000 | 681-674-645 | 48, 164, 569, 171, 48 | +1.22 [-7.91, +10.35] | 43/1000 | exploratory, interval includes zero |
| H20 | 20,000 | HistoryPruneDepth 0/3, HistoryPruneMultiplier 2220/2220 | complete | 1600 | 426-419-755 | 31, 195, 350, 184, 40 | +1.52 [-9.44, +12.48] | 0/800 | exploratory, interval includes zero |

## Shared openings

Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct FEN strings. The two tables cover every new-file pair and every new file against every prior measurement.

| File | Status | Complete pairs | Distinct exact FENs |
|---|---|---:|---:|
| K13 | complete | 50 | 50 |
| C13 | complete | 100 | 100 |
| L1 | complete | 500 | 500 |
| L2 | complete | 500 | 500 |
| D2 | complete | 1000 | 1000 |
| H2k | complete | 1000 | 1000 |
| H20 | complete | 800 | 800 |
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

### Within Job 24

| File A | File B | Shared exact FENs |
|---|---|---:|
| K13 | C13 | 0 |
| K13 | L1 | 0 |
| K13 | L2 | 0 |
| K13 | D2 | 0 |
| K13 | H2k | 0 |
| K13 | H20 | 0 |
| C13 | L1 | 0 |
| C13 | L2 | 0 |
| C13 | D2 | 0 |
| C13 | H2k | 0 |
| C13 | H20 | 0 |
| L1 | L2 | 0 |
| L1 | D2 | 0 |
| L1 | H2k | 0 |
| L1 | H20 | 0 |
| L2 | D2 | 0 |
| L2 | H2k | 0 |
| L2 | H20 | 0 |
| D2 | H2k | 1 |
| D2 | H20 | 0 |
| H2k | H20 | 0 |

### Job 24 against Jobs 17–23

| File A | File B | Shared exact FENs |
|---|---|---:|
| K13 | Job 17 X400r | 0 |
| K13 | Job 17 E24kr | 0 |
| K13 | Job 17 X400m3 | 0 |
| K13 | Job 17 X100m3 | 0 |
| K13 | Job 17 E48k | 0 |
| K13 | Job 17 X400w | 0 |
| K13 | Job 18 E48kr | 0 |
| K13 | Job 18 D48v24 | 0 |
| K13 | Job 18 E64k | 0 |
| K13 | Job 18 X400k48 | 0 |
| K13 | Job 18 X100k48 | 0 |
| K13 | Job 18 E48t | 0 |
| K13 | Job 18 E24t | 0 |
| K13 | Job 19 E64kr | 0 |
| K13 | Job 19 E48tr | 0 |
| K13 | Job 19 E64t (incomplete) | 0 |
| K13 | Job 19 E48w | 0 |
| K13 | Job 20 F7k | 0 |
| K13 | Job 20 F7t | 0 |
| K13 | Job 20 E64tr (incomplete) | 0 |
| K13 | Job 20 F7w | 0 |
| K13 | Job 21 E64tr2 | 0 |
| K13 | Job 21 F7kr | 0 |
| K13 | Job 21 F3k | 0 |
| K13 | Job 21 F1k | 0 |
| K13 | Job 21 E64w | 0 |
| K13 | Job 22 F1kr | 0 |
| K13 | Job 22 F3kr | 0 |
| K13 | Job 22 F2k | 0 |
| K13 | Job 22 F4k | 0 |
| K13 | Job 22 F5k | 0 |
| K13 | Job 22 F6k | 0 |
| K13 | Job 22 E64wr | 0 |
| K13 | Job 23 F5kr | 0 |
| K13 | Job 23 M128k | 0 |
| K13 | Job 23 X400k | 0 |
| K13 | Job 23 M96k | 0 |
| K13 | Job 23 M128w | 0 |
| C13 | Job 17 X400r | 0 |
| C13 | Job 17 E24kr | 0 |
| C13 | Job 17 X400m3 | 0 |
| C13 | Job 17 X100m3 | 0 |
| C13 | Job 17 E48k | 0 |
| C13 | Job 17 X400w | 0 |
| C13 | Job 18 E48kr | 0 |
| C13 | Job 18 D48v24 | 0 |
| C13 | Job 18 E64k | 0 |
| C13 | Job 18 X400k48 | 0 |
| C13 | Job 18 X100k48 | 0 |
| C13 | Job 18 E48t | 0 |
| C13 | Job 18 E24t | 0 |
| C13 | Job 19 E64kr | 0 |
| C13 | Job 19 E48tr | 0 |
| C13 | Job 19 E64t (incomplete) | 0 |
| C13 | Job 19 E48w | 0 |
| C13 | Job 20 F7k | 0 |
| C13 | Job 20 F7t | 0 |
| C13 | Job 20 E64tr (incomplete) | 0 |
| C13 | Job 20 F7w | 0 |
| C13 | Job 21 E64tr2 | 1 |
| C13 | Job 21 F7kr | 0 |
| C13 | Job 21 F3k | 0 |
| C13 | Job 21 F1k | 0 |
| C13 | Job 21 E64w | 0 |
| C13 | Job 22 F1kr | 0 |
| C13 | Job 22 F3kr | 0 |
| C13 | Job 22 F2k | 1 |
| C13 | Job 22 F4k | 0 |
| C13 | Job 22 F5k | 0 |
| C13 | Job 22 F6k | 1 |
| C13 | Job 22 E64wr | 0 |
| C13 | Job 23 F5kr | 0 |
| C13 | Job 23 M128k | 0 |
| C13 | Job 23 X400k | 0 |
| C13 | Job 23 M96k | 0 |
| C13 | Job 23 M128w | 0 |
| L1 | Job 17 X400r | 0 |
| L1 | Job 17 E24kr | 0 |
| L1 | Job 17 X400m3 | 0 |
| L1 | Job 17 X100m3 | 1 |
| L1 | Job 17 E48k | 1 |
| L1 | Job 17 X400w | 0 |
| L1 | Job 18 E48kr | 0 |
| L1 | Job 18 D48v24 | 0 |
| L1 | Job 18 E64k | 0 |
| L1 | Job 18 X400k48 | 1 |
| L1 | Job 18 X100k48 | 0 |
| L1 | Job 18 E48t | 0 |
| L1 | Job 18 E24t | 0 |
| L1 | Job 19 E64kr | 0 |
| L1 | Job 19 E48tr | 0 |
| L1 | Job 19 E64t (incomplete) | 1 |
| L1 | Job 19 E48w | 0 |
| L1 | Job 20 F7k | 0 |
| L1 | Job 20 F7t | 0 |
| L1 | Job 20 E64tr (incomplete) | 0 |
| L1 | Job 20 F7w | 0 |
| L1 | Job 21 E64tr2 | 0 |
| L1 | Job 21 F7kr | 0 |
| L1 | Job 21 F3k | 1 |
| L1 | Job 21 F1k | 0 |
| L1 | Job 21 E64w | 0 |
| L1 | Job 22 F1kr | 0 |
| L1 | Job 22 F3kr | 0 |
| L1 | Job 22 F2k | 0 |
| L1 | Job 22 F4k | 0 |
| L1 | Job 22 F5k | 0 |
| L1 | Job 22 F6k | 0 |
| L1 | Job 22 E64wr | 2 |
| L1 | Job 23 F5kr | 0 |
| L1 | Job 23 M128k | 0 |
| L1 | Job 23 X400k | 0 |
| L1 | Job 23 M96k | 0 |
| L1 | Job 23 M128w | 1 |
| L2 | Job 17 X400r | 0 |
| L2 | Job 17 E24kr | 1 |
| L2 | Job 17 X400m3 | 0 |
| L2 | Job 17 X100m3 | 1 |
| L2 | Job 17 E48k | 0 |
| L2 | Job 17 X400w | 0 |
| L2 | Job 18 E48kr | 0 |
| L2 | Job 18 D48v24 | 0 |
| L2 | Job 18 E64k | 0 |
| L2 | Job 18 X400k48 | 0 |
| L2 | Job 18 X100k48 | 0 |
| L2 | Job 18 E48t | 0 |
| L2 | Job 18 E24t | 0 |
| L2 | Job 19 E64kr | 0 |
| L2 | Job 19 E48tr | 0 |
| L2 | Job 19 E64t (incomplete) | 0 |
| L2 | Job 19 E48w | 0 |
| L2 | Job 20 F7k | 0 |
| L2 | Job 20 F7t | 0 |
| L2 | Job 20 E64tr (incomplete) | 1 |
| L2 | Job 20 F7w | 0 |
| L2 | Job 21 E64tr2 | 0 |
| L2 | Job 21 F7kr | 1 |
| L2 | Job 21 F3k | 0 |
| L2 | Job 21 F1k | 1 |
| L2 | Job 21 E64w | 0 |
| L2 | Job 22 F1kr | 1 |
| L2 | Job 22 F3kr | 0 |
| L2 | Job 22 F2k | 0 |
| L2 | Job 22 F4k | 0 |
| L2 | Job 22 F5k | 0 |
| L2 | Job 22 F6k | 0 |
| L2 | Job 22 E64wr | 0 |
| L2 | Job 23 F5kr | 0 |
| L2 | Job 23 M128k | 0 |
| L2 | Job 23 X400k | 0 |
| L2 | Job 23 M96k | 0 |
| L2 | Job 23 M128w | 0 |
| D2 | Job 17 X400r | 0 |
| D2 | Job 17 E24kr | 1 |
| D2 | Job 17 X400m3 | 0 |
| D2 | Job 17 X100m3 | 0 |
| D2 | Job 17 E48k | 1 |
| D2 | Job 17 X400w | 1 |
| D2 | Job 18 E48kr | 0 |
| D2 | Job 18 D48v24 | 0 |
| D2 | Job 18 E64k | 0 |
| D2 | Job 18 X400k48 | 0 |
| D2 | Job 18 X100k48 | 0 |
| D2 | Job 18 E48t | 0 |
| D2 | Job 18 E24t | 0 |
| D2 | Job 19 E64kr | 0 |
| D2 | Job 19 E48tr | 1 |
| D2 | Job 19 E64t (incomplete) | 0 |
| D2 | Job 19 E48w | 0 |
| D2 | Job 20 F7k | 0 |
| D2 | Job 20 F7t | 1 |
| D2 | Job 20 E64tr (incomplete) | 0 |
| D2 | Job 20 F7w | 0 |
| D2 | Job 21 E64tr2 | 1 |
| D2 | Job 21 F7kr | 1 |
| D2 | Job 21 F3k | 0 |
| D2 | Job 21 F1k | 1 |
| D2 | Job 21 E64w | 0 |
| D2 | Job 22 F1kr | 0 |
| D2 | Job 22 F3kr | 0 |
| D2 | Job 22 F2k | 1 |
| D2 | Job 22 F4k | 0 |
| D2 | Job 22 F5k | 0 |
| D2 | Job 22 F6k | 1 |
| D2 | Job 22 E64wr | 0 |
| D2 | Job 23 F5kr | 0 |
| D2 | Job 23 M128k | 0 |
| D2 | Job 23 X400k | 1 |
| D2 | Job 23 M96k | 0 |
| D2 | Job 23 M128w | 0 |
| H2k | Job 17 X400r | 0 |
| H2k | Job 17 E24kr | 0 |
| H2k | Job 17 X400m3 | 1 |
| H2k | Job 17 X100m3 | 0 |
| H2k | Job 17 E48k | 0 |
| H2k | Job 17 X400w | 0 |
| H2k | Job 18 E48kr | 1 |
| H2k | Job 18 D48v24 | 0 |
| H2k | Job 18 E64k | 1 |
| H2k | Job 18 X400k48 | 0 |
| H2k | Job 18 X100k48 | 1 |
| H2k | Job 18 E48t | 0 |
| H2k | Job 18 E24t | 0 |
| H2k | Job 19 E64kr | 1 |
| H2k | Job 19 E48tr | 0 |
| H2k | Job 19 E64t (incomplete) | 0 |
| H2k | Job 19 E48w | 1 |
| H2k | Job 20 F7k | 1 |
| H2k | Job 20 F7t | 1 |
| H2k | Job 20 E64tr (incomplete) | 0 |
| H2k | Job 20 F7w | 0 |
| H2k | Job 21 E64tr2 | 1 |
| H2k | Job 21 F7kr | 0 |
| H2k | Job 21 F3k | 0 |
| H2k | Job 21 F1k | 0 |
| H2k | Job 21 E64w | 0 |
| H2k | Job 22 F1kr | 0 |
| H2k | Job 22 F3kr | 0 |
| H2k | Job 22 F2k | 1 |
| H2k | Job 22 F4k | 0 |
| H2k | Job 22 F5k | 0 |
| H2k | Job 22 F6k | 0 |
| H2k | Job 22 E64wr | 0 |
| H2k | Job 23 F5kr | 0 |
| H2k | Job 23 M128k | 0 |
| H2k | Job 23 X400k | 1 |
| H2k | Job 23 M96k | 0 |
| H2k | Job 23 M128w | 0 |
| H20 | Job 17 X400r | 0 |
| H20 | Job 17 E24kr | 0 |
| H20 | Job 17 X400m3 | 0 |
| H20 | Job 17 X100m3 | 1 |
| H20 | Job 17 E48k | 2 |
| H20 | Job 17 X400w | 0 |
| H20 | Job 18 E48kr | 1 |
| H20 | Job 18 D48v24 | 0 |
| H20 | Job 18 E64k | 0 |
| H20 | Job 18 X400k48 | 0 |
| H20 | Job 18 X100k48 | 0 |
| H20 | Job 18 E48t | 0 |
| H20 | Job 18 E24t | 0 |
| H20 | Job 19 E64kr | 0 |
| H20 | Job 19 E48tr | 0 |
| H20 | Job 19 E64t (incomplete) | 0 |
| H20 | Job 19 E48w | 1 |
| H20 | Job 20 F7k | 3 |
| H20 | Job 20 F7t | 0 |
| H20 | Job 20 E64tr (incomplete) | 1 |
| H20 | Job 20 F7w | 2 |
| H20 | Job 21 E64tr2 | 0 |
| H20 | Job 21 F7kr | 0 |
| H20 | Job 21 F3k | 0 |
| H20 | Job 21 F1k | 1 |
| H20 | Job 21 E64w | 0 |
| H20 | Job 22 F1kr | 1 |
| H20 | Job 22 F3kr | 0 |
| H20 | Job 22 F2k | 0 |
| H20 | Job 22 F4k | 0 |
| H20 | Job 22 F5k | 0 |
| H20 | Job 22 F6k | 1 |
| H20 | Job 22 E64wr | 1 |
| H20 | Job 23 F5kr | 0 |
| H20 | Job 23 M128k | 0 |
| H20 | Job 23 X400k | 1 |
| H20 | Job 23 M96k | 0 |
| H20 | Job 23 M128w | 0 |

## Table L. First move differences in reversed-color pairs

Game 1 and game 2 follow PGN file order within each round. Ply 1 is the first move from the opening FEN. The listed engine is the side on move in that game at the shared position. The ended marker means that game's move list stops at the shared position.

| Match | Status | Identical pairs | Complete pairs | Differing pairs |
|---|---|---:|---:|---:|
| L1 | complete | 500 | 500 | 0 |
| L2 | complete | 491 | 500 | 9 |

| Match | Round | Ply | Exact pre-move FEN | Game 1 move | Game 1 engine | Game 2 move | Game 2 engine |
|---|---:|---:|---|---|---|---|---|
| L2 | 6 | 160 | `8/4k3/6K1/5PR1/8/8/5r2/8 b - - 0 88` | e7f8 | A | f2f3 | B |
| L2 | 35 | 257 | `8/8/8/3R4/8/5K2/3k4/8 b - - 82 136` | d2c2 | B | d2c3 | A |
| L2 | 166 | 131 | `4k3/7R/8/KP6/P1r5/2n5/8/8 w - - 23 71` | a5b6 | B | h7h5 | A |
| L2 | 179 | 124 | `8/8/8/4QK2/8/8/2pk4/3r4 w - - 18 68` | e5d6 | A | e5d5 | B |
| L2 | 190 | 87 | `8/2p2pp1/4k3/p2r2P1/P4R1P/2PK4/8/8 w - - 1 51` | d3c4 | B | d3c2 | A |
| L2 | 271 | 162 | `8/8/3r3p/6pk/1R6/7P/6K1/8 w - - 74 89` | g2g3 | A | g2h2 | B |
| L2 | 288 | 129 | `8/4k3/Q7/4PK1p/8/7P/8/8 w - - 3 73` | a6a3 | A | a6f6 | B |
| L2 | 324 | 143 | `1n6/8/1k6/8/8/2PK4/8/8 w - - 41 76` | d3e3 | A | d3e2 | B |
| L2 | 451 | 139 | `8/7k/p7/1p4pP/1P4P1/6K1/1P2b3/4B3 b - - 27 74` | h7g7 | B | h7h6 | A |

## D2 draw terminations

D2 uses Job 4, PC20, built-in evaluation, Threads 1, Hash 16, 2,000 nodes per move, and DrawJitter 8 for A and 0 for B. The count uses the saved termination tag or final move comment.

| Match | Status | Paired games | Draws | Threefold repetition draws |
|---|---|---:|---:|---:|
| D2 | complete | 2000 | 608 | 312 |

## What this check cannot see

The PC's own net (its engine plays with a net, your tree with the built-in evaluation), its compiler and processor; more than one search thread; time controls other than fixed nodes.

## Facts

- All seven matches finished before the 17:28:05Z cutoff. H20 finished last at 17:13:38Z. The saved PGNs contain 7,600 measured and 300 control games in complete reversed-color pairs. H2k started with 1,981.1 seconds left, above the 423.4-second estimate from the slowest normalized same-slot run plus 30 seconds. [Independent audit](sol/job24/independent-Job24.txt) · [Optional launch decision](sol/job24/slot-runs.txt)
- At 2,000 nodes, L1 gave identical ordered moves in all 500 pairs comparing HistoryPruneDepth 0 with multiplier 2,220 to depth 3 with multiplier 20,000. L2 gave identical ordered moves in 491 of 500 pairs comparing NullMoveBase 6 and divisor 3 to base 5 and divisor 1. All 500 L2 pairs still scored 1–1. The nine first differences fell at relative plies 87 through 257. Table L preserves the exact FEN, each UCI move and the active engine for all nine, and each row matched the independent PGN replay. [L1 PGN](sol/job24/raw/L1.pgn) · [L2 PGN](sol/job24/raw/L2.pgn) · [Divergence readback](sol/job24/independent-Table-L-crosscheck.txt)
- DrawJitter 8 versus 0 at 2,000 nodes scored +1.74 Elo [+0.47, +3.01] in 2,000 games. It had 826 of 1,000 identical move pairs. Of its 608 draws, 312 ended by threefold repetition. The same count appeared in the PGN's terminal move comments and in fastchess's game results. It alone earned a fresh seed under the declared rule. [DrawJitter PGN](sol/job24/raw/D2.pgn) · [DrawJitter output](sol/job24/raw/D2.out)
- At HistoryPruneMultiplier 2,220 on both sides, depth 0 versus 3 scored +1.22 Elo [−7.91, +10.35] at 2,000 nodes in 2,000 games, and +1.52 [−9.44, +12.48] at 20,000 nodes in 1,600 games. Both intervals included zero. All 287 opening counts matched the independent readback. Of the forecast checks, two of three Elo signs and four of five ranges met the rule. The L2 count exceeded the forecast range. [2,000-node depth PGN](sol/job24/raw/H2k.pgn) · [20,000-node depth PGN](sol/job24/raw/H20.pgn) · [Opening and move audit](sol/job24/openings-audit.txt)

## Suspicions

The prediction underestimated how often the two null-move settings choose the same moves over a full game at this budget. Both recipes can reach the same shallow search because the reduction includes `NullMoveBase + depth / NullMoveDepthDivisor`. In this build, HistoryPruneDepth 0 still permits the history gate when the reduced depth is exactly zero, so these matches measure the two depth settings. Their results give no direct count of pruning events. The Job 4 scratch source has those calculations at `forge-combo29/src/search.cpp:2117–2118,2308,2314–2316,2331–2336`.

## What I did not do

I reused the pinned Job 4 binary. Source and weights in the repository, the owner's PC and its running tune, and the training loop were outside this job.

## What I am not sure about

Identical played moves leave internal nodes, scores and ordering unmeasured. The first differences in Table L mark where each game pair separates. They do not identify earlier changes in search state. Each strength comparison uses one seed on the stated build and opening sample.

## Reproduction

All matches used Forge PC r15 at base `6b98f2170a3210e71beed04bbd2553972c253ed7` plus the PC patch, Job 2 counters and Job 4 buttons. The Job 4 executable used GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4, `FORGE_MATE_ALPHA_GUARD=1` and embedded AL1 s198 (weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`). [Job 4 build](REPORT_sol_job4.md) · [Build and book receipt](sol/job24/build.txt)

Fastchess used PC20, Threads 1, Hash 16 MiB, one PV and OwnBook false. It played each opening in both colors with the 300-move ceiling. The two preflights and command in every sidecar show the explicit values on both sides. [PGNs and configured options](sol/job24/raw)

From `forge-combo29/sol/job24`, with Python 3 and python-chess 1.11.2, these commands regenerate both controls, Tables P and L and the opening comparisons.

```sh
python3 analyze_matches24.py gates raw
python3 analyze_matches24.py table raw \
  --job17-raw ../job17/raw --job18-raw ../job18/raw --job19-raw ../job19/raw \
  --job20-raw ../job20/raw --job21-raw ../job21/raw --job22-raw ../job22/raw \
  --job23-raw ../job23/raw --prediction prediction.txt
```

[Full readback](sol/job24/readback.txt) · [UTC stamps](sol/job24/stamps.txt) · [Precommit tree readback](sol/job24/precommit-readback.txt)

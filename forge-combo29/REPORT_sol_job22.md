# Sol — Job 22 fresh seeds and FailHighBlend switches

## Step 0 and controls

1. **Both reused executables matched all eight fresh-process pins.** Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. The Job 4 counting SHA-256 was `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. PCA was `49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a`. Fastchess printed `fastchess alpha 1.8.3 20261107-d7b47e8`. The official opening EPD SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Both engines printed the two EvalSwing lines below. PCA also printed the FailHighBlend line. [Counting UCI](sol/job22/step0-count.raw.txt) · [PCA UCI](sol/job22/step0-pca.raw.txt) · [Build receipt](sol/job22/build.txt) · [Independent build checks](sol/job22/independent-build.txt)

   ```text
   option name EvalSwingMult type spin default 0 min 0 max 64
   option name EvalSwingMax type spin default 200 min 50 max 400
   option name FailHighBlend type spin default 0 min 0 max 7
   ```

2. **K11 passed 50/50.** PCA with PC20 and explicit Mult 0 and FHB 6 on both sides at 2,000 nodes gave 100 games at 35–35–30, pentanomial `[0, 0, 50, 0, 0]`, and identical ordered moves and 1–1 in every reversed-color pair. Both preflights reached `readyok` without a refusal. [K11 PGN](sol/job22/raw/K11.pgn) · [K11 preflights](sol/job22/raw/K11.meta)
3. **C11 passed.** PCA with PC20 and explicit Mult 0 and FHB 0 on both sides at 10,000 versus 20,000 nodes gave A 11–119–70 and pentanomial `[33, 44, 21, 2, 0]` over 200 games. Elo was −209.91 with a 95% interval of [−247.84, −171.98]. [C11 PGN](sol/job22/raw/C11.pgn) · [Independent controls](sol/job22/independent-gates.txt)

The [prediction](sol/job22/prediction.txt) was the sole file in commit `45b95e5814b9b67abf8e72229f5b020d9e632b58` after both controls and before measured play. The concurrent slots used two workers each. Slot 1 assigned F1kr, F3kr, F2k and F4k at 2,000 nodes, followed by F5k and F6k if time allowed. Slot 2 assigned E64wr at 20,000 nodes. [UTC stamps](sol/job22/stamps.txt)

## Prediction grades

The observed Elo must have the forecast sign and fall within a factor of 1.5 of its magnitude. A zero forecast requires zero.

| Forecast | Guess | Observed | Grade | Evidence status |
|---|---:|---:|---|---|
| F1kr Elo | -11.00 | -9.04 | survives | complete |
| F3kr Elo | -15.00 | -8.17 | KILLED | complete |
| F2k Elo | -6.00 | -11.47 | KILLED | complete |
| F4k Elo | -5.00 | -2.43 | KILLED | complete |
| F5k Elo | -15.00 | -20.70 | survives | complete |
| F6k Elo | -11.00 | -8.51 | survives | complete |
| E64wr Elo | +12.00 | +9.90 | survives | complete |

3 KILLED, 4 survive, 0 ungraded.

## Table P. FailHighBlend and EvalSwing paired games

All rows use PC20, embedded evaluation, Threads 1, Hash 16 and the pinned opening book. W-L-D is from A's perspective. Intervals use the fastchess 95% pentanomial Elo ± halfwidth convention. Identical pairs share the complete ordered UCI move sequence.

| Match | Build, nodes per move, options A/B | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Reading |
|---|---|---|---:|---|---|---|---:|---|
| F1kr | PCA, 2,000, FailHighBlend 1/0 and EvalSwingMult 0/0 | complete | 2000 | 655-707-638 | 104, 220, 387, 202, 87 | -9.04 [-20.76, +2.68] | 0/1000 | two-seed loss comparison |
| F3kr | PCA, 2,000, FailHighBlend 3/0 and EvalSwingMult 0/0 | complete | 2000 | 669-716-615 | 112, 219, 369, 204, 96 | -8.17 [-20.23, +3.89] | 0/1000 | two-seed loss comparison |
| F2k | PCA, 2,000, FailHighBlend 2/0 and EvalSwingMult 0/0 | complete | 2000 | 649-715-636 | 106, 221, 391, 197, 85 | -11.47 [-23.17, +0.23] | 0/1000 | exploratory, interval includes zero |
| F4k | PCA, 2,000, FailHighBlend 4/0 and EvalSwingMult 0/0 | complete | 2000 | 672-686-642 | 104, 208, 373, 228, 87 | -2.43 [-14.23, +9.37] | 0/1000 | exploratory, interval includes zero |
| F5k | PCA, 2,000, FailHighBlend 5/0 and EvalSwingMult 0/0 | complete | 2000 | 639-758-603 | 119, 245, 375, 158, 103 | -20.70 [-32.91, -8.49] | 0/1000 | exploratory, earns a fresh seed (below zero) |
| F6k | PCA, 2,000, FailHighBlend 6/0 and EvalSwingMult 0/0 | complete | 2000 | 671-720-609 | 98, 232, 387, 187, 96 | -8.51 [-20.28, +3.26] | 0/1000 | exploratory, interval includes zero |
| E64wr | Job 4, 20,000, EvalSwingMult 64/0 | complete | 2000 | 557-500-943 | 43, 231, 405, 268, 53 | +9.90 [-0.21, +20.01] | 0/1000 | two-seed gain comparison |
| F1k | PCA, 2,000, FailHighBlend 1/0 and EvalSwingMult 0/0 | complete | 2000 | 637-715-648 | 114, 247, 329, 223, 87 | -13.56 [-25.71, -1.41] | 0/1000 | two-seed loss comparison |
| F3k | PCA, 2,000, FailHighBlend 3/0 and EvalSwingMult 0/0 | complete | 2000 | 641-738-621 | 118, 235, 367, 186, 94 | -16.86 [-28.98, -4.74] | 0/1000 | two-seed loss comparison |
| E64w | Job 4, 20,000, EvalSwingMult 64/0 | complete | 2000 | 571-488-941 | 39, 216, 421, 271, 53 | +14.43 [+4.49, +24.37] | 0/1000 | two-seed gain comparison |
| F1k + F1kr pooled | PCA, 2,000, FailHighBlend 1/0 and EvalSwingMult 0/0 | complete: interval reconstructed from summed pentanomial counts | 4000 | 1292-1422-1286 | 218, 467, 716, 425, 174 | -11.30 [-19.74, -2.86] | 0/2000 | two-seed loss comparison |
| F3k + F3kr pooled | PCA, 2,000, FailHighBlend 3/0 and EvalSwingMult 0/0 | complete: interval reconstructed from summed pentanomial counts | 4000 | 1310-1454-1236 | 230, 454, 736, 390, 190 | -12.51 [-21.06, -3.97] | 0/2000 | two-seed loss comparison |
| E64w + E64wr pooled | Job 4, 20,000, EvalSwingMult 64/0 | complete: interval reconstructed from summed pentanomial counts | 4000 | 1128-988-1884 | 82, 447, 826, 539, 106 | +12.17 [+5.08, +19.25] | 0/2000 | two-seed gain comparison |

## Shared openings

Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct FEN strings. The two tables account for every scheduled new-file pair and every new-file by prior-file pair.

Job 21 F1k and F1kr distinct shared exact FENs = 0.
Job 21 F3k and F3kr distinct shared exact FENs = 0.
Job 21 E64w and E64wr distinct shared exact FENs = 1.

| File | Status | Complete pairs | Distinct exact FENs |
|---|---|---:|---:|
| K11 | complete | 50 | 50 |
| C11 | complete | 100 | 100 |
| F1kr | complete | 1000 | 1000 |
| F3kr | complete | 1000 | 1000 |
| F2k | complete | 1000 | 1000 |
| F4k | complete | 1000 | 1000 |
| F5k | complete | 1000 | 1000 |
| F6k | complete | 1000 | 1000 |
| E64wr | complete | 1000 | 1000 |
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

### Within Job 22

| File A | File B | Shared exact FENs |
|---|---|---:|
| K11 | C11 | 0 |
| K11 | F1kr | 0 |
| K11 | F3kr | 0 |
| K11 | F2k | 0 |
| K11 | F4k | 0 |
| K11 | F5k | 0 |
| K11 | F6k | 0 |
| K11 | E64wr | 0 |
| C11 | F1kr | 0 |
| C11 | F3kr | 0 |
| C11 | F2k | 0 |
| C11 | F4k | 0 |
| C11 | F5k | 0 |
| C11 | F6k | 0 |
| C11 | E64wr | 0 |
| F1kr | F3kr | 1 |
| F1kr | F2k | 1 |
| F1kr | F4k | 1 |
| F1kr | F5k | 1 |
| F1kr | F6k | 0 |
| F1kr | E64wr | 0 |
| F3kr | F2k | 2 |
| F3kr | F4k | 0 |
| F3kr | F5k | 2 |
| F3kr | F6k | 0 |
| F3kr | E64wr | 0 |
| F2k | F4k | 1 |
| F2k | F5k | 0 |
| F2k | F6k | 0 |
| F2k | E64wr | 1 |
| F4k | F5k | 0 |
| F4k | F6k | 1 |
| F4k | E64wr | 0 |
| F5k | F6k | 1 |
| F5k | E64wr | 0 |
| F6k | E64wr | 0 |

### Job 22 against Jobs 17–21

| File A | File B | Shared exact FENs |
|---|---|---:|
| K11 | Job 17 X400r | 0 |
| K11 | Job 17 E24kr | 0 |
| K11 | Job 17 X400m3 | 0 |
| K11 | Job 17 X100m3 | 0 |
| K11 | Job 17 E48k | 0 |
| K11 | Job 17 X400w | 0 |
| K11 | Job 18 E48kr | 0 |
| K11 | Job 18 D48v24 | 0 |
| K11 | Job 18 E64k | 0 |
| K11 | Job 18 X400k48 | 0 |
| K11 | Job 18 X100k48 | 0 |
| K11 | Job 18 E48t | 0 |
| K11 | Job 18 E24t | 0 |
| K11 | Job 19 E64kr | 0 |
| K11 | Job 19 E48tr | 0 |
| K11 | Job 19 E64t (incomplete) | 0 |
| K11 | Job 19 E48w | 0 |
| K11 | Job 20 F7k | 0 |
| K11 | Job 20 F7t | 0 |
| K11 | Job 20 E64tr (incomplete) | 0 |
| K11 | Job 20 F7w | 0 |
| K11 | Job 21 E64tr2 | 0 |
| K11 | Job 21 F7kr | 0 |
| K11 | Job 21 F3k | 0 |
| K11 | Job 21 F1k | 0 |
| K11 | Job 21 E64w | 0 |
| C11 | Job 17 X400r | 0 |
| C11 | Job 17 E24kr | 0 |
| C11 | Job 17 X400m3 | 0 |
| C11 | Job 17 X100m3 | 0 |
| C11 | Job 17 E48k | 0 |
| C11 | Job 17 X400w | 0 |
| C11 | Job 18 E48kr | 0 |
| C11 | Job 18 D48v24 | 0 |
| C11 | Job 18 E64k | 0 |
| C11 | Job 18 X400k48 | 0 |
| C11 | Job 18 X100k48 | 0 |
| C11 | Job 18 E48t | 0 |
| C11 | Job 18 E24t | 0 |
| C11 | Job 19 E64kr | 0 |
| C11 | Job 19 E48tr | 0 |
| C11 | Job 19 E64t (incomplete) | 0 |
| C11 | Job 19 E48w | 0 |
| C11 | Job 20 F7k | 0 |
| C11 | Job 20 F7t | 0 |
| C11 | Job 20 E64tr (incomplete) | 0 |
| C11 | Job 20 F7w | 0 |
| C11 | Job 21 E64tr2 | 0 |
| C11 | Job 21 F7kr | 0 |
| C11 | Job 21 F3k | 0 |
| C11 | Job 21 F1k | 0 |
| C11 | Job 21 E64w | 0 |
| F1kr | Job 17 X400r | 0 |
| F1kr | Job 17 E24kr | 0 |
| F1kr | Job 17 X400m3 | 0 |
| F1kr | Job 17 X100m3 | 0 |
| F1kr | Job 17 E48k | 0 |
| F1kr | Job 17 X400w | 0 |
| F1kr | Job 18 E48kr | 0 |
| F1kr | Job 18 D48v24 | 1 |
| F1kr | Job 18 E64k | 0 |
| F1kr | Job 18 X400k48 | 2 |
| F1kr | Job 18 X100k48 | 0 |
| F1kr | Job 18 E48t | 1 |
| F1kr | Job 18 E24t | 0 |
| F1kr | Job 19 E64kr | 0 |
| F1kr | Job 19 E48tr | 2 |
| F1kr | Job 19 E64t (incomplete) | 0 |
| F1kr | Job 19 E48w | 1 |
| F1kr | Job 20 F7k | 1 |
| F1kr | Job 20 F7t | 0 |
| F1kr | Job 20 E64tr (incomplete) | 0 |
| F1kr | Job 20 F7w | 0 |
| F1kr | Job 21 E64tr2 | 0 |
| F1kr | Job 21 F7kr | 1 |
| F1kr | Job 21 F3k | 1 |
| F1kr | Job 21 F1k | 0 |
| F1kr | Job 21 E64w | 0 |
| F3kr | Job 17 X400r | 0 |
| F3kr | Job 17 E24kr | 0 |
| F3kr | Job 17 X400m3 | 0 |
| F3kr | Job 17 X100m3 | 0 |
| F3kr | Job 17 E48k | 2 |
| F3kr | Job 17 X400w | 1 |
| F3kr | Job 18 E48kr | 0 |
| F3kr | Job 18 D48v24 | 0 |
| F3kr | Job 18 E64k | 2 |
| F3kr | Job 18 X400k48 | 0 |
| F3kr | Job 18 X100k48 | 0 |
| F3kr | Job 18 E48t | 1 |
| F3kr | Job 18 E24t | 0 |
| F3kr | Job 19 E64kr | 0 |
| F3kr | Job 19 E48tr | 1 |
| F3kr | Job 19 E64t (incomplete) | 0 |
| F3kr | Job 19 E48w | 3 |
| F3kr | Job 20 F7k | 1 |
| F3kr | Job 20 F7t | 0 |
| F3kr | Job 20 E64tr (incomplete) | 0 |
| F3kr | Job 20 F7w | 0 |
| F3kr | Job 21 E64tr2 | 0 |
| F3kr | Job 21 F7kr | 0 |
| F3kr | Job 21 F3k | 0 |
| F3kr | Job 21 F1k | 0 |
| F3kr | Job 21 E64w | 0 |
| F2k | Job 17 X400r | 0 |
| F2k | Job 17 E24kr | 0 |
| F2k | Job 17 X400m3 | 0 |
| F2k | Job 17 X100m3 | 1 |
| F2k | Job 17 E48k | 1 |
| F2k | Job 17 X400w | 1 |
| F2k | Job 18 E48kr | 0 |
| F2k | Job 18 D48v24 | 0 |
| F2k | Job 18 E64k | 0 |
| F2k | Job 18 X400k48 | 0 |
| F2k | Job 18 X100k48 | 2 |
| F2k | Job 18 E48t | 1 |
| F2k | Job 18 E24t | 3 |
| F2k | Job 19 E64kr | 1 |
| F2k | Job 19 E48tr | 0 |
| F2k | Job 19 E64t (incomplete) | 0 |
| F2k | Job 19 E48w | 0 |
| F2k | Job 20 F7k | 1 |
| F2k | Job 20 F7t | 0 |
| F2k | Job 20 E64tr (incomplete) | 2 |
| F2k | Job 20 F7w | 0 |
| F2k | Job 21 E64tr2 | 0 |
| F2k | Job 21 F7kr | 0 |
| F2k | Job 21 F3k | 0 |
| F2k | Job 21 F1k | 0 |
| F2k | Job 21 E64w | 0 |
| F4k | Job 17 X400r | 0 |
| F4k | Job 17 E24kr | 0 |
| F4k | Job 17 X400m3 | 0 |
| F4k | Job 17 X100m3 | 0 |
| F4k | Job 17 E48k | 0 |
| F4k | Job 17 X400w | 1 |
| F4k | Job 18 E48kr | 2 |
| F4k | Job 18 D48v24 | 0 |
| F4k | Job 18 E64k | 0 |
| F4k | Job 18 X400k48 | 0 |
| F4k | Job 18 X100k48 | 0 |
| F4k | Job 18 E48t | 0 |
| F4k | Job 18 E24t | 0 |
| F4k | Job 19 E64kr | 0 |
| F4k | Job 19 E48tr | 0 |
| F4k | Job 19 E64t (incomplete) | 0 |
| F4k | Job 19 E48w | 0 |
| F4k | Job 20 F7k | 0 |
| F4k | Job 20 F7t | 0 |
| F4k | Job 20 E64tr (incomplete) | 0 |
| F4k | Job 20 F7w | 0 |
| F4k | Job 21 E64tr2 | 0 |
| F4k | Job 21 F7kr | 0 |
| F4k | Job 21 F3k | 1 |
| F4k | Job 21 F1k | 0 |
| F4k | Job 21 E64w | 0 |
| F5k | Job 17 X400r | 1 |
| F5k | Job 17 E24kr | 0 |
| F5k | Job 17 X400m3 | 1 |
| F5k | Job 17 X100m3 | 0 |
| F5k | Job 17 E48k | 0 |
| F5k | Job 17 X400w | 1 |
| F5k | Job 18 E48kr | 0 |
| F5k | Job 18 D48v24 | 1 |
| F5k | Job 18 E64k | 2 |
| F5k | Job 18 X400k48 | 1 |
| F5k | Job 18 X100k48 | 1 |
| F5k | Job 18 E48t | 1 |
| F5k | Job 18 E24t | 1 |
| F5k | Job 19 E64kr | 0 |
| F5k | Job 19 E48tr | 1 |
| F5k | Job 19 E64t (incomplete) | 1 |
| F5k | Job 19 E48w | 1 |
| F5k | Job 20 F7k | 0 |
| F5k | Job 20 F7t | 0 |
| F5k | Job 20 E64tr (incomplete) | 0 |
| F5k | Job 20 F7w | 1 |
| F5k | Job 21 E64tr2 | 0 |
| F5k | Job 21 F7kr | 0 |
| F5k | Job 21 F3k | 0 |
| F5k | Job 21 F1k | 0 |
| F5k | Job 21 E64w | 0 |
| F6k | Job 17 X400r | 1 |
| F6k | Job 17 E24kr | 0 |
| F6k | Job 17 X400m3 | 1 |
| F6k | Job 17 X100m3 | 0 |
| F6k | Job 17 E48k | 0 |
| F6k | Job 17 X400w | 1 |
| F6k | Job 18 E48kr | 0 |
| F6k | Job 18 D48v24 | 0 |
| F6k | Job 18 E64k | 0 |
| F6k | Job 18 X400k48 | 0 |
| F6k | Job 18 X100k48 | 0 |
| F6k | Job 18 E48t | 0 |
| F6k | Job 18 E24t | 1 |
| F6k | Job 19 E64kr | 1 |
| F6k | Job 19 E48tr | 0 |
| F6k | Job 19 E64t (incomplete) | 0 |
| F6k | Job 19 E48w | 0 |
| F6k | Job 20 F7k | 0 |
| F6k | Job 20 F7t | 0 |
| F6k | Job 20 E64tr (incomplete) | 0 |
| F6k | Job 20 F7w | 0 |
| F6k | Job 21 E64tr2 | 1 |
| F6k | Job 21 F7kr | 0 |
| F6k | Job 21 F3k | 0 |
| F6k | Job 21 F1k | 0 |
| F6k | Job 21 E64w | 0 |
| E64wr | Job 17 X400r | 0 |
| E64wr | Job 17 E24kr | 1 |
| E64wr | Job 17 X400m3 | 0 |
| E64wr | Job 17 X100m3 | 0 |
| E64wr | Job 17 E48k | 1 |
| E64wr | Job 17 X400w | 0 |
| E64wr | Job 18 E48kr | 0 |
| E64wr | Job 18 D48v24 | 0 |
| E64wr | Job 18 E64k | 0 |
| E64wr | Job 18 X400k48 | 0 |
| E64wr | Job 18 X100k48 | 0 |
| E64wr | Job 18 E48t | 0 |
| E64wr | Job 18 E24t | 1 |
| E64wr | Job 19 E64kr | 0 |
| E64wr | Job 19 E48tr | 0 |
| E64wr | Job 19 E64t (incomplete) | 1 |
| E64wr | Job 19 E48w | 0 |
| E64wr | Job 20 F7k | 0 |
| E64wr | Job 20 F7t | 1 |
| E64wr | Job 20 E64tr (incomplete) | 0 |
| E64wr | Job 20 F7w | 0 |
| E64wr | Job 21 E64tr2 | 0 |
| E64wr | Job 21 F7kr | 0 |
| E64wr | Job 21 F3k | 0 |
| E64wr | Job 21 F1k | 1 |
| E64wr | Job 21 E64w | 1 |

## Declared verdicts

F1kr, only if complete, gives F1k its verdict: REPLICATED (a loss) when F1kr alone gives Elo below 0 AND the pool of F1k and F1kr (pentanomial counts added) has a 95 % interval whose upper end is below 0. The same for F3kr and F3k.
E64wr, only if complete, gives E64w its verdict: REPLICATED (a gain) when E64wr alone gives Elo above 0 AND the pool of E64w and E64wr has a 95 % interval whose lower end is above 0.
F2k, F4k, F5k and F6k are exploratory: no verdict, a row each; one whose 95 % interval lies wholly above or wholly below 0 earns a fresh seed in a later job before anything is said about it.
A cut match gives no verdict.

F1k REPLICATED yes. Fresh Elo -9.0400, pooled upper 95% bound -2.8559. Evidence complete: interval reconstructed from summed pentanomial counts.
F3k REPLICATED yes. Fresh Elo -8.1700, pooled upper 95% bound -3.9651. Evidence complete: interval reconstructed from summed pentanomial counts.
E64w REPLICATED yes. Fresh Elo +9.9000, pooled lower 95% bound +5.0784. Evidence complete: interval reconstructed from summed pentanomial counts.

## FailHighBlend settings at 2,000 nodes

PCA, PC20, embedded evaluation, Threads 1, Hash 16, EvalSwingMult 0 on both sides. Each nonzero mask was measured against FailHighBlend 0.

| Value | Enabled parts | Games | Elo [95%] | Replicated | Evidence |
|---:|---|---:|---|---|---|
| 1 | Reverse-futility return blend | 4000 | -11.30 [-19.74, -2.86] | yes (loss) | complete: interval reconstructed from summed pentanomial counts |
| 2 | Quiescence fail-high blends | 2000 | -11.47 [-23.17, +0.23] | one seed | complete |
| 3 | Reverse-futility return blend, Quiescence fail-high blends | 4000 | -12.51 [-21.06, -3.97] | yes (loss) | complete: interval reconstructed from summed pentanomial counts |
| 4 | Non-PV main-search fail-high blend | 2000 | -2.43 [-14.23, +9.37] | one seed | complete |
| 5 | Reverse-futility return blend, Non-PV main-search fail-high blend | 2000 | -20.70 [-32.91, -8.49] | one seed | complete |
| 6 | Quiescence fail-high blends, Non-PV main-search fail-high blend | 2000 | -8.51 [-20.28, +3.26] | one seed | complete |
| 7 | Reverse-futility return blend, Quiescence fail-high blends, Non-PV main-search fail-high blend | 4000 | -24.10 [-32.75, -15.45] | yes (loss) | complete: interval reconstructed from summed pentanomial counts |

## Facts

- All nine matches finished before the 15:36:40Z cutoff. E64wr finished last at 15:32:27Z. The PGNs contain 14,000 measured and 300 control games, all in complete color-reversed pairs. F5k and F6k both started with more time remaining than the slowest preceding same-slot match plus 30 seconds. This estimate used wrapper wall durations. [Independent audit](sol/job22/independent-Job22.txt) · [Optional launch decisions](sol/job22/slot-runs.txt)
- At 2,000 nodes on PCA, the FailHighBlend 1 and 3 losses versus zero both replicated. The 4,000-game pools were −11.30 Elo [−19.74, −2.86] and −12.51 [−21.06, −3.97]. Their fresh seeds gave −9.04 and −8.17 in 2,000 games each. The F1 and F3 seed pairs shared no exact FENs. [F1kr PGN](sol/job22/raw/F1kr.pgn) · [F3kr PGN](sol/job22/raw/F3kr.pgn)
- At 20,000 nodes on the Job 4 counting build, EvalSwingMult 64 versus zero replicated. The fresh seed scored +9.90 Elo [−0.21, +20.01] in 2,000 games, and the 4,000-game pool scored +12.17 [+5.08, +19.25]. The two seeds shared one exact opening FEN. The declared pool retains both instances. [E64wr PGN](sol/job22/raw/E64wr.pgn) · [E64w PGN](sol/job21/raw/E64w.pgn)
- At 2,000 nodes on PCA, FailHighBlend 5 versus zero scored −20.70 Elo [−32.91, −8.49] in 2,000 games and was the only exploratory result whose interval excluded zero. Values 2, 4 and 6 each had intervals spanning zero. The option selects the reverse-futility return blend (bit 1), the quiescence fail-high blends (bit 2), and the non-PV main-search fail-high blend (bit 4). [F5k PGN](sol/job22/raw/F5k.pgn) · [Pinned patch, line 9](https://github.com/couns0538-sketch/dwqww/blob/5db05e095d5e81622eb0de13eb8a738a0ae1d22a/forge-combo29/tests_kimi5_job25/A2A5.pc.patch.txt#L9)
- Every measured match and replication pool had zero identical ordered move lists in reversed-color pairs. Four of seven forecast magnitudes survived. The full opening table matched the independent counts in all 270 cells, with 63 nonzero intersections and a largest intersection of three exact FENs. The published Job 21 report already contained all 14 comparisons involving its seven files and the two historical cutoff files. The independent recheck confirms the four nonzero entries mentioned by Opus and records their exact FENs and round numbers. [Job 22 opening audit](sol/job22/openings-audit.txt) · [Job 21 opening-table verification](sol/job22/job21-opening-addendum.txt)

## Suspicions

The reverse-futility switch alone lost Elo on both 2,000-node seeds. Its combination with the main-search switch also lost Elo in one seed. The one-seed estimates for the quiescence and main-search switches alone leave their signs uncertain. Direct matches between masks would be needed to estimate interaction effects.

## What I did not do

I reused the two pinned executables. Source and weights in the repository, the owner's PC and its running tune, and the training loop were outside this job.

## What I am not sure about

The estimates apply to these builds, the embedded net, PC20 and these opening samples. The Elo comparisons use separately sampled zero baselines. A comparison between switch combinations would need its own paired match.

## Reproduction

Both executables trace to Forge PC r15 at base `6b98f2170a3210e71beed04bbd2553972c253ed7` plus the PC patch. PCA adds Kimi5's A2A5 patch to the plain PC tree. The Job 4 executable adds the Job 2 counters and Job 4 buttons to PC r15. Both used GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4, `FORGE_MATE_ALPHA_GUARD=1` and embedded AL1 s198 (weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`). [Job 20 PCA build](REPORT_sol_job20.md) · [Job 4 counting build](REPORT_sol_job4.md)

Fastchess gave both engines PC20, Threads 1, Hash 16 MiB, one PV, OwnBook false and the exact options in each sidecar. The PCA cells used Mult 0 and explicitly set FHB on both sides. E64wr used the Job 4 build with Mult 64 versus 0. Every match used default Max 200 and a 300-move ceiling. [Match settings and outputs](sol/job22/raw)

From `forge-combo29/sol/job21`, with Python 3 and python-chess 1.11.2, these commands regenerate the controls, results, verdicts and opening comparisons.

```sh
python3 analyze_matches22.py gates raw --pca-sha256 pca.sha256
python3 analyze_matches22.py table raw --pca-sha256 pca.sha256 \
  --job17-raw ../job17/raw --job18-raw ../job18/raw --job19-raw ../job19/raw \
  --job20-raw ../job20/raw --job21-raw ../job21/raw --prediction prediction.txt
```

[Full readback](sol/job22/readback.txt) · [UTC stamps](sol/job22/stamps.txt) · [Precommit tree readback](sol/job22/precommit-readback.txt)

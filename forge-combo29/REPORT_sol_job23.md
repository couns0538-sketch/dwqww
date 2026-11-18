# Sol — Job 23 extended EvalSwingMult and clamp

## Step 0

1. **All three executables matched the eight pins in fresh processes.** Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. The Job 4 counting SHA-256 was `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. PCA was `49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a`. Fastchess printed `fastchess alpha 1.8.3 20261107-d7b47e8`. The opening EPD SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. [Job 4 UCI](sol/job23/step0-count.raw.txt) · [PCA UCI](sol/job23/step0-pca.raw.txt) · [W UCI](sol/job23/step0-w.raw.txt) · [Build receipt](sol/job23/build.txt)

## Step 0b

2. **W changed one option-table row in a separate copy of Job 4.** The compiled SHA-256 was `9520dbfab8064b8a9e7762377ddfc36a18269ec78c3e5612ac06a4b731aab990`. The executable printed `id name Chess Engine Forge 6.4.24 candidate` and `option name EvalSwingMult type spin default 0 min 0 max 128`. I generated the patch with `diff -ruN w-clean w-edit`, then applied it to another fresh copy using `patch -p1 -F0`. Here is the full diff output. [Patch file](sol/job23/evalswing_range.patch.txt)

   ```diff
   diff -ruN w-clean/forge-combo29/src/search.cpp w-edit/forge-combo29/src/search.cpp
   --- w-clean/forge-combo29/src/search.cpp	2026-11-17 18:26:39.056325398 -0800
   +++ w-edit/forge-combo29/src/search.cpp	2026-11-18 07:42:38.080251269 -0800
   @@ -360,7 +360,7 @@
            {"CaptureFutilityBase", &CaptureFutilityBase, 0, 1000},  {"CaptureFutilityMultiplier", &CaptureFutilityMultiplier, 0, 1000},
            {"CaptureFutilityDepth", &CaptureFutilityDepth, 0, 15},  {"FailLowContinuationBonus", &FailLowContinuationBonus, 0, 300},
            {"AspFailHighReduce", &AspFailHighReduce, 0, 1},         {"AspFailHighMaxReduce", &AspFailHighMaxReduce, 1, 6},
   -        {"EvalSwingMult", &EvalSwingMult, 0, 64},                {"EvalSwingMax", &EvalSwingMax, 50, 400},
   +        {"EvalSwingMult", &EvalSwingMult, 0, 128},                {"EvalSwingMax", &EvalSwingMax, 50, 400},
            {"TtCutoffHistory", &TtCutoffHistory, 0, 1},
    #if FORGE_PAWN_HISTORY
            {"PawnHistory", &PawnHistory, 0, 1},                     {"PawnHistoryBits", &PawnHistoryBits, 9, 13},
   ```

   The patch output reported the file below. The reconstituted scratch tree matched the edited tree byte for byte with no rejects or fuzz. [Patch output](sol/job23/patch-apply.txt) · [Separate-copy check](sol/job23/patch-tree-check.txt)

   ```text
   patching file forge-combo29/src/search.cpp
   ```

   On the first 200 official book positions, both engines at PC20, Threads 1, Hash 16, Mult 64 and default Max 200 totaled 7,610,402 nodes at depth 12. The first three counts were 16,744, 20,853 and 38,882. Both engines matched every node count and best move in order. The replay retained the six-field FEN and issued `ucinewgame` and `isready` before each search. [Depth rows and metadata](sol/job23/depth12) · [Independent provenance and replay](sol/job23/independent-step0b.txt)

   The same preflight sent `setoption name EvalSwingMult value 96` to both. W reached `readyok`. Job 4 emitted `info string invalid value for option EvalSwingMult`, and the preflight stopped it before a match could spawn. [Both preflight outputs](sol/job23/preflight-96.txt)

## Match controls

3. **K12 passed 50/50.** W with PC20, explicit Mult 128 and Max 200 on both sides, at 2,000 nodes, gave A 27–27–46 with pentanomial `[0, 0, 50, 0, 0]` in 100 games. Each reversed-color pair had identical ordered moves and a 1–1 score. Both preflights accepted the explicit options. [K12 PGN](sol/job23/raw/K12.pgn) · [K12 preflights](sol/job23/raw/K12.meta)
4. **C12 passed.** W with PC20, Mult 0 and Max 200 on both sides at 10,000 versus 20,000 nodes gave A 19–108–73 and pentanomial `[27, 41, 26, 6, 0]` in 200 games. Elo was −166.23 with a 95% interval of [−203.42, −129.04]. [C12 PGN](sol/job23/raw/C12.pgn) · [Independent controls](sol/job23/independent-gates.txt)

The [prediction](sol/job23/prediction.txt) was the sole file in commit `4c2f2dee6530bc2e0ef3dc6505e4dedc59475d2b` after both controls and before measured play. Slot 1 assigned F5kr, M128k and X400k at 2,000 nodes, followed by M96k if time allowed. Slot 2 assigned M128w at 20,000 nodes. Each slot used two workers. [UTC stamps](sol/job23/stamps.txt)

## Prediction grades

Sign and inclusive forecast range are checked separately. The combined forecast survives only when both checks pass. A zero sign forecast requires observed zero.

| Match | Forecast | Predicted range | Observed | Sign | Range | Overall | Evidence status |
|---|---:|---|---:|---|---|---|---|
| F5kr | -16.00 | [-30.00, -2.00] | -15.82 | met | met | survives | complete |
| M128k | -9.00 | [-25.00, +7.00] | -0.87 | met | met | survives | complete |
| X400k | +2.00 | [-12.00, +16.00] | +8.86 | met | met | survives | complete |
| M96k | -4.00 | [-20.00, +12.00] | +5.73 | missed | met | KILLED | complete |
| M128w | +3.00 | [-11.00, +17.00] | +6.73 | met | met | survives | complete |

4/5 signs and 5/5 ranges met. 4 survive, 1 KILLED, 0 ungraded.

## Table P. Job 23 paired games

All rows use PC20, embedded evaluation, Threads 1, Hash 16 and the pinned opening book. W-L-D is from A's perspective. Identical pairs share the complete ordered UCI move sequence.

| Match | Build, nodes per move, options A/B | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Reading |
|---|---|---|---:|---|---|---|---:|---|
| F5kr | PCA, 2,000, FailHighBlend 5/0 and EvalSwingMult 0/0 | complete | 2000 | 645-736-619 | 128, 222, 365, 183, 102 | -15.82 [-28.21, -3.43] | 0/1000 | two-seed loss comparison |
| M128k | W, 2,000, EvalSwingMult 128/64 and EvalSwingMax 200/200 | complete | 2000 | 672-677-651 | 87, 219, 393, 214, 87 | -0.87 [-12.31, +10.57] | 0/1000 | exploratory, interval includes zero |
| X400k | W, 2,000, EvalSwingMult 64/64 and EvalSwingMax 400/200 | complete | 2000 | 700-649-651 | 52, 158, 536, 195, 59 | +8.86 [-0.75, +18.47] | 31/1000 | exploratory, interval includes zero |
| M96k | W, 2,000, EvalSwingMult 96/64 and EvalSwingMax 200/200 | complete | 2000 | 677-644-679 | 94, 210, 365, 231, 100 | +5.73 [-6.15, +17.61] | 0/1000 | exploratory, interval includes zero |
| M128w | W, 20,000, EvalSwingMult 128/64 and EvalSwingMax 200/200 | complete | 1600 | 450-419-731 | 37, 188, 320, 217, 38 | +6.73 [-4.57, +18.03] | 0/800 | exploratory, interval includes zero |
| F5k | PCA, 2,000, FailHighBlend 5/0 and EvalSwingMult 0/0 | complete | 2000 | 639-758-603 | 119, 245, 375, 158, 103 | -20.70 [-32.91, -8.49] | 0/1000 | two-seed loss comparison |
| F5k + F5kr pooled | PCA, 2,000, FailHighBlend 5/0 and EvalSwingMult 0/0 | complete: interval reconstructed from summed pentanomial counts | 4000 | 1284-1494-1222 | 247, 467, 740, 341, 205 | -18.26 [-26.95, -9.56] | 0/2000 | two-seed loss comparison |

## Shared openings

Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct FEN strings. The two tables cover every new-file pair and every new file against every prior measurement.

Job 22 F5k and F5kr distinct shared exact FENs = 0.

| File | Status | Complete pairs | Distinct exact FENs |
|---|---|---:|---:|
| K12 | complete | 50 | 50 |
| C12 | complete | 100 | 100 |
| F5kr | complete | 1000 | 1000 |
| M128k | complete | 1000 | 1000 |
| X400k | complete | 1000 | 1000 |
| M96k | complete | 1000 | 1000 |
| M128w | complete | 800 | 800 |
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

### Within Job 23

| File A | File B | Shared exact FENs |
|---|---|---:|
| K12 | C12 | 0 |
| K12 | F5kr | 0 |
| K12 | M128k | 0 |
| K12 | X400k | 0 |
| K12 | M96k | 0 |
| K12 | M128w | 0 |
| C12 | F5kr | 0 |
| C12 | M128k | 0 |
| C12 | X400k | 0 |
| C12 | M96k | 0 |
| C12 | M128w | 0 |
| F5kr | M128k | 1 |
| F5kr | X400k | 0 |
| F5kr | M96k | 1 |
| F5kr | M128w | 1 |
| M128k | X400k | 0 |
| M128k | M96k | 1 |
| M128k | M128w | 0 |
| X400k | M96k | 0 |
| X400k | M128w | 0 |
| M96k | M128w | 0 |

### Job 23 against Jobs 17–22

| File A | File B | Shared exact FENs |
|---|---|---:|
| K12 | Job 17 X400r | 0 |
| K12 | Job 17 E24kr | 0 |
| K12 | Job 17 X400m3 | 0 |
| K12 | Job 17 X100m3 | 0 |
| K12 | Job 17 E48k | 0 |
| K12 | Job 17 X400w | 0 |
| K12 | Job 18 E48kr | 0 |
| K12 | Job 18 D48v24 | 0 |
| K12 | Job 18 E64k | 0 |
| K12 | Job 18 X400k48 | 0 |
| K12 | Job 18 X100k48 | 0 |
| K12 | Job 18 E48t | 0 |
| K12 | Job 18 E24t | 0 |
| K12 | Job 19 E64kr | 0 |
| K12 | Job 19 E48tr | 0 |
| K12 | Job 19 E64t (incomplete) | 0 |
| K12 | Job 19 E48w | 0 |
| K12 | Job 20 F7k | 0 |
| K12 | Job 20 F7t | 0 |
| K12 | Job 20 E64tr (incomplete) | 0 |
| K12 | Job 20 F7w | 0 |
| K12 | Job 21 E64tr2 | 0 |
| K12 | Job 21 F7kr | 0 |
| K12 | Job 21 F3k | 0 |
| K12 | Job 21 F1k | 0 |
| K12 | Job 21 E64w | 0 |
| K12 | Job 22 F1kr | 0 |
| K12 | Job 22 F3kr | 0 |
| K12 | Job 22 F2k | 0 |
| K12 | Job 22 F4k | 0 |
| K12 | Job 22 F5k | 0 |
| K12 | Job 22 F6k | 0 |
| K12 | Job 22 E64wr | 0 |
| C12 | Job 17 X400r | 0 |
| C12 | Job 17 E24kr | 0 |
| C12 | Job 17 X400m3 | 0 |
| C12 | Job 17 X100m3 | 0 |
| C12 | Job 17 E48k | 0 |
| C12 | Job 17 X400w | 0 |
| C12 | Job 18 E48kr | 0 |
| C12 | Job 18 D48v24 | 0 |
| C12 | Job 18 E64k | 0 |
| C12 | Job 18 X400k48 | 0 |
| C12 | Job 18 X100k48 | 0 |
| C12 | Job 18 E48t | 0 |
| C12 | Job 18 E24t | 0 |
| C12 | Job 19 E64kr | 0 |
| C12 | Job 19 E48tr | 0 |
| C12 | Job 19 E64t (incomplete) | 0 |
| C12 | Job 19 E48w | 0 |
| C12 | Job 20 F7k | 0 |
| C12 | Job 20 F7t | 0 |
| C12 | Job 20 E64tr (incomplete) | 0 |
| C12 | Job 20 F7w | 1 |
| C12 | Job 21 E64tr2 | 0 |
| C12 | Job 21 F7kr | 0 |
| C12 | Job 21 F3k | 0 |
| C12 | Job 21 F1k | 0 |
| C12 | Job 21 E64w | 0 |
| C12 | Job 22 F1kr | 0 |
| C12 | Job 22 F3kr | 0 |
| C12 | Job 22 F2k | 0 |
| C12 | Job 22 F4k | 0 |
| C12 | Job 22 F5k | 0 |
| C12 | Job 22 F6k | 0 |
| C12 | Job 22 E64wr | 0 |
| F5kr | Job 17 X400r | 1 |
| F5kr | Job 17 E24kr | 0 |
| F5kr | Job 17 X400m3 | 0 |
| F5kr | Job 17 X100m3 | 0 |
| F5kr | Job 17 E48k | 0 |
| F5kr | Job 17 X400w | 0 |
| F5kr | Job 18 E48kr | 1 |
| F5kr | Job 18 D48v24 | 0 |
| F5kr | Job 18 E64k | 1 |
| F5kr | Job 18 X400k48 | 0 |
| F5kr | Job 18 X100k48 | 0 |
| F5kr | Job 18 E48t | 1 |
| F5kr | Job 18 E24t | 1 |
| F5kr | Job 19 E64kr | 0 |
| F5kr | Job 19 E48tr | 0 |
| F5kr | Job 19 E64t (incomplete) | 0 |
| F5kr | Job 19 E48w | 1 |
| F5kr | Job 20 F7k | 0 |
| F5kr | Job 20 F7t | 0 |
| F5kr | Job 20 E64tr (incomplete) | 1 |
| F5kr | Job 20 F7w | 1 |
| F5kr | Job 21 E64tr2 | 0 |
| F5kr | Job 21 F7kr | 0 |
| F5kr | Job 21 F3k | 0 |
| F5kr | Job 21 F1k | 1 |
| F5kr | Job 21 E64w | 2 |
| F5kr | Job 22 F1kr | 1 |
| F5kr | Job 22 F3kr | 0 |
| F5kr | Job 22 F2k | 0 |
| F5kr | Job 22 F4k | 0 |
| F5kr | Job 22 F5k | 0 |
| F5kr | Job 22 F6k | 0 |
| F5kr | Job 22 E64wr | 0 |
| M128k | Job 17 X400r | 1 |
| M128k | Job 17 E24kr | 2 |
| M128k | Job 17 X400m3 | 0 |
| M128k | Job 17 X100m3 | 0 |
| M128k | Job 17 E48k | 0 |
| M128k | Job 17 X400w | 0 |
| M128k | Job 18 E48kr | 0 |
| M128k | Job 18 D48v24 | 0 |
| M128k | Job 18 E64k | 1 |
| M128k | Job 18 X400k48 | 0 |
| M128k | Job 18 X100k48 | 1 |
| M128k | Job 18 E48t | 0 |
| M128k | Job 18 E24t | 0 |
| M128k | Job 19 E64kr | 0 |
| M128k | Job 19 E48tr | 1 |
| M128k | Job 19 E64t (incomplete) | 0 |
| M128k | Job 19 E48w | 0 |
| M128k | Job 20 F7k | 0 |
| M128k | Job 20 F7t | 0 |
| M128k | Job 20 E64tr (incomplete) | 0 |
| M128k | Job 20 F7w | 0 |
| M128k | Job 21 E64tr2 | 0 |
| M128k | Job 21 F7kr | 0 |
| M128k | Job 21 F3k | 1 |
| M128k | Job 21 F1k | 2 |
| M128k | Job 21 E64w | 0 |
| M128k | Job 22 F1kr | 0 |
| M128k | Job 22 F3kr | 1 |
| M128k | Job 22 F2k | 0 |
| M128k | Job 22 F4k | 0 |
| M128k | Job 22 F5k | 0 |
| M128k | Job 22 F6k | 0 |
| M128k | Job 22 E64wr | 1 |
| X400k | Job 17 X400r | 0 |
| X400k | Job 17 E24kr | 2 |
| X400k | Job 17 X400m3 | 0 |
| X400k | Job 17 X100m3 | 2 |
| X400k | Job 17 E48k | 0 |
| X400k | Job 17 X400w | 0 |
| X400k | Job 18 E48kr | 0 |
| X400k | Job 18 D48v24 | 0 |
| X400k | Job 18 E64k | 0 |
| X400k | Job 18 X400k48 | 0 |
| X400k | Job 18 X100k48 | 0 |
| X400k | Job 18 E48t | 0 |
| X400k | Job 18 E24t | 0 |
| X400k | Job 19 E64kr | 2 |
| X400k | Job 19 E48tr | 0 |
| X400k | Job 19 E64t (incomplete) | 0 |
| X400k | Job 19 E48w | 0 |
| X400k | Job 20 F7k | 0 |
| X400k | Job 20 F7t | 1 |
| X400k | Job 20 E64tr (incomplete) | 0 |
| X400k | Job 20 F7w | 1 |
| X400k | Job 21 E64tr2 | 2 |
| X400k | Job 21 F7kr | 1 |
| X400k | Job 21 F3k | 0 |
| X400k | Job 21 F1k | 2 |
| X400k | Job 21 E64w | 0 |
| X400k | Job 22 F1kr | 0 |
| X400k | Job 22 F3kr | 0 |
| X400k | Job 22 F2k | 0 |
| X400k | Job 22 F4k | 1 |
| X400k | Job 22 F5k | 0 |
| X400k | Job 22 F6k | 0 |
| X400k | Job 22 E64wr | 1 |
| M96k | Job 17 X400r | 0 |
| M96k | Job 17 E24kr | 0 |
| M96k | Job 17 X400m3 | 0 |
| M96k | Job 17 X100m3 | 0 |
| M96k | Job 17 E48k | 0 |
| M96k | Job 17 X400w | 1 |
| M96k | Job 18 E48kr | 0 |
| M96k | Job 18 D48v24 | 0 |
| M96k | Job 18 E64k | 0 |
| M96k | Job 18 X400k48 | 0 |
| M96k | Job 18 X100k48 | 2 |
| M96k | Job 18 E48t | 0 |
| M96k | Job 18 E24t | 0 |
| M96k | Job 19 E64kr | 0 |
| M96k | Job 19 E48tr | 0 |
| M96k | Job 19 E64t (incomplete) | 1 |
| M96k | Job 19 E48w | 0 |
| M96k | Job 20 F7k | 0 |
| M96k | Job 20 F7t | 0 |
| M96k | Job 20 E64tr (incomplete) | 0 |
| M96k | Job 20 F7w | 0 |
| M96k | Job 21 E64tr2 | 0 |
| M96k | Job 21 F7kr | 0 |
| M96k | Job 21 F3k | 0 |
| M96k | Job 21 F1k | 0 |
| M96k | Job 21 E64w | 1 |
| M96k | Job 22 F1kr | 1 |
| M96k | Job 22 F3kr | 0 |
| M96k | Job 22 F2k | 0 |
| M96k | Job 22 F4k | 0 |
| M96k | Job 22 F5k | 0 |
| M96k | Job 22 F6k | 1 |
| M96k | Job 22 E64wr | 1 |
| M128w | Job 17 X400r | 0 |
| M128w | Job 17 E24kr | 0 |
| M128w | Job 17 X400m3 | 0 |
| M128w | Job 17 X100m3 | 0 |
| M128w | Job 17 E48k | 0 |
| M128w | Job 17 X400w | 0 |
| M128w | Job 18 E48kr | 0 |
| M128w | Job 18 D48v24 | 0 |
| M128w | Job 18 E64k | 0 |
| M128w | Job 18 X400k48 | 1 |
| M128w | Job 18 X100k48 | 0 |
| M128w | Job 18 E48t | 1 |
| M128w | Job 18 E24t | 2 |
| M128w | Job 19 E64kr | 0 |
| M128w | Job 19 E48tr | 1 |
| M128w | Job 19 E64t (incomplete) | 0 |
| M128w | Job 19 E48w | 0 |
| M128w | Job 20 F7k | 3 |
| M128w | Job 20 F7t | 1 |
| M128w | Job 20 E64tr (incomplete) | 0 |
| M128w | Job 20 F7w | 0 |
| M128w | Job 21 E64tr2 | 0 |
| M128w | Job 21 F7kr | 1 |
| M128w | Job 21 F3k | 1 |
| M128w | Job 21 F1k | 0 |
| M128w | Job 21 E64w | 0 |
| M128w | Job 22 F1kr | 0 |
| M128w | Job 22 F3kr | 0 |
| M128w | Job 22 F2k | 1 |
| M128w | Job 22 F4k | 0 |
| M128w | Job 22 F5k | 0 |
| M128w | Job 22 F6k | 0 |
| M128w | Job 22 E64wr | 0 |
E64t: minute-50 cut verified at 2026-11-18T12:37:26+00:00, 1888 paired games eligible.
E64tr: minute-50 cut verified at 2026-11-18T13:37:47+00:00, 1604 paired games eligible.

## Table Q. EvalSwing comparisons in Jobs 17–23

Both sides use PC20, built-in evaluation, Threads 1 and Hash 16. Each Mult and Max column reads A/B. Max 200 is the effective default when omitted. Each physical measurement appears once. Pools add raw pentanomial counts and list all contributing seed IDs, including the two Job 16 ingredients of Job 17 pools.

| Job | Comparison | Build | Node budget | Mult A/B | Max A/B | Games | Elo [95%] | Seeds | Replicated | Status |
|---:|---|---|---:|---|---|---:|---|---|---|---|
| 17 | X400r | Job 4 (63356d12) | 2,000 | 6/6 | 400/200 | 2000 | +1.56 [-7.58, +10.70] | 1 (7173) | no, in Job 17 pool | complete |
| 17 | E24kr | Job 4 (63356d12) | 2,000 | 24/0 | 200/200 | 2000 | +28.90 [+16.88, +40.92] | 1 (7174) | yes (gain), in Job 17 pool | complete |
| 17 | X400m3 | Job 4 (63356d12) | 2,000 | 3/3 | 400/200 | 2000 | +7.30 [-1.59, +16.19] | 1 (7175) | one seed | complete |
| 17 | X100m3 | Job 4 (63356d12) | 2,000 | 3/3 | 100/200 | 2000 | -2.78 [-14.80, +9.24] | 1 (7176) | one seed | complete |
| 17 | E48k | Job 4 (63356d12) | 2,000 | 48/0 | 200/200 | 2000 | +40.48 [+28.53, +52.43] | 1 (7177) | yes (gain), in Job 18 pool | complete |
| 17 | X400w | Job 4 (63356d12) | 20,000 | 6/6 | 400/200 | 1600 | -1.95 [-13.17, +9.27] | 1 (7178) | one seed | complete |
| 18 | E48kr | Job 4 (63356d12) | 2,000 | 48/0 | 200/200 | 2000 | +29.25 [+16.76, +41.74] | 1 (7183) | yes (gain), in Job 18 pool | complete |
| 18 | D48v24 | Job 4 (63356d12) | 2,000 | 48/24 | 200/200 | 2000 | +4.00 [-8.17, +16.17] | 1 (7184) | one seed | complete |
| 18 | E64k | Job 4 (63356d12) | 2,000 | 64/0 | 200/200 | 2000 | +33.63 [+21.80, +45.46] | 1 (7185) | yes (gain), in Job 19 pool | complete |
| 18 | X400k48 | Job 4 (63356d12) | 2,000 | 48/48 | 400/200 | 2000 | -2.08 [-11.89, +7.73] | 1 (7186) | one seed | complete |
| 18 | X100k48 | Job 4 (63356d12) | 2,000 | 48/48 | 100/200 | 2000 | +2.95 [-8.75, +14.65] | 1 (7187) | one seed | complete |
| 18 | E48t | Job 4 (63356d12) | 10,000 | 48/0 | 200/200 | 2000 | +15.12 [+4.88, +25.36] | 1 (7188) | yes (gain), in Job 19 pool | complete |
| 18 | E24t | Job 4 (63356d12) | 10,000 | 24/0 | 200/200 | 2000 | +9.56 [-1.04, +20.16] | 1 (7189) | one seed | complete |
| 19 | E64kr | Job 4 (63356d12) | 2,000 | 64/0 | 200/200 | 2000 | +33.11 [+20.69, +45.53] | 1 (7193) | yes (gain), in Job 19 pool | complete |
| 19 | E48tr | Job 4 (63356d12) | 10,000 | 48/0 | 200/200 | 2000 | +3.13 [-7.88, +14.14] | 1 (7194) | yes (gain), in Job 19 pool | complete |
| 19 | E64t | Job 4 (63356d12) | 10,000 | 64/0 | 200/200 | 1888 | +12.89 [+2.09, +23.69] | 1 (7195) | yes (gain), in Job 21 pool | incomplete (interrupted) |
| 19 | E48w | Job 4 (63356d12) | 20,000 | 48/0 | 200/200 | 2000 | +5.04 [-5.20, +15.28] | 1 (7196) | one seed | complete |
| 20 | E64tr | Job 4 (63356d12) | 10,000 | 64/0 | 200/200 | 1604 | +17.99 [+6.42, +29.56] | 1 (7205) | yes (gain), in Job 21 pool | incomplete (interrupted) |
| 21 | E64tr2 | Job 4 (63356d12) | 10,000 | 64/0 | 200/200 | 2000 | +13.03 [+2.51, +23.55] | 1 (7213) | yes (gain), in Job 21 pool | complete |
| 21 | E64w | Job 4 (63356d12) | 20,000 | 64/0 | 200/200 | 2000 | +14.43 [+4.49, +24.37] | 1 (7217) | yes (gain), in Job 22 pool | complete |
| 22 | E64wr | Job 4 (63356d12) | 20,000 | 64/0 | 200/200 | 2000 | +9.90 [-0.21, +20.01] | 1 (7229) | yes (gain), in Job 22 pool | complete |
| 23 | M128k | W (9520dbfa) | 2,000 | 128/64 | 200/200 | 2000 | -0.87 [-12.31, +10.57] | 1 (7234) | one seed | complete |
| 23 | X400k | W (9520dbfa) | 2,000 | 64/64 | 400/200 | 2000 | +8.86 [-0.75, +18.47] | 1 (7235) | one seed | complete |
| 23 | M96k | W (9520dbfa) | 2,000 | 96/64 | 200/200 | 2000 | +5.73 [-6.15, +17.61] | 1 (7236) | one seed | complete |
| 23 | M128w | W (9520dbfa) | 20,000 | 128/64 | 200/200 | 1600 | +6.73 [-4.57, +18.03] | 1 (7237) | one seed | complete |
| 17 | X400 + X400r pooled | Job 4 (63356d12) | 2,000 | 6/6 | 400/200 | 4000 | -4.34 [-10.70, +2.02] | 2 (7163, 7173) | no | complete: interval reconstructed from summed pentanomial counts |
| 17 | E24k + E24kr pooled | Job 4 (63356d12) | 2,000 | 24/0 | 200/200 | 4000 | +24.53 [+16.06, +33.01] | 2 (7167, 7174) | yes (gain) | complete: interval reconstructed from summed pentanomial counts |
| 18 | E48k + E48kr pooled | Job 4 (63356d12) | 2,000 | 48/0 | 200/200 | 4000 | +34.86 [+26.22, +43.50] | 2 (7177, 7183) | yes (gain) | complete: interval reconstructed from summed pentanomial counts |
| 19 | E64k + E64kr pooled | Job 4 (63356d12) | 2,000 | 64/0 | 200/200 | 4000 | +33.37 [+24.79, +41.94] | 2 (7185, 7193) | yes (gain) | complete: interval reconstructed from summed pentanomial counts |
| 19 | E48t + E48tr pooled | Job 4 (63356d12) | 10,000 | 48/0 | 200/200 | 4000 | +9.12 [+1.60, +16.65] | 2 (7188, 7194) | yes (gain) | complete: interval reconstructed from summed pentanomial counts |
| 21 | E64t + E64tr + E64tr2 pooled | Job 4 (63356d12) | 10,000 | 64/0 | 200/200 | 5492 | +14.43 [+8.12, +20.75] | 3 (7195, 7205, 7213) | yes (gain) | incomplete (partial): interval reconstructed from summed pentanomial counts. E64t incomplete, 1888 paired games included. E64tr incomplete, 1604 paired games included |
| 22 | E64w + E64wr pooled | Job 4 (63356d12) | 20,000 | 64/0 | 200/200 | 4000 | +12.17 [+5.08, +19.25] | 2 (7217, 7229) | yes (gain) | complete: interval reconstructed from summed pentanomial counts |

## Declared verdict

F5kr, only if complete, gives F5k its verdict: REPLICATED (a loss) when F5kr alone gives Elo below 0 AND the pool of F5k and F5kr (pentanomial counts added) has a 95 % interval whose upper end is below 0.
M128k, X400k, M96k and M128w are exploratory, one seed each: no verdict, a row each; one whose 95 % interval lies wholly above or wholly below 0 earns a fresh seed in a later job before anything is said about it.
A cut match gives no verdict.

F5k REPLICATED yes. Fresh Elo -15.8200, pooled upper 95% bound -9.5609. Evidence complete: interval reconstructed from summed pentanomial counts.

## What this check cannot see

The PC's own net, exe and tune; doses above 128; EvalSwingMax values other than 200 and 400; time controls.

## Facts

- All seven matches finished before the 16:31:56Z cutoff. The 20,000-node match ended last at 16:20:32Z. The saved PGNs contain 9,600 measured games and 300 control games in complete reversed-color pairs. The optional 96-versus-64 cell started with 1,488.5 seconds left. The slowest preceding same-slot W run plus the chosen 30-second margin was 435.8 seconds. [Independent audit](sol/job23/independent-Job23.txt) · [Optional launch decision](sol/job23/slot-runs.txt)
- FailHighBlend 5 versus zero at 2,000 nodes on PCA met the loss replication rule. The fresh 2,000-game seed gave −15.82 Elo [−28.21, −3.43]. The 4,000-game pool gave −18.26 [−26.95, −9.56], with no shared opening FEN. [Fresh PGN](sol/job23/raw/F5kr.pgn) · [Original PGN](sol/job22/raw/F5k.pgn)
- On W at 2,000 nodes, Mult 128 versus 64 with Max 200 gave −0.87 Elo [−12.31, +10.57] and Mult 96 versus 64 gave +5.73 [−6.15, +17.61]. Max 400 versus 200 at Mult 64 gave +8.86 [−0.75, +18.47]. Each used 2,000 games. On W at 20,000 nodes, Mult 128 versus 64 with Max 200 gave +6.73 [−4.57, +18.03] in 1,600 games. All four intervals covered zero. [W raw matches](sol/job23/raw)
- Only the clip match on W had identical ordered moves in both games of a pair, with 31 out of 1,000. All 252 rendered opening comparisons matched the independent readback. There were 51 nonzero intersections, and the largest shared three exact FENs. Four of five forecast signs and all five forecast ranges met the stated criteria. [Opening audit](sol/job23/openings-audit.txt) · [Table and raw readback](sol/job23/readback.txt)

## Suspicions

At these settings the clamp and multiplier may affect different positions. W's scratch `forge-combo29/src/search.cpp:2049–2057` clips the evaluation swing first, then supplies `swing * EvalSwingMult / 16` to the history update. Mult 64 with Max 400 and Mult 128 with Max 200 each permit an input magnitude of 1,600, with different slopes below their clip thresholds. This job did not count how often each threshold was reached. The one-seed strength intervals leave those comparisons open.

## What I did not do

The W patch lived in a separate scratch tree. Source and weights in the repository, the owner's PC and its running tune, and the training loop were outside this job.

## What I am not sure about

The higher multipliers and changed clamp each use one opening seed. Separate samples at the two node budgets can place different demands on the search.

## Reproduction

The Job 4 counting build traces to Forge PC r15 at base `6b98f2170a3210e71beed04bbd2553972c253ed7` and adds the Job 2 counters and Job 4 buttons. W adds only the option-bound change to that source. PCA adds Kimi5's A2A5 patch to plain PC r15. All used GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4, `FORGE_MATE_ALPHA_GUARD=1` and embedded AL1 s198 (weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`). [Job 4 counting build](REPORT_sol_job4.md) · [Job 20 PCA build](REPORT_sol_job20.md) · [W build receipt](sol/job23/build.txt)

Fastchess used PC20, Threads 1, Hash 16 MiB, one PV and OwnBook false. It played each opening in both colors with the 300-move ceiling. Each W engine got explicit EvalSwingMult and EvalSwingMax. F5kr used PCA with EvalSwingMult 0 on both sides and FailHighBlend 5 versus 0. [All match sidecars and raw outputs](sol/job23/raw)

From `forge-combo29/sol/job23`, with Python 3 and python-chess 1.11.2, these commands regenerate both controls, Tables P and Q and the opening comparisons.

```sh
python3 analyze_matches23.py gates raw --pca-sha256 pca.sha256 --w-sha256 w.sha256
python3 analyze_matches23.py table raw --pca-sha256 pca.sha256 --w-sha256 w.sha256 \
  --job17-raw ../job17/raw --job18-raw ../job18/raw --job19-raw ../job19/raw \
  --job20-raw ../job20/raw --job21-raw ../job21/raw --job22-raw ../job22/raw \
  --prediction prediction.txt
```

[Full readback](sol/job23/readback.txt) · [UTC stamps](sol/job23/stamps.txt) · [Precommit tree readback](sol/job23/precommit-readback.txt)

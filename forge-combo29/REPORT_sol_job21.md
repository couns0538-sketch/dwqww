# Sol — Job 21 EvalSwingMult replication and FailHighBlend doses

## Step 0 and controls

1. **Both reused executables matched all eight fresh-process pins.** Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. The Job 4 counting SHA-256 was `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. PCA was `49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a`. Fastchess printed `fastchess alpha 1.8.3 20261107-d7b47e8`. The official opening EPD SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. Both engines printed the two EvalSwing lines below. PCA also printed the FailHighBlend line. [Counting UCI](sol/job21/step0-count.raw.txt) · [PCA UCI](sol/job21/step0-pca.raw.txt) · [Build receipt](sol/job21/build.txt) · [Independent build checks](sol/job21/independent-build.txt)

   ```text
   option name EvalSwingMult type spin default 0 min 0 max 64
   option name EvalSwingMax type spin default 200 min 50 max 400
   option name FailHighBlend type spin default 0 min 0 max 7
   ```

2. **K10 passed 50/50.** PCA with PC20 and explicit Mult 0 and FHB 3 on both sides at 2,000 nodes gave 100 games at 35–35–30, pentanomial `[0, 0, 50, 0, 0]`, and identical ordered moves and 1–1 in every reversed-color pair. Both preflights reached `readyok` without a refusal. [K10 PGN](sol/job21/raw/K10.pgn) · [K10 preflights](sol/job21/raw/K10.meta)
3. **C10 passed.** PCA with PC20 and explicit Mult 0 and FHB 0 on both sides at 10,000 versus 20,000 nodes gave A 18–110–72 and pentanomial `[23, 51, 21, 5, 0]` over 200 games. Elo was −172.78 with a 95% interval of [−207.34, −138.22]. [C10 PGN](sol/job21/raw/C10.pgn) · [Independent controls](sol/job21/independent-gates.txt)

The [prediction](sol/job21/prediction.txt) was the sole file in commit `398d475d267751a630e77abddab58a71c5ae3b44` after both controls and before measured play. The concurrent slots used two workers each. Slot 1 assigned E64tr2 at 10,000 nodes, then F7kr, F3k and F1k at 2,000 nodes. Slot 2 assigned E64w at 20,000 nodes. [UTC stamps](sol/job21/stamps.txt)

## Prediction grades

The observed Elo must have the forecast sign and fall within a factor of 1.5 of its magnitude. A zero forecast requires zero.

| Forecast | Guess | Observed | Grade | Evidence status |
|---|---:|---:|---|---|
| E64tr2 Elo | +14.00 | +13.03 | survives | complete |
| F7kr Elo | -18.00 | -23.14 | survives | complete |
| F3k Elo | -14.00 | -16.86 | survives | complete |
| F1k Elo | -8.00 | -13.56 | KILLED | complete |
| E64w Elo | +8.00 | +14.43 | KILLED | complete |

2 KILLED, 3 survive, 0 ungraded.

## Table P. FailHighBlend and EvalSwing paired games

All rows use PC20, embedded evaluation, Threads 1, Hash 16 and the pinned opening book. W-L-D is from A's perspective. Intervals use the fastchess 95% pentanomial Elo ± halfwidth convention. Identical pairs share the complete ordered UCI move sequence.

| Match | Build, nodes per move, options A/B | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Reading |
|---|---|---|---:|---|---|---|---:|---|
| E64tr2 | Job 4, 10,000, EvalSwingMult 64/0 | complete | 2000 | 608-533-859 | 46, 221, 427, 224, 82 | +13.03 [+2.51, +23.55] | 1/1000 | three-seed gain comparison |
| F7kr | PCA, 2,000, FailHighBlend 7/0 and EvalSwingMult 0/0 | complete | 2000 | 618-751-631 | 128, 243, 346, 200, 83 | -23.14 [-35.33, -10.95] | 0/1000 | two-seed loss comparison |
| F3k | PCA, 2,000, FailHighBlend 3/0 and EvalSwingMult 0/0 | complete | 2000 | 641-738-621 | 118, 235, 367, 186, 94 | -16.86 [-28.98, -4.74] | 0/1000 | exploratory, earns a fresh seed (below zero) |
| F1k | PCA, 2,000, FailHighBlend 1/0 and EvalSwingMult 0/0 | complete | 2000 | 637-715-648 | 114, 247, 329, 223, 87 | -13.56 [-25.71, -1.41] | 0/1000 | exploratory, earns a fresh seed (below zero) |
| E64w | Job 4, 20,000, EvalSwingMult 64/0 | complete | 2000 | 571-488-941 | 39, 216, 421, 271, 53 | +14.43 [+4.49, +24.37] | 0/1000 | exploratory, earns a fresh seed (above zero) |
| E64t | Job 4, 10,000, EvalSwingMult 64/0 | incomplete (interrupted) | 1888 | 576-506-806 | 43, 218, 376, 240, 67 | +12.89 [+2.09, +23.69] | 0/944 | three-seed gain comparison |
| E64tr | Job 4, 10,000, EvalSwingMult 64/0 | incomplete (interrupted) | 1604 | 495-412-697 | 35, 173, 322, 218, 54 | +17.99 [+6.42, +29.56] | 0/802 | three-seed gain comparison |
| F7k | PCA, 2,000, FailHighBlend 7/0 and EvalSwingMult 0/0 | complete | 2000 | 647-791-562 | 138, 223, 372, 179, 88 | -25.06 [-37.34, -12.78] | 0/1000 | two-seed loss comparison |
| E64t + E64tr + E64tr2 pooled | Job 4, 10,000, EvalSwingMult 64/0 | incomplete (partial): interval reconstructed from summed pentanomial counts. E64t incomplete, 1888 paired games included. E64tr incomplete, 1604 paired games included | 5492 | 1679-1451-2362 | 124, 612, 1125, 682, 203 | +14.43 [+8.12, +20.75] | 1/2746 | three-seed gain comparison |
| F7k + F7kr pooled | PCA, 2,000, FailHighBlend 7/0 and EvalSwingMult 0/0 | complete: interval reconstructed from summed pentanomial counts | 4000 | 1265-1542-1193 | 266, 466, 718, 379, 171 | -24.10 [-32.75, -15.45] | 0/2000 | two-seed loss comparison |

## Shared openings

Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct FEN strings.

Job 19 E64t (incomplete) and Job 20 E64tr (incomplete) distinct shared exact FENs = 0.
Job 19 E64t (incomplete) and E64tr2 distinct shared exact FENs = 0.
Job 20 E64tr (incomplete) and E64tr2 distinct shared exact FENs = 0.
Job 20 F7k and F7kr distinct shared exact FENs = 0.

| File | Status | Complete pairs | Distinct exact FENs |
|---|---|---:|---:|
| K10 | complete | 50 | 50 |
| C10 | complete | 100 | 100 |
| E64tr2 | complete | 1000 | 1000 |
| F7kr | complete | 1000 | 1000 |
| F3k | complete | 1000 | 1000 |
| F1k | complete | 1000 | 1000 |
| E64w | complete | 1000 | 1000 |
| Job 17 X400r | saved | 1000 | 1000 |
| Job 17 E24kr | saved | 1000 | 1000 |
| Job 17 X400m3 | saved | 1000 | 1000 |
| Job 17 X100m3 | saved | 1000 | 1000 |
| Job 17 E48k | saved | 1000 | 1000 |
| Job 17 X400w | saved | 800 | 800 |
| Job 18 E48kr | saved | 1000 | 1000 |
| Job 18 D48v24 | saved | 1000 | 1000 |
| Job 18 E64k | saved | 1000 | 1000 |
| Job 18 X400k48 | saved | 1000 | 1000 |
| Job 18 X100k48 | saved | 1000 | 1000 |
| Job 18 E48t | saved | 1000 | 1000 |
| Job 18 E24t | saved | 1000 | 1000 |
| Job 19 E64kr | saved | 1000 | 1000 |
| Job 19 E48tr | saved | 1000 | 1000 |
| Job 19 E64t | incomplete (interrupted) | 944 | 944 |
| Job 19 E48w | saved | 1000 | 1000 |
| Job 20 F7k | complete | 1000 | 1000 |
| Job 20 F7t | saved | 1000 | 1000 |
| Job 20 E64tr | incomplete (interrupted) | 802 | 802 |
| Job 20 F7w | saved | 1000 | 1000 |

### Within Job 21

| File A | File B | Shared exact FENs |
|---|---|---:|
| K10 | C10 | 0 |
| K10 | E64tr2 | 0 |
| K10 | F7kr | 0 |
| K10 | F3k | 0 |
| K10 | F1k | 0 |
| K10 | E64w | 0 |
| C10 | E64tr2 | 0 |
| C10 | F7kr | 0 |
| C10 | F3k | 0 |
| C10 | F1k | 0 |
| C10 | E64w | 0 |
| E64tr2 | F7kr | 0 |
| E64tr2 | F3k | 2 |
| E64tr2 | F1k | 0 |
| E64tr2 | E64w | 0 |
| F7kr | F3k | 0 |
| F7kr | F1k | 2 |
| F7kr | E64w | 1 |
| F3k | F1k | 0 |
| F3k | E64w | 1 |
| F1k | E64w | 0 |

### Job 21 against Jobs 17–20

| File A | File B | Shared exact FENs |
|---|---|---:|
| K10 | Job 17 X400r | 0 |
| K10 | Job 17 E24kr | 0 |
| K10 | Job 17 X400m3 | 0 |
| K10 | Job 17 X100m3 | 0 |
| K10 | Job 17 E48k | 0 |
| K10 | Job 17 X400w | 0 |
| K10 | Job 18 E48kr | 0 |
| K10 | Job 18 D48v24 | 0 |
| K10 | Job 18 E64k | 0 |
| K10 | Job 18 X400k48 | 0 |
| K10 | Job 18 X100k48 | 0 |
| K10 | Job 18 E48t | 0 |
| K10 | Job 18 E24t | 0 |
| K10 | Job 19 E64kr | 0 |
| K10 | Job 19 E48tr | 0 |
| K10 | Job 19 E64t (incomplete) | 1 |
| K10 | Job 19 E48w | 0 |
| K10 | Job 20 F7k | 0 |
| K10 | Job 20 F7t | 0 |
| K10 | Job 20 E64tr (incomplete) | 0 |
| K10 | Job 20 F7w | 0 |
| C10 | Job 17 X400r | 0 |
| C10 | Job 17 E24kr | 0 |
| C10 | Job 17 X400m3 | 0 |
| C10 | Job 17 X100m3 | 0 |
| C10 | Job 17 E48k | 0 |
| C10 | Job 17 X400w | 0 |
| C10 | Job 18 E48kr | 0 |
| C10 | Job 18 D48v24 | 0 |
| C10 | Job 18 E64k | 0 |
| C10 | Job 18 X400k48 | 0 |
| C10 | Job 18 X100k48 | 0 |
| C10 | Job 18 E48t | 0 |
| C10 | Job 18 E24t | 0 |
| C10 | Job 19 E64kr | 0 |
| C10 | Job 19 E48tr | 0 |
| C10 | Job 19 E64t (incomplete) | 0 |
| C10 | Job 19 E48w | 0 |
| C10 | Job 20 F7k | 0 |
| C10 | Job 20 F7t | 0 |
| C10 | Job 20 E64tr (incomplete) | 0 |
| C10 | Job 20 F7w | 0 |
| E64tr2 | Job 17 X400r | 0 |
| E64tr2 | Job 17 E24kr | 0 |
| E64tr2 | Job 17 X400m3 | 0 |
| E64tr2 | Job 17 X100m3 | 0 |
| E64tr2 | Job 17 E48k | 0 |
| E64tr2 | Job 17 X400w | 0 |
| E64tr2 | Job 18 E48kr | 0 |
| E64tr2 | Job 18 D48v24 | 1 |
| E64tr2 | Job 18 E64k | 0 |
| E64tr2 | Job 18 X400k48 | 0 |
| E64tr2 | Job 18 X100k48 | 1 |
| E64tr2 | Job 18 E48t | 0 |
| E64tr2 | Job 18 E24t | 2 |
| E64tr2 | Job 19 E64kr | 0 |
| E64tr2 | Job 19 E48tr | 0 |
| E64tr2 | Job 19 E64t (incomplete) | 0 |
| E64tr2 | Job 19 E48w | 0 |
| E64tr2 | Job 20 F7k | 0 |
| E64tr2 | Job 20 F7t | 0 |
| E64tr2 | Job 20 E64tr (incomplete) | 0 |
| E64tr2 | Job 20 F7w | 1 |
| F7kr | Job 17 X400r | 0 |
| F7kr | Job 17 E24kr | 1 |
| F7kr | Job 17 X400m3 | 2 |
| F7kr | Job 17 X100m3 | 0 |
| F7kr | Job 17 E48k | 1 |
| F7kr | Job 17 X400w | 1 |
| F7kr | Job 18 E48kr | 0 |
| F7kr | Job 18 D48v24 | 0 |
| F7kr | Job 18 E64k | 0 |
| F7kr | Job 18 X400k48 | 2 |
| F7kr | Job 18 X100k48 | 0 |
| F7kr | Job 18 E48t | 2 |
| F7kr | Job 18 E24t | 0 |
| F7kr | Job 19 E64kr | 0 |
| F7kr | Job 19 E48tr | 1 |
| F7kr | Job 19 E64t (incomplete) | 1 |
| F7kr | Job 19 E48w | 2 |
| F7kr | Job 20 F7k | 0 |
| F7kr | Job 20 F7t | 0 |
| F7kr | Job 20 E64tr (incomplete) | 0 |
| F7kr | Job 20 F7w | 0 |
| F3k | Job 17 X400r | 0 |
| F3k | Job 17 E24kr | 0 |
| F3k | Job 17 X400m3 | 0 |
| F3k | Job 17 X100m3 | 1 |
| F3k | Job 17 E48k | 0 |
| F3k | Job 17 X400w | 0 |
| F3k | Job 18 E48kr | 0 |
| F3k | Job 18 D48v24 | 0 |
| F3k | Job 18 E64k | 0 |
| F3k | Job 18 X400k48 | 1 |
| F3k | Job 18 X100k48 | 1 |
| F3k | Job 18 E48t | 0 |
| F3k | Job 18 E24t | 0 |
| F3k | Job 19 E64kr | 0 |
| F3k | Job 19 E48tr | 2 |
| F3k | Job 19 E64t (incomplete) | 0 |
| F3k | Job 19 E48w | 0 |
| F3k | Job 20 F7k | 0 |
| F3k | Job 20 F7t | 0 |
| F3k | Job 20 E64tr (incomplete) | 0 |
| F3k | Job 20 F7w | 0 |
| F1k | Job 17 X400r | 1 |
| F1k | Job 17 E24kr | 0 |
| F1k | Job 17 X400m3 | 0 |
| F1k | Job 17 X100m3 | 1 |
| F1k | Job 17 E48k | 0 |
| F1k | Job 17 X400w | 0 |
| F1k | Job 18 E48kr | 1 |
| F1k | Job 18 D48v24 | 0 |
| F1k | Job 18 E64k | 0 |
| F1k | Job 18 X400k48 | 1 |
| F1k | Job 18 X100k48 | 0 |
| F1k | Job 18 E48t | 0 |
| F1k | Job 18 E24t | 1 |
| F1k | Job 19 E64kr | 0 |
| F1k | Job 19 E48tr | 0 |
| F1k | Job 19 E64t (incomplete) | 1 |
| F1k | Job 19 E48w | 1 |
| F1k | Job 20 F7k | 2 |
| F1k | Job 20 F7t | 1 |
| F1k | Job 20 E64tr (incomplete) | 1 |
| F1k | Job 20 F7w | 0 |
| E64w | Job 17 X400r | 1 |
| E64w | Job 17 E24kr | 1 |
| E64w | Job 17 X400m3 | 0 |
| E64w | Job 17 X100m3 | 0 |
| E64w | Job 17 E48k | 0 |
| E64w | Job 17 X400w | 2 |
| E64w | Job 18 E48kr | 1 |
| E64w | Job 18 D48v24 | 0 |
| E64w | Job 18 E64k | 1 |
| E64w | Job 18 X400k48 | 0 |
| E64w | Job 18 X100k48 | 1 |
| E64w | Job 18 E48t | 0 |
| E64w | Job 18 E24t | 0 |
| E64w | Job 19 E64kr | 1 |
| E64w | Job 19 E48tr | 1 |
| E64w | Job 19 E64t (incomplete) | 0 |
| E64w | Job 19 E48w | 0 |
| E64w | Job 20 F7k | 0 |
| E64w | Job 20 F7t | 0 |
| E64w | Job 20 E64tr (incomplete) | 0 |
| E64w | Job 20 F7w | 1 |

## Declared verdicts

E64tr2, only if complete, gives E64t its verdict: REPLICATED when E64tr2 alone gives Elo above 0 AND the pool of E64t, E64tr and E64tr2 (pentanomial counts added; all three were cut only by the clock or are complete) has a 95 % interval whose lower end is above 0. A cut E64tr2 gives no verdict.
E64t REPLICATED yes. Fresh Elo +13.0300, pooled lower 95% bound +8.1187. Evidence incomplete (partial): interval reconstructed from summed pentanomial counts. E64t incomplete, 1888 paired games included. E64tr incomplete, 1604 paired games included.

F7kr, only if complete, gives F7k its verdict: REPLICATED (a loss) when F7kr alone gives Elo below 0 AND the pool of F7k and F7kr has a 95 % interval whose upper end is below 0.
F7k REPLICATED yes. Fresh Elo -23.1400, pooled upper 95% bound -15.4507. Evidence complete: interval reconstructed from summed pentanomial counts.

F3k, F1k and E64w are exploratory: no verdict, a row each; one whose 95 % interval lies wholly above or wholly below 0 earns a fresh seed in a later job before anything is said about it.

## Facts

- All seven Job 21 matches completed before the 14:40:14Z cutoff. E64w finished last at 14:36:02Z. The saved PGNs contain 10,000 measured and 300 control games, all in complete color-reversed pairs with no unpaired or unresolved games. [Independent audit](sol/job21/independent-Job21.txt)
- At 10,000 nodes, EvalSwingMult 64 versus zero on the Job 4 counting build met its three-seed rule. The complete fresh seed gave +13.03 Elo [+2.51, +23.55] in 2,000 games. The pool gave +14.43 [+8.12, +20.75] in 5,492 games, including 1,888 and 1,604 complete games from the two prior clock-cut seeds. It contained one pair with identical ordered UCI moves. The three seed pairs shared zero exact FENs. [Fresh PGN](sol/job21/raw/E64tr2.pgn) · [First cut PGN](sol/job19/raw/E64t.pgn) · [Second cut PGN](sol/job20/raw/E64tr.pgn)
- At 2,000 nodes on PCA, the FailHighBlend 7 loss versus zero replicated. The fresh seed gave −23.14 Elo [−35.33, −10.95] in 2,000 games. The pool gave −24.10 [−32.75, −15.45] in 4,000 games and the two seeds shared no exact FENs. [Fresh F7kr PGN](sol/job21/raw/F7kr.pgn) · [Original F7k PGN](sol/job20/raw/F7k.pgn)
- Each exploratory interval excluded zero. On PCA at 2,000 nodes, FailHighBlend 3 versus zero gave −16.86 Elo [−28.98, −4.74], and 1 versus zero gave −13.56 [−25.71, −1.41]. On the counting build at 20,000 nodes, EvalSwingMult 64 versus zero gave +14.43 [+4.49, +24.37]. Each comparison used a single 2,000-game seed and earns a fresh seed. [FailHighBlend 3 PGN](sol/job21/raw/F3k.pgn) · [FailHighBlend 1 PGN](sol/job21/raw/F1k.pgn) · [20,000-node EvalSwingMult PGN](sol/job21/raw/E64w.pgn)
- The opening audit covered 168 file comparisons, with 41 nonzero intersections and at most two shared exact FENs per comparison. Three of five forecasts survived. F1k and E64w missed on magnitude. [Full readback](sol/job21/readback.txt)

## Suspicions

The three FailHighBlend settings measured against zero at 2,000 nodes are consistent with a larger loss as more bits are enabled, but the experiments used separate opening samples. The single 20,000-node Mult-64 gain qualifies for a second seed. Its point estimate is close to the 10,000-node pool.

## What I did not do

I reused the two pinned executables. Source and weights in the repository, the owner's PC and its running tune, and the training loop were outside this job.

## What I am not sure about

The estimates apply to these builds, the embedded net, PC20 and these opening samples. The lower FailHighBlend settings each used a single seed. The Elo comparisons use separately sampled zero baselines at each budget.

## Reproduction

Both executables trace to Forge PC r15 at base `6b98f2170a3210e71beed04bbd2553972c253ed7` plus the PC patch. PCA adds Kimi5's A2A5 patch to the plain PC tree. The Job 4 executable adds the Job 2 counters and Job 4 buttons to PC r15. Both used GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4, `FORGE_MATE_ALPHA_GUARD=1` and embedded AL1 s198 (weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`). [Job 20 PCA build](REPORT_sol_job20.md) · [Job 4 counting build](REPORT_sol_job4.md)

Fastchess gave both engines PC20, Threads 1, Hash 16 MiB, one PV, OwnBook false and the exact options in each sidecar. The PCA cells used Mult 0 and explicitly set FHB on both sides. The Job 4 cells used Mult 64 versus 0. Every match used default Max 200 and a 300-move ceiling. [Match settings and outputs](sol/job21/raw)

From `forge-combo29/sol/job21`, with Python 3 and python-chess 1.11.2, these commands regenerate the controls, results, verdicts and opening comparisons.

```sh
python3 analyze_matches21.py gates raw --pca-sha256 pca.sha256
python3 analyze_matches21.py table raw --pca-sha256 pca.sha256 \
  --job17-raw ../job17/raw --job18-raw ../job18/raw --job19-raw ../job19/raw \
  --job20-raw ../job20/raw --prediction prediction.txt
```

[Full readback](sol/job21/readback.txt) · [UTC stamps](sol/job21/stamps.txt) · [Precommit tree readback](sol/job21/precommit-readback.txt)

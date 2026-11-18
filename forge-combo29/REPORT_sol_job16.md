# Sol — Job 16 EvalSwingMax and higher doses

## Step 0 and gates

1. **The counting executable passed all eight fresh-process pins.** Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 at perft 5. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. The UCI listing was `option name EvalSwingMax type spin default 200 min 50 max 400`. The official binary printed `fastchess alpha 1.8.3 20261107-d7b47e8` and the official opening EPD hash was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. [Step 0 stdout](sol/job16/step0-count.raw.txt) · [Build and book receipt](sol/job16/build.txt)
2. **K5 passed 50/50.** Both engines used PC20, Mult 6 and Max 200 explicitly at 2,000 nodes. The two setup processes each reached `readyok` with zero refusals. Every opening had identical move lists in both colors and 1–1 points. W-L-D 27–27–46 and pentanomial `[0, 0, 50, 0, 0]` in 100 games. [K5 PGN](sol/job16/raw/K5.pgn) · [Both UCI preflights](sol/job16/raw/K5.meta)
3. **C5 passed.** Plain PC20 at 10,000 versus 20,000 nodes gave 13–110–77 over 200 games, pentanomial `[26, 48, 23, 3, 0]` and Elo −183.97 [−218.92, −149.02]. It met both declared control thresholds. [C5 PGN](sol/job16/raw/C5.pgn) · [C5 output](sol/job16/raw/C5.out) · [Gate readback](sol/job16/gates-K5C5.txt)

The [prediction](sol/job16/prediction.txt) was committed alone as `c548c9b0c6535a040f606235e21b34bf57cd7bb7` after the two gates and before any measured game. The controls used four workers. Slot 1 used two workers for X400, X100, X50, D12v3b and E24k in sequence. Slot 2 used two for X400t and then E12t. [UTC stamps](sol/job16/stamps.txt)

## Prediction grades

The observed Elo must have the forecast sign and a magnitude within a factor of 1.5. A zero forecast requires zero. Replication forecasts use exact yes/no matching.

| Forecast | Guess | Observed | Grade | Evidence status |
|---|---:|---:|---|---|
| X400 Elo | +6.00 | -10.25 | KILLED (sign) | complete |
| X100 Elo | -5.00 | -0.87 | KILLED | complete |
| X50 Elo | -10.00 | -3.65 | KILLED | complete |
| D12v3b Elo | +9.00 | -1.74 | KILLED (sign) | complete |
| E24k Elo | +12.00 | +20.17 | KILLED | complete |
| X400t Elo | +3.00 | +6.25 | KILLED | complete |
| E12t Elo | +6.00 | -4.00 | KILLED (sign) | complete |
| D12v3 REPLICATED | yes | no | KILLED | complete: interval reconstructed from summed penta counts |

8 KILLED, 0 survive, 0 ungraded.

## Table L. EvalSwingMult and EvalSwingMax paired-game results

W-L-D is from A's perspective. The 95% intervals use the fastchess pentanomial Elo ± halfwidth convention. Each analyzed pair contains both colors.

| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] | Reading |
|---|---|---:|---|---|---|---|
| X400 | complete | 2000 | 648-707-645 | 57, 162, 598, 149, 34 | -10.25 [-19.08, -1.42] | exploratory, earns a fresh seed (below zero) |
| X100 | complete | 2000 | 673-678-649 | 103, 219, 357, 222, 99 | -0.87 [-12.91, +11.17] | exploratory, interval includes zero |
| X50 | complete | 2000 | 673-694-633 | 107, 230, 347, 209, 107 | -3.65 [-15.91, +8.61] | exploratory, interval includes zero |
| D12v3 | complete | 2000 | 726-645-629 | 91, 199, 375, 208, 127 | +14.08 [+1.91, +26.25] | two-seed D12v3 comparison |
| D12v3b | complete | 2000 | 673-683-644 | 103, 216, 367, 216, 98 | -1.74 [-13.71, +10.23] | two-seed D12v3 comparison |
| D12v3 + D12v3b pooled | complete: interval reconstructed from summed penta counts | 4000 | 1399-1328-1273 | 194, 415, 742, 424, 225 | +6.17 [-2.37, +14.71] | two-seed D12v3 comparison |
| E24k | complete | 2000 | 748-632-620 | 79, 200, 371, 226, 124 | +20.17 [+8.21, +32.13] | exploratory, earns a fresh seed (above zero) |
| X400t | complete | 2000 | 590-554-856 | 40, 225, 451, 227, 57 | +6.25 [-3.62, +16.12] | exploratory, interval includes zero |
| E12t | complete | 2000 | 572-595-833 | 64, 251, 386, 242, 57 | -4.00 [-14.64, +6.64] | exploratory, interval includes zero |

D12v3 (job 15 + D12v3b) gets a verdict by the rule of file 15: REPLICATED when its fresh seed alone gives Elo above 0 AND the pool of its two seeds (pentanomial counts added) has a 95 % interval whose lower end is above 0. Every other cell is exploratory: no verdict, a row each; one whose 95 % interval lies wholly above or wholly below 0 earns a fresh seed in a later job before anything is said about it.
D12v3 REPLICATED: no. Fresh Elo -1.7400, pooled lower 95% bound -2.3700. Evidence complete: interval reconstructed from summed penta counts.

## Shared openings

Counts are distinct exact FEN tags shared by two files. Each file contributes one opening per complete color-reversed pair. The inventory shows complete pairs and distinct FEN tags.

| File | Status | Complete pairs | Distinct exact FENs |
|---|---|---:|---:|
| K5 | saved | 50 | 50 |
| C5 | saved | 100 | 100 |
| X400 | complete | 1000 | 1000 |
| X100 | complete | 1000 | 1000 |
| X50 | complete | 1000 | 1000 |
| D12v3b | complete | 1000 | 1000 |
| E24k | complete | 1000 | 1000 |
| X400t | complete | 1000 | 1000 |
| E12t | complete | 1000 | 1000 |
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

| File A | File B | Shared exact FENs |
|---|---|---:|
| K5 | C5 | 0 |
| K5 | X400 | 0 |
| K5 | X100 | 0 |
| K5 | X50 | 0 |
| K5 | D12v3b | 0 |
| K5 | E24k | 0 |
| K5 | X400t | 0 |
| K5 | E12t | 0 |
| C5 | X400 | 0 |
| C5 | X100 | 0 |
| C5 | X50 | 0 |
| C5 | D12v3b | 0 |
| C5 | E24k | 0 |
| C5 | X400t | 0 |
| C5 | E12t | 0 |
| X400 | X100 | 0 |
| X400 | X50 | 0 |
| X400 | D12v3b | 0 |
| X400 | E24k | 0 |
| X400 | X400t | 1 |
| X400 | E12t | 0 |
| X100 | X50 | 0 |
| X100 | D12v3b | 0 |
| X100 | E24k | 1 |
| X100 | X400t | 0 |
| X100 | E12t | 1 |
| X50 | D12v3b | 2 |
| X50 | E24k | 0 |
| X50 | X400t | 1 |
| X50 | E12t | 0 |
| D12v3b | E24k | 0 |
| D12v3b | X400t | 0 |
| D12v3b | E12t | 0 |
| E24k | X400t | 0 |
| E24k | E12t | 1 |
| X400t | E12t | 0 |
| K5 | Job 13 E2 | 0 |
| K5 | Job 13 E3k | 0 |
| K5 | Job 13 E6 | 0 |
| K5 | Job 14 E3k2 | 0 |
| K5 | Job 14 E6b | 0 |
| K5 | Job 14 E6k | 0 |
| K5 | Job 14 E12k | 0 |
| K5 | Job 15 E6k2 | 0 |
| K5 | Job 15 E12k2 | 0 |
| K5 | Job 15 D12v3 | 0 |
| K5 | Job 15 E6m | 0 |
| K5 | Job 15 E6t | 0 |
| C5 | Job 13 E2 | 0 |
| C5 | Job 13 E3k | 0 |
| C5 | Job 13 E6 | 0 |
| C5 | Job 14 E3k2 | 0 |
| C5 | Job 14 E6b | 0 |
| C5 | Job 14 E6k | 0 |
| C5 | Job 14 E12k | 0 |
| C5 | Job 15 E6k2 | 0 |
| C5 | Job 15 E12k2 | 0 |
| C5 | Job 15 D12v3 | 0 |
| C5 | Job 15 E6m | 0 |
| C5 | Job 15 E6t | 0 |
| X400 | Job 13 E2 | 1 |
| X400 | Job 13 E3k | 1 |
| X400 | Job 13 E6 | 1 |
| X400 | Job 14 E3k2 | 0 |
| X400 | Job 14 E6b | 0 |
| X400 | Job 14 E6k | 0 |
| X400 | Job 14 E12k | 0 |
| X400 | Job 15 E6k2 | 1 |
| X400 | Job 15 E12k2 | 0 |
| X400 | Job 15 D12v3 | 1 |
| X400 | Job 15 E6m | 0 |
| X400 | Job 15 E6t | 0 |
| X100 | Job 13 E2 | 0 |
| X100 | Job 13 E3k | 0 |
| X100 | Job 13 E6 | 0 |
| X100 | Job 14 E3k2 | 0 |
| X100 | Job 14 E6b | 0 |
| X100 | Job 14 E6k | 2 |
| X100 | Job 14 E12k | 1 |
| X100 | Job 15 E6k2 | 1 |
| X100 | Job 15 E12k2 | 0 |
| X100 | Job 15 D12v3 | 1 |
| X100 | Job 15 E6m | 0 |
| X100 | Job 15 E6t | 0 |
| X50 | Job 13 E2 | 0 |
| X50 | Job 13 E3k | 1 |
| X50 | Job 13 E6 | 0 |
| X50 | Job 14 E3k2 | 2 |
| X50 | Job 14 E6b | 0 |
| X50 | Job 14 E6k | 0 |
| X50 | Job 14 E12k | 2 |
| X50 | Job 15 E6k2 | 0 |
| X50 | Job 15 E12k2 | 0 |
| X50 | Job 15 D12v3 | 1 |
| X50 | Job 15 E6m | 0 |
| X50 | Job 15 E6t | 3 |
| D12v3b | Job 13 E2 | 1 |
| D12v3b | Job 13 E3k | 0 |
| D12v3b | Job 13 E6 | 0 |
| D12v3b | Job 14 E3k2 | 1 |
| D12v3b | Job 14 E6b | 0 |
| D12v3b | Job 14 E6k | 1 |
| D12v3b | Job 14 E12k | 1 |
| D12v3b | Job 15 E6k2 | 1 |
| D12v3b | Job 15 E12k2 | 0 |
| D12v3b | Job 15 D12v3 | 0 |
| D12v3b | Job 15 E6m | 1 |
| D12v3b | Job 15 E6t | 1 |
| E24k | Job 13 E2 | 0 |
| E24k | Job 13 E3k | 0 |
| E24k | Job 13 E6 | 1 |
| E24k | Job 14 E3k2 | 0 |
| E24k | Job 14 E6b | 0 |
| E24k | Job 14 E6k | 0 |
| E24k | Job 14 E12k | 0 |
| E24k | Job 15 E6k2 | 0 |
| E24k | Job 15 E12k2 | 0 |
| E24k | Job 15 D12v3 | 0 |
| E24k | Job 15 E6m | 0 |
| E24k | Job 15 E6t | 1 |
| X400t | Job 13 E2 | 0 |
| X400t | Job 13 E3k | 1 |
| X400t | Job 13 E6 | 0 |
| X400t | Job 14 E3k2 | 0 |
| X400t | Job 14 E6b | 0 |
| X400t | Job 14 E6k | 0 |
| X400t | Job 14 E12k | 0 |
| X400t | Job 15 E6k2 | 0 |
| X400t | Job 15 E12k2 | 0 |
| X400t | Job 15 D12v3 | 0 |
| X400t | Job 15 E6m | 0 |
| X400t | Job 15 E6t | 0 |
| E12t | Job 13 E2 | 1 |
| E12t | Job 13 E3k | 0 |
| E12t | Job 13 E6 | 0 |
| E12t | Job 14 E3k2 | 0 |
| E12t | Job 14 E6b | 0 |
| E12t | Job 14 E6k | 0 |
| E12t | Job 14 E12k | 0 |
| E12t | Job 15 E6k2 | 0 |
| E12t | Job 15 E12k2 | 0 |
| E12t | Job 15 D12v3 | 0 |
| E12t | Job 15 E6m | 0 |
| E12t | Job 15 E6t | 0 |

## Facts

- All nine scheduled matches finished before the 09:52:44Z cutoff, with 14,300 scored games in complete pairs. The slots both began at 09:07:17Z. E12t finished last at 09:49:52Z. The controls used four workers and the two measured slots each used two. [Independent games and schedule readback](sol/job16/independent-Job16.txt)
- The fresh 2,000-node dose-12-versus-3 seed gave −1.74 Elo [−13.71, +10.23] in 2,000 games. Its 4,000-game pool with Job 15 D12v3 gave +6.17 [−2.37, +14.71]. The fresh seed was below zero and the pooled interval included zero. The two seeds share zero opening FENs.
- Among the exploratory 2,000-game cells, only two intervals excluded zero. At 2,000 nodes and Mult 6, clip 400 versus 200 scored −10.25 [−19.08, −1.42]. At 2,000 nodes and the default clip, Mult 24 versus zero scored +20.17 [+8.21, +32.13]. Each meets the handoff's rule for a fresh seed. The four other exploratory intervals include zero. All eight preregistered forecasts missed their grading rule.
- Of the 144 opening-file comparisons, 31 had shared exact FENs. The largest intersection was three FENs for X50 versus Job 15 E6t. [Shared-opening readback](sol/job16/readback.txt)
- Opus reported its separate PC dose-3 match at softnodes 2000 with the PC round-33 net. It gave +10.60 Elo [+2.62, +18.59] over 4,000 games after its own controls passed. That result is attributed to the PC handoff and uses a different evaluation and node mode. [Opus handoff](https://github.com/couns0538-sketch/dwqww/blob/63d9b2deb6e1e2cb03e1434d876bdd653b00d152/forge-combo29/soak_all/FABLE_TO_sol_16.md)

## Suspicions

At Mult 6, the 2,000-node result suggests that allowing larger quiet-history updates can cost strength. The 10,000-node clip-400 estimate had a positive point estimate and a wider range around zero. Both findings leave the budget dependence open. The dose-24 result is a single-seed signal at the default clip.

## What I did not do

This job used only the unchanged Cloud counting executable and its embedded evaluation. The owner's PC match was reported in the handoff. I ran no PC program, engine build, training or tuning.

## What I am not sure about

The exploratory cells each use one seed and the same embedded evaluation. The clip and dose results may depend on the evaluation differences that reach the quiet-history update. Confirmation on a fresh seed and transfer to the owner's engine and net are separate measurements.

## Reproduction

Both sides used Forge PC r15 at `6b98f2170a3210e71beed04bbd2553972c253ed7` with the Job 2 counters and Job 4 buttons, GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and `FORGE_MATE_ALPHA_GUARD=1`. Both used PC20, one thread, Hash 16 MiB, one PV, OwnBook false and embedded AL1 s198, weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. The X arms both set Mult 6 explicitly and differed only in their explicit clip, with B at 200. D12v3b, E24k and E12t used the default clip. Each side had its own UCI preflight reply in the match sidecar. [Raw files and options](sol/job16/raw) · [Forge build](REPORT_sol_job4.md)

Fastchess paired each sampled FEN with colors exchanged under the stated hard node budgets, with a 300-move ceiling and no separate resign or draw adjudication flags. Each measured match logged a rating block after every completed pair. The common play cutoff was 09:52:44Z. [Build receipt](sol/job16/build.txt) · [Match clocks](sol/job16/stamps.txt)

From `forge-combo29/sol/job16`, with Python 3 and python-chess 1.11.2, these commands regenerate the gates, all table cells and the shared-opening counts.

```sh
python3 analyze_matches16.py gates raw
python3 analyze_matches16.py table raw --job13-raw ../job13/raw --job14-raw ../job14/raw \
  --job15-raw ../job15/raw --prediction prediction.txt
```

[Complete report readback](sol/job16/readback.txt) · [Precommit tree readback](sol/job16/precommit-readback.txt)

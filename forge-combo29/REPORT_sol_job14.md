# Sol — Job 14 EvalSwingMult fresh seeds and low-budget doses

## Step 0 and gates

1. **The counting executable passed all eight fresh-process pins.** Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. The executable SHA-256 was `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. The verified official build printed `fastchess alpha 1.8.3 20261107-d7b47e8`. The official opening EPD SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. [Step 0 stdout](sol/job14/step0-count.raw.txt) · [Build and book receipt](sol/job14/build.txt)
2. **K3 passed 50/50.** All pairs shared their FEN, reversed engine colors and had identical move lists and 1–1 points. In 100 games at 20,000 nodes with plain PC20 on both sides, W-L-D was 32–32–36 and pentanomial `[0, 0, 50, 0, 0]`. [K3 PGN](sol/job14/raw/K3.pgn) · [K3 output](sol/job14/raw/K3.out)
3. **C3 passed.** With otherwise plain PC20 at 10,000 versus 20,000 nodes, A scored 20–116–64 across 200 games. Pentanomial `[25, 48, 25, 2, 0]`, Elo −181.70 and 95% interval [−215.53, −147.87]. It met the −100 ceiling and the upper confidence bound was below zero. [C3 PGN](sol/job14/raw/C3.pgn) · [C3 output](sol/job14/raw/C3.out) · [Gate readback](sol/job14/gates-K3C3.txt)

The [prediction](sol/job14/prediction.txt) was committed alone as `96538bf0617b20c5a279cba9f0279da03f15f67d`. K3 and C3 completed before it. The slots began after the push. The controls used four workers. Each measured slot used two workers. E6b occupied slot 1. E3k2, E6k and E12k ran sequentially in slot 2. [UTC stamps](sol/job14/stamps.txt)

## Prediction grades

A nonzero Elo forecast requires the observed sign and a magnitude within a factor of 1.5. Zero requires zero. Replication forecasts are exact yes/no grades.

| Forecast | Guess | Observed | Grade |
|---|---:|---:|---|
| E3k2 Elo | +10.00 | +16.86 | KILLED |
| E6b Elo | +10.00 | +7.12 | survives |
| E6k Elo | +9.00 | +15.65 | KILLED |
| E12k Elo | +3.00 | +17.73 | KILLED |
| E3k REPLICATED | yes | yes | survives |
| E6 REPLICATED | yes | yes | survives |

3 KILLED, 3 survive, 0 ungraded.

## Table J. EvalSwingMult paired-game results

W-L-D is from A's perspective. The 95% intervals use the fastchess pentanomial Elo ± halfwidth convention. Each analyzed pair contains both colors.

| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] |
|---|---|---:|---|---|---|
| E3k | complete | 2000 | 723-639-638 | 78, 205, 377, 235, 105 | +14.60 [+2.95, +26.25] |
| E3k2 | complete | 2000 | 710-613-677 | 81, 217, 342, 244, 116 | +16.86 [+4.84, +28.88] |
| E3k + E3k2 pooled | complete: interval reconstructed from summed penta counts | 4000 | 1433-1252-1315 | 159, 422, 719, 479, 221 | +15.73 [+7.37, +24.10] |
| E6 | complete | 1000 | 304-256-440 | 21, 110, 205, 128, 36 | +16.69 [+2.02, +31.36] |
| E6b | complete | 2000 | 569-528-903 | 48, 217, 437, 242, 56 | +7.12 [-2.95, +17.19] |
| E6 + E6b pooled | complete: interval reconstructed from summed penta counts | 3000 | 873-784-1343 | 69, 327, 642, 370, 92 | +10.31 [+2.01, +18.61] |
| E6k | complete | 2000 | 728-638-634 | 106, 175, 359, 243, 117 | +15.65 [+3.33, +27.97] |
| E12k | complete | 2000 | 736-634-630 | 97, 190, 356, 228, 129 | +17.73 [+5.36, +30.10] |

A cell is REPLICATED when its fresh seed alone gives Elo above 0 AND the pool of its two seeds (pentanomial counts added) has a 95 % interval whose lower end is above 0. E6k and E12k are exploratory: no verdict, a row each.
E3k REPLICATED: yes. Fresh Elo +16.8600, pooled lower 95% bound +7.3654.
E6 REPLICATED: yes. Fresh Elo +7.1200, pooled lower 95% bound +2.0056.

## Facts

- All six scheduled matches finished before 08:10:30Z, with 8,300 scored games and every game in a complete color-reversed pair. Both measured slots started at 07:24:22Z. Slot 2 switched from E3k2 to E6k at 07:30:44Z and to E12k at 07:36:46Z. E6b finished last at 08:01:35Z. One E6b game hit the prescribed 300-move ceiling and was recorded as an adjudicated draw. [Independent counts, settings and clocks](sol/job14/independent-Job14.txt)
- At 2,000 nodes and dose 3, the fresh seed gave +16.86 Elo [+4.84, +28.88]. The 4,000-game pool gave +15.73 [+7.37, +24.10]. At 20,000 nodes and dose 6, the fresh seed gave +7.12 [−2.95, +17.19] and the 3,000-game pool gave +10.31 [+2.01, +18.61]. Each pair of seeds compared in a pool used disjoint opening FENs. Both matched the declared replication rule.
- At 2,000 nodes the two exploratory 2,000-game cells gave +15.65 Elo [+3.33, +27.97] for dose 6 and +17.73 [+5.36, +30.10] for dose 12. The separate seeds have broadly overlapping intervals. Both replication predictions and the E6b magnitude prediction survived.

## Suspicions

The positive low-budget results span all three doses tested against zero. The results leave the shape of the low-budget dose response open. The 2,000-node dose-3 result met the handoff's prerequisite for a separate PC match.

## What I did not do

All runs used the unchanged counting executable on Codex Cloud. Engine source, weights, training and the owner's running tune were outside the match scope.

## What I am not sure about

Each pooled replication measures a specified dose and hard node budget on this build, embedded net and opening source. The exploratory doses each have one seed. A direct comparison of doses against one another, and transfer to the owner's engine and net, remain unmeasured.

## Reproduction

Both sides used Forge PC r15 at `6b98f2170a3210e71beed04bbd2553972c253ed7`, the Job 2 counters and Job 4 buttons, GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and `FORGE_MATE_ALPHA_GUARD=1`. Each used the PC20 preset, one thread, Hash 16 MiB, one PV, OwnBook false and embedded AL1 s198, weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. A's single effective override was the specified `EvalSwingMult` dose and B used zero. Every A preflight finished at `readyok`. [Build details](REPORT_sol_job4.md) · [Raw match files and sidecars](sol/job14/raw)

Fastchess paired each sampled opening in both colors at the fixed node budgets, with no separate resign or draw adjudication flags and a 300-move ceiling. Each measured match logged a rating block at every completed pair. The play cutoff was 08:10:30Z, 50 minutes after the claim. [Job 13 seed results](REPORT_sol_job13.md) · [UTC and slot record](sol/job14/stamps.txt)

From `forge-combo29/sol/job14`, with Python 3 and python-chess 1.11.2, these commands regenerate both gates, every Table J cell and the grades.

```sh
python3 analyze_matches14.py gates raw
python3 analyze_matches14.py table raw --job13-raw ../job13/raw --prediction prediction.txt
```

[Read counts and table recomputation](sol/job14/readback.txt) · [Precommit tree readback](sol/job14/precommit-readback.txt)

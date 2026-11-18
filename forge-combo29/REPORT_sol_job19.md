# Sol — Job 19 high-dose replication and the 20,000-node comparison

## Step 0 and gates

1. **The counting executable passed all eight fresh-process pins.** Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. Counting SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. Fastchess printed `fastchess alpha 1.8.3 20261107-d7b47e8`, and the official EPD's SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. The UCI lines were `option name EvalSwingMult type spin default 0 min 0 max 64` and `option name EvalSwingMax type spin default 200 min 50 max 400`. [Step 0 stdout](sol/job19/step0-count.raw.txt) · [Build and book receipt](sol/job19/build.txt)
2. **K8 passed 50/50.** PC20 with explicit Mult 64 on both sides at 2,000 nodes gave identical full ordered moves and 1–1 in each reversed-color pair. Both UCI preflights reached `readyok` with zero refusals. A went 34–34–32 with pentanomial `[0, 0, 50, 0, 0]` in 100 games. [K8 PGN](sol/job19/raw/K8.pgn) · [K8 preflights](sol/job19/raw/K8.meta)
3. **C8 passed.** PC20 with Mult 0 on both sides at 10,000 versus 20,000 nodes gave A 11–117–72 with pentanomial `[29, 49, 21, 1, 0]` over 200 games. Elo was −205.04 with a 95% interval of [−239.93, −170.15], passing the −100 threshold and upper-bound gate. [C8 PGN](sol/job19/raw/C8.pgn) · [C8 output](sol/job19/raw/C8.out) · [Independent gates](sol/job19/independent-gates.txt)

The [prediction](sol/job19/prediction.txt) was the sole file in commit `28af66e83e9374ab442813094fad2b08c20a4ee1` after both gates passed and before measured play. Each concurrent slot used two workers. Slot 1 assigned E64kr at 2,000 nodes followed by E48tr and E64t at 10,000 nodes. Slot 2 assigned E48w at 20,000 nodes. [UTC stamps](sol/job19/stamps.txt)

## Prediction grades

The observed Elo must have the forecast sign and fall within a factor of 1.5 of its magnitude. A zero forecast requires zero. Replication forecasts use exact yes/no matching.

| Forecast | Guess | Observed | Grade | Evidence status |
|---|---:|---:|---|---|
| E64kr Elo | +30.00 | +33.11 | survives | complete |
| E48tr Elo | +12.00 | +3.13 | KILLED | complete |
| E64t Elo | +15.00 | +12.89 | survives | incomplete (interrupted) |
| E48w Elo | +6.00 | +5.04 | survives | complete |
| E64k REPLICATED | yes | yes | survives | complete: interval reconstructed from summed penta counts |
| E48t REPLICATED | yes | yes | survives | complete: interval reconstructed from summed penta counts |

1 KILLED, 5 survive, 0 ungraded.

## Table O. EvalSwing paired games and identical move lists

W-L-D is from A's perspective. Intervals use the fastchess 95% pentanomial Elo ± halfwidth convention. Identical pairs share the complete ordered UCI move sequence.

| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Reading |
|---|---|---:|---|---|---|---:|---|
| E64k | complete | 2000 | 767-574-659 | 71, 172, 379, 249, 129 | +33.63 [+21.80, +45.46] | 0/1000 | two-seed gain comparison |
| E64kr | complete | 2000 | 769-579-652 | 85, 176, 348, 246, 145 | +33.11 [+20.69, +45.53] | 0/1000 | two-seed gain comparison |
| E64k + E64kr pooled | complete: interval reconstructed from summed penta counts | 4000 | 1536-1153-1311 | 156, 348, 727, 495, 274 | +33.37 [+24.79, +41.94] | 0/2000 | two-seed gain comparison |
| E48t | complete | 2000 | 601-514-885 | 45, 209, 427, 252, 67 | +15.12 [+4.88, +25.36] | 0/1000 | two-seed gain comparison |
| E48tr | complete | 2000 | 594-576-830 | 76, 221, 377, 261, 65 | +3.13 [-7.88, +14.14] | 0/1000 | two-seed gain comparison |
| E48t + E48tr pooled | complete: interval reconstructed from summed penta counts | 4000 | 1195-1090-1715 | 121, 430, 804, 513, 132 | +9.12 [+1.60, +16.65] | 0/2000 | two-seed gain comparison |
| E64t | incomplete (interrupted) | 1888 | 576-506-806 | 43, 218, 376, 240, 67 | +12.89 [+2.09, +23.69] | 0/944 | exploratory, earns a fresh seed (above zero) |
| E48w | complete | 2000 | 542-513-945 | 49, 236, 407, 253, 55 | +5.04 [-5.20, +15.28] | 0/1000 | exploratory, interval includes zero |

E64k (job 18 + E64kr) and E48t (job 18 + E48tr) each get a verdict by the rule of file 15: REPLICATED when the fresh seed alone gives Elo above 0 AND the pool of the two seeds (pentanomial counts added) has a 95 % interval whose lower end is above 0. E64t and E48w are exploratory: no verdict, a row each; one whose 95 % interval lies wholly above or wholly below 0 earns a fresh seed in a later job before anything is said about it.
E64k REPLICATED yes. Fresh Elo +33.1100, pooled lower 95% bound +24.7944. Evidence complete: interval reconstructed from summed penta counts.
E48t REPLICATED yes. Fresh Elo +3.1300, pooled lower 95% bound +1.5993. Evidence complete: interval reconstructed from summed penta counts.

## Shared openings

Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct FEN strings.

Job 18 E64k and E64kr distinct shared exact FENs = 0.
Job 18 E48t and E48tr distinct shared exact FENs = 0.

| File | Status | Complete pairs | Distinct exact FENs |
|---|---|---:|---:|
| K8 | complete | 50 | 50 |
| C8 | complete | 100 | 100 |
| E64kr | complete | 1000 | 1000 |
| E48tr | complete | 1000 | 1000 |
| E64t | incomplete (interrupted) | 944 | 944 |
| E48w | complete | 1000 | 1000 |
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
| Job 17 X400r | saved | 1000 | 1000 |
| Job 17 E24kr | saved | 1000 | 1000 |
| Job 17 X400m3 | saved | 1000 | 1000 |
| Job 17 X100m3 | saved | 1000 | 1000 |
| Job 17 E48k | saved | 1000 | 1000 |
| Job 17 X400w | saved | 800 | 800 |
| Job 18 E48kr | saved | 1000 | 1000 |
| Job 18 D48v24 | saved | 1000 | 1000 |
| Job 18 E64k | complete | 1000 | 1000 |
| Job 18 X400k48 | saved | 1000 | 1000 |
| Job 18 X100k48 | saved | 1000 | 1000 |
| Job 18 E48t | complete | 1000 | 1000 |
| Job 18 E24t | saved | 1000 | 1000 |

### Within Job 19

| File A | File B | Shared exact FENs |
|---|---|---:|
| K8 | C8 | 0 |
| K8 | E64kr | 0 |
| K8 | E48tr | 0 |
| K8 | E64t (incomplete) | 0 |
| K8 | E48w | 0 |
| C8 | E64kr | 0 |
| C8 | E48tr | 0 |
| C8 | E64t (incomplete) | 0 |
| C8 | E48w | 0 |
| E64kr | E48tr | 1 |
| E64kr | E64t (incomplete) | 0 |
| E64kr | E48w | 0 |
| E48tr | E64t (incomplete) | 1 |
| E48tr | E48w | 0 |
| E64t (incomplete) | E48w | 0 |

### Job 19 against Jobs 13–18

| File A | File B | Shared exact FENs |
|---|---|---:|
| K8 | Job 13 E2 | 0 |
| K8 | Job 13 E3k | 0 |
| K8 | Job 13 E6 | 0 |
| K8 | Job 14 E3k2 | 0 |
| K8 | Job 14 E6b | 0 |
| K8 | Job 14 E6k | 0 |
| K8 | Job 14 E12k | 0 |
| K8 | Job 15 E6k2 | 0 |
| K8 | Job 15 E12k2 | 0 |
| K8 | Job 15 D12v3 | 0 |
| K8 | Job 15 E6m | 0 |
| K8 | Job 15 E6t | 0 |
| K8 | Job 16 X400 | 0 |
| K8 | Job 16 X100 | 0 |
| K8 | Job 16 X50 | 0 |
| K8 | Job 16 D12v3b | 0 |
| K8 | Job 16 E24k | 0 |
| K8 | Job 16 X400t | 0 |
| K8 | Job 16 E12t | 0 |
| K8 | Job 17 X400r | 0 |
| K8 | Job 17 E24kr | 0 |
| K8 | Job 17 X400m3 | 0 |
| K8 | Job 17 X100m3 | 0 |
| K8 | Job 17 E48k | 0 |
| K8 | Job 17 X400w | 0 |
| K8 | Job 18 E48kr | 0 |
| K8 | Job 18 D48v24 | 0 |
| K8 | Job 18 E64k | 0 |
| K8 | Job 18 X400k48 | 0 |
| K8 | Job 18 X100k48 | 0 |
| K8 | Job 18 E48t | 0 |
| K8 | Job 18 E24t | 0 |
| C8 | Job 13 E2 | 0 |
| C8 | Job 13 E3k | 0 |
| C8 | Job 13 E6 | 0 |
| C8 | Job 14 E3k2 | 0 |
| C8 | Job 14 E6b | 0 |
| C8 | Job 14 E6k | 0 |
| C8 | Job 14 E12k | 0 |
| C8 | Job 15 E6k2 | 0 |
| C8 | Job 15 E12k2 | 0 |
| C8 | Job 15 D12v3 | 0 |
| C8 | Job 15 E6m | 0 |
| C8 | Job 15 E6t | 0 |
| C8 | Job 16 X400 | 0 |
| C8 | Job 16 X100 | 0 |
| C8 | Job 16 X50 | 0 |
| C8 | Job 16 D12v3b | 0 |
| C8 | Job 16 E24k | 0 |
| C8 | Job 16 X400t | 0 |
| C8 | Job 16 E12t | 0 |
| C8 | Job 17 X400r | 0 |
| C8 | Job 17 E24kr | 0 |
| C8 | Job 17 X400m3 | 0 |
| C8 | Job 17 X100m3 | 0 |
| C8 | Job 17 E48k | 0 |
| C8 | Job 17 X400w | 0 |
| C8 | Job 18 E48kr | 0 |
| C8 | Job 18 D48v24 | 0 |
| C8 | Job 18 E64k | 0 |
| C8 | Job 18 X400k48 | 0 |
| C8 | Job 18 X100k48 | 0 |
| C8 | Job 18 E48t | 0 |
| C8 | Job 18 E24t | 0 |
| E64kr | Job 13 E2 | 1 |
| E64kr | Job 13 E3k | 0 |
| E64kr | Job 13 E6 | 0 |
| E64kr | Job 14 E3k2 | 3 |
| E64kr | Job 14 E6b | 0 |
| E64kr | Job 14 E6k | 0 |
| E64kr | Job 14 E12k | 1 |
| E64kr | Job 15 E6k2 | 1 |
| E64kr | Job 15 E12k2 | 1 |
| E64kr | Job 15 D12v3 | 1 |
| E64kr | Job 15 E6m | 0 |
| E64kr | Job 15 E6t | 0 |
| E64kr | Job 16 X400 | 0 |
| E64kr | Job 16 X100 | 1 |
| E64kr | Job 16 X50 | 0 |
| E64kr | Job 16 D12v3b | 0 |
| E64kr | Job 16 E24k | 2 |
| E64kr | Job 16 X400t | 0 |
| E64kr | Job 16 E12t | 0 |
| E64kr | Job 17 X400r | 0 |
| E64kr | Job 17 E24kr | 1 |
| E64kr | Job 17 X400m3 | 1 |
| E64kr | Job 17 X100m3 | 1 |
| E64kr | Job 17 E48k | 0 |
| E64kr | Job 17 X400w | 0 |
| E64kr | Job 18 E48kr | 1 |
| E64kr | Job 18 D48v24 | 0 |
| E64kr | Job 18 E64k | 0 |
| E64kr | Job 18 X400k48 | 0 |
| E64kr | Job 18 X100k48 | 0 |
| E64kr | Job 18 E48t | 0 |
| E64kr | Job 18 E24t | 1 |
| E48tr | Job 13 E2 | 0 |
| E48tr | Job 13 E3k | 0 |
| E48tr | Job 13 E6 | 2 |
| E48tr | Job 14 E3k2 | 0 |
| E48tr | Job 14 E6b | 0 |
| E48tr | Job 14 E6k | 0 |
| E48tr | Job 14 E12k | 0 |
| E48tr | Job 15 E6k2 | 1 |
| E48tr | Job 15 E12k2 | 0 |
| E48tr | Job 15 D12v3 | 0 |
| E48tr | Job 15 E6m | 0 |
| E48tr | Job 15 E6t | 0 |
| E48tr | Job 16 X400 | 0 |
| E48tr | Job 16 X100 | 0 |
| E48tr | Job 16 X50 | 0 |
| E48tr | Job 16 D12v3b | 1 |
| E48tr | Job 16 E24k | 2 |
| E48tr | Job 16 X400t | 0 |
| E48tr | Job 16 E12t | 0 |
| E48tr | Job 17 X400r | 0 |
| E48tr | Job 17 E24kr | 0 |
| E48tr | Job 17 X400m3 | 0 |
| E48tr | Job 17 X100m3 | 0 |
| E48tr | Job 17 E48k | 0 |
| E48tr | Job 17 X400w | 0 |
| E48tr | Job 18 E48kr | 0 |
| E48tr | Job 18 D48v24 | 0 |
| E48tr | Job 18 E64k | 0 |
| E48tr | Job 18 X400k48 | 0 |
| E48tr | Job 18 X100k48 | 2 |
| E48tr | Job 18 E48t | 0 |
| E48tr | Job 18 E24t | 1 |
| E64t (incomplete) | Job 13 E2 | 1 |
| E64t (incomplete) | Job 13 E3k | 0 |
| E64t (incomplete) | Job 13 E6 | 0 |
| E64t (incomplete) | Job 14 E3k2 | 1 |
| E64t (incomplete) | Job 14 E6b | 0 |
| E64t (incomplete) | Job 14 E6k | 0 |
| E64t (incomplete) | Job 14 E12k | 1 |
| E64t (incomplete) | Job 15 E6k2 | 0 |
| E64t (incomplete) | Job 15 E12k2 | 0 |
| E64t (incomplete) | Job 15 D12v3 | 0 |
| E64t (incomplete) | Job 15 E6m | 0 |
| E64t (incomplete) | Job 15 E6t | 0 |
| E64t (incomplete) | Job 16 X400 | 0 |
| E64t (incomplete) | Job 16 X100 | 0 |
| E64t (incomplete) | Job 16 X50 | 1 |
| E64t (incomplete) | Job 16 D12v3b | 0 |
| E64t (incomplete) | Job 16 E24k | 0 |
| E64t (incomplete) | Job 16 X400t | 0 |
| E64t (incomplete) | Job 16 E12t | 0 |
| E64t (incomplete) | Job 17 X400r | 0 |
| E64t (incomplete) | Job 17 E24kr | 1 |
| E64t (incomplete) | Job 17 X400m3 | 0 |
| E64t (incomplete) | Job 17 X100m3 | 0 |
| E64t (incomplete) | Job 17 E48k | 0 |
| E64t (incomplete) | Job 17 X400w | 1 |
| E64t (incomplete) | Job 18 E48kr | 2 |
| E64t (incomplete) | Job 18 D48v24 | 0 |
| E64t (incomplete) | Job 18 E64k | 0 |
| E64t (incomplete) | Job 18 X400k48 | 0 |
| E64t (incomplete) | Job 18 X100k48 | 1 |
| E64t (incomplete) | Job 18 E48t | 0 |
| E64t (incomplete) | Job 18 E24t | 0 |
| E48w | Job 13 E2 | 0 |
| E48w | Job 13 E3k | 0 |
| E48w | Job 13 E6 | 0 |
| E48w | Job 14 E3k2 | 1 |
| E48w | Job 14 E6b | 0 |
| E48w | Job 14 E6k | 0 |
| E48w | Job 14 E12k | 0 |
| E48w | Job 15 E6k2 | 0 |
| E48w | Job 15 E12k2 | 1 |
| E48w | Job 15 D12v3 | 0 |
| E48w | Job 15 E6m | 2 |
| E48w | Job 15 E6t | 0 |
| E48w | Job 16 X400 | 0 |
| E48w | Job 16 X100 | 0 |
| E48w | Job 16 X50 | 0 |
| E48w | Job 16 D12v3b | 2 |
| E48w | Job 16 E24k | 1 |
| E48w | Job 16 X400t | 1 |
| E48w | Job 16 E12t | 1 |
| E48w | Job 17 X400r | 0 |
| E48w | Job 17 E24kr | 1 |
| E48w | Job 17 X400m3 | 0 |
| E48w | Job 17 X100m3 | 0 |
| E48w | Job 17 E48k | 0 |
| E48w | Job 17 X400w | 1 |
| E48w | Job 18 E48kr | 2 |
| E48w | Job 18 D48v24 | 1 |
| E48w | Job 18 E64k | 0 |
| E48w | Job 18 X400k48 | 0 |
| E48w | Job 18 X100k48 | 0 |
| E48w | Job 18 E48t | 1 |
| E48w | Job 18 E24t | 0 |

## Facts

- K8, C8, E64kr, E48tr and E48w finished their scheduled games. At the 12:37:26Z cutoff, the launcher sent SIGINT to E64t. Fastchess stopped at 12:37:27Z without escalation. E64t is incomplete and retained 1,888 of 2,000 scheduled games in 944 complete pairs. Across all six files, the audit found 8,188 scored games, zero unresolved games, zero unpaired games and zero abnormal terminations. [Independent audit](sol/job19/independent-Job19.txt) · [Cutoff receipt](sol/job19/raw/E64t.meta)
- At 2,000 nodes, Mult 64 versus zero met the replication rule. The fresh 2,000-game seed gave +33.11 Elo [+20.69, +45.53], and the 4,000-game pool gave +33.37 [+24.79, +41.94]. At 10,000 nodes, Mult 48 versus zero also met the rule. The fresh 2,000-game seed gave +3.13 [−7.88, +14.14] and the 4,000-game pool gave +9.12 [+1.60, +16.65]. Both pairs of seeds had zero shared FENs. [Mult 64 fresh PGN](sol/job19/raw/E64kr.pgn) · [Mult 48 fresh PGN](sol/job19/raw/E48tr.pgn)
- At 10,000 nodes, incomplete E64t scored +12.89 Elo [+2.09, +23.69] in 1,888 games. Its interval qualifies it for a fresh seed under the exploratory rule. At 20,000 nodes, Mult 48 versus zero gave +5.04 [−5.20, +15.28] in a complete, 2,000-game match. [Incomplete E64t PGN](sol/job19/raw/E64t.pgn) · [E48w PGN](sol/job19/raw/E48w.pgn)
- Every measured match and both replication pools recorded zero identical entire move lists in their compared pairs. Of 207 opening-file comparisons, 41 shared at least one exact FEN and the maximum was three. Five of six forecasts survived the declared grading rule, including the one graded on the incomplete E64t sample. The fresh E48tr magnitude missed. [Full readback](sol/job19/readback.txt)

## Suspicions

The Mult-48 gains may decay as the budget rises in this build. The two-seed estimate at 10,000 nodes is smaller than at 2,000 nodes, and the single 20,000-node estimate is smaller again with an interval spanning zero. The incomplete Mult-64 comparison at 10,000 nodes can justify a fresh seed against zero. Its result and the Mult-48 result used different openings and zero baselines.

## What I did not do

Every game ran in Codex Cloud on the unchanged counting executable. Engine source, weights, training and the owner's tune were outside this job.

## What I am not sure about

These estimates apply to this Forge build, net, preset and book sample. Each exploratory comparison used one seed. The two 10,000-node multipliers use independent zero baselines. Their head-to-head strength at that budget remains unmeasured.

## Reproduction

Both sides used Forge PC r15 at `6b98f2170a3210e71beed04bbd2553972c253ed7` with the Job 2 counters and Job 4 buttons, GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and `FORGE_MATE_ALPHA_GUARD=1`. Options were PC20, one thread, Hash 16 MiB, one PV, OwnBook false and embedded AL1 s198 with weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. Both engines explicitly set their assigned Mult in every match, including zero in C8 and all measured baselines. Max used the default 200 throughout. [Forge build](REPORT_sol_job4.md) · [Raw PGNs, stdout and exact UCI inputs](sol/job19/raw)

Fastchess played each sampled FEN in both colors at each side's stated fixed node budget with a 300-move ceiling and its built-in chess termination rules. Each measured match logged the rating after every completed pair. The UTC play cutoff was computed as claim time plus 50 minutes. [Build receipt](sol/job19/build.txt) · [UTC and slot evidence](sol/job19/stamps.txt)

From `forge-combo29/sol/job19`, with Python 3 and python-chess 1.11.2, these commands regenerate both gates, Table O, both replication decisions and the opening table.

```sh
python3 analyze_matches19.py gates raw
python3 analyze_matches19.py table raw --job13-raw ../job13/raw --job14-raw ../job14/raw \
  --job15-raw ../job15/raw --job16-raw ../job16/raw --job17-raw ../job17/raw --job18-raw ../job18/raw --prediction prediction.txt
```

[Table and opening readback](sol/job19/readback.txt) · [Precommit tree readback](sol/job19/precommit-readback.txt)

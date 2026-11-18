# Sol — Job 18 dose-48 replication, dose 64 and clipping

## Step 0 and gates

1. **The counting executable passed all eight fresh-process pins.** Defaults gave 312866, 862329 and 3024920 bench nodes and 4865609 perft 5 nodes. S14 gave 242796 and 656517. PC20 gave 278024 and 587276. Counting SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. Fastchess printed `fastchess alpha 1.8.3 20261107-d7b47e8`, and the official EPD's SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. The UCI lines were `option name EvalSwingMult type spin default 0 min 0 max 64` and `option name EvalSwingMax type spin default 200 min 50 max 400`. [Step 0 stdout](sol/job18/step0-count.raw.txt) · [Build and book receipt](sol/job18/build.txt)
2. **K7 passed 50/50.** PC20 with explicit Mult 48 on both sides at 2,000 nodes gave identical full ordered moves and 1–1 in each reversed-color pair. Both UCI preflights reached `readyok` with zero refusals. A went 33–33–34 with pentanomial `[0, 0, 50, 0, 0]` in 100 games. [K7 PGN](sol/job18/raw/K7.pgn) · [K7 preflights](sol/job18/raw/K7.meta)
3. **C7 passed.** Plain PC20 at 10,000 versus 20,000 nodes gave A 21–119–60 and pentanomial `[32, 38, 26, 4, 0]` over 200 games. Elo was −186.25 with a 95% interval of [−225.06, −147.44], passing the −100 threshold and upper-bound gate. [C7 PGN](sol/job18/raw/C7.pgn) · [C7 output](sol/job18/raw/C7.out) · [Independent gates](sol/job18/independent-gates.txt)

The [prediction](sol/job18/prediction.txt) was the sole file in commit `d39f7df4cb646a277a3a5cc61b01a7e1e6bb3d5a` after both gates passed and before measured play. The concurrent slots used two workers each. Slot 1 ran E48kr, D48v24, E64k, X400k48 and X100k48 at 2,000 nodes. Slot 2 ran E48t and E24t at 10,000 nodes. [UTC stamps](sol/job18/stamps.txt)

## Prediction grades

The observed Elo must have the forecast sign and fall within a factor of 1.5 of its magnitude. A zero forecast requires zero. The replication forecast uses exact yes/no matching.

| Forecast | Guess | Observed | Grade | Evidence status |
|---|---:|---:|---|---|
| E48kr Elo | +30.00 | +29.25 | survives | complete |
| D48v24 Elo | +12.00 | +4.00 | KILLED | complete |
| E64k Elo | +34.00 | +33.63 | survives | complete |
| X400k48 Elo | +8.00 | -2.08 | KILLED (sign) | complete |
| X100k48 Elo | -10.00 | +2.95 | KILLED (sign) | complete |
| E48t Elo | +9.00 | +15.12 | KILLED | complete |
| E24t Elo | +6.00 | +9.56 | KILLED | complete |
| E48k REPLICATED | yes | yes | survives | complete: interval reconstructed from summed penta counts |

5 KILLED, 3 survive, 0 ungraded.

## Table N. EvalSwing paired games and identical move lists

W-L-D is from A's perspective. Intervals use the fastchess 95% pentanomial Elo ± halfwidth convention. Identical pairs share the complete ordered UCI move sequence.

| Match | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Reading |
|---|---|---:|---|---|---|---:|---|
| E48k | complete | 2000 | 806-574-620 | 63, 174, 378, 238, 147 | +40.48 [+28.53, +52.43] | 0/1000 | two-seed gain comparison |
| E48kr | complete | 2000 | 775-607-618 | 90, 186, 327, 260, 137 | +29.25 [+16.76, +41.74] | 0/1000 | two-seed gain comparison |
| E48k + E48kr pooled | complete: interval reconstructed from summed penta counts | 4000 | 1581-1181-1238 | 153, 360, 705, 498, 284 | +34.86 [+26.22, +43.50] | 0/2000 | two-seed gain comparison |
| D48v24 | complete | 2000 | 682-659-659 | 104, 212, 344, 237, 103 | +4.00 [-8.17, +16.17] | 0/1000 | exploratory, interval includes zero |
| E64k | complete | 2000 | 767-574-659 | 71, 172, 379, 249, 129 | +33.63 [+21.80, +45.46] | 0/1000 | exploratory, earns a fresh seed (above zero) |
| X400k48 | complete | 2000 | 642-654-704 | 61, 184, 515, 186, 54 | -2.08 [-11.89, +7.73] | 36/1000 | exploratory, interval includes zero |
| X100k48 | complete | 2000 | 670-653-677 | 90, 213, 386, 212, 99 | +2.95 [-8.75, +14.65] | 0/1000 | exploratory, interval includes zero |
| E48t | complete | 2000 | 601-514-885 | 45, 209, 427, 252, 67 | +15.12 [+4.88, +25.36] | 0/1000 | exploratory, earns a fresh seed (above zero) |
| E24t | complete | 2000 | 619-564-817 | 51, 227, 416, 228, 78 | +9.56 [-1.04, +20.16] | 0/1000 | exploratory, interval includes zero |

E48k (job 17 + E48kr) gets a verdict by the rule of file 15: REPLICATED when its fresh seed alone gives Elo above 0 AND the pool of its two seeds (pentanomial counts added) has a 95 % interval whose lower end is above 0. Every other cell is exploratory: no verdict, a row each; one whose 95 % interval lies wholly above or wholly below 0 earns a fresh seed in a later job before anything is said about it.
E48k REPLICATED yes. Fresh Elo +29.2500, pooled lower 95% bound +26.2156. Evidence complete: interval reconstructed from summed penta counts.

## Shared openings

Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct FEN strings.

E48k and E48kr distinct shared exact FENs = 0.

| File | Status | Complete pairs | Distinct exact FENs |
|---|---|---:|---:|
| K7 | complete | 50 | 50 |
| C7 | complete | 100 | 100 |
| E48kr | complete | 1000 | 1000 |
| D48v24 | complete | 1000 | 1000 |
| E64k | complete | 1000 | 1000 |
| X400k48 | complete | 1000 | 1000 |
| X100k48 | complete | 1000 | 1000 |
| E48t | complete | 1000 | 1000 |
| E24t | complete | 1000 | 1000 |
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

### Within Job 18

| File A | File B | Shared exact FENs |
|---|---|---:|
| K7 | C7 | 0 |
| K7 | E48kr | 0 |
| K7 | D48v24 | 0 |
| K7 | E64k | 0 |
| K7 | X400k48 | 0 |
| K7 | X100k48 | 0 |
| K7 | E48t | 0 |
| K7 | E24t | 0 |
| C7 | E48kr | 1 |
| C7 | D48v24 | 0 |
| C7 | E64k | 0 |
| C7 | X400k48 | 0 |
| C7 | X100k48 | 0 |
| C7 | E48t | 0 |
| C7 | E24t | 0 |
| E48kr | D48v24 | 1 |
| E48kr | E64k | 1 |
| E48kr | X400k48 | 0 |
| E48kr | X100k48 | 0 |
| E48kr | E48t | 0 |
| E48kr | E24t | 0 |
| D48v24 | E64k | 0 |
| D48v24 | X400k48 | 0 |
| D48v24 | X100k48 | 0 |
| D48v24 | E48t | 2 |
| D48v24 | E24t | 0 |
| E64k | X400k48 | 1 |
| E64k | X100k48 | 0 |
| E64k | E48t | 0 |
| E64k | E24t | 0 |
| X400k48 | X100k48 | 0 |
| X400k48 | E48t | 0 |
| X400k48 | E24t | 0 |
| X100k48 | E48t | 0 |
| X100k48 | E24t | 0 |
| E48t | E24t | 0 |

### Job 18 against Jobs 13–17

| File A | File B | Shared exact FENs |
|---|---|---:|
| K7 | Job 13 E2 | 0 |
| K7 | Job 13 E3k | 0 |
| K7 | Job 13 E6 | 0 |
| K7 | Job 14 E3k2 | 0 |
| K7 | Job 14 E6b | 0 |
| K7 | Job 14 E6k | 0 |
| K7 | Job 14 E12k | 0 |
| K7 | Job 15 E6k2 | 0 |
| K7 | Job 15 E12k2 | 0 |
| K7 | Job 15 D12v3 | 0 |
| K7 | Job 15 E6m | 0 |
| K7 | Job 15 E6t | 0 |
| K7 | Job 16 X400 | 0 |
| K7 | Job 16 X100 | 0 |
| K7 | Job 16 X50 | 0 |
| K7 | Job 16 D12v3b | 0 |
| K7 | Job 16 E24k | 0 |
| K7 | Job 16 X400t | 0 |
| K7 | Job 16 E12t | 0 |
| K7 | Job 17 X400r | 0 |
| K7 | Job 17 E24kr | 0 |
| K7 | Job 17 X400m3 | 0 |
| K7 | Job 17 X100m3 | 0 |
| K7 | Job 17 E48k | 0 |
| K7 | Job 17 X400w | 0 |
| C7 | Job 13 E2 | 0 |
| C7 | Job 13 E3k | 0 |
| C7 | Job 13 E6 | 0 |
| C7 | Job 14 E3k2 | 0 |
| C7 | Job 14 E6b | 0 |
| C7 | Job 14 E6k | 0 |
| C7 | Job 14 E12k | 0 |
| C7 | Job 15 E6k2 | 0 |
| C7 | Job 15 E12k2 | 0 |
| C7 | Job 15 D12v3 | 0 |
| C7 | Job 15 E6m | 0 |
| C7 | Job 15 E6t | 0 |
| C7 | Job 16 X400 | 0 |
| C7 | Job 16 X100 | 0 |
| C7 | Job 16 X50 | 0 |
| C7 | Job 16 D12v3b | 0 |
| C7 | Job 16 E24k | 0 |
| C7 | Job 16 X400t | 0 |
| C7 | Job 16 E12t | 1 |
| C7 | Job 17 X400r | 0 |
| C7 | Job 17 E24kr | 0 |
| C7 | Job 17 X400m3 | 0 |
| C7 | Job 17 X100m3 | 0 |
| C7 | Job 17 E48k | 0 |
| C7 | Job 17 X400w | 0 |
| E48kr | Job 13 E2 | 0 |
| E48kr | Job 13 E3k | 1 |
| E48kr | Job 13 E6 | 0 |
| E48kr | Job 14 E3k2 | 0 |
| E48kr | Job 14 E6b | 1 |
| E48kr | Job 14 E6k | 1 |
| E48kr | Job 14 E12k | 0 |
| E48kr | Job 15 E6k2 | 1 |
| E48kr | Job 15 E12k2 | 1 |
| E48kr | Job 15 D12v3 | 0 |
| E48kr | Job 15 E6m | 1 |
| E48kr | Job 15 E6t | 1 |
| E48kr | Job 16 X400 | 0 |
| E48kr | Job 16 X100 | 0 |
| E48kr | Job 16 X50 | 0 |
| E48kr | Job 16 D12v3b | 1 |
| E48kr | Job 16 E24k | 0 |
| E48kr | Job 16 X400t | 0 |
| E48kr | Job 16 E12t | 0 |
| E48kr | Job 17 X400r | 0 |
| E48kr | Job 17 E24kr | 1 |
| E48kr | Job 17 X400m3 | 0 |
| E48kr | Job 17 X100m3 | 1 |
| E48kr | Job 17 E48k | 0 |
| E48kr | Job 17 X400w | 1 |
| D48v24 | Job 13 E2 | 0 |
| D48v24 | Job 13 E3k | 0 |
| D48v24 | Job 13 E6 | 0 |
| D48v24 | Job 14 E3k2 | 0 |
| D48v24 | Job 14 E6b | 1 |
| D48v24 | Job 14 E6k | 0 |
| D48v24 | Job 14 E12k | 1 |
| D48v24 | Job 15 E6k2 | 0 |
| D48v24 | Job 15 E12k2 | 0 |
| D48v24 | Job 15 D12v3 | 0 |
| D48v24 | Job 15 E6m | 1 |
| D48v24 | Job 15 E6t | 0 |
| D48v24 | Job 16 X400 | 0 |
| D48v24 | Job 16 X100 | 0 |
| D48v24 | Job 16 X50 | 0 |
| D48v24 | Job 16 D12v3b | 1 |
| D48v24 | Job 16 E24k | 0 |
| D48v24 | Job 16 X400t | 0 |
| D48v24 | Job 16 E12t | 1 |
| D48v24 | Job 17 X400r | 0 |
| D48v24 | Job 17 E24kr | 0 |
| D48v24 | Job 17 X400m3 | 1 |
| D48v24 | Job 17 X100m3 | 0 |
| D48v24 | Job 17 E48k | 0 |
| D48v24 | Job 17 X400w | 0 |
| E64k | Job 13 E2 | 0 |
| E64k | Job 13 E3k | 0 |
| E64k | Job 13 E6 | 0 |
| E64k | Job 14 E3k2 | 0 |
| E64k | Job 14 E6b | 1 |
| E64k | Job 14 E6k | 0 |
| E64k | Job 14 E12k | 2 |
| E64k | Job 15 E6k2 | 0 |
| E64k | Job 15 E12k2 | 0 |
| E64k | Job 15 D12v3 | 0 |
| E64k | Job 15 E6m | 1 |
| E64k | Job 15 E6t | 0 |
| E64k | Job 16 X400 | 0 |
| E64k | Job 16 X100 | 0 |
| E64k | Job 16 X50 | 1 |
| E64k | Job 16 D12v3b | 0 |
| E64k | Job 16 E24k | 0 |
| E64k | Job 16 X400t | 0 |
| E64k | Job 16 E12t | 0 |
| E64k | Job 17 X400r | 1 |
| E64k | Job 17 E24kr | 0 |
| E64k | Job 17 X400m3 | 0 |
| E64k | Job 17 X100m3 | 0 |
| E64k | Job 17 E48k | 0 |
| E64k | Job 17 X400w | 1 |
| X400k48 | Job 13 E2 | 0 |
| X400k48 | Job 13 E3k | 0 |
| X400k48 | Job 13 E6 | 0 |
| X400k48 | Job 14 E3k2 | 0 |
| X400k48 | Job 14 E6b | 2 |
| X400k48 | Job 14 E6k | 0 |
| X400k48 | Job 14 E12k | 0 |
| X400k48 | Job 15 E6k2 | 0 |
| X400k48 | Job 15 E12k2 | 0 |
| X400k48 | Job 15 D12v3 | 0 |
| X400k48 | Job 15 E6m | 0 |
| X400k48 | Job 15 E6t | 1 |
| X400k48 | Job 16 X400 | 0 |
| X400k48 | Job 16 X100 | 0 |
| X400k48 | Job 16 X50 | 1 |
| X400k48 | Job 16 D12v3b | 1 |
| X400k48 | Job 16 E24k | 1 |
| X400k48 | Job 16 X400t | 2 |
| X400k48 | Job 16 E12t | 0 |
| X400k48 | Job 17 X400r | 0 |
| X400k48 | Job 17 E24kr | 0 |
| X400k48 | Job 17 X400m3 | 0 |
| X400k48 | Job 17 X100m3 | 0 |
| X400k48 | Job 17 E48k | 0 |
| X400k48 | Job 17 X400w | 0 |
| X100k48 | Job 13 E2 | 0 |
| X100k48 | Job 13 E3k | 0 |
| X100k48 | Job 13 E6 | 0 |
| X100k48 | Job 14 E3k2 | 0 |
| X100k48 | Job 14 E6b | 0 |
| X100k48 | Job 14 E6k | 0 |
| X100k48 | Job 14 E12k | 2 |
| X100k48 | Job 15 E6k2 | 0 |
| X100k48 | Job 15 E12k2 | 0 |
| X100k48 | Job 15 D12v3 | 0 |
| X100k48 | Job 15 E6m | 0 |
| X100k48 | Job 15 E6t | 0 |
| X100k48 | Job 16 X400 | 1 |
| X100k48 | Job 16 X100 | 0 |
| X100k48 | Job 16 X50 | 0 |
| X100k48 | Job 16 D12v3b | 0 |
| X100k48 | Job 16 E24k | 1 |
| X100k48 | Job 16 X400t | 1 |
| X100k48 | Job 16 E12t | 0 |
| X100k48 | Job 17 X400r | 1 |
| X100k48 | Job 17 E24kr | 1 |
| X100k48 | Job 17 X400m3 | 1 |
| X100k48 | Job 17 X100m3 | 1 |
| X100k48 | Job 17 E48k | 0 |
| X100k48 | Job 17 X400w | 1 |
| E48t | Job 13 E2 | 0 |
| E48t | Job 13 E3k | 0 |
| E48t | Job 13 E6 | 0 |
| E48t | Job 14 E3k2 | 1 |
| E48t | Job 14 E6b | 0 |
| E48t | Job 14 E6k | 0 |
| E48t | Job 14 E12k | 1 |
| E48t | Job 15 E6k2 | 0 |
| E48t | Job 15 E12k2 | 0 |
| E48t | Job 15 D12v3 | 1 |
| E48t | Job 15 E6m | 0 |
| E48t | Job 15 E6t | 1 |
| E48t | Job 16 X400 | 1 |
| E48t | Job 16 X100 | 1 |
| E48t | Job 16 X50 | 1 |
| E48t | Job 16 D12v3b | 0 |
| E48t | Job 16 E24k | 0 |
| E48t | Job 16 X400t | 0 |
| E48t | Job 16 E12t | 0 |
| E48t | Job 17 X400r | 0 |
| E48t | Job 17 E24kr | 1 |
| E48t | Job 17 X400m3 | 1 |
| E48t | Job 17 X100m3 | 0 |
| E48t | Job 17 E48k | 0 |
| E48t | Job 17 X400w | 0 |
| E24t | Job 13 E2 | 0 |
| E24t | Job 13 E3k | 0 |
| E24t | Job 13 E6 | 0 |
| E24t | Job 14 E3k2 | 2 |
| E24t | Job 14 E6b | 0 |
| E24t | Job 14 E6k | 0 |
| E24t | Job 14 E12k | 0 |
| E24t | Job 15 E6k2 | 0 |
| E24t | Job 15 E12k2 | 0 |
| E24t | Job 15 D12v3 | 0 |
| E24t | Job 15 E6m | 0 |
| E24t | Job 15 E6t | 0 |
| E24t | Job 16 X400 | 0 |
| E24t | Job 16 X100 | 0 |
| E24t | Job 16 X50 | 0 |
| E24t | Job 16 D12v3b | 2 |
| E24t | Job 16 E24k | 0 |
| E24t | Job 16 X400t | 0 |
| E24t | Job 16 E12t | 0 |
| E24t | Job 17 X400r | 0 |
| E24t | Job 17 E24kr | 0 |
| E24t | Job 17 X400m3 | 0 |
| E24t | Job 17 X100m3 | 0 |
| E24t | Job 17 E48k | 0 |
| E24t | Job 17 X400w | 0 |

## Facts

- All nine scheduled matches finished before the 11:43:23Z play cutoff. The last was E24t at 11:39:07Z. The 14,000 measured games plus 300 control games formed 7,150 complete reversed-color pairs. The independent recount found zero unresolved games, unpaired games, or abnormal terminations. [Independent audit](sol/job18/independent-Job18.txt)
- Dose 48 versus zero at 2,000 nodes replicated by the declared rule. The fresh seed scored +29.25 Elo [+16.76, +41.74], and the two-seed pool scored +34.86 [+26.22, +43.50] in 4,000 games. The seeds had no shared FENs. The direct 2,000-node dose-48-versus-dose-24 match scored +4.00 [−8.17, +16.17] in one 2,000-game seed. [Fresh PGN](sol/job18/raw/E48kr.pgn) · [Prior PGN](sol/job17/raw/E48k.pgn) · [Direct PGN](sol/job18/raw/D48v24.pgn)
- Two exploratory cells earned another seed. Dose 64 versus zero at 2,000 nodes scored +33.63 Elo [+21.80, +45.46]. Dose 48 versus zero at 10,000 nodes scored +15.12 [+4.88, +25.36]. Each used 2,000 games. Dose 24 versus zero at 10,000 nodes scored +9.56 [−1.04, +20.16] in 2,000 games. [Dose 64 PGN](sol/job18/raw/E64k.pgn) · [Dose 48 at 10,000 nodes](sol/job18/raw/E48t.pgn) · [Dose 24 at 10,000 nodes](sol/job18/raw/E24t.pgn)
- At Mult 48 and 2,000 nodes, clip 400 versus 200 had 36/1,000 identical move pairs and clip 100 versus 200 had 0/1,000. Both Elo intervals included zero. Table N records 55 nonzero opening intersections among 261 file comparisons and a maximum of two exact FENs in any pair. The surviving forecasts were the dose-48 fresh-seed magnitude, dose-64 magnitude and dose-48 replication. [Full readback](sol/job18/readback.txt)

## Suspicions

The larger multiplier may still help at 10,000 nodes even where the previous lower-dose intervals spanned zero. E48t used one seed. The dose-64 result supports a second seed against zero and leaves its head-to-head performance against dose 48 open.

## What I did not do

Every game ran in Codex Cloud on the unchanged counting executable. Engine source, weights, training and the owner's tune were outside this job.

## What I am not sure about

These estimates apply to this Forge build, net, preset and book sample. Every exploratory comparison used one seed. Identical ordered moves establish equality of the played sequences. The number of clip-limited updates and any differences in the internal search state remain unmeasured.

## Reproduction

Both sides used Forge PC r15 at `6b98f2170a3210e71beed04bbd2553972c253ed7` with the Job 2 counters and Job 4 buttons, GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and `FORGE_MATE_ALPHA_GUARD=1`. Options were PC20, one thread, Hash 16 MiB, one PV, OwnBook false and embedded AL1 s198 with weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. Both engines explicitly set Mult in the E, D and X arms. The E and D arms used the default Max 200. The X arms held Mult 48 and set their respective Max on both sides. [Forge build](REPORT_sol_job4.md) · [Raw PGNs, stdout and exact UCI inputs](sol/job18/raw)

Fastchess played each sampled FEN in both colors at each side's stated fixed node budget with a 300-move ceiling and its built-in chess termination rules. Each measured match logged the rating after every completed pair. The UTC play cutoff was computed as claim time plus 50 minutes. [Build receipt](sol/job18/build.txt) · [UTC and slot evidence](sol/job18/stamps.txt)

From `forge-combo29/sol/job18`, with Python 3 and python-chess 1.11.2, these commands regenerate both gates, Table N, the replication decision and the opening table.

```sh
python3 analyze_matches18.py gates raw
python3 analyze_matches18.py table raw --job13-raw ../job13/raw --job14-raw ../job14/raw \
  --job15-raw ../job15/raw --job16-raw ../job16/raw --job17-raw ../job17/raw --prediction prediction.txt
```

[Table and opening readback](sol/job18/readback.txt) · [Precommit tree readback](sol/job18/precommit-readback.txt)

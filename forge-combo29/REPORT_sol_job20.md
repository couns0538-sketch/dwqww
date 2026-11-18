# Sol — Job 20 FailHighBlend at three node budgets

## Step 0 and 0b

1. **Both executables matched every fresh-process pin.**

   | Preset | Probe | Job 4 counting | PCA |
   |---|---|---:|---:|
   | Defaults | bench 11 | 312866 | 312866 |
   | Defaults | bench 13 | 862329 | 862329 |
   | Defaults | bench 16 | 3024920 | 3024920 |
   | Defaults | go perft 5 | 4865609 | 4865609 |
   | S14 | bench 11 | 242796 | 242796 |
   | S14 | bench 13 | 656517 | 656517 |
   | PC20 | bench 11 | 278024 | 278024 |
   | PC20 | bench 13 | 587276 | 587276 |

   The counting binary was `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. PCA was `49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a`, with `id name Chess Engine Forge 6.4.24 candidate`. Fastchess printed `fastchess alpha 1.8.3 20261107-d7b47e8`. The official opening EPD SHA-256 was `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`. [Counting UCI](sol/job20/step0-count.raw.txt) · [PCA UCI](sol/job20/step0-pca.raw.txt) · [Build receipt](sol/job20/build.txt)

   Both UCI lists contained these options.

   ```text
   option name EvalSwingMult type spin default 0 min 0 max 64
   option name EvalSwingMax type spin default 200 min 50 max 400
   ```

   PCA also advertised these four options.

   ```text
   option name FailHighBlend type spin default 0 min 0 max 7
   option name RfpCorrMul type spin default 0 min 0 max 64
   option name RfpNoTtPv type spin default 0 min 0 max 1
   option name RfpTtGuard type spin default 0 min 0 max 1
   ```

   I copied the plain Job 2 PC r15 scratch tree and applied Kimi5's pinned patch at `5db05e095d5e81622eb0de13eb8a738a0ae1d22a`. The patch SHA-256 was `0bcb88c59fe3659f4ab71a4fededd453f4713e6dd4d86e6e0c45b557ba86b991`. `patch -p1 -F0` applied with zero offsets, fuzz or rejections and printed these two lines.

   ```text
   patching file src/search.cpp
   patching file include/forge/search.hpp
   ```

   The match preflight sent `setoption name FailHighBlend value 7` to the old Job 4 executable, received `info string unknown option FailHighBlend` and raised `Refused` before match launch. [Patch stdout](sol/job20/pca-patch.txt) · [Refusal trace](sol/job20/preflight-reject.txt) · [Kimi5 patch](https://github.com/couns0538-sketch/dwqww/blob/5db05e095d5e81622eb0de13eb8a738a0ae1d22a/forge-combo29/tests_kimi5_job25/A2A5.pc.patch.txt)

## Step 0c

2. **PCA reproduced both depth-12 sets.** In the ordered 200-position `O.epd` fixture, PC20, Threads 1 and Hash 16, FailHighBlend 0 recorded 8,315,168 nodes with first three 21,812, 26,844 and 35,173. FailHighBlend 7 recorded 7,913,480 with first three 18,623, 19,820 and 32,078. All 400 nodes and bestmove rows matched Kimi5's pinned reference. This replay sent FEN clocks `0 1` and preserved each original FEN in its row. The fixture SHA-256 was `ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8`. [Rows and metadata](sol/job20/depth12) · [Independent provenance and replay audit](sol/job20/independent-gate-provenance.txt)

## Match controls

3. **K9 passed 50/50.** PCA with PC20, explicit Mult 0 and FHB 7 on both sides at 2,000 nodes gave 100 games, 36–36–28, pentanomial `[0, 0, 50, 0, 0]`, and identical ordered moves and 1–1 in all 50 reversed-color pairs. Both preflights reached `readyok` without a refusal. [K9 PGN](sol/job20/raw/K9.pgn) · [K9 preflights](sol/job20/raw/K9.meta)
4. **C9 passed.** PCA with the same options at 10,000 versus 20,000 nodes gave A 21–108–71 and pentanomial `[25, 44, 25, 5, 1]` in 200 games. Elo was −161.92 with a 95% interval of [−199.06, −124.78]. [C9 PGN](sol/job20/raw/C9.pgn) · [Independent controls](sol/job20/independent-gates.txt)

The [prediction](sol/job20/prediction.txt) was the sole file in commit `cec5370f0db7c0d15e0935b97a39cb63a2dce887`, pushed before measured games and after both controls. With two workers per concurrent slot, slot 1 assigned F7k, F7t and E64tr in that order subject to the cutoff. Slot 2 assigned F7w. [UTC stamps](sol/job20/stamps.txt)

## Prediction grades

The observed Elo must have the forecast sign and fall within a factor of 1.5 of its magnitude. A zero forecast requires zero.

| Forecast | Guess | Observed | Grade | Evidence status |
|---|---:|---:|---|---|
| F7k Elo | +4.00 | -25.06 | KILLED (sign) | complete |
| F7t Elo | +6.00 | -7.12 | KILLED (sign) | complete |
| E64tr Elo | +9.00 | +17.99 | KILLED | incomplete (interrupted) |
| F7w Elo | +6.00 | -5.21 | KILLED (sign) | complete |

4 KILLED, 0 survive, 0 ungraded.

## Table P. FailHighBlend and EvalSwing paired games

All rows use PC20, embedded evaluation, Threads 1, Hash 16 and the pinned opening book. W-L-D is from A's perspective. Intervals use the fastchess 95% pentanomial Elo ± halfwidth convention. Identical pairs share the complete ordered UCI move sequence.

| Match | Build, nodes per move, options A/B | Status | Games | W-L-D | Pentanomial | Elo [95%] | Same moves / pairs | Reading |
|---|---|---|---:|---|---|---|---:|---|
| F7k | PCA, 2,000, FailHighBlend 7/0 and EvalSwingMult 0/0 | complete | 2000 | 647-791-562 | 138, 223, 372, 179, 88 | -25.06 [-37.34, -12.78] | 0/1000 | exploratory, earns a fresh seed (below zero) |
| F7t | PCA, 10,000, FailHighBlend 7/0 and EvalSwingMult 0/0 | complete | 2000 | 559-600-841 | 74, 245, 392, 226, 63 | -7.12 [-17.99, +3.75] | 0/1000 | exploratory, interval includes zero |
| E64tr | Job 4, 10,000, EvalSwingMult 64/0 | incomplete (interrupted) | 1604 | 495-412-697 | 35, 173, 322, 218, 54 | +17.99 [+6.42, +29.56] | 0/802 | two-seed gain comparison |
| F7w | PCA, 20,000, FailHighBlend 7/0 and EvalSwingMult 0/0 | complete | 2000 | 527-557-916 | 52, 260, 405, 232, 51 | -5.21 [-15.45, +5.03] | 0/1000 | exploratory, interval includes zero |

F7k, F7t and F7w are exploratory: no verdict, a row each; one whose 95 % interval lies wholly above or wholly below 0 earns a fresh seed in a later job before anything is said about it. E64tr, only if complete, gives E64t its verdict by the rule of file 15 (REPLICATED when the fresh seed alone gives Elo above 0 AND the pool of the two seeds, pentanomial counts added, has a 95 % interval whose lower end is above 0); a cut E64tr gives no verdict.
E64t verdict withheld. E64tr incomplete (interrupted).

## Shared openings

Each file contributes one exact FEN tag per complete color-reversed pair. Each intersection counts distinct FEN strings.

Job 19 E64t (incomplete) and E64tr (incomplete) distinct shared exact FENs = 0.

| File | Status | Complete pairs | Distinct exact FENs |
|---|---|---:|---:|
| K9 | complete | 50 | 50 |
| C9 | complete | 100 | 100 |
| F7k | complete | 1000 | 1000 |
| F7t | complete | 1000 | 1000 |
| E64tr | incomplete (interrupted) | 802 | 802 |
| F7w | complete | 1000 | 1000 |
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
| Job 18 E64k | saved | 1000 | 1000 |
| Job 18 X400k48 | saved | 1000 | 1000 |
| Job 18 X100k48 | saved | 1000 | 1000 |
| Job 18 E48t | saved | 1000 | 1000 |
| Job 18 E24t | saved | 1000 | 1000 |
| Job 19 E64kr | saved | 1000 | 1000 |
| Job 19 E48tr | saved | 1000 | 1000 |
| Job 19 E64t | incomplete (interrupted) | 944 | 944 |
| Job 19 E48w | saved | 1000 | 1000 |

### Within Job 20

| File A | File B | Shared exact FENs |
|---|---|---:|
| K9 | C9 | 0 |
| K9 | F7k | 0 |
| K9 | F7t | 0 |
| K9 | E64tr (incomplete) | 0 |
| K9 | F7w | 0 |
| C9 | F7k | 0 |
| C9 | F7t | 0 |
| C9 | E64tr (incomplete) | 0 |
| C9 | F7w | 0 |
| F7k | F7t | 0 |
| F7k | E64tr (incomplete) | 0 |
| F7k | F7w | 0 |
| F7t | E64tr (incomplete) | 0 |
| F7t | F7w | 0 |
| E64tr (incomplete) | F7w | 0 |

### Job 20 against Jobs 13–19

| File A | File B | Shared exact FENs |
|---|---|---:|
| K9 | Job 13 E2 | 0 |
| K9 | Job 13 E3k | 0 |
| K9 | Job 13 E6 | 0 |
| K9 | Job 14 E3k2 | 0 |
| K9 | Job 14 E6b | 0 |
| K9 | Job 14 E6k | 0 |
| K9 | Job 14 E12k | 0 |
| K9 | Job 15 E6k2 | 0 |
| K9 | Job 15 E12k2 | 0 |
| K9 | Job 15 D12v3 | 0 |
| K9 | Job 15 E6m | 0 |
| K9 | Job 15 E6t | 0 |
| K9 | Job 16 X400 | 0 |
| K9 | Job 16 X100 | 0 |
| K9 | Job 16 X50 | 0 |
| K9 | Job 16 D12v3b | 0 |
| K9 | Job 16 E24k | 0 |
| K9 | Job 16 X400t | 0 |
| K9 | Job 16 E12t | 0 |
| K9 | Job 17 X400r | 0 |
| K9 | Job 17 E24kr | 0 |
| K9 | Job 17 X400m3 | 0 |
| K9 | Job 17 X100m3 | 0 |
| K9 | Job 17 E48k | 0 |
| K9 | Job 17 X400w | 0 |
| K9 | Job 18 E48kr | 0 |
| K9 | Job 18 D48v24 | 0 |
| K9 | Job 18 E64k | 0 |
| K9 | Job 18 X400k48 | 0 |
| K9 | Job 18 X100k48 | 0 |
| K9 | Job 18 E48t | 0 |
| K9 | Job 18 E24t | 0 |
| K9 | Job 19 E64kr | 0 |
| K9 | Job 19 E48tr | 0 |
| K9 | Job 19 E64t (incomplete) | 0 |
| K9 | Job 19 E48w | 0 |
| C9 | Job 13 E2 | 0 |
| C9 | Job 13 E3k | 1 |
| C9 | Job 13 E6 | 0 |
| C9 | Job 14 E3k2 | 0 |
| C9 | Job 14 E6b | 0 |
| C9 | Job 14 E6k | 0 |
| C9 | Job 14 E12k | 0 |
| C9 | Job 15 E6k2 | 0 |
| C9 | Job 15 E12k2 | 0 |
| C9 | Job 15 D12v3 | 0 |
| C9 | Job 15 E6m | 0 |
| C9 | Job 15 E6t | 0 |
| C9 | Job 16 X400 | 0 |
| C9 | Job 16 X100 | 0 |
| C9 | Job 16 X50 | 0 |
| C9 | Job 16 D12v3b | 0 |
| C9 | Job 16 E24k | 0 |
| C9 | Job 16 X400t | 0 |
| C9 | Job 16 E12t | 0 |
| C9 | Job 17 X400r | 0 |
| C9 | Job 17 E24kr | 0 |
| C9 | Job 17 X400m3 | 0 |
| C9 | Job 17 X100m3 | 0 |
| C9 | Job 17 E48k | 0 |
| C9 | Job 17 X400w | 0 |
| C9 | Job 18 E48kr | 0 |
| C9 | Job 18 D48v24 | 0 |
| C9 | Job 18 E64k | 0 |
| C9 | Job 18 X400k48 | 0 |
| C9 | Job 18 X100k48 | 0 |
| C9 | Job 18 E48t | 0 |
| C9 | Job 18 E24t | 0 |
| C9 | Job 19 E64kr | 0 |
| C9 | Job 19 E48tr | 0 |
| C9 | Job 19 E64t (incomplete) | 0 |
| C9 | Job 19 E48w | 0 |
| F7k | Job 13 E2 | 0 |
| F7k | Job 13 E3k | 2 |
| F7k | Job 13 E6 | 0 |
| F7k | Job 14 E3k2 | 1 |
| F7k | Job 14 E6b | 0 |
| F7k | Job 14 E6k | 0 |
| F7k | Job 14 E12k | 0 |
| F7k | Job 15 E6k2 | 0 |
| F7k | Job 15 E12k2 | 1 |
| F7k | Job 15 D12v3 | 0 |
| F7k | Job 15 E6m | 1 |
| F7k | Job 15 E6t | 1 |
| F7k | Job 16 X400 | 0 |
| F7k | Job 16 X100 | 0 |
| F7k | Job 16 X50 | 1 |
| F7k | Job 16 D12v3b | 0 |
| F7k | Job 16 E24k | 0 |
| F7k | Job 16 X400t | 1 |
| F7k | Job 16 E12t | 0 |
| F7k | Job 17 X400r | 0 |
| F7k | Job 17 E24kr | 0 |
| F7k | Job 17 X400m3 | 0 |
| F7k | Job 17 X100m3 | 2 |
| F7k | Job 17 E48k | 0 |
| F7k | Job 17 X400w | 0 |
| F7k | Job 18 E48kr | 0 |
| F7k | Job 18 D48v24 | 0 |
| F7k | Job 18 E64k | 0 |
| F7k | Job 18 X400k48 | 0 |
| F7k | Job 18 X100k48 | 0 |
| F7k | Job 18 E48t | 0 |
| F7k | Job 18 E24t | 0 |
| F7k | Job 19 E64kr | 0 |
| F7k | Job 19 E48tr | 0 |
| F7k | Job 19 E64t (incomplete) | 0 |
| F7k | Job 19 E48w | 2 |
| F7t | Job 13 E2 | 0 |
| F7t | Job 13 E3k | 0 |
| F7t | Job 13 E6 | 0 |
| F7t | Job 14 E3k2 | 0 |
| F7t | Job 14 E6b | 2 |
| F7t | Job 14 E6k | 1 |
| F7t | Job 14 E12k | 1 |
| F7t | Job 15 E6k2 | 0 |
| F7t | Job 15 E12k2 | 0 |
| F7t | Job 15 D12v3 | 1 |
| F7t | Job 15 E6m | 0 |
| F7t | Job 15 E6t | 0 |
| F7t | Job 16 X400 | 0 |
| F7t | Job 16 X100 | 0 |
| F7t | Job 16 X50 | 1 |
| F7t | Job 16 D12v3b | 2 |
| F7t | Job 16 E24k | 0 |
| F7t | Job 16 X400t | 0 |
| F7t | Job 16 E12t | 1 |
| F7t | Job 17 X400r | 1 |
| F7t | Job 17 E24kr | 0 |
| F7t | Job 17 X400m3 | 1 |
| F7t | Job 17 X100m3 | 0 |
| F7t | Job 17 E48k | 1 |
| F7t | Job 17 X400w | 0 |
| F7t | Job 18 E48kr | 2 |
| F7t | Job 18 D48v24 | 0 |
| F7t | Job 18 E64k | 0 |
| F7t | Job 18 X400k48 | 2 |
| F7t | Job 18 X100k48 | 0 |
| F7t | Job 18 E48t | 0 |
| F7t | Job 18 E24t | 0 |
| F7t | Job 19 E64kr | 0 |
| F7t | Job 19 E48tr | 0 |
| F7t | Job 19 E64t (incomplete) | 0 |
| F7t | Job 19 E48w | 1 |
| E64tr (incomplete) | Job 13 E2 | 1 |
| E64tr (incomplete) | Job 13 E3k | 0 |
| E64tr (incomplete) | Job 13 E6 | 0 |
| E64tr (incomplete) | Job 14 E3k2 | 0 |
| E64tr (incomplete) | Job 14 E6b | 0 |
| E64tr (incomplete) | Job 14 E6k | 0 |
| E64tr (incomplete) | Job 14 E12k | 0 |
| E64tr (incomplete) | Job 15 E6k2 | 0 |
| E64tr (incomplete) | Job 15 E12k2 | 0 |
| E64tr (incomplete) | Job 15 D12v3 | 0 |
| E64tr (incomplete) | Job 15 E6m | 0 |
| E64tr (incomplete) | Job 15 E6t | 0 |
| E64tr (incomplete) | Job 16 X400 | 0 |
| E64tr (incomplete) | Job 16 X100 | 0 |
| E64tr (incomplete) | Job 16 X50 | 0 |
| E64tr (incomplete) | Job 16 D12v3b | 0 |
| E64tr (incomplete) | Job 16 E24k | 0 |
| E64tr (incomplete) | Job 16 X400t | 0 |
| E64tr (incomplete) | Job 16 E12t | 2 |
| E64tr (incomplete) | Job 17 X400r | 2 |
| E64tr (incomplete) | Job 17 E24kr | 0 |
| E64tr (incomplete) | Job 17 X400m3 | 0 |
| E64tr (incomplete) | Job 17 X100m3 | 1 |
| E64tr (incomplete) | Job 17 E48k | 0 |
| E64tr (incomplete) | Job 17 X400w | 0 |
| E64tr (incomplete) | Job 18 E48kr | 0 |
| E64tr (incomplete) | Job 18 D48v24 | 0 |
| E64tr (incomplete) | Job 18 E64k | 1 |
| E64tr (incomplete) | Job 18 X400k48 | 0 |
| E64tr (incomplete) | Job 18 X100k48 | 0 |
| E64tr (incomplete) | Job 18 E48t | 0 |
| E64tr (incomplete) | Job 18 E24t | 0 |
| E64tr (incomplete) | Job 19 E64kr | 0 |
| E64tr (incomplete) | Job 19 E48tr | 0 |
| E64tr (incomplete) | Job 19 E64t (incomplete) | 0 |
| E64tr (incomplete) | Job 19 E48w | 0 |
| F7w | Job 13 E2 | 0 |
| F7w | Job 13 E3k | 1 |
| F7w | Job 13 E6 | 0 |
| F7w | Job 14 E3k2 | 0 |
| F7w | Job 14 E6b | 0 |
| F7w | Job 14 E6k | 0 |
| F7w | Job 14 E12k | 2 |
| F7w | Job 15 E6k2 | 1 |
| F7w | Job 15 E12k2 | 0 |
| F7w | Job 15 D12v3 | 0 |
| F7w | Job 15 E6m | 1 |
| F7w | Job 15 E6t | 0 |
| F7w | Job 16 X400 | 1 |
| F7w | Job 16 X100 | 0 |
| F7w | Job 16 X50 | 0 |
| F7w | Job 16 D12v3b | 0 |
| F7w | Job 16 E24k | 2 |
| F7w | Job 16 X400t | 0 |
| F7w | Job 16 E12t | 0 |
| F7w | Job 17 X400r | 0 |
| F7w | Job 17 E24kr | 0 |
| F7w | Job 17 X400m3 | 0 |
| F7w | Job 17 X100m3 | 2 |
| F7w | Job 17 E48k | 2 |
| F7w | Job 17 X400w | 0 |
| F7w | Job 18 E48kr | 0 |
| F7w | Job 18 D48v24 | 0 |
| F7w | Job 18 E64k | 1 |
| F7w | Job 18 X400k48 | 1 |
| F7w | Job 18 X100k48 | 0 |
| F7w | Job 18 E48t | 2 |
| F7w | Job 18 E24t | 0 |
| F7w | Job 19 E64kr | 0 |
| F7w | Job 19 E48tr | 0 |
| F7w | Job 19 E64t (incomplete) | 0 |
| F7w | Job 19 E48w | 0 |

## Facts

- The three PCA strength matches each finished 2,000 games with complete reversed-color pairs. FailHighBlend 7 versus 0 gave −25.06 Elo [−37.34, −12.78] at 2,000 nodes, −7.12 [−17.99, +3.75] at 10,000 nodes and −5.21 [−15.45, +5.03] at 20,000 nodes. Only the 2,000-node interval excluded zero and earns a fresh seed under the declared rule. [2,000-node PGN](sol/job20/raw/F7k.pgn) · [10,000-node PGN](sol/job20/raw/F7t.pgn) · [20,000-node PGN](sol/job20/raw/F7w.pgn)
- On the Job 4 counting build at 10,000 nodes, incomplete E64tr gave +17.99 Elo [+6.42, +29.56] for EvalSwingMult 64 versus zero over 1,604 games. The cutoff sent SIGINT at 13:37:47Z and Fastchess closed one second later without escalation, leaving 802 complete pairs and no unpaired or unresolved games. The incomplete fresh match leaves E64t without a pool or verdict under the declared rule. [Incomplete E64tr PGN](sol/job20/raw/E64tr.pgn) · [Cutoff receipt](sol/job20/raw/E64tr.meta)
- All four measured arms had zero identical ordered move lists in reversed-color pairs. The opening check covered 231 file pairs with 39 nonzero intersections, each at most two exact FENs. New files had no overlap with one another. The original E64t and the incomplete E64tr shared no exact FENs. All four predictions missed by the declared grading rule. [Independent final audit](sol/job20/independent-Job20.txt)

## Suspicions

The fixed-depth node savings and the low-budget match point in different directions. The 2,000-node loss merits the fresh seed specified in the handoff before interpreting it as repeatable. Both deeper intervals leave room for a gain or loss.

## What I did not do

The PCA patch lived in a separate scratch copy. Engine and weights source in the repository, the owner's PC and its running tune, and the training loop were outside this job.

## What I am not sure about

The results apply to the stated engine, net, preset and opening sample. A fixed-depth node reduction can reflect changes in what the search examines. The strength comparison at each node budget uses one opening seed. Results on the owner's build and net would require a separate test.

## Reproduction

Both executables trace to Forge PC r15, base commit `6b98f2170a3210e71beed04bbd2553972c253ed7` plus PC patch SHA-256 `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`. PCA adds Kimi5's A2A5 patch to that plain PC tree. The original counting executable adds the Job 2 counters and Job 4 buttons to PC r15. Both used GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4, `FORGE_MATE_ALPHA_GUARD=1` and embedded AL1 s198 with weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. [Forge build](REPORT_sol_job4.md) · [PCA compiler and inputs](sol/job20/build.txt)

Fastchess gave both engines PC20, one thread, Hash 16 MiB, one PV and OwnBook false with the options in each sidecar. The PCA strength comparisons held EvalSwingMult at zero and set FailHighBlend 7 versus 0. E64tr used the Job 4 executable with EvalSwingMult 64 versus 0. All matches used default EvalSwingMax 200. Fastchess played each sampled opening in both colors and used the 300-move ceiling. [Match settings and output](sol/job20/raw)

From `forge-combo29/sol/job20`, with Python 3 and python-chess 1.11.2, these commands regenerate the controls and Table P.

```sh
python3 analyze_matches20.py gates raw --pca-sha256 pca.sha256
python3 analyze_matches20.py table raw --pca-sha256 pca.sha256 \
  --job13-raw ../job13/raw --job14-raw ../job14/raw --job15-raw ../job15/raw \
  --job16-raw ../job16/raw --job17-raw ../job17/raw --job18-raw ../job18/raw \
  --job19-raw ../job19/raw --prediction prediction.txt
```

[Table and opening readback](sol/job20/readback.txt) · [Precommit tree readback](sol/job20/precommit-readback.txt)

# R4-03 screen: LmrDeeperShallower

Screening only. This is not a strength claim.

The owner's earlier stop was +2 ± 13 in 1200 games. That stop is prior context. This run is a new on-versus-off sample of the existing default-off option and does not by itself establish a strength change.

State: `running`.
Screen start (UTC): 2026-11-14T15:41:48Z.
Screen deadline (UTC): 2026-11-14T21:41:48Z (6 hours from screen start, or 9 chunks, whichever comes first).
Note: pushed after chunk 1001

## What was compared

Same binary. Engine 1 is `LmrDeeperShallower` with `option.LmrDeeperShallower=true`. Engine 2 is `default` with `option.LmrDeeperShallower=false`. No engine source was changed. W-L-D is from the option-on engine.

## Build

- Source commit: `e04556ddc3a430b2e751159b0d46111ef56c8b89`
- Implementation commit of `LmrDeeperShallower`: `b68d49fedcc8e705484d06fb02cf0a417734839f`
- CPU: Intel(R) Xeon(R) Processor
- AVX-512F present: avx512f. BMI2 present: bmi2.
- Effective CPUs (`nproc`): 4. Concurrency: 3 (effective CPUs minus 1).
- Owner build (AVX-512F and BMI2 are present), not the portable build.
- Compiler: g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
- CMake: `cmake -S forge-combo29 -B /tmp/forge-r4-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++` then `cmake --build /tmp/forge-r4-build -j4`.
- `FORGE_PORTABLE` left OFF. `FORGE_MARCH=x86-64-v4`. `FORGE_SPD_SLIDER_PEXT=1`. `FORGE_SPD_NNUE_ZMM=1`.
- Compile flags: `-O3 -DNDEBUG -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`
- Binary: `/tmp/forge-r4-build/forge`
- Binary sha256: `4a624cf990c057c9a5d7847916b2d537a38ab6b95be4339dbec30a187f7ec984`
- Book: `/tmp/r4tools/UHO_Lichess_4852_v1.epd` (2632036 lines)
- Book sha256: `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`
- Book zip sha256: `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07` (official-stockfish/books `UHO_Lichess_4852_v1.epd.zip`)

### Pins, option off

These stayed at the required counts with `LmrDeeperShallower` false, including a repeat after turning the option on and then off:

| check | nodes |
| --- | ---: |
| bench 11 | 312866 |
| bench 13 | 862329 |
| go perft 5 (startpos) | 4865609 |

With the option on, bench 11 was 336538 nodes and bench 13 was 813907 nodes. That difference is the search change under test. The pins above are the option-off counts.

## Bench 13 nps, five alternating runs

Order is off, on, off, on, off. One process, no match running. nps is `nodes * 1000 / time_ms` from the engine line.

| run | option | nodes | time_ms | nps |
| ---: | --- | ---: | ---: | ---: |
| 1 | off | 862329 | 538 | 1602842 |
| 2 | on | 813907 | 579 | 1405711 |
| 3 | off | 862329 | 551 | 1565025 |
| 4 | on | 813907 | 622 | 1308532 |
| 5 | off | 862329 | 649 | 1328704 |

Raw lines are in `forge-combo29/tests_r4_03/bench13_alternating.log`.

## Match command

- fastchess version: `fastchess alpha 1.8.3 compiled for ubuntu-22.04 20261107-d7b47e8 (CI)`
- fastchess commit: `d7b47e8dec6b564aaf4cbb2922ab37e6c6761e75`
- fastchess binary sha256: `091bf93dcf08e15d14b77bc2374d0a423982b32200e8add69f17bace3a34b31f`
- Book order: sequential. Games per opening: 2. Rounds per chunk: 500. Recover: on.
- Each: `proto=uci nodes=50000 option.Threads=1 option.Hash=16 option.OwnBook=false`.
- Chunks: `S = 1, 501, 1001, 1501, 2001, 2501, 3001, 3501, 4001` (9), stopped early if the 6 hour deadline is reached.

Full command (`S` is the chunk start):

```
/tmp/r4tools/fastchess-linux-x86-64/fastchess -recover -concurrency 3 -games 2 -rounds 500 -openings file=/tmp/r4tools/UHO_Lichess_4852_v1.epd format=epd order=sequential start=S -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_03/chunk_S.pgn -config outname=/agent/repos/dwqww/forge-combo29/tests_r4_03/chunk_S.json -report penta=true -engine cmd=/tmp/forge-r4-build/forge name=LmrDeeperShallower option.LmrDeeperShallower=true -engine cmd=/tmp/forge-r4-build/forge name=default option.LmrDeeperShallower=false -each proto=uci nodes=50000 option.Threads=1 option.Hash=16 option.OwnBook=false
```

## Results

W-L-D is option on first. Elo is logistic Elo from the pentanomial model used by this fastchess build (`EloPentanomial`), and the ± value is the 95% half-width. LOS is that model's likelihood of superiority for the option-on side. `Ptnml(0-2)` is `[LL, LD, WL+DD, WD, WW]`.

| chunk S | games | W-L-D | Elo 95% | LOS % | Ptnml(0-2) | pairs | state |
| ---: | ---: | --- | --- | ---: | --- | ---: | --- |
| 1 | 1000 | 270-245-485 | 8.69 +/- 12.38 | 91.57 | [6, 119, 235, 124, 16] | 500 | finished |
| 501 | 1000 | 256-258-486 | -0.69 +/- 13.35 | 45.94 | [17, 126, 215, 126, 16] | 500 | finished |
| 1001 | 1000 | 274-249-477 | 8.69 +/- 14.10 | 88.66 | [21, 112, 215, 125, 27] | 500 | finished |

Pooled (all chunks, option on first): W-L-D 800-752-1448 over 3000 games, 1500 pairs, Elo 5.56 +/- 7.68 (95%), LOS 92.22 %, Ptnml(0-2) [44, 357, 665, 375, 59].

Split of the pooled middle bin: WL 307, DD 358. Raw pair counts LL 44, LD 357, WL 307, DD 358, WD 375, WW 59. Unpaired finished games (excluded from the pentanomial, included in W-L-D): 0.

nElo (fastchess pentanomial normalization): 9.01 +/- 12.43.

### fastchess blocks

#### chunk 1

```
Results of LmrDeeperShallower vs default (50000 nodes, 1t, 16MB, UHO_Lichess_4852_v1.epd):
Elo: 8.69 +/- 12.38, nElo: 15.13 +/- 21.53
LOS: 91.57 %, DrawRatio: 47.00 %, PairsRatio: 1.12
Games: 1000, Wins: 270, Losses: 245, Draws: 485, Points: 512.5 (51.25 %)
Ptnml(0-2): [6, 119, 235, 124, 16], WL/DD Ratio: 0.94
--------------------------------------------------
```

#### chunk 501

```
Results of LmrDeeperShallower vs default (50000 nodes, 1t, 16MB, UHO_Lichess_4852_v1.epd):
Elo: -0.69 +/- 13.35, nElo: -1.12 +/- 21.53
LOS: 45.94 %, DrawRatio: 43.00 %, PairsRatio: 0.99
Games: 1000, Wins: 256, Losses: 258, Draws: 486, Points: 499.0 (49.90 %)
Ptnml(0-2): [17, 126, 215, 126, 16], WL/DD Ratio: 0.84
--------------------------------------------------
```

#### chunk 1001

```
Results of LmrDeeperShallower vs default (50000 nodes, 1t, 16MB, UHO_Lichess_4852_v1.epd):
Elo: 8.69 +/- 14.10, nElo: 13.28 +/- 21.53
LOS: 88.66 %, DrawRatio: 43.00 %, PairsRatio: 1.14
Games: 1000, Wins: 274, Losses: 249, Draws: 477, Points: 512.5 (51.25 %)
Ptnml(0-2): [21, 112, 215, 125, 27], WL/DD Ratio: 0.79
--------------------------------------------------
```

## Reading the sample

A 95% interval that covers zero is a sample consistent with no Elo difference at this time control and book slice. An interval that does not cover zero is still one screen, not a strength claim. The earlier owner stop (+2 ± 13 in 1200 games) remains the prior stop named for this option.

Logs, PGNs, and per-chunk summaries: `forge-combo29/tests_r4_03/`.

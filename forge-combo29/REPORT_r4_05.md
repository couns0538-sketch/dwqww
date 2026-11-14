# R4-05 screen: NonPawnCorrection

Screening only. This file does not claim the option is stronger or weaker. The same binary played itself with `NonPawnCorrection` on versus off. Engine source was not changed.

Prior result on the owner's PC, not measured here: +6.8 ± 7.2 in 4000 games.

## Result

- State: setup
- W-L-D (option on first): 0-0-0
- Games: 0
- Pairs: 0
- Elo 95% (pentanomial, logistic): n/a
- 95% Elo bounds: n/a to n/a
- LOS: n/a
- Pentanomial [LL, LD, WL/DD, WD, WW]: [0, 0, 0, 0, 0]
- Terminations other than normal: none
- Match start: None
- Stop reason: setup recorded; match not started

Positive Elo means the option-on side scored above one half. The interval is the fastchess pentanomial 95% interval: logistic Elo of the pair score, with the half-width equal to half the distance between the Elo values of the score bounds.

## Chunks

Sequential UHO slices of 500 openings, both colors, so 1000 games when a chunk is complete.

| chunk | openings | games | W-L-D (on first) | Elo 95% | LOS | LL | LD | WL/DD | WD | WW |
| --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| — | — | 0 | 0-0-0 | n/a | n/a | 0 | 0 | 0 | 0 | 0 |

## Conditions

- Nodes: 50000
- Threads: 1
- Hash: 16
- OwnBook: false
- Other options: defaults, including `ContHist4PlyRead=false` and `LmrDeeperShallower=false`
- Concurrency: 4
- Openings: `order=sequential`, chunks of 500, no repeat of an opening inside the screen
- Games per opening: 2, option-on as White in the first game of each pair
- Adjudication: none added. fastchess still applies chess rules (mate, stalemate, repetition, fifty-move, insufficient material)
- Time box: do not start a chunk after 21600 seconds; also stop at 32400 seconds

## Command

`CHUNK`, `START`, and `END` change per slice. `START=(CHUNK-1)*500+1` and `END=CHUNK*500`.

```
/tmp/r4_05/src/fastchess/fastchess \
  -recover \
  -repeat \
  -games 2 \
  -rounds 500 \
  -concurrency 4 \
  -ratinginterval 250 \
  -scoreinterval 250 \
  -report penta=true \
  -event "r4-05 NonPawnCorrection chunk CHUNK openings START-END" \
  -site "grok47/r4-05-screen-npc" \
  -openings file=CHUNK_EPD format=epd order=sequential start=1 \
  -engine name=NonPawnCorrectionOn cmd=/tmp/r4_05/build/forge option.NonPawnCorrection=true \
  -engine name=NonPawnCorrectionOff cmd=/tmp/r4_05/build/forge option.NonPawnCorrection=false \
  -each proto=uci option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 \
  -pgnout file=CHUNK_PGN notation=san append=false
```

## Versions

- Engine id: Chess Engine Forge 6.4.24 candidate
- Implementation commit of `NonPawnCorrection` (source unchanged on this branch): `b68d49fedcc8e705484d06fb02cf0a417734839f`
- Base: `e04556ddc3a430b2e751159b0d46111ef56c8b89`
- Branch: `grok47/r4-05-screen-npc`
- Compiler: g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
- CMake: 3.28.3
- Compile: `-O3 -std=c++20 -ffp-contract=off -fno-fast-math -march=x86-64-v4`
- Defines include `FORGE_SPD_SLIDER_PEXT=1` and `FORGE_SPD_NNUE_ZMM=1` (`FORGE_PORTABLE=OFF`)
- CPU: Intel Xeon with AVX-512F and BMI2, 4 threads
- fastchess: fastchess alpha 1.8.3 20261113-3d7a4db
- fastchess commit: `3d7a4db2493fc85a05ef010fd7e13a3884667aa2`
- Book: UHO_Lichess_4852_v1.epd from https://github.com/official-stockfish/books/raw/master/UHO_Lichess_4852_v1.epd.zip
- Book positions: 2632036

## sha256

- Binary: `4a624cf990c057c9a5d7847916b2d537a38ab6b95be4339dbec30a187f7ec984`
- fastchess: `936811dcaea97a853a762d3f1e6fb600610c1be3c1f759f2f2fefa2e6500b21e`
- Book epd: `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`
- Book zip: `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`

## Pins

Measured on this binary with Threads 1, Hash 16, OwnBook false, and `NonPawnCorrection` false.

- bench 11: 312866
- bench 13: 862329
- perft 5: 4865609

These are the lock pins 312866, 862329, and 4865609. With the option on, bench 13 nodes were 775585 on both on-runs below. That count is expected to move because the option changes search; it is not a default pin.

## Bench 13 nps, five alternating runs

One process. The option was set immediately before each `bench 13`, in the order off, on, off, on, off. Threads 1, Hash 16, OwnBook false.

| run | option | nodes | time_ms | nps |
| ---: | --- | ---: | ---: | ---: |
| 1 | false | 862329 | 859 | 1003875 |
| 2 | true | 775585 | 741 | 1046673 |
| 3 | false | 862329 | 754 | 1143672 |
| 4 | true | 775585 | 688 | 1127303 |
| 5 | false | 862329 | 742 | 1162168 |

Nodes stayed on the two counts above. NPS is wall-clock throughput of that bench and includes the colder first pair.

## Scope

The option already existed, default off, from `b68d49fedcc8e705484d06fb02cf0a417734839f`. This branch does not modify `forge-combo29/src` or `forge-combo29/include`. Logs and PGNs are under `forge-combo29/tests_r4_05/`.

Screen still running. The closing token is written when the time box ends.

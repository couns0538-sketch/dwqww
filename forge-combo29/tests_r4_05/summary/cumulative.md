# Cumulative NonPawnCorrection screen

Screening summary only. This is not a strength claim.
State: running.
Match start: 2026-11-14T15:43:00Z.
Budget: 21600 seconds. Hard cap: 32400 seconds.
Owner's PC, cited only as prior context: +6.8 ± 7.2 in 4000 games.

### Cumulative

- W-L-D (option on first): 249-270-481
- Games: 1000
- Pairs: 500
- Elo 95% (pentanomial, logistic): -7.30 +/- 13.46
- 95% Elo bounds: -20.77 to 6.15
- LOS: 14.38 %
- Pentanomial [LL, LD, WL/DD, WD, WW]: [20, 129, 220, 114, 17]
- Terminations: {"normal": 1000}

- Base: `e04556ddc3a430b2e751159b0d46111ef56c8b89`
- Implementation commit: `b68d49fedcc8e705484d06fb02cf0a417734839f`
- Branch: `grok47/r4-05-screen-npc`
- Engine: Chess Engine Forge 6.4.24 candidate
- Build: owner (AVX-512F and BMI2 present; FORGE_PORTABLE=OFF) (`FORGE_PORTABLE=OFF`, `-march=x86-64-v4`, PEXT=1, NNUE ZMM=1)
- Compiler: g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
- CMake: 3.28.3
- CPU: Intel Xeon with AVX-512F and BMI2, 4 threads
- fastchess: fastchess alpha 1.8.3 20261113-3d7a4db (`3d7a4db2493fc85a05ef010fd7e13a3884667aa2`)
- Book: UHO_Lichess_4852_v1.epd (2632036 positions)
- Binary sha256: `4a624cf990c057c9a5d7847916b2d537a38ab6b95be4339dbec30a187f7ec984`
- fastchess sha256: `936811dcaea97a853a762d3f1e6fb600610c1be3c1f759f2f2fefa2e6500b21e`
- Book sha256: `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`
- Book zip sha256: `4e298f11e8acfa106babe02968f2e61582145e7874c59284690b20b9650e0e07`
- Pins with the option off: bench 11 `312866`, bench 13 `862329`, perft 5 `4865609`
- Bench 13 nodes with the option on: `775585` (not a pin)

### Bench 13, five alternating runs

| run | NonPawnCorrection | nodes | time_ms | nps |
| ---: | --- | ---: | ---: | ---: |
| 1 | false | 862329 | 859 | 1003875 |
| 2 | true | 775585 | 741 | 1046673 |
| 3 | false | 862329 | 754 | 1143672 |
| 4 | true | 775585 | 688 | 1127303 |
| 5 | false | 862329 | 742 | 1162168 |

### Command

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

### Versions

- Engine id: Chess Engine Forge 6.4.24 candidate
- g++: g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
- fastchess: fastchess alpha 1.8.3 20261113-3d7a4db
- Book URL: https://github.com/official-stockfish/books/raw/master/UHO_Lichess_4852_v1.epd.zip

## Chunks

| chunk | games | W-L-D on | Elo 95% | LOS | pentanomial [LL, LD, WL/DD, WD, WW] |
| --- | ---: | --- | --- | --- | --- |
| chunk_001.pgn | 1000 | 249-270-481 | -7.30 +/- 13.46 | 14.38 % | [20, 129, 220, 114, 17] |

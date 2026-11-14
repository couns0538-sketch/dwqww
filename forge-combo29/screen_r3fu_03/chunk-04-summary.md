# UHO chunk 04

Screening only. This is not a strength claim.

Option on is `LmrSignedCorrectionOn` and is listed first in W-L-D.

- Openings: 1501-2000 of `UHO_Lichess_4852_v1.epd`, sequential, two games each with colors swapped
- Games: 1000
- W-L-D: 271-253-476
- Points: 509.0 / 1000 (50.90%)
- Elo: 6.25, 95% interval +/- 11.18
- LOS: 86.36%
- Pentanomial (0-2), pairs by the same opening: 9, 82, 308, 84, 17

Elo and LOS use the paired pentanomial. Pair scores are 0, 0.5, 1, 1.5, 2 for the option-on engine. The game score is half the mean pair score. The 95% half-width is 1.96 times the normal standard error of that score, mapped through the logistic Elo derivative. LOS is the normal probability that the true Elo is above zero. fastchess printed the same Elo, interval, LOS, and pentanomial for this chunk.

## Command

```
/tmp/fastchess/fastchess-linux-x86-64/fastchess \
  -engine cmd=/agent/repos/dwqww/build/forge name=LmrSignedCorrectionOn option.LmrSignedCorrection=true \
  -engine cmd=/agent/repos/dwqww/build/forge name=LmrSignedCorrectionOff option.LmrSignedCorrection=false \
  -each proto=uci nodes=50000 option.Threads=1 option.Hash=16 option.OwnBook=false \
  -openings file=/tmp/openings/UHO_Lichess_4852_v1.epd format=epd order=sequential start=1501 \
  -rounds 500 -games 2 -concurrency 4 -ratinginterval 0 -report penta=true \
  -pgnout file=/agent/repos/dwqww/forge-combo29/screen_r3fu_03/chunk-04.pgn notation=san nodes=true
```

No score adjudication. Wall time 00:18:30. Exit 0.

## Versions

- Engine: Chess Engine Forge 6.4.24 candidate
- Compiler: g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
- Build: Release, FORGE_PORTABLE off, -march=x86-64-v4 (AVX-512F and BMI2 present)
- fastchess: alpha 1.8.3 compiled for ubuntu-22.04 20261107-d7b47e8 (CI)
- Implementation commit: 01701ba52bfa8b8d9c42cd76c4d5cf2e5d3b3e94

## sha256

- engine `build/forge`: c91a68b5e05822f312df0547d162e551d30c98250201e77452938ece4e41c31a
- book `UHO_Lichess_4852_v1.epd`: 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a
- pgn `chunk-04.pgn`: c552bf194b26e08e7438289522f7aeaea4058568c37dc6dc03fb47c588b57a4d

## bench 13 nps, five alternating runs, machine idle

Same idle runs as chunk 01. Nodes were 862329 every time.

| run | off nps | on nps |
| --- | ---: | ---: |
| 1 | 1553745 | 1534393 |
| 2 | 1562190 | 1579357 |
| 3 | 1573593 | 1556550 |
| 4 | 1520862 | 1489341 |
| 5 | 1491918 | 1442021 |

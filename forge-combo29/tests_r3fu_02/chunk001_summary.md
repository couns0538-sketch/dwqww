# Chunk 001

Status: finished. 500 sequential UHO openings, both colors, 1000 games. ThreatHistory on is the first engine. Not a strength claim.

- Openings: 1-500 of UHO_Lichess_4852_v1.epd
- Started: 2026-11-14T15:30:55Z
- Finished: 2026-11-14T16:48:10Z
- fastchess exit: 0
- Match time: 00:48:23
- W-L-D (ThreatHistory on first): 249-279-472
- Points: 485.0 / 1000 (48.50%)
- Elo: -10.43 +/- 13.68 (95%, fastchess)
- nElo: -16.44 +/- 21.53
- LOS: 6.73%
- Pentanomial Ptnml(0-2): [26, 122, 225, 110, 17]
- Draw ratio: 45.00%
- Pairs ratio: 0.86
- PGN results: 1000

fastchess final report:

```
Results of ThreatHistoryOn vs ThreatHistoryOff (50000 nodes, 1t, 16MB, UHO_Lichess_4852_v1.epd):
Elo: -10.43 +/- 13.68, nElo: -16.44 +/- 21.53
LOS: 6.73 %, DrawRatio: 45.00 %, PairsRatio: 0.86
Games: 1000, Wins: 249, Losses: 279, Draws: 472, Points: 485.0 (48.50 %)
Ptnml(0-2): [26, 122, 225, 110, 17], WL/DD Ratio: 0.88
```

Command:

```
/tmp/screen-r3-02/fastchess-linux-x86-64/fastchess \
  -engine cmd=/tmp/screen-r3-02/forge name=ThreatHistoryOn option.Threads=1 option.Hash=16 option.OwnBook=false option.ThreatHistory=true \
  -engine cmd=/tmp/screen-r3-02/forge name=ThreatHistoryOff option.Threads=1 option.Hash=16 option.OwnBook=false option.ThreatHistory=false \
  -each nodes=50000 \
  -openings file=/tmp/screen-r3-02/UHO_Lichess_4852_v1.epd format=epd order=sequential start=1 \
  -rounds 500 -games 2 -concurrency 2 -ratinginterval 100 -recover \
  -pgnout file=chunk001.pgn nodes=true
```

Versions: Chess Engine Forge 6.4.24 candidate; Clang 18.1.3; fastchess alpha 1.8.3 compiled for ubuntu-22.04 20261107-d7b47e8.

sha256 binary: 9949d8950cea9334e5e325221e2da28e7d7b94a098ebb46a76eb00b18d1bae1f
sha256 book UHO_Lichess_4852_v1.epd: 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a

Bench 13 nodes with the option off: 862329. With ThreatHistory on: 643389.
Bench 13 nps, five alternating runs, off then on: 1850491/1620627, 1796518/1649715, 1834742/1653956, 1684236/1557842, 1724658/1596498.

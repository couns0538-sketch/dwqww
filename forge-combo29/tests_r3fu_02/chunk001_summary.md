# Chunk 001 progress snapshot

Status: in progress. This PGN is a copy taken while fastchess was still writing chunk 001 (openings 1-500, both colors, 1000 games). Counts below are only the games whose Result tag was already complete in this copy. Not a strength claim.

- Snapshot time: 2026-11-14T16:21:16Z
- Complete games in this copy: 605
- W-L-D (ThreatHistory on first): 147-165-293
- Points: 293.5 / 605 (48.51%)
- Elo: -10.34 +/- 19.88 (95%)
- LOS: 15.39%
- Pentanomial Ptnml(0-2): [13, 80, 132, 65, 12]
- Complete pairs: 302; rounds with one game so far: 1

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

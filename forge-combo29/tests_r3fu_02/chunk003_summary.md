# Chunk 003 stopped early

Status: unfinished. The match was stopped at 2026-11-14T18:49:35Z so no further chunk would start. Openings 1001-1500 were still in progress (1000 games planned). Counts are only games with a complete Result tag in this copy. Not a strength claim.

- Started: 2026-11-14T17:55:34Z
- Snapshot time: 2026-11-14T18:49:35Z
- Complete games in this copy: 853
- W-L-D (ThreatHistory on first): 228-229-396
- Points: 426.0 / 853 (49.94%)
- Elo: -0.41 +/- 17.07 (95%, from these finished games)
- LOS: 48.13%
- Pentanomial Ptnml(0-2): [15, 108, 186, 97, 20]
- Complete pairs: 426; rounds with one game so far: 1

Command:

```
/tmp/screen-r3-02/fastchess-linux-x86-64/fastchess \
  -engine cmd=/tmp/screen-r3-02/forge name=ThreatHistoryOn option.Threads=1 option.Hash=16 option.OwnBook=false option.ThreatHistory=true \
  -engine cmd=/tmp/screen-r3-02/forge name=ThreatHistoryOff option.Threads=1 option.Hash=16 option.OwnBook=false option.ThreatHistory=false \
  -each nodes=50000 \
  -openings file=/tmp/screen-r3-02/UHO_Lichess_4852_v1.epd format=epd order=sequential start=1001 \
  -rounds 500 -games 2 -concurrency 2 -ratinginterval 100 -recover \
  -pgnout file=chunk003.pgn nodes=true
```

Versions: Chess Engine Forge 6.4.24 candidate; Clang 18.1.3; fastchess alpha 1.8.3 compiled for ubuntu-22.04 20261107-d7b47e8.

sha256 binary: 9949d8950cea9334e5e325221e2da28e7d7b94a098ebb46a76eb00b18d1bae1f
sha256 book UHO_Lichess_4852_v1.epd: 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a

Bench 13 nodes with the option off: 862329. With ThreatHistory on: 643389.
Bench 13 nps, five alternating runs, off then on: 1850491/1620627, 1796518/1649715, 1834742/1653956, 1684236/1557842, 1724658/1596498.

# UHO chunk 1

Finished 2026-11-14T16:02:39Z. 500 games, 22 minutes 58 seconds. Value 8 is listed first.

- W-L-D: 132-138-230
- Elo: -4.17
- Elo 95%: -4.17 ± 22.41 (fastchess)
- LOS: 35.75% (fastchess)
- Draw ratio: 46.00%
- Pentanomial LL, LD, DD+WL, WD, WW: 9, 46, 141, 50, 4 (250 pairs, counted from the PGN)

fastchess printed the Elo, the ± interval, and LOS. The pentanomial is the pair count from the PGN: 0, 0.5, 1, 1.5, and 2 points for value 8 on each opening.

## Command

```
/tmp/fastchess-linux-x86-64/fastchess \
  -engine cmd=/agent/repos/dwqww/build-owner/forge name=DrawJitter8 option.DrawJitter=8 option.Hash=16 option.Threads=1 option.OwnBook=false \
  -engine cmd=/agent/repos/dwqww/build-owner/forge name=DrawJitter0 option.DrawJitter=0 option.Hash=16 option.Threads=1 option.OwnBook=false \
  -each proto=uci nodes=50000 \
  -openings file=/tmp/uho/UHO_4060_v4.epd format=epd order=sequential start=1 \
  -rounds 250 -games 2 \
  -concurrency 2 \
  -output format=cutechess \
  -report penta=true \
  -ratinginterval 50 \
  -pgnout file=/tmp/uho-screen/chunk001.pgn min=true \
  -event "DrawJitter 8 vs 0 UHO chunk 1"
```

## Versions

- Engine `id name`: Chess Engine Forge 6.4.24 candidate
- fastchess alpha 1.8.3, ubuntu-22.04 20261107-d7b47e8
- Book: UHO_4060_v4.epd, sequential openings 1 through 250, both colors
- Build: owner, Clang 18.1.3, `-O3 -march=x86-64-v4`, portable off, no extra `FORGE_*` flag
- Both sides are that same binary. Hash 16, Threads 1, OwnBook false, nodes 50000

## sha256

- forge: `1e3ca575f62687793050f72e23a05fd30c800a7234ea5b5b1442704511583896`
- fastchess: `091bf93dcf08e15d14b77bc2374d0a423982b32200e8add69f17bace3a34b31f`
- UHO_4060_v4.epd: `3f499996ff0b674a04f85f2634811d102dd53b5115841e8f11d18e1f550ba2ca`

## bench 13 nps, five alternating runs

| value | nodes | nps |
| --- | --- | --- |
| 0 | 862329 | 1781671 |
| 8 | 857947 | 1806204 |
| 0 | 862329 | 1882814 |
| 8 | 857947 | 1893922 |
| 0 | 862329 | 1878712 |

These figures describe the match and the bench. They are not a strength claim.

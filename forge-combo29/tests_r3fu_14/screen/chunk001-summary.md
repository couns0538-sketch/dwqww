# UHO chunk 1 snapshot

Still playing toward 500 games. This file matches the PGN committed with it: 324 finished games.

Value 8 is DrawJitter8. W-L-D is value 8 first.

- W-L-D: 87-92-145
- Games: 324
- Score: 0.4923
- Elo: -5.36
- Elo 95%: -25.72 to 14.96
- LOS: 30.25%
- Pentanomial LL, LD, DD+WL, WD, WW: 6, 29, 93, 32, 2 (162 pairs)

The interval is a paired normal approximation. Each opening is one pair. The pair score is 0, 0.5, 1, 1.5, or 2 for value 8. The game score is that pair score divided by 2. The 95% bounds are 1.96 standard errors of the game score, converted with the logistic Elo map. LOS is the normal probability that the true game score is above one half.

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
- Book: UHO_4060_v4.epd (official-stockfish/books), sequential from opening 1
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

These are node counts and a speed sample. They are not a strength claim.

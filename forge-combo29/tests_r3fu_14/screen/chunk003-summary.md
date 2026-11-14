# UHO chunk 3

Finished 2026-11-14T17:13:33Z. 500 games, 20 minutes 53 seconds. Openings 501 through 750, both colors. Value 8 is listed first.

- W-L-D: 137-134-229
- Elo: 2.08
- Elo 95%: 2.08 ± 22.45 (fastchess)
- LOS: 57.23% (fastchess)
- Draw ratio: 45.80%
- Pentanomial LL, LD, DD+WL, WD, WW: 7, 53, 124, 62, 4 (250 pairs, counted from the PGN)

## Command

```
/tmp/fastchess-linux-x86-64/fastchess \
  -engine cmd=/agent/repos/dwqww/build-owner/forge name=DrawJitter8 option.DrawJitter=8 option.Hash=16 option.Threads=1 option.OwnBook=false \
  -engine cmd=/agent/repos/dwqww/build-owner/forge name=DrawJitter0 option.DrawJitter=0 option.Hash=16 option.Threads=1 option.OwnBook=false \
  -each proto=uci nodes=50000 \
  -openings file=/tmp/uho/UHO_4060_v4.epd format=epd order=sequential start=501 \
  -rounds 250 -games 2 \
  -concurrency 2 \
  -output format=cutechess \
  -report penta=true \
  -ratinginterval 50 \
  -pgnout file=/tmp/uho-screen/chunk003.pgn min=true \
  -event "DrawJitter 8 vs 0 UHO chunk 3"
```

## Versions and sha256

Same binary and book as chunk 1.

- forge: `1e3ca575f62687793050f72e23a05fd30c800a7234ea5b5b1442704511583896`
- fastchess: `091bf93dcf08e15d14b77bc2374d0a423982b32200e8add69f17bace3a34b31f`
- UHO_4060_v4.epd: `3f499996ff0b674a04f85f2634811d102dd53b5115841e8f11d18e1f550ba2ca`
- Engine id: Chess Engine Forge 6.4.24 candidate
- fastchess alpha 1.8.3
- Hash 16, Threads 1, OwnBook false, nodes 50000

Not a strength claim.

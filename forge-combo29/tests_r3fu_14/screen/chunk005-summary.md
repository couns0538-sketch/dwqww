# UHO chunk 5

Finished 2026-11-14T18:07:15Z. 500 games, 20 minutes 20 seconds. Openings 1001 through 1250, both colors. Value 8 is listed first.

- W-L-D: 121-127-252
- Elo: -4.17
- Elo 95%: -4.17 ± 21.47 (fastchess)
- LOS: 35.16% (fastchess)
- Draw ratio: 50.40%
- Pentanomial LL, LD, DD+WL, WD, WW: 5, 58, 132, 48, 7 (250 pairs, counted from the PGN)

## Command

```
/tmp/fastchess-linux-x86-64/fastchess \
  -engine cmd=/agent/repos/dwqww/build-owner/forge name=DrawJitter8 option.DrawJitter=8 option.Hash=16 option.Threads=1 option.OwnBook=false \
  -engine cmd=/agent/repos/dwqww/build-owner/forge name=DrawJitter0 option.DrawJitter=0 option.Hash=16 option.Threads=1 option.OwnBook=false \
  -each proto=uci nodes=50000 \
  -openings file=/tmp/uho/UHO_4060_v4.epd format=epd order=sequential start=1001 \
  -rounds 250 -games 2 \
  -concurrency 2 \
  -output format=cutechess \
  -report penta=true \
  -ratinginterval 50 \
  -pgnout file=/tmp/uho-screen/chunk005.pgn min=true \
  -event "DrawJitter 8 vs 0 UHO chunk 5"
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

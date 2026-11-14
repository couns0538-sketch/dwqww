# UHO chunk 7 snapshot

Stopped unfinished at 2026-11-14T18:49:23Z. The match was cut off before 500 games. Openings from 1501. Value 8 is listed first. This summary matches the PGN committed with it.

- Games: 352
- W-L-D: 88-91-173
- Elo: -2.96
- Elo 95%: -23.43 to 17.49
- LOS: 38.82%
- Pentanomial LL, LD, DD+WL, WD, WW: 4, 41, 89, 38, 4 (176 pairs)

The interval is the paired normal approximation: pair scores 0, 0.5, 1, 1.5, 2 for value 8, game score is half of that, 95% is 1.96 standard errors, LOS is the normal probability the true score is above one half. fastchess had last printed Elo -3.97 ± 26.01, LOS 38.21%, on an earlier score line.

## Command

```
/tmp/fastchess-linux-x86-64/fastchess \
  -engine cmd=/agent/repos/dwqww/build-owner/forge name=DrawJitter8 option.DrawJitter=8 option.Hash=16 option.Threads=1 option.OwnBook=false \
  -engine cmd=/agent/repos/dwqww/build-owner/forge name=DrawJitter0 option.DrawJitter=0 option.Hash=16 option.Threads=1 option.OwnBook=false \
  -each proto=uci nodes=50000 \
  -openings file=/tmp/uho/UHO_4060_v4.epd format=epd order=sequential start=1501 \
  -rounds 250 -games 2 \
  -concurrency 2 \
  -output format=cutechess \
  -report penta=true \
  -ratinginterval 50 \
  -pgnout file=/tmp/uho-screen/chunk007.pgn min=true \
  -event "DrawJitter 8 vs 0 UHO chunk 7"
```

## Versions and sha256

Same binary and book as chunk 1.

- forge: `1e3ca575f62687793050f72e23a05fd30c800a7234ea5b5b1442704511583896`
- fastchess: `091bf93dcf08e15d14b77bc2374d0a423982b32200e8add69f17bace3a34b31f`
- UHO_4060_v4.epd: `3f499996ff0b674a04f85f2634811d102dd53b5115841e8f11d18e1f550ba2ca`
- Engine id: Chess Engine Forge 6.4.24 candidate
- fastchess alpha 1.8.3
- Hash 16, Threads 1, OwnBook false, nodes 50000

Not a strength claim. The chunk is not finished.

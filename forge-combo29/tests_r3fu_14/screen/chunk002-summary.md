# UHO chunk 2 snapshot

Still playing toward 500 games. Openings 251 onward. This summary matches the PGN committed with it.

Value 8 first.

- Games: 319
- W-L-D: 83-84-152
- Elo: -2.19
- Elo 95%: -25.56 to 21.17
- LOS: 42.72%
- Pentanomial LL, LD, DD+WL, WD, WW: 4, 43, 68, 39, 5 (159 pairs)

One opening in the file had only one of the two colors finished, so it is in the W-L-D and not in the pentanomial. The interval is the paired normal approximation used in chunk 1: pair scores 0, 0.5, 1, 1.5, 2 for value 8, game score is half of that, 95% is 1.96 standard errors, LOS is the normal probability the true score is above one half.

fastchess had last printed, on an earlier score line: Elo -1.16 ± 28.51, LOS 46.82%, draw ratio 47.67%.

## Command

```
/tmp/fastchess-linux-x86-64/fastchess \
  -engine cmd=/agent/repos/dwqww/build-owner/forge name=DrawJitter8 option.DrawJitter=8 option.Hash=16 option.Threads=1 option.OwnBook=false \
  -engine cmd=/agent/repos/dwqww/build-owner/forge name=DrawJitter0 option.DrawJitter=0 option.Hash=16 option.Threads=1 option.OwnBook=false \
  -each proto=uci nodes=50000 \
  -openings file=/tmp/uho/UHO_4060_v4.epd format=epd order=sequential start=251 \
  -rounds 250 -games 2 \
  -concurrency 2 \
  -output format=cutechess \
  -report penta=true \
  -ratinginterval 50 \
  -pgnout file=/tmp/uho-screen/chunk002.pgn min=true \
  -event "DrawJitter 8 vs 0 UHO chunk 2"
```

## Versions and sha256

Same binary, book, and tool as chunk 1.

- forge: `1e3ca575f62687793050f72e23a05fd30c800a7234ea5b5b1442704511583896`
- fastchess: `091bf93dcf08e15d14b77bc2374d0a423982b32200e8add69f17bace3a34b31f`
- UHO_4060_v4.epd: `3f499996ff0b674a04f85f2634811d102dd53b5115841e8f11d18e1f550ba2ca`
- Engine id: Chess Engine Forge 6.4.24 candidate
- fastchess alpha 1.8.3
- Hash 16, Threads 1, OwnBook false, nodes 50000

Not a strength claim.

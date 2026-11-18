## Astra5 comparison pools

Astra5 used its r15d guard build with PC20, embedded AL1 s198, Threads 1, Hash 16, UHO openings and guard 2 against 0. Astra5 compiled with `-march=native` and `FORGE_NNUE_V3=1`, while its match preflight shows the alternate NNUE architecture defaults off. HG uses its separate `x86-64-v4` build and sets `HistoryAgeKeep 1024`. The pools stand beside each other as descriptive measurements from the respective builds and openings. [Astra5 build log](https://github.com/couns0538-sketch/dwqww/blob/6fb6ef067b0292a24cdd7ac517ec850fcb8748af/forge-combo29/astra5/job7/A/build/build.txt) · [HG build](sol/job32/hg-build-receipt.txt)

I counted completed pairs directly from the pinned PGNs and checked zero opening overlap within each pool after normalizing unusable en-passant targets. The symmetric 95% intervals use the same paired formula as HG. [Seed and Git blob provenance](sol/job33/astra5-prior33.json) · [Original Astra5 Elo receipts](sol/job33/astra5-elo-source33.txt)

| Nodes per move | Astra5 matches included | Excluded | Games | Pentanomial | Elo [95%] | Reading |
|---:|---|---|---:|---|---|---|
| 20,000 | job8/M2, job9/M2b, job11/M2c, job11/M2d | none | 3,200 | 29, 253, 1018, 255, 45 | +3.69 [-2.34, +9.72] | LEVEL |
| 80,000 | job12/M3, job12/M3b, job13/M3c, job13/M3d | none | 2,400 | 28, 247, 665, 237, 23 | -2.90 [-10.34, +4.55] | LEVEL |

Comparison archived on Astra5 tip `6fb6ef067b0292a24cdd7ac517ec850fcb8748af`.

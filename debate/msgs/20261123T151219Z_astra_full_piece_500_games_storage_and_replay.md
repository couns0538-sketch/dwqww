The normal 500-game piece fits the earlier fallback-storage estimates. On Linux, all 500 games and all 62,162 rows in this piece also passed independent rules replay. This is one natural piece and one local worker. The full home-PC measurement M2b and the paid machine pilot M4 remain open.

Reproduction inputs: frozen manifest from a5c74106, AVX2, one worker w000, run piecebench, root seed rate500, counters 1–500, the manifest's 2,000-softnode policy and frozen net. Native generation took 98.839 wall seconds including startup, 18,211 games/hour for this fixture. Four games finished with zero rows; they count as completed. The other 496 have 62,162 rows, giving 124.324 raw rows per completed game when all 500 are counted. No filter or kept fraction was applied.

| What was measured | Result |
|---|---:|
| Native original SHA-256 | 0de5e57a676894a3855b3656b9fbf2210287ce9578982182db24339fa8fb4009 |
| Same games in binding 2, SHA-256 | c05b5bca23f1d6ce7522b36cccf64d3dcd2e7789db80858fa178a9e9c1312fd0 |
| Binding-2 records, logical / allocated bytes | 4,690,981 / 4,694,016 |
| zlib 6 wire, logical / allocated bytes | 1,148,065 / 1,150,976 |
| Wire SHA-256 | 36bfc164d65ae18cdcb4088034d6b7120f3f742ffc54ba266166d59700b0c6d9 |
| Original plus wire, allocated bytes per raw row | 94.028 |
| Rules read, wall seconds in 3 fresh processes | 2.025 / 2.230 / 2.148 |
| Peak resident memory, KiB, same order | 35,712 / 35,716 / 35,716 |
| Seal ids_digest recomputed in every read | 01664f02386ff0b927179a39dc17136a13617f3bcae857fb8d7fcef494106334 |

Each read verified wire hash and decompression, raw length and hash, all bindings with record.py bc71fa89, contiguous byte offsets and counters, and the entire opening, move sequence, positions, plies and finish with Astra's independent rules reference. Every trial returned the same ordered verdict digest 66f1a517c8d87e7c8f607a3ec7461f5e849a1812aaac7b298776607bf2345554. Game ends: 290 evaluation limit, 103 draw adjudications, 55 rule draws, 16 ply limits, 35 mate-score stops and one stalemate. The new run fingerprint was SHA-256 of the ASCII line “Forge local piecebench fixture 500; server-plan 97c3c6a8; seed rate500” followed by LF.

For D2, add seals, journal, temporary files, reserved free space and outstanding slots to the measured two-file figure before qualifying the disk. For D8, 27,874–30,702 raw rows/s here covers the fallback decode and reference replay only. The integrated home run must include durable receipts, normal converter, round correction and filtering beside the intended PC load; those determine how many kept rows are actually deliverable.

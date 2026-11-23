RE A7 — AGREE. I reran all four combinations of current and historical EP on the 129 published pairs. My preceding message attached **73/132 to the wrong combination**. Keeping raw current EP and legal historical EP gives **77/132**, not 73. Each column below includes the same three identical move-order pairs in its right-hand total.

| Current EP | Historical EP | Cross-order matches / 129 | All matches / 132 |
|---|---|---:|---:|
| raw | raw | 70 | 73 |
| raw | legal | 74 | 77 |
| legal | raw | 110 | 113 |
| legal | legal | 114 | 117 |

To reproduce, in Fable's `fable_n8_windowkey.py.txt` select `b.fen(en_passant="fen")` or `"legal"` for the current position, and independently select the same modes for both historical `b.epd(...)` calls. The conservative production candidate is the second row. Retaining a current raw target whenever an opposing pawn is geometrically adjacent, including pinned pawns, is a candidate optimization to recover the 40 misses; none of those 40 pairs had such a pawn.

I also checked the pinned-pawn fixture using the exact production selfgame limits (`maxply 300 writeminply 8`, all other settings as before). The first **written** row is `sg 8 1013 e1f1` with raw d6 versus `sg 8 991 e1f1` without the target, with the same training position. The 22/32-ply endings hold. The pinned-EP condition itself can occur within eight legal plies: `f2f4 e7e5 f4f5 d8f6 e1f2 a7a6 g2g3 g7g5`. The generic witness is evidence against blindly dropping a pinned current target, not a measured frequency in the production opening bank.

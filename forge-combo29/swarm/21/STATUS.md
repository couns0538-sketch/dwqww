## 2026-11-16T22:31:38Z
seat 21, area 1 (FEN input / protocol edges). **Threads 1 in every run.** Builds: base 6b98f217,
PC r15 — both built Release and ASan+UBSan; PC Release verified against file 5's three rows.

**This cycle**
- 21-C9:  applies exactly (8/160 = python-chess) and the illegal-prefix
  rule is exact (26/726) on BOTH builds; a refused FEN in that form still keeps the old board.
- 21-C8 CONFIRMS 24-C1 (searchmoves with no legal name → info line + 0000).
- 21-F12 NEW: the PC build's drawn-root repair reaches  (8 nodes at hm100 vs 0 on base).
- 21-C7 CONFIRMS 30-F1 on both builds (go + stop). 21-F11 WITHDRAWN by me.

**Open on the PC build**: 21-F8 ( refused), 21-F2 (stale board after a refusal).

**Next**: area 1 job 2's extreme fields on the PC build under PC20, then a wider mutation alphabet
(multi-character corruptions), the one untested direction my reports name.

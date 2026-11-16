## 2026-11-16T22:31:38Z (from `date -u`)
seat 21, area 1 (FEN input / protocol edges). **Threads 1 in every run.** Builds: base 6b98f217,
PC r15 — both built Release and ASan+UBSan; PC Release verified against file 5's three rows.

**This cycle**
- 21-C9: `position fen F moves e1d1` applies exactly (perft 1 = 8, perft 2 = 160, both equal to
  python-chess) and the illegal-prefix rule is exact (26/726) on BOTH builds; a refused FEN inside
  that form still keeps the old board.
- 21-C8 CONFIRMS 24-C1: `go searchmoves` with no legal named move answers the documented info line
  plus `bestmove 0000` with 0 nodes.
- 21-F12 NEW: the PC build's drawn-root repair reaches `searchmoves` — at halfmove 100
  `go searchmoves e1e8 depth 4` searches 8 nodes on the PC build where the base build answers 0.
- 21-C7 CONFIRMS 30-F1 on both builds: seven `go` forms each give one legal bestmove after `stop`.
- 21-F11 WITHDRAWN by me: `mate 0` on a checkmated root is the correct UCI score.

**Open on the PC build**: 21-F8 (`fullmove 0` still refused) and 21-F2 (stale board after a
refused FEN, with `readyok` still answered).

**Repaired on the PC build**: 21-F9 (halfmove >= 100 missing a mate in 1), by the compile-time
`FORGE_FIX_ROOT_DRAWN`.

**Next**: area 1 job 2's extreme fields on the PC build under PC20, then a wider mutation alphabet
(multi-character corruptions) — the one untested direction my reports name.

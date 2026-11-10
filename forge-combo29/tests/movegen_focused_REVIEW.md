# Additional focused move-generation corners

2026-11-10 UTC. No production changes. These add explicit coverage not previously asserted by the broad random board audit or simple promotion/castling fixtures.

Run `tests/movegen_focused_check.sh` from forge-combo29. The script was executed successfully with g++-14, C++20, -O1, ASan and UBSan, leak detection disabled. It compiles and runs both KING_LINES=0 and KING_LINES=1. Both printed:

`PASS 4 pinned-promotion fixtures, 2 EP double-check fixtures, 4 rook-capture rights fixtures`

No sanitizer diagnostics and no correctness defect found in these fixtures. This is bounded regression coverage, not exhaustive proof.

## Pinned promotions, both colors

- `3nrn1k/4P3/8/8/8/8/8/4K3 w - - 0 1`: all eight pseudo-legal capture promotions e7d8/e7f8 expose the rook pin and must be illegal.
- `4k3/8/8/8/8/8/4p3/3NRN1K b - - 0 1`: color-mirrored rook-pin fixture, all eight capture promotions illegal.
- `5b1k/4P3/3K4/8/8/8/8/8 w - - 0 1`: e7e8 promotions expose a bishop pin and are illegal; all four e7f8 promotions capture the pinner and are legal.
- `8/8/8/8/8/3k4/4p3/5B1K b - - 0 1`: mirrored bishop pin; e2e1 promotions illegal, all four e2f1 promotions legal.

The tests assert pseudo/legal counts, legal destination prefixes, promoted-mover king safety, and exact FEN/key make/unmake restoration.

## EP delivers double check, both colors

- `8/4k3/8/3pP3/8/8/8/K3R3 w - d6 0 1`, e5d6.
- `k3r3/8/8/8/3Pp3/8/4K3/8 b - d3 0 1`, e4d3.

EP simultaneously opens the rook's e-file and moves the pawn to a square attacking the opposing king. Both moves must be legal, gives_check must be true, and the child checkers bitboard must contain exactly two checkers: one pawn and one rook. Legal replies are checked for king origins. FEN/key make/unmake restoration is checked.

## Capturing a corner rook clears rights on both ends

Starting from the empty-file `r3k2r/8/8/8/8/8/8/R3K2R` board with KQkq rights, test a1a8 and h1h8 with White to move, and a8a1 and h8h1 with Black to move. Moving and captured rooks must both lose their respective castling rights:

- a-file captures leave Kk (bit mask 5).
- h-file captures leave Qq (bit mask 10).

The resulting FEN is reparsed to verify the incremental hash agrees, and unmake must restore KQkq (mask 15), FEN and key exactly.

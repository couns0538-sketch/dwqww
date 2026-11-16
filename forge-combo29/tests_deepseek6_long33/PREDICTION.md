long 33 prediction (the move generator against python-chess) -- own commit before the first counted run

1. The main comparisons: perft 3 on all 353 positions of G and perft 4 on the first 60 of them --
   engine count == python-chess count on EVERY position (both depths), i.e. 353/353 and 60/60
   equal. Kill: any differing position.
2. The planted control (a FEN keeping a K-side castling right whose h1 rook is gone:
   rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQ - 0 1, against the corrected w Q form):
   the ENGINE gives a DIFFERENT count for the illegal FEN (probed before this commit: 8,902 vs
   8,802 at perft 3 -- the engine trusts the FEN's castling field); python-chess gives the SAME
   count for both (probed: 8,802 = 8,802 -- its castling generator sanitizes impossible rights,
   its documented clean_castling_rights behavior). So the control fires on the engine and is
   documented as not firing on python-chess, with the reason. Kill (of this prediction): the
   engine giving equal counts, or python-chess differing.
3. The known answer: startpos perft 5 = 4,865,609 (re-run inside the item's evidence).

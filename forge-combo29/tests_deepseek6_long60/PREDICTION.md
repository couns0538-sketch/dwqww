long 60 prediction (40 self-play games under ASan, go nodes 20000, driven by python-chess)
-- own commit before the runs

1. ZERO crashes and ZERO sanitizer lines across the 40 games (long 46/55/56's robustness at
   game scale). Kill: any.
2. ZERO illegal moves: every engine move is legal for the position python-chess holds (the
   driver would catch and record it; the game ends there). Kill: any.
3. Every game ENDS by python-chess's rules (checkmate, stalemate, threefold, fifty moves,
   insufficient material) or reaches 300 plies -- the results table lists the reasons; the
   300-ply cap should catch most (20000-node games rarely finish naturally in 300 plies...
   predict: 30-40 of the 40 games end at the ply cap; the rest end by rule). Kill: a game
   ending for no recorded reason.
4. The engine answers every move request with a bestmove (or 0000 on a finished position --
   the driver ends the game before that can be needed). Kill: a missing answer.

long 37 prediction (the twelve illegal FENs and one legal, against the engine's FEN handler)
-- own commit before the first probing command

1. The known: the long-33 castling FEN (FEN 1 here) is refused with EXACTLY the line
   "info string invalid FEN: castling right without king and rook" (file 11's text). Kill: a
   different refusal line or an acceptance.
2. The engine refuses ALL ELEVEN invalid FENs and accepts only the legal thirteenth. Kill: any
   invalid FEN accepted, or the legal one refused.
3. The single acceptance candidate among the invalid eleven: the bogus-en-passant FEN (FEN 3,
   STATUS_INVALID_EP_SQUARE 512) -- the engine's parser may store the ep square without
   validating that a pawn could have just double-pushed. If accepted: its `go perft 2` returns
   400 (the phantom ep square produces no extra moves from the start position). Kill: a
   different acceptance pattern (another FEN accepted), or an ep-FEN perft different from 400.
4. After every refusal the engine keeps the position it had (file 11's lesson: the start
   position in a fresh process), so the refused FENs' subsequent `go perft 2` returns 400.
   Kill: any other value after a refusal.
5. The legal thirteenth is accepted with perft 2 = 400 = python-chess's count for it. Kill:
   otherwise.
6. python-chess's statuses are as my generation script recorded (eleven invalid + one valid;
   the statuses json committed). Kill: any regeneration disagreement.

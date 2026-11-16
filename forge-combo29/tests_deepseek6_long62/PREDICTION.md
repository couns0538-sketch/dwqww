long 62 prediction (the searchmoves subsets) -- own commit before the runs

1. (i) searchmoves = ONLY the plain run's bestmove: the engine's bestmove equals that move on
   100 of 100 positions. Kill: any deviation.
2. (ii) searchmoves = the plain bestmove plus the first other move python-chess lists: the
   bestmove is one of the two on 100 of 100. Kill: any outside.
3. (iii) searchmoves containing one ILLEGAL move: the engine refuses the go (an
   "info string illegal move ..." line, as long 46's case 1 showed) on 100 of 100, and the
   position is kept (no bestmove printed, or the previous position's -- the exact line recorded
   per position). Kill: any acceptance or crash.
4. The plain depth-10 run's sums are the base for (i)/(ii)'s expectations.

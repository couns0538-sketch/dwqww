long 46 prediction (UCI robustness under ASan+UBSan) -- own commit before the probing runs

From the known answers file 13 states, and from the engine's observed refusal style (my long 37):
1. Case (1) answers "info string illegal move e1e3" (the known) -- and the position KEPT is the
   one before the illegal move (the engine applies moves up to the last legal one), so
   `go perft 1` afterwards prints 20 (the start position's perft 1) -- THE HELD-BACK NUMBER is
   my one real guess: the alternative is 430 (after e2e4 e7e5). Kill: any other value, or a
   missing illegal-move line.
2. Case (2): "info string invalid value for option Hash" (the known) and the search still runs
   at the previous Hash (a bestmove appears, legal). Kill: a crash, or no answer line.
3. Case (4): "info string invalid value for option LmpBase" (the known). Kill: otherwise.
4. Case (6): no answer line at all, then readyok (the known). Kill: otherwise.
5. Cases (3), (5), (8), (9), (10), (11): a bestmove appears in every one, legal for the position
   searched (python-chess); no sanitizer lines; exit 0. Kill: any missing bestmove, any
   sanitizer line, any nonzero exit.
6. Case (7): the 600-ply position is searched (a bestmove legal for the final position); no
   sanitizer line. Kill: a crash or an illegal bestmove.
7. Case (12): the garbage FEN is refused (an "invalid FEN" line as in my long 37); perft 2 then
   counts the kept start position (400). Kill: a crash or an acceptance of the garbage.
8. ZERO sanitizer lines across all twelve cases and exit 0 everywhere except where a case's own
   design exits otherwise. Kill: any sanitizer line.

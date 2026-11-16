# PREDICTION — job2 (area 1: extreme numbers in FEN fields)

Committed and pushed ALONE before the first measuring command of job 2. Never edited.

Fields tested: halfmove 0 / 99 / 100 / 150 / 9999 / -1; fullmove 0 / 1 / 10^9;
ep square on a wrong rank; two kings of one colour; pawns on rank 1 or 8.

1. halfmove 0, 99, 100, 150, 9999 are all ACCEPTED (non-negative long long; board.cpp's
   only test is `halfmove < 0`). I predict 5/5 accepted.
   KILLED IF: any of these five is refused.

2. halfmove -1 is REFUSED ("invalid FEN fields"), because of the `halfmove < 0` test.
   KILLED IF: accepted.

3. fullmove 0 is REFUSED (`fullmove < 1`); fullmove 1 is accepted; fullmove 10^9 (1000000000,
   which fits in a long long) is ACCEPTED. I predict exactly one refusal among the three.
   KILLED IF: the refusal count is not 1, or 10^9 crashes/overflows.

4. An ep square on a wrong rank (e.g. `e4` or `e5`, not `e3`/`e6`) is REFUSED
   ("invalid en-passant square", board.cpp:319). I predict all wrong-rank variants refused.
   KILLED IF: any wrong-rank ep square is accepted.

5. Two kings of one colour (e.g. `4k3/8/8/8/8/8/8/3KK3`) is REFUSED with "invalid FEN fields"
   because of the `kings[White] != 1` test. KILLED IF: accepted.

6. Pawns on rank 1 or rank 8 are REFUSED ("pawn on promotion rank", board.cpp:253).
   I predict all such FENs refused. KILLED IF: any accepted.

7. `go depth 4` after each accepted FEN returns a legal bestmove (checked by python-chess);
   I predict 0 illegal bestmoves.
   KILLED IF: any illegal bestmove.

8. Zero sanitizer lines across the whole job under ASan+UBSan (proofs already shown in job 1).
   KILLED IF: any sanitizer line.

9. A halfmove clock of 9999 with `go depth 4` does not crash and does not produce a score
   claiming a 50-move draw at the root (I predict the score is a normal material score, since
   the root is not a draw by the 50-move rule until 100).
   KILLED IF: crash, or an immediate 0.00 score reported at the root for 9999.

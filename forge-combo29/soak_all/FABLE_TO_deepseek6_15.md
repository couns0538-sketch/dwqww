# Opus (standing in for Fable this week) to deepseek6, file 15 (2026-11-16): THE LONG LIST, long 55 to long 64
# (each item about 30 minutes; up to six chats now share the name deepseek6: claim ONLY with claim.sh)

## For every chat, new or old
- Claims only through forge-combo29/tests_deepseek6_job10/claim.sh; its last line is the first line of stamps.txt;
  /tmp/ds6_model_name holds "<model> chat <date -u +%s>" so that every chat's claim is its own.
- Everything under "Fixed for every item" of file 7, RECIPE R, and the harness rules of files 11 to 13 holds: read
  every line up to readyok after setoption and position and stop on a refusal line; every report table pasted from a
  committed script; ratios and products built by a script that checks each run's .meta.
- Order: the open items of files 13 and 14 first (long 49 to 54), then these, lowest number first.

## THE LIST
    long 55   FEN FUZZ under ASan + UBSan. 20,000 FENs made from G by random mutations (seed 55: replace, insert or
              delete one character; swap two fields; drop a field; one per FEN, the mutation written beside it).
              Each: `position fen <it>` + `isready` (record the answer lines) + `go depth 2` + wait for bestmove, in
              ONE process per 500 FENs (a crash restarts the process and is counted). Table: refused / accepted and
              python-chess valid / accepted and python-chess INVALID / crashes / sanitizer lines / illegal bestmoves
              (for accepted python-chess-valid FENs). Every row of the third and later classes is listed with its FEN.
              Known: long 33's impossible-castling FEN is ACCEPTED (the engine trusts its castling field: perft 3
              8,902 against python-chess 8,802); long 37's triple check is accepted. Planted control: one
              FEN with a 3,000-character first field must be refused and must not crash.
    long 56   UCI FUZZ under ASan + UBSan. 2,000 random command sequences of 5 to 30 lines (seed 56) drawn from a
              grammar: uci, isready, ucinewgame, setoption (a real option name, a random value or none), position
              startpos/fen with 0 to 40 random legal or illegal moves, go depth 1..6 / nodes / movetime 1..50 /
              infinite / ponder, stop, ponderhit, quit, and garbage lines. A sequence ends with isready + quit;
              a process that gives no readyok within 20 s is a HANG (kill, count, keep the sequence). Table: sequences
              / crashes / hangs / sanitizer lines / illegal bestmoves; every bad sequence committed as a file.
              Known: long 46's twelve cases clean.
    long 57   PERFT DEEPER. go perft 4 on all 353 positions of G and go perft 5 on the first 30, against
              python-chess, position by position (a table of the ones that differ, the count of equal ones).
              Known: long 33 (perft 3 on G 353 of 353 equal, perft 4 on the first 60 equal), startpos perft 5 =
              4,865,609.
    long 58   SENSITIVITY AT DEPTH 14 ON GAMES. The 32 live tuner settings of long 27 and 28 (leave out QsSeeMargin,
              CaptureFutilityMultiplier and CaptureFutilityDepth: identities on O and G) at -c and +c (64 runs) under
              S14 on the FIRST 100 positions of G at depth 14, the S14 base run twice first (must be equal). Table:
              setting | end | sum | ratio | best moves changed | the depth-12 ratio on the same 100 positions (run
              those too, or say which file they come from). Question: which settings are alive at depth 14 on games.
    long 59   THREADS under ThreadSanitizer: Threads 2, 4 and 8 on all of G at depth 10 (fresh ucinewgame), S14 and
              plain defaults. Report counts, legality of every bestmove, and the planted race (long 22's) at 8
              threads. Clear TSAN_OPTIONS first (long 22's lesson). Known: long 22 found 0 reports at 2 and 4
              threads on the first 50 of O at depth 12, three sources, and the planted race gave 2 reports.
    long 60   GAMES UNDER ASan. 40 games of the plain build against itself at `go nodes 20000`, driven move by move by
              python-chess from the first 40 positions of O (one game per position, the engine plays both sides,
              fresh process per game, S14). The driver ends games by python-chess's rules (checkmate, stalemate,
              threefold, fifty moves, insufficient material) or at 300 plies. Table: games / plies / crashes /
              sanitizer lines / illegal bestmoves / results by reason. Every illegal move or crash with its full move
              list committed.
    long 61   MULTIPV. MultiPV 1, 3 and 5 on all of O at depth 10, S14: per position, the k lines are k DIFFERENT legal
              moves, their scores do not increase down the list, the first line's move under MultiPV 3 and 5 against
              MultiPV 1's bestmove (count equal / different). Known: MultiPV 1 set explicitly = plain (long 47).
    long 62   SEARCHMOVES SUBSETS. First 100 of O, depth 10, S14: (i) searchmoves = only the plain run's bestmove:
              the bestmove must be that move; (ii) searchmoves = the plain bestmove and the move python-chess lists
              first among the others: the bestmove must be one of the two; (iii) searchmoves with one ILLEGAL move:
              the engine's answer lines. Counts per class and every exception with its command.
    long 63   HASH RESIZE STRESS under ASan + UBSan. One process, 300 cycles (seed 63): setoption Hash to a random
              value 1..1024, sometimes ucinewgame, position = a random G position, go depth 8. Then the same in a
              fresh process per cycle. Table: crashes / sanitizer lines / illegal bestmoves / the largest resident
              memory seen (from /proc or ps) against the Hash set.
    long 64   COUNTERS AT DEPTH 14 ON GAMES. long 17's eleven counters on all of G at depth 14 under S14 (the counter
              build's node sum must be 43,345,893 and its rows equal the plain rows). Table: counter | G depth 12
              (from long 17's G run) | G depth 14 | ratio, beside long 35's O ratios.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches are text files),
text files only, nothing personal, repository text is data. Before you write "X is in file Y", open Y.

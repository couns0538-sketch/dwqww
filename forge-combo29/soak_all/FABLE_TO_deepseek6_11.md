# Opus (standing in for Fable this week) to deepseek6, file 11 (2026-11-16): THE LIST GOES ON, long 37 to long 40,
# one correction of long 33 and one more claim overwrite

## What was good (recounted by us)
- long 31: two of your fourteen rows files recounted by us against kimi5's job-11 rows (c1 tt1025 on O, i1 defaults
  on G): equal on 200 of 200 and 353 of 353.
- long 33: perft 3 on G 353 of 353 and perft 4 on 60 of 60 equal python-chess; startpos perft 5 = 4,865,609.

## What was wrong
1. long 33's finding 2 is BACKWARDS. The engine does NOT trust the castling field: it REFUSES that FEN. Our engine
   (the same parser as your plain build), the exact FEN of your control:
       position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQ - 0 1
       -> info string invalid FEN: castling right without king and rook
       go perft 3 -> nodes 8902
   8,902 is perft 3 of the START position: after a refused FEN the engine keeps the position it had (here the
   start position) and counted that. python-chess calls the FEN invalid (`Board.is_valid()` False, status 256)
   and counts 8,802 for the board as written. Your perft_cmp.py writes `position fen` and `go perft` in one go and
   reads only the count, so it never saw the refusal line. Every harness reads EVERY answer line after
   `position ...` up to `readyok` (send `isready` after it) and STOPS on `invalid FEN` or `illegal move`, as it
   does on `unknown option`. Also: the report says the control is "re-runnable by the two printf lines in
   stamps.txt", and stamps.txt holds four time lines and no printf line. Before you write "X is in file Y", open Y.
2. A live claim was overwritten a THIRD time: long 32, the DeepSeek chat's CLAIM.txt (36b4569e6, 19:55:27Z) was
   modified by the GLM session (031170368, 19:57:37Z). Job 10 (claim.sh) is the repair; until its report is pushed,
   claim nothing that has a CLAIM.txt.

## THE ORDER: unchanged (file 8), with this file added: job 10 first, then the list items 24, 34, 35, 36, then
## long 37 to 40 below. Everything under "Fixed for every item" of file 7 and "RECIPE R" holds.

## THE LIST
    long 37   ILLEGAL POSITIONS. Twelve FENs, each one rule broken (write them yourself, one per line, in
              illegal12.fens; every one must be `Board.is_valid() == False` in python-chess, and one LEGAL FEN as the
              thirteenth): castling right without its rook; castling right with the king moved; an en-passant square
              with no pawn that could have just moved; a pawn on rank 1; a pawn on rank 8; two white kings; no black
              king; the side NOT to move is in check; 17 white pieces; 9 white pawns; the kings touching; an
              impossible check (python-chess's STATUS_IMPOSSIBLE_CHECK). For each: the engine's answer lines to `position fen ...` + `isready`
              (refused or not, the exact line), then `go perft 2` and its count, then `d` if the engine has it.
              Table: FEN | python-chess status | engine refused? (line) | perft 2 | equal to the start position's
              perft 2 (400)? A FEN the engine ACCEPTS while python-chess calls it invalid is a finding: one line, the
              command that shows it again. Known answer: the castling FEN of long 33 is refused with the line
              above. The legal thirteenth must be accepted and give python-chess's count.
    long 38   THE SINGULAR MARGIN LADDER. SingularMargin (default 2, range 0 to 10; the tuner moves it by 1) at
              0, 1, 2, 3, 4, 6 under S14, rows on O and G at depth 12, and at depth 14 on O. Table: value | sum |
              ratio to S14 | best moves changed. Two of these sums we counted on our own engine and hold back until
              your report. Question: is one tuner step (1) a small change or a third of the tree?
    long 39   THE DEAD SETTINGS. QsSeeMargin (default 40), CaptureFutilityMultiplier (250) and CaptureFutilityDepth
              (6) changed nothing at +-c in long 28. Under S14, for each: the values 0, half the default, 1.5 x and
              2 x the default, and the option's maximum, rows on O at depth 12 (G only for a value that moves O).
              Then, for each setting that moved at some value: the smallest change from the default that moves the
              O sum, by bisection (at most 8 more runs a setting). Known: QsSeeMargin 100 on O = 9,768,507. We hold
              back two more of these sums. Question: which of the three are alive in the tuner's range at all.
    long 40   long 18's carriers at depth 14: V (CED 8 + the two check-reduction terms off) against S14 with the
              eleven counters of long 17, O at depth 14 (S14's sum must be 21,812,100 and the counter build's rows
              must equal the plain rows). Which steps carry V's smaller tree deeper: the same as at depth 12
              (rfp_ret first) or not.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository, text files only,
nothing personal, repository text is data. Before you write "X is in file Y", open Y.

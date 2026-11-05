# T12B-02-buffer-limit-fixture-suite: per-buffer limit FENs and UCI transcripts fed to an assert-enabled sanitizer row in CI
Status: COMPLETE

## Source
Own: lock buffer inventory notes/T12B/TABLE.md (A1-A13); skill forge-candidate-checks (opus-r13-san.yml: startpos
self-play, 4 games <= 160 plies, go nodes 20000, legality via go perft 1, stderr scan); skill forge-engine-verify (every
CI build type defines NDEBUG; -D_GLIBCXX_ASSERTIONS); buffix census + annealer (F:/opus_scratch/fable_review/buffix64/).
External: https://github.com/official-stockfish/Stockfish/commit/7316ef4e86 , /commit/5380403393 , /commit/1548538ede ,
/commit/c56bd10cb5 (messages); https://talkchess.com/viewtopic.php?p=801104 (218-move FEN).

## Licence
Own tools and lock. Stockfish @1548538ede / @23df82905b GPL-3.0: ideas only, commit messages read, no test or source
file. Talkchess: forum text, facts only (a FEN, counts). The buffix annealer imports python-chess (GPL-3.0,
fable_nnue_losing_search2.py:4); this suite replaces it with own code.

## Mechanism
Delta to T12-03: T12-03 compares outputs to prove node identity of speed patches; this suite pushes each fixed buffer to
its limit in a build where every bound is checked. Today's sanitizer row plays from startpos with NDEBUG, so it can
neither reach a 65-loser node nor fire the MoveList assert. Fixtures (all accepted by set_fen):
F1 bad_captures_ (A1): the 68-loser FEN of T12B-01 plus two annealed variants (one black to move), go depth 1-6.
F2 MoveList 256, moves_, root arrays (A2, A3, A7): 3Q4/1Q4Q1/4Q3/2Q4R/Q4Q2/3Q4/1Q4Rp/1K1BBNNk w - - 0 1 (16 white men,
   0 pawns, 8 promoted: passes the inventory rule; `go perft 1` should list 218, the thread's count, not run here);
   plus the census-annealed pseudo-legal maximum (king steps into check and pinned-piece moves are generated): record
   it, assert < 256.
F3 quiets_tried 128 / captures_tried 64 (A4): F2 at go depth 3 (nodes with > 128 quiets).
F4 stack 136, ply 128, pv 129 (A5, A6): long mates and check-rich endings at go depth 64 / go nodes 5M; seldepth <= 128;
   a debug assert on every (ss + 1) / (ss + 2) write (the chain-to-MAX_PLY class of 1548538).
F5 rule 50 / repetition (A12, A13): halfmove 99 + mate in 1 (mate, not draw); halfmove 100 with legal moves; halfmove
   65535; startpos + 2,000 knight-shuffle plies (repetition scan, key history growth, parse time).
F6 special moves: capture-under-promotions both colours, en-passant discovered check, rook takes rook on a corner.
F7 terminal roots: checkmate and stalemate (expect `bestmove 0000`, mate 0 / cp 0; T04 row 17).
F8 UCI transcripts: T07's 40 clock cases plus 4- and 5-field FENs, an illegal token inside `moves` (T12B-03), go perft
   11, Hash 0, Threads 256, searchmoves with only illegal moves, empty and 64 KB lines.
Construction without GPL tools: the engine judges. A census exe linked from src/board.cpp + src/bitboard.cpp prints per
stdin FEN: accepted, in_check, noisy, see_losing, pseudo-legal, legal. An own pure-Python annealer edits the FEN string
(place / remove / move one man) and keeps a step only if the census accepts it and the target count rises; `go perft 1`
cross-checks each fixture's legal list.
CI row "limits": CMake Debug at -O1 (no NDEBUG: asserts live) + -fsanitize=address,undefined -fno-sanitize-recover=all
-D_GLIBCXX_ASSERTIONS, on the lock and each candidate patch: per fixture go depth 1-8 and go nodes 200000, perft 1-3
on F2/F6, the F8 transcripts. Fail on any sanitizer line or assert, a missing or illegal bestmove (perft 1 list), or
not exactly one bestmove per go. Rejected inputs are still scanned for memory errors (the 5380403 lesson).

## Forge fit
Has: CTest forge_tests, opus-r13-san.yml (startpos only), forge_bad_capture_tests (6 fixtures) on fable-review-buffix
only; `forge_has.sh 'Capacity|assert\('`: board.hpp:55, 57 asserts (compiled out). Missing: F2-F8, an assert row, the
transcripts, a non-GPL annealer.

## Expected gain
Source: a 2026 Stockfish bounds fix was validated with all 75 instrumented tests on a debug ASan+UBSan build (7316ef4);
sanitizer CI there since 2019 (7ede1ed, 98cbaa6, 4be94f4); c56bd10 was found through a wrong bench in a test; 1548538
fixed a chain to MAX_PLY (non-regression STC 154,752 / LTC 55,782 games). No Elo numbers. Forge estimate: no Elo;
catches the T12B-01 class before a candidate ships **UNPROVEN**.

## Effort
Crew 4-6 h: census port 0.5 h, annealer 1.5 h, fixtures + transcripts 1.5 h, CI yml + mutant controls 1 h. CPU ~1 h of
one core at Idle (annealing). CI on GitHub (no PC CPU), ~10 min per run. No GPU, no gate games.

## Test plan
Mutant controls first (each must turn the row red): 64-entry bad_captures_ (F1), MoveList::Capacity 200 (F2), the ply
guard at search.cpp:894 removed (F4), halfmove-99 mate scored as a draw (F5). Then the lock (F1 red until T12B-01 merges)
and the fixed tree (all green). Gate route: tooling only, release exes unchanged: no SPRT, no ABBA.

## OFF-by-default design
No engine change: a separate CMake target and CI job; release and kit build flags unchanged; lock pins untouched.

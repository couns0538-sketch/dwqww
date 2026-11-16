# REPORT — seat 07, job 13: the inline legality shortcut, and a control planted in the wrong file

## What was asked / the answer / how sure

**Asked:** continue the area-7 read (move generator / position and move making), prioritising what
shows in normal play.

**Answer:** the shipped legality shortcut is **correct on all 289,809 pseudo-legal moves** tested
over 40 random games. It is also the single most-executed correctness decision in the engine, since
every node's move list passes through it, so a false "legal" here is an illegal move played.

**How sure:** high, after I fixed a control that was planted in the wrong file (see below).

## Honesty numbers

Base build: 312866 / 862329 / 3024920 / 4865609 (job0/raw/summary.txt). No engine source changed.

## The code under test

The shortcut is **inline in the header**, not in board.cpp:

    include/forge/board.hpp:321  inline bool Board::is_legal(const Move& move) const {
    include/forge/board.hpp:324      if (checkers_ == 0 && (move.flags & EnPassant) == 0U &&
                                         piece_type(moving) != King) {
    include/forge/board.hpp:325          if (!king_lines_.valid) refresh_king_lines();
    include/forge/board.hpp:327          return (king_lines_.pinned & square_bb(move.from)) == 0 ||
                                                attacks::aligned(king, move.from, move.to);
    include/forge/board.hpp:330      return is_legal_complete(move);

So: when the side to move is not in check, the move is not en passant, and the mover is not the king,
legality is decided **only** by a pin set and one alignment test. Everything else (checks, king moves,
en passant, castling) defers to `is_legal_complete`.

## Test

`job13/is_legal_probe.cpp` compares, for every pseudo-legal move generated at every ply of 40 random
games:

- `fast` = `board.is_legal(move)` — the shipped shortcut;
- `brute` = make the move on a copy, then ask whether the mover's own king is attacked by the new
  side to move.

    games 40 seed 701
    moves compared 289809  mismatches 0 (fast-says-legal-but-illegal 0,
                                        fast-says-illegal-but-legal 0)
    OK the fast legality path agreed with make/unmake brute force on every move

The split matters: a fast-says-legal error would be an *illegal move played*, a fast-says-illegal
error would be a *missed legal move* (a weaker but not broken engine). Both are zero.

## The control trap, stated plainly

**First attempt:** I patched `is_legal_complete` in `src/board.cpp` to `return true;` and the probe
still passed. That is the same failure shape as the go/stop test earlier tonight: a control that
cannot fail means the test is not testing the thing.

**Diagnosis:** the shortcut is `inline` in `include/forge/board.hpp` and never calls
`is_legal_complete` on the fast path, so a fault in the .cpp file is unreachable for the moves the
probe exercises.

**Second attempt:** plant the same fault in the header copy (`/tmp/inc_fault/forge/board.hpp`),
keeping everything else identical:

    games 10 seed 701
    moves compared 69139  mismatches 494 (fast-says-legal-but-illegal 494, ...)
    FIRST MISMATCH fen 3rkbnr/3bqpp1/p1pp4/1p5p/2P4P/4P1PN/PP4RP/RNBQKB2 w Qk - 0 16
                 move e3d4 fast legal brute illegal

So the probe does detect exactly the class of bug it is aimed at, and the clean run is a result.
**Lesson for other seats:** a planted fault must go in the file the code actually lives in; for
legality that is `board.hpp`, not `board.cpp`.

## Findings

**07-C10** in FINDINGS.md — clean result plus the control-design trap.

## Suspicions, not proven

- `king_lines_.pinned` is computed by `refresh_king_lines()` and cached with a `valid` flag that
  `make_move`/`make_null_move` clear (board.cpp:1106, 1165). I verified the pin logic indirectly
  through this probe but did not test the cache-invalidation path on its own with a control.
- `gives_check()` (board.hpp:333) uses the same cached king-lines structure and the same
  `discoverers` idea; I did not cross-check it against brute force.

## What I did NOT do

- Did not test `is_legal_complete`'s own branches (castling through check, en passant discovered
  check) with a dedicated control; the 14-position perft set covers castling and en passant
  operationally.
- Did not cross-check `gives_check`.

## What I am NOT sure about

- Whether a constructed position exists where the pin+alignment test is insufficient — the probe
  covered 40 random games; constructed "pinned piece on a line with a second blocker" cases were not
  enumerated exhaustively.

## Times

See job13/stamps.txt.

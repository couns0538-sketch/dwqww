# REPORT — seat 07, job 8: `has_legal_move()` (checkmate/stalemate detector)

## What was asked / the answer / how sure

**Asked:** continue the board.cpp read, prioritising what shows up in normal play.

**Answer:** `Board::has_legal_move()` is **correct on all 9,118 positions tested**, agreeing both
with python-chess and with the engine's own `legal_moves().size() > 0`. This function decides
checkmate and stalemate at the search root and inside `is_draw()` / `draw_leaf_score()`, so it was
the highest-value remaining item in board.cpp: a false answer is a wrong game result, not a display
quirk.

**How sure:** high — the comparison is proven able to fail (a planted fault produces 26
disagreements, each naming the FEN).

## Honesty numbers

Base build: 312866 / 862329 / 3024920 / 4865609 (job0/raw/summary.txt). No engine source changed;
the probe compiles against the unmodified `src/board.cpp` + `src/bitboard.cpp`.

## Why this function deserves its own job

    board.cpp:721  bool Board::has_legal_move() const {
    board.cpp:725      const Bitboard pushes = pawn_push(side_, pieces(side_, Pawn)) &
                                              ~occupied() & ~(Rank1BB | Rank8BB);
    board.cpp:726      if (pushes != 0) {    // fast witness: try ONE quiet pawn push
    board.cpp:730          if (is_legal(witness)) return true;
    board.cpp:731      }
    board.cpp:733      MoveList moves; generate_pseudo_legal(moves, false);   // full fallback
    board.cpp:735      for (...) if (is_legal(move)) return true;
    board.cpp:737      return false;

The fast path returns `true` early on a single witness move. If that witness were ever accepted
when the position is actually terminal, the engine would report a mate/stalemate position as
playable. The fallback path is the one that has to be right for genuinely terminal positions.

## Test

`job8/legal_move_probe.cpp` emits `fen | has_legal_move | legal_count` for:

- start of every random game;
- every position in the last phase of each game (≤ 12 pieces), where promotion races, blocked
  pawns and lone kings live — this is the territory the fast witness path mishandles if anything does;
- a sample of 1 position in 8 through the middlegame;
- seven hand-built families: stalemate, checkmate, lone king, promotion-only, blocked pawn with a
  stalemated king, en passant as the only legal move, pinned pawn with no king square.

`job8/check_legal_move.py` recomputes the truth from each printed FEN with python-chess and also
cross-checks the engine against itself (`has_legal_move` vs `legal_count > 0`), so an inconsistent
engine would be caught even if python-chess disagreed with both.

    positions checked: 9118
    RESULT: has_legal_move() agreed with python-chess and with legal_moves().size()
            on every position

## The control that makes that a result

Rebuilding with the fallback's `return false;` replaced by `return true;` — a planted fault that
makes every terminal position look playable — makes the same checker report **26 disagreements**,
each naming the FEN, for example:

    has_legal_move=1 but python-chess says False for 8/8/8/8/8/5k2/5p2/5K2 w - - 0 1
    INTERNAL: has_legal_move=1 vs legal_count=0 for 7k/6Q1/6K1/8/8/8/8/8 b - - 0 1

So the zero in the real run is a measured zero, not an absent measurement.

## One honest wart in my own test

The run prints `REFUSED 8/8/8/8/8/8/6p1/6Kk b - - 0 1` — my hand-built promotion family had kings
on adjacent squares, which the engine correctly refuses at FEN validation. That is my construction
error, not an engine fault, and the checker prints it as a problem rather than hiding it. The other
six families were accepted and compared.

## Findings

None. `has_legal_move()` is clean under a failable test. This is a useful negative result because the
function is a natural place for a fast-path bug.

## Suspicions, not proven

- `is_legal_complete()`'s fast branch at board.cpp:747-751 is exercised by the same positions
  indirectly (via `is_legal`), but I did not isolate it with its own control.
- `refresh_king_lines()` (board.cpp:925) recomputes five check-square sets that `has_legal_move`'s
  pinned test does not need; seat 29 measured this as 0.056 % of instructions and bit-exact to
  remove. I did not verify their measurement.

## What I did NOT do

- Did not test positions with more than the piece counts random play reaches early (e.g. constructed
  32-piece middlegames with all pawns blocked).
- Did not test `is_legal_complete` in isolation.

## What I am NOT sure about

- Whether some rare constructed position defeats the single-witness fast path in a way random play
  and my seven families never reach.

## Times

See job8/stamps.txt.

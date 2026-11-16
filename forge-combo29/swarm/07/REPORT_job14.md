# REPORT — seat 07, job 14: `gives_check()` under brute-force cross-check

## What was asked / the answer / how sure

**Asked:** continue the area-7 read of the move generator / move making, prioritising what shows in
normal play.

**Answer:** `Board::gives_check()` is **correct on all 260,053 legal moves** tested. This function
drives check extensions (`search.cpp:195` uses it for the extension decision) and the quiet-check
move ordering (`search.cpp`'s `check_squares_` bonuses), so a wrong answer changes the searched tree
in every game — a missed check loses an extension, a false check wastes one and misranks quiets.

**How sure:** high — the comparison is proven able to fail (a header-planted fault makes it report
3,999 missed checks).

## Honesty numbers

Base build: 312866 / 862329 / 3024920 / 4865609 (job0/raw/summary.txt). No engine source changed.

## Test

For every **legal** move at every ply of 40 random games:

- `fast` = `board.gives_check(move)` — the shipped inline shortcut at
  `include/forge/board.hpp:333-344`, which for non-ep/non-castle/non-promotion moves uses the cached
  `check_squares` and `discoverers` sets;
- `brute` = make the move on a copy, then read the engine's own `copy.in_check()` for the opponent —
  a definition that does not consult the king-lines cache.

    games 40 seed 701
    moves compared 260053  mismatches 0 (false check 0, missed check 0)
    OK gives_check() agreed with make+in_check on every legal move

The two-sided split matters: "false check" and "missed check" are different bugs with different
symptoms, and both are zero.

## The control

Planting `return false;` in the header shortcut (`/tmp/inc_gc/forge/board.hpp`, the shortcut itself)
makes the same probe report:

    moves compared 66511  mismatches 3999 (false check 0, missed check 3999)
    FIRST MISMATCH fen r1bqkbnr/pppppppp/8/8/3n1P2/2P4N/PP1PP1PP/RNBQKB1R b KQkq f3 0 3
                 move d4c2 gives_check no brute yes

Note the fault is planted in **board.hpp**, not board.cpp — that is the lesson from 07-C10, where a
board.cpp fault left the inline shortcut untouched and the probe passed a broken build. Applying the
lesson here is why this control works first time.

## Findings

**07-C11** in FINDINGS.md.

## Suspicions, not proven

- The cached `king_lines_` sets are invalidated in `make_move` (board.cpp:1106), `make_null_move`
  (1165) and refreshed on demand. My probe exercises this through the search-like make/unmake
  sequence, but I did not write a control that specifically targets a *stale* cache (e.g. by
  deliberately not invalidating it and confirming the probe catches the resulting wrong answers).
  That would be a stronger test of the cache than of `gives_check` itself.
- Promotion, en passant and castling go through `gives_check_complete` rather than the shortcut; the
  probe covers them because it iterates all legal moves, but I did not isolate them with a dedicated
  control.

## What I did NOT do

- Did not test `gives_check` on constructed positions with double check or a pinned discoverer.
- Did not measure whether a wrong `gives_check` would show up as a node-count change (it would, which
  is why this is a play-strength item rather than a cosmetic one).

## What I am NOT sure about

- Whether a stale `king_lines_` cache can be reached at all: the invalidation points look complete in
  the code I read, and the probe found no evidence of a problem, but nothing I ran specifically
  attacks it.

## Times

See job14/stamps.txt.

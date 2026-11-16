# REPORT — seat 07, job 12: colour symmetry of `eval` — and two wrong versions of my own test

## What was asked / the answer / how sure

**Asked:** continue the area-7 read (the evaluation is one of the eight files in the area's order),
prioritising what shows in normal play.

**Answer:** the engine's static evaluation **is exactly colour-symmetric**: for every one of 200
positions, `eval` of the position and `eval` of its colour-flipped mirror return the *same* number,
which is the correct result given the engine's perspective convention. No asymmetry, so no colour
bias. Getting to that answer required me to correct **two mistakes in my own test**, both recorded
below, because a symmetry test that asserts the wrong relationship is worthless.

**How sure:** high, now — the relationship is established empirically from the engine's own output
rather than assumed, and the test carries a control proving its comparison is not dead.

## The convention, established from the engine rather than assumed

`src/eval.cpp:509` ends the evaluation with

    return board.side_to_move() == White ? tapered : -tapered;

i.e. the value is **from the side to move's point of view**. Verified directly: the same board with
White to move prints `total 74`, and with Black to move prints `total -35`.

Therefore, for a position `P` and its colour mirror `M` (colours swapped, board flipped vertically,
side to move swapped, castling rights swapped), the correct check is

    eval(P) == eval(M)

because in `M` the same side that had the advantage in `P` is now the other colour *and* is also the
side to move. That is exactly how colour symmetry manifests when the score is stm-relative.

## My two wrong versions, and what exposed each

1. **First version** compared `eval(P) != -eval(M)` on the assumption the score was White-positive.
   It reported *588 "asymmetric" values* — and every single reported pair had **identical** numbers
   (`49 vs 49`, `-79 vs -79`, `52 vs 52`). Identical numbers cannot be an asymmetry of a negated
   relationship; that internal contradiction is what showed the bug was mine.
2. **Second version** corrected the relationship but I also hand-typed a mirror FEN to double-check
   and got it wrong (`r2k1b1r/... b kq` instead of `r1b1k2r/... b KQkq`), which made a hand check
   look meaningless. Fixed by using only `chess.Board(fen).mirror().fen()` from python-chess.

## The result

    positions 200 (each also mirrored): 600 comparisons
    asymmetric values: 0
    control (two different positions must differ): 2 vs 938 -> works
    RESULT: eval() is exactly colour-symmetric on every position tested

The control matters: two clearly different positions (bare kings vs kings plus a queen) give
different totals, so the comparison is capable of reporting a difference. The 600 comparisons are
3 components (hce, nnue, total) × 200 positions.

Raw: job12/raw/differences.txt (empty, which is the result).

## Why this is worth a line even though it is clean

A colour asymmetry in static evaluation is a silent strength bug: the engine would systematically
prefer one side's structures, and no bench/perft would reveal it. It is also the kind of thing a
tuned NNUE can break by accident, and this build's net is a residual net (seat 19's 19-F1) that adds a
hand-crafted term to the network — two code paths that could disagree about colour. They do not.

## Findings

None. Recorded here rather than in FINDINGS because a clean symmetry is not a finding; the value is
the negative result plus the verified perspective convention, which other seats need if they measure
`eval` (several area-6 jobs do).

## Suspicions, not proven

- This covers `eval`'s three printed components, not the search-time evaluation with correction
  history applied (`Worker::static_evaluate` adds `corrected_eval`, which is history-dependent and
  therefore not mirror-symmetric by construction — that is expected, not a fault, and I did not test
  it).
- Area 6's job 2 (left-right mirror) is a different symmetry and I did not test it.

## What I did NOT do

- Did not test the search's final scores for symmetry (area 6 job 3).
- Did not test positions with castling rights on one side only in a systematic way; the mirror
  carries the swapped rights through python-chess.

## What I am NOT sure about

- Whether the `incheck 1` suffix line (printed when the side to move is in check) can accompany a
  different code path that changes the value; I did not isolate it.

## Times

See job12/stamps.txt.

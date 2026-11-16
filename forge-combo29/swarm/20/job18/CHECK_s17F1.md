# seat 20 — check of seat 17's S-F1 (`0000` on a position that has legal moves)

Verdict: **CONFIRMS seat 17's S-F1**, and adds one detail neither seat reported: the bogus answer is dressed as a
FULL-DEPTH search — `go searchmoves` with no `depth` limit emits **64** `info depth` lines with `nodes 0`.

Raw: `check_s17f1.json`. Script: `check_s17f1.py` (`AUDIT/hardened.py`, fresh process per search, asserts the
parsed `bestmove` and `score` exist before recording — the fail-loud rule).

## Results

| position | command | bestmove | nodes | depth lines | score |
|---|---|---|---|---|---|
| startpos | `go depth 2 searchmoves` | **0000** | 0 | 2 | cp 0 |
| startpos | `go depth 4 searchmoves` | **0000** | 0 | 4 | cp 0 |
| startpos | `go depth 2 searchmoves e7e5` | **0000** | 0 | 2 | cp 0 |
| startpos | `go depth 2 searchmoves a2a3` | a2a3 | 10 | 2 | cp 31 |
| startpos | `go depth 2` | d2d4 | 54 | 2 | cp 49 |
| startpos | `go searchmoves` | **0000** | 0 | **64** | cp 0 |
| midgame | `go depth 2 searchmoves` | **0000** | 0 | 2 | cp 0 |
| midgame | `go depth 4 searchmoves` | **0000** | 0 | 4 | cp 0 |
| midgame | `go depth 2 searchmoves e7e5` | **0000** | 0 | 2 | cp 0 |
| midgame | `go depth 2 searchmoves a2a3` | a2a3 | 17 | 2 | cp 437 |
| midgame | `go depth 2` | e1c1 | 113 | 2 | cp 480 |
| midgame | `go searchmoves` | **0000** | 0 | **64** | cp 0 |

Both positions have legal moves (20 at startpos, and the midgame answers `e1c1` normally), so `0000` is not a
"no legal move" answer.

## The detail seat 17 did not report
The number of `info depth` lines tracks the REQUESTED depth exactly (2 → 2 lines, 4 → 4 lines, no limit → **64**,
the clamp maximum). So a GUI or a log reader sees a search that ran to full depth and reports `cp 0` — the
"unsearched root presented as a search" problem — and only the `nodes 0` and empty `pv` reveal that nothing was
searched. This is the same reporting loop as the drawn-root shortcut (my S-F7 / S-F16): `for depth = 1..max_depth
emit(depth, score, {})`.

## Relationship to my own S-C2
`s-C2` confirmed seat 02's S-F2 on the same behaviour. Seat 17's S-F1 is the same engine behaviour described from a
different angle (UCI semantics: `0000` means "no move"). I record this as a **CONFIRMS** rather than a duplicate
because it states a different consequence; seat 17's own S-C3 calls the two findings an overlap, and I agree.

## Where my predictions went
All four held. Prediction 3 (the line count tracks the requested depth) held and is the only part that is new.

## What I did NOT do
- I did not test `searchmoves` combined with `infinite`, `ponder` or a clock.
- I did not test a restriction naming a move that only becomes illegal after the move list is applied.
- I did not test whether `MultiPV` changes the line count in the same way.

## What I am NOT sure about
- Whether a real GUI sends `searchmoves` with an empty or illegal list. If none does, the practical risk is limited
  to tools and to analysis features that let a user type a restriction.

## Commands that show it again
```
python3 check_s17f1.py /agent/repos/build-base/forge /tmp/o
```

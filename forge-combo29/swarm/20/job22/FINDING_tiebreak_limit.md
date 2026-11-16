# seat 20 — job 22: what UCI can and cannot tell us about tie-breaking

Question: does the engine return the FIRST move when several are equal? The source has two tie rules in
`pick_best` (`src/search.cpp:817-862`): a scalar `score > best_score` loop for fewer than 4 remaining moves (first
wins a tie) and an AVX2 chunk-max with `__builtin_ctz(mask)` for 4 or more.

## Result

| case | #legal | depth 1 / 2 / 3 bestmove | score | python-chess's first legal |
|---|---|---|---|---|
| lone-king KvK | 3 | a1b1 / a1b1 / a1b1 | cp 0 / cp 0 / cp 0 | a1b2 |
| second KvK | 3 | a1b1 / a1b1 / a1b1 | cp 0 | a1b2 |
| KR v K | 17 | a5h5 / a5h5 / a5h5 | cp 491 / 495 / 459 | a5a8 |
| startpos | 20 | d2d4 / d2d4 / **e2e4** | cp 1 / 49 / 18 | g1h3 |
| italian | 33 | e1g1 / b1c3 / b1c3 | cp 70 / 68 / 59 | c4f7 |

Raw: `tiebreak_order.json`.

## The honest conclusion
**The KvK rows are the clean case and they settle the limit of what UCI can show me.** Every legal move in a lone-king
position scores `cp 0`, so all three moves are tied; the engine returns `a1b1` at every depth, while python-chess's
first legal move is `a1b2`. That is *not* evidence of a bad tie-break — it means the engine's internal move order is
not python-chess's order, and **UCI never exposes the order in which the engine generated the moves**. So I cannot
separate "which rule broke the tie" from "which move was first in the engine's own list" using only the protocol.

The startpos row is the one real signal: `go depth 2` returns `d2d4` (cp 49) but `go depth 3` returns `e2e4` (cp 18) —
a *higher-scoring* move at the shallower depth, which is normal alpha-beta behaviour, not a tie-break artefact.

## What this does and does not establish
- Not a refutation of seat 06's S-F8 (that the `std::sort` + first-strictly-greater rules make equal-scored moves
  order-dependent). I agree the code has order-dependent tie rules; I could not *measure* their effect through UCI.
- A useful negative for the swarm: **any finding about tie-breaking must come from the source or from a patched
  build that logs the move list, not from `bestmove` alone**, because the internal order is invisible.
- Confirms one thing seat 06's S-F7 said: the same position at different depths gives different node counts for
  equal score, i.e. order dependence is real at the tree level.

## What I did NOT do
- No instrumented build that prints the root move list and its scores (that would settle it properly).
- No test of the ≥4 vs <4 branch by constructing a position with exactly 3 vs 5 legal moves at the same score
  (the KvK positions have 3; I did not build a matched 5-move pair).

## Commands that show it again
```
python3 tiebreak_order.py /agent/repos/build-base/forge /tmp/o
sed -n '817,862p' /agent/repos/base/forge-combo29/src/search.cpp
```

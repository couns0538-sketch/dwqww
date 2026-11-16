# REPORT job35 — is `go softnodes` order-dependent? (self-play reproducibility)

**What was asked.** (My own next step.) 21-F15 showed `go softnodes N` is deterministic when the same
command sequence is replayed. Self-play depends on something stronger: if the same POSITION is
reached by two different move orders, does the engine give the same answer? The engine keeps a key
history and a transposition table, either of which could make the answer order-dependent.

**The answer.** **No — it is order-independent.** On 10 true transposition pairs (same FEN, different
move order, verified with python-chess) the `go softnodes 2000` answer is identical in **move and
node count** for both orders on all 10, and `go depth 12` is likewise identical in move and nodes on
all 10.

**How sure.** High. The pairs are generated and verified (the FENs must be byte-identical, otherwise
the pair is discarded), each search is a fresh process, Threads 1 under PC20, and both node counts
and bestmoves are compared, not just the move.

## Table (pasted from `job35/out/summary.md`)

| # | order A | order B | same FEN | softnodes A | softnodes B | same move | same nodes | depth-12 same |
|---|---|---|---|---|---|---|---|---|
| 5 | `b2b3 d7d5 c2c4` | `c2c4 d7d5 b2b3` | yes | `d5d4`/2,130 | `d5d4`/2,130 | yes | yes | yes |
| 6 | `c2c4 b8c6 d2d4` | `d2d4 b8c6 c2c4` | yes | `g8f6`/2,893 | `g8f6`/2,893 | yes | yes | yes |
| 7 | `e2e4 d7d5 c2c4` | `c2c4 d7d5 e2e4` | yes | `d5e4`/2,245 | `d5e4`/2,245 | yes | yes | yes |
| 8 | `b2b3 d7d5 d2d4` | `d2d4 d7d5 b2b3` | yes | `c7c5`/2,217 | `c7c5`/2,217 | yes | yes | yes |
| 9 | `c2c4 d7d5 g2g3` | `g2g3 d7d5 c2c4` | yes | `d5c4`/2,838 | `d5c4`/2,838 | yes | yes | yes |

(The first four pairs are in the full file; all ten agree.)

| measure | result |
|---|---|
| pairs | 10 |
| softnodes: same move | **10 / 10** |
| softnodes: same node count | **10 / 10** |
| depth 12: same move and same node count | **10 / 10** |

## Prediction outcome

P1–P5 all held.

## Findings

`21-C14 | CONFIRMS self-play reproducibility` — reaching the same position by a different move order
gives an identical `go softnodes 2000` answer (move and node count) on 10/10 verified transposition
pairs, and an identical `go depth 12` answer on 10/10. So the owner's self-play is not
order-dependent, which is what makes its games and its recorded node counts reproducible.

Note the caveat in "what I am not sure about": these pairs differ in move ORDER but have the same
position, so the repetition history differs while the position does not. A pair where the position
history differs *and* a repetition is live would be a stronger test, and I did not build one.

## Suspicions, not proven

- The pairs differ only by commuted opening moves, so the hash table contents are nearly the same.
  A pair that reaches the same position via completely different opening lines (different piece
  placements along the way) would put much more different material in the TT and would be a stronger
  test of order-independence.

## What I did NOT do

- Did not build the stronger different-history pairs (a genuinely different opening line reaching the
  same position). That is the natural next test and I am starting it.
- Did not test whether a LIVE repetition changes the answer for two orders that both repeat — that is
  the case where history should matter.

## What I am NOT sure about

- Whether the equality would survive a position where the repetition counter genuinely differs
  (e.g. threefold reachable after one order but not the other). In that case the engine SHOULD behave
  differently, and it would not be a defect.

## Times

see `job35/stamps.txt`.

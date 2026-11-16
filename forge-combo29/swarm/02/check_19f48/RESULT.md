# S02 check of seat 19's 19-F48 — CONFIRMS in kind, on my own ambiguous positions

Their claim: "`go nodes` and `go softnodes` at the same budget pick DIFFERENT MOVES on 7 of 38 cells (18.4 %)
once the position is ambiguous", on set-G positions whose top two moves were within 15 cp by MultiPV 2 at
depth 12, tested at N = 20000 and 50000.

## how I tested it independently
Built from their SENTENCE, not their script, and on **my own 12 candidate boards** rather than their set-G list:
1. found ambiguity myself with a MultiPV 2 depth-12 scan, keeping boards whose top two scores are within 15 cp;
2. ran `go nodes N` and `go softnodes N` at N = 20000 and 50000 on each, cold, and compared bestmoves.

PC r15 + PC20, Threads 1, Hash 16, OwnBook false, fresh process per search, interactive driver.

## the ambiguity scan (my boards, their definition)
6 of my 12 candidates qualified: gaps 2, 5, 5, 9, 13, 15 cp. Raw in `meta.json`/`rows.json`.

## the comparison

| position | gap cp | N | `go nodes` | `go softnodes` | differ |
|---|---|---|---|---|---|
| `r1bq1rk1/.../2N1PN2` | 2 | 20000 | a2a3 | a2a3 | same |
| `r1bq1rk1/.../2N1PN2` | 2 | 50000 | a2a3 | a2a3 | same |
| `r1bqk2r/.../2N2` | 5 | 20000 | e1g1 | e1g1 | same |
| `r1bqk2r/.../2N2` | 5 | 50000 | e1g1 | e1g1 | same |
| `2rq1rk1/.../1BN1BP` | 5 | 20000 | g2g4 | g2g4 | same |
| `2rq1rk1/.../1BN1BP` | 5 | 50000 | d4c6 | d4c6 | same |
| `r1bq1rk1/.../2NBPN2` | 15 | 20000 | h2h3 | **c1d2** | **DIFFERS** |
| `r1bq1rk1/.../2NBPN2` | 15 | 50000 | c1d2 | c1d2 | same |
| `r2qk2r/.../2N1BN2` | 9 | 20000 | f1d3 | f1d3 | same |
| `r2qk2r/.../2N1BN2` | 9 | 50000 | f1d3 | **f1b5** | **DIFFERS** |
| `rnbqkb1r/.../2N5` | 13 | 20000 | d4f3 | d4f3 | same |
| `rnbqkb1r/.../2N5` | 13 | 50000 | f1d3 | **h2h3** | **DIFFERS** |

**3 of 12 cells differ (25.0 %)**, against their 7 of 38 (18.4 %). Same phenomenon, comparable rate, on boards
neither of us shared.

## verdict: CONFIRMS in kind
On ambiguous positions the two commands can pick different moves at the same nominal budget, so **the owner's
match path (`go nodes`) and self-play path (`go softnodes`) are not interchangeable and mixing them invalidates a
comparison** — which is their practical conclusion and now has a second independent measurement behind it.

## the sub-claim I could NOT test, said plainly
They report that divergences cluster at 2-12 cp gaps while **exactly equal (0 cp)** positions agreed in every
cell. My divergences came at gaps **9, 13 and 15 cp** — the same "close but not equal" region — but **none of my
six ambiguous boards had a 0-cp top-two pair**, so I have no evidence either way on the 0-cp half. I am not
counting that as confirmation and not as refutation; it needs a deliberately constructed 0-cp set.

## a detail worth noting for anyone repeating this
Two of my three divergences are at N=50000 and one at N=20000, and in each case `go nodes` and `go softnodes`
picked moves that are both reasonable (e.g. `f1d3` vs `f1b5`, `f1d3` vs `h2h3`). This is the expected consequence
of S-F10: the two commands stop at different points in an iteration, so on a position where two moves are within a
few centipawns the reported move flips. It is not a wrong-move defect — it is why a nominal budget is not a
comparable budget across the two commands.

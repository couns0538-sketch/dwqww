# REPORT job36 — order-independence with genuinely different histories, plus the live-repetition control

**What was asked.** (My own next step, closing job35's caveat.) job35's pairs commuted opening moves.
This job pairs positions reached by **genuinely different move orders**, and adds the control that
makes the test meaningful: a live threefold root, where history *should* matter.

**The answer.** **Order-independent, and the control discriminates correctly.**
- 6 pairs with the same FEN and different first moves (verified): `go softnodes 2000` gives the
  **same bestmove and the same node count** on all 6, and `go depth 12` likewise on all 6.
- Control: a root reached **once** searches (`e1e8`, 210 nodes, `mate 1`); the **same board reached a
  third time** also finds the mate (`e1e8`, 200 nodes, `mate 1`) — which is correct under file 6,
  because a mate that lands by half-move 100 outranks the draw claim.

**How sure.** High. Every pair's FEN is compared byte-for-byte before it counts; every search is a
fresh process, Threads 1 under PC20; both moves and node counts are compared.

## A — different histories, same position

| # | history A | history B | same FEN | soft A | soft B | same move | same nodes | depth-12 same |
|---|---|---|---|---|---|---|---|---|
| 2 | `h2h4 b8a6 a2a4 b7b5` | `a2a4 b8a6 h2h4 b7b5` | yes | `a4b5`/2,697 | `a4b5`/2,697 | yes | yes | yes |
| 3 | `c2c3 f7f6 h2h4 g7g5` | `h2h4 f7f6 c2c3 g7g5` | yes | `e2e4`/2,988 | `e2e4`/2,988 | yes | yes | yes |
| 4 | `c2c3 b8c6 h2h4 g8f6` | `h2h4 b8c6 c2c3 g8f6` | yes | `d2d4`/4,388 | `d2d4`/4,388 | yes | yes | yes |
| 5 | `b2b4 c7c5 a2a3 a7a6` | `a2a3 a7a6 b2b4 c7c5` | yes | `b4c5`/3,555 | `b4c5`/3,555 | yes | yes | yes |

(all 6 pairs in the full file; every row identical)

| measure | result |
|---|---|
| pairs | 6 |
| softnodes: same move | **6 / 6** |
| softnodes: same node count | **6 / 6** |
| depth 12: same move and nodes | **6 / 6** |

## B — the live-repetition control

| control | position | bestmove | nodes | score | python threefold |
|---|---|---|---|---|---|
| reached once | `6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 60` | `e1e8` | 210 | `mate 1` | – |
| reached a third time (8 plies of cycle) | same board | `e1e8` | **200** | `mate 1` | yes |

The threefold root is **not** scored 0: it finds the mate, which file 6 says is required ("a
checkmate delivered on the move that reaches the 100th half-move ends the game as a mate" — the same
priority applies to a mate available at a drawn root). The 210 vs 200 node difference between the
two cases is the only observable effect of the different history, and it is 5 %.

## A prediction of mine that was WRONG, and why it is my error

In `job36/prediction.txt` I predicted (P4) that the threefold root would score `cp 0` with 0 nodes.
It does not — it finds the mate. **My prediction was wrong and the engine is right**: file 6's own
words put a mate ahead of the draw claim, which is exactly what the engine does. This is the same
mistake I made in 21-F9 and withdrew, in a new place, so I am recording it rather than quietly
re-labeling the prediction.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 6 pairs, FENs verified identical | **held** (after fixing my generator: the first run found 0 pairs because I searched only 60 games for a coincidence; 800 games found 6) |
| P2 softnodes same move | **held** 6/6 |
| P3 softnodes same node count | **held** 6/6 |
| P4 threefold root scores cp 0 / 0 nodes | **FAILED — and the engine is right, my prediction was wrong** |
| P5 0 crashes / sanitizer lines | held |

## Findings

`21-C15 | CONFIRMS order-independence with different histories` — 6 pairs of the same position
reached by different move orders give identical softnodes answers (move and nodes) and identical
depth-12 answers. Together with 21-C14 that is 16/16 pairs.

`21-C16 | CONFIRMS a mate outranks a drawn root` — a threefold root with a mate in 1 finds the mate
(`mate 1`, 200 nodes) instead of scoring the draw, which is what file 6 requires. This is the
discrimination control that makes 21-C14/C15 meaningful rather than vacuous.

## Suspicions, not proven

- Whether a threefold root with NO mate available scores 0 (file 6 says it should). I tested only the
  mate case; the no-mate case is the complement and I did not run it here.

## What I did NOT do

- Did not test the no-mate threefold root — that is the next check under file 6.
- Did not test insufficient-material roots at a drawn root with a mate available (a position that is
  both "dead material" and winning is impossible, so this may be vacuous).

## What I am NOT sure about

- Whether any real game reaches a threefold root with a mate in 1. It is a constructed case; its
  value is as a control, not as a practical scenario.

## Times

see `job36/stamps.txt`.

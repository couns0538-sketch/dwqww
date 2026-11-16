# REPORT — seat 07, job 7: repetition rule and a failed SEE cross-check

## What was asked / the answer / how sure

**Asked:** (continuation of the board.cpp read, highest normal-play risk first) test
`Board::is_repetition()` and anything else in board.cpp that silently changes play.

**Answer:** `is_repetition()` **agrees with python-chess threefold at all 62 plies** tested,
including the two cases that matter most in play: a twofold must not be declared a draw, and a
counter reset by a pawn move must break the repetition. My SEE cross-check **failed to become a
usable oracle** and I draw **no conclusion** about `see_ge` from it; that is written up as a
non-result, not a finding.

**How sure:** high for the repetition result (a planted fault makes the same comparison report 17
disagreements, so the clean result is not vacuous). For SEE: nothing claimed either way.

## Honesty numbers

Base build, job0/raw/summary.txt: 312866 / 862329 / 3024920 / 4865609. No engine source changed;
both programs compile against the unmodified `src/board.cpp` + `src/bitboard.cpp`.

## Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| read `is_repetition()` and both overloads | done | board.cpp:1224-1248, callers search.cpp:1308/1317/2251/2256 | see below |
| compare `is_repetition()` with python-chess threefold | done | job7/repetition_probe.cpp + job7/check_repetition.py | 62 plies, 0 disagreements |
| prove that comparison can fail | done | planted fault below | 17 disagreements reported |
| cross-check `see_ge` against an independent reference | **not done (failed)** | job7/see_crosscheck.cpp + job7/SEE_NOTES.txt | my oracle was wrong twice; no result drawn |

## The repetition rule, as the code states it

    board.cpp:1224  is_repetition()            count earlier occurrences of key_ in the
                                               halfmove-limited window; draw at >= 2
                                               (i.e. this position plus two earlier ones)
    board.cpp:1235  is_repetition(root_index)  span limited by min(halfmove, plies_from_null);
                                               true on a match at/after the root, else >= 2

Callers: `Worker::is_draw` (search.cpp:1308), `draw_leaf_score` (1317), and the root-drawn
special case (2251, 2256). So the rule decides real scores, not just a display field.

## Test

Six move lists, each played from startpos, comparing `is_repetition()` against python-chess
`is_repetition(3)` after **every** ply:

1. `g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8` — a genuine threefold.
2. the same with `e2e4 e7e5` in the middle — a counter reset, so the later shuffles are **not** a draw.
3. `g1f3 g8f6 f3g1 f6g8` — a twofold only, which must **not** be a draw.
4. a queen shuffle repeating twice.
5. eight reversible plies, a pawn move, then more — the fifty-move-counter interaction.
6. a long shuffle repeating many times.

    plies compared: 62
    RESULT: engine is_repetition() agrees with python-chess threefold at every ply

The checker asserts a `rep=` column and a key exist on every ply and refuses to run if any move
list is illegal, so a missing line cannot pass as agreement.

**Control (this is what makes the clean run meaningful):** rebuilding with `return matches >= 1;`
in `is_repetition()` — a planted fault that declares a twofold as a draw — makes the same checker
report **17 disagreements**, each naming the ply and FEN, e.g.
`list 4 ply 7 move c3b1: engine rep=True python-chess threefold=False fen
r1bqkbnr/pppppppp/2n5/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 7 4`. So the comparison detects exactly the
class of bug it is aimed at.

## The SEE cross-check: a non-result, stated plainly

I wrote `see_crosscheck.cpp`, an independent swap-list static-exchange evaluator, to compare with
`Board::see_ge()`. It disagreed on captures. Rather than report that as an engine finding, I checked
its first disagreeing cases by hand with python-chess:

- `fen 2b1kbn1/2r3p1/p1Pp1q2/5p2/2BpPP2/1P2Q2r/P1R4P/RNB1K3 w Q - 2 29`, move `e4f5`:
  after `exf5`, Black's **only** legal captures are `h3e3` and `d4e3`; nothing recaptures on f5.
  So `see_ge(exf5, 100) = true` is **correct** and my reference invented a recapture.
- `fen r1bqkbnr/pppppppp/2n5/8/8/2P5/PP1PPPPP/RNBQKBNR w KQkq - 1 2`, move `b2b4`:
  White wins a knight for a pawn (+200 by piece count after `b4 Nxb4 cxb4`), so the engine was
  right and my first reference version was wrong.

I fixed two bugs in the reference (the standing-piece bookkeeping in the swap list, and matching
the engine's documented choice that a king is worth 0 in SEE, `include/forge/eval.hpp:32`), and it
still differs, so it is not fit to be an oracle. **I therefore claim nothing about `see_ge`** beyond
this: it is exercised indirectly by the 14-position perft agreement and by the honesty pins, both
of which are unchanged. A real SEE check needs an oracle that is itself validated move by move
against python-chess's legality — which is what my two hand checks did, and both went the engine's
way.

## Findings

No new FINDINGS. `is_repetition()` is clean under a failable test; SEE is unresolved rather than
faulty, and an unresolved check is not a finding.

## Suspicions, not proven

- `is_repetition(root_index)`'s rule ("a match at or after the root is a draw, even the first one")
  is a deliberate search-side rule, not FIDE threefold. I did not test it separately; the no-argument
  overload I did test is the one the UI-facing root check uses.
- `key_after` has no runtime check in Release (job6 report). Unchanged conclusion.

## What I did NOT do

- Did not produce a trustworthy SEE oracle; explicitly abandoned rather than tuned until it agreed
  (tuning until agreement would have been circular).
- Did not test `is_repetition(root_index)` at search depth.

## What I am NOT sure about

- Whether the engine's SEE mishandles pinned attackers in some position; my oracle could not tell me.

## Times

See job7/stamps.txt.

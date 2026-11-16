# ADDENDUM — variant H (generator emission order) is REFUTED; and the lone-king defect is a misevaluation

## A. Variant H: canonicalising the generator's emission order does NOT fix the asymmetry

The one-position dump in `REPORT_cause.md` showed the move generator's emission order differs under a colour
mirror. Variant H (`make_variant_h.py`, patch `FORGE_swarm06_generator_order.patch.txt`, applies `-p1` no fuzz)
reorders the finished move list by the mirror-invariant key `(from^56, to^56, promotion)`.

**It works as designed**: measured on three positions, emission order becomes mirror-invariant on all three
(`variant_h_fixture.txt`: base False/False/False → variant H True/True/True), and **perft 5 is unchanged at
4,865,609**, which is the proof it is a pure reorder.

**And it changes nothing about the asymmetry:**

| build | depth-10 G bestmove mismatches | score differences |
|---|---|---|
| base | **101** of 353 | 334 |
| variant H (generator order canonical) | **101** of 353 | 338 |

**So the generator's emission order is not what produces the asymmetry — eighth mechanism refuted.** This is
consistent with the picker re-scoring every move before it is searched: the order the generator hands over is
discarded by the sort that follows, so making that order canonical cannot matter.

Honesty: variant H fails the pins (bench 11 367464, bench 13 1010323, bench 16 2834878; perft 5 unchanged),
as any order change must. Evidence only, not a candidate.

## B. The lone-king defect: a MISEVALUATION, now established by ground truth

My S-F32–S-F34 were withdrawn because I read the mate sign backwards (`mated_in(ply) = -MateValue + ply`, so a
longer mate is a better score). That withdrawal stands as a claim about *signs*.

But a play-out settles the position independently of any score, and **I reproduced it exactly** on the base
build (`playout_verify.py`, both sides played by the engine at depth 12, python-chess adjudicating, scores
never consulted, 3 runs each):

| White's first move | plies survived | end |
|---|---|---|
| c6d6 | **22, 22, 22** | checkmate each time |
| c6c7 | **20, 20, 20** | checkmate each time |

Fully deterministic, and `c6d6` survives **strictly longer in every run** (min 22 vs max 20). So:

- The engine's preference for `c6c7` **is wrong by ground truth**, regardless of any score or sign.
- The error is in its **score for `c6d6`** — it rates that move `mate -8` when playing it out actually holds
  22 plies. A misevaluation of the losing alternative, which then produces the wrong choice.
- It is **not** a cross-build regression (base shows it), and **not** a sign convention problem.

Recorded as S-F39. S-F32/S-F33/S-F34 stay withdrawn as *ordering-flaw* claims; the defect is real but its
nature is different from what I first reported.

## C. Why the scores could not settle any of this

S-F38, and this is the reusable lesson: a `searchmoves` score and a free-choice score at the same nominal depth
are **not comparable** — they search different trees. On this board the restricted searches reached
**seldepth 43 on 16M nodes** while the free choice reached **seldepth 37 on 166M**. Two numbers that look like
they should be comparable were not. Any claim of the form "it plays X but scores Y better" must quote seldepth
and nodes for both, and say whether each was restricted or free.

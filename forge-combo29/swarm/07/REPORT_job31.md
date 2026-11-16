# REPORT — seat 07, job 31: what `bestmove 0000` should mean, and the one-candidate boundary

## What was asked / the answer / how sure

**Asked:** (1) state in the patch header the design choice about `bestmove 0000`, recommend an answer
and its consequence for a GUI, as seat 12 did for the abort fix; (2) then the C-series re-checks, and
if time remains test whether the early branch prints a score when the restriction names a move that
IS legal but leaves exactly one candidate.

**Answer:** all four candidate answers measured, recommendation and its GUI consequence written into
the patch header. The one-candidate boundary is **handled correctly** — a legal single candidate is
searched normally on both builds.

**How sure:** high; every number is from a fresh process, Threads 1, Hash 16, and the recommendation
rests on measurement (A/B/C) rather than taste.

## The design question, measured on startpos (20 legal moves), `go depth 6 searchmoves e2e5`

| | answer | depth lines | nodes |
|---|---|---|---|
| **A** unpatched | `bestmove 0000` | 6, all `score cp 0 nodes 0` | 0 |
| **B** this seat's patch | `bestmove 0000` + `info string searchmoves restriction has no legal root moves` | **0** | 0 |
| **C** full-root search | `bestmove d2d4` | 6, real | **1703** |
| **D** no answer | — | — | GUI hangs |

C was measured by running the same engine **without** the restriction, which is exactly the answer C
would give; no second engine was needed to state its consequence.

## The recommendation, in one sentence

**Ship B.** A fabricated score is a defect; an honest `0000` is not. B changes nothing a GUI does
today — the GUI already received `0000` in A — it removes the false score, not the move.

**If the owner wants a playable move instead**, that is a *separate* decision and it must announce
itself: `bestmove d2d4` plus `info string searchmoves matched no legal move; searched the full root`.
A GUI must never be handed a move outside the set it asked for without being told.

D is rejected for the same reason seat 12 rejected it in S-F11: a GUI that never receives a
`bestmove` is worse off than one that receives a poor answer.

## Why B rather than C, though C is friendlier

`searchmoves` exists so a caller can **forbid** moves — it is how a training or analysis harness
restricts the root. Silently searching the full root would produce a move the caller explicitly
excluded, which is a louder lie than an honest "I could not honour your restriction". B keeps the
engine truthful and leaves the policy choice where it belongs, with whoever sent the restriction.

## The one-candidate boundary (asked second)

| case | base 6b98f217 | PC r15 + patch, PC20 |
|---|---|---|
| `searchmoves e2e4` on startpos | `e2e4`, 6 depth lines, **438** nodes | `e2e4`, 6 depth lines, **344** nodes |
| `searchmoves f3e5`, a real capture, single candidate | `f3e5`, 6 depth lines, **138** nodes | `f3e5`, 6 depth lines, **175** nodes |

Both nonzero on both builds, so a one-candidate legal restriction is **not** routed through the
empty-root branch. The branch keys on `root_candidates.empty()`, i.e. on emptiness rather than on
smallness — which is the correct criterion, and this is the boundary that would have exposed it if
the implementation had used a size test like `size() <= 1`.

**Honest note on my own test:** my first version used `position startpos moves e2e4 e7e5 g1f3` with
`searchmoves f3e5`, where it is **Black** to move, so `f3e5` was never legal and the harness printed a
false warning. python-chess showed the move illegal and the case was corrected. Nothing in the final
table depends on the bad case.

## Findings

**07-C24** (the design answer) and **07-C25** (the boundary) in FINDINGS.md.

## Suspicions, not proven

- Whether any GUI actually acts destructively on `0000` in a live position. Seat 12 asserts some may
  resign, adjudicate or crash; I did not test a GUI, only reasoned from the UCI meaning of `0000`.

## What I did NOT do

- Did not implement option C (ignore the restriction), by choice — it needs the owner's decision.
- Did not test a restriction that names one legal move *plus* several illegal ones beyond the two
  cases above.

## What I am NOT sure about

- Whether a training harness (the PC's own use of `searchmoves`) would prefer C. If the PC's loop
  restricts the root for label quality, C could be actively harmful there; that is an argument for B.

## Times

See job31/stamps.txt.

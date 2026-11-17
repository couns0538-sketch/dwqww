# 19-C49 — reconciling seat 27's population result with my 19-C46

## What seat 27 reported (as relayed)
600 real self-play positions, python-chess-validated: **PC20 deeper 127, shallower 60, net +0.063 ply,
p = 1.1e-06**. On its own 8 positions PC20 was **+6 at softnodes 2000** with no negative cell below 8000.
One-at-a-time at 2000: **TtPruneV2 +6** — the opposite of my attribution. Its diagnosis: my −2 and its +6 are
both small-sample artefacts; the residual is a **move-choice effect**, and restricting to the 406 positions where
both chose the same move collapsed the depth sum from **+38 to −11**. Node spend identical (0.989).

## What I now believe — three separate claims, three different answers

Seat 27 is right that I cannot defend the *sign* of a 6-position effect, and its control point is correct and
important. But its result and mine do not actually compete, because **they measure different quantities.** On
200 positions of my own slice (odd lines of `R_2911.fens`), PC r15 vs base, Threads 1, Hash 16, both regimes run
through the same guarded harness:

| quantity | my result at n=200 | verdict |
|---|---|---|
| **S14 vs PC20 at softnodes 2000** | PC20 deeper 17, S14 deeper 24, equal 159 → net **+9 ply for S14**, sign test **p = 0.349** | **NO difference.** My "−2" does not replicate — and neither does seat 27's "+6". |
| **S14 vs PC20 at softnodes 3000** | PC20 deeper 14, S14 deeper 20, equal 166 → net **+10 for S14**, **p = 0.392** | **NO difference.** |
| **2000 → 3000, within ONE engine** | S14 **+134 ply**; PC20 **+133 ply** | **REAL and LARGE — but engine-independent.** |

**The third row is the reconciliation.** Raising the budget from 2000 to 3000 buys **+0.67 ply per position**, and
it buys *exactly the same* amount for both engines (+134 vs +133). **The budget is a lever on depth; the PC20
switches are not.** My 19-C46 read a −2 and a +1 as evidence that the budget "flips PC20's switches" — the flip I
found between 2,000 and 3,000 was **the budget working, not PC20 working.** That attribution was wrong and I
withdraw it.

**What survives of 19-C46:** the numbers at 8k–20k where PC20 is genuinely deeper — which seat 27 also keeps.
**What does not survive:** the claim that TtPruneV2 "costs the ply at 2,000" and that raising the budget makes
PC20's switches pay. Both were 6-position artifacts, as seat 27 says.

## Where I still disagree, and it is a real disagreement
Seat 27 reports 67.9 % of its decided positions favouring PC20 (127/187). My 200 positions give **41.5 %** (17/41).
**Difference in proportions z = 3.18** — these are not two samples of one truth; the two samples genuinely disagree,
and it is not my sample size alone that explains it. Likely candidates, in the order I would test them:
1. **Position provenance.** Its 600 are *self-play* positions (likely unbalanced, one side winning, many near
   mates). My 200 come from `R_2911.fens`, which is a game set too — but a different population, and self-play
   positions from a small budget are a very particular distribution.
2. **The ply metric's sensitivity near mates.** At `softnodes 2000` the median search is depth ~7–8; when a mate is
   found early, *depth* stops being a measure of anything (the engine breaks on `mate_moves > 0`). A population
   rich in decided positions would inflate any depth difference in whichever direction the earlier mate happens to
   sit.
3. **Its own control point, applied to its own headline.** If depth differences below one ply at a fixed budget
   are largely move-choice, then a **+0.063 ply mean** is *well* inside the band it says needs the same-move
   restriction. Its p = 1.1e-06 is not evidence against that — with n = 600 a genuine 0.063-ply move-choice
   artefact is easily significant. **A tiny effect can be highly significant and still be an artefact.**

## Seat 27's control point, applied to my own data — and it does NOT behave as expected
This is the part I owe them, so I ran it. Restricting to positions where both engines chose the **same move**:

| comparison | same-move subset | different-move subset |
|---|---|---|
| S14 vs PC20 at 2000 | 176 pos, **+5** | 24 pos, +4 |
| 2000 → 3000 within S14 | 179 pos, **+112** | 21 pos, +22 |
| 2000 → 3000 within PC20 | 182 pos, **+113** | 18 pos, +20 |

**The same-move restriction does not collapse the budget effect — it absorbs 84 % of it** (112 of 134). That is
because on 47 % of positions the two budgets return the *identical search* (93/200 for S14, 94/200 for PC20; 98.9 %
of those also match node-for-node). Those positions contribute **zero** to the sum and dilute nothing.

So the control point **vindicates the budget result and dissolves the engine comparison** — the opposite of how it
was used. Same-move restriction is the right instrument; it just points at a different conclusion than the one it
was applied to.

## The mechanism nobody in this thread had checked
`softnodes N` is **not a node budget of N**:
- `search.cpp:2499` sets the hard cap to **4 × N**;
- `search.cpp:2932` tests the soft limit **only after a completed iteration**.

So `softnodes N` means "stop at the first iteration boundary at or after N nodes". Consequences, both measured:
- **Mean spend at `softnodes 2000` is 3,185 nodes (S14) / 3,234 (PC20), not 2,000** — a 59–62 % overrun.
- **`softnodes 3000` mean spend is 4,711 / 4,536** — so the real ratio is 1.40–1.48, not 1.5.
- **On 46.5–47.0 % of positions, 2000 and 3000 buy the identical search.** The "2000 vs 3000" question is
  ill-posed on nearly half the sample: the budget is not a variable there.
- **A degenerate class exists**: on 1 of 200 positions no iteration completes before the 4N hard cap, so the engine
  returns `root_candidates.front()` — a move chosen by nothing, with **no `info` line at all**. Both builds do it
  in every regime including `depth 12` and `movetime 500`... (see caveat below).

**Caveat, honestly:** my first attempt to demonstrate that degenerate position used a **hand-typed shell pipeline
and lied** — the `printf` dropped the FEN, the engine got a malformed position and returned nodes 0. The guarded
harness then showed the position searches normally *except* under `softnodes`, where it hits the cap with no
completed iteration. So the degenerate class is real (1/200, both engines, reproducible under `softnodes`) but my
first diagnosis of it was a shell artefact. **The 0 was mine, not the engine's.**

## What I would put in front of the owner — unchanged in form, corrected in reason
- **"PC20 uses the same nodes and reaches slightly greater depth at match budgets (8k–20k)"** — stands, seat 27
  agrees.
- **Do NOT change the self-play budget on the grounds that it helps PC20.** It does not. It helps *depth* by
  +0.67 ply per move for **both** engines, at **~1.45× the nodes per move**, and PC20 is neither helped nor hurt
  differentially. **That is the trade, and it is engine-neutral.**
- At the self-play budget PC20 and S14 are **indistinguishable in depth at n=200** (p = 0.35 / 0.39). Claims of
  ±0.06 ply in either direction are below the resolution of this instrument.

## What I withdraw and what I keep
- **WITHDRAWN:** 19-C46's attribution of the 2000→3000 flip to `TtPruneV2` and to "PC20's switches paying".
  It was a 6-position artefact read as a mechanism; the mechanism I read from the source (TtPruneV2 pruning
  "needing more nodes to pay for itself") does not survive contact with 200 positions.
- **KEEP:** the depth gain from raising the budget is real and large (+0.67 ply/pos) — but it belongs to the
  budget, not to PC20.
- **KEEP:** PC20 deeper at 8k–20k.
- **KEEP:** the granularity finding (19-C49 proper), which is new and applies to every budget comparison any seat
  has made with `softnodes`.

# S02 check of seat 23's 23-F27 — the margin predicts sensitivity, EXCEPT for found mates

Their finding, well-qualified by them: positions whose move changes between budgets have median top-two gap
**12 cp**, while positions that do not change have median **46 cp**; but as a per-position classifier a small gap
is weak — at every threshold from 5 to 30 cp precision is only 45-56 %.

## the test I added: their rule at gap ZERO, split by the kind of answer
Their frame says a small margin is unstable, so a gap of exactly 0 should be the most unstable case of all. My
S-C11/S-C12 work left me with gap-0 boards in two kinds, which their 60-position sample may not have separated:
**found mates** (>= 2 moves each giving mate in 1) and **quiet ties** (two equal centipawn moves, no mate).

Each board run at four budgets — N = 5,000 / 20,000 / 50,000 / 200,000 — and the bestmove compared across them.
PC r15 + PC20, Threads 1, Hash 16, OwnBook false, cold, interactive driver.

| kind | position | bestmove across budgets | stable |
|---|---|---|---|
| mate-tie (0 cp) | `4k3/8/4K3/8/8/8/8/R6R w` | a1a8, a1a8, a1a8, a1a8 | STABLE |
| mate-tie (0 cp) | `k7/8/1K6/8/8/8/8/3R3R w` | d1d8, d1d8, d1d8, d1d8 | STABLE |
| mate-tie (0 cp) | `k7/8/1K6/8/8/8/8/3Q3R w` | h1h8, h1h8, h1h8, h1h8 | STABLE |
| mate-tie (0 cp) | `k7/8/1K6/8/8/8/7Q/7R w` | h1a1, h1a1, h1a1, h1a1 | STABLE |
| mate-tie (0 cp) | `1k6/8/2K5/8/8/8/Q7/Q7 w` | a1h8, a1h8, a1h8, a1h8 | STABLE |
| mate-tie (0 cp) | `1k6/8/3K4/8/8/8/8/R6Q w` | a1a8, a1a8, a1a8, a1a8 | STABLE |
| quiet-tie (0 cp) | `4k3/8/8/3p4/3P4/8/8/4K3 w` | **e1d2, e1e2, e1e2, e1e2** | **CHANGED** |
| quiet-tie (0 cp) | `4k3/8/8/2p1p3/2P1P3/8/8/4K3 w` | e1f2 ×4 | STABLE |
| quiet-tie (0 cp) | `4k3/8/3n4/8/8/3N4/8/4K3 w` | **d3f2, e1e2, d3b2, d3b2** | **CHANGED** |

**mate-tie: 6 of 6 stable. quiet-tie: 1 of 3 stable.**

## verdict: CONFIRMS their rule and adds the exception that sharpens it
- Their core claim holds: a small margin means instability. **Two of my three quiet 0-cp ties changed move across
  budgets** — the smallest possible margin produced the instability their rule predicts.
- **But a 0-cp FOUND MATE never changed, 6 of 6, at any budget from 5,000 to 200,000 nodes.** So the margin is not
  sufficient on its own: what also matters is whether the answer is FORCED. A mate in 1 is found at every budget,
  so no amount of extra search can flip it, whereas a quiet 0-cp tie is re-broken at every depth by whichever
  equal-scoring leaf the search reaches first.

## the refined statement, which is the useful form for a harness
**Budget sensitivity is driven by the margin AND by whether the answer is forced.** A position is safe across
budgets if its answer is forced (a found mate, even at 0 margin — 6/6 stable here); a position with a small margin
in a QUIET position is unsafe even at 0 (2 of 3 changed). This is consistent with their precision numbers being
weak at a single threshold: the margin alone cannot classify, but "small margin and not forced" is a much better
predictor than either alone.

## scope
Nine gap-0 boards of my own construction, four budgets each. That is enough to establish the exception and its
direction; it is not a rate over real game positions, and seat 23's 60-position sample remains the better estimate
for the general population.

# PREDICTION - committed BEFORE measurement (19-C49)

## What I am testing
Seat 27's result and mine both compare depth at `softnodes 2000` vs a fixed node budget, treating `softnodes N`
as "a budget of N nodes". **The source does not implement it that way.** `src/search.cpp:2932`:

    if (soft_node_limit_ != 0 && total_nodes() + extra_nodes_ >= soft_node_limit_) break;

This is only evaluated AFTER a completed iteration, and `node_limit_` is set to **4x N** as the hard cap
(`search.cpp:2499`). So `softnodes N` means **"stop at the first iteration boundary at or after N nodes"** -
actual spend overruns N, by up to a whole iteration, and the hard cap is 4N.

## The consequence neither of us accounted for
If the iteration at the 2000-node boundary is large, then **`softnodes 2000` and `softnodes 3000` can stop at
the SAME completed iteration** - in which case the two budgets produce an IDENTICAL search, and any "effect of
raising the budget" on those positions is exactly zero, not small.

## My prediction, stated before any number exists
1. **On a substantial fraction of positions - I predict 25-60 % - `softnodes 2000` and `softnodes 3000` return the
   identical (bestmove, depth, nodes).** If so, the 2000-vs-3000 question is partly ill-posed: on those positions
   the budget is not a variable at all.
2. The mean node spend at `softnodes 2000` will **exceed 2000** (overrun), and the ratio spend(3000)/spend(2000)
   will be **well below 1.5** - I predict 1.0-1.25 - not the 1.5 a literal node budget would give.
3. **Kill condition:** if fewer than 10 % of positions are identical across the two budgets, then the granularity
   point is practically irrelevant and I drop it.

## What each outcome means
- Large identical fraction -> the practical question is NOT "2000 vs 3000" but "how many distinct searches do
  these budgets buy", and both my -2 and seat 27's +0.063 are arguments about a difference that, on most
  positions, does not exist. That would be the reconciliation.
- Small identical fraction -> budgets do differ; seat 27's sample then decides the sign and I concede.

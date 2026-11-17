# Seat 19's softnodes granularity: confirmed, but the fraction is configuration-dependent (S-C41)

Seat 19's `19-C49` predicted — before measuring — that `softnodes N` stops at the first **iteration boundary** at or
after N nodes, so `softnodes 2000` and `softnodes 3000` can buy the **identical** search on a large share of
positions, making any "effect of the budget" exactly zero there rather than small. I checked their two source
citations and both are right, then tested the predictions.

## The mechanism, verified in source

```2928:2934:src/search.cpp
        if (mate_moves > 0 && score >= mate_in(mate_moves * 2 - 1)) break;
        // The iteration above is finished. Passing the soft budget stops here,
        // keeping this move and score. The hard cap is enforced inside search.
        if (soft_node_limit_ != 0 && total_nodes() + extra_nodes_ >= soft_node_limit_) break;
        if (should_stop()) break;
```

```2497:2501:src/search.cpp
    if (limits.soft_nodes && parent_worker_ == nullptr && is_main() && limits.nodes > 0) {
        constexpr std::uint64_t kMaxNodes = std::numeric_limits<std::uint64_t>::max();
        node_limit_ = limits.nodes > kMaxNodes / 4 ? kMaxNodes : limits.nodes * 4;
        node_limit_specified_ = true;
```

The soft budget is only tested **after an iteration completes**, and the hard cap is **4N**. So `softnodes N` means
"stop at the first iteration boundary at or after N" — it **overruns** N, by up to a whole iteration.

## P1 — CONFIRMED on PC20, but it is configuration-dependent, which the prediction did not say

12 positions, fresh process per row, read to `bestmove` before `quit` (Trap 11), three runs:

| settings | identical 2000-vs-3000 | control: identical 2000-vs-20000 |
|---|---|---|
| **PC20** | **6 of 12 = 50 %** (three runs, same six positions) | **0 of 12** |
| plain | **2 of 12 = 17 %** | 0 of 12 |

Seat 19 predicted **25–60 %**, killed under 10 %. On PC20 it lands at **50 %**, inside their range — **P1 stands**.
On plain settings it is **17 %**: still above their kill threshold, but far below their predicted range.

**The control is what makes either number mean anything.** If 2000-vs-20000 were also "identical" then the tool
could not distinguish budgets at all and the fraction would be an artefact (Trap 8). It is 0 of 12 in both configs,
so the identity at 2000-vs-3000 is real.

**The configuration dependence is a finding in itself and it is not in their prediction.** The identical share is a
property of how large the iteration spanning 2,000 nodes happens to be, which depends on the search's reduction and
pruning settings. PC20 makes iterations coarser at that depth; the plain build makes them finer. So "what fraction of
positions are identical" has no single answer — it is a function of the settings, and any measurement of it needs
its configuration stated. Their prediction names none.

## P2 — the ratio, and why one number cannot describe it

Their P2 predicted mean spend above 2,000 (overrun) and a spend ratio of **1.0–1.25**. Measured on PC20:

| | value |
|---|---|
| mean spend at `softnodes 2000` | **3,072 nodes** — overrun **+1,072** |
| mean spend at `softnodes 3000` | 4,871 nodes |
| ratio of means | **1.586** |
| mean of per-position ratios | 1.788 |
| median of per-position ratios | 1.325 |

Overrun: **confirmed**. Ratio: **outside their 1.0–1.25 on every statistic** — but the reason is more interesting
than a miss, and it is the `S-F126` lesson again:

**The ratio is bimodal, not distributed.** On the six identical positions it is **exactly 1.00 by construction**. On
the other six it runs **1.65–3.81×** (rookend 3.81, italian 2.65, sicilian 2.64, mateish 2.39, complex 2.31, kid 1.65;
median 2.52). So a single mean (1.586) and a single median (1.325) each describe **neither cluster**. A literal node
budget would give a uniform 1.5 on every position; this gives 1.00 or 2.5 depending on which side of a boundary the
position falls.

Seat 19 predicted a single number for a quantity with two populations. That is not a careless error — it is what
happens when you predict the *mean of a bimodal variable*: the mean lands between the modes and looks like a modest
underestimate rather than a description of nothing.

## Why this is the same phenomenon as my `S-F123`, from the opposite side

| command | which rung it selects |
|---|---|
| `go nodes N` | the last completed iteration **at or below** N (`S-F123`: 200,000 → 101,640) |
| `softnodes N` | the first completed iteration **at or above** N (here: 2,000 → up to 4,121) |

Both mean **the budget is not a quantity**, and in both cases two different budgets can select the *same* search.
Their consequence is right and sharper than mine in one respect: **for `go nodes` the same-budget collision is a
measurement hazard, but for `softnodes` it is the thing under study** — seat 19 is testing whether raising a budget
changes play, and on 50 % of positions (PC20) it provably cannot, because the engine runs the identical tree.

## What I am not claiming

* Not that P1 is wrong — it stands on PC20 at 50 %, inside their stated range.
* Not that the plain-settings 17 % refutes them; their kill threshold was 10 %, and 17 % clears it.
* Not that the identical positions are a defect. The engine is doing what its code says; the issue is that a
  *budget comparison* on those positions is comparing a configuration with itself.
* Not a general fraction. **12 positions, and the figure moves with settings**, so 50 % is "on this set under PC20",
  not a property of the engine.

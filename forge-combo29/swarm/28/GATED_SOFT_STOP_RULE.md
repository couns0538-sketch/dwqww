# THE GATED SOFT-STOP RULE — a one-page fix spec

## The rule, in one sentence

Before starting an iteration, stop if the projected finish exceeds the soft plan by at least **1.5x that
iteration's own measured cost** — i.e. compute `P = t_last + C * c_last` and stop when
`P - soft >= 1.5 * c_last`, using `C = 1.3`.

In code terms, at the iteration boundary, with `c_last` the cost of the iteration just finished:

```
projected = elapsed_ms() + 1.3 * c_last;
if (projected - soft_limit_ms_ >= 1.5 * c_last) -> stop, keeping the last completed iteration
else                                            -> risk the next iteration
```

The gate exists because the ungated rule (`stop when projected > soft`) also fires on near-misses, where
the iteration would very often have completed anyway; those are exactly the cases that cost 2-3 plies.

## The sweep that justifies 1.5 (not a guess)

| gate | base saving mean | base lose 2+ plies | PC20 saving mean | PC20 lose 2+ plies |
|---|---|---|---|---|
| 0 (ungated) | 62 ms | 2 | 85 ms | 4 |
| 0.5 | 47 | 2 | 85 | 4 |
| 1.0 | 29 | 1 | 66 | 3 |
| **1.5** | **22** | **1** | **35** | **0** |
| 2.0 | 4 | 0 | 35 | 0 |
| 3.0 | 4 | 0 | 0 | 0 |

At 1.5 the last PC20 two-or-more-ply loss disappears and nothing further is bought above it. Ungated, for
comparison: PC20 mean 85 ms / max 826 ms saved, at up to **4 plies** lost. This is a **trade-off curve, not
a free lunch** — 1.5 spends some of the saving to remove the ply losses.

## The 6 s-plan scaling note (read this before choosing numbers)

**Every millisecond above was measured at the 10 s plan (soft 454 ms).** The owner's clock is 6 s + 0.06,
whose soft plan is 317 ms. The **ratios** transfer — the 1.5x gate, `C = 1.3`, the ply costs, and the
fraction of searches affected — but the **milliseconds do not**. Read the ms figures as roughly **70 %** of
the quoted values at the 6 s control, not as the values themselves. The gate constant itself (1.5) is
dimensionless and needs no rescaling.

## When the just-completed iteration already overran soft (the 6 s regime)

At the owner's control soft is 317 ms and sparse-class iterations reach 415 ms, so `c_last > soft` is not a
corner case — it is where the heavy moves live. **The rule handles it by algebra, not by a special case:**

```
stop  <=>  t - B >= (G - C) * c_last        with G = 1.5, C = 1.3  ->  (G - C) = +0.2
```

Because **G > C**, a LARGER last iteration makes the rule stop **sooner**. As `c_last` grows the condition
reduces to "stop whenever `t` is at all past B", which is the right behaviour. Verified on the ladders:

| budget | iterations whose own cost exceeded soft | rule STOPS | rule CONTINUES | largest such iteration |
|---|---|---|---|---|
| 454 ms (10 s plan) | 4 of 661 | 4 | **0** | 1239 ms (2.73x soft) |
| 317 ms (the owner's 6 s plan) | 10 of 661 | 10 | **0** | 1239 ms (3.91x soft) |

**The one thing to add: an iteration floor.** Complete at least one iteration before any time rule may
fire, or a search whose first iteration exceeds a very small soft plan returns with no bestmove. The
engine's loop already does this (the stop check sits AFTER the iteration), and an implementation must not
move it before.

### The hard limit of what this rule can fix — state it before promising a fix

The rule fires at an iteration BOUNDARY, so it **cannot** prevent the cost of the iteration that overran;
that time is already spent. It only refuses to start the next one. Measured, per overrun case:

| budget | overrun cases | preventable (time remained after) | already spent (nothing left to save) |
|---|---|---|---|
| 317 ms | 10 | **3** | 7 |

So at the owner's control the rule can reclaim time in **3 of the 10** overran iterations. The single
largest cost in the whole dataset — a 1239 ms iteration reached after only 48 ms — is **not preventable by
this rule at all**: the search was 48 ms in and the iteration itself took 1239 ms. A rule that fires at
iteration boundaries cannot see that coming. Preventing *that* class needs a check INSIDE the iteration
(the existing hard limit already caps it; a node-based or time-based mid-iteration abandon is a different
and larger change, and I have not measured it).

That is the honest boundary of this recommendation: it is a cheap, low-risk improvement that recovers time
in most-but-not-all heavy cases, and it is not a fix for the worst one.

## The estimate-error caveat, with the specific thing an implementation must get right

The rule needs `c_last`, the cost of the iteration **just completed** — not of the next one. That is a
measured quantity, available for free, and it is the thing to get right: **do not substitute an estimate of
the next iteration's cost.** Using the just-finished iteration's own cost is what makes the rule robust.

I measured how much this matters. Predicting the NEXT iteration's cost naively is poor — with the best
naive predictor the median absolute error is **58 %**, the 90th percentile 138 %, and the worst cases over
3000 % (`predictor_error_out.txt`). That looks fatal. **It is not**, because the gate's threshold scales
with the same estimate:

| predictor for c | agreement with the oracle decision |
|---|---|
| `c_hat = 1.264 x c_last` (calibrated in-sample) | 48/48 = 100 % |
| `c_hat = 1.267 x c_last` (calibrated on BASE, evaluated out-of-sample on PC20) | 24/24 = 100 % |
| `c_hat = 1.0 x c_last` (assume no growth at all) | 48/48 = 100 % |
| `c_hat = 2.0 x c_last` (assume mean growth) | 47/48 = 98 % |

So **the rule picks the same stopping depth as a perfect predictor even with a crude constant**, including
out of sample. That is the licence to build it with a simple predictor. What it does NOT licence: reading
the projection as a time estimate for anything else (scheduling, reporting), where the 58 % median error
applies in full.

### The one thing that would break it
If `c_last` is taken to be the cost of the *current* iteration before it finishes, or if the search's
`elapsed_ms()` includes setup that is not part of the iteration, the gate mis-fires. Anchor both quantities
to the same clock and the same iteration boundary.

## Where this came from, and its limits
- Arithmetic on 48 committed iteration ladders (`ladder_base_w10000.tsv`, `ladder_PC20_w10000.tsv`), run
  through `gated_rule.py`, `gate_survives.py`, `predictor_error.py`. **Not** a patched engine.
- **Computed, not built.** A real implementation integrates with aspiration re-searches and MultiPV, which
  this arithmetic does not model — those add iterations the ladder never saw.
- **Not a strength claim.** A millisecond saved and a ply lost have an exchange rate only a match can price.
  This file supplies the arithmetic so that match can be specified.
- **It does not fix the worst case.** At the 6 s plan it is preventable in only 3 of the 10 overran
  iterations, and the largest single iteration cost in the dataset (1239 ms after 48 ms of search) is not
  preventable at all from an iteration boundary. See the section above.
- The heavy class is sparse endgames, and which board is heavy differs by BUILD as well as position
  (`base#7` is 1585 ms on base vs 843 ms on PC20; `pc#57` is 281 on base vs 1586 on PC20) — so a fix should
  be validated on both builds.

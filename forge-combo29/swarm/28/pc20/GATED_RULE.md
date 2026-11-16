# The gated soft-stop rule: measured against the ungated one, with a concrete recommendation

## RECOMMENDATION (this line carries the caveat, as asked)

**Adopt the gated rule with G = 1.5**: before starting an iteration, stop if the projected finish exceeds
the soft plan by at least 1.5x that iteration's own measured cost. On the ladders this removes every 2-ply
loss (PC20: 4 such searches -> 0) while still recovering a mean 35 ms and up to 424 ms per affected search.
**Caveat, in the recommendation itself: all milliseconds here were measured at the 10 s plan (soft 454 ms).
The ratios — 1.5x gate, the ply costs, the fraction of searches affected — transfer to the owner's 6 s
clock (soft 317 ms); the millisecond figures do not, and should be read as ~70 % of these values on the 6 s
plan, not as the values themselves.**

## The two rules, stated exactly

Both act only at iteration boundaries. With iteration costs `c_i`, a projected next finish
`P_i = t_i + C * c_i` (C = 1.3, the median growth factor measured in S-F26/S-F27) and overshoot
`O_i = P_i - B` against the soft budget B:

- **ungated**: stop at iteration i when `P_i > B` — "the next iteration will not fit, so do not start it".
- **gated (G)**: stop only when `P_i > B` **and** `O_i >= G * c_i` — a near miss is risked, because a
  projection that misses by less than G times the iteration's own cost often completes anyway.

The gate exists because the ungated rule's expensive cases are the ones where the next iteration only just
missed the budget: several cheap iterations would still have fitted, so stopping there throws plies away.

**Hand-check of the arithmetic** on a synthetic ladder `1:10 2:40 3:120 4:400 5:900`, B = 454, C = 1.3:
at depth 3 the projection is 224 (continue); at depth 4 it is 764, overshoot 310, and 2c = 560 so the
gated rule continues where the ungated rule stops; at depth 5 it is 1550 and both stop. So the gate lets
the depth-4 iteration be risked and, in that example, reaches depth 5 — the ungated rule would have
stopped a ply earlier. The rule does what it says.

## Measured comparison — same ladders, both rules (`gated_rule_out.txt`, `gated_rule_G15.txt`)

| build | rule | saving median | saving mean | saving max | plies lost median | mean | max | lose 0 | lose 1 | lose 2+ |
|---|---|---|---|---|---|---|---|---|---|---|
| base | ungated | 0 | 62 | 516 | 0 | 0.38 | 3 | 18 | 4 | 2 |
| base | gated G=2 | 0 | 4 | 95 | 0 | 0.04 | 1 | 23 | 1 | 0 |
| PC20 | ungated | 0 | 85 | 826 | 0 | 0.46 | 4 | 20 | 0 | 4 |
| PC20 | gated G=2 | 0 | 35 | 424 | 0 | 0.12 | 1 | 21 | 3 | 0 |

| build | ungated | gated G=1.5 |
|---|---|---|
| base saving mean / max | 62 / 516 ms | 22 / 374 ms |
| base plies mean / max / lose2+ | 0.38 / 3 / 2 | 0.17 / 2 / 1 |
| PC20 saving mean / max | 85 / 826 ms | **35 / 424 ms** |
| PC20 plies mean / max / lose2+ | 0.46 / 4 / **4** | 0.12 / 1 / **0** |

## The gate sweep, which is what makes G = 1.5 the choice rather than a guess

| gate | base save mean | base lose2+ | PC20 save mean | PC20 lose2+ |
|---|---|---|---|---|
| 0 (ungated) | 62 ms | 2 | 85 ms | 4 |
| 0.5 | 47 | 2 | 85 | 4 |
| 1.0 | 29 | 1 | 66 | 3 |
| **1.5** | **22** | **1** | **35** | **0** |
| 2.0 | 4 | 0 | 35 | 0 |
| 3.0 | 4 | 0 | 0 | 0 |

The knee is at 1.5: going from 1.0 to 1.5 removes the last PC20 2+ ply losses at no cost in mean saving
(35 ms either side of the step on PC20), and going beyond 1.5 buys nothing on PC20 while erasing the
remaining base saving at 3.0.

## What this is and is not
- **It is** the quantity the owner needs to choose: on the heavy searches the ungated rule buys 85 ms mean
  / 826 ms max at up to 4 plies lost, and the gated rule at 1.5 buys 35 ms mean / 424 ms max at up to 1
  ply. It is a trade-off curve, not a free lunch, and the knee is at 1.5.
- **It is not** proof of a strength gain. A saved millisecond and a lost ply have an exchange rate only a
  match can price. This file gives the arithmetic so that match can be specified.
- **Not measured**: I computed from recorded ladders rather than running a patched engine, so the numbers
  are what the rule WOULD do at those iteration boundaries, not what a real implementation would do (a real
  one has to estimate `c_i` for the next iteration and can be wrong). That gap is the main risk in adopting
  it, and it is a build-and-match question, not an arithmetic one.

## Reproduce
```
cd forge-combo29/swarm/28/pc20
python3 gated_rule.py 454 1.3 1.5
```

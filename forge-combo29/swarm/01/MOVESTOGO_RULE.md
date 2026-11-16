# The `movestogo` rule for every latency harness

**Seat 01, 2026-11-16. Confirmed on PC r15 + PC20, Threads 1, Hash 16, wtime=btime=2000, 5 runs per value,
medians. Evidence: `clampcheck/check_movestogo_clamp.txt`. Mechanism: `include/forge/clock_plan.hpp:37-48`.**

## The two rules

> **1. Never send `movestogo 0` to mean "unset".**
> **2. Never quote a plan-derived budget without the `movestogo` actually sent, since anything above 50
> silently becomes 50.**

## Why rule 1

`clock_plan.hpp:37` branches on `moves_to_go > 0`, so a **zero or negative** `movestogo` does not mean "no
limit" — it selects the **sudden-death** branch:

```
movestogo N > 0 :  soft = available/(min(N,50)+1) + inc*3/4      <- short, even-spread budget
movestogo 0 / <0:  soft = available/divisor + inc*pct/100        <- sudden-death budget (divisor 22)
```

Measured at a 2000 ms clock: **`movestogo 0` = 482 ms, `movestogo -1` = 487 ms, no `movestogo` token at all
= 57 ms.** So sending `0` "to ignore the field" gives **8.4x the plan of omitting it**, and 18x the
`movestogo 50` budget. To get the no-movestogo behaviour, **omit the token**.

## Why rule 2

`clock_plan.hpp:38` is `mtg = moves_to_go < 50 ? moves_to_go : 50`, so anything above 50 is clamped:

| `movestogo` | 50 | 51 | 100 | 1000 |
|---|---|---|---|---|
| median wall time | 25.9 ms | 25.5 ms | 26.4 ms | 25.8 ms |

A 0.9 ms spread — **3.5 %** of the 50-median. Everything above 50 is indistinguishable from 50, so a harness
that requests a large `movestogo` to "spread the clock over many moves" gets **50**, and its expected
per-move budget is wrong by `movestogo/50`.

## The consequence in one line

A budget computed from the plan is only reproducible if the `movestogo` you sent is also recorded — because
the engine may have used a different number than the one you sent, and zero is the one value that means the
opposite of what it looks like.

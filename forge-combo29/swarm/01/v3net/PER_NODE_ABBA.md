# Seat 29's own method, run on my build: 0.91× / 0.88× (S-C40)

Seat 29's `29-F59` measured per-node cost a different way than my `S-F118`: fixed node budget, 8 real-game
positions, ABBA interleaving, no profiler. That is a genuinely independent instrument, so I reproduced their method
on my build. It agrees, and it exposed two harness bugs of mine on the way.

## Result

`go nodes 200000`, 8 positions, ABBA per position (A,B,B,A), medians, `Threads 1`, `Hash 16`. Three full runs:

| mode | run 1 | run 2 | run 3 |
|---|---|---|---|
| PC20 | 0.91× | 0.91× | 0.92× |
| plain | 0.88× | 0.89× | 0.89× |

So on this build, with their method, the v3 net costs **0.88–0.92×** the per-node time of the built-in evaluation —
slightly **cheaper**, and nowhere near the 2.5× that would keep their P4 alive, let alone their predicted 4–25×.

## The three figures, and the caveat I will not bury

| route | figure | build / method |
|---|---|---|
| seat 29 `29-F59` | 0.96× PC20, 1.16× plain | their build, their box, fixed node budget |
| my `S-F118` | **1.09×** | this build, `bench 13` wall medians, 4 file-backed runs |
| my `S-C40` (their method, my build) | **0.91× / 0.88×** | this build, fixed node budget, ABBA |

**The two of my own figures disagree in SIGN** — 1.09× says the net is dearer per node, 0.88–0.92× says cheaper.
That is not a rounding difference and I am not going to average it away. What both agree on, and what the claim
actually is:

* the per-node difference is **small** — everywhere inside 0.88×–1.16× across all three routes;
* therefore the **6.2–6.8× wall cost is node count**, not per-node work;
* therefore the ceiling on v3 kernel work is the v3 family's share of `bench 13` (**~19 %**), and the lever is
  search shape.

**Why the point value moves:** `bench 13` is 8 fixed positions at fixed depth, so its nodes are dominated by a few
tactical positions; the ABBA set is 8 game positions under a node budget, which weights quiet positions more. A ratio
near 1 is the easiest kind of number to move with workload choice, and this is a machine where I have already
produced two phantom timing results (`S-F74`, `S-F115`). **The defensible statement is "about the same, within
~12 %"**, and the honest note is that the direction is method-dependent.

## Two harness bugs this cost me, both already-recorded traps

**1. `quit` before `bestmove` truncates everything (Trap 11 / `S-F121`).** My first version wrote
`go nodes 200000` and `quit` into the same pipe. Every position returned `None`:

```
position  no-net nodes  net nodes
startpos  MISSING       MISSING
... 8 of 8 MISSING
```

`grep -c '^info depth'` on that input form returns **0**. The engine was fine; the pipe closed under it. This is the
same defect I recorded an hour earlier and then committed again in a new script — the rule was known and did not
transfer, which is the whole reason the gate exists.

Worse: **the script still printed a "COMPARISON with the published figures" block with zero data in it.** A reader
could have taken that for a result. It now refuses: *"NOTHING WAS MEASURED. Every position returned no reading, so no
ratio exists and none is claimed."*

**2. My control was wrong in a way that discarded every good row.** I required the two configurations to reach the
**same node count**, and printed `NON-DETERMINISTIC - DROPPED` for all 8 positions even though the counts were
perfectly reproducible. The requirement is impossible with a fixed node budget: the loop exits at an **iteration
boundary**, so two configurations with different tree shapes cross the budget at different points — startpos gave
166,281 nodes no-net and 105,432 with the net, both deterministic across repeats. **The correct control is
determinism per configuration, not equality between them.**

## A real finding that fell out of the bug

Chasing the "different node counts" I found that **`go nodes N` does not spend N nodes**:

| requested | spent | repeat |
|---|---|---|
| 200,000 | **101,640** | 101,640 |
| 500,000 | **267,839** | 267,839 |

Deterministic, repeatable, and consistently **under** the budget — about half at 200k, about 54 % at 500k. So a
harness that says "I searched 200,000 nodes" is wrong about what the engine did, and any per-node figure derived from
the *requested* budget rather than the *reported* count would be wrong by roughly 2×. That is filed as `S-F123`, and
it is why this script normalises by the measured node count from the last `info` line rather than by the request.

## What I am not claiming

* Not that the net is faster per node in general — the workload decides the sign.
* Not that seat 29's 1.16× plain figure is wrong; their box, their positions.
* Not that this settles the direction. It settles the **magnitude being small**, which is what the ceiling argument
  needs.

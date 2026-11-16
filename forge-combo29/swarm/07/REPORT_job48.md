# REPORT — seat 07, job 48: the determinism claim behind 11-S-F91 cannot rest on node counts

## What was asked / the answer / how sure

**Asked:** (cycle work) seat 11's **S-F91** claims `FORGE_FIX_HARD_LIMIT_EMERGENCY`'s real benefit is
**determinism**: sweeping `go wtime t btime t` for t = 11..60, **5 of 50** clock values differ with the
switch off, and repeating 5× the shipped build was "stable at 601 nodes 5/5 while OFF was unstable". A
falsifiable claim about a switch's value, so worth an independent check.

**Answer:** **the claim cannot be established by its own method.** Node counts at these clock values are
**not reproducible on this machine**, on either build — I found that by applying the repetition test to my
own sweep and discovering that **4 of 15 of my own sweep values were not reproduced by their repeats on
the same binary**.

**How sure:** high. This is not a marginal statistical point; the same binary produced 412 nodes once and
971 nodes five other times at the same clock value.

## What I measured

PC r15 under PC20, plus a variant with only `FORGE_FIX_HARD_LIMIT_EMERGENCY` set to 0. Threads 1,
Hash 16, fresh process per cell, `go wtime t btime t` for t = 11..60 on startpos.

**Sweep:** **15 of 50** values differ between ON and OFF (seat 11: 5 of 50). The differing values are
t = 11, 14, 15, 19, 20, 21, 31, 33, 36, 37, 38, 39, 48, 49, 57.

**Determinism, 5 fresh runs per cell on those 15 values:**

    summary: OFF unstable at 11 of 15 values; ON unstable at 8 of 15

So the shipped build is **not** stable at these clocks in my run — 8 of 15 values gave two different
node counts across five runs.

## The observation that invalidates the method (including mine)

The decisive test is not "how many values differ" but "**does a value that differs reproduce at all?**"
Comparing each sweep value against its own five repeats on the same binary:

| t | sweep ON | five repeats | reproduced? |
|---|---|---|---|
| 11 | `(d2d4, 412)` | `{(d2d4, 971)}` | **NO** |
| 14 | `(d2d4, 412)` | `{(d2d4, 971)}` | **NO** |
| 19 | `(d2d4, 412)` | `{(d2d4, 971)}` | **NO** |
| 20 | `(d2d4, 412)` | `{(d2d4, 971)}` | **NO** |
| 21 | `(d2d4, 971)` | `{(d2d4, 971)}` | yes |
| 57 | `(d2d4, 6170)` | `{(d2d4, 6170)}` | yes |

    sweep ON  value reproduced by its own repeats: 11/15   (failures at t = 11, 14, 19, 20)
    sweep OFF value reproduced by its own repeats: 13/15   (failures at t = 11, 49)

**The same binary, at the same clock value, gave 412 nodes in one invocation and 971 in five others.**
A node count under a wall-clock stop is therefore not a measurement anyone can compare across builds at
these clock values, and neither my 15/50 nor seat 11's 5/50 is a reproducible count.

## What *is* stable, and how the claim should be made

**The bestmove was stable across every repeat** — always `d2d4`, except `t=11` with the switch OFF
giving `c2c3`. So if there is a determinism benefit to measure here, it must be measured **on the move**,
not on the node count. That is a fair restatement of seat 11's thesis, and I would support it: the move
is a discrete, reproducible quantity; the node count at a 12 ms budget is not.

## Why this matters beyond one finding

It is the same lesson as 07-C42/C43 in a different guise: **a quantity that looks exact can be
irreproducible when the stopping condition is a clock.** I have now hit that twice — once with budgets
ordering (07-C42/C43) and once here. Any table comparing node counts across builds under a wall-clock
stop needs a repeat-against-itself check before it is believed, and mine did not have one until this job.

## Findings

**07-C47** in FINDINGS.md.

## Suspicions, not proven

- That seat 11's 601-node stability observation was real on their run and my machine was simply noisier
  at that moment. Both can be true; the point is that a claim of the form "X is deterministic" cannot be
  carried by a quantity that I can show is not reproducible here.

## What I did NOT do

- Did not test at larger clocks (≥ 200 ms) where the node count may well be reproducible — 07-C45's
  wtime sweep showed stable counts at 3000 ms across runs.
- Did not examine *why* the count varies: the obvious candidates are the iteration boundary landing at a
  different ply rather than a timing race, since `d2d4` stayed constant.

## What I am NOT sure about

- Whether the 412/971 difference is the search stopping one iteration later or an internal
  non-determinism. Two distinct values only, so it looks like an iteration-boundary effect, but I did
  not trace which.

## Times

See job48/stamps.txt.

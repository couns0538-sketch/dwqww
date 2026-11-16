# REPORT — seat 07, job 48b: restating 11-S-F91 on the move, the only reproducible quantity

## What was asked / the answer / how sure

**Asked:** restate S-F91's thesis on the **move**, not the node count — the only form the data supports,
with the t=11 move change as the datum that keeps it alive. And put this repeat-against-itself rule in the
FINDINGS header, stating that it applies to any node-count table under a clock stop, including my own
earlier ones.

**Answer:** both done. **On moves the thesis survives**: both builds are perfectly stable across five
repeats at every clock value tested, and the **only** move difference in the whole exercise is **t = 11**,
where the shipped build plays `d2d4` and the switch-off build plays `c2c3` — the unsearched
first-legal-move answer the switch exists to prevent.

**How sure:** high for the move data (5 repeats × 15 clock values × 2 builds, zero move variation within
any cell). The node-count evidence is withdrawn per 07-C47.

## The move data

    ON : move changed across repeats at 0 of 15 values
    OFF: move changed across repeats at 0 of 15 values

    sweep move differences between ON and OFF: [(t=11, 'd2d4', 'c2c3')]

So:

- **Reproducibility**: on the move, both builds are deterministic at these clocks. That is the property
  S-F91 was reaching for, and it holds for both builds — which is worth stating plainly.
- **Effect of the switch**: exactly one clock value in 11..60 changes the move, and at that value the
  switch-off build returns `c2c3`, the first legal move in generation order, which is what an unsearched
  fallback looks like.

## The restated thesis

> **In the band below the Move Overhead, `FORGE_FIX_HARD_LIMIT_EMERGENCY` prevents the engine from falling
> back to an unsearched first-legal move at at least one clock value (t = 11), and the move choice is
> reproducible with the switch on and off.**

That is narrower than "the switch's benefit is determinism" and it is supported by a datum rather than by a
node count. It also matches the switch's own source comment, which describes the failure it prevents.

## The rule, and its application to my own earlier tables

Added to the FINDINGS header:

> **A node count under a clock stop is not reproducible until you prove it is.** Repeat the SAME cell on
> the SAME binary before comparing anything across builds. Mine did not: at `go wtime 11 btime 11` one
> binary gave **412 nodes once and 971 on five other runs**, and 4 of 15 of my own sweep values failed
> their own repeats (07-C47). This applies to **every** node-count table under a wall-clock stop,
> **including my own earlier ones**.

**Applied to my own work, explicitly:** `job11`'s clock tables contain a `nodes` column. I checked what I
used it for — only as a parse check ("rows without nodes = 0"), never as a cross-build or cross-setting
comparison — so **job11's conclusions (0 overruns, 0 illegal moves, wall-time shares) are unaffected**.
But the column is there, and a later reader comparing those numbers across builds would be comparing an
irreproducible quantity. The header now says so.

## Findings

**07-C48** in FINDINGS.md; it supersedes the node-count part of 07-C47 while keeping its method lesson.

## Suspicions, not proven

- That t = 11 is the *only* such value in the whole space, rather than the only one in 11..60 on startpos.
  One position and a 50-value grid is what I tested; a different position could have a different band.

## What I did NOT do

- Did not sweep other positions for the same move difference, so the "at least one clock value" phrasing
  is deliberately weak.
- Did not test whether the switch changes the move at clocks *above* 60 ms.

## What I am NOT sure about

- Whether `c2c3` at t=11 is genuinely worse than `d2d4` or merely different. It is the unsearched
  first-legal move, so it carries no search evidence at all, but I did not measure a strength difference.

## Times

See job48/stamps.txt.

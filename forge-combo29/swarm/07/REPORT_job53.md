# REPORT — seat 07, job 53: check of 19-F59 (the "mirror defect" is a depth limit)

## What was asked / the answer / how sure

**Asked:** (cycle work) seat 19's **19-F59** claims the "mirror defect" on `6k1/8/5K2/8/6r1/8/8/8 w` is a
**depth limit**, not a preference for dying quickly: `go depth 16` and `depth 20` both give `f6e7`
(`cp −490`), but `depth 24` gives `f6f5` with a mate score — the longest defence. If true, a case others
might call a bug is a calibration case.

**Answer:** **confirmed. The move flips between depth 20 and depth 24.**

**How sure:** high. Depth is a discrete, reproducible quantity (07-C47), one fresh process per depth, six
depths measured.

## Results (PC r15 under PC20, Threads 1, Hash 16)

| `go depth` | bestmove | score | PV length |
|---|---|---|---|
| 12 | `f6e7` | cp −490 | 15 |
| 16 | `f6e7` | cp −490 | 17 |
| 20 | `f6e7` | cp −490 | 21 |
| 22 | `f6e7` | cp −567 | 24 |
| **24** | **`f6f5`** | **mate −16** | 26 |
| 26 | `f6f5` | mate −16 | 28 |

The score is **identical (`cp −490`) at depths 12, 16 and 20** while the PV lengthens, which is the
signature of a search that has not yet resolved the position into a mate. Between depth 20 and 24 the score
becomes a mate and **the move changes to `f6f5`** — the longer defence.

**So seat 19's reading holds:** below the depth where the longer losing line becomes visible, both moves
read `cp −490` and the engine cannot distinguish them; at greater depth the longer defence is found. That
makes it a **calibration case, not a bug** — their word, and my data supports it.

## The one difference from their numbers, stated rather than smoothed

They report depth 24 as **`mate −15` with a 29-ply line**; I measure **`mate −16` with 26 plies**. Same
move, adjacent mate distance. The likely explanations are a depth-boundary difference or a mate-distance
convention difference — 07-C40 already showed this engine's plies-to-mate convention needs care with
`2N−1` against `2|N|`. **It does not affect the conclusion**, which rests on the *move changing with depth*,
not on the distance.

## Why this one matters beyond itself

It is the cleanest example tonight of a claim that **looks like a defect and is not one**, and it is
distinguishable only by varying depth. That is the same discipline as the header rule about defects that
should vanish with more budget: here the defect *does* vanish with more depth, which is what tells you it
was a horizon artefact all along. A harness that tested only at the owner's match depth would have filed a
bug that does not exist.

## Findings

**07-C53** in FINDINGS.md.

## Suspicions, not proven

- That the engine would pick the longest defence at *any* sufficient depth, or only that it finds a longer
  one than `f6e7` at 24. I did not verify that `f6f5` line is maximal.

## What I did NOT do

- Did not test depths between 20 and 24 to find the exact flip point (22 still gives `f6e7`, 24 gives
  `f6f5`, so the boundary is 23 or 24).
- Did not check the same shape on other board classes.

## What I am NOT sure about

- Whether the `mate −16` versus their `mate −15` indicates we are reading different lines, which would
  matter if the *length* of the defence is the point rather than the move.

## Times

See job53/stamps.txt.

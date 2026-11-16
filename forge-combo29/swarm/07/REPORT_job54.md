# REPORT — seat 07, job 54: check of 20-S-F53 (the zero-node report is one shared habit)

## What was asked / the answer / how sure

**Asked:** (cycle work) seat 20's **S-F53** claims the zero-node report is **one reporting habit**, not a
quirk of any single command: "any path that reports without searching emits one `info depth` line per
depth, capped at 64 when no depth is given", identical on both builds. That directly concerns **my own
07-F1**, so it needed checking by my own harness.

**Answer:** **confirmed, on all six cases and both builds.** It also **reframes my own finding**: 07-F1 is
one symptom of a shared habit, not a `searchmoves` defect.

**How sure:** high. Six paths × two builds, all at 0 nodes, the 64-cap appearing exactly where the rule
predicts.

## Results (base 6b98f217 and PC r15/PC20, Threads 1, Hash 16, fresh process per cell)

| case | base: depth lines / nodes / bestmove | PC: same |
|---|---|---|
| `go depth 2`, mate root | **2** / 0 / `0000` | 2 / 0 / `0000` |
| `go nodes 100`, mate root | **64** / 0 / `0000` | 64 / 0 / `0000` |
| `go depth 2 searchmoves` (empty) | **2** / 0 / `0000` | 2 / 0 / `0000` |
| `go searchmoves` (no depth) | **64** / 0 / `0000` | 64 / 0 / `0000` |
| `go nodes 100 searchmoves` | **64** / 0 / `0000` | 64 / 0 / `0000` |
| `go searchmoves e2e5` (illegal) | **64** / 0 / `0000` | 64 / 0 / `0000` |

The rule predicts every row: a depth given → one line per depth (2); no depth → the 64 cap. And it makes
no difference whether the reason for not searching is a **terminal root** or an **empty restriction**.

## What this does to my own 07-F1

**07-F1 is one instance of this habit, not a `searchmoves` defect.** I had recorded it as the
empty-intersection case (`searchmoves` matching nothing), and 07-C46 pinned that scope further. On this
evidence, the correct scope is wider: **every zero-node path** emits 2 or 64 fabricated score lines.

**Consequence I should state plainly rather than defend my own patch:** my patch
(`job2`/`job29`) removes the lines for the empty-restriction case only. A repair aimed at the **shared
report path** — so that all of these emit **one** honest line — is the better shape, and seat 20 says as
much. My patch is not wrong, it is **narrower than the defect**.

## Why the shared diagnosis matters practically

Three separate "findings" could have been filed here (terminal root, empty restriction, bare
`searchmoves`), and three separate patches written. They are one line of code emitting a loop's worth of
lines, and the shared diagnosis means the owner can fix it once and close all three. That is more useful
than any single case, which is why I am recording it as a reframing of my own work rather than a separate
row.

## Findings

**07-C54** in FINDINGS.md.

## Suspicions, not proven

- That the fix is literally one line (emit once instead of per depth). Seat 20 says "one fix direction:
  emit ONE line"; I did not write or test such a patch.

## What I did NOT do

- Did not extend my own patch to the shared path. That is a change to engine behaviour for paths I have
  not fully characterised (e.g. whether any consumer relies on the 64-line form), and the owner should
  decide it.
- Did not test other "report without searching" paths (e.g. `go mate 0`, a restricted-but-drawn root).

## What I am NOT sure about

- Whether the 64 cap is deliberate or a coincidence of `max_depth` clamping to 64. The rule reproduces, but
  its origin I did not read in the code.

## Times

See job54/stamps.txt.

# REPORT — seat 07, job 55: the shared-path repair for the zero-node report

## What was asked / the answer / how sure

**Asked:** (cycle work, following 07-C54) my own patch for 07-F1 was **narrower than the defect** — it
removed the fabricated lines for the empty-`searchmoves` case only, while 07-C54 showed the same habit on
six paths across both builds. The useful next step was the repair at the **shared** path.

**Answer:** **one edit fixes all six paths, and every published number is unchanged.**

**How sure:** high. Six cases verified before and after, and all eight PC pins re-measured on the patched
build.

## The defect, located

Every path that reports without searching reaches one loop:

    src/search.cpp:2589   for (int depth = 1; depth <= max_depth; ++depth) {
    src/search.cpp:2590       result.depth = depth;
    src/search.cpp:2591       result.score = score;
    src/search.cpp:2592       emit(depth, score, {});
    src/search.cpp:2593       if (should_stop()) break;
    src/search.cpp:2594   }

`max_depth` is 64 when no depth is given, so this emits **2 or 64** fabricated `score cp 0 nodes 0` lines
for a search that never ran — on a terminal root, on an empty restriction, and on a bare `go searchmoves`
alike. That is one line of code, not three defects.

## The patch (job55/shared_report_oneline.patch.txt)

Replace the loop with a single emit at `max_depth`, with a comment stating why. The patch applies with
`patch -p1 --fuzz=0` (exit 0).

## Before and after, all six paths (Threads 1, Hash 16)

| case | base | PC r15 | **PC r15 + patch** |
|---|---|---|---|
| `go depth 2`, mate root | 2 lines | 2 | **1** |
| `go nodes 100`, mate root | 64 | 64 | **1** |
| `go depth 2 searchmoves` (empty) | 2 | 2 | **1** |
| `go searchmoves` (no depth) | 64 | 64 | **1** |
| `go nodes 100 searchmoves` | 64 | 64 | **1** |
| `go searchmoves e2e5` (illegal) | 64 | 64 | **1** |

All six still answer `bestmove 0000` with 0 nodes — the **fabricated score lines** are what is removed, not
the answer.

## Honesty pins on the patched build

    none  bench11 312866  bench13 862329  bench16 3024920  perft5 4865609
    S14   bench11 242796  bench13 656517
    PC20  bench11 278024  bench13 587276

**All eight unchanged.** That is the expected result for a repair that removes output lines rather than
changing search: it costs no search work, and a patch that *had* moved a pin would have been a sign it
reached the search.

## What this supersedes

My earlier patches — `job2` (base tree) and `job29` (PC tree) — fixed only the empty-restriction case.
**This patch is the better shape** and I say so rather than keeping the narrower one on the shelf: it
closes the terminal-root and bare-`searchmoves` cases with one edit, which is exactly what seat 20's S-F53
diagnosed.

## Findings

**07-C55** in FINDINGS.md.

## Suspicions, not proven

- Whether any consumer *relies* on the 2/64-line form. A GUI drawing a depth ladder for a terminal position
  would see one rung instead of many, which is more honest; a harness that counts `info depth` lines to
  measure "depth reached" would now read 64→1 on these paths. I noted it rather than assuming it is
  harmless everywhere.

## What I did NOT do

- Did not ship this as the engine's change — it is a text patch in my folder, per the rules.
- Did not test `go mate 0` or a restricted-but-drawn root, which may reach a different branch.

## What I am NOT sure about

- Whether `result.depth = max_depth` is the right reported depth for a position that never searched. It
  matches what the loop last set, so the change is line-count only, but a "depth 0" report might be more
  honest still. That is a presentation decision for the owner.

## Times

See job55/stamps.txt.

# REPORT — seat 07, job 29: the PC-tree patch for 07-F1, and proof it cures the defect on r15

## What was asked / the answer / how sure

**Asked:** (cycle work) 07-F1 was found on the base tree. Since it survives on the PC build under PC20
(07-C22), the useful next step is a patch that fixes it **there**, with its published numbers intact.

**Answer:** the base-tree patch does **not** apply to the PC tree (hunk 3 conflicts with the
`FORGE_FIX_ROOT_DRAWN` block), so I wrote a **separate PC-tree patch**, three edits, applying cleanly
with `patch -p1 --fuzz=0`. On the patched PC build: **all eight published numbers unchanged**, the
empty-root cases go from **64 zero-node depth lines to 0**, `bestmove 0000` still returned, and every
control behaves exactly as before — including the 19-F12 abort case, which this patch deliberately
does not touch.

**How sure:** high. Pins are exact; before/after behaviour is measured with the same harness; the
controls in the same run are unchanged.

## Why a second patch was needed

    base tree: hunk 1 at 2200, hunk 2 at 2208, hunk 3 at 2256   -> applies with --fuzz=0
    PC tree  : hunks 1 and 2 succeed with offset +321, hunk 3 FAILED at 2260

The PC tree wraps the drawn-root score in `#if !FORGE_FIX_ROOT_DRAWN ... #endif`, so the anchor text
for hunk 3 moved. Rather than weaken the patch with fuzz, I regenerated it against the PC tree's own
text.

## The patch (job29/job29_pc_searchmoves_empty_root.patch.txt)

Three edits, identical in intent to the base patch:

1. a local `bool restricted_root_empty = false;` beside `root_candidates`;
2. `restricted_root_empty = result.restricted_root_empty;` right after the existing detection at
   search.cpp:2531 — reusing the engine's **own** predicate, not inventing one;
3. inside the empty-root branch, before the depth loop: return without emitting any depth line, with
   `result.nodes` and `result.elapsed_ms` still filled in.

`best_move` is left `none` on purpose, so the UCI layer keeps printing `bestmove 0000` exactly as
before — no protocol change, nothing for a GUI to relearn.

## Results on the patched PC build (PC20, Threads 1, Hash 16)

Pins — every published number still exact:

    none  bench11 312866  bench13 862329  bench16 3024920  perft5 4865609
    S14   bench11 242796  bench13 656517
    PC20  bench11 278024  bench13 587276

Behaviour — the defect is gone, the controls are untouched:

| case | before | after |
|---|---|---|
| 07-F1 `go searchmoves e2e5` | `0000`, **64** zero-node depth lines | `0000`, **0** depth lines |
| no-match + node budget | `0000`, **64** zero-node depth lines | `0000`, **0** depth lines |
| 19-F12 `go depth 12` + quit | `a2a3`, 0 depth lines | `a2a3`, 0 depth lines (**unchanged, different path**) |
| control `searchmoves e2e4` | 33 depth lines, 50,224,817 nodes | identical |
| discriminator 2a/2b/2c/2d | 21600 / 11458 / 17308 / 11191 nodes | identical |

## What this proves and what it does not

**Proves:** 07-F1 exists on the PC build and a three-edit patch removes the fabricated score line
without moving a single node count on any published bench, and without disturbing the abort path.

**Does not prove:** that the owner wants this behaviour. Withdrawing the depth line is a judgement:
I chose "print no score at all" over "print a score with the real explanation", because an absent line
cannot be misparsed while `score cp 0` is a false claim. `REPORT_job2.md` argues this from the code
(2210/2531 already detects the state); Opus may still prefer a different presentation.

**Also not proven:** that this is the only remaining instance of the pattern. 07-C22 shows the abort
path at 3017 is a *different* fallback, and I have not patched that one.

## Findings

**07-C22** (three reported symptoms = two paths) and **07-C23** (this patch, verified on r15).

## Suspicions, not proven

- The 19-F12 fallback (`root_candidates.front()` at 3017) answers a legal move with no score. That is
  arguably acceptable for an aborted search, but seat 19's report and my discriminator both show the
  move is the *first in generation order*, which is not a searched move. Whether that deserves a fix
  is a judgement I have not made.

## What I did NOT do

- Did not patch the 19-F12 path.
- Did not test the patch under ASan/UBSan on the PC build (the change is three lines of control flow
  with no arithmetic; the base patch's reasoning carries over, but I did not re-run the sanitizer).

## What I am NOT sure about

- Whether the owner's PC build has other divergences from this patched copy (file 5 says the patch
  reproduces the PC source byte for byte, and my pins match, so I believe not).

## Times

See job29/stamps.txt.

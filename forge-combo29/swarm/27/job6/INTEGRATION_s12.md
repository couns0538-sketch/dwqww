# Integration check: seat 27's drawn-root patch + seat 12's two-doors patch

Why this matters: seat 12's `two_doors_mate.patch.txt`, seat 01's `fifty_move_mate.patch.txt` and my
`drawn_root_reporting.patch.txt` all rewrite the **same** block of `src/search.cpp` (the drawn-root
adjudication at ~2248-2270). Opus has to know they are not independent before merging any of them.

## What I ran

Base `6b98f217`, clean copy. **CORRECTION: the two commands below are the ORIGINAL ones I ran; the comment on
the first line was wrong and is annotated rather than silently rewritten, because this file is the record of a
mistake.** The verified correct levels are in "Warning for Opus" at the bottom and in PATCHES.md.

```
patch -p2 < seat12/two_doors_mate.patch.txt     # WRONG AS WRITTEN: -p2 works from INSIDE forge-combo29/,
                                                # not from the repo root. From the root it must be -p1.
                                                # (I ran it as -p2 from inside, which is why it applied.)
patch -p1 < seat27/job1/drawn_root_reporting.patch.txt   # correct: -p1 from inside forge-combo29/
```

`patch` reported `Hunk #1 succeeded at 2275 (offset 19 lines)` — an offset, no fuzz, no failed hunk.

## Resulting code (read, not assumed) — the two changes compose correctly

Seat 12's mate scan runs first and decides `root_draw_adjudicated`; my block then reports **one** line
instead of the depth ladder:

```cpp
const bool root_drawn = root_draw_adjudicated;
if (root_candidates.empty() || root_drawn) {
    ...
    // A drawn root is a claim, not a finished search: report one line, at depth 1,
    result.depth = std::min(1, max_depth);
    result.score = score;
    emit(result.depth, score, {});
```

## Verified behaviour (paced driver, fresh process per row)

Position `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - <clock> 60` — White has Ra8# available:

| clock | base `e06310ec` | seat12 + mine `80b5e535` |
|---|---|---|
| 100 | 8 info lines, `score cp 0`, **`bestmove f2f3`** | 8 info lines, **`bestmove a1a8`** |
| 99 (control) | `bestmove a1a8` | `bestmove a1a8` |

So at clock 100 the base build hides a mate-in-one behind the draw adjudication and plays a pawn move;
with seat 12's mate scan the same position finds `a1a8`, and my patch keeps the reporting honest (one
`info` line rather than a claimed depth ladder). The clock-99 control is identical on both builds, so the
difference is the patch and not noise.

## Honesty numbers for the combined build `80b5e535`

bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four unchanged
(raw in `job6/honesty_integ/`).

## Warning for Opus

- **CORRECTED (seat 12 found this; the line that used to sit here was wrong twice over): order does not
  matter, and the `-p` level is `-p1` from the repo root for seat 12's patch** (not `-p2` from the root, which
  fails) **or `-p2` from inside `forge-combo29/`**. Mine takes `-p1` from inside `forge-combo29/`.
  Measured on a clean `6b98f217` archive: `-p2` from the root → `Skipping patch. 1 out of 1 hunk ignored`;
  `-p1` from the root → `checking file forge-combo29/src/search.cpp` and it applies. A script that assumes one
  prefix for both patches will silently skip one, so check every exit code.
- **CORRECTION (seat 12 found this; my original text here was wrong): order does not matter.** Both orders
  succeed and give a byte-identical `src/search.cpp`, sha256 `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`.
  My claim that "mine first then seat 12's fails" came from running seat 12's patch at the wrong `-p` level
  (`-p1` from inside `forge-combo29/`, where it needs `-p2` or `-p1` from the repo root). The real constraint is
  the `-p` level per patch, plus checking every exit code. See PATCHES.md at the top of my folder.
- Take seat 12's patch on its own merits (it is their finding and their test); I am reporting only that
  the two do not collide and that the combination is better than either alone on the clock-100 case.

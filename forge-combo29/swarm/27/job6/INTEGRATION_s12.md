# Integration check: seat 27's drawn-root patch + seat 12's two-doors patch

Why this matters: seat 12's `two_doors_mate.patch.txt`, seat 01's `fifty_move_mate.patch.txt` and my
`drawn_root_reporting.patch.txt` all rewrite the **same** block of `src/search.cpp` (the drawn-root
adjudication at ~2248-2270). Opus has to know they are not independent before merging any of them.

## What I ran

Base `6b98f217`, clean copy, from the repository root's parent:

```
patch -p2 < seat12/two_doors_mate.patch.txt     # their patch is -p2 against the repo root
patch -p1 < seat27/job1/drawn_root_reporting.patch.txt   # mine is -p1 against forge-combo29/
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

- **Apply seat 12's patch with `-p2` from the repository root**, mine with `-p1` from `forge-combo29/`.
  With `-p1` seat 12's patch fails cleanly (`Skipping patch. 1 out of 1 hunk ignored`) — it does not
  half-apply, which is good, but a script that assumes one prefix will silently skip it.
- **CORRECTION (seat 12 found this; my original text here was wrong): order does not matter.** Both orders
  succeed and give a byte-identical `src/search.cpp`, sha256 `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`.
  My claim that "mine first then seat 12's fails" came from running seat 12's patch at the wrong `-p` level
  (`-p1` from inside `forge-combo29/`, where it needs `-p2` or `-p1` from the repo root). The real constraint is
  the `-p` level per patch, plus checking every exit code. See PATCHES.md at the top of my folder.
- Take seat 12's patch on its own merits (it is their finding and their test); I am reporting only that
  the two do not collide and that the combination is better than either alone on the clock-100 case.

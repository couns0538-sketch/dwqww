# The stricter no-search sweep: it counts zeros correctly, and cannot tell a legitimate zero from a broken one

seat 19 · area 9 · the third and last sweep attempt, reported with what it can and cannot establish.

## 1. The three lines

**What I did.** Built a sweep using the closing check from `HARNESS_TRAPS` (traps 1 and 1b together): a search
happened only if **`nodes > 0` AND the PV is non-empty**. Crucially it looks at **the last `info` line before each
`bestmove`**, so it is **immune to the `readyok` interleaving** that broke my per-search attempt (19-C16).

**The result.** It reports, across all 49 branches: **seat 21 469 zero-node of 6,770 claimed**, seat 05 320/425,
27 219/1,557, 25 186/267, 15 140/2,206 (and 6 empty-PV), 17 52/2,938, 24 24/2,315, 07 10/250, 02 9/113,
10 6/1,135, 20 4/234, 30 4/12.

**And it still cannot be used as a defect count, for a reason that is now clear:** **`nodes 0` is the engine's
CORRECT answer on terminal and drawn roots.** Seat 21 is the area-1 seat that *studies* those positions — its
`asan_raw_031.txt` shows `info depth 1/2 ... score cp 0 nodes 0 ... pv` (empty) followed by a real `bestmove`,
because the root is drawn. **That is the behaviour it was measuring, not a defect.**

**How sure.** Certain of the counts (mechanical). Certain that at least the seat-21 majority is legitimate (I read
the file). **Therefore the total is not a defect count and I am not reporting one.**

## 2. Why the mechanism is now understood

The three sweeps each failed in an *instructive* way:

| sweep | approach | why it could not work |
|---|---|---|
| 19-C13 (input files) | find files whose last `go` has only `quit` after it | flags *suspicion*, not defect — and "committed" ≠ "currently used" (19-C21) |
| 19-C14 / 19-C16 (outputs) | zero `info` lines per file / per `bestmove`-block | indentation bug, then block boundaries broken by interleaved `readyok` |
| **19-C34 (this)** | last `info` before each `bestmove` has `nodes 0` or an empty PV | **robust mechanically, but `nodes 0` is legitimate on drawn roots** |

**The lesson: a static sweep of committed output cannot distinguish "the search didn't happen" from "the search
correctly returned nothing", because both produce `nodes 0` and an empty PV.** The distinguishing information is
**the position** — a drawn/terminal root explains a zero and an aborted search does not. **Any usable version must
replay the position or read the driver's command stream, not just the output.**

## 3. What the seat-level counts do suggest

Not a defect rate, but a **map of who writes zero-node output at all**, which is where a real problem *could* live:

- **Seat 21's 469 of 6,770 is the largest and is expected** — it is the terminal-position seat by design.
- **Seat 05's 320 of 425 is high in proportion** (75 %). Its work includes mate and fifty-move-horizon boards
  where a zero-root answer is plausible — but a 75 % rate is worth its owner glancing at, since it is high enough
  that a *broken* zero could hide inside it without moving the number much.
- **Seat 25's 186 of 267 (70 %) and 95 files** likewise.
- The rest are small proportions.

**I am deliberately not turning those into findings.** A percentage of legitimate zeros cannot show a defect; it
can only say where to look. That is what I did with seats 10 and 07 in 19-C15 — opened them, found deliberate
work, said so — and the same courtesy applies here.

## 4. Finding

**19-C33 — a `nodes 0` / empty-PV sweep is mechanically robust (immune to the `readyok` interleaving of 19-C16)
but CANNOT produce a defect count, because `nodes 0` with an empty PV is the engine's CORRECT answer on any drawn
or terminal root.** Seat 21's 469 of 6,770 claimed searches are of exactly that kind — verified by reading
`job1/out_asan/asan_raw_031.txt`, where a drawn root gives `score cp 0 nodes 0` and an empty pv before a real
`bestmove`. **The distinguishing information is the position, not the output**, so any usable version must replay
the position or read the driver's commands. Seat-level counts are a map of where zeros are written, not a defect
rate; 05 (320/425) and 25 (186/267) are the only proportions high enough that a real zero could hide inside, and I
did not open them.

### What I did NOT do

- I did not replay positions to classify each zero as legitimate or aborted. **That is the correct next step** and
  it is a different tool: for each zero-node search, re-run the position and ask whether the root is drawn.
- I did not open seats 05's or 25's zero-heavy files.
- I did not delete the two earlier, broken sweeps — they are the evidence for §2.

## 5. Files

`checks/sweep_nosearch.py`, `checks/sweep_ns/RESULT.txt`; earlier attempts at `checks/sweep/`,
`checks/sweep_out2/`, `checks/sweep_ps/`.

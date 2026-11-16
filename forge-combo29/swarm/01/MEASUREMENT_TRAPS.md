# The two settings that silently change what a harness measures

**Seat 01, 2026-11-16. One page, ready for the brief. Both are confirmed by me on PC r15 + PC20, Threads 1,
Hash 16, and both have the same shape: the default is fine, a plausible non-default silently changes the
measurement, and nothing warns you.**

> **Assert and record `Threads 1`, `MultiPV 1`, and never send `movestogo 0`.**

## Trap 1 — `MultiPV` above 1 divides a node budget (S-C21)

The M lines are produced from the same N nodes, so a fixed budget buys fewer plies:

| budget | MultiPV 1 | MultiPV 4 | MultiPV 8 |
|---|---|---|---|
| `go nodes 20000` | depth 10 | depth 8 | **depth 7** |
| `go nodes 50000` | depth 12 | depth 10 | **depth 8** |
| `go softnodes 2000` | depth 8 | depth 3 | **depth 2** |

The loss is **sublinear** in M (the budget is spent line-by-line per depth, not divided), and the deepest depth
often carries a **truncated line set** — 5 of 9 MultiPV>1 cells in my run reported fewer lines than the setting,
so a GUI reading all M lines gets stale ones.

**Why it bites:** MultiPV above 1 is a plausible leftover from an analysis session. A benchmark run afterwards
measures a smaller search and reports it as the engine being slower or shallower.

## Trap 2 — `movestogo` zero means the opposite of "unset" (S-F62)

`clock_plan.hpp:37` branches on `moves_to_go > 0`, so **zero or negative selects the sudden-death branch**:
at a 2000 ms clock, `movestogo 0` = **482 ms**, `movestogo -1` = **487 ms**, and **no token at all = 57 ms** —
**8.4x** the plan of omitting it. And above 50, `movestogo` is silently clamped to 50 (medians 25.9 / 25.5 /
26.4 / 25.8 ms for 50 / 51 / 100 / 1000 — a 3.5 % spread).

**Why it bites:** the intuitive way to "ignore a field" — send zero — is the one value that changes the plan in
the wrong direction, by nearly an order of magnitude.

## The third, already in the brief — `Threads` above 1

Score, node count and sometimes the move vary run to run, by design (shared hash). One thread per game.

## The common shape, and the guard

All three are **settings whose name suggests they do not matter to the measurement**. So:

1. **Assert them explicitly** at the top of every harness: `Threads 1`, `MultiPV 1`, and never `movestogo 0`.
2. **Record them in the output**, not just in the script — a result file that does not state Threads and MultiPV
   cannot be compared with one that does.
3. When a number looks wrong, **check the settings before the engine**: two of tonight's three were a setting,
   not a search defect.

This is the same family as the attribution rule: the failure is never in the number, and it is never announced.

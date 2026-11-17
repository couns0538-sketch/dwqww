# The settings that silently change what a harness measures

**Seat 01, 2026-11-17. One page, ready for the brief. Every trap below is confirmed by me on PC r15 + PC20,
Threads 1, Hash 16. All four share one shape: the default is fine, a plausible non-default silently changes the
measurement, and nothing warns you.**

> ## THE RULE
>
> **Assert and record `Threads 1` and `MultiPV 1`, and to mean "no limit" OMIT the token — never send 0.**

## Trap 1 — `MultiPV` above 1 divides a node budget (S-C21)

The M lines are produced from the same N nodes, so a fixed budget buys fewer plies:

| budget | MultiPV 1 | MultiPV 4 | MultiPV 8 |
|---|---|---|---|
| `go nodes 20000` | depth 10 | depth 8 | **depth 7** |
| `go nodes 50000` | depth 12 | depth 10 | **depth 8** |
| `go softnodes 2000` | depth 8 | depth 3 | **depth 2** |

The loss is **sublinear** in M (the budget is spent line-by-line per depth, not divided), and the deepest depth
often carries a **truncated line set** — 5 of 9 MultiPV>1 cells in my run reported fewer lines than the setting.

**Why it bites:** MultiPV above 1 is a plausible leftover from an analysis session. A benchmark run afterwards
measures a smaller search and reports it as the engine being shallower.

## Trap 2 — `movestogo 0` means the opposite of "unset" (S-F62)

`clock_plan.hpp:37` branches on `moves_to_go > 0`, so **zero or negative selects the sudden-death branch**: at a
2000 ms clock, `movestogo 0` = **482 ms**, `movestogo -1` = **487 ms**, and **no token at all = 57 ms** — **8.4x**
the plan of omitting it. Above 50 it is silently clamped to 50 (medians 25.9 / 25.5 / 26.4 / 25.8 ms for
50 / 51 / 100 / 1000 — a 3.5 % spread).

## Trap 3 — `depth 0` is one ply, not "no limit" (S-C28, S-F87)

`go depth 0` **clamps to one ply** — measured **depth 1, 155 nodes** — while **omitting the field reaches depth 21**
(1,493,714 nodes) in the same wall time. A **21-fold depth loss** from the value a harness is most likely to send
when it means "unset". The other limits behave consistently: `go movetime 0` still reached **depth 6** (993 nodes,
1.3 ms — a floor, not zero time), and only `go nodes 0` is honoured literally, answering at once with a different
move (`f5f4` against the control's `b6b5`).

## Trap 4 — `Threads` above 1 varies by design (already in the brief)

Score, node count and sometimes the move change run to run, because the threads share one hash table. One thread
per game; state it and record it.

## The family, and why one rule covers all four

**To mean no limit, omit the token.**

| what a harness sends to mean "unset" | what it actually does |
|---|---|
| `movestogo 0` | selects the **sudden-death** branch: 482 ms per move instead of 57 ms — 8.4x the plan of omitting the token |
| `depth 0` | clamps to **one ply**: depth 1 in 155 nodes, against depth 21 when the field is absent — a 21-fold loss |
| `MultiPV` above 1 | **divides the node budget** across the lines: depth 10 → 7 at 20,000 nodes, depth 8 → 2 on `softnodes 2000` |
| `Threads` above 1 | **varies by design**: score, node count and sometimes the move differ run to run |

All four are settings whose **name** suggests they do not matter to the measurement, and each changes the search
in the direction opposite to the intent. That is why the rule is uniform: **never send a value meaning "unset";
omit the field.**

## The guard

1. **Assert them explicitly** at the top of every harness: `Threads 1`, `MultiPV 1`, omit `movestogo`/`depth`
   rather than sending 0.
2. **Record them in the output**, not just in the script — a result file that does not state Threads and MultiPV
   cannot be compared with one that does.
3. When a number looks wrong, **check the settings before the engine**: all four of these were a setting, not a
   search defect.

This is the same family as the attribution rule: the failure is never in the number, and it is never announced.

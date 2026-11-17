# The five things that silently change what a harness measures

**Seat 01, 2026-11-17. One page, ready for the brief. Every trap below is confirmed by me on PC r15 + PC20,
Threads 1, Hash 16. Four are settings and one is a timer, and all five share one shape: the default is fine, a plausible
non-default or a careless measurement silently changes the number, and nothing warns you.**

> ## THE RULE
>
> **Assert and record `Threads 1` and `MultiPV 1`; to mean "no limit" OMIT the token — never send 0; and time
> from immediately before `go` on a warmed process, verified with a `time 0` search.**

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

## Trap 5 — caller wall is only sound if the timer starts after the preamble (S-C32, S-F92)

Not a setting this time, but the same species: a measurement that quietly includes the apparatus.

Seat 27's clock findings were retracted after it found **1,300 ms of harness** (Python startup, subprocess spawn,
UCI preamble) charged to the clock on a search the engine reports as `time 0`. Its own `time` field showed
329/328/322 ms against a 433 ms hard limit — inside the plan all along.

**The rule is about WHERE the timer starts, not whether the caller times at all:**

> **Time from immediately before `go` on a warmed process, and verify with a `time 0` search that the residual is
> a few milliseconds.**

| harness | residual on a `time 0` search |
|---|---|
| mine (timer immediately before `go`, preamble already read to `readyok`) | **0.89 ms** |
| seat 27's (startup + spawn + preamble charged) | **1,300 ms** |

Cross-check against the engine's own `time` field: `go wtime 6000 …` caller 288.71 vs engine **288** (gap
**0.71 ms**); `movetime 500` 490.65 vs 473; `nodes 20000` 11.33 vs 6. So a sound caller measurement and the
engine's own field agree to tens of milliseconds, and the zero-time control proves it in one search.

A rule phrased as "never use caller-measured wall" would forbid a method that is demonstrably fine; the control is
what distinguishes the two cases.

## The family of four settings, and why one rule covers all of them

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
3. When a number looks wrong, **check the settings and the timer before the engine**: four of these five were a
   setting and the fifth was the measurement itself — none was a search defect.

This is the same family as the attribution rule: the failure is never in the number, and it is never announced.

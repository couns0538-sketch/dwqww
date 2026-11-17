# The nine traps that silently change what a harness measures — including two about the harness itself

**Seat 01, 2026-11-17. One page, ready for the brief. Every trap below is confirmed by me on PC r15 + PC20,
Threads 1, Hash 16. Four are settings, one is a timer, one is a command whose safety depends on the position,
one is a measurement whose truth depends on the setting, and one is the act of typing — and all eight share one shape: the default is fine, a plausible
non-default or a careless measurement silently changes the number, and nothing warns you.**

> ## THE RULE
>
> **Assert and record `Threads 1` and `MultiPV 1`; to mean "no limit" OMIT the token — never send 0; time from
> immediately before `go` on a warmed process, verified with a `time 0` search; and put a wall cap and a node cap
> on every fixed-depth command.**

**A note on this page's own shape.** I appended Trap 3 and Trap 5 after the closing sections before this was
corrected — twice — and the row checker reported the file clean each time, because it counts table cells and not
section order. `check_page_shape.py` exists for that gap: it prints the heading sequence, flags duplicates and
empty sections, and flags anything stranded after closing material.

## Trap 0 — a hand-typed number and a measured number look identical (why tables are pasted)

Before the settings traps: the one that produces wrong numbers out of correct measurements.

I transcribed `depth 8 → 20/26` into a finding when the committed sweep had printed **`26/26`** — a figure carried
across from an adjacent row while writing by hand. The measurement was right; the sentence was wrong; nothing about
"20/26" looks more suspicious than "26/26".

> **A plausible wrong number looks exactly like a right one.**

So: **tables in a report are the pasted output of a committed script, never retyped.** A transcription error is
invisible to every plausibility check the author applies, because the wrong number reads as naturally as the right
one — and only the script knows which it is.

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

## Trap 6 — a fixed-depth command needs a wall cap AND a node cap, because safety is a property of the POSITION

`go depth 20` untimed finished in **0.0 s** on my mate boards and **did not finish in 90 s** on a K+Q board at
halfmove 80, where it reached **depth 15 at 250,077,687 nodes** (seat 10's 10-F65, confirmed as S-C34).

**The mechanism: a short forced mate breaks the iterative loop early** — the loop exits as soon as a mate is found,
so the search never grinds to the requested depth. **A high-halfmove bare-queen endgame has no short mate and both a
long mate search and the fifty-move horizon active**, so it grinds through hundreds of millions of nodes to
complete one depth.

So the same command is safe on one board and a grind on another, and **the trigger is the board, not the call**:

> **Any `go depth N` in a harness gets a wall cap and a node cap. Whether it is safe is a property of the position.**

A harness without a cap cannot tell "slow" from "hung", which is exactly how this reads when it happens.

## Trap 7 — a play-out is ground truth only for the player that plays it

A play-out is a better test than reading a score: it plays the game out and lets an independent library adjudicate,
so a wrong score cannot hide the consequence. **But it does not remove the engine from the PLAY** — both sides are
moved by the same depth-limited searcher, so the same first move can produce a 40-ply defence at depth 10 and a
16-ply one at depth 12.

Measured on one board with two candidate first moves (`c6d6` / `c6c7` plies survived, 3 deterministic runs each):

| play-out setting | plies survived | reading |
|---|---|---|
| depth 8 | **26 / 26** | equal |
| depth 10 | **24 / 40** | second move better by 16 |
| **depth 12** | **20 / 16** | **second move worse by 4** |
| depth 14 | **22 / 32** | second move better by 10 |
| nodes 5k / 20k / 50k | 20 / 22 | second move better |

**One setting supports the claim, one ties, three reverse it.**

> **A play-out measures "self-play survival at depth D", not objective move quality. State D, and show the ordering
> is stable across a range — or do not call it ground truth.**

**Truth, like safety, is a property of the configuration.**

## Trap 8 — a test that cannot fire returns the same answer as a test that found nothing

The subtlest one, and the only one in this page that is about the HARNESS rather than the engine.

I tested whether the built-in book answers `position startpos` using `go depth 12`. It reported **0 of 3** — a
clean negative. But the book is probed only when `game_search` holds, i.e. for **clock or movetime** searches
(`uci.cpp:681`); a depth search **can never** produce a book answer. The instrument was structurally incapable of
firing, and its empty result read exactly like a measurement that found nothing. Re-run with a clock search: **3
of 3**.

> **Before trusting a negative, show that the test CAN return a positive.** A test that cannot fire and a test that
> found nothing report identically.

The cheapest form of that proof is the same one used for the sanitizer zero and the mirror check: **plant the
positive**. Here it was a `go wtime` search; elsewhere it is a fake engine, a planted fault, or a second position.

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

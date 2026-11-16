# NOTE — two silent runaways: a bad node budget, and a clock line with no usable time in it

**THE TWO RULES, in one line each:**
1. **Send a node budget only after validating it as a positive integer** — an unusable value means *no* node limit.
2. **Send the MOVER's own clock, or both clocks; never the wrong side's clock alone, and never `movestogo` unless it is genuinely known** — `movestogo 0` is read as maximum urgency and quadruples the time spent.


Seat 30, area 10. **Both of these are HARNESS TRAPS, not engine defects.** The engine computes
correct chess in both cases; it simply does not stop. Both are silent — a driver waiting for
`bestmove` with no wall-clock guard waits forever, and a driver that closes stdin instead gets a
fabricated move (19-F12). They are the same shape, and a harness that guards against neither will
hang on someone else's machine and look like an engine bug.

Builds: **PC r15** (base `6b98f217` + the `FABLE_TO_swarm_5.md` patch, `-DFORGE_MATE_ALPHA_GUARD=1`,
sha256 `068f0927…`) and **base** (`6b98f217`, `e06310ec…`). Both: Threads 1, Hash 16, OwnBook false,
every setoption confirmed by `readyok`, every row a fresh process.

Reproduce both at once: `python3 forge-combo29/swarm/30/check11/runaway_traps.py out_traps 20`
(raw: `check11/out_traps/runaway_traps.json`).

## Trap 1 — a `go nodes` value that is not a positive integer means NO node limit

```
position startpos
go nodes -1          # also: go nodes xyz    go nodes depth 5
```

| go line | build | answered in 20 s? | nodes reached |
|---|---|---|---|
| `go nodes -1` | base | **NO** | 207,603,225 (120 s run) |
| `go nodes xyz` | base | **NO** | 168,212,008 (120 s run) |
| `go nodes depth 5` | base | **NO** | 207,603,225 (120 s run) |
| `go nodes 200000` (control) | both | yes | 101,640 |
| `go nodes -1` / `xyz` / `depth 5` | **PC r15** | **yes, 0.00 s** | `a2a3` / `c2c4` / depth 5 obeyed |

The PC build repairs this (`FORGE_FIX_GO_PARSE`). The base tree treats an unusable value as "no
limit", so a driver that relies on that budget to end the search never gets a move.
`stop` does recover it (0.01 s), and a second limit rescues the line outright
(`go nodes -1 depth 5` answers at once) — so a harness that always sends a depth or clock beside its
node budget cannot fall into it.

**Rule: never send a node budget you have not validated as a positive integer.**

## Trap 2 — a one-sided clock is not a short clock, it is NO clock

> **A one-sided clock is not a short clock, it is no clock.**

```
position fen 2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 b - - 18 55
go wtime 0            # NO btime field
```

| go line | build | answered in 20 s? | nodes reached |
|---|---|---|---|
| `go wtime 0` | PC r15 | **NO** | 26,264,563 |
| `go wtime 1000` | PC r15 | **NO** | **26,264,563 — identical** |
| `go wtime 0` | base | **NO** | 41,641,416 |
| `go wtime 1000` | base | **NO** | **41,641,416 — identical** |
| `go wtime 0 btime 0` (control) | both | yes, 4 ms | depth 1 / 39 nodes |
| `go wtime 1000 btime 1000` (control) | both | yes | depth 18 / 53,919 |

With the mover's own clock absent, the OTHER side's clock value is irrelevant: `wtime 0` and
`wtime 1000` produce the same tree to the node. The engine is not swapping or ignoring clocks — it
reads `wtime` for White and `btime` for Black (src/uci.cpp:121-124) exactly as it should, and with
`OwnBook false` explicitly set (a book reply is instant and hides all of this) the mover's OWN clock
is obeyed properly: on this Black-to-move board `go btime 0` -> depth 1 / 39 nodes / 4.1 ms and
`go btime 1000` -> depth 12 / 27,183 nodes / 24.4 ms, while `go wtime 0` runs to 27,302,675 nodes and
no bestmove. So the precise rule is: **omit the mover's own clock and the search is unbounded**;
that is a malformed `go` line, not a clock bug.

(Seat 27 originally reported this area as a "clock swap" and has since withdrawn that, correctly
attributing its own anomaly to `OwnBook` being left on. My measurement is a different fact and
survives its retraction — see 30-C46. Both of us were caught by harness details, which is the point
of this page.)
That is what seat 27 measured as "the clock is ignored"; the real cause is the **missing field**, not
the side to move (see 30-C40/C41/C42/C43). With both clocks present the engine obeys the clock
monotonically (30-F51).

**Rule: send the MOVER's own clock, or both clocks — never the wrong side's clock alone.**
(Narrowed from my earlier "always send both clocks", which was safe advice but not the cause: on a
WHITE-to-move board `go wtime 6000` alone is the mover's own clock and works normally at depth 16 /
223,639 nodes / 136 ms, while on a BLACK-to-move board `go wtime 6000` alone runs to 26,264,563 nodes
with no bestmove and `go btime 6000` alone works at depth 26 / 328,863 nodes / 160 ms — 30-C49.)

## Why these belong together

| | trap 1 | trap 2 |
|---|---|---|
| trigger | a node value that is not a positive integer | a clock line with one side missing |
| what the engine does | searches with no node limit | searches with no time plan |
| nodes before I killed it | 207,603,225 | 41,641,416 |
| symptom for the driver | no `bestmove`, forever | no `bestmove`, forever |
| looks like | an engine hang | an engine hang |
| actually is | a malformed `go` line | a malformed `go` line |

A THIRD, related trap on the same `go` line (30-F55): **`movestogo 0` is read as maximum urgency.**
At the owner's own match clock, `go wtime 6000 btime 6000 winc 60 binc 60` spends 498 ms of a
6,060 ms budget (8 %), while the same line plus `movestogo 0` spends **2,023 ms (33 %)** — 4.1x the
time from one placeholder field, 3 of 3 identical. Omit `movestogo` unless it is genuinely known.

In all three cases the fix is in the harness, not the engine: validate the budget, send both clocks, and
**always** run searches under a wall-clock guard that reports `RUNAWAY` rather than blocking. On the
base tree the node-budget form additionally has a one-line engine repair (the PC build has it); the
one-sided-clock form has no engine-side fix at all, because a `go` line that omits a clock carries no
time information to obey.

Findings: **30-F25/F26/F28, 30-C25** (node budget), **30-C40/C41/C42, 30-F52/F53** (one-sided clock).
Companion note on the node-budget trap in more detail: `NOTE_go_nodes_budget.md`.

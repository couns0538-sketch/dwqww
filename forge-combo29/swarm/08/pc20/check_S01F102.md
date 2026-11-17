# CHECK of seat 01's S-F102 / S-F103 — the book cannot fire on a depth search — seat 08

Their claim:
> S-F102/S-F103: "the book is probed only when `game_search` holds — clock or movetime — so a depth search can NEVER
> produce a book answer ... my first run reported 0/3 book fires because I used `go depth 12` ... Corrected to a clock
> search, the same harness then reported 3/3."

## Verdict: CONFIRMS — all four clauses, with the planted positive built in

My own harness, PC r15 under PC20, Threads 1, Hash 16, **OwnBook true** (without that the test is meaningless, and I
say so as a control). Three opening positions reached by move lists: startpos, `1.e4`, `1.e4 e5`.

| `go` form | book lines | note |
|---|---|---|
| **`go depth 12`** | **0 of 3** | info depth lines printed normally (12 each) — a real search, no book |
| **`go wtime 6000 btime 6000`** | **3 of 3** | `info string book move …`, 0 info depth lines |
| **`go movetime 100`** | **3 of 3** | same |
| `go wtime 6000` with **OwnBook false** | **0 (suppressed)** | 19 info depth lines, a real search |

| their statement | my measurement |
|---|---|
| a depth search can **never** produce a book answer | **0 of 3** |
| a clock search does | **3 of 3** |
| `movetime` is the other `game_search` form | **3 of 3** |
| the option is what gates it | **OwnBook false suppresses it, 0 book lines with a real 19-line search** |

**The 0-of-3 and the 3-of-3 are in the same run, on the same positions, through the same harness** — so the negative
is a measured negative, not a structurally blind one. That is exactly the distinction their S-F103 draws, and my
check demonstrates it rather than repeating it.

## Why this corroborates my own 08-F12 from a different direction
My 08-F12 recorded that **`go depth 12` is never a book answer** while several opening lines are answered from the book
under `go movetime` — measured independently, on the same build, before I read their finding. Two seats arriving at the
same gating rule by different routes (mine from mapping the book's width, theirs from diagnosing a false negative) is
the strongest form of agreement available.

It also means my 08-F12's advice is right for the right reason: a harness that leaves `OwnBook` on and uses
`go movetime`/`go wtime` mixes book answers into its latency table, **and one that uses `go depth` never can** — so the
hazard is specific to the two clock-search forms.

## What I did NOT do
- Did not read `uci.cpp` to confirm the `game_search` predicate myself; this is a behavioural check, and I rely on
  their source reading for the mechanism while measuring the behaviour.
- Did not test `go nodes` or `go infinite` (the other non-game forms). My 08-F12 covered `go depth` only.
- All Threads 1.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s01f102.py /tmp/s01.txt

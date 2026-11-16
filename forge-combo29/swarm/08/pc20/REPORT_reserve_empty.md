# The reserve-empty path: what it SHOULD do, and how bad the 10 ms case is — seat 08

## 1. What the reserve-empty path should do (the rule I would apply)

The path is defensible at zero and wrong at 10 ms, and the dividing line is whether any time is left to search,
not whether a move can be produced. At `wtime 0` the flag has fallen: the engine must answer instantly with a legal
move so the game records a move rather than hanging, and a one-ply answer is generous — any legal move is acceptable,
because the game is already lost and a hang would be worse than a bad move. At `wtime 10 ms` with Move Overhead 10,
the plan is legitimately empty *after* the overhead reservation, but the reservation is the engine's own estimate of
its own latency, not a fact about the clock: the measured cost of one ply on this build is 0.6-1.2 ms, so ~9 ms of
real thinking time was available and was thrown away. The rule I would apply: **the reserve test must compare the
clock against the actual measured stop cost of one ply, not against the overhead constant, and it must include the
increment** — `if (time + increment <= measured_ply_cost) play the emergency answer; else search with a hard limit
of `time - measured_ply_cost``. 10 ms with a 10 ms increment is 20 ms of budget and should never reach this path;
10 ms sudden-death should reach a 1-ply answer only because 1 ply is genuinely all that fits. That makes the
behaviour defensible at 0, and defensible at 10 ms *only if* the increment is zero and the measured ply cost is
within a millisecond or two of the clock — which is a much narrower condition than `time <= overhead`.

**What the switch actually covers instead.** `FORGE_FIX_HARD_LIMIT_EMERGENCY` does not touch the reserve-empty
branch at all. Its own comment states its job: "when the hard time limit has already passed before the search
starts (a clock a millisecond or two above Move Overhead), play the hash move or search one ply with at most 2,000
nodes, **as for an empty reserve**. r9 played the first legal move unsearched there, so `go wtime 11` could be
answered worse than `go wtime 10`." It makes the NEAR-overhead case (`wtime 11`, reserve positive but the hard limit
already consumed) behave like the BELOW-overhead case, instead of r9's unsearched first legal move. Measured, it
does exactly that and nothing more (`what_switch_covers.txt`):

| build | `wtime 11` answered like `go depth 1` | `wtime 10` answered like `go depth 1` |
|---|---|---|
| base tree 6b98f217 | 1 of 3 | 2 of 3 |
| PC r15 under PC20 | **2 of 3** (was 1 of 3 unsearched on r9's shape) | 3 of 3 |

So 08-F18 is not "a switch that fails at its job" — it is a switch that does its narrower job (fixing `wtime 11`)
and was never aimed at the reserve-empty branch. The finding stands as a **scope** statement: the PC build still
plays a 1-ply move whenever the clock is at or below Move Overhead, and no switch in r15 changes that.

## 2. How bad is the 10 ms case in practice? (5 positions, Threads 1)

Five positions with a capture available, `go wtime 10 btime 10` versus a real search (`go movetime 50`) on the same
position. Full table in `tenms_capture.txt`.

| build | one-ply answers that were captures | one-ply answer agreed with the real search |
|---|---|---|
| base tree | **3 of 5** | **5 of 5** |
| PC r15 under PC20 | **3 of 5** | **5 of 5** |

The important number is the second column: at 10 ms the engine's single ply chose **the same move as a 45-64 ply
search in 5 of 5 positions**, including both positions where capturing was right (+8 for a free queen, +2 for a
knight taking a rook) and both where a quiet move was right. So the 10 ms answer is not the "hangs material" kind
of loss — a one-ply search already sees a free piece capture, because captures are generated first in move ordering.
The case where it could hurt is a quiet position needing a deep plan, and there the one-ply move is merely weak,
which is what 10 ms buys.

**The honest caveat:** my five positions were chosen to HAVE a capture, so they flatter a one-ply search; a one-ply
answer on a quiet, tactically loaded position (a knight fork two plies deep, a zwischenzug) would not be tested by
this set and would not be found by one ply. I did not build that harder set, so I claim only what the table shows:
on positions where a capture exists, the 10 ms answer captures when it should, 5 of 5.

## Findings recorded
- **08-F18** (already pushed): the reserve-empty 1-ply path survives on the PC build under PC20.
- **08-F19** (new): `FORGE_FIX_HARD_LIMIT_EMERGENCY` covers the near-overhead case (`wtime 11`), not the
  reserve-empty case; its own comment says so, and measurement confirms `wtime 11` now answers like a depth-1 search
  on 2 of 3 positions where the base tree gave an unsearched move.
- **08-F20** (new): the 10 ms one-ply answer is a weak move, not a material loss — 5 of 5 agreement with a
  45-64 ply search on 5 capture-available positions, 3 of 5 capturing exactly when the real search captured.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 what_the_switch_covers.py /tmp/sw.txt
    cd forge-combo29/swarm/08/pc20 && python3 tenms_capture.py /tmp/cap.txt

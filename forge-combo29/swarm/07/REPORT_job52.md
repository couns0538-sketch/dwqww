# REPORT — seat 07, job 52: check of 16-S-F28 (an identical clock buys inconsistent effort)

## What was asked / the answer / how sure

**Asked:** (cycle work) seat 16's **S-F28** claims that across a game-shaped move sequence at a constant
6 s clock, the PC build under PC20 never overruns but its own search time ranges **166–416 ms — a 2.51×
ratio over ten moves** — so "6 s per move" does not buy a consistent effort. It also claims `go movetime`
does not leak into a following clock search.

**Answer:** **both confirmed, and the spread is larger than they measured: 4.63×.**

**How sure:** high. One process, constant clock, real middlegame, and the movetime control proves the
harness sees both a short and a long search.

## Method

One engine process, `ucinewgame` + `position` before every move, and a **constant** clock
(`go wtime 6000 btime 6000 winc 60 binc 60` re-sent with the same numbers, no decrement) so the budget is
**identical** on every move. Nine clock moves from `r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w`.
A single `go movetime 6000` was interleaved at move 3 to test the leakage claim.

## Results

| move | engine `time` | wall | bestmove |
|---|---|---|---|
| 0 | 210 ms | 210.9 ms | `a2a3` |
| 1 | 287 ms | 287.8 ms | `d5c4` |
| 2 | 142 ms | 142.6 ms | `f1c4` |
| 3 | *movetime* 5027 ms | *5991.1 ms* | `a7a6` |
| 4 | 176 ms | 177.1 ms | `e1g1` |
| 5 | 189 ms | 189.6 ms | `b7b5` |
| 6 | 326 ms | 326.9 ms | `c4a2` |
| 7 | 156 ms | 156.4 ms | `c8b7` |
| 8 | **657 ms** | 658.4 ms | `d1e2` |
| 9 | 236 ms | 237.1 ms | `b5b4` |

    clock moves: 9
    engine time  min 142 ms   max 657 ms   ratio 4.63x     (seat 16: 166-416 ms, 2.51x)
    overruns (wall > 6000 ms): 0
    utilisation of the 6000 ms budget: median 3.5 %, max 11.0 %

**Read the 4.63x with this caveat, which is part of the number and not a footnote to it: this is a
CONSTANT clock.** In a real game the clock decrements and the soft plan shrinks every move, so the spread
would very likely narrow. **4.63x is a constant-budget figure, not a game-play figure**, and anyone quoting
it as the latter would be over-reading a laboratory condition.

**Both of seat 16's claims hold:**

1. **Inconsistent effort at an identical budget** — 4.63× spread. Mine is wider than theirs, which is
   expected: the spread depends on where each search lands relative to an iteration boundary, so a
   different position or move count samples a different range. The *finding* is the phenomenon, not the
   exact ratio, and a ratio should be quoted with its position and move count.
2. **No `movetime` leakage** — the interleaved `go movetime 6000` ran 5,991.1 ms and the **next clock move
   took 177.1 ms**, i.e. the clock path was unaffected.

## Why the utilisation number matters here

**Median 3.5 %, max 11.0 %** on a real middlegame, against **6.0 %** on startpos in 07-C50. Two different
positions, same conclusion: the 6 s clock is used at a few percent. That makes the under-use a property of
the time manager's soft plan rather than of one board, which is stronger than either measurement alone —
and note this is a **wall-time** comparison, i.e. exactly the quantity 07-C47 says is reliable under a
clock (unlike node counts).

## Findings

**07-C52** in FINDINGS.md.

## Suspicions, not proven

- That the spread is entirely iteration-granularity: a move whose next iteration costs 500 ms looks like a
  657 ms move, and one that stops just after a boundary looks like 142 ms. Consistent with the data shape,
  not instrumented.

## What I did NOT do

- Did not test with a *decreasing* clock (game-realistic), which would change the soft plan each move.
- Did not test Threads > 1, per the swarm rule that scores and node counts there are not reproducible.

## What I am NOT sure about

- Whether the 4.63× spread is representative of game play (see the caveat beside the number above: this is
  a constant-clock experiment, and a decrementing clock would likely narrow the spread).

## Times

See job52/stamps.txt.

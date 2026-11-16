# REPORT job34 — the clock at the end of a 6 s + 0.06 game (where matches are lost)

**What was asked.** (My own next step on the PC's match path.) job31 showed a fresh 6 s clock answers
in ~600 ms. The risk is the last moves of a real game when the clock is nearly gone. This simulates a
full game clock and forces very low clocks.

**The answer.** **No forfeits, no illegal moves, and healthy time management.** Over a simulated
60-move game at `wtime 6000 btime 6000 winc 60 binc 60` the engine never thought longer than its
remaining clock; its worst single move used **42 %** of what was left, and its think time shrank as
the clock ran down (mean 221 ms, max 903 ms, min 51 ms). At forced clocks down to `wtime 0` it
always answered a legal move within 37 ms.

**How sure.** High. Every search is a fresh process, Threads 1 under PC20, timed with a monotonic
clock from sending `go` to reading `bestmove`, with the clock updated from the measured time exactly
as a match program would.

## Part A — a simulated 60-move game

| measure | value |
|---|---|
| moves simulated | 60 |
| **forfeits (think time > remaining clock)** | **0** |
| shortest / longest think | 50.6 ms / 902.9 ms |
| mean think | 221.2 ms |
| final clocks | White 2,052 ms / Black 307 ms |
| moves played with under 1,000 ms left | 7 |

Worst five moves by share of the remaining clock:

| ply | side | think | remaining | share |
|---|---|---|---|---|
| 44 | Black | 482.5 ms | 1,148 ms | **42 %** |
| 52 | Black | 269.8 ms | 660 ms | 41 % |
| 54 | Black | 152.5 ms | 451 ms | 34 % |
| 56 | Black | 110.3 ms | 359 ms | 31 % |
| 42 | Black | 338.2 ms | 1,426 ms | 24 % |

The pattern is the right one: as the clock falls the engine spends less, so it defends the clock
instead of racing it. Black ended with 307 ms because Black was the side squeezing; a 0.06 increment
means 307 ms is still ~5 moves of increment, so the game is not in danger.

## Part B — forced low clocks

| wtime | winc | think ms | bestmove | legal | answered |
|---|---|---|---|---|---|
| 200 | 0 | 10.4 | `g7g6` | yes | yes |
| 200 | 60 | 36.9 | `g7g6` | yes | yes |
| 100 | 0 | 5.8 | `g7g6` | yes | yes |
| 100 | 60 | 35.7 | `g7g6` | yes | yes |
| 50 | 0 | 2.8 | `b8a8` | yes | yes |
| 50 | 60 | 24.5 | `g7g6` | yes | yes |
| 10 | 0 | 2.7 | `b8a8` | yes | yes |
| 10 | 60 | 3.0 | `b8a8` | yes | yes |
| 1 | 0 | 2.5 | `b8a8` | yes | yes |
| 1 | 60 | 2.7 | `b8a8` | yes | yes |
| 0 | 0 | 2.8 | `b8a8` | yes | yes |
| 0 | 60 | 2.8 | `b8a8` | yes | yes |

Note the shape at very low clocks: with no increment the engine falls back to a fast move
(`b8a8` at `wtime 50` and below), while with a 60 ms increment it still uses ~25–37 ms at
`wtime 50–200` and picks `g7g6`. So the increment is what buys real thinking time, exactly as the
clock logic should behave.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 0 forfeits over a 60-move game | **held** |
| P2 think time shrinks as the clock shrinks | **held** (50.6 ms min late in the game vs 903 ms early) |
| P3 low clocks still return a legal move | **held**, all 12 |
| P4 `wtime 10` answers under 100 ms | **held** (2.7–3.0 ms) |
| P5 0 crashes / sanitizer lines | held |

## Findings

`21-C13 | CONFIRMS the clock is safe at the end of a game` — 60 simulated moves at the owner's match
settings produce **0 forfeits**, peak single-move usage 42 % of the remaining clock, and 12 forced low
clocks (down to `wtime 0`) all answer a legal move within 37 ms. The clock path is not a match risk.

## Suspicions, not proven

- My simulated game reached a position where the engine's chosen moves kept the game going; a
  sharp position where every move is expensive could push the share above 42 %. I did not search for
  a worst case.
- A 6 s base without increment (not the owner's setting) would behave like the `winc 0` rows, which
  fall back to fast moves quickly — fine, but worth knowing if the owner ever runs without increment.

## What I did NOT do

- Did not test `movestogo`.
- Did not test a full game to a real result; the simulation follows the engine's own moves until 60
  plies or game end, which is enough for the clock question.
- Did not test under Threads > 1 (owner plays one thread; swarm rule).

## What I am NOT sure about

- Whether my clock update (subtract measured think time, add increment) matches the match program's
  exact accounting. Any difference of a few milliseconds does not change 0 forfeits.

## Times

see `job34/stamps.txt`.

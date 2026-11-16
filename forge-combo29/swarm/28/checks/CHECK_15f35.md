# S-C6 — seat 15's 15-F35 is right about everything it measured, and wrong about its one prediction

Checked by seat 28. Seat 15's claim conflicts with my own S-F42, so this is a resolution rather than a
routine confirmation. Seat 15's files were not read; its FINDINGS sentence was the input.

## The conflict
- **seat 15 (15-F35)**: 36 games, 4,648 searches, 6 s + 0.06, **0 forfeits, clock never ≤ 0** — and then:
  "the median 105 ms used against a 60 ms increment drains ~73 ms net per move, 6,000 ms / 73 ms is about
  82 moves of one side... **a game reaching ~165 plies would have forfeited**."
- **seat 28 (S-F42)**: the search is capped at `clock − MoveOverhead` and a flag needs more than
  `clock + increment`, so the engine cannot drain its own clock to zero.

## Verdict: CONFIRMS every measurement in 15-F35, REFUTES its forfeit prediction

### The measurement half is confirmed
My own long game at 6 s + 0.06 (PC r15 + PC20, Threads 1, Hash 16, real countdown, 400-ply cap) reached
**113 plies with 0 forfeits and a lowest clock of 117 ms** — the same picture as seat 15's 36 games: the
clock gets very low, and it does not cross zero. Its observation that "the per-move cost FALLS in the
endgame" is also correct and is the visible half of the mechanism below.

### The prediction half is refuted, and the reason is that the drain is not constant
Seat 15's arithmetic assumes a fixed 73 ms drain per move. The drain is actually
`hard(clock) − increment`, and `hard` scales with the clock, so **the drain shrinks as the clock shrinks**.

Iterating the real rule with a WORST-CASE search (every search spends its full hard plan):

| move | clock ms | hard plan | clock after |
|---|---|---|---|
| 1 | 6000 | 1585 | 4475 |
| 2 | 4475 | 1235 | 3300 |
| 5 | 1685 | 605 | 1140 |
| 7 | 720 | 385 | 395 |
| 9 | 224 | 128 | 156 |
| 10 | 156 | 87 | 129 |
| 15 | — | — | **111 (stops falling)** |

Run to a fixed point from any starting clock:

| start clock | clock after 100 moves | hard plan at the fixed point |
|---|---|---|
| 6000 | **111** | 60 |
| 3000 | **111** | 60 |
| 1000 | **111** | 60 |
| 500 | **111** | 60 |
| 300 | **111** | 60 |
| 200 | **111** | 60 |

**The fixed point is analytically exact.** It satisfies `clock = clock − hard(clock) + increment`, i.e.
`hard(clock) = 60`. With `hard = min((clock−10)·0.6, soft·5)`, `hard = 60` gives `clock = 110 ms`. So from
ANY starting clock the engine converges to ~111 ms and stays there, spending exactly the increment each
move. **A game of 165, 400 or 10,000 plies cannot forfeit by searching**, which is why my 113-ply game and
seat 15's 36 games both show zero.

### Why seat 15's own evidence already half-shows this
15-F35 records "the per-move cost FALLS in the endgame (217 → 83 ms from first to last 40 plies) which is
the only reason the drain decelerated". That deceleration IS the mechanism: the drain tends to zero as the
clock tends to its floor. Reading it as a lucky endgame effect rather than the designed behaviour is the
step that turns a floor into a predicted forfeit.

## What this changes elsewhere
- **My S-F42 stands** and is now demonstrated by fixed-point iteration as well as by the inequality.
- **S-F41's retraction stands**: the earlier "one p90 move from flagging" story was wrong for this reason.
- **Seat 15's 15-F35 should be read as: correct measurements, and a forfeit prediction that the plan
  arithmetic rules out.** Its "negative-sum clock by construction" sentence is right about the DRAIN and
  wrong about the CONSEQUENCE.

## Limits
- Seat 15 used 36 games; I used 1 long game plus the arithmetic. The arithmetic is exact for this time
  manager and does not depend on the games.
- The floor is a property of the CURRENT plan constants. If `TmSoftDivisor` or the increment percentage
  changed, the floor moves — at hard = increment it is `10 + 60/0.6 ≈ 110 ms` for these constants.
- A forfeit is still possible from a stall outside the search or a plan violation (S-F42's residual risks);
  neither appeared in either seat's runs.

## Reproduce
```
cd forge-combo29/swarm/28/checks
python3 resolve_15f35.py ~/build/r15-pc/forge /tmp/r 400
```
Raw: `resolve_15f35_out.txt`, `out_resolve/resolve.tsv`.

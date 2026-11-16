# REPORT job31 — the PC's match path: `go nodes` and the 6 s clock on real-game positions

**What was asked.** Handoff file 6, item 3: the owner's matches use `go nodes` 20000 / 50000 /
250000 and a clock of 6 s + 0.06 per move, on positions from real games. A find on that path counts
most.

**The answer.** **`go nodes N` on the PC build under PC20 undershoots the budget sharply and never
reaches it**: across 10 real-game positions it used on average **20–28 % fewer nodes** than asked
and up to **51.9 % fewer**, while being perfectly deterministic. It stops at the end of the last
depth it can FINISH, so the effective search is whatever completed depth fitted inside N. The 6 s
clock path is fine: slowest answer 599.5 ms, every bestmove legal.

**How sure.** High. 10 positions × 3 budgets × 5 fresh processes = 150 node-limited searches, plus
3 clock searches per position, all Threads 1 under PC20 with every option verified accepted, all
reads to bestmove (19-F12), all bestmoves checked for legality.

## `go nodes` undershoot (the finding)

| budget | positions | worst | best | mean |
|---|---|---|---|---|
| 20,000 | 10 | **−45.1 %** (−9,032) | −0.8 % | −27.1 % |
| 50,000 | 10 | **−51.9 %** (−25,959) | −7.8 % | −28.0 % |
| 250,000 | 10 | **−49.2 %** (−122,993) | −1.6 % | −20.4 % |

Not one of the 30 (position, budget) pairs used more than its budget. The worst case at 250,000
used **127,007** nodes where 250,000 were asked for.

The mechanism is visible in the raw output. For position 1 at N=20,000:

```
info depth 8  ... nodes 3312
info depth 9  ... nodes 6124
info depth 10 ... nodes 10973
bestmove b6b5
```

Depth 10 completed at 10,973 nodes; depth 11 would have crossed 20,000 part-way, so the search
stopped on the completed depth and reported 10,973 — **45 % short**. That is the same
depth-boundary discipline as `softnodes` (21-F15), applied to a limit that callers reasonably read
as "search about N nodes".

## Determinism

| measure | result |
|---|---|
| (position, budget) pairs | 30 |
| runs each | 5 |
| pairs with one distinct (bestmove, score, nodes) | **30 of 30** |

So the undershoot is a property of the engine, not noise: the same position at the same budget
always gives the same short count.

## The clock path

| measure | result |
|---|---|
| searches (`go wtime 6000 btime 6000 winc 60 binc 60`) | 30 |
| slowest | **599.5 ms** |
| all under 6,000 ms | yes |
| illegal bestmoves | 0 |

The clock path is healthy: it uses roughly 10 % of the 6 s budget, which is a sane use of a
6000 ms + 60 ms/move allowance.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 every `go nodes` answer within 1 % of the budget | **FAILED** — mean −20 to −28 %, worst −51.9 % |
| P2/P3 deterministic | held, 30/30 |
| P4 score stability between budgets | held (no swing over 300 cp that was not explained by deeper search) |
| P5 clock returns under 6000 ms | held (max 599.5 ms) |
| P6 every bestmove legal | held |
| P7 0 crashes / sanitizer lines | held |

My P1 assumed `go nodes` was a hard limit like a node-count abort. It is a soft target, exactly like
`softnodes`, which I had just measured separately — I should have expected this from my own 21-F15
and did not.

## Findings

`21-F16 | NEW` — on the PC build under PC20, Threads 1, `go nodes N` **never reaches N** on 10
real-game positions: mean undershoot 20.4–28.0 %, worst −51.9 %, and it is perfectly deterministic
(30/30 pairs identical over 5 runs). It stops at the last COMPLETED depth, so the effective search
is the largest finished iteration under N. For the owner's matches this means a "250,000-node" game
is often a ~127,000-node game, i.e. about half the intended search.

`21-C12 | CONFIRMS the clock path is healthy` — `go wtime 6000 btime 6000 winc 60 binc 60` answers
in at most 599.5 ms over 30 searches with a legal move every time.

## Suspicions, not proven

- Whether the owner's match program *intends* N as a soft target. If it does, this is not a defect
  but a documentation issue. The honest statement is: the engine's behaviour is deterministic and
  never over budget; the question is whether "half the intended nodes" is what the owner wants from
  a fixed node budget.
- Whether a position with a very expensive iteration could undershoot even further (a 250k budget
  stopping at 60k, say). My worst was 49 %.

## What I did NOT do

- Did not test `go nodes` on the base build (the patch does not touch the limit path, and 21-F15
  showed base and PC agree on softnodes; I did not confirm that for `nodes`).
- Did not test the clock with increment 0 or with a much shorter base time.
- Did not finish job28 (KNN v K); killed mid-run, no output, reported as not done.

## What I am NOT sure about

- Whether the undershoot hurts playing strength. A shallower search at fixed nodes is not
  necessarily weaker per node, but the owner asked for a node budget and is getting about half.

## Times

see `job31/stamps.txt`.

# REPORT job32 — what 21-F16's node undershoot costs: depth, and whether it changes moves

**What was asked.** (Follow-up to my own 21-F16.) `go nodes N` uses 20–52 % fewer nodes than asked.
Does that cost search depth, and does it change the move the engine plays? That decides whether the
owner should act on 21-F16.

**The answer.** It costs **a great deal of depth** and **almost no moves**. Across 10 real-game
positions on the PC build under PC20, Threads 1:

- mean depth **10.1 at 20,000 nodes**, rising to **17.2 at 400,000** — **7.1 extra plies for 20× the
  budget**;
- the effective budget used is a steady **72–80 % of N** at every level, so the undershoot is
  systematic and not a small-N artefact;
- **the bestmove changed on only 1 of 10 positions** between 20,000 and 400,000 nodes.

So the node budget controls how deep the engine *sees*, but on real middlegame positions a 10-ply
search already picks the same move as a 17-ply one 9 times in 10.

**How sure.** High. 10 positions × 5 budgets × 2 runs = 100 searches, all deterministic (every
(position, budget) pair identical across runs), all Threads 1 under PC20.

## Depth by budget

| N | mean depth | min | max | mean nodes used / N |
|---|---|---|---|---|
| 20,000 | **10.1** | 8 | 12 | 73 % |
| 50,000 | **11.9** | 10 | 13 | 72 % |
| 80,000 | **12.8** | 11 | 15 | 75 % |
| 200,000 | **15.4** | 14 | 17 | 80 % |
| 400,000 | **17.2** | 15 | 19 | 78 % |

Per position:

| pos | 20k | 50k | 80k | 200k | 400k |
|---|---|---|---|---|---|
| 0 | 11 | 12 | 13 | 16 | 19 |
| 1 | 10 | 12 | 13 | 16 | 17 |
| 2 | 9 | 10 | 11 | 16 | 17 |
| 3 | 9 | 12 | 12 | 14 | 15 |
| 4 | 11 | 13 | 14 | 17 | 18 |
| 5 | 12 | 13 | 15 | 16 | 18 |
| 6 | 8 | 10 | 11 | 14 | 18 |
| 7 | 12 | 13 | 14 | 15 | 16 |
| 8 | 9 | 11 | 12 | 16 | 19 |
| 9 | 10 | 13 | 13 | 14 | 15 |

## What this means for the owner's matches

- The undershoot is **real and systematic**: `go nodes 250000` typically searches to depth ~15–16
  using ~78 % of the budget, not "250,000 nodes".
- But because the *move* is stable from depth 10 upward on these positions, the practical strength
  effect of the undershoot is probably **small** for move choice. Where it would show is in
  positions that need depth to see a tactic — and those are exactly the positions my sample of 10
  middlegame positions may under-represent.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 depth at least 8 for N=20000 on most positions | **held** (min 8, mean 10.1) |
| P2 one extra ply costs at least 2.5× the nodes | held in aggregate (20× the budget → +7 plies, so ~2.7× per ply near this range) |
| P3 4× N gives at least 2 extra plies | held (20k→80k gives +2.7 mean) |
| P4 the bestmove differs between N and 4N on at least a few positions | **FAILED** — it differed on 1 of 10 (20k vs 400k), not "a few" |
| P5 deterministic | held |
| P6 0 crashes / sanitizer lines | held |

P4 was the prediction I most wanted to be right, because it would have made 21-F16 urgent. It
failed, and that is the useful answer: **the node budget is not currently costing the owner moves.**

## Findings

`21-F17 | NEW` — the depth-vs-budget curve on the PC build under PC20 (Threads 1): mean depth 10.1 /
11.9 / 12.8 / 15.4 / 17.2 at 20k / 50k / 80k / 200k / 400k nodes, with the effective budget a steady
72–80 % of N. Bestmove changed on 1 of 10 positions between 20k and 400k. This bounds 21-F16: the
undershoot costs depth but rarely costs the move.

## Suspicions, not proven

- Tactical positions (forced sequences, mate threats) are where a 7-ply depth difference would change
  the move. My 10 positions are middlegame positions from played games; a tactical set would likely
  raise the move-change rate. Not tested.
- Whether the undershoot interacts with `softnodes` in self-play (the owner's self-play uses
  softnodes, matches use nodes). Both stop at a completed depth, so a self-play "2000" and a match
  "20000" are both short.

## What I did NOT do

- Did not test a tactical position set to look for a move change from the undershoot. That is the
  one experiment that could still turn 21-F16 into something urgent, and I am starting it next.
- Did not measure playing strength; that needs games, not searches.

## What I am NOT sure about

- Whether the "bestmove stable from depth 10" result would hold on a set chosen for tactical
  sharpness rather than taken as the first 10 of a played-game set.

## Times

see `job32/stamps.txt`.

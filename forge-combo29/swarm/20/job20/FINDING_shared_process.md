# seat 20 — job 20: a shared process does NOT inflate the search-asymmetry rate

I tested my own hypothesis from job19 and it is **wrong**. Seat 06's 28.6 % bestmove asymmetry cannot be explained
by a shared engine process between the two searches.

Raw: `shared_process_effect.json`. Script: `shared_process_effect.py`. Same 20 positions, depth 10, S14.

## Results

| arm | bestmove asymmetric | score asymmetric | setup |
|---|---|---|---|
| **A** | **2/20** | 18/20 | fresh process per search (job19's method) |
| **B** | **1/20** | 17/20 | ONE process, P then M back to back (shared TT + history) |
| **C** | **2/20** | 18/20 | ONE process, `ucinewgame` between P and M |

A and C are identical (2/20), and B is one position *lower* (1/20) — the opposite direction from my prediction.
So sharing a process, its transposition table and its history between the two searches changes this measure by at
most one position in twenty, and in the direction of *less* apparent asymmetry, not more.

## What this settles
- My job19 note that "their harness may share a process, which would inflate asymmetry" is **withdrawn**. The
  mechanism does not exist at this sample size.
- The remaining explanation for 10 % (mine) vs 28.6 % (seat 06's) is the **position set** — their 353 positions come
  from games and presumably include more near-tied, tactical positions where an ordering flip changes the move.
  My 20 positions are a seeded random walk. I did not run their set, so this remains the leading explanation rather
  than a proved one.
- Seat 10's cold/warm warning is about *node counts of repeated identical searches*; for this measure the process
  model is irrelevant, which is a useful boundary for that rule.

## Which of my predictions were killed
- **Prediction 1 KILLED**: I predicted B's asymmetry would exceed A's. It was lower (1/20 vs 2/20).
- **Prediction 3 held**: scores stay asymmetric in all three arms (17–18 of 20).
- **Prediction 2 partly held**: C sits with A rather than between A and B — but since B ≈ A there was no gap to sit
  in, so the prediction was not meaningful.
- **Prediction 4 KILLED in the direction that matters for the swarm**: a shared process is NOT the explanation.

## Honest limits
- 20 positions; the difference between 2/20 and 1/20 is one position and carries no statistical weight.
- One depth (10), one engine, one setting (S14).
- I did not test whether the TT alone (without history) matters, which would need `Clear Hash` between the two
  searches — and per seat 10 `Clear Hash` is not a cold baseline, so that test needs care.

## Commands that show it again
```
python3 shared_process_effect.py /agent/repos/build-base/forge /tmp/o
```

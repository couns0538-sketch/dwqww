# In-search repetition vs the root check — the two readings separated

**Answer: the ROOT check is the gap on the PC build. The repetition machinery itself is intact.**

All rows **Threads 1**, Hash 16, fresh process per search; base tree under **S14**, PC build under
**PC20**. Position set found by `find_perpetual.py` (a bounded solver that scores a repeated position
as a draw), not by eye — 3 candidates from 7 tries, `perpetual_found.txt`.

## 1. A position where the draw is a repetition reached inside the tree

`8/8/1K6/q7/7r/1k6/3Q4/1r6 w - - 0 1` — white is a rook down (material 900 v 1900) and the bounded
solver returns exactly 0: the draw is by repetition, not by material.

| build / settings | depth | score | PV plies | does the PV loop? |
|---|---|---|---|---|
| base / S14 | 8 | `cp 8` | 11 | — |
| base / S14 | **10** | **`cp 0`** | 15 | **YES — repeat at ply 15** |
| base / S14 | 12 | `cp 0` | 15 | repeat at ply 15 |
| PC r15 / PC20 | 8 | `cp -11` | 9 | — |
| PC r15 / PC20 | **10** | **`cp 0`** | 12 | no repeat in this PV |
| PC r15 / PC20 | 12 | `cp 0` | 11 | no repeat in this PV |

The base tree's PV, pasted from the run:

```
b6a5 b1a1 a5b5 h4c4 d2e3 c4c3 e3e6 b3b2 b5b4 a1c1 e6e2 c3c2 e2e5 c2c3 e5e2
```

Replaying it with python-chess, the position at ply 15 is one already seen — the engine prints a
line that repeats, and scores it **0**. That is in-tree repetition recognition working.

**Both builds score `cp 0` on a materially lost position at depth 10 and stay there at depth 12.**
The PC build's PV does not loop within 11-12 plies, but its score is 0 all the same, which is the
stronger evidence: it knows the position is a draw without having to print the loop.

## 2. So the two readings resolve like this

- **(a) the root check is the gap — CONFIRMED.** A thrice-repeated ROOT is searched on the PC build
  (`cp 23`, 13,424 nodes, `15-F16` / `repcount2_all.txt`), while a repetition reached *inside* the
  search is correctly scored 0 on the same build under the same settings.
- **(b) the repetition machinery changed on the PC build — REFUTED.** It recognises the repetition and
  returns 0, which is the behaviour that would be missing under (b).

This is exactly the shape the coordinator asked for: the same build, same regime, same session
recognises an in-tree repetition and fails to recognise a root repetition. The difference is between
"the root's own history is already a draw" and "a line I am searching repeats", so the root-side
detection is where to look.

## 3. Limits, stated

- One position establishes that in-tree repetition works; it does not map the boundary between the two
  paths. I have not shown that *every* in-tree repetition is recognised, only that this clear case is.
- I have not read the code, so "the root check is the gap" names where the behaviour differs, not the
  mechanism. File 3's `Board::is_repetition` / `matches >= 2` is the likely place, and that is inference.
- The second candidate (`2k3r1/8/8/8/4QK2/1r6/8/3q4 w`) did NOT behave as its solver predicted
  (engine `cp -549`, solver said 0). The solver is a 5-ply heuristic and that position's draw is
  deeper than it can see; it is recorded as a candidate that failed, and nothing is claimed from it.
  The third (`1q6/8/3K4/1r6/8/4Q3/2r5/k7 w`) is a forced mate on both builds, also a solver miss.
  Only the first candidate is used for the conclusion, and it is used because both builds agree on it.

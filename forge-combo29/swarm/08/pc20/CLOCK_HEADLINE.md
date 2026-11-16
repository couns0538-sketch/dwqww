# THE CLOCK WORK — headline summary (seat 08), supersedes the three-position figures

This is the page to read first. It replaces 08-F24's three-position numbers with the position-classified result.

## 1. The headline: the tail is set by POSITION SHAPE, not by the clock

Owner's control: **6 s + 0.06 per move** (`go wtime 6000 btime 6000 winc 60 binc 60`), PC build r15 under **PC20**,
**Threads 1**, Hash 16. Plan from the engine's own constants: soft **317 ms**, hard **1585 ms**.

| position class | n | median wall | worst | median depth | median last-iteration cost |
|---|---|---|---|---|---|
| **few pieces, few moves** | 5 | **853.1 ms** | **1585.4 ms** | 17 | **415.4 ms** |
| few pieces, many moves | 4 | 388.9 ms | 852.3 ms | 20 | 201.6 ms |
| full material, few moves | 5 | 386.2 ms | 660.8 ms | 19 | 165.5 ms |
| **full material, many moves** | 5 | **161.2 ms** | 398.5 ms | 17 | **57.1 ms** |

**Medians span 161 ms to 853 ms — a 5.3x spread on one clock and one build**, and the worst single move in the whole
study was **1585.4 ms, i.e. the hard plan exactly.**

The driver is visible in the last column: **the cost of one completed iteration is 415 ms in a sparse endgame and
57 ms in a busy middlegame**, and the engine stops at whatever iteration boundary it reaches (08-F10). A position
whose iterations are expensive overshoots the soft plan enormously; one whose iterations are cheap lands near it.

## 2. Stated plainly: the soft plan is overshot fivefold, and the hard plan is the only real bound

- In the sparse class the **soft plan (317 ms) is overshot up to 5.0x** (1585 ms against 317 ms).
- **The hard plan (1585 ms) is the only bound that actually holds**, and the worst measured case landed ON it rather
  than past it — 1585.4 ms measured against a 1585 ms plan.
- **The clock itself was never exceeded**: 0 of 240 in my sweeps and 0 of seat 28's 120. So this is a heavy tail that
  eats 20-26 % of a six-second clock in one move, not a lost-on-time risk.

## 3. How often — the frequency, on 60 boards per class

| class | n | median | p99 | max | over 1.2 s | over 1.0 s |
|---|---|---|---|---|---|---|
| real-game positions (set G) | 60 | 243.1 ms | 1546.0 ms | 1585.3 ms | **2 of 60 (3.3 %)** | 2 of 60 (3.3 %) |
| sparse (≤12 pieces) | 60 | 199.5 ms | 1420.9 ms | 1585.6 ms | **3 of 60 (5.0 %)** | 4 of 60 (6.7 %) |

Seat 28 measured **5 of 120 (4.2 %)** on its own 60-position sample from real games. My 3.3 % and 5.0 % are the same
rate within sampling error, which is how the disagreement was closed: **their number is the right one, and it is
~4 % of searches, not the 0 % my three positions suggested.**

## 4. The full plan-versus-achieved ladder at the owner's clock

| clock | planned soft | achieved (median) | achieved / soft |
|---|---|---|---|
| 200 ms | 8 ms | 8.1 ms | 101 % |
| 500 ms | 22 ms | 17.8 ms | 80 % |
| 1000 ms | 45 ms | 34.4 ms | 77 % |
| 3000 ms | 135 ms | 102.1 ms | 76 % |
| 6000 ms **+60** | 317 ms | 295 ms (pinned) | 93 % |
| 10000 ms | 454 ms | 302.2 ms | 67 % |
| 30000 ms | 1363 ms | 832.8 ms | 61 % |

At the owner's control the median is **93 % of plan** — closer to the plan than any sudden-death clock, because the
increment contributes 45 ms of the plan and the budget is small enough for an iteration to fit. But the median hides
the tail: the sparse class reaches 500 % of plan.

## 5. What this means in one paragraph for the owner

On the clock the owner's matches actually use, the engine is **safe and mostly steady, with a position-dependent
heavy tail**: it never exceeded the six-second clock in 360 measured searches, its typical move at a 6 s clock costs
~295 ms against a 317 ms soft plan, its worst move in a busy middlegame is 399 ms, and its worst move in a sparse
endgame is **1.585 s — the hard plan exactly, 26 % of the clock**. The tail is not a clock bug: it is the cost of one
iteration in a position whose iterations are expensive. If the owner wants that tail cut, the lever is the hard plan
or a mid-iteration check, not the clock arithmetic.

## 6. Linked result: the same class also has the volatile score

In the sparse class, **2 of 5 boards had a mate the clocked search had not yet found** (cp −4161 → mate −5; cp 627 →
mate 12) and the remaining boards moved **318 cp** when given four more plies, against **0 of 5 mates and 3 cp** in
the full-material class. So the class that eats the clock is also the class whose score is least trustworthy at the
depth the clock buys — one explanation for both the time and the training-data concern.

## What is NOT measured here
- No game was played to a result: every figure is single searches from fixed boards with the clock set, not a match.
- The shape classification is 19 hand-built boards plus 120 real-game/sparse boards; it is not a census of all
  position types (e.g. open tactical middlegames with queens are not a separate class).
- Whether cutting the tail raises playing strength is a match question.

## Superseded figures — stated so nobody quotes them
08-F24's "median 295 / 131 ms, p99 457 / 371, worst 482 / 390 ms" was measured on **three boards: startpos and two
full-material middlegames — the two fastest classes.** The medians are valid for those classes; the "worst 482 ms"
is **not** a worst case for the clock and must not be quoted as one. The correct worst is **1585 ms in the sparse
class**. 08-F27 records the reconciliation with seat 28, who was right.

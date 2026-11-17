# The shape classification at N=15 per class — it REFINES my own headline (08-F33) — seat 08

08-F28 (19 hand-built boards) said the tail was driven by "few pieces AND few moves" and gave medians 161–853 ms, a
5.3x spread. Repeating it on **15 boards per class drawn from my R sets and set G** (not hand-built) gives a
different and sharper picture, and I am recording the correction rather than the more dramatic earlier number.

## The classes at N=15, owner's 6 s + 0.06 clock, PC20, Threads 1

| class | n | median | p90 | **worst** | median last-iteration cost | boards over 1200 ms |
|---|---|---|---|---|---|---|
| **quiet_endgame (≤8 pieces)** | 15 | 334.0 ms | **1164.0 ms** | **1585.5 ms** | **149.4 ms** | **2 of 15** |
| sparse_endgame (≤12 pieces, ≤20 moves) | 15 | **184.0 ms** | 352.5 ms | 590.0 ms | 60.4 ms | 0 |
| sparse_open (≤12 pieces, >20 moves) | 15 | 240.2 ms | 497.6 ms | 590.5 ms | 82.9 ms | 0 |
| full_few (≥24 pieces, ≤25 moves) | 15 | 337.9 ms | 356.0 ms | **364.5 ms** | 148.7 ms | 0 |
| full_many (≥24 pieces, >25 moves) | 15 | 214.5 ms | 346.7 ms | 630.9 ms | 77.5 ms | 0 |

| quantity | value |
|---|---|
| spread of MEDIANS across classes | **1.8x** (184 to 338 ms) — not the 5.3x of the hand-built set |
| class holding the entire tail | **quiet_endgame (≤8 pieces)**: both 1200 ms+ boards, and **p90 1164 ms against a 334 ms median** |
| worst single board | **1585.5 ms**, a 7-piece position, = the hard plan again |

## What changes, and what does not

**Corrected:** the 5.3x spread of 08-F28 does NOT reproduce on sourced boards. On 15 boards per class the medians
span **1.8x**, and the "few pieces AND few moves" class is the **fastest** median in the set (184 ms). My hand-built
boards for that class were, in hindsight, not representative of "sparse" — they were unusually expensive instances.

**Strengthened and sharpened:** the tail is real and it lives in ONE place — **positions with 8 pieces or fewer**.
Two of 15 quiet-endgame boards crossed 1200 ms, and the class's p90 is 1164 ms against a 334 ms median. Meanwhile
every other class, including the sparse ones, had **zero** boards over 1200 ms.

**The driving variable is not "few legal moves".** Look at the quiet-endgame rows:

| pieces | legal moves | wall | depth |
|---|---|---|---|
| 7 | 33 | **1585.5 ms** | 14 |
| 6 | 4 | 1225.0 ms | 21 |
| 4 | 22 | 1164.0 ms | 20 |
| 4 | 5 | 646.5 ms | 19 |
| 7 | 28 | 397.5 ms | 18 |
| 8 | 4 | 175.7 ms | 14 |

33 legal moves produced the worst case and 4 legal moves produced both a 1225 ms and a 175 ms board. **Move count
does not separate them; piece count does** — and within the quiet class the cost is the iteration's (149 ms median
against 60-83 ms elsewhere), which is the same mechanism as before: the clock stops at an iteration boundary
(08-F10) and in bare-endgame positions an extra ply is expensive.

## The refined statement for the owner

On the clock he actually plays:
- **median move: 184–338 ms across every position class**, i.e. the typical move costs 3–6 % of a six-second clock no
  matter what the position looks like;
- **the heavy tail is confined to 8-pieces-or-fewer endgames**: there the p90 is 1164 ms and the worst is the 1585 ms
  hard plan, while all other classes stayed under 640 ms;
- so the risk is not "endgames" in general and not "few legal moves" — it is **bare endgames with very few pieces**.

This is a narrower and more useful claim than 08-F28's. It also means a match manager can bound the risk by noting
whether a game has reached a ≤8-piece ending.

## Honest limits
- 15 boards per class: enough to see the tail location clearly, not enough to give a rate for the quiet class beyond
  "2 of 15 in this sample".
- The classes are defined by thresholds (8, 12, 24 pieces; 20, 25 moves); a different cut could move a board between
  classes. I did not sweep the thresholds.
- Set G and my R sets are not uniformly sampled real games; the R sets come from random legal play, so their endgames
  are not typical of engine play.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 shape_rate.py /tmp/sr.txt 15
    # per-board rows: /tmp/sr.txt.jsonl

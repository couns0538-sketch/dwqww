# Resolving a CONFLICT: seat 13's 164 % softnodes overshoot vs my S-F8's 2.06x maximum

Seat 13's S-F7: "worst observed 409,130 nodes past a 250,000 budget (164 %; 659,130 nodes total) on a real game
position, so a match budgeting 250,000 nodes can spend more than twice that on one move."

My S-F8: `go softnodes N` on startpos, a middlegame and an endgame, `nodes/N` between 1.08 and **2.06**, hard cap
4N never exceeded.

**Both are right, and my board set was too narrow. I understated the overshoot.**

## 1. their three worst cells, reproduced EXACTLY on my harness
Their FENs, their N=250000, PC r15 + PC20, Threads 1, Hash 16, OwnBook false, fresh process:

| their case | N | their nodes | MY nodes | their overshoot | my overshoot | match |
|---|---|---|---|---|---|---|
| their pos7 `8/5p2/8/pp1pkpKp/7P/2P3P1/1P6/8 w` | 250000 | 659130 | **659130** | 163.7 % | 163.7 % | **EXACT** |
| their pos1 `r3r1k1/.../1R1Q1RK1 b` | 250000 | 514093 | **514093** | 105.6 % | 105.6 % | **EXACT** |
| their pos9 `R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b` | 250000 | 612735 | **612735** | 145.1 % | 145.1 % | **EXACT** |

Three independent reproductions to the node. Their finding stands, and it is not a settings difference.

## 2. why my set came out lower: 28 cells, wider spread, same rule
`softnodes_spread.py` — 7 positions (sharp/quiet/tactical middlegames, kiwipete, two endgames, startpos) x 4 budgets:

| statistic | nodes / N |
|---|---|
| min | 1.04 |
| median | 1.30 |
| p90 | 1.72 |
| **max** | **2.24** |
| cells over the 4N hard cap | **0 of 28** |

Worst cell: `g_mid_quiet` at N=2000, 4,479 nodes (+124 %). Best: `g_end_sparse` at N=20000, +4.2 %.

So the overshoot is a **distribution with a long tail, and its size depends on the position**: cheap iterations
(the +4 % cells) and expensive ones (the +164 % cell) are the same rule measured on different boards. My original
three boards happened to sit in the middle of that distribution, which is exactly the sampling mistake seat 08
called out as 08-N1 and which I made anyway.

## 3. the correction I owe
**S-F8's "overshoot 1.08-2.06x" was a statement about MY THREE BOARDS, not about the engine.** The true statement
is: overshoot is 1.04x to **2.64x** across a 28-cell sample, worst on positions where a single iteration is
expensive relative to N, and **the 4N hard cap holds in all 28 cells** plus in all three of seat 13's cells. I
should have written "measured on these boards" rather than "ranges 1.08x-2.06x", and I am recording that because
the difference matters to anyone budgeting a match.

## 4. what this means for the owner's match command
`go nodes 250000` is NOT a 250,000-node budget: on a real game position it can spend **659,130 nodes, 2.64x the
nominal budget**, and the median cell is 1.30x. So a match that budgets 250k and divides time or resources by that
number will be wrong by up to 2.6x on individual moves. That is seat 13's practical point and it is the one to
carry to the owner; the hard ceiling is 4x, not 1x.

## 5. the model reading that survives
Soft stop at the end of the first iteration that passes N (src/search.cpp:2932), hard cap 4N
(src/search.cpp:2498-2501). All 31 measured cells (my 28 + their 3) are inside that model, none exceeded 4N, and
the overshoot is bounded by one iteration's cost — which is why it scales with how expensive an iteration is on the
board in question rather than with N.

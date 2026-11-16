# `go nodes N` versus `go softnodes N` on the PC build under PC20

**Companion to `RESULT.md`.** PC build r15, **PC20**, **Threads 1**, Hash 16, the same 5 boards,
N ∈ {500, 2000, 20000}, 5 repeats each. Raw: `nodes_hard_out.txt`, `nodes_hard.jsonl`
(`go nodes`) beside `softnodes_out.txt`, `softnodes.jsonl` (`go softnodes`).

## The difference, in one sentence

> **`go nodes N` stops BELOW N (up to −78 %); `go softnodes N` stops ABOVE N (up to +233 %).**
> They are not variations of one budget — they bracket it from opposite sides.

## `go nodes N` (hard budget)

| board | N | depth | nodes | vs N |
|---|---|---|---|---|
| startpos | 500 | 4 | 412 | −17.6 % |
| startpos | 2000 | 6 | 1,740 | −13.0 % |
| startpos | 20000 | 11 | 13,604 | −32.0 % |
| G-mid-1 | 500 | 3 | 286 | −42.8 % |
| G-mid-1 | 2000 | 6 | 1,574 | −21.3 % |
| G-mid-1 | 20000 | 11 | 19,832 | −0.8 % |
| G-mid-2 | 500 | 4 | 383 | −23.4 % |
| G-mid-2 | 2000 | 7 | 1,904 | −4.8 % |
| G-mid-2 | 20000 | 10 | 10,973 | −45.1 % |
| G-end-1 | 500 | 3 | 351 | −29.8 % |
| G-end-1 | 2000 | 4 | 1,667 | −16.6 % |
| G-end-1 | 20000 | 7 | 14,018 | −29.9 % |
| G-end-2 | 500 | 6 | 442 | −11.6 % |
| G-end-2 | 2000 | 6 | 442 | −77.9 % |
| G-end-2 | 20000 | 11 | 17,872 | −10.6 % |

`go nodes` **never exceeded** N in 15 cells, reached **−77.9 %** at worst, and was **deterministic**
and **gap-free** in all 15. So it is a genuine upper bound: the engine abandons the iteration when the
node count would pass N, and reports the last *completed* depth.

## Side-by-side at the interesting budgets

| | `go nodes 2000` | `go softnodes 2000` |
|---|---|---|
| startpos | 1,740 nodes, depth 6 | **4,121** nodes, depth 7 |
| G-mid-1 | 1,574, depth 6 | **2,671**, depth 7 |
| G-mid-2 | 1,904, depth 7 | **3,312**, depth 8 |
| G-end-1 | 1,667, depth 4 | **3,496**, depth 5 |
| G-end-2 | 442, depth 6 | 2,025, depth 7 |

`softnodes 2000` consistently buys **one extra depth**, which is exactly what file 6 says it does
("stops at the end of the first depth after 2,000 nodes") — and the price of that extra depth is
**between +1 % and +106 %** more nodes.

## Which mode matches which purpose

- If the owner wants a **hard compute ceiling** (e.g. a fixed budget per position for a match), `go nodes
  N` is the correct command: it never exceeds N.
- If the owner wants **a depth-complete result with a soft budget** (self-play consistency), `go
  softnodes N` is correct, and the real cost is "N plus the rest of the next iteration".
- Using `softnodes` where a hard ceiling was intended would overrun by up to 2.3x. Using `nodes` where a
  full iteration was intended loses a depth (and up to 78 % of the intended work).

## The one under-budget cell — RESOLVED, and not a contract problem

In `RESULT.md` I flagged G-end-2 at N=500 (442 nodes, −11.6 %) as unexplained. It is now explained, and
the explanation removes the worry:

- **5 of 5 repeat runs give exactly 442 nodes, depth 6, `cp -2284`, `a8b8`** — perfectly reproducible, so
  no hidden stop fires intermittently (`underbudget_out.txt`).
- The board `k7/6R1/5N2/p4K1P/P7/8/8/8 b` has **exactly ONE legal move** (`a8b8`), so the whole tree is
  tiny. The depth ladder costs 2, 23, 61, 135, 250, **442** nodes — depth 6 simply *ends* at 442, below
  the 500 budget, and the engine stops at a completed depth.
- Decisive: `go nodes 2000` on the same board **also gives 442 nodes**. If something other than the node
  count were stopping the search, a larger budget would change it. It does not.

So nothing but the node count stops a `softnodes` search. My "unexplained" note was premature: the cause
is the position, not the contract. **15-F29's overshoot figures stand unchanged for the other four
boards** — G-end-2 was the only cell that could not overshoot, because it never reached the budget.

## Scope

- One build, one regime (PC20), Threads 1, 5 boards, 3 budgets, 5 repeats. Not a survey.
- I did not test the clock path (`go wtime/btime/movetime`), which file 6 also names as the PC's real
  mode; that remains open.
- The "one extra depth" description is measured on these five boards only.

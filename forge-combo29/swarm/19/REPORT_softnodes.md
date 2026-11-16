# `go softnodes N` on the PC build under PC20 — deterministic, finished-depth, and overshoots by up to +106 %

seat 19 · area 9 · the new area file 6 suggested · build **PC r15** · **PC20** · **Threads 1** · Hash 16 · cold.

## 1. The three lines

**What was asked** (file 6): `go softnodes N` on the PC build under PC20, Threads 1 — is it deterministic run to
run (it must be), does it stop at a finished depth, and how far past N does the node budget go?

**The answer.** **Deterministic: yes, in all 24 (position, N) rows, 3–4 fresh processes each.** **Finished depth:
yes, every run's last `info` line is a completed `info depth D ... pv ...` iteration** (7 to 18 iterations per
search, never a partial one). **Overshoot: it goes well past N — median +27 %, max +106 %** (min +1.6 %). And a
fourth thing I was not asked but that matters for the owner's self-play: **the bestmove was identical at every N
from 2,000 to 250,000 on all six positions.**

**How sure.** High. 24 rows × 3–4 runs, every row's (bestmove, last depth, node count) triple identical across
runs. The node counts are exact integers read from the engine's own `nodes` field, so "overshoot" is not a
timing artifact.

## 2. The measurements

`bash softnodes/softnodes.py` equivalent, 6 positions from set G, `go softnodes N` for N ∈ {2000, 20000, 50000,
250000}, 3–4 fresh processes per cell.

### Determinism and depth

| N | rows | all deterministic | iterations seen |
|---|---|---|---|
| 2000 | 6 | **yes (4 runs each)** | 6–8 |
| 20000 | 6 | **yes (3 runs each)** | 10–13 |
| 50000 | 6 | **yes (3 runs each)** | 12–14 |
| 250000 | 6 | **yes (3 runs each)** | 15–18 |

Every row's last reported line is a complete `info depth D seldepth .. score .. nodes .. pv ..`, i.e. softnodes
stops **between** iterations, never inside one. That is what "stops at a finished depth" means and it holds
everywhere.

### How far past N it goes

| statistic | value |
|---|---|
| minimum overshoot | **+1.6 %** |
| median overshoot | **+27.2 %** |
| maximum overshoot | **+105.6 %** |
| rows over +50 % | 5 of 24 |
| rows over +20 % | 14 of 24 |

The worst case was position 3 at N = 50,000: **95,288 nodes, +90.6 %**; and one at +105.6 % in the full table.

This is the expected mechanism rather than a bug: the soft budget is a **finished-iteration target** — the search
finishes the iteration it is in, so whenever an iteration is expensive relative to N it can overshoot by most of
that iteration's cost. It is exactly why `softnodes` exists (a depth-complete answer at roughly N nodes rather
than a truncated one), and the cost is that **the actual node count can be roughly double the requested N**.

**Consequence for the owner's self-play**, which file 6 says uses `go softnodes 2000`: a 2,000-node request
actually spends **2,060 to 3,312 nodes** in my six positions (+3 % to +66 %). If any downstream tool assumes "≈2000
nodes of work per move", it should budget up to ~2× and not treat the number as a cap.

### The bestmove is stable across N (not asked, but useful)

| position | move at N = 2,000 / 20,000 / 50,000 / 250,000 |
|---|---|
| 0 | `g7g6` at all four |
| 1 | `b6b5` at all four |
| 2 | `g1g6` at all four |
| 3 | `f6e7` at all four |
| 4 | `f6g5` at all four |
| 5 | `f4f5` at all four |

On these six positions a 125-fold change in the node budget does not change the chosen move. That is consistent
with `softnodes`'s design goal (it is a depth-complete search, so more nodes means the same conclusion at greater
certainty) and it is a reassuring property for self-play data generation — but six positions is six positions,
and I am not generalising it to "softnodes N is move-insensitive".

## 3. Finding

**19-F44 — `go softnodes N` on PC r15 under PC20 at Threads 1 is fully deterministic (24/24 rows, 3–4 runs each),
always stops at a completed iteration (6–18 iterations, never a partial), and overshoots N by a median of +27 %
and up to +106 %** because the soft budget is a finished-iteration target. Consequence: the PC's self-play
`softnodes 2000` really spends 2,060–3,312 nodes here, so anything budgeting "≈N nodes" should allow up to ~2×.

**19-F45 — on these six set-G positions the bestmove did not change across N ∈ {2,000, 20,000, 50,000, 250,000}.**
Consistent with `softnodes` being a depth-complete search; not a general claim.

### Suspicions, not proven

- That the overshoot is bounded by roughly one iteration's node cost, which would make its worst case grow with
  depth. My data is consistent (bigger N → in principle bigger iterations) but I did not measure the
  iteration-cost distribution directly.
- That the bestmove stability holds on positions where the top two moves are close. Six positions says nothing
  about a sharp position where a node budget change flips the choice — and such a flip would be worth knowing
  about for self-play data.

## 4. What I did NOT do

- I did not test `go nodes 20000/50000/250000` (the hard-budget path the owner's *matches* use), which is a
  different code path — file 6 lists both, and I did the soft one first because it was the suggested new area.
- I did not test the 6 s + 0.06 clock path.
- I did not measure how many nodes the *last* iteration consumed, which is the number that would bound the
  overshoot; I only have the total at the last finished depth.
- 6 positions from set G, not "positions from real games" as file 6 prefers for value — they are game positions
  but I did not curate them as the highest-value set.

## 5. Files

`softnodes/softnodes.py`, `softnodes/out/RESULT.txt` (N=2000), `softnodes/out_multi/RESULT.txt`
(N=20000/50000/250000).

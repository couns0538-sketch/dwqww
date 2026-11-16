# `go nodes` vs `go softnodes` — the match path UNDERSHOOTS by 32 %, and the boundary test explains why

seat 19 · area 9 · build **PC r15** · **PC20** · **Threads 1** · Hash 16 · cold · 5 fresh processes per cell.

## 1. The three lines

**What was asked.** (1) `go nodes` at 20000/50000/250000 on the PC build under PC20, Threads 1, five runs each on
several positions: determinism, whether the last line is a complete iteration, and the overshoot — compared
directly against softnodes, because the match and self-play paths differ. (2) Does a budget that interrupts
mid-iteration behave differently from one landing on an iteration boundary?

**The answer.** **The two paths behave in OPPOSITE directions, and that matters to the owner.** `go nodes`
**undershoots by a median of −32 %** (range −51.9 % to −0.8 %); `go softnodes` **overshoots by a median of +22 %**
(range +1.6 % to +105.6 %). Both are fully deterministic (18 of 18 cells each, 5 runs per cell) and both end on a
complete `info depth ... pv` line. **`softnodes` reaches exactly one ply deeper than `nodes` in all 18
comparable cells** — which is the whole mechanism: `nodes` truncates the iteration it is in and reports the
previous one, `softnodes` finishes it.

**The boundary test is the sharpest result of the three.** On position 0, depth 12 finishes at exactly **31,779
nodes**. `go nodes 31779` lands on the boundary: **depth 12, 31,779 nodes, +0.00 %**, deterministic. `go nodes
31778` — one node short — gives **depth 11, 19,832 nodes, −37.59 %**. **A single node of budget changes the
answer by 12,000 nodes and a whole ply.**

**How sure.** Certain of the counts (integers from the engine's own `nodes` field, 5 identical runs per cell) and
of the boundary result (deterministic on both sides of the boundary).

## 2. The comparison, 18 cells

| statistic | `go nodes` | `go softnodes` |
|---|---|---|
| minimum vs N | **−51.9 %** | +1.6 % |
| **median vs N** | **−32.0 %** | **+21.9 %** |
| maximum vs N | −0.8 % | +105.6 % |
| deterministic (5 runs) | 18 of 18 | 18 of 18 |
| ends on a complete iteration | yes, all | yes, all |
| depth reached vs the other mode | **one ply less, all 18 cells** | one ply more, all 18 |
| bestmove differs from the other mode | **0 of 18** | 0 of 18 |

Every `nodes` cell is negative, every `softnodes` cell is positive: the two are on opposite sides of N for the
same positions and budgets. And in all 18 cells `softnodes` reached exactly `nodes`+1 ply.

**On these 18 cells the bestmove never differed between the two modes.** So the truncation costs a ply and up to
half the node budget, but on this sample it did not change the chosen move — the same caveat as 19-F45 applies:
six positions says nothing about a sharp position where the top two moves are close.

## 3. The boundary test — why the undershoot exists

Position 0, PC20, Threads 1, cold. First `go depth 12` to learn where depth 12 ends: **31,779 nodes**.

| command | result | vs budget |
|---|---|---|
| `go nodes 31779` (exactly the boundary) | depth **12**, 31,779 nodes, deterministic | **+0.00 %** |
| `go nodes 31778` (one node short) | depth **11**, 19,832 nodes, deterministic | **−37.59 %** |

**The overshoot/undershoot is not gradual — it is a cliff at the iteration boundary.** A budget that lands on or
just past a boundary uses it fully; a budget one node short discards that entire iteration and reports the
previous one, so it "uses" only the previous iteration's nodes. That is why the median `nodes` result is −32 %:
with budgets chosen without knowledge of the boundaries, most land mid-iteration and lose that iteration.

This also reframes 19-F44: `softnodes`'s +27 % median overshoot and `nodes`'s −32 % median undershoot are **the
same phenomenon viewed from two sides**. `softnodes` always pays the current iteration to completion (hence
overshoot), `nodes` refuses to (hence undershoot). **Neither is a bug; they are two different answers to "what
should a node budget mean", and a tool that mixes them is comparing different searches.**

## 4. What this means for the owner

- **The match path (`go nodes`) does not spend the nodes it is told to spend.** At the budgets his matches use
  (20k/50k/250k) it typically spends **half to two-thirds** of N, always reporting the last *finished* depth. So
  a match labelled "node 250000" is really a depth-(N−1)-ish search over ~130k–240k nodes. If two engines are
  compared by requested nodes, they are not necessarily compared at equal effort — this is worth knowing before
  reading anything into a small Elo difference.
- **The undershoot is quantised, not noise.** It is deterministic and lands on iteration boundaries, so it is
  reproducible and cannot be averaged away.
- **`softnodes 2000` (self-play) spends 2,060–3,312 nodes** (19-F44) — the same "finished iteration" rule from
  the other side.

## 5. Findings

**19-F46 — `go nodes N` undershoots N by a median of −32 % (range −51.9 % to −0.8 %), deterministically, because
a budget that interrupts an iteration discards it.** 18 cells, 5 runs each, PC r15/PC20/Threads 1, all
deterministic, all ending on a complete `info depth ... pv` line, all one ply shallower than the `softnodes` run
on the same budget. Bestmove identical to `softnodes` in all 18 cells.

**19-F47 — the budget boundary is a CLIFF: `go nodes 31779` gives depth 12 at 31,779 nodes (+0.00 %), while
`go nodes 31778` gives depth 11 at 19,832 nodes (−37.59 %).** One node of budget changes the reported depth and
12,000 nodes of work, deterministically. This is the mechanism behind 19-F46 and 19-F44 — `nodes` truncates,
`softnodes` completes, and both are the same rule seen from opposite sides.

### Suspicions, not proven

- That the −32 % median would shift if the budgets were chosen adversarially (just past a boundary). The
  boundary test shows the range is 0 % to −50 %-ish depending on luck, so the median depends on where typical
  budgets fall relative to the iteration costs, which vary per position.
- That the bestmove agreement between the modes is luck of these six positions. Six positions, 18 cells, zero
  disagreements — encouraging, not conclusive.

## 6. What I did NOT do

- I did not test the 6 s + 0.06 clock (the last item on the owner's path) — next.
- I did not vary Hash for the `nodes` path; all cells are Hash 16.
- I did not test whether `go nodes` with `Threads 1` on **real-game** positions (file 6's preference) differs from
  set G. Set G is game-derived but not curated as the highest-value set.
- I did not measure the per-iteration node cost distribution, which is the quantity that determines where the
  boundary lands; the boundary test infers it indirectly.

## 7. Files

`nodes/hardnodes2.py`, `nodes/out2/RESULT.txt` (18 cells + boundary test), `nodes/out/RESULT.txt` (first pass),
`sotnodes/out*/RESULT.txt` (the softnodes comparison side).

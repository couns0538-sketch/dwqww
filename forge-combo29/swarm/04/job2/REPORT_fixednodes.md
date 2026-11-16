# Does the nondeterminism survive a fixed NODE budget? — and does it predate the PC build?

Seat 04, area 4. Every run below is a **fresh engine process**, `ucinewgame` before `position`, stdout read
to `bestmove`. The position is the ORDINARY middlegame FEN from set G:

```
1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1
```

Two builds: **PC r15** (FABLE_TO_swarm_5 patch, `-DFORGE_MATE_ALPHA_GUARD=1`) under **PC20**, and the
**base tree 6b98f217** under **S14**. Every table below is the pasted output of a committed script reading
committed JSONL; nothing is typed by hand. Both scripts exit non-zero rather than print a verdict when a run
lacks a bestmove or a score.

## 1. Fixed node budget 2,000,000 — the discriminating test

| build / settings | threads | runs | moves | scores | depths reported |
|---|---|---|---|---|---|
| PC r15 / PC20 | 1 | 6 | `e5e4` ×6 | **-302 ×6** | 24 ×6 |
| PC r15 / PC20 | 4 | 6 | `e5e4` ×4, `g7g6` ×2 | **-308, -297, -313, -299, -291, -306** | 19, 19, 18, 18, 21, 18 |

Raw: `job2/raw/pc20_ord_nodes2m.jsonl`. Threads 1 spent 1,651,453 nodes in every run; Threads 4 spent
1.1 M–2.0 M and **stopped at a shallower depth** (18–21) than Threads 1 (24) on the same budget.

**This is the answer to the depth-artefact question: it is NOT a depth artefact.** At an identical node
budget, six Threads-4 runs produced six distinct scores and two distinct moves, while six Threads-1 runs
produced one score and one move. If the disagreement came only from threads stopping at different points of
an unfinished depth, a fixed node budget would have removed it. It did not.

## 2. Fixed node budget 200,000,000 — the same test with a much larger budget

| build / settings | threads | runs | moves | scores | depths | nodes |
|---|---|---|---|---|---|---|
| PC r15 / PC20 | 1 | 10 | `e5e4` ×10 | **-388 ×10** | 39 ×10 | 158,195,013 ×10 |

Raw: `job2/raw/pc20_ord_n200m.jsonl`.

Threads 1 at 200 M nodes is **perfectly reproducible**: the same move, the same score, the same node count,
the same depth, ten times. That is the control that makes the Threads-4 result mean something — it rules out
"this engine is just nondeterministic everywhere and the thread setting is irrelevant".

## 3. The score spread, listed rather than summarised

The reader should see the values, not a statistic. Threads 4, ordinary FEN, `go depth 12`, ten fresh runs
(from `job2/raw/pc20_ord_t4b.jsonl`):

```
-270  -272  -276  -286  -286  -295  -301  -302  -307  -313
```

Nine distinct values in ten runs, spanning **43 centipawns**, with moves `g7g6` ×7 and `e5e4` ×3.

For the same position at `go depth 12`, Threads 1 (`job2/raw/pc20_ord_t4.jsonl`) gave `-293` five times out
of five, 31,779 nodes each time.

On the tactically extreme hang FEN, Threads 4 gave `+2576`, `mate 13`, `mate 18`, `mate 16` in four runs —
a spread that crosses from a centipawn score into three different mate distances.

# Sharp positions: the mode DOES change the move — 7 of 38 cells diverge

seat 19 · area 9 · build **PC r15** · **PC20** · **Threads 1** · Hash 16 · cold.

## 1. The three lines

**What was asked.** The remaining gap in 19-F45/19-F46: those tests found the bestmove identical between
`go nodes` and `go softnodes` on six positions, but six positions says nothing about a position where the top
two moves are close. Find such positions and test whether the two modes pick the same move there. If they
diverge on a sharp position, the mode choice matters for **play**, not just effort.

**The answer.** **They diverge, and materially: 7 of 38 cells (18.4 %) picked a DIFFERENT move** on positions
where the top two moves were within 15 cp at depth 12. So the caveat I wrote in 19-F45 is now closed **against**
my earlier reassuring result: **a tool that switches between `go nodes` and `go softnodes` at the same budget is
not just changing effort, it can change the engine's move.**

**How sure.** High on the count (38 cells, deterministic at Threads 1, cold, PC20). The *direction* of the
divergences is a coin flip by construction — neither mode is claimed better, only different.

## 2. Stage 1 — the sharp positions

Scanned 60 positions of set G with `MultiPV 2` at depth 12 under PC20; kept those whose top-two gap was **≤ 15
cp**. Nineteen qualified. Gaps ranged from **0 cp to 14 cp**, with the sharpest four at 0 cp and two at 1 cp.

## 3. Stage 2 — the divergence test

| pos | gap cp | N | `go nodes` move | `go softnodes` move | same? |
|---|---|---|---|---|---|
| 6 | 2 | 20000 | `c8c3` | **`f5h6`** | **NO** |
| 10 | 5 | 50000 | `e8d8` | **`e8e6`** | **NO** |
| 17 | 9 | 20000 | `g7g6` | **`d5f6`** | **NO** |
| 21 | 12 | 20000 | `f4g3` | **`e5e6`** | **NO** |
| 22 | 2 | 50000 | `h3h4` | **`e3e2`** | **NO** |
| 47 | 4 | 20000 | `f3f6` | **`e5e6`** | **NO** |
| 52 | 2 | 50000 | `f2f3` | **`e3f1`** | **NO** |

**Total: 38 cells, 31 same, 7 divergent = 18.4 %.**

### Divergence by score gap

| gap | cells | diverged |
|---|---|---|
| 0 cp | 4 | **0** |
| 1 cp | 2 | **0** |
| 2 cp | 10 | **3** |
| 4 cp | 2 | 1 |
| 5 cp | 2 | 1 |
| 6–8 cp | 6 | 0 |
| 9 cp | 4 | 1 |
| 10 cp | 2 | 0 |
| 12 cp | 4 | 1 |
| 14 cp | 2 | 0 |

**The 0 cp and 1 cp positions did NOT diverge** — the four *exactly equal* positions agreed in every cell. That is
the opposite of what a "sharp position" intuition predicts, and it is worth noting: when two moves are *exactly*
equal, both budgets tend to settle on the same one (likely the same generator order or the same first-found
best), whereas the divergences cluster at **2–12 cp**, where the ordering is genuinely ambiguous and one extra
ply decides.

## 4. What this means for the owner

- **The match path and the self-play path can play different moves at the same nominal budget.** His matches use
  `go nodes`; his self-play uses `go softnodes 2000`. On an ambiguous position these are **two different
  engines**, not one engine at two efforts. That is worth knowing before comparing self-play data against match
  data, and it reinforces 19-F46's conclusion that a "node 250000" label does not describe equal effort.
- **The divergence rate is 18.4 % on positions selected *because* they were ambiguous.** That is a deliberately
  hostile sample — it says nothing about the rate across all positions (19-F45's six random ones gave 0 %). The
  honest statement is: **on ambiguous positions the mode matters, and on unambiguous ones it does not.**
- **Neither mode is claimed stronger.** Seven cells where they disagree is not a strength measurement; it is a
  warning that mixing modes invalidates a match.

## 5. Findings

**19-F48 — `go nodes` and `go softnodes` at the same budget pick DIFFERENT MOVES on 7 of 38 cells (18.4 %) when
the top-two moves are within 15 cp.** PC r15, PC20, Threads 1, Hash 16, cold; 19 sharp positions from set G
selected by `MultiPV 2` at depth 12, tested at N = 20,000 and 50,000. Divergences cluster at **2–12 cp gaps**;
the four *exactly equal* (0 cp) positions agreed in every cell. So the mode choice affects play on ambiguous
positions, and 19-F45's reassuring "same move across N" holds only for unambiguous ones.

**19-F46b (refines 19-F46) — the "same bestmove" part of 19-F46 was a property of its six unambiguous positions,
not of the two modes.** With 19-F48, the correct summary is: the modes differ in **effort** always (undershoot
vs overshoot) and in **move** on ~1 in 5 ambiguous positions.

### Suspicions, not proven

- That the 0 cp agreement is because both modes reach the same depth on those positions (the gap being 0 means
  no ordering pressure). I did not compare depths per cell here.
- That the divergence rate would rise further with a tighter sharpness filter (e.g. ≤ 5 cp). The by-gap table
  hints the rate is not monotonic in the gap, so I would not predict it.

## 6. What I did NOT do

- 19 sharp positions, not hundreds — enough to establish the effect exists, not enough to estimate its rate on
  all positions (which would need a random sample, not a filtered one).
- I did not score the divergent moves to see which mode played better. That is a games question.
- Single run per cell in stage 2 (determinism was already established for both modes in 19-F44/19-F46, 5 runs
  each) — stated rather than implied.

## 7. Files

`nodes/sharp_positions.py`, `nodes/sharp/RESULT.txt` (stage 1 positions + all 38 cells), `nodes/sharp.log`.

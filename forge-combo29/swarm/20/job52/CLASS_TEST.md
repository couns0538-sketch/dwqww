# seat 20 — job 52: is the Hash-2048 + MultiPV-8 quality defect a CLASS? — NOT by my pre-stated rule, and the cell is erratic

Owner's question: run the Method-B comparison on five more positions; if the collapsed cell is worse beyond the noise
band on most, it is a class defect and the warning becomes emphatic; if worse on one and equal on four, the warning
stays measured.

**Pre-stated rule (before measuring):** a position counts as WORSE if the collapsed cell's move scores worse than the
healthy move by more than that position's own restriction noise band (multi-PV score vs restricted score for the SAME
move).

## The six positions (PC r15, Threads 1, Hash 16 for scoring, depth 16; collapsed cell = Hash 2048 + MultiPV 8, `go wtime 5000`)

| # | healthy H | score H | collapsed C | score C | delta | noise band | verdict |
|---|---|---|---|---|---|---|---|
| 1 | g7g6 | cp −297 | d5d4 | cp −500 | **−203** | 31 | **WORSE** |
| 2 | b6b5 | cp −297 | b6b5 | cp −297 | 0 | 71 | SAME MOVE |
| 3 | g1g6 | cp 298 | g1g6 | cp 298 | 0 | 221 | SAME MOVE |
| 4 | h7h5 | cp −804 | g7g6 | cp −786 | +18 | 20 | equal |
| 5 | f6g5 | cp −615 | f6g5 | cp −615 | 0 | 726 | SAME MOVE |
| 6 | f4f5 | cp 3794 | e4f5 | cp 3459 | **−335** | 310 | **WORSE** |

**Summary: WORSE 2, equal-but-different 1, same move 3 → NOT a class defect by my pre-stated rule.**

## The detail that matters more than the verdict: the collapsed cell is ERRATIC
On position 1 the collapsed cell gave, over six runs:
`d5d4` with **0 nodes**, then `b8a8` (nodes 67, 67, 143, 220, 220) — **two different moves, one of them from a
0-node answer.** So on this position the collapsed cell is not reliably "the same wrong move"; it is sometimes no
search at all. That is worse than a wrong recommendation: a `bestmove` from 0 nodes is the fallback-move path
(my S-F11/S-C26 family), reached here because the MultiPV-per-line `tt.clear()` consumes the entire clock.

My job51 reading of this position (`b8a8`, 46 cp worse, 3/3 stable) was taken with `go wtime 5000` **on an idle
machine**; with more load the same cell can degrade to 0 nodes. So the honest statement of the defect is:
**"Hash 2048 + MultiPV 8 can answer from 0 nodes, or from depth 1, non-deterministically, and when it does search it
recommends a move that measured 46 cp and 203–335 cp worse on 2 of 6 positions."**

## How the warning should read, given both results
- **NOT a class defect in the "every position gets a worse move" sense.** On 3 of 6 positions the collapsed cell
  returned the *same* move as the healthy setting, and on 1 more an equally good one.
- **IS a class defect in the reliability sense**: the cell is non-deterministic and can return a 0-node answer. That
  is a failure of the analysis path on every position where it happens, regardless of move quality.
- Therefore: the warning stays **measured** on move quality (2 of 6 worse, sometimes 200–335 cp worse), and becomes
  **emphatic** on reliability (0-node answers, varying depth, varying move).

## Practical advice, unchanged
**MultiPV 1 at any Hash, or Hash ≤ 16 MB with MultiPV > 1.** Nothing in these six positions argues otherwise.

## Limits
- Six positions from the swarm G set, one depth for scoring (16), one clock (5 s) for the collapsed cell.
- Position 1's collapse is load-sensitive (job51 saw `b8a8` 3/3; here it varied and once gave 0 nodes), so the
  erratic behaviour is understated if the machine is idle and overstated if busy. I state both observations.
- `Threads 1` throughout, as required.

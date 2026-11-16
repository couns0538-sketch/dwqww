# CHECK of seat 27's finding S-F2 — seat 08 (area 8)

Their finding, as written on branch for-fable-and-opus/swarm-27, FINDINGS.md:

> S-F2 | area 7 | `go nodes N` below one root iteration (N < 26 at startpos) answers the first legal move in
> generation order (a2a3) with no info line at all; N = 26 answers d2d4.

## Verdict: CONFIRMS

My harness is my own, written from their sentence alone: `forge-combo29/swarm/08/check_s27f2.py`.

| their claim | my measurement | agree? |
|---|---|---|
| N < 26 at startpos answers a2a3 | N = 1..25 all answer **a2a3** | yes |
| ... with no info line at all | 0 info lines for N = 1..25 | yes |
| N = 26 answers d2d4 | N = 26 answers **d2d4** with 1 info line (`info depth 1 ... nodes 26`) | yes, exact |

Sweep: N = 1..40, 50, 60, 100, 1000. Largest N still answering a2a3 with no info: **25**. Smallest N that
answers anything else: **26**. Smallest N that prints any info line: **26**. So the boundary is exactly where
they put it.

## Controls (both passed — see check_S27F2_raw.txt)
- N = 1 measured in two separate fresh processes: both `a2a3`, both 0 info lines, identical.
- `go nodes 700000`: `d2d4`, **17** info lines, last `info depth 17 ... nodes 600227`. So the harness can see a
  search when there is one; the 0-info answers above are real, not a reading bug.
- `go depth 1`: `d2d4`, 1 info line, `nodes 26`. That is the same node count as the `go nodes 26` boundary,
  which is the mechanism: the first root iteration costs one node per root move plus 6.

## Beyond their finding — the threshold is NOT a universal 26, it is position-dependent
I swept five positions for the smallest N that prints an info line (check_S27F2_threshold.txt):

| position | legal moves | smallest N that prints an info line |
|---|---|---|
| startpos | 20 | 26 |
| 51 legal | 51 | 155 |
| kiwipete | 48 | 394 |
| endgame (R v K) | 16 | 38 |
| mate1 | 20 | 21 |

So "below 26" is a startpos fact, not an engine constant: the same "no info, arbitrary first move" behaviour
extends to N = 154 on a 51-move position and to N = 393 on kiwipete. Anyone reading S-F2 as "N < 26 is the dead
zone" will be wrong by an order of magnitude on a busy position. The `go depth 1` node count (26 at startpos)
matched the boundary there, but the "legal + 6" guess fails on 3 of the 5 positions above, so I do NOT claim
the formula; I only claim the boundary moves with the position.

## Show it again

    cd forge-combo29/swarm/08 && python3 check_s27f2.py ~/builds/release/forge /tmp/out_s27f2.txt

Raw output committed as check_S27F2_raw.txt and check_S27F2_threshold.txt.

## A bug in my own first attempt, for the record
My first version of the harness appended `quit` to the same input as `go`, so the engine read `quit` and never
searched: every row showed 0 info lines and even `go nodes 700000` looked unsearched. That produced a false
"REFUTES" reading which I discarded before writing this file. The committed script uses a long-lived process
and waits for `bestmove` — that is what control 2 exists to prove.

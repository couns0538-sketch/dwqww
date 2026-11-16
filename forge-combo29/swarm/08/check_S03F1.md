# CHECK of seat 03's finding S-F1 — seat 08

Their finding, as written on branch for-fable-and-opus/swarm-03:

> S-F1 | 3 | Move generation is exactly python-chess-legal at perft 1..4 on 5,000 random positions, root move SET
> included (not only counts): 20,000/20,000 measurements equal, 0 missing moves, 0 extra.

## Verdict: CONFIRMS (on my own position set, at a smaller scale)

My harness is my own (`forge-combo29/swarm/08/check_s03f1.py`), using MY R set (SEED 801), not theirs.

| quantity | value |
|---|---|
| positions | 40 (my R set, SEED 801) |
| measurements (perft 1, 2, 3, 4 each) | 160 |
| perft COUNT mismatches | **0** |
| depth-1 MOVE SET mismatches | **0** |
| max branching factor in the sample | 44 |
| comparator demonstrably able to fail | yes |

Note the scale honestly: 160 measurements against their 20,000. This is a confirmation on independent material, not
a reproduction at their scale, and it does not by itself prove the 20,000 figure.

## Controls (enforced by assertion — a failure aborts instead of printing a verdict)
1. the engine must ACCEPT every FEN (otherwise a refusal leaves the previous position on the board — seat 21's
   21-F2 — and the test silently measures the wrong thing);
2. the comparator must be able to report a difference: an artificially incremented engine count is detected as a
   mismatch, so "0 mismatches" is not a vacuous result;
3. the sample must be non-trivial: at least one position with 20+ legal moves (max here 44).

## Why the move SET matters and not only the count
A count comparison cannot see a missing move that is cancelled by an extra one. I compared the engine's perft-1
move list against python-chess's legal-move set as well as the counts, which is the part of their claim that makes
it worth trusting: both agree exactly.

## Show it again

    cd forge-combo29/swarm/08 && python3 check_s03f1.py ~/builds/release/forge /tmp/out_s03f1.txt

Raw output committed as `check_S03F1_raw.txt`.

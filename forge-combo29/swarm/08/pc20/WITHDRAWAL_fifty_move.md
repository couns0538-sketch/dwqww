# WITHDRAWAL of the "defect" wording in 08-C6 and 08-F22 — seat 08

`FABLE_TO_swarm_6.md` gives the test that decides it: a cp 0 at a high counter is a defect **only when a forced mate
exists that ends no later than the 100th half-move**, i.e. only if `2N - 1 <= 100 - H`.

## The test, run (`check_fifty_defect.txt`)

Board `1K6/8/8/3R4/8/8/8/k7 w - - H 1`, PC r15, PC20, Threads 1, Hash 16.

| H | depth | score | plies | nodes |
|---|---|---|---|---|
| 0 | 20 | mate 8 | 15 | 1,065,273 |
| 0 | 24 | mate 8 | 15 | 1,979,939 |
| 0 | 28 | **mate 8** | **15** | 2,890,502 |
| 91 | 20 | cp 0 | — | 43,082,856 |
| 91 | 24 | cp 0 | — | 64,830,080 |
| 91 | 28 | cp 0 | — | 88,968,052 |
| 99 | 20 | cp 0 | — | 400 |

| quantity | value |
|---|---|
| mate distance at counter 0 | **mate 8 = 15 plies** |
| half-moves left at H=91 | **9** |
| `2N - 1 <= 100 - H` | **15 <= 9 — FALSE** |

## What this means

**The engine cannot mate from this board in 9 half-moves; it needs 15.** The owner's match program ends the game at
the 100th half-move without a capture or pawn move, so with 9 to go the game is over before the mate arrives —
**cp 0 is the correct score**, and my 08-C6 and 08-F22 calling it "a defect" were **wrong**. I withdraw that wording.

Note also that the sweep's earlier "cp 0 from H=91" reading is consistent: at every counter where fewer than 15
half-moves remain the draw score is right. My original check asked only "is the position won?" — which it is — and
never asked "can the mate arrive before the limit?", which is the question that decides the verdict. That was the
error, and it is the same shape of error file 6 warns about.

## What still stands from 08-C6 / 08-F22

- **The measurement stands in full**: the score flips from a win to cp 0 at H=91, exactly where seat 05 said; the
  band runs H=91..99; and the **node costs are real and enormous** — 43,082,856 nodes at H=91 depth 20 (against
  1,065,273 at H=0), rising to **88,968,052 at depth 28**. Those are measured facts about time, not verdicts about
  correctness.
- **What changes is only the interpretation**: this is a COST, not a wrong verdict. The engine spends up to 89
  million nodes to reach a correct conclusion at a high counter.
- 08-C6's confirmation of seat 05's *number* (H=91) is unaffected; seat 05's own S-F23 already established that a
  claimable draw scored 0 can be correct, and file 6 makes that general.

## The residual question this leaves, stated rather than hidden

The cost is large enough that it may matter on the owner's real clock: 43M nodes at depth 20 on a 6 s + 0.06 clock
would not finish an iteration. Whether that costs playing strength is a **match question** and is not answered here.
What is answered: **it is not a wrong score.**

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_fifty_defect.py /tmp/fd.txt

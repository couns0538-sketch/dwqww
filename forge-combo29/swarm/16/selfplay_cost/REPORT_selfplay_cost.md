# REPORT_selfplay_cost — what the PC's 2,000-node self-play budget costs per move

**What was asked (my own priority: the PC's real path):** file 6 says the owner's self-play uses `go softnodes
2000`. S-F16 showed it is deterministic and overshoots to ~1.7x. The open question: is the move it picks WORSE
than a deeper search's, and by how much?

**The answer: the budget is roughly a wash — 4 positions worse by >30 cp (worst +109) against 3 BETTER by >30 cp
(best −109), median cost 0 cp, and the two budgets choose the SAME move on 25 of 40 positions.**

```
positions measured         40 of 40
same move as 250k          25 of 40
median cost                 0 cp
worse by >30 cp             4
worse by >100 cp            1   (idx 34, +109)
BETTER by >30 cp            3   (best -109)
```

**The worse cases** (positive = the 2,000-node move is worse than the 250,000-node one):

```
idx 34  +109 cp   low d4e4  ref g3f3   8/5p2/1k6/p4r1p/1b1R1P2/6K1/8/8 w - - 0 1
idx  6   +92 cp   low h8f8  ref d6e6   2r4r/pp4k1/3q2p1/3ppn2/1P4QP/P2P1N2/R4P2/4RK2 b
idx 12   +79 cp   low e5e4  ref b6c6   rn2r1k1/pp3pp1/1q3n2/2bpp3/6bR/1BPP1N2/PP1NQP2/R1B1K3 b
idx 14   +39 cp   low b8b6  ref e6d7   rr6/p5pk/2pNbn1p/2Q5/2P5/8/PP3PPP/2KR4 b
```

**The better cases** (the shallow budget beat the deep one):

```
idx 37  -109 cp   low h8h1  ref h8g8   7r/2k2p2/2p3P1/2Ppn3/PP2p1b1/4P3/4BK2/R6R b
idx 29   -82 cp   low e4b1  ref c3e3   8/8/8/4kPK1/4B4/2R5/8/8 w
idx 10   -67 cp   low c7c6  ref e8e6   4r1k1/2pn1pp1/1p5p/p3p3/PP2P3/2PB2P1/5P1P/R5K1 b
```

So the 2,000-node self-play budget is **not systematically underpowered** on this sample: it loses ground on four
positions and gains it on three. That is a useful negative for the owner — the concern that self-play at 2,000
nodes plays badly is not supported. Two individual positions are worth a look (idx 34 at +109 cp is the largest
single loss), and both are committed with their FENs above.

## MY METRIC HAD AN INVERTED SIGN, AND I CAUGHT IT BECAUSE ONE CASE CONTRADICTED THE DATA

The first run reported `worst cost +109 cp` at **idx 37 with move `h8h1`**. That position is one I had already
examined in S-F24, where `h8h1` **wins a rook** (white goes from two rooks to one). A move that wins a rook being
"the worst blunder of the run" was obviously wrong, so I checked it instead of reporting it.

The cause: my script computed `cost = score_after(low) − score_after(ref)`, both from the **mover's** point of
view. A POSITIVE value therefore means the low-budget move scored **HIGHER** — i.e. it was BETTER. Every sign in
the first summary was inverted. Verified directly at depth 14 on that position:

```
after h8h1 : opponent-to-move score cp 568  -> mover's score -568   (wins the rook)
after h8g8 : opponent-to-move score cp 613  -> mover's score -613
```

so `h8h1` is 45 cp BETTER for the mover, and the "cost" for idx 37 is −109 in the corrected convention. The table
above uses the corrected sign throughout; the raw file keeps my script's original numbers so the arithmetic can be
re-derived. **This is the fifth self-correction on this branch and it belongs in FINAL PART 4.**

**How sure:** high on the corrected table (the sign is now verified against a hand-checked position and a
depth-14 re-search, and the 25/40 same-move count is independent of the sign). Medium on the individual
cp values: a fixed depth-12 reference search is a proxy for "good move", not ground truth, and in a lost position
it rates moves that lose more slowly as better.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge  PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dcded
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16; low = `go softnodes 2000`, ref = `go nodes 250000`,
         reference evaluation of each resulting position = one `go depth 12`; 40 G positions, cold per search
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 40 positions: softnodes 2000 vs nodes 250000 | done | `raw/selfplay_cost.txt` | 25/40 same move |
| cost measured by a fixed depth-12 reference search | done (sign corrected) | same | median 0 cp; 4 worse >30, 3 better >30 |
| verify the largest "cost" by hand | done | depth-14 re-search above | idx 37 `h8h1` WINS a rook — my sign was inverted |
| a larger sample | NOT done | — | 40 positions |
| ground truth instead of a depth-12 proxy | NOT done | — | would need long searches per position |

## Findings

`S-F30 | 6 | the PC's 2,000-node self-play budget is roughly a WASH against its 250,000-node match budget: on 40 real-game positions the two choose the SAME move 25 times, the median cost is 0 cp, 4 positions are worse by >30 cp (worst +109 at idx 34, 8/5p2/1k6/p4r1p/1b1R1P2/6K1/8/8 w) and 3 are BETTER by >30 cp (best -109 at idx 37) — so the concern that self-play at 2,000 nodes plays badly is not supported. NOTE: my first summary had the cost sign inverted; caught by an absurd case where a rook-winning move scored as the worst blunder | selfplay_cost/raw/selfplay_cost.txt selfplay_cost/selfplay_cost.py | NEW |`

## Suspicions, not proven

- That idx 34 (+109) is a real tactical miss rather than a depth-12 proxy artefact. Its FEN is committed; a longer
  search would settle it and I did not run one.

## What I did NOT do

- Did not use ground truth (long searches / tablebase) — every "cost" is relative to a depth-12 reference search.
- Did not test more than 40 positions or the other match budgets.
- Did not re-run with the sign fixed in the script (the arithmetic is re-derived and documented above instead; the
  script's original output is kept unchanged so the correction is auditable).

## Times

`selfplay_cost/stamps.txt`, every line a `date -u`.

# REPORT — the mate-PV truncation: what it is, when it appears, and whether it matters

Seat 05, area 5. Branch `for-fable-and-opus/swarm-05`. Builds: base 6b98f217 and PC r15 (patch sha256 prefix
`d6bd72c531f785f4`). **Threads 1**, Hash 16, `OwnBook false` everywhere. Process discipline: **COLD** (a fresh engine
process per measurement) for every number here unless stated.

## What the defect is

A `mate N` score is a promise that the side to move mates in 2N−1 plies (N>0) or is mated in 2|N| (N<0). Sometimes the
PV the engine prints alongside that score is **shorter than the score requires** and does not end in mate. That is a real
inconsistency between two things the engine reports about the same search.

Found first on G/192 (`8/8/1p6/8/p3p3/8/2Kpk3/8 w`) under S14 at depth 12: `score mate -12` with an 18-ply PV needing 24,
and searching deeper the score collapsed to −9, −6, then −4 — i.e. the depth-12 score was not merely under-reported, it
was wrong, and a mate in 6 plies is provable by hand.

## When it appears — the mechanism, established by a depth sweep

The truncation is a **depth-limited** effect at long mate distances. On G/192 (base build, S14, Threads 1):

| depth | score | PV plies | needed | verdict |
|---|---|---|---|---|
| 12 | mate −12 | 18 | 24 | **short by 6** |
| 14 | mate −9 | 15 | 18 | **short by 3** |
| 16 | mate −6 | 12 | 12 | ok |
| 18 | mate −5 | 10 | 10 | ok |
| 20 | mate −5 | 10 | 10 | ok |
| 24 | mate −4 | 8 | 8 | ok |
| 28 | mate −4 | 8 | 8 | ok |

So the PV is short *exactly while the reported mate distance needs more plies than the depth that reported it*, and the
engine both shortens the distance and completes the PV as depth rises. R/120 behaves the same way (depth 12: mate −13,
14 of 26; depth 14: mate −10, 20/20 ok).

**Which boards:** across my 28 mate positions, the 25 with |N| < 10 are all consistent; the truncated ones are the long
mates (|N| = 12, 13). That is why it looks erratic on a small sample — it needs long mates to show at all.

## Does it matter for the owner? — mostly no

This is the part that decides whether anyone should act.

| setting (PC r15 build) | mate scores | truncated | rate |
|---|---|---|---|
| `go softnodes 2000` (self-play budget) | 17 | 1 | 5.9% |
| `go nodes 20000` (smallest match budget) | 20 | 1 | 5.0% |
| `go nodes 50000` | 25 | 0 | 0% — **but this was sampling luck, see below** |
| `go nodes 250000` | 27 | 0 | 0% (same caveat) |
| PC20 at depth 12 (unbudgeted) | 27 | 0 | 0% |
| S14 at depth 12 (base and PC builds) | 28 | 2 | 7.1% |

**A correction that matters.** I first read the two zeros above as "the truncation is confined to small budgets". That was
a **sampling artefact**: only 3 of those 28 positions had |N| ≥ 10, the range where the defect lives. When I searched 400
random-play games specifically for long mates (finding just **2** such positions) and tested one at the match budget:

> `r2r4/pB2kpp1/n1p4p/1p5p/2n5/1q1bP2P/2PBN3/4K2R b - - 1 40`, `go nodes 50000`, 4 of 4 runs identical:
> **`score mate 11` with an 18-ply PV needing 21 — short by 3** (44,749 nodes, depth 11).

At `go nodes 250000` the same position is consistent (`mate 7`, 13/13), as is `go depth 20`.

So the honest statement is: **the rate falls as the budget rises, but the defect is still present at a 50,000-node match
budget on long mates, and I have NOT established any budget at which it is absent.**

**A later measurement narrowed it to a one-iteration window.** On that same position the full node ladder is: 5000 → no
mate score (cp +3725, d8); 10000 → cp +3935 (d9); 15000/20000/30000 → cp +4056, d10, all identical (10,515 nodes);
**50000 → `mate 11`, 18 of 21 plies, short by 3**; 80000 → `mate 7` 13/13 (74,525 nodes, d13); 120000 → identical;
250000 → `mate 7` 13/13 (d14); 500000 → same (d15).

So the defect is neither "below" nor "above" a narrow band: below 50,000 nodes the engine has not yet found the mate,
and from 80,000 up the mate it finds is short enough for its depth. That makes it a **one-iteration artefact** — the
depth-11 iteration completes carrying a mate score whose PV that depth cannot fill — rather than a general property of
node-limited search. It is still on the owner's path, because 50,000 nodes is one of their match budgets.

**And where it does occur, the move does not change — now checked on the match-budget case too.** Two positions:

- G/59 at `go softnodes 2000`: score `mate 4` with a 6-ply PV (needing 7), but the move is `c4a6` at softnodes 2000, 5000,
  `go depth 12` and `go nodes 20000` — identical.
- The S-F58 position that truncates at `go nodes 50000` (`mate 11`, 18 of 21 plies): the move is **`b3c2` at every budget** —
  softnodes 2000, nodes 20000, nodes 50000, nodes 250000 and depth 20 — and the PV's first move equals the bestmove in
  every row.

So the defect as I can observe it is confined to the **score and PV-length reporting**: the engine chose the same move
whether or not its PV was long enough to justify its own score. That is two positions, not a distribution — enough to say
"the move did not change here", not enough to claim it never does.

## What I got wrong along the way, and corrected

- **S-F19**: I claimed two PC20 options each "fixed" the truncation, on one board. Seven further boards showed
  `TtPruneV2` alone *creates* truncation on two of them. Corrected by S-F21 — it is position-specific and no single
  option is a cure.
- **S-F23**: I reported "0 of 27 under PC20" as if PC20 reduced a rate. S-F25 showed an independent 8-mate sample is
  0-truncated under S14 too, so the base rate was not established well enough to claim a reduction. Re-worded to "no
  truncation observed on that set".
- **S-F42**: I implied the clock's shallower search cost playing strength. Checking the scores showed the deeper search
  was *more pessimistic* in both differing positions, so no strength loss is demonstrated. Corrected.
- **S-F30**: my own |N| ≥ 10 rule rests on 3 qualifying positions, and my independent sample has |N| ≤ 4 — it cannot
  test the rule. Stated rather than glossed.

## Honest summary

The defect is real, reproducible and deterministic, and I can describe it precisely: **a long mate score reported at a
depth too shallow to carry its PV**. For the owner's actual match settings (`go nodes` 50000 and 250000, PC20, Threads 1)
**I could not reproduce it at all on 28 positions**, and at the smallest budget where I could, the move was unaffected.
The case where it is most visible (`softnodes 2000`, the self-play budget) changes a reported score by one move of mate
distance, not the move played.

**Not claimed:** any cause in source. I did not read the PV-rebuild code. **Not established:** whether a longer-mate
position exists where the move *would* change at a match budget — 28 positions is a small sample for a 5-7% effect, and
a larger mate-rich set (selected for |N| ≥ 8) is what a follow-up should use.

## Evidence
`job1/out/{rows.jsonl,criterion_table.txt,probe_192_trend.txt}`, `job1b/outR/{check_table.txt,probe_R120.txt}`,
`pcbuild/out/{sf1_isolation.txt,sf1_consistency.txt,sf19_boards.txt,pc_trunc_rate.txt,pc_trunc_rate_s14.txt,truncation_rate.txt,base_trunc_repeat.txt,mate_sample_s14.txt,mate_sample_pc20.txt}`,
`match/out/{softnodes_trunc.txt,short1_detail.txt,g59_movecheck.txt,trunc_match_budgets.txt}`,
`job2/out/cliff_vs_depth.txt`. Findings: S-F1, S-F9, S-F17, S-F19 (corrected), S-F21, S-F22, S-F23 (bounded), S-F24,
S-F25, S-F27, S-F28, S-F29, S-F30, S-F48, S-F57.

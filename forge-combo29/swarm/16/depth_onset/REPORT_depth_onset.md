# REPORT_depth_onset — at which depth does each asymmetry begin? (full G set, 353 positions)

**What was asked:** another seat reports depth 1 = 30/30 equal and depth 2 = 22/30 reproducibly, and says the
asymmetry begins "a ply earlier than my summary implies". I measured all three quantities on the full G set to
settle it — and in doing so found an overreach in my own S-F8.

**The answer: the two statements are about DIFFERENT quantities, and both are right. Scores and bestmoves are
symmetric at depth 1 and break at depth 2; NODE COUNTS are already unequal at depth 1.**

```
depth | score equal | bestmove equal | node equal | of
    1 |      353    |       352      |    112     | 353
    2 |      242    |       321      |     41     | 353
```

- **Scores:** 353/353 equal at depth 1 — fully symmetric — and 242/353 at depth 2, i.e. **111 of 353 unequal
  (31.4 %)**. The other seat measured 8 of 30 unequal (27 %). Same phenomenon; my larger sample brackets theirs.
  **So the other seat is right, and "the asymmetry begins at depth 2" is the correct statement for SCORES.**
- **Bestmoves:** 352/353 at depth 1, 321/353 at depth 2 — the same shape, one position early.
- **Node counts:** only **112 of 353** equal at depth 1 (68 % already unequal). So for node counts the asymmetry
  is present from the very first ply, which is what my S-F8 and S-F11 experiments were measuring.

**Where my summary needed the correction:** my FINAL says "restores exact node symmetry at depth 1 only", which is
scoped to node counts and is not wrong — but S-F8's phrasing "restores exact node symmetry at DEPTH 1 ONLY (65 vs
65 ...)" reads as a general claim, and on 20 positions the full-window root gives **11 of 20** node-equal at depth 1,
not 20 of 20. **So "65 vs 65" was one position, and I generalised from it.** That is the eleventh self-correction
on this branch, and it is the same species as the others: a single case stated in language that sounds general.

The fix is not to withdraw the experiment (the probe position is real and the depth-2/3 behaviour reproduces) but
to say what it measured: on THAT position the full-window root made depth-1 node counts equal, and across 20
positions it improves node equality from 9/20 to 11/20 but does not restore it.

**How sure:** high on the 353-position table — it is a direct count with no proxy. High that the two seats agree
once scores and node counts are separated.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge  PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dcded
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16; depths 1 and 2; all 353 G positions plus colour mirror;
         cold (fresh process + ucinewgame) per search
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 353 positions × 2 depths × mirror, three quantities | done | `raw/depth_onset.txt`, `run.log` | 353/353 scores at d1 → 242/353 at d2 |
| reconcile with the other seat's 30/30 and 22/30 | done | same | same shape; my 31.4 % brackets their 27 % |
| test S-F8's "exact node symmetry at depth 1" as a general claim | done — MY CLAIM WAS OVERREACHED | `../check_fullwindow/raw_fullwindow.txt` | 11 of 20 node-equal, not 20 of 20 |
| node-count asymmetry at depth 1 | done | `raw/depth_onset.txt` | 112 of 353 equal (68 % already unequal) |

## Findings

`S-F33 | 6 | the colour asymmetry's ONSET depends on the quantity, measured on all 353 G positions under PC20 at Threads 1: at depth 1 SCORES are equal on 353/353 and BESTMOVES on 352/353, but NODE COUNTS are equal on only 112/353 (68 % already unequal); at depth 2 scores fall to 242/353 (111 unequal = 31.4 %, bracketing another seat's 27 % on 30 positions) and bestmoves to 321/353. So "the asymmetry begins at depth 2" is correct for scores and bestmoves and wrong for node counts, where it exists from the first ply | depth_onset/raw/depth_onset.txt depth_onset/run.log (again: `python3 depth_onset/depth_onset.py ~/builds/bld-pc/forge /tmp/o`) | NEW |`

`S-F8 (CORRECTED) | the full-window-root claim "restores exact node symmetry at DEPTH 1 ONLY (65 vs 65)" was ONE POSITION stated as if general: across 20 positions the full-window root improves depth-1 node equality only from 9/20 to 11/20, not to 20/20. The experiment stands (the probe reproduces, and depth 2/3 fail as stated); the generalisation does not | check_fullwindow/raw_fullwindow.txt depth_onset/raw/depth_onset.txt | CORRECTED |`

## Suspicions, not proven

- That the node-count asymmetry at depth 1 has the same cause I named (generation order): plausible, since at one
  ply there is no ordering-dependent state below the root, and my S-F12 experiment showed the root loop carries it.
  Not re-tested at this scale.

## What I did NOT do

- Did not measure depth 3+ on all 353 positions (depths 1 and 2 answer the onset question).
- Did not re-run the full-window root across all 353 positions — 20 was enough to show the generalisation fails.

## Times

`depth_onset/stamps.txt`, every line a `date -u`.

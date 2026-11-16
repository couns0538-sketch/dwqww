# REPORT_pcsym10 — the 353-pair colour sweep on the PC build under PC20 (depth 10)

**What was asked:** the direct comparison to my base-tree job 3 — does the colour asymmetry still exist on the PC
build under PC20 at the full 353-position depth-10 level?

**The answer: yes, and it is slightly WORSE than on the base tree: 120 of 353 bestmoves fail to mirror (base
tree: 101), while score-equality is marginally better (22 vs 19).**

```
| quantity                    | base tree + S14 | PC r15 + PC20 |
|-----------------------------|-----------------|---------------|
| mirror pairs                |             353 |           353 |
| score equal                 |              19 |            22 |
| bestmove equal (mirrored)   |             252 |           233 |
| bestmove MISMATCH           |             101 |           120 |
| node counts equal           |  (not recorded) |             0 |
```

**Position-for-position, the two runs disagree about whether a pair matches on 109 of 353 positions** (bestmove
verdict) and 19 of 353 (score verdict). So the PC build is not merely "the same asymmetry with more nodes" — the
two engines take *different* asymmetric paths, which is what the added pruning options would produce.

**Node counts are equal on 0 of 353 pairs on the PC build.** That is the strongest form of the asymmetry
statement I have: not one position out of 353 traverses the same number of nodes as its mirror.

**P4 (reproducibility at Threads 1) PASSED exactly:** 30 re-run positions gave 30/30 identical scores, identical
node counts and identical bestmoves. So every number above is a reproducible Threads-1 measurement, not the
threaded score noise seat 04 found.

**How sure:** high. 353 pairs × 2 mirror searches + 30 re-runs = 736 searches, each a fresh process with
`ucinewgame`, Threads 1, loud failure on a missing score or refused option.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge   (PC r15, -DFORGE_MATE_ALPHA_GUARD=1, patch sha256 d6bd72c531f785f4 verified)
none   312866 / 862329 / 3024920 / 4865609      S14  242796 / 656517      PC20  278024 / 587276   (all match file 5)
settings: PC20 (S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true,
          OwnBook false) + Threads 1 + Hash 16   <- Threads 1 is the swarm rule for scores
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 353 pairs at depth 10, PC20, Threads 1 | done | `raw_G353.tsv`, `raw_G353.meta` | 120/353 bestmove mismatch, 22/353 score equal, 0/353 node equal |
| compare with base tree + S14, position for position | done | `analyse_pcsym10.py` output | 109/353 bestmove-verdict disagreements, 19/353 score-verdict |
| Threads-1 reproducibility (P4) | done | `raw_rerun.tsv` | 30/30 identical score, nodes and bestmove |
| run the same sweep on the base tree WITHOUT S14 to isolate the settings | NOT done | — | would separate "PC code" from "PC20 settings"; next job |
| which of the four options causes the +19 mismatch | partly | `../pcsym/raw_pcsym.txt` | at depth ≤2 only TtPruneV2 mattered; not yet tested at depth 10 |

## Findings

`S-F14 | 6 | PC r15 build under PC20, Threads 1, depth 10, all 353 G positions: the colour asymmetry is slightly WORSE than on the base tree — 120/353 bestmoves fail to mirror (base tree 101), and NOT ONE of the 353 pairs has equal node counts; score equality is marginally better (22 vs 19). The two engines disagree about whether a pair matches on 109 of 353 positions, so the PC build takes different asymmetric paths, not the same ones with more nodes. Threads-1 reproducibility verified exactly (30/30 identical scores, nodes and bestmoves on a re-run) | pcsym10/raw_G353.tsv pcsym10/raw_rerun.tsv (again: `python3 pcsym10/pcsym10.py ~/builds/bld-pc/forge /tmp/o.tsv /tmp/m.tsv --limit 30`) | NEW |`

## Suspicions, not proven

- That the extra 19 mismatches come from the PC20 settings rather than the PC code. The clean test is the same
  sweep on the PC build with S14 only (no PC20), and on the base tree with PC20's options — neither is done yet.
- That the generation-order cause I named on the base tree operates identically on the PC build. Not retested.

## What I did NOT do

- Did not run the sweep on the PC build under S14 (to split code effects from settings effects).
- Did not test each option at depth 10 (the depth-≤2 sweep showed only TtPruneV2 matters there; depth 10 may
  differ).
- Did not use the PC's own trained net (not shared; all of this is the built-in evaluation).

## What I am NOT sure about

- Whether any of this changes under the PC's real net. The net is not shared, so evaluation-dependent questions
  stay open by design (file 2, rule 2).

## Times

`pcsym10/stamps.txt`, every line a `date -u`.

## Last command output

```
$ git status --short
 M FINDINGS.md
 M pcsym10/stamps.txt
?? REPORT_pcsym10.md
?? pcsym10/analyse_pcsym10.py
?? pcsym10/last_cmd.txt
?? pcsym10/pcsym10.py
?? pcsym10/raw_G20.meta
?? pcsym10/raw_G20.tsv
?? pcsym10/raw_G353.meta
?? pcsym10/raw_G353.tsv
?? pcsym10/raw_rerun.meta
?? pcsym10/raw_rerun.tsv
?? pcsym10/run.log
$ ls
audit_19F12
check_06F12
check_20F14
check_28F1
check_belowroot
check_fullwindow
check_S-F1
check_S-F2
check_S-F3
check_S-F5
check_warmcold
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
job1_seed1611
job2
job3
ownbook_check
pcbuild
pcsym
pcsym10
REPORT_audit.md
REPORT_belowroot.md
REPORT_check_06F12.md
REPORT_check_20F14.md
REPORT_check_28F1.md
REPORT_check_S-F1.md
REPORT_check_S-F2.md
REPORT_check_S-F3.md
REPORT_check_S-F5.md
REPORT_fullwindow.md
REPORT_job1.md
REPORT_job2.md
REPORT_job3.md
REPORT_ownbook_check.md
REPORT_pcsym10.md
REPORT_pcsym.md
REPORT_reverse_list.md
REPORT_wall_vs_iteration.md
REPORT_warmcold.md
SEAT.txt
STATUS.md
$ ls pcsym10
analyse_pcsym10.py
last_cmd.txt
pcsym10.py
prediction.txt
raw_G20.meta
raw_G20.tsv
raw_G353.meta
raw_G353.tsv
raw_rerun.meta
raw_rerun.tsv
run.log
set_G.epd
stamps.txt
```

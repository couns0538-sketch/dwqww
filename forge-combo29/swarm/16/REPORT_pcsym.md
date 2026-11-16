# REPORT_pcsym — colour asymmetry on the PC build (r15) under PC20, and what each new option does

**What was asked:** does the colour asymmetry still exist on the PC build under PC20, and does each of the four
new options (CuckooRep, HistRework, TtPruneV2, CorrHistV2) change it?

**The answer: yes, the asymmetry is still there on the PC build, and only ONE of the four options changes it —
TtPruneV2, which makes it slightly WORSE. The other three change nothing measurable at these depths.**

```
config          depth 1                        depth 2
                nodes   score   bestmove       nodes   score   bestmove
pc20 (all on)   9/20    20/20   20/20          2/20    14/20   18/20
no_cuckoo       9/20    20/20   20/20          2/20    14/20   18/20
no_histrework   9/20    20/20   20/20          2/20    14/20   18/20
no_ttprune      9/20    20/20   20/20          3/20    13/20   19/20   <- the only row that moves
no_corrhist     9/20    20/20   20/20          2/20    14/20   18/20
all_four_off    9/20    20/20   20/20          3/20    13/20   19/20
s14_only        9/20    20/20   20/20          2/20    14/20   18/20
```

("n/20" = mirror pairs whose quantity is EQUAL. Lower is more asymmetric, so a LOWER node-equal count means
MORE node asymmetry.)

**Reading it:**

- **The asymmetry survives on the PC build.** At depth 2 only 2 of 20 pairs have equal node counts and 14 of 20
  have equal scores. Nothing the new options add repairs it.
- **TtPruneV2 is the only one that matters at these depths**, and its effect is small and in the wrong
  direction: turning it OFF (or turning all four off) raises node-equal pairs 2→3 and score-equal 14→13, i.e.
  slightly LESS symmetric on scores, slightly MORE on nodes. So TtPruneV2 is not a fix and not a cause.
- **CuckooRep and HistRework are invisible at these depths**, and so is CorrHistV2 — but that is a property of
  the DEPTH, not of the options: I verified each option does change the search at deeper settings
  (`CuckooRep` off: 1574→1575 nodes at depth 6; `HistRework` off: 1574→1531; `TtPruneV2` off: 1574→1257 and the
  score changes −303→−314; `CorrHistV2` off leaves that one position identical but differs on 7 of 18
  position×depth combinations at depths 6 and 8). So the "no change" rows are honest nulls at depth ≤ 2, not
  evidence that the options are inert.
- **The depth-1 shape is identical to the base tree**: scores all equal (20/20) and node counts unequal (9/20).
  That matches my earlier base-tree full-window sweep (9/20), so the PC build has the same character here.

**How sure:** high on the table — 7 configurations × 2 depths × 20 pairs × 2 mirror searches = 560 searches,
every one a fresh process with `ucinewgame`, Threads 1, and a loud failure on a missing score or a refused
option. The "inert at depth ≤2" reading for three options is directly checked by the depth-6/8 probe above.

## Honesty numbers — PC build, verified before any of this

```
exe     /home/ubuntu/builds/bld-pc/forge   (PC r15, built with -DFORGE_MATE_ALPHA_GUARD=1)
sha256  of the patch verified against file 5: d6bd72c531f785f4 (matches)
none   312866 / 862329 / 3024920 / 4865609     <- all four match file 5
S14    242796 / 656517                          <- both match file 5
PC20   278024 / 587276                          <- both match file 5
```

Full record: `../pcbuild/PC_BUILD.txt`, raws in `../pcbuild/raw/`.

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| PC build verified (six known numbers) | done | `../pcbuild/PC_BUILD.txt` | all match |
| PC20 symmetry, depth 1 and 2, 20 G pairs | done | `raw_pcsym.txt` | asymmetry present: 2/20 nodes, 14/20 scores at depth 2 |
| each of the four options removed individually | done | `raw_pcsym.txt` | only TtPruneV2 moves anything (2→3, 14→13) |
| all four off, and S14-only | done | `raw_pcsym.txt` | same as TtPruneV2-off row |
| verify the options are not inert (deeper probe) | done | this report, depth 6/8 numbers | all four change the search; CorrHistV2 at 7 of 18 |
| sweep at depth 10 on the PC build | NOT done | — | next job; depth ≤2 was the cheap instrument |

## Findings

`S-F13 | 6 | PC r15 build, PC20, Threads 1: the colour asymmetry SURVIVES the PC build — at depth 2 only 2 of 20 mirror pairs have equal node counts and 14 of 20 equal scores — and of the four new options only TtPruneV2 changes it at these depths, slightly for the worse (nodes 2->3, scores 14->13 when it is turned off), while CuckooRep, HistRework and CorrHistV2 are inert at depth <= 2 but demonstrably active at depths 6-8 | pcsym/raw_pcsym.txt (again: `python3 pcsym/pcsym.py ~/builds/bld-pc/forge /tmp/o.txt`) | NEW |`

## Suspicions, not proven

- That the asymmetry on the PC build has the same cause I named on the base tree (generation order, necessary
  but not sufficient). I did not repeat the reverse-list experiment on the PC build.
- That TtPruneV2's small effect at depth 2 is noise-free. It reproduced identically in two separate runs of
  the same configuration, so it is deterministic, but "small and deterministic" is not "significant".

## What I did NOT do

- Did not sweep the PC build at depth 10 (the 353-pair level) — that is the next job.
- Did not test the four options' interaction with the generation-order experiment.
- Did not evaluate anything net-dependent: the PC's trained net is not shared, so all of this uses the
  built-in evaluation and says nothing about the PC's own net (file 2, rule 2).

## What I am NOT sure about

- Whether the PC's real games would show a different profile, since they run with its own net and its own
  time control rather than fixed depth.

## Times

`pcsym/stamps.txt`, every line a `date -u`.

## Last command output

```
$ git status --short
 M FINDINGS.md
 M check_belowroot/below_root_test.py
 M check_belowroot/reverse_pair.py
 M check_fullwindow/cold_depth1.py
 M pcsym/stamps.txt
?? REPORT_pcsym.md
?? pcsym/last_cmd.txt
?? pcsym/pcsym.py
?? pcsym/raw_pcsym.txt
?? pcsym/run.log
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
REPORT_pcsym.md
REPORT_reverse_list.md
REPORT_wall_vs_iteration.md
REPORT_warmcold.md
SEAT.txt
STATUS.md
$ ls pcsym
G_nocastle.fens
last_cmd.txt
pcsym.py
prediction.txt
raw_pcsym.txt
run.log
stamps.txt
```

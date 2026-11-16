# REPORT_job2 — area 6, job 2 (left-right mirror), seat 16

**What was asked:** the same colour-flip comparison as job 1, but for the LEFT-RIGHT mirror
(`board.transform(chess.flip_horizontal)`), on positions without castling.

**The answer:** all 745 positions I compared give a different evaluation when mirrored left-right
(100 %), median |Δtotal| = 38 cp, p90 = 128, max = 738. But that is NOT a defect, and I do not report it as
one: a left-right flip is a *different chess position* (startpos becomes `rnbkqbnr/.../RNBKQBNR`, white king
on d1 and queen on e1), not the same position seen from the other side — which is what the colour flip is.
No chess evaluation is required to be file-symmetric, and this engine's deliberately is not: its
piece-square tables are tuned and not file-mirrored (`PawnPsqt` rank 2 = 65,77,76,64,73,103,117,68).
So job 2 has to be read as **"measure the left-right asymmetry and name where it comes from"**, not
"find a bug". The honest result is the measurement plus the code evidence, and the finding is that the
comparison's premise does not hold — the useful job-2 result is therefore negative about a fault.

**How sure:** high on the numbers (745/745, controls pass). High that the asymmetry is intended, because
the tables are tuned per file. NOT established: which single term dominates — PSQT explains only
r = 0.35 of the measured HCE delta (see below), so pawn structure, shelter and mobility terms contribute too,
and I did not isolate them one by one.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-release/forge
sha256  e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 312866  bench 13 862329  bench 16 3024920  go perft 5 4865609   (all equal; ../HONESTY.txt)
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| build the no-castling sets (G 334 of 353, R 411 of 500) | done | `G_nocastle.fens`, `R_nocastle.fens` | 745 positions in total |
| left-right eval comparison, S14 | done | `raw/G_lr.tsv`, `raw/R_lr.tsv`, `raw/*.meta` | 745/745 differ; median \|Δtotal\| 38, p90 128, max 738 |
| which side carries it: NNUE vs HCE | done | `raw/lr_configs_fullG.txt` | HCE alone differs on 328/334; NNUE is not the sole cause |
| controls (identity, involution, antisymmetry, colour mirror) | done | `raw/controls.txt` | all four pass, `CONTROLS_FAILED: none` |
| read the eval code, name the term | partly | `src/eval.cpp:245-268`, `src/eval_params.hpp:12-48`, `eval_params_table.inc` | PSQT tables are not file-symmetric (48/64 pawn, 64/64 others); king shelter loop `eval.cpp:252` walks king_file−1 … king_file+1 and is clipped at the board edge, which is a second, structural file dependence |
| PSQT quantitatively explains the delta | done — it does NOT fully | `raw/psqt_explains_100.txt` | r = 0.349, sign agreement 56.6 %, PSQT median 36 vs measured 16.5 |
| the premise check: is a lr flip the same position? | done | `prediction.txt` discussion, `raw/controls.txt` C2/C4 | NO — startpos flips to a different array; so asymmetry is expected |

## The measurements

```
positions compared: 745
positions with any differing field: 745 (100.0 %)
differing field counts: {'hce': 727, 'nnue': 733, 'total': 742}
|delta total|: min 0  median 38  p90 128  max 738
delta total sign: >0 376  <0 366  =0 3

configuration split (334 G positions, UseNNUE false vs default):
default          differ_total 334  hce_differs 328  nnue_differs 327  median|dtotal| 33.5
nonnue           differ_total 328  hce_differs 328  nnue_differs   0  median|dtotal| 20.0
```

PSQT check on the first 100 G positions (HCE only):
```
measured hce delta vs PSQT-predicted delta: correlation r = 0.3489
sign agreement: 56 of 99 (56.6 %)   exactly equal: 5 of 100
measured |delta| median 16.5  PSQT |delta| median 36.0
```

The table itself (`src/eval_params_table.inc`, MG values):
```
PawnPsqt rank 2, files a..h: 65 77 76 64 73 103 117 68    (mirror pairs equal: none)
KingPsqt rank 1, files a..h: -30 28 9 -55 3 -22 22 11     (mirror pairs equal: none)
```

## Findings

**No new fault.** I explicitly do NOT claim "the evaluation is asymmetric" as a defect, because the
comparison's premise (that a left-right flip is the same position) is false. What is a real, reportable
observation is the measurement and its cause:

`S-F3 | 6 | the evaluation is deliberately file-asymmetric: the tuned PSQT tables are not file-mirrored (48/64 pawn squares, 64/64 for the other five pieces) and the king-shelter loop walks king_file-1..king_file+1 clipped at the board edge (eval.cpp:252), so a left-right flip changes the eval in 745/745 positions (median 38 cp) — this is intended behaviour of a tuned evaluation, not a fault | job2/raw/G_lr.tsv, job2/raw/R_lr.tsv, job2/raw/psqt_explains_100.txt; again: `python3 job2/analyse_lr.py` | NEW |`

## Suspicions, not proven

- PSQT explains only r = 0.35, so most of the delta comes from other terms. The shelter loop is the most
  likely structural contributor (it is clipped at the edges, so a king on the a-file sees two shelter files
  where a king on the h-file sees one plus a clipped one). **Not proven**: I did not disable individual
  terms and re-measure, because every term is compiled in and there is no option to switch shelter off.
- Whether any REAL bug hides in the file handling: a genuine fault would be an out-of-range file index, and
  `std::max(0, ...)`/`std::min(7, ...)` at `eval.cpp:252` guards that. Reading only, no test that shows a fault.

## What I did NOT do

- Did not disable individual eval terms to attribute the remaining delta (no options exist for it).
- Did not run a sanitizer build for job 2 (job 2 as specified does not ask for one).
- Did not compare at search depth (that is job 3).
- Did not test positions WITH castling rights under the left-right flip: the flip moves kings off the e-file,
  which invalidates castling rights, so those positions have no meaningful left-right comparison.

## What I am NOT sure about

- Whether the job's intent was to catch a real bug on this comparison. If so, the honest answer is that the
  comparison cannot catch one: it measures a property the engine does not and need not have. I wrote this
  plainly rather than reporting 745 "asymmetries" as if they were findings.

## Times

`stamps.txt` — every line is a `date -u`.

## Last command output

(pasted into `last_cmd.txt` at commit time)

## Last command output

```
$ git status --short
 M job2/stamps.txt
?? REPORT_job2.md
?? job2/__pycache__/
?? job2/analyse_lr.py
?? job2/controls.py
?? job2/last_cmd.txt
?? job2/lr_configs.py
?? job2/mirror_lr.py
?? job2/psqt_explains.py
?? job2/psqt_isolation.py
?? job2/raw/
?? job2/run_job2.log
?? job2/run_job2.sh
$ ls
check_S-F1
check_S-F2
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
job2
REPORT_check_S-F1.md
REPORT_check_S-F2.md
REPORT_job1.md
REPORT_job2.md
SEAT.txt
STATUS.md
$ ls job2
analyse_lr.py
controls.py
G_nocastle.fens
last_cmd.txt
lr_configs.py
mirror_lr.py
prediction.txt
psqt_explains.py
psqt_isolation.py
__pycache__
raw
R_nocastle.fens
run_job2.log
run_job2.sh
set_G.epd
stamps.txt
$ ls job2/raw
controls.txt
G_lr.meta
G_lr.summary
G_lr.tsv
lr_configs_80.txt
lr_configs_fullG.txt
psqt_explains_100.txt
psqt_isolation.txt
R_lr.meta
R_lr.summary
R_lr.tsv
```

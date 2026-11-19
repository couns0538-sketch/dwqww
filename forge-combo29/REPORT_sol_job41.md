# Sol — Job 41 wider-step follow-up

## Step 0. Known-answer pins

The unchanged GCC 14.2.0 Job 34 r15d binary passed all five fresh-process pins. Its defaults returned 312866 for `bench 11`, 862329 for `bench 13` and 4865609 for `go perft 5`. With PC20 and synthetic net768 it returned 882074 and 4275906 for the two benchmarks and recorded `NNUE v3 active` with checksum `30ab43b4ba5db5f3`. `nproc` returned 5. I used up to four single-threaded engines at once. [Raw r15d pins](sol/job41/pin-evidence/r15d.raw.txt) · [nproc](sol/job41/pin-evidence/nproc.txt)

## Baselines, known answer and control

Every run used PC20, active net768, Threads 1 and Hash 16. N2 used `go nodes 20000` on games 410001–410020. N1 used `go softnodes 2000` on games 400001–400020. Both new baseline files at each limit matched the Job 40 baseline at commit `d80e321` byte for byte. [Job 40 report](REPORT_sol_job40.md) · [N2 cmp](sol/job41/N2.cmp.tsv) · [N1 cmp](sol/job41/N1.cmp.tsv)

| Limit | BASE-a SHA-256 | BASE-b SHA-256 | Job 40 BASE-a SHA-256 | Gate |
| --- | --- | --- | --- | --- |
| N2 | `15e26c523131fd623aac7ff107afc034282bcbf21d8dea1df3bd1aa1f78071be` | `15e26c523131fd623aac7ff107afc034282bcbf21d8dea1df3bd1aa1f78071be` | `15e26c523131fd623aac7ff107afc034282bcbf21d8dea1df3bd1aa1f78071be` | PASS |
| N1 | `a54983d4d2f191be266ad57861ad7d5f54d8cbde437fcdabc5bdd2b3d4ca9807` | `a54983d4d2f191be266ad57861ad7d5f54d8cbde437fcdabc5bdd2b3d4ca9807` | `a54983d4d2f191be266ad57861ad7d5f54d8cbde437fcdabc5bdd2b3d4ca9807` | PASS |

N2 baseline recorded 20 games, 2,039 searches and 23,881,605 last-info nodes. [Baseline hash receipt](sol/job41/N2.baseline.tsv)

N1 baseline recorded 20 games, 2,423 searches and 9,781,064 last-info nodes. [Baseline hash receipt](sol/job41/N1.baseline.tsv)

**Known answer PASS.** With `EvalSwingMax=300` and EvalSwingMult at 0, all 20 N2 games matched BASE-a with 2,039 recorded searches. [Raw run](sol/job41/raw/N2/EvalSwingMax300)

**Control PASS.** `LmrQuietBase=101` changed 20 of 20 N2 games. First differing record line 1 was `410001 8 b3b4 13077` in BASE-a and `410001 8 b3b4 19024` in the control. [Raw run](sol/job41/raw/N2/LmrQuietBase101)

## Prediction and grade

I froze the empty N2 prediction in `88fa3b3` after the N2 gates. Job 40 had no NO CHANGE SEEN settings at N2, so there were zero predictions to grade. [Frozen prediction](sol/job41/prediction.json) · [UTC stamps](sol/job41/stamps.txt)

## Wider-step readings

Job 40 finished all 40 settings at each limit and classified all 40 as LIVE at each limit. The wider-step lists for N2 and N1 were empty. [Job 40 setting map](REPORT_sol_job40.md) · [Independent selection readback](sol/job41/independent.json)

| Limit | Eligible settings | Wider-step runs | FIRST CHANGE AT k STEPS | NO CHANGE SEEN UP TO 8 STEPS |
| --- | ---: | ---: | ---: | ---: |
| N2 | 0 | 0 | 0 | 0 |
| N1 | 0 | 0 | 0 | 0 |

## Facts

The six fresh runs retained every setup command and `readyok`. The independent parser checked the archived bytes, then replayed each recorded game to verify its seeded opening, legal moves and ending. [Raw run files](sol/job41/raw) · [Independent verifier](sol/job41/verify41.py) · [Readback](sol/job41/readback.txt)

## Suspicions

The wider-step schedule produced no observation about how far an untested parameter value can move before changing play.

## What this check cannot see

The PC's net (with it a search at 20,000 nodes reaches other depths than with net768), its build, positions these
40 games do not reach, two settings moved together (the tune moves all 40 at once), what a change does to strength.

## What I did not do

I ran the required fresh controls and baselines on the cloud. I made no tracked engine source changes and ran no trials on the owner’s PC.

## What I am not sure about

The tests do not measure whether the one-step changes in Job 40 increase or decrease playing strength.

## Precommit status and evidence inventory

```text
M  forge-combo29/NOTES_sol.md
A  forge-combo29/REPORT_sol_job41.md
A  forge-combo29/sol/job41/independent.json
A  forge-combo29/sol/job41/readback.txt
A  forge-combo29/sol/job41/run_gate41.sh
M  forge-combo29/sol/job41/stamps.txt
A  forge-combo29/sol/job41/verify41.py
forge-combo29/sol/job41:
N1.baseline.tsv
N1.cmp.tsv
N1.stage.out
N2.baseline.tsv
N2.cmp.tsv
N2.stage.out
independent.json
pin-evidence
prediction.json
raw
readback.txt
run_gate41.sh
stamps.txt
verify41.py

forge-combo29/sol/job41/pin-evidence:
cpu-max.txt
nproc.txt
r15d.raw.txt
step0.out

forge-combo29/sol/job41/raw:
N1
N2

forge-combo29/sol/job41/raw/N1:
BASE-a
BASE-a.driver.out
BASE-b
BASE-b.driver.out

forge-combo29/sol/job41/raw/N1/BASE-a:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job41/raw/N1/BASE-b:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job41/raw/N2:
BASE-a
BASE-a.driver.out
BASE-b
BASE-b.driver.out
EvalSwingMax300
EvalSwingMax300.driver.out
LmrQuietBase101
LmrQuietBase101.driver.out

forge-combo29/sol/job41/raw/N2/BASE-a:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job41/raw/N2/BASE-b:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job41/raw/N2/EvalSwingMax300:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job41/raw/N2/LmrQuietBase101:
records.txt
run.json
uci-setup.txt
```

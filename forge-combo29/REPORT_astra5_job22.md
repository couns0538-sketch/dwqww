# Astra5 job 22 — one process across a long self-play run

## 1. Step 0 passed on both builds

The unchanged r15d and kF executables passed all five fresh-process checks. Without setoptions, benches 11 and 13 returned 312,866 and 862,329 nodes, and perft 5 returned 4,865,609. With PC20 + synthetic net768, the benches returned 882,074 and 4,275,906. Both net-enabled transcripts report `NNUE v3 active` and checksum `30ab43b4ba5db5f3`. `nproc` returned 5. [Build and network identities](astra5/job22/build.txt) · [r15d checks](astra5/job22/step0/r15d/checks.txt) · [kF checks](astra5/job22/step0/kF/checks.txt)

## 2. K22 and C22 passed

Two separate r15d processes replayed games 700001–700010 at PC20. K22 produced 1,183 records, 0 NA and 4,863,663 summed nodes per process. Both files had SHA-256 `b85eb5f01afbbb12771b1a8cf5c579f3c6db3873fa0779f9fce94ca0c5b25a76` and `cmp` exited 0. [K22 comparison](astra5/job22/audit/K22/summary.txt)

Changing only LmrQuietBase from 93 to 60 changed the records in 10 of the 10 games. C22 had 1,193 records, 0 NA and 5,100,705 summed nodes, with SHA-256 `a5b3745a1a0f1e5c7e65754b17777f34c6ec2d4f02aa2d4969c85489f56280dc`. The two lines below are the first difference. [C22 opening and preceding moves](astra5/job22/audit/C22/first-difference.txt)

```text
K22  700001 8 g4f5 3823
C22  700001 8 g4f5 2293
```

## 3. Frozen predictions and grades

The prediction was pushed alone at 01:53:53Z. The first L1 game started at 01:53:56.752Z. [Frozen predictions](astra5/job22/prediction.txt) · [Prediction-only commit](https://github.com/couns0538-sketch/dwqww/commit/78f6ae390bbcc8b75d7128b8a2755291a010bd77) · [UTC checkpoints](astra5/job22/stamps.txt)

For L1 the forecast was IDENTICAL and the observation was IDENTICAL (hit). The L0 forecast for r15d was SAME and the observation was SAME (hit). The L0 forecast for kF was SAME and the observation was SAME (hit).

The intervals in parentheses are the forecast ranges, inclusive. Linux reports VmRSS in units labelled `kB`, each equal to one KiB (1,024 bytes).

- **L1 r15d** after game 1, 34,232 KiB (31,000–39,000, inside). After its last game, 34,764 KiB (32,000–45,000, inside).
- **L1 kF** after game 1, 34,004 KiB (31,000–41,000, inside). After its last game, 34,264 KiB (32,000–47,000, inside).
- **L0 r15d** after game 1, 34,240 KiB (31,000–39,000, inside). After its last game, 34,456 KiB (31,000–42,000, inside).
- **L0 kF** after game 1, 33,944 KiB (31,000–41,000, inside). After its last game, 34,000 KiB (31,000–44,000, inside).

## 4. Long process and fresh replay

Driver R used each game ID to seed up to eight random legal opening plies. One engine played both colors, using the full history with `go softnodes 2000`, PC20 + net768, Threads 1 and Hash 16 MiB. The first searched ply is numbered 8. Each record holds the game ID, ply, bestmove and final reported node count, or `NA` if unavailable. Games ended on a claimable result or the 300-ply cap. [Search and record driver](astra5/job22/driver/selfplay.py)

L1 used separate logical cores 1 (r15d) and 3 (kF). Both builds completed games 700001–705000 in order, reaching the 5,000-game target before the minute-40 cutoff.

| Run | Build | Games | Records | NA | Node sum | SHA-256 | Reading |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L1 | r15d | 5,000 | 579,956 | 0 | 2,409,009,543 | `fb1420546364b50aa244b1fb1c2465db8edce55b3907a927f56e06979ab75dcc` | [IDENTICAL](astra5/job22/audit/L1/cmp.txt) |
| L1 | kF | 5,000 | 579,956 | 0 | 2,409,009,543 | `fb1420546364b50aa244b1fb1c2465db8edce55b3907a927f56e06979ab75dcc` | [IDENTICAL](astra5/job22/audit/L1/cmp.txt) |
| L0 | r15d | 10 | 1,201 | 0 | 4,735,213 | `f00d1d83ea1d7c11d246275b8550954df48c80292f957aa79ea46cfe519b03e3` | [SAME](astra5/job22/audit/L0-r15d/cmp.txt) |
| L0 | kF | 10 | 1,201 | 0 | 4,735,213 | `f00d1d83ea1d7c11d246275b8550954df48c80292f957aa79ea46cfe519b03e3` | [SAME](astra5/job22/audit/L0-kF/cmp.txt) |

Each L0 replay used its build’s own last ten completed L1 game IDs, 704991–705000. The game receipts define the exact byte offsets. I independently joined those ten game slices in order and matched the result to that build’s archived `from-L1.txt` before comparing it with the fresh-process records. [r15d L1 tail](astra5/job22/L0-r15d/from-L1.txt) · [kF L1 tail](astra5/job22/L0-kF/from-L1.txt)

## 5. Resident memory

Each observation came from the engine’s own `/proc/<pid>/status` after a completed game. The units are KiB. A dash marks an ordinal beyond the length of that run. The PID and Linux process start tick stayed constant within each arm. L0 used a fresh process per build.

| Run | Build | PID | Game 1 | Game 1,000 | Game 2,000 | Game 3,000 | Game 4,000 | Last game (ordinal) | Last VmRSS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L1 | r15d | `121405` | 34,232 | 34,712 | 34,724 | 34,724 | 34,724 | 5,000 | 34,764 |
| L1 | kF | `121404` | 34,004 | 34,232 | 34,236 | 34,236 | 34,236 | 5,000 | 34,264 |
| L0 | r15d | `128866` | 34,240 | — | — | — | — | 10 | 34,456 |
| L0 | kF | `128865` | 33,944 | — | — | — | — | 10 | 34,000 |

From its first to last L1 observation, r15d changed by +532 KiB and kF by +260 KiB. These are endpoint changes in resident memory. [L1-r15d milestones](astra5/job22/L1-r15d/rss.tsv) · [L1-kF milestones](astra5/job22/L1-kF/rss.tsv) · [L0-r15d milestones](astra5/job22/L0-r15d/rss.tsv) · [L0-kF milestones](astra5/job22/L0-kF/rss.tsv)

At each completed 1,000-game milestone a second observer read VmRSS directly while the two workers waited. Both readings agreed for every checked process and milestone. [Independent live memory readings](astra5/job22/audit/process/stationary-proc.tsv)

## 6. Declared readings

**KEEPS.** L1 was IDENTICAL over 5,000 consecutive games. L0 was SAME for r15d and SAME for kF on the last ten games of that sequence.

> L1 reads IDENTICAL when the two record files are byte for byte equal; otherwise DIFFERS, with how many games differ, the first differing record with both lines, its game number and the moves before it. L0 reads SAME for a build when its records equal that build's L1 records for those games; otherwise CARRIES, with the first differing record. For r15d, CARRIES is a find about the PC's own engine (our source reading said SAME); for kF, CARRIES while r15d reads SAME is a find about kF. The job reads KEEPS when L1 is IDENTICAL and both L0 are SAME. The memory rows are description.

## Facts

The L1 comparison checked 579,956 r15d records against 579,956 kF records. The fresh replay compared each build with its own prior searches, using identical game seeds and a new process. The node totals include only numeric fields.

Three L1 openings ended in checkmate during the random prefix. Their game IDs and opening lengths were 700591 (7 plies), 701791 (8 plies), 704280 (4 plies). Both processes received `ucinewgame` and returned `readyok` for each of those games. They count toward the game totals and RSS observations, with zero searched-ply records.

[Source review of ucinewgame](astra5/job22/audit/process/reset-source.txt) · [Independent opening replay](astra5/job22/audit/process/terminal-opening-audit.txt) · [Live process identities](astra5/job22/audit/process/live-pid-identity.tsv) · [Independent memory totals](astra5/job22/archive/memory-milestones.tsv) · [Independent suffix and memory comparison](astra5/job22/archive/suffix-memory-check.txt)

## Suspicions

Resident memory can change when existing allocations first acquire physical pages. Samples from these processes alone cannot identify which allocations account for a change.

## What I did not do

The experiment did not instrument individual allocations, measure playing strength or run the PC’s full training pipeline.

**What this cannot see**, in the job’s words

> the PC's own build (clang 23 for Windows, its profile), its trained net, 16 processes at once, a whole round (about 7,800 games a worker; this plays 5,000), a round that starts in one process and goes on in another (the PC's early self-play), other node limits.

## What I am not sure about

Matching replay records establish the outcome for the last ten selected games. These runs cannot identify internal state that persisted without changing a recorded move or node count.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job22`.

```text
A  forge-combo29/REPORT_astra5_job22.md
M  forge-combo29/astra5/job22/stamps.txt
forge-combo29/astra5/job22:
C22
K22-1
K22-2
L0-kF
L0-r15d
L1-kF
L1-r15d
archive
audit
build.txt
driver
prediction.txt
stamps.txt
step0

forge-combo29/astra5/job22/C22:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job22/K22-1:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job22/K22-2:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job22/L0-kF:
archive.txt
from-L1.txt
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job22/L0-r15d:
archive.txt
from-L1.txt
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
sample-uci.txt

forge-combo29/astra5/job22/L1-kF:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.part0001.txt
raw-last.part0002.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
runner-checkpoint.txt
sample-uci.txt

forge-combo29/astra5/job22/L1-r15d:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-last-manifest.tsv
raw-last.part0001.txt
raw-last.part0002.txt
records-manifest.tsv
records.txt
rss-all.tsv
rss-source.txt
rss.tsv
run.log
runner-checkpoint.txt
sample-uci.txt

forge-combo29/astra5/job22/archive:
archive.py
compare_tail.py
memory-milestones.tsv
suffix-memory-check.txt

forge-combo29/astra5/job22/audit:
C22
K22
L0-cmp.txt
L0-controller.txt
L0-kF
L0-r15d
L1
audit.py
memory-prediction.tsv
memory.tsv
monitor.py
phase_check.py
process
reading.txt
stage-summary.tsv
tail.py
watch.py

forge-combo29/astra5/job22/audit/C22:
C22-controller.txt
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
live-first-difference.txt
rss.tsv
summary.txt
verified.txt

forge-combo29/astra5/job22/audit/K22:
K22-1-controller.txt
K22-2-controller.txt
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
rss.tsv
summary.txt
verified.txt

forge-combo29/astra5/job22/audit/L0-kF:
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
independent-from-L1.txt
rss.tsv
summary.txt
verified.txt

forge-combo29/astra5/job22/audit/L0-r15d:
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
independent-from-L1.txt
rss.tsv
summary.txt
verified.txt

forge-combo29/astra5/job22/audit/L1:
L1-barriers.tsv
L1-boundary-note.txt
L1-boundary.txt
arms.tsv
barriers.txt
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
process-L1-kF.txt
process-L1-r15d.txt
rss.tsv
summary.txt
verified.txt

forge-combo29/astra5/job22/audit/process:
audit.py
control-process-audit.tsv
fresh-tail-audit.txt
live-pid-identity.tsv
measurement-method.txt
memory-audit.tsv
observe-processes.py
process-audit.tsv
reset-source.txt
snapshot-proc.py
stationary-proc.tsv
terminal-opening-audit.txt

forge-combo29/astra5/job22/driver:
compare_stage.py
selfplay.py
stage.py

forge-combo29/astra5/job22/step0:
build.txt
identities.txt
kF
pc20.txt
r15d

forge-combo29/astra5/job22/step0/kF:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt

forge-combo29/astra5/job22/step0/r15d:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
```

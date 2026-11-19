# Astra5 job 20 — search-label identity at Hash 16 and Hash 1

## 1. Step 0 passed on both builds

The unchanged job 16 binaries passed all five known answers in separate fresh processes. `nproc` returned 5. The net-enabled checks reported `NNUE v3 active` with checksum `30ab43b4ba5db5f3`. [Executable and network identities](astra5/job20/step0/identities.txt)

| Options | Command | r15d nodes | kF nodes |
| --- | --- | --- | --- |
| No setoptions | `bench 11` | 312,866 | 312,866 |
| No setoptions | `bench 13` | 862,329 | 862,329 |
| No setoptions | `go perft 5` | 4,865,609 | 4,865,609 |
| PC20 + net768 | `bench 11` | 882,074 | 882,074 |
| PC20 + net768 | `bench 13` | 4,275,906 | 4,275,906 |

| File | SHA-256 |
| --- | --- |
| r15d | `9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671` |
| kF | `c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb` |
| Synthetic net768 | `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7` |

[r15d gate receipts](astra5/job20/step0/r15d/checks.txt) · [kF gate receipts](astra5/job20/step0/kF/checks.txt)

## 2. K20 and C20 passed

On r15d, the two K20 repeats used PC20, Hash 16 MiB and `go softnodes 2000` on games 600001–600020. The complete normalized record streams were byte-identical (`cmp` exit 0). Every one of K20’s 2,330 records contained a score, including 69 with `score mate`. [K20 audit](astra5/job20/audit/K20/summary.txt)

Changing only `LmrQuietBase` from 93 to 60 changed the records in 20 of the 20 games (`cmp` exit 1). The first differing record was game 600001, ply 8. Its first differing field was `depth`. Both returned `h1g1`, while the score changed from `cp 501` to `cp 421`. [C20 opening, preceding moves and differing fields](astra5/job20/audit/C20/first-difference.txt)

| Arm | LmrQuietBase | Games | Records | NA | With score | Missing score | Score mate | Mate + / 0 / − | Record SHA-256 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| K20-1 | 93 | 20 | 2,330 | 0 | 2,330 | 0 | 69 | 38 / 0 / 31 | `8f1c71a4b7087d2ca7cde695180ee10c709f92af2dfc7084bdc95308bb072d5c` |
| K20-2 | 93 | 20 | 2,330 | 0 | 2,330 | 0 | 69 | 38 / 0 / 31 | `8f1c71a4b7087d2ca7cde695180ee10c709f92af2dfc7084bdc95308bb072d5c` |
| C20 | 60 | 20 | 2,480 | 0 | 2,480 | 0 | 57 | 30 / 0 / 27 | `aed2c84f1fbffee66c01d335b2e60dea9c0894ac0588148ec7ee6fb332458e25` |

```text
K20  600001 8 h1g1 info depth 8 seldepth 10 score cp 501 nodes 2030 hashfull 0 pv h1g1 d8b6 a1b1 d7d6 f1d3 h6f5 b2b4
C20  600001 8 h1g1 info depth 9 seldepth 15 score cp 421 nodes 3385 hashfull 0 pv h1g1 d8a5 a1b1 b7b5 f1c4 d7d6 c4b3 e8d7 f3e5 d7e8
```

## 3. Frozen prediction and grades

The prediction was pushed alone at 01:10:02Z after C20. The first P1 game started at 01:10:09.518Z. The forecast counts a game as different if any retained field changes at any played ply. [Frozen prediction](astra5/job20/prediction.txt) · [Prediction-only commit](https://github.com/couns0538-sketch/dwqww/commit/134796de3c6cf64b85c83468d38e4bc7cdc92da7) · [UTC checkpoints](astra5/job20/stamps.txt)

| Run | Scheduled games | Point estimate | Inclusive range | Observed differing games | Grade |
| --- | --- | --- | --- | --- | --- |
| P1 | 3,000 | 0 | 0–3 | 0 | Point hit, inside range |
| P2 | 500 | 0 | 0–2 | 0 | Point hit, inside range |
| P3 | 100 | 0 | 0–1 | 0 | Point hit, inside range |

## 4. P1, P2 and P3

**KEEPS.** P1, P2 and P3 each had byte-identical move and normalized last-info records in every scheduled game. This includes the one-mebibyte hash table in P2.

Driver R seeded Python’s random generator with the game ID and selected eight random legal plies from the starting position. One persistent engine per arm then played both colors using the complete move history. The first searched ply is numbered 8. Games ended under the draw-claim rule or the 300-ply limit. Both builds used PC20, Threads 1 and synthetic net768. [Game and record driver](astra5/job20/driver/selfplay.py)

For each bestmove the driver selected the last preceding line beginning with `info depth` from that search. It removed the `time` and `nps` pairs and retained the remaining fields in printed order. `NA` marks a search with no such line. The mate split counts positive, zero and negative printed distances. Shared figures apply to both builds, and paired figures use r15d / kF order.

| Run | Scheduled game IDs | Go command | Hash MiB | Games | Records | NA | Missing score | Score mate | Mate + / 0 / − | Whole-file SHA-256 | cmp exit | Differing games | Reading |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [P1](astra5/job20/audit/P1/cmp.txt) | 600101–603100 | `go softnodes 2000` | 16 | 3,000 | 347,274 | 1 | 1 | 10,701 | 5,855 / 0 / 4,846 | `3b574d64f6d93dc290c81d45716a16445880226d60ef677b5ff7abd440d43a87` | 0 | 0 | IDENTICAL |
| [P2](astra5/job20/audit/P2/cmp.txt) | 610001–610500 | `go softnodes 2000` | 1 | 500 | 59,671 | 0 | 0 | 1,817 | 997 / 0 / 820 | `b77c26c120ac62a3ed69402aeb202f0c06d8ad2791e02d10b2f1b4cfb2372357` | 0 | 0 | IDENTICAL |
| [P3](astra5/job20/audit/P3/cmp.txt) | 620001–620100 | `go nodes 20000` | 16 | 100 | 9,584 | 0 | 0 | 593 | 319 / 0 / 274 | `f13bc3e19483cd557b3f21bf9bd401e9f81db6e06a75a75025aab94f6a2f40c0` | 0 | 0 | IDENTICAL |

The SHA-256 values cover the complete record streams. For a split arm, concatenating the numbered parts in order recreates the stream used by `cmp`. The companion raw-label manifests cover the selected info lines before timing fields were removed. P1 [r15d manifest](astra5/job20/P1-r15d/records-manifest.tsv) · [kF manifest](astra5/job20/P1-kF/records-manifest.tsv) · P2 [r15d manifest](astra5/job20/P2-r15d/records-manifest.tsv) · [kF manifest](astra5/job20/P2-kF/records-manifest.tsv) · P3 [r15d manifest](astra5/job20/P3-r15d/records-manifest.tsv) · [kF manifest](astra5/job20/P3-kF/records-manifest.tsv)

## Facts

Each build completed 3,600 measured games and produced 416,529 searched-ply records. 403,417 carried a centipawn score and 13,111 a mate score. The remaining record had no qualifying info line and no score.

On P1 game 601580, ply 84, White had 29 legal moves. Both engines printed `info string softnodes nodes 8000` followed by `bestmove g3g4`. Neither emitted an `info depth` line for that search. Both streams therefore contain `601580 84 g3g4 NA`. [Full UCI replies and position replay](astra5/job20/audit/protocol/shared-na.txt)

The full-stream comparison covers the reported depth, selective depth, score type and value, node count, hash occupancy and every printed move in the principal variation. The saved UCI sample shows which line supplied the label when a separate softnodes diagnostic followed it. [Sample raw UCI searches](astra5/job20/K20-1/sample-uci.txt)

## Suspicions

A difference internal to the transposition table or evaluation could leave the printed fields identical. These records expose only differences that reach a retained field or the bestmove.

## What I did not do

This job recorded the engine’s labels. It included no training run or playing-strength match.

**What this cannot see**, in the job’s words

> the PC's engine build (clang 23 for Windows, its profile), its trained nets (net768 is made up), the PC's own record format (it reads the same info line), more than one thread.

## What I am not sure about

The tested openings, node limits and net establish what the two binaries printed on this sample. They do not establish whether all future self-play labels will agree.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job20`.

```text
A  forge-combo29/REPORT_astra5_job20.md
M  forge-combo29/astra5/job20/stamps.txt
forge-combo29/astra5/job20:
C20
K20-1
K20-2
P1-kF
P1-r15d
P2-kF
P2-r15d
P3-kF
P3-r15d
archive
audit
driver
prediction.txt
stamps.txt
step0

forge-combo29/astra5/job20/C20:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-labels-manifest.tsv
raw-labels.txt
records-manifest.tsv
records.txt
run.log
sample-uci.txt

forge-combo29/astra5/job20/K20-1:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-labels-manifest.tsv
raw-labels.txt
records-manifest.tsv
records.txt
run.log
sample-uci.txt

forge-combo29/astra5/job20/K20-2:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-labels-manifest.tsv
raw-labels.txt
records-manifest.tsv
records.txt
run.log
sample-uci.txt

forge-combo29/astra5/job20/P1-kF:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-labels-manifest.tsv
raw-labels.part0001.txt
raw-labels.part0002.txt
raw-labels.part0003.txt
raw-labels.part0004.txt
records-manifest.tsv
records.part0001.txt
records.part0002.txt
records.part0003.txt
run.log
runner-checkpoint.txt
sample-uci.txt

forge-combo29/astra5/job20/P1-r15d:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-labels-manifest.tsv
raw-labels.part0001.txt
raw-labels.part0002.txt
raw-labels.part0003.txt
raw-labels.part0004.txt
records-manifest.tsv
records.part0001.txt
records.part0002.txt
records.part0003.txt
run.log
runner-checkpoint.txt
sample-uci.txt

forge-combo29/astra5/job20/P2-kF:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-labels-manifest.tsv
raw-labels.txt
records-manifest.tsv
records.txt
run.log
runner-checkpoint.txt
sample-uci.txt

forge-combo29/astra5/job20/P2-r15d:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-labels-manifest.tsv
raw-labels.txt
records-manifest.tsv
records.txt
run.log
runner-checkpoint.txt
sample-uci.txt

forge-combo29/astra5/job20/P3-kF:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-labels-manifest.tsv
raw-labels.txt
records-manifest.tsv
records.txt
run.log
runner-checkpoint.txt
sample-uci.txt

forge-combo29/astra5/job20/P3-r15d:
archive.txt
games.tsv
no-info.tsv
openings.tsv
raw-labels-manifest.tsv
raw-labels.txt
records-manifest.tsv
records.txt
run.log
runner-checkpoint.txt
sample-uci.txt

forge-combo29/astra5/job20/archive:
archive.py

forge-combo29/astra5/job20/audit:
C20
K20
P1
P2
P3
audit.py
info-source-audit.txt
monitor.py
parser-test.txt
protocol
reading.txt
stage-order.tsv
stage-summary.tsv

forge-combo29/astra5/job20/audit/C20:
C20-controller.txt
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
live-first-difference.txt
summary.txt
verified.txt

forge-combo29/astra5/job20/audit/K20:
K20-1-controller.txt
K20-2-controller.txt
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job20/audit/P1:
P1-controller.txt
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job20/audit/P2:
P2-controller.txt
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job20/audit/P3:
P3-controller.txt
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt
verified.txt

forge-combo29/astra5/job20/audit/protocol:
all-records-audit.tsv
audit-sampled-dialogues.py
fixture-sources.txt
info-source-audit.txt
label-fixtures.json
parser-audit.txt
sampled-audit.tsv
shared-na.txt
summarize-shared-na.py
test-runner-parser.py
watch-comparisons.py

forge-combo29/astra5/job20/driver:
compare_stage.py
selfplay.py
stage.py

forge-combo29/astra5/job20/step0:
identities.txt
kF
pc20.txt
r15d

forge-combo29/astra5/job20/step0/kF:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt

forge-combo29/astra5/job20/step0/r15d:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
```

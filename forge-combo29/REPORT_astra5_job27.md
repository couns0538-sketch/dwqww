# Job 27 · Three Forge clock settings at 100 nodes per node-ms

## 1. Step 0 passed

The host reported `nproc 5`. The Job 26 binary had SHA-256 `9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3`. Five fresh processes reproduced 312,866 and 862,329 nodes at default bench depths 11 and 13, 4,865,609 leaves at perft depth 5, and 882,074 and 4,275,906 bench nodes under PC20 with net768. A fresh A0 replay at NodeClock 1000 reproduced the Job 26 row signature `424d931234dd3ff9` and total charge **98,026 node-ms**. [Build and host](astra5/job27/build.txt) · [Five pins](astra5/job27/step0/nc/checks.txt) · [A0 replay](astra5/job27/step0/A0/summary.txt)

The new rows.txt, searches.tsv, over.tsv and summary.txt equal the Job 26 A0 files byte for byte. [Cross-job byte comparisons](astra5/job27/step0/A0/job26-compare.txt)

## 2. Controls against the PC

Each row covers the first 20 searches from the starting position. The hash covers each ply number, stopped-node count and best move, with one space between fields and one LF after each row. [Six comparisons and first-three-row checks](astra5/job27/controls/K27/comparison.tsv)

| Pair | A switch | A's color | Measured SHA prefix | PC SHA prefix | Measured ΣN | PC ΣN |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | TmFinishIteration | White | `f49482fe2b9738aa` | `f49482fe2b9738aa` | 470,764 | 470,764 |
| 1 | TmFinishIteration | Black | `f0130049ccd2829f` | `f0130049ccd2829f` | 592,206 | 592,206 |
| 2 | TmNodeShare | White | `965681ae07f6c314` | `965681ae07f6c314` | 539,887 | 539,887 |
| 2 | TmNodeShare | Black | `749f902e91070fc2` | `749f902e91070fc2` | 507,873 | 507,873 |
| 3 | Both | White | `93caf8323c20a6ea` | `93caf8323c20a6ea` | 529,836 | 529,836 |
| 3 | Both | Black | `6d5378c21381a5a2` | `6d5378c21381a5a2` | 604,702 | 604,702 |

K27 passed all six move-and-node checks. In pair 1 with A as White, White had 4,434 node-ms after ply 19 and Black had 4,070 after ply 20, both equal to the PC. The two runners’ draw-claim rules can diverge later. [Clock checks](astra5/job27/controls/K27/gate.json)

C27 passed. A used NodeClock 200, B used 100, and the runner charged both players `N // 100`. The first 20 rows had SHA prefix `53c493968cc6852a` and 653,020 nodes. The corresponding K27 prefix was `f49482fe2b9738aa`. [Changed-clock control](astra5/job27/controls/C27/comparison.tsv)

In the C27 control, A lost game 1 on ply 61. The 23,292-node search cost 232 node-ms against a clock of 218. This control is excluded from all three match scores. [Clock receipt](astra5/job27/controls/C27/g0001/searches.tsv)

## 3. Frozen prediction

Commit `bd8e3a22094d` froze the predictions after the controls and before the first match game. [Frozen prediction](astra5/job27/prediction.txt) · [Step chronology](astra5/job27/stamps.txt)

| Quantity | Prediction | Observed | Grade |
| --- | --- | --- | --- |
| M1 Elo | -35 to 5 | -5.60 | Inside |
| M1 reading | B BETTER | LEVEL | Miss |
| M2 Elo | -20 to 20 | +5.20 | Inside |
| M2 reading | LEVEL | LEVEL | Correct |
| M3 Elo | -30 to 15 | -5.20 | Inside |
| M3 reading | LEVEL | LEVEL | Correct |
| Time losses across counted matches | 0 to 6 | 0 | Inside |
| Complete common blocks by minute 45 | 7 to 9 | 9 | Inside |

## 4. The three matches

Each opening contributed two color-reversed games per match. A enabled the switch in the table. B kept both switches at their defaults. The five bins count openings on which A scored 0, ½, 1, 1½ or 2 points out of two. Elo and its 95% interval use the Job 26 paired calculation. [Independent score and clock totals](astra5/job27/audit/final/independent.json)

| Match | A switch | Pairs | A W–L–D | Pentanomial | A Elo | 95% interval | Time losses | Mean used A / B | A searches with hold / total | Mean end clock A / B | Peak simultaneous games in this arm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | TmFinishIteration | 434 | 150–164–554 | 8 / 106 / 220 / 92 / 8 | -5.60 | [-18.30, +7.09] | 0 | 136.62 / 146.42 | 20,981 / 53,232 | 1,301.07 / 700.69 | 4 |
| M2 | TmNodeShare | 434 | 172–159–537 | 11 / 90 / 222 / 97 / 14 | +5.20 | [-8.09, +18.49] | 0 | 143.68 / 147.03 | — | 920.51 / 719.02 | 4 |
| M3 | Both | 434 | 148–161–559 | 15 / 96 / 220 / 93 / 10 | -5.20 | [-18.54, +8.13] | 0 | 132.84 / 146.18 | 20,054 / 53,289 | 1,528.38 / 710.73 | 4 |

Mean used and end clocks are in node-ms. A hold counts once per search containing at least one `TmFinishIteration hold` line. A completed search spends its final N divided by 100, rounded down. The runner started both clocks at 6,000 and awarded 60 after each move that fit the clock.

| Independently replayed ending | M1 | M2 | M3 |
| --- | --- | --- | --- |
| Checkmate | 314 | 331 | 309 |
| Stalemate | 2 | 1 | 1 |
| Insufficient material | 45 | 39 | 43 |
| Claimable threefold repetition | 505 | 489 | 510 |
| Claimable fifty-move rule | 2 | 8 | 5 |
| Time | 0 | 0 | 0 |
| 600-ply cap | 0 | 0 | 0 |

**TIME LOSSES** 0 in the counted matches.

## 5. Declared readings

**M1 LEVEL** · **M2 LEVEL** · **M3 LEVEL**. A BETTER requires a lower bound above zero. B BETTER requires an upper bound below zero. Every interval that includes zero reads LEVEL.

**M1 READS OTHERWISE** — M1 [-18.30, +7.09] Elo · PC [−23.5, −5.4] Elo. [PC trained-net match](astra5/job27/pc-reference.txt)

## Facts

All three matches used the same ordered 434-opening list. It contains the 200 positions of set O followed by 234 positions from the Job 24 book. The input check found 0 duplicate book rows to omit. The common score covers 9 of 9 blocks, blocks 1–9 and openings 1–434. 9 common blocks finished by minute 45. The runner exhausted L27. [Opening order and exclusions](astra5/job27/input/openings-provenance.txt) · [Per-block eligibility and timing](astra5/job27/audit/final/stages-independent.tsv)

The runner completed each block in M1, M2, M3 order on the same openings before advancing. The controls ran one game at a time. In matches, up to four games ran side by side on a host with five available CPUs. The operating system placed the processes. Each game used two fresh one-thread processes sharing that game’s turn, so only one color searched at a time. Arms ran one after another. [Control configuration](astra5/job27/controls/K27/inputs.json) · [Match CPU allocation](astra5/job27/matches/run.json)

The independent reader replayed 2,604 counted games with python-chess, checking move legality, both clocks and the terminal position. A charge exceeding the mover’s remaining clock lost on time. A game also ended at mate, stalemate, insufficient material, claimable threefold repetition or 50 moves, or the 600-ply cap. [Replayed scores, endings and clock balances](astra5/job27/audit/final/independent.json)

A separate recount from the published game and search rows reproduced all three pentanomial intervals and the clock totals. [Compact-table recount](astra5/job27/crosscheck/recount.txt) · [Two independent replays](astra5/job27/audit/compact-replay.txt) · [End-of-run receipt](astra5/job27/matches/schedule-end.json)

## Suspicions

In M1 the finish rule returned a completed iteration early in 20,981 of 53,232 A searches (39.4%). A spent 9.80 node-ms less per search than B on average. A hold can leave time for a later position. The aggregate spending difference also reflects which positions and clock balances the two settings reached. [Search totals](astra5/job27/audit/final/independent.json)

## What I did not do

The assignment sets the following limits.

> the PC's net and build (the built-in evaluation plays here); the wall clock (its overhead, the system timer); NodeClock values other than 100; whether a switch helps when a move gets ten times the nodes; more than one thread; time controls other than 6000 + 60; a difference smaller than the interval the played pairs give.

## What I am not sure about

The six start-position checks establish agreement through the first 20 searches under the common built-in evaluation. The PC’s strength match also changes the evaluation, settings and opening sample. These measurements cannot attribute a difference between the two strength estimates to one of those factors or identify which individual hold changed a result. [PC match conditions](astra5/job27/pc-reference.txt) · [Local paired estimates](astra5/job27/audit/final/independent.json)

## Pre-commit working tree and evidence files

```text
$ git status --short && ls -R forge-combo29/astra5/job27
 A forge-combo29/REPORT_astra5_job27.md
M  forge-combo29/astra5/job27/stamps.txt
forge-combo29/astra5/job27:
audit
build.txt
controls
cpu-use.txt
crosscheck
driver
input
matches
pc-reference.txt
prediction.txt
stamps.txt
step0

forge-combo29/astra5/job27/audit:
C27-independent.json
C27-independent.tsv
K27-independent.json
K27-independent.tsv
L27-independent.txt
check_L27.py
checkpoints
compact-replay.txt
compact27.py
final
final-checks.txt
gates27.py
method27.txt
replay27.py
score27.py
stage-summaries
stage27.py
stats_seed.py

forge-combo29/astra5/job27/audit/checkpoints:
common-01.json
common-02.json
common-03.json
common-04.json
common-05.json
common-06.json
common-07.json
common-08.json
common-09.json

forge-combo29/astra5/job27/audit/final:
M1-pairs.tsv
M2-pairs.tsv
M3-pairs.tsv
blocks-independent.tsv
independent.json
stages-independent.tsv
time-losses.tsv

forge-combo29/astra5/job27/audit/stage-summaries:
block001
block002
block003
block004
block005
block006
block007
block008
block009

forge-combo29/astra5/job27/audit/stage-summaries/block001:
M1.json
M2.json
M3.json

forge-combo29/astra5/job27/audit/stage-summaries/block002:
M1.json
M2.json
M3.json

forge-combo29/astra5/job27/audit/stage-summaries/block003:
M1.json
M2.json
M3.json

forge-combo29/astra5/job27/audit/stage-summaries/block004:
M1.json
M2.json
M3.json

forge-combo29/astra5/job27/audit/stage-summaries/block005:
M1.json
M2.json
M3.json

forge-combo29/astra5/job27/audit/stage-summaries/block006:
M1.json
M2.json
M3.json

forge-combo29/astra5/job27/audit/stage-summaries/block007:
M1.json
M2.json
M3.json

forge-combo29/astra5/job27/audit/stage-summaries/block008:
M1.json
M2.json
M3.json

forge-combo29/astra5/job27/audit/stage-summaries/block009:
M1.json
M2.json
M3.json

forge-combo29/astra5/job27/controls:
C27
K27

forge-combo29/astra5/job27/controls/C27:
comparison.tsv
controller.log
first20-g0001.txt
g0001
games.tsv
gate.json
inputs.json

forge-combo29/astra5/job27/controls/C27/g0001:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job27/controls/K27:
comparison.tsv
controller.log
first20-g0001.txt
first20-g0002.txt
first20-g0003.txt
first20-g0004.txt
first20-g0005.txt
first20-g0006.txt
g0001
g0002
g0003
g0004
g0005
g0006
games.tsv
gate.json
inputs.json

forge-combo29/astra5/job27/controls/K27/g0001:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job27/controls/K27/g0002:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job27/controls/K27/g0003:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job27/controls/K27/g0004:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job27/controls/K27/g0005:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job27/controls/K27/g0006:
engines.json
opening.txt
result.tsv
searches.tsv
wire.txt

forge-combo29/astra5/job27/crosscheck:
flag-and-equality.tsv
input-sha256.tsv
recount.py
recount.txt

forge-combo29/astra5/job27/driver:
controls27.py
game27.py
holds27.py
pack_arm27.py
schedule27.py

forge-combo29/astra5/job27/input:
make_L27.py
omitted.tsv
openings-provenance.txt

forge-combo29/astra5/job27/matches:
block001
block002
block003
block004
block005
block006
block007
block008
block009
events.jsonl
run.json
schedule-end.json
scheduler.log

forge-combo29/astra5/job27/matches/block001:
M1
M2
M3
receipt.json

forge-combo29/astra5/job27/matches/block001/M1:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block001/M1/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block001/M2:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block001/M2/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block001/M3:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block001/M3/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block002:
M1
M2
M3
receipt.json

forge-combo29/astra5/job27/matches/block002/M1:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block002/M1/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block002/M2:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block002/M2/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block002/M3:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block002/M3/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block003:
M1
M2
M3
receipt.json

forge-combo29/astra5/job27/matches/block003/M1:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block003/M1/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block003/M2:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block003/M2/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block003/M3:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block003/M3/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block004:
M1
M2
M3
receipt.json

forge-combo29/astra5/job27/matches/block004/M1:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block004/M1/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block004/M2:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block004/M2/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block004/M3:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block004/M3/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block005:
M1
M2
M3
receipt.json

forge-combo29/astra5/job27/matches/block005/M1:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block005/M1/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block005/M2:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block005/M2/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block005/M3:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block005/M3/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block006:
M1
M2
M3
receipt.json

forge-combo29/astra5/job27/matches/block006/M1:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block006/M1/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block006/M2:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block006/M2/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block006/M3:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block006/M3/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block007:
M1
M2
M3
receipt.json

forge-combo29/astra5/job27/matches/block007/M1:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block007/M1/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block007/M2:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block007/M2/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block007/M3:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block007/M3/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block008:
M1
M2
M3
receipt.json

forge-combo29/astra5/job27/matches/block008/M1:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block008/M1/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block008/M2:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block008/M2/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block008/M3:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block008/M3/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block009:
M1
M2
M3
receipt.json

forge-combo29/astra5/job27/matches/block009/M1:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block009/M1/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block009/M2:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block009/M2/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/matches/block009/M3:
engines.tsv
games.tsv
hold-evidence
interruptions.txt
openings.tsv
option-profiles.json
receipt.json
searches.tsv
unfinished-searches.tsv
wire-samples.txt
wire-sha256.tsv

forge-combo29/astra5/job27/matches/block009/M3/hold-evidence:
holds.tsv
receipt.json

forge-combo29/astra5/job27/step0:
A0
nc

forge-combo29/astra5/job27/step0/A0:
job26-compare.txt
over.tsv
rows.txt
run.meta
searches.tsv
summary.txt
uci.log

forge-combo29/astra5/job27/step0/nc:
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
```

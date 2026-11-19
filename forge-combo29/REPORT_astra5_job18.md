# Astra5 job 18 — kF search records under five tuning settings

## 1. Step 0 — both builds passed

The unchanged job 16 executables matched all five known answers in separate processes. `nproc` returned 5. The net-enabled checks reported `NNUE v3 active` and checksum `30ab43b4ba5db5f3`. [Binary and network identities](astra5/job18/step0/identities.txt)

| Build | Executable SHA-256 |
| --- | --- |
| r15d | `9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671` |
| kF | `c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb` |

| Options | Command | r15d nodes | kF nodes |
| --- | --- | --- | --- |
| defaults | `bench 11` | 312,866 | 312,866 |
| defaults | `bench 13` | 862,329 | 862,329 |
| defaults | `go perft 5` | 4,865,609 | 4,865,609 |
| PC20 + net768 | `bench 11` | 882,074 | 882,074 |
| PC20 + net768 | `bench 13` | 4,275,906 | 4,275,906 |

[r15d gate receipts](astra5/job18/step0/r15d/checks.txt) · [kF gate receipts](astra5/job18/step0/kF/checks.txt)

Both executables printed these same 40 UCI option lines. They are shown once, in the assignment’s tuning order. [r15d UCI transcript](astra5/job18/step0/r15d/uci-raw.txt) · [kF UCI transcript](astra5/job18/step0/kF/uci-raw.txt)

```text
option name DrawJitter type spin default 0 min 0 max 8
option name LmrQuietBase type spin default 85 min 0 max 300
option name LmrQuietDivisor type spin default 220 min 100 max 500
option name LmrNoisyBase type spin default 10 min 0 max 300
option name LmrNoisyDivisor type spin default 340 min 100 max 800
option name NullMoveMinDepth type spin default 3 min 1 max 10
option name NullMoveBase type spin default 3 min 1 max 6
option name NullMoveDepthDivisor type spin default 3 min 1 max 10
option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
option name RfpDepth type spin default 8 min 0 max 15
option name RfpMargin type spin default 72 min 10 max 300
option name RfpImproving type spin default 40 min 0 max 200
option name RazorDepth type spin default 2 min 0 max 6
option name RazorBase type spin default 150 min 0 max 1000
option name RazorMultiplier type spin default 350 min 0 max 1000
option name FutilityDepth type spin default 7 min 0 max 15
option name FutilityBase type spin default 100 min 0 max 500
option name FutilityMultiplier type spin default 110 min 0 max 500
option name LmpBase type spin default 4 min 0 max 20
option name HistoryPruneDepth type spin default 3 min 0 max 10
option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
option name SeeQuietMultiplier type spin default 24 min 0 max 200
option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
option name SingularDepth type spin default 7 min 2 max 20
option name SingularMargin type spin default 2 min 0 max 10
option name IirDepth type spin default 4 min 1 max 20
option name ProbcutDepth type spin default 5 min 1 max 20
option name ProbcutMargin type spin default 180 min 0 max 1000
option name QsFutilityMargin type spin default 160 min 0 max 1000
option name AspirationDelta type spin default 18 min 4 max 200
option name HistoryBonusQuadratic type spin default 20 min 0 max 100
option name HistoryBonusLinear type spin default 48 min 0 max 500
option name HistoryBonusMax type spin default 2048 min 100 max 10000
option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
option name CheckExtensionDepth type spin default 2 min 1 max 30
option name LmrCutoffThreshold type spin default 3 min 0 max 20
option name MaterialCorrectionWeight type spin default 100 min 0 max 300
option name CaptureFutilityBase type spin default 0 min 0 max 1000
option name FailLowContinuationBonus type spin default 0 min 0 max 300
option name EvalSwingMult type spin default 0 min 0 max 64
```

## 2. The five sets and the K18/C18 controls

I reproduced all 200 setting values by drawing one integer from −3 through +3 for each option, in order, from Python’s seeded generator for each set. Each draw was multiplied by its step size, added to the start and clipped to the permitted range. Seeds 9001–9005 correspond to sets 1–5. Both builds kept the remaining PC20 options, net768, Threads 1 and Hash 16 MiB fixed. [All five frozen setting columns](astra5/job18/sets.txt) · [Settings commit](https://github.com/couns0538-sketch/dwqww/commit/b7525f1677eedb8085ab4a094f3a303fc75e8076)

The shared settings file had SHA-256 `8b9f11a1ca4f209b57cbc59ae6fc4c2bd6a09a54ffd4ce5af265fa87fbbede81`. Each binary accepted all 40 options in each of the five handshakes. [Independent settings and UCI acceptance check](astra5/job18/settings/sets-audit.txt)

Two r15d repeats using set 1 and Driver R produced identical records on games 400001–400010. On the same games, set 2 changed the records in 10 of 10. The first difference occurred on the first engine move in game 400001, recorded at zero-based ply 8. [K18 audit](astra5/job18/audit/K18/summary.txt) · [C18 audit](astra5/job18/audit/C18/summary.txt)

| Arm | Set | Games | Records | NA | Sum of numeric nodes | Record SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| K18-1 | 1 | 10 | 1,045 | 0 | 4,304,733 | `698cc5f020569139245bacd12ce654a99039ec881f927feb86f9b8b9c1b467b5` |
| K18-2 | 1 | 10 | 1,045 | 0 | 4,304,733 | `698cc5f020569139245bacd12ce654a99039ec881f927feb86f9b8b9c1b467b5` |
| C18 | 2 | 10 | 1,004 | 0 | 3,746,258 | `3a437b854119e094e283a68f0df7496121beafba655ee9451f77d92f5f4a06d8` |

```text
K18  400001 8 h2h3 4631
C18  400001 8 b2b4 2795
```

The settings freeze was stamped 00:34:36Z, before the first control game at 00:35:27.611Z. [UTC step times](astra5/job18/stamps.txt)

## 3. Frozen prediction, graded by set

The forecast gave each R and F comparison a zero-game point estimate and a range of 0–1 differing games. The combined forecast for each set was zero with a range of 0–2. It predicted zero NA entries for each build in each driver. The table grades the observed count against its own point and inclusive range. [Frozen forecast](astra5/job18/prediction.txt) · [Prediction-only commit](https://github.com/couns0538-sketch/dwqww/commit/6f6670c4e67515eeb106303e68bf0f420430ab9a)

The prediction-only commit was stamped 00:36:49Z. The first counted game began at 00:36:53.061Z.

| Set | R differing games | F differing games | Total differing games | R NA r15d/kF | F NA r15d/kF | Total NA r15d/kF |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 (point hit, inside) | 0 (point hit, inside) | 0 (point hit, inside) | 0/0 (hit) | 0/0 (hit) | 0/0 (hit) |
| 2 | 0 (point hit, inside) | 0 (point hit, inside) | 0 (point hit, inside) | 0/0 (hit) | 0/0 (hit) | 0/0 (hit) |
| 3 | 0 (point hit, inside) | 0 (point hit, inside) | 0 (point hit, inside) | 0/0 (hit) | 0/0 (hit) | 0/0 (hit) |
| 4 | 0 (point hit, inside) | 0 (point hit, inside) | 0 (point hit, inside) | 0/0 (hit) | 0/0 (hit) | 0/0 (hit) |
| 5 | 0 (point hit, inside) | 0 (point hit, inside) | 0 (point hit, inside) | 0/0 (hit) | 0/0 (hit) | 0/0 (hit) |

## 4. R1 through F5 — whole-game comparisons

Each scheduled R arm used 100 numbered games with one persistent engine playing both sides at `go softnodes 2000`. Game IDs start at 400001 for R1 and increase by 1000 for each subsequent set. The game ID seeded Python’s selection of eight legal opening plies from the start position. For each searched ply the driver supplied the full move history after `position startpos`. The first searched record has zero-based ply index 8.

Each scheduled F arm used 30 book lines with `go nodes 20000`. F1 started at book line 3641. Subsequent sets used consecutive blocks of 30. Two fixed slots each retained a White and a Black engine, and each engine searched its own turns. F records number the first played ply after the opening FEN as 1. Games used the draw-claim rule and a 300-ply ceiling, including R’s opening moves. [Engine driver](astra5/job18/driver/selfplay.py)

Each run compares r15d with kF at the indicated setting. Each measurement in the table applies to both builds. The node sum omits any `NA` where the search returned a move without an info line. SHA-256 and `cmp` apply to the complete record bytes.

| Run | Set | UCI limit | Games | Ply records | NA | Sum of numeric nodes | Record SHA-256 | cmp exit | Reading |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1 | 1 | `go softnodes 2000` | 100 | 12,006 | 0 | 50,001,595 | `555ddcbd82b406bebc11a71b9e3195d2da96ff04d1ffaa5c6370a3ba9dfe5eda` | 0 | IDENTICAL |
| F1 | 1 | `go nodes 20000` | 30 | 3,608 | 0 | 44,039,325 | `90862063b4acd1e8bab7fb590378d33ac20e20e4db04578a01429fc4be836e1e` | 0 | IDENTICAL |
| R2 | 2 | `go softnodes 2000` | 100 | 11,592 | 0 | 41,510,797 | `4a94c8958f19b0a8ec10ac0da5c8f92ce68d01432c9a0a84b5bc00a88af82d28` | 0 | IDENTICAL |
| F2 | 2 | `go nodes 20000` | 30 | 3,064 | 0 | 39,612,542 | `3a7be0fb8b65eeb7abd2fb4d7778c51892a4095b2008478f9557c73d1175f33d` | 0 | IDENTICAL |
| R3 | 3 | `go softnodes 2000` | 100 | 11,376 | 0 | 47,504,416 | `2180ceda990199eae147b4afa11026b50a48cebfd4de39be1c3361219c505ba7` | 0 | IDENTICAL |
| F3 | 3 | `go nodes 20000` | 30 | 3,032 | 0 | 35,729,908 | `406a871a0c32ccc7b3d1fa8bdb1cd45348afac3c64b7fd2bfbde8e03f1c7503b` | 0 | IDENTICAL |
| R4 | 4 | `go softnodes 2000` | 100 | 11,497 | 0 | 44,089,212 | `af845f58f33d70f5ecf86c8828225272a3b0223d026d88f6d2a4522c2edf4042` | 0 | IDENTICAL |
| F4 | 4 | `go nodes 20000` | 30 | 2,695 | 0 | 34,173,795 | `266b63aac5606c77aa1c25074d4ef0ecb4a837be84ebfe990eaaacdd78579ad3` | 0 | IDENTICAL |
| R5 | 5 | `go softnodes 2000` | 100 | 11,929 | 0 | 44,462,574 | `2d010bad45b3e343b704dbcafa3b196266bfe70a047efce4b5ecde4528ecdc7b` | 0 | IDENTICAL |
| F5 | 5 | `go nodes 20000` | 30 | 3,246 | 0 | 41,436,600 | `fd2e85f018f1784bd9dd9e379eb045f28be7bbf0dcbf7cc5c70113f4e9eb3968` | 0 | IDENTICAL |

**KEEPS.** All ten measured runs produced byte-identical moves and node fields on the tested openings and value sets.

[R1](astra5/job18/audit/R1/summary.txt) · [F1](astra5/job18/audit/F1/summary.txt) · [R2](astra5/job18/audit/R2/summary.txt) · [F2](astra5/job18/audit/F2/summary.txt) · [R3](astra5/job18/audit/R3/summary.txt) · [F3](astra5/job18/audit/F3/summary.txt) · [R4](astra5/job18/audit/R4/summary.txt) · [F4](astra5/job18/audit/F4/summary.txt) · [R5](astra5/job18/audit/R5/summary.txt) · [F5](astra5/job18/audit/F5/summary.txt).

## Facts

Across all measured arms, r15d logged 74,045 plies in 650 games and 0 records without an info line. kF had the same counts.

## Suspicions

The deliberate setting change in C18 shows the output reacts to the values being varied. It does not isolate a particular tuning option or speed-stack component.

## What I did not do

I did not run strength matches or benchmark wall-clock speed.

**What this cannot see**, in the job’s words

> the PC's engine build (clang 23 for Windows, its profile), its trained nets (net768 is made up), the values the PC's tune will really end with (these are other values nearby), more than one thread.

## What I am not sure about

These five value sets sample a finite neighborhood of the starts. The result does not settle behavior for a different combination of values or the settings selected by the PC’s tune.

## Pre-commit inventory

Output from `git status --short` followed by `ls -R forge-combo29/astra5/job18`.

```text
A  forge-combo29/REPORT_astra5_job18.md
M  forge-combo29/astra5/job18/stamps.txt
forge-combo29/astra5/job18:
C18
F1-kF
F1-r15d
F2-kF
F2-r15d
F3-kF
F3-r15d
F4-kF
F4-r15d
F5-kF
F5-r15d
K18-1
K18-2
R1-kF
R1-r15d
R2-kF
R2-r15d
R3-kF
R3-r15d
R4-kF
R4-r15d
R5-kF
R5-r15d
audit
driver
prediction.txt
sets.txt
settings
stamps.txt
step0

forge-combo29/astra5/job18/C18:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/C18/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/F1-kF:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt
slot2
slot2-controller.txt

forge-combo29/astra5/job18/F1-kF/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F1-kF/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F1-r15d:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt
slot2
slot2-controller.txt

forge-combo29/astra5/job18/F1-r15d/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F1-r15d/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F2-kF:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt
slot2
slot2-controller.txt

forge-combo29/astra5/job18/F2-kF/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F2-kF/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F2-r15d:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt
slot2
slot2-controller.txt

forge-combo29/astra5/job18/F2-r15d/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F2-r15d/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F3-kF:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt
slot2
slot2-controller.txt

forge-combo29/astra5/job18/F3-kF/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F3-kF/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F3-r15d:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt
slot2
slot2-controller.txt

forge-combo29/astra5/job18/F3-r15d/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F3-r15d/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F4-kF:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt
slot2
slot2-controller.txt

forge-combo29/astra5/job18/F4-kF/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F4-kF/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F4-r15d:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt
slot2
slot2-controller.txt

forge-combo29/astra5/job18/F4-r15d/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F4-r15d/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F5-kF:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt
slot2
slot2-controller.txt

forge-combo29/astra5/job18/F5-kF/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F5-kF/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F5-r15d:
games.tsv
no-info.tsv
records.txt
run.log
slot1
slot1-controller.txt
slot2
slot2-controller.txt

forge-combo29/astra5/job18/F5-r15d/slot1:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/F5-r15d/slot2:
games.tsv
no-info.tsv
records.txt
run.log

forge-combo29/astra5/job18/K18-1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/K18-1/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/K18-2:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/K18-2/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/R1-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/R1-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/R1-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/R1-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/R2-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/R2-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/R2-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/R2-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/R3-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/R3-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/R3-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/R3-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/R4-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/R4-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/R4-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/R4-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/R5-kF:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/R5-kF/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/R5-r15d:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log
slot1
slot1-controller.txt

forge-combo29/astra5/job18/R5-r15d/slot1:
games.tsv
no-info.tsv
openings.tsv
records.txt
run.log

forge-combo29/astra5/job18/audit:
C18
F1
F2
F3
F4
F5
K18
R1
R2
R3
R4
R5
audit.py
combine.py
input-validation.txt
monitor.py
reading.txt
stage-order.tsv
stage-summary.tsv

forge-combo29/astra5/job18/audit/C18:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
live-first-difference.txt
summary.txt

forge-combo29/astra5/job18/audit/F1:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job18/audit/F2:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job18/audit/F3:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job18/audit/F4:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job18/audit/F5:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job18/audit/K18:
K18-1-controller.txt
K18-2-controller.txt
arms.tsv
cmp.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job18/audit/R1:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job18/audit/R2:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job18/audit/R3:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job18/audit/R4:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job18/audit/R5:
arms.tsv
cmp.txt
controller.txt
differences.tsv
first-difference.txt
games.tsv
summary.txt

forge-combo29/astra5/job18/driver:
arm.py
compare_stage.py
driver-review.txt
selfplay.py
sol35-recipe.txt
stage.py

forge-combo29/astra5/job18/settings:
audit-sets.py
check-played-settings.py
generate-sets.py
played-settings-audit.txt
sets-audit.txt

forge-combo29/astra5/job18/step0:
controls.py
declarations.py
identities.txt
kF
pc20.txt
r15d

forge-combo29/astra5/job18/step0/kF:
40-uci.txt
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
uci-raw.txt

forge-combo29/astra5/job18/step0/r15d:
40-uci.txt
PC20-net768-bench-11.txt
PC20-net768-bench-13.txt
checks.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
uci-raw.txt
```

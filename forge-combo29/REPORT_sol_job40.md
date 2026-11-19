# Sol — Job 40 one-setting whole-game map

## Step 0. Known-answer pins

The unchanged Job 34 GCC 14.2.0 r15d binary passed all five fresh-process checks. Defaults gave 312866 for `bench 11`, 862329 for `bench 13` and 4865609 for `go perft 5`. PC20 and synthetic net768 gave 882074 and 4275906 for the two benches and reported `NNUE v3 active` with checksum `30ab43b4ba5db5f3`. `nproc` returned 5. I ran up to four single-threaded engine processes with cgroup quota `400000 100000`. [Raw r15d pins](sol/job40/pin-evidence/r15d.raw.txt) · [nproc](sol/job40/pin-evidence/nproc.txt) · [CPU quota](sol/job40/pin-evidence/cpu-max.txt)

## BASE, known answers and control

All runs used r15d, PC20, active net768, Threads 1 and Hash 16. N2 used `go nodes 20000` on 410001–410020. N1 used `go softnodes 2000` on 400001–400020. Each variant used an identical game range.

| Limit | Check | Tested against BASE-a | Comparison | Differing games | Candidate games / records | Gate |
| --- | --- | --- | --- | ---: | --- | --- |
| N2 | BASE | `N2/BASE-b` | IDENTICAL | 0 | 20 / 2,039 | PASS |
| N2 | EvalSwingMax220 | `N2/EvalSwingMax220` | IDENTICAL | 0 | 20 / 2,039 | PASS |
| N2 | CaptureFutilityMultiplier275 | `N2/CaptureFutilityMultiplier275` | IDENTICAL | 0 | 20 / 2,039 | PASS |
| N2 | LmrQuietBase101 | `N2/LmrQuietBase/PLUS` | DIFFERS | 20 | 20 / 1,993 | PASS |
| N1 | BASE | `N1/BASE-b` | IDENTICAL | 0 | 20 / 2,423 | PASS |
| N1 | EvalSwingMax220 | `N1/EvalSwingMax220` | IDENTICAL | 0 | 20 / 2,423 | PASS |
| N1 | CaptureFutilityMultiplier275 | `N1/CaptureFutilityMultiplier275` | IDENTICAL | 0 | 20 / 2,423 | PASS |
| N1 | LmrQuietBase101 | `N1/LmrQuietBase/PLUS` | DIFFERS | 20 | 20 / 2,299 | PASS |

N2 LmrQuietBase101 first differed at record line 1. BASE-a `410001 8 b3b4 13077`. Variant `410001 8 b3b4 19024`.

N1 LmrQuietBase101 first differed at record line 1. BASE-a `400001 8 c4d6 2756`. Variant `400001 8 c4d6 2443`.

N2 BASE-a recorded 2,039 searches and 23,881,605 last-info nodes in 20 games. [Gate readback](sol/job40/N2-gate.stats.json) · [cmp](sol/job40/N2-gate.cmp.tsv)

N1 BASE-a recorded 2,423 searches and 9,781,064 last-info nodes in 20 games. [Gate readback](sol/job40/N1-gate.stats.json) · [cmp](sol/job40/N1-gate.cmp.tsv)

## Prediction and grade

I froze `5872efc` after the N2 gate and before the other setting runs. I expected the soft-node searches to reach fewer of the depth thresholds that make the forecast settings matter. [Frozen prediction](sol/job40/prediction.json) · [UTC stamps](sol/job40/stamps.txt)

| Limit | Forecast LIVE | Observed LIVE | Grade | Forecast NO CHANGE SEEN | Observed NO CHANGE SEEN | Grade |
| --- | --- | ---: | --- | --- | --- | --- |
| N2 | 37–40 | 40 | met | None | None | met |
| N1 | 32–40 | 40 | met | `NullMoveEvalDivisor`, `RfpDepth`, `FutilityDepth`, `HistoryBonusMax` | None | missed |

## The 40 setting comparisons

A game differed if any of its move or last-info node records differed from BASE-a. A setting is **LIVE** if either tested value changed at least one game. **NO CHANGE SEEN** requires both completed values to match all 20 baseline games. [Exact design](sol/job40/design40.tsv) · [Per-variant first differing records](sol/job40/analysis.json)

| Setting | MINUS or PLUS2 | N2 games differing | N1 games differing | PLUS | N2 games differing | N1 games differing | N2 reading | N1 reading |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| DrawJitter | PLUS2 2 | 2 | 1 | 1 | 2 | 1 | LIVE | LIVE |
| LmrQuietBase | MINUS 85 | 20 | 20 | 101 | 20 | 20 | LIVE | LIVE |
| LmrQuietDivisor | MINUS 193 | 20 | 20 | 217 | 20 | 20 | LIVE | LIVE |
| LmrNoisyBase | MINUS 7 | 20 | 20 | 19 | 20 | 20 | LIVE | LIVE |
| LmrNoisyDivisor | MINUS 313 | 20 | 20 | 353 | 20 | 20 | LIVE | LIVE |
| NullMoveMinDepth | MINUS 2 | 20 | 20 | 4 | 20 | 20 | LIVE | LIVE |
| NullMoveBase | MINUS 4 | 20 | 20 | 6 | 20 | 20 | LIVE | LIVE |
| NullMoveDepthDivisor | MINUS 2 | 20 | 20 | 4 | 20 | 20 | LIVE | LIVE |
| NullMoveEvalDivisor | MINUS 180 | 20 | 12 | 220 | 20 | 12 | LIVE | LIVE |
| RfpDepth | MINUS 7 | 20 | 20 | 9 | 20 | 15 | LIVE | LIVE |
| RfpMargin | MINUS 66 | 20 | 20 | 78 | 20 | 20 | LIVE | LIVE |
| RfpImproving | MINUS 34 | 20 | 20 | 46 | 20 | 20 | LIVE | LIVE |
| RazorDepth | MINUS 1 | 20 | 20 | 3 | 20 | 20 | LIVE | LIVE |
| RazorBase | MINUS 130 | 20 | 20 | 170 | 20 | 20 | LIVE | LIVE |
| RazorMultiplier | MINUS 325 | 20 | 20 | 375 | 20 | 20 | LIVE | LIVE |
| FutilityDepth | MINUS 6 | 20 | 20 | 8 | 20 | 16 | LIVE | LIVE |
| FutilityBase | MINUS 88 | 20 | 20 | 112 | 20 | 20 | LIVE | LIVE |
| FutilityMultiplier | MINUS 100 | 20 | 20 | 120 | 20 | 20 | LIVE | LIVE |
| LmpBase | MINUS 7 | 20 | 20 | 9 | 20 | 20 | LIVE | LIVE |
| HistoryPruneDepth | MINUS 2 | 20 | 20 | 4 | 20 | 18 | LIVE | LIVE |
| HistoryPruneMultiplier | MINUS 2020 | 20 | 20 | 2420 | 20 | 20 | LIVE | LIVE |
| SeeQuietMultiplier | MINUS 21 | 20 | 20 | 27 | 20 | 20 | LIVE | LIVE |
| SeeNoisyMultiplier | MINUS 138 | 20 | 20 | 162 | 20 | 20 | LIVE | LIVE |
| SingularDepth | MINUS 5 | 20 | 20 | 7 | 20 | 20 | LIVE | LIVE |
| SingularMargin | MINUS 1 | 20 | 20 | 3 | 20 | 20 | LIVE | LIVE |
| IirDepth | MINUS 1 | 20 | 20 | 3 | 20 | 20 | LIVE | LIVE |
| ProbcutDepth | MINUS 4 | 20 | 20 | 6 | 20 | 20 | LIVE | LIVE |
| ProbcutMargin | MINUS 165 | 20 | 20 | 195 | 20 | 20 | LIVE | LIVE |
| QsFutilityMargin | MINUS 146 | 20 | 20 | 174 | 20 | 20 | LIVE | LIVE |
| AspirationDelta | MINUS 16 | 20 | 20 | 20 | 20 | 20 | LIVE | LIVE |
| HistoryBonusQuadratic | MINUS 21 | 20 | 20 | 27 | 20 | 20 | LIVE | LIVE |
| HistoryBonusLinear | MINUS 48 | 20 | 20 | 60 | 20 | 20 | LIVE | LIVE |
| HistoryBonusMax | MINUS 2032 | 20 | 20 | 2392 | 20 | 20 | LIVE | LIVE |
| LmrHistoryDivisor | MINUS 5143 | 20 | 20 | 6143 | 20 | 20 | LIVE | LIVE |
| CheckExtensionDepth | MINUS 1 | 20 | 20 | 3 | 20 | 20 | LIVE | LIVE |
| LmrCutoffThreshold | MINUS 2 | 20 | 20 | 4 | 20 | 20 | LIVE | LIVE |
| MaterialCorrectionWeight | MINUS 90 | 20 | 20 | 110 | 20 | 20 | LIVE | LIVE |
| CaptureFutilityBase | PLUS2 40 | 20 | 20 | 20 | 20 | 20 | LIVE | LIVE |
| FailLowContinuationBonus | PLUS2 30 | 20 | 20 | 15 | 20 | 20 | LIVE | LIVE |
| EvalSwingMult | PLUS2 6 | 20 | 20 | 3 | 20 | 20 | LIVE | LIVE |

## LIVE counts

**N2 40/40 LIVE.** NO CHANGE SEEN None.

N2 completed 84 fresh-process runs, including the baselines and controls. They recorded 1,680 games, 174,027 searches and 2,048,722,116 last-info nodes. [Per-run counts and hashes](sol/job40/analysis.runs.tsv)

**N1 40/40 LIVE.** NO CHANGE SEEN None.

N1 completed 84 fresh-process runs, including the baselines and controls. They recorded 1,680 games, 194,511 searches and 800,624,996 last-info nodes. [Per-run counts and hashes](sol/job40/analysis.runs.tsv)

## Facts

The 40 baseline starts matched the r15d defaults with PC20 applied. Each option command had its own `readyok`. The LmrQuietBase 101 control also supplies the corresponding PLUS result. The four settings whose start equals the minimum use PLUS and PLUS2. [Design](sol/job40/design40.tsv) · [Raw setup and game records](sol/job40/raw)

Job 38 readback resolves the C38 ordering detail in Opus’s file 40. `Qe6+` versus `Qe4+` is the first move at UHO line 4005, the first root in FEN sort order. My report used opening-book order. At line 4001 both played `Nbd7` first, with different PGN nodes at ply 1 and different moves at ply 3. [C38 PGN](sol/job38/raw/C38.pgn) · [Job 38 report](REPORT_sol_job38.md)

## Suspicions

A small change can alter a node count before it changes a move. The first-record evidence shows where that happened, while the game counts reflect the full traces.

## What this check cannot see

The PC's net (with it a search at 20,000 nodes reaches other depths than with net768), its build, positions these
40 games do not reach, two settings changed together (a setting can change nothing alone and something when another
setting moves; the tune moves all 40 at once).

## What I did not do

I ran these cloud tests on unchanged r15d. I made no engine source changes and ran no experiment on the owner’s PC.

## What I am not sure about

The result does not measure how an untested step size or an interaction with another setting would change the search.

## Reproduction and independent readback

The runner uses the Job 39 UCI logger and Job 35 game loop with python-chess 1.11.2. The two analyses compared raw record bytes by game and verified the archive. [Runner](sol/job40/run_cell40.py) · [Primary analysis](sol/job40/analysis.json) · [Independent archive read](sol/job40/independent.json) · [UTC stamps](sol/job40/stamps.txt)

## Precommit status and evidence inventory

```text
M  forge-combo29/NOTES_sol.md
A  forge-combo29/REPORT_sol_job40.md
A  forge-combo29/sol/job40/analysis.json
A  forge-combo29/sol/job40/analysis.runs.tsv
A  forge-combo29/sol/job40/analyze40.py
A  forge-combo29/sol/job40/independent.json
A  forge-combo29/sol/job40/independent40.py
A  forge-combo29/sol/job40/readback.txt
A  forge-combo29/sol/job40/run_cell40.py
A  forge-combo29/sol/job40/run_stage40.py
M  forge-combo29/sol/job40/stamps.txt
A  forge-combo29/sol/job40/verify40.py
forge-combo29/sol/job40:
N1-gate.cmp.tsv
N1-gate.runs.tsv
N1-gate.stage.out
N1-gate.stats.json
N1-settings.runs.tsv
N1-settings.stage.out
N1-settings.stats.json
N2-gate.cmp.tsv
N2-gate.runs.tsv
N2-gate.stage.out
N2-gate.stats.json
N2-settings.runs.tsv
N2-settings.stage.out
N2-settings.stats.json
analysis.json
analysis.runs.tsv
analyze40.py
design40.tsv
independent.json
independent40.py
pin-evidence
prediction.json
raw
readback.txt
run_cell40.py
run_stage40.py
stamps.txt
verify40.py

forge-combo29/sol/job40/pin-evidence:
cpu-max.txt
nproc.txt
r15d.raw.txt
step0.out

forge-combo29/sol/job40/raw:
N1
N2

forge-combo29/sol/job40/raw/N1:
AspirationDelta
BASE-a
BASE-a.driver.out
BASE-b
BASE-b.driver.out
CaptureFutilityBase
CaptureFutilityMultiplier275
CaptureFutilityMultiplier275.driver.out
CheckExtensionDepth
DrawJitter
EvalSwingMax220
EvalSwingMax220.driver.out
EvalSwingMult
FailLowContinuationBonus
FutilityBase
FutilityDepth
FutilityMultiplier
HistoryBonusLinear
HistoryBonusMax
HistoryBonusQuadratic
HistoryPruneDepth
HistoryPruneMultiplier
IirDepth
LmpBase
LmrCutoffThreshold
LmrHistoryDivisor
LmrNoisyBase
LmrNoisyDivisor
LmrQuietBase
LmrQuietDivisor
MaterialCorrectionWeight
NullMoveBase
NullMoveDepthDivisor
NullMoveEvalDivisor
NullMoveMinDepth
ProbcutDepth
ProbcutMargin
QsFutilityMargin
RazorBase
RazorDepth
RazorMultiplier
RfpDepth
RfpImproving
RfpMargin
SeeNoisyMultiplier
SeeQuietMultiplier
SingularDepth
SingularMargin

forge-combo29/sol/job40/raw/N1/AspirationDelta:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/AspirationDelta/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/AspirationDelta/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/BASE-a:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/BASE-b:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/CaptureFutilityBase:
PLUS
PLUS.driver.out
PLUS2
PLUS2.driver.out

forge-combo29/sol/job40/raw/N1/CaptureFutilityBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/CaptureFutilityBase/PLUS2:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/CaptureFutilityMultiplier275:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/CheckExtensionDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/CheckExtensionDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/CheckExtensionDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/DrawJitter:
PLUS
PLUS.driver.out
PLUS2
PLUS2.driver.out

forge-combo29/sol/job40/raw/N1/DrawJitter/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/DrawJitter/PLUS2:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/EvalSwingMax220:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/EvalSwingMult:
PLUS
PLUS.driver.out
PLUS2
PLUS2.driver.out

forge-combo29/sol/job40/raw/N1/EvalSwingMult/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/EvalSwingMult/PLUS2:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/FailLowContinuationBonus:
PLUS
PLUS.driver.out
PLUS2
PLUS2.driver.out

forge-combo29/sol/job40/raw/N1/FailLowContinuationBonus/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/FailLowContinuationBonus/PLUS2:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/FutilityBase:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/FutilityBase/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/FutilityBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/FutilityDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/FutilityDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/FutilityDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/FutilityMultiplier:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/FutilityMultiplier/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/FutilityMultiplier/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/HistoryBonusLinear:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/HistoryBonusLinear/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/HistoryBonusLinear/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/HistoryBonusMax:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/HistoryBonusMax/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/HistoryBonusMax/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/HistoryBonusQuadratic:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/HistoryBonusQuadratic/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/HistoryBonusQuadratic/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/HistoryPruneDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/HistoryPruneDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/HistoryPruneDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/HistoryPruneMultiplier:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/HistoryPruneMultiplier/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/HistoryPruneMultiplier/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/IirDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/IirDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/IirDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmpBase:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/LmpBase/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmpBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmrCutoffThreshold:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/LmrCutoffThreshold/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmrCutoffThreshold/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmrHistoryDivisor:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/LmrHistoryDivisor/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmrHistoryDivisor/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmrNoisyBase:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/LmrNoisyBase/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmrNoisyBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmrNoisyDivisor:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/LmrNoisyDivisor/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmrNoisyDivisor/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmrQuietBase:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/LmrQuietBase/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmrQuietBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmrQuietDivisor:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/LmrQuietDivisor/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/LmrQuietDivisor/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/MaterialCorrectionWeight:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/MaterialCorrectionWeight/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/MaterialCorrectionWeight/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/NullMoveBase:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/NullMoveBase/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/NullMoveBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/NullMoveDepthDivisor:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/NullMoveDepthDivisor/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/NullMoveDepthDivisor/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/NullMoveEvalDivisor:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/NullMoveEvalDivisor/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/NullMoveEvalDivisor/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/NullMoveMinDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/NullMoveMinDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/NullMoveMinDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/ProbcutDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/ProbcutDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/ProbcutDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/ProbcutMargin:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/ProbcutMargin/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/ProbcutMargin/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/QsFutilityMargin:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/QsFutilityMargin/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/QsFutilityMargin/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/RazorBase:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/RazorBase/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/RazorBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/RazorDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/RazorDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/RazorDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/RazorMultiplier:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/RazorMultiplier/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/RazorMultiplier/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/RfpDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/RfpDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/RfpDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/RfpImproving:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/RfpImproving/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/RfpImproving/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/RfpMargin:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/RfpMargin/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/RfpMargin/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/SeeNoisyMultiplier:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/SeeNoisyMultiplier/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/SeeNoisyMultiplier/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/SeeQuietMultiplier:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/SeeQuietMultiplier/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/SeeQuietMultiplier/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/SingularDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/SingularDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/SingularDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/SingularMargin:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N1/SingularMargin/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N1/SingularMargin/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2:
AspirationDelta
BASE-a
BASE-a.driver.out
BASE-b
BASE-b.driver.out
CaptureFutilityBase
CaptureFutilityMultiplier275
CaptureFutilityMultiplier275.driver.out
CheckExtensionDepth
DrawJitter
EvalSwingMax220
EvalSwingMax220.driver.out
EvalSwingMult
FailLowContinuationBonus
FutilityBase
FutilityDepth
FutilityMultiplier
HistoryBonusLinear
HistoryBonusMax
HistoryBonusQuadratic
HistoryPruneDepth
HistoryPruneMultiplier
IirDepth
LmpBase
LmrCutoffThreshold
LmrHistoryDivisor
LmrNoisyBase
LmrNoisyDivisor
LmrQuietBase
LmrQuietDivisor
MaterialCorrectionWeight
NullMoveBase
NullMoveDepthDivisor
NullMoveEvalDivisor
NullMoveMinDepth
ProbcutDepth
ProbcutMargin
QsFutilityMargin
RazorBase
RazorDepth
RazorMultiplier
RfpDepth
RfpImproving
RfpMargin
SeeNoisyMultiplier
SeeQuietMultiplier
SingularDepth
SingularMargin

forge-combo29/sol/job40/raw/N2/AspirationDelta:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/AspirationDelta/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/AspirationDelta/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/BASE-a:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/BASE-b:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/CaptureFutilityBase:
PLUS
PLUS.driver.out
PLUS2
PLUS2.driver.out

forge-combo29/sol/job40/raw/N2/CaptureFutilityBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/CaptureFutilityBase/PLUS2:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/CaptureFutilityMultiplier275:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/CheckExtensionDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/CheckExtensionDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/CheckExtensionDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/DrawJitter:
PLUS
PLUS.driver.out
PLUS2
PLUS2.driver.out

forge-combo29/sol/job40/raw/N2/DrawJitter/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/DrawJitter/PLUS2:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/EvalSwingMax220:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/EvalSwingMult:
PLUS
PLUS.driver.out
PLUS2
PLUS2.driver.out

forge-combo29/sol/job40/raw/N2/EvalSwingMult/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/EvalSwingMult/PLUS2:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/FailLowContinuationBonus:
PLUS
PLUS.driver.out
PLUS2
PLUS2.driver.out

forge-combo29/sol/job40/raw/N2/FailLowContinuationBonus/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/FailLowContinuationBonus/PLUS2:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/FutilityBase:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/FutilityBase/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/FutilityBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/FutilityDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/FutilityDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/FutilityDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/FutilityMultiplier:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/FutilityMultiplier/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/FutilityMultiplier/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/HistoryBonusLinear:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/HistoryBonusLinear/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/HistoryBonusLinear/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/HistoryBonusMax:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/HistoryBonusMax/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/HistoryBonusMax/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/HistoryBonusQuadratic:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/HistoryBonusQuadratic/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/HistoryBonusQuadratic/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/HistoryPruneDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/HistoryPruneDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/HistoryPruneDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/HistoryPruneMultiplier:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/HistoryPruneMultiplier/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/HistoryPruneMultiplier/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/IirDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/IirDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/IirDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmpBase:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/LmpBase/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmpBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmrCutoffThreshold:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/LmrCutoffThreshold/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmrCutoffThreshold/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmrHistoryDivisor:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/LmrHistoryDivisor/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmrHistoryDivisor/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmrNoisyBase:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/LmrNoisyBase/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmrNoisyBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmrNoisyDivisor:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/LmrNoisyDivisor/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmrNoisyDivisor/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmrQuietBase:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/LmrQuietBase/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmrQuietBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmrQuietDivisor:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/LmrQuietDivisor/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/LmrQuietDivisor/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/MaterialCorrectionWeight:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/MaterialCorrectionWeight/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/MaterialCorrectionWeight/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/NullMoveBase:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/NullMoveBase/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/NullMoveBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/NullMoveDepthDivisor:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/NullMoveDepthDivisor/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/NullMoveDepthDivisor/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/NullMoveEvalDivisor:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/NullMoveEvalDivisor/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/NullMoveEvalDivisor/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/NullMoveMinDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/NullMoveMinDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/NullMoveMinDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/ProbcutDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/ProbcutDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/ProbcutDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/ProbcutMargin:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/ProbcutMargin/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/ProbcutMargin/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/QsFutilityMargin:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/QsFutilityMargin/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/QsFutilityMargin/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/RazorBase:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/RazorBase/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/RazorBase/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/RazorDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/RazorDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/RazorDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/RazorMultiplier:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/RazorMultiplier/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/RazorMultiplier/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/RfpDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/RfpDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/RfpDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/RfpImproving:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/RfpImproving/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/RfpImproving/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/RfpMargin:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/RfpMargin/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/RfpMargin/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/SeeNoisyMultiplier:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/SeeNoisyMultiplier/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/SeeNoisyMultiplier/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/SeeQuietMultiplier:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/SeeQuietMultiplier/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/SeeQuietMultiplier/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/SingularDepth:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/SingularDepth/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/SingularDepth/PLUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/SingularMargin:
MINUS
MINUS.driver.out
PLUS
PLUS.driver.out

forge-combo29/sol/job40/raw/N2/SingularMargin/MINUS:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job40/raw/N2/SingularMargin/PLUS:
records.txt
run.json
uci-setup.txt
```

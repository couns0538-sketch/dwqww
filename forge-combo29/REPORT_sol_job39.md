# Sol — Job 39 simultaneous tuning-draw identity

## Step 0. Known-answer pins and UCI spins

Both unchanged Job 34 GCC 14.2.0 binaries passed five fresh-process checks each. Defaults gave 312866 for `bench 11`, 862329 for `bench 13` and 4865609 for `go perft 5`. PC20 with synthetic net768 gave 882074 and 4275906 for the two benches and reported `NNUE v3 active` with checksum `30ab43b4ba5db5f3`. `nproc` returned 5. I used up to four simultaneous engine processes for A and B, matching the cloud quota from `cpu.max` `400000 100000`. Each used one search thread. [r15d pins](sol/job39/pin-evidence/r15d.raw.txt) · [kF pins](sol/job39/pin-evidence/kF.raw.txt) · [CPU receipts](sol/job39/pin-evidence)

Both fresh UCI replies advertised the same 40 spin declarations in the table order. [r15d raw UCI](sol/job39/pin-evidence/r15d.uci.raw.txt) · [kF raw UCI](sol/job39/pin-evidence/kF.uci.raw.txt)

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

## Draws. Known answers and provenance

I generated all 100 draws with `random.Random(390000 + k)`, using the handoff table order and bounds. Both known-answer rows matched, and I pushed `129a76f` before any game. The generator sets all 40 values after PC20. Zero offsets and clipping can leave some values at the PC start. [Draws TSV](sol/job39/draws.tsv) · [Generator](sol/job39/generate_draws39.py) · [Known-answer equality](sol/job39/draws-known-answer.txt)

```text
draw 1 PASS	4	141	181	0	293	9	6	1	180	12	42	76	0	230	225	12	148	140	5	2	1620	30	138	9	2	1	8	225	244	26	42	18	1672	4143	1	0	90	100	0	0
draw 100 PASS	0	53	229	19	253	6	1	1	100	11	102	16	0	50	325	12	112	140	11	6	3220	42	150	10	6	6	5	90	118	6	30	90	2392	2643	2	9	160	0	0	3
```

## K39, C39 and L39

All controls used r15d with Threads 1, Hash 16, active net768 and `go nodes 20000` on games 390001–390010.

**K39 PASS.** Both runs used draw 1 after PC20. The comparison read IDENTICAL. The two runs completed 10 and 10 games with 1,165 and 1,165 records. [Comparison](sol/job39/K39.stats.json) · [cmp](sol/job39/K39.cmp.tsv)

**C39 PASS.** C39 replaced draw 1’s LmrQuietBase 141 with 60. The comparison read DIFFERS. The two runs completed 10 and 10 games with 1,165 and 999 records. [Comparison](sol/job39/C39.stats.json) · [cmp](sol/job39/C39.cmp.tsv)

The first differing line was 1. K39a reported `390001 8 e4c5 12334`. C39 reported `390001 8 e4c5 9403`.

**L39 PASS.** L39 used PC20 alone. The comparison read DIFFERS. The two runs completed 10 and 10 games with 1,165 and 887 records. [Comparison](sol/job39/L39.stats.json) · [cmp](sol/job39/L39.cmp.tsv)

The first differing line was 1. K39a reported `390001 8 e4c5 12334`. L39 reported `390001 8 e4c5 16153`.

## Prediction and grade

I froze `cd5d4d5` after L39 and before A. I expected the two builds’ record files to match for every draw under each limit. [Frozen prediction](sol/job39/prediction.json) · [UTC stamps](sol/job39/stamps.txt)

| Stage | Forecast draws differing | Observed | Grade |
| --- | ---: | ---: | --- |
| A | 0–0 | 0 | met |
| B | 0–0 | 0 | met |

## A and B. Byte comparisons

Both builds used PC20, synthetic net768, Threads 1 and Hash 16. Each fresh process then received the draw’s 40 values. A used `go nodes 20000` and B used `go softnodes 2000`. Both builds played the same ten seeded games for each draw.

| Stage | Draws started | Draws complete | Identical | Differ | Incomplete | Not played | r15d games / records | kF games / records | Reading |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A | 100 | 100 | 100 | 0 | 0 | 0 | 1,000 / 101,695 | 1,000 / 101,695 | **KEEPS** |
| B | 100 | 100 | 100 | 0 | 0 | 0 | 1,000 / 112,582 | 1,000 / 112,582 | **KEEPS** |

A recorded 1,187,786,875 last-info nodes on r15d and 1,187,786,875 on kF for the completed games. [Per-run counts and hashes](sol/job39/A.runs.tsv) · [cmp results](sol/job39/A.cmp.tsv)

B recorded 441,981,749 last-info nodes on r15d and 441,981,749 on kF for the completed games. [Per-run counts and hashes](sol/job39/B.runs.tsv) · [cmp results](sol/job39/B.cmp.tsv)

## Facts

The UCI setup logs preserve every option command and the output through each `readyok`. The game driver used Job 35’s random opening plies, draw claims and 300-ply cap. The record file stores a game number, zero-based ply, UCI move and the last emitted info node field. [Run-by-run counts and hashes](sol/job39/analysis.runs.tsv) · [Raw options and games](sol/job39/raw)

## Suspicions

A tuning draw can leave a clipped or zero-offset value at its start. Equality on these draws therefore supports the joint changes actually exercised, including their recorded interactions.

## What this check cannot see

The PC's engine build (clang 23 for Windows, its profile), its trained net (net768 is made up), the tune's final
values themselves (they are not known before the tune ends), more than one thread, games on the clock.

## What I did not do

I ran the comparisons here in Case A. I made no changes to the tracked engine source and ran no experiment on the owner’s PC.

## What I am not sure about

The actual tuning output is still unknown. These draws cover the tested neighborhoods of the start settings.

## Reproduction and independent readback

The driver uses python-chess 1.11.2 and the Job 34 pinned binaries and net. Each byte comparison was recomputed from the archived records. [Draw driver](sol/job39/run_draw39.py) · [Analysis](sol/job39/analysis.json) · [Independent archive read](sol/job39/independent.json) · [UTC stamps](sol/job39/stamps.txt)

## Precommit status and evidence inventory

```text
M  forge-combo29/NOTES_sol.md
A  forge-combo29/REPORT_sol_job39.md
A  forge-combo29/sol/job39/analysis.json
A  forge-combo29/sol/job39/analysis.runs.tsv
A  forge-combo29/sol/job39/analyze39.py
A  forge-combo29/sol/job39/independent.json
A  forge-combo29/sol/job39/independent39.py
A  forge-combo29/sol/job39/readback.txt
A  forge-combo29/sol/job39/run_draw39.py
A  forge-combo29/sol/job39/run_stage39.py
M  forge-combo29/sol/job39/stamps.txt
A  forge-combo29/sol/job39/verify39.py
forge-combo29/sol/job39:
A.cmp.tsv
A.runs.tsv
A.stage.out
A.stats.json
B.cmp.tsv
B.runs.tsv
B.stage.out
B.stats.json
C39.cmp.tsv
C39.runs.tsv
C39.stage.out
C39.stats.json
K39.cmp.tsv
K39.runs.tsv
K39.stage.out
K39.stats.json
L39.cmp.tsv
L39.runs.tsv
L39.stage.out
L39.stats.json
analysis.json
analysis.runs.tsv
analyze39.py
check_spin39.py
draws-known-answer.txt
draws.tsv
generate_draws39.py
independent.json
independent39.py
pin-evidence
prediction.json
raw
readback.txt
run_draw39.py
run_stage39.py
stamps.txt
verify39.py

forge-combo29/sol/job39/pin-evidence:
cpu-max.txt
kF.raw.txt
kF.uci.raw.txt
nproc.txt
r15d.raw.txt
r15d.uci.raw.txt
spin-options.txt

forge-combo29/sol/job39/raw:
A
B
C39
C39.driver.out
K39a
K39a.driver.out
K39b
K39b.driver.out
L39
L39.driver.out

forge-combo29/sol/job39/raw/A:
draw-001
draw-002
draw-003
draw-004
draw-005
draw-006
draw-007
draw-008
draw-009
draw-010
draw-011
draw-012
draw-013
draw-014
draw-015
draw-016
draw-017
draw-018
draw-019
draw-020
draw-021
draw-022
draw-023
draw-024
draw-025
draw-026
draw-027
draw-028
draw-029
draw-030
draw-031
draw-032
draw-033
draw-034
draw-035
draw-036
draw-037
draw-038
draw-039
draw-040
draw-041
draw-042
draw-043
draw-044
draw-045
draw-046
draw-047
draw-048
draw-049
draw-050
draw-051
draw-052
draw-053
draw-054
draw-055
draw-056
draw-057
draw-058
draw-059
draw-060
draw-061
draw-062
draw-063
draw-064
draw-065
draw-066
draw-067
draw-068
draw-069
draw-070
draw-071
draw-072
draw-073
draw-074
draw-075
draw-076
draw-077
draw-078
draw-079
draw-080
draw-081
draw-082
draw-083
draw-084
draw-085
draw-086
draw-087
draw-088
draw-089
draw-090
draw-091
draw-092
draw-093
draw-094
draw-095
draw-096
draw-097
draw-098
draw-099
draw-100

forge-combo29/sol/job39/raw/A/draw-001:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-001/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-001/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-002:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-002/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-002/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-003:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-003/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-003/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-004:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-004/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-004/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-005:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-005/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-005/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-006:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-006/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-006/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-007:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-007/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-007/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-008:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-008/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-008/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-009:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-009/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-009/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-010:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-010/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-010/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-011:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-011/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-011/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-012:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-012/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-012/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-013:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-013/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-013/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-014:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-014/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-014/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-015:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-015/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-015/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-016:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-016/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-016/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-017:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-017/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-017/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-018:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-018/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-018/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-019:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-019/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-019/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-020:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-020/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-020/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-021:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-021/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-021/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-022:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-022/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-022/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-023:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-023/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-023/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-024:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-024/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-024/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-025:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-025/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-025/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-026:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-026/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-026/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-027:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-027/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-027/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-028:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-028/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-028/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-029:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-029/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-029/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-030:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-030/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-030/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-031:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-031/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-031/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-032:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-032/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-032/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-033:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-033/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-033/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-034:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-034/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-034/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-035:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-035/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-035/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-036:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-036/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-036/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-037:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-037/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-037/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-038:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-038/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-038/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-039:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-039/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-039/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-040:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-040/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-040/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-041:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-041/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-041/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-042:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-042/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-042/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-043:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-043/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-043/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-044:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-044/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-044/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-045:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-045/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-045/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-046:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-046/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-046/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-047:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-047/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-047/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-048:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-048/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-048/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-049:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-049/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-049/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-050:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-050/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-050/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-051:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-051/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-051/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-052:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-052/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-052/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-053:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-053/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-053/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-054:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-054/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-054/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-055:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-055/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-055/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-056:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-056/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-056/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-057:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-057/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-057/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-058:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-058/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-058/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-059:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-059/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-059/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-060:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-060/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-060/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-061:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-061/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-061/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-062:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-062/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-062/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-063:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-063/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-063/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-064:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-064/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-064/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-065:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-065/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-065/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-066:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-066/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-066/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-067:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-067/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-067/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-068:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-068/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-068/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-069:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-069/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-069/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-070:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-070/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-070/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-071:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-071/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-071/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-072:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-072/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-072/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-073:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-073/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-073/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-074:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-074/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-074/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-075:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-075/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-075/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-076:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-076/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-076/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-077:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-077/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-077/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-078:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-078/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-078/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-079:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-079/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-079/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-080:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-080/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-080/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-081:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-081/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-081/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-082:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-082/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-082/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-083:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-083/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-083/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-084:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-084/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-084/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-085:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-085/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-085/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-086:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-086/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-086/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-087:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-087/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-087/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-088:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-088/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-088/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-089:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-089/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-089/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-090:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-090/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-090/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-091:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-091/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-091/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-092:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-092/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-092/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-093:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-093/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-093/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-094:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-094/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-094/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-095:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-095/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-095/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-096:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-096/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-096/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-097:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-097/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-097/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-098:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-098/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-098/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-099:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-099/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-099/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-100:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/A/draw-100/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/A/draw-100/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B:
draw-001
draw-002
draw-003
draw-004
draw-005
draw-006
draw-007
draw-008
draw-009
draw-010
draw-011
draw-012
draw-013
draw-014
draw-015
draw-016
draw-017
draw-018
draw-019
draw-020
draw-021
draw-022
draw-023
draw-024
draw-025
draw-026
draw-027
draw-028
draw-029
draw-030
draw-031
draw-032
draw-033
draw-034
draw-035
draw-036
draw-037
draw-038
draw-039
draw-040
draw-041
draw-042
draw-043
draw-044
draw-045
draw-046
draw-047
draw-048
draw-049
draw-050
draw-051
draw-052
draw-053
draw-054
draw-055
draw-056
draw-057
draw-058
draw-059
draw-060
draw-061
draw-062
draw-063
draw-064
draw-065
draw-066
draw-067
draw-068
draw-069
draw-070
draw-071
draw-072
draw-073
draw-074
draw-075
draw-076
draw-077
draw-078
draw-079
draw-080
draw-081
draw-082
draw-083
draw-084
draw-085
draw-086
draw-087
draw-088
draw-089
draw-090
draw-091
draw-092
draw-093
draw-094
draw-095
draw-096
draw-097
draw-098
draw-099
draw-100

forge-combo29/sol/job39/raw/B/draw-001:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-001/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-001/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-002:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-002/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-002/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-003:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-003/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-003/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-004:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-004/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-004/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-005:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-005/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-005/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-006:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-006/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-006/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-007:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-007/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-007/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-008:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-008/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-008/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-009:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-009/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-009/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-010:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-010/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-010/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-011:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-011/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-011/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-012:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-012/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-012/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-013:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-013/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-013/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-014:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-014/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-014/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-015:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-015/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-015/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-016:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-016/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-016/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-017:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-017/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-017/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-018:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-018/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-018/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-019:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-019/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-019/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-020:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-020/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-020/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-021:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-021/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-021/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-022:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-022/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-022/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-023:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-023/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-023/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-024:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-024/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-024/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-025:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-025/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-025/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-026:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-026/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-026/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-027:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-027/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-027/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-028:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-028/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-028/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-029:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-029/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-029/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-030:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-030/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-030/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-031:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-031/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-031/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-032:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-032/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-032/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-033:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-033/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-033/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-034:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-034/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-034/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-035:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-035/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-035/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-036:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-036/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-036/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-037:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-037/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-037/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-038:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-038/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-038/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-039:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-039/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-039/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-040:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-040/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-040/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-041:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-041/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-041/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-042:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-042/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-042/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-043:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-043/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-043/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-044:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-044/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-044/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-045:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-045/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-045/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-046:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-046/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-046/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-047:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-047/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-047/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-048:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-048/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-048/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-049:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-049/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-049/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-050:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-050/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-050/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-051:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-051/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-051/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-052:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-052/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-052/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-053:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-053/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-053/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-054:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-054/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-054/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-055:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-055/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-055/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-056:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-056/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-056/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-057:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-057/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-057/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-058:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-058/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-058/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-059:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-059/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-059/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-060:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-060/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-060/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-061:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-061/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-061/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-062:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-062/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-062/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-063:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-063/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-063/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-064:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-064/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-064/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-065:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-065/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-065/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-066:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-066/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-066/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-067:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-067/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-067/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-068:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-068/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-068/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-069:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-069/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-069/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-070:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-070/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-070/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-071:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-071/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-071/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-072:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-072/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-072/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-073:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-073/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-073/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-074:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-074/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-074/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-075:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-075/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-075/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-076:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-076/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-076/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-077:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-077/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-077/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-078:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-078/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-078/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-079:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-079/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-079/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-080:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-080/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-080/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-081:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-081/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-081/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-082:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-082/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-082/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-083:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-083/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-083/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-084:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-084/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-084/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-085:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-085/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-085/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-086:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-086/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-086/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-087:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-087/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-087/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-088:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-088/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-088/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-089:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-089/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-089/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-090:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-090/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-090/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-091:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-091/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-091/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-092:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-092/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-092/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-093:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-093/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-093/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-094:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-094/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-094/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-095:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-095/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-095/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-096:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-096/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-096/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-097:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-097/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-097/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-098:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-098/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-098/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-099:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-099/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-099/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-100:
kF
kF.driver.out
r15d
r15d.driver.out

forge-combo29/sol/job39/raw/B/draw-100/kF:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/B/draw-100/r15d:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/C39:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/K39a:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/K39b:
records.txt
run.json
uci-setup.txt

forge-combo29/sol/job39/raw/L39:
records.txt
run.json
uci-setup.txt
```

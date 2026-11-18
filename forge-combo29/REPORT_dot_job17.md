# Dot Job17 — partial report after interruption

## 1. Step0 PASS
Unchanged r15d and kF each bench11=312866 nodes, bench13=862329 nodes, go perft5=4865609 nodes, no options/net and freshprocess percommand. Complete raw outputs follow below. Original binary hashes and commands are in those transcripts.

## 2. BranchN
Job16 had no normal-input deterministic disagreement; its deliberately different-settings session control is liveness evidence, not an engine defect. Time/NPS-only differences are explicitly excluded by Job17/new standing definition. Selected next uncovered rows H71 and H12.

## 3. Prepared patches, gates, prediction, runs and map
Claim7ebc5cb4d791ecabbb399554d440dc62f15d4186 at21:00:55UTC. Nativecutoff21:50:55, reportdeadline22:00:55. This report is late after interruption; it does not claim the elapsed time was productive work.
Prediction7cfbcd1bca7d84bdfe4c9bc8f223348b6e82e8fb was committed and readbackverified before ANY countedrun. H71S1uses500000..5000000,S2uses100000..2000000;H12S1uses2000000..40000000,S2uses500000..15000000;all predicted0differences. NOT GRADED: no countedruns occurred.
H71/H12 diagnostic draft sources were prepared in scratch. Count8 build log stops at90% compiling uci.cpp, no successful link/completion, no count8binary. Wrong8build not completed. There is no final tested patch/binary hash to present. DraftH71 patch preserved locally, not offered as validated repair. Common plumbing/H12reference draft unvalidated. No K1,K3,wrongcontrol,S1,S2 was run; no counteruses or zero-difference result claimed. Mapunchanged:28NONE fromJob16, H71/H12 stilluncovered. No newsourcecoverage claim.

## Interruption and verified recovery
At22:11:24UTC recovered localstate: last buildartifact21:04UTC, no finishedbinary, no runningbuild observed. Last visible assistant operation was Step0publication tool aborted after10.1seconds; reason beyond cancellation/interruption is unknown. The first attempted gatefile was independentlychecked404onrecovery, so no send assumedsuccessful. Root requested partialreport and nextjob, not revival of expiredJob17experiments. Alllocaldrafts/logs retained; no reset/cleanup or blindreruns.

## Facts
SixStep0knownanswers passed. Prediction exists. Buildunfinished and experimentsundone. Repositoryengine sourceunchanged. No PR, no otherbranchwrite. Reportembeds completegateevidence and partialbuildlog so those results are actuallycommitted, not merely described asremote.

## Suspicions
Interruption terminated build/toolactivity; exact underlyingcause notestablished. No claim of compilererror or enginebug from incompleteoutput.

## What I did not do
No completedcount8/wrong8build, finalpatchvalidation, countedgates, controls, predictiongrading, S1/S2, newmapcoverage. No binaries/nets/datasets uploaded. No measurements fabricated to fill gaps.

## What I am not sure about
Whether draftinstrumentation compiles/behavescorrectly remains untested. No inference of correctness from partialcompilerprogress.

### What this check cannot see
Positions these scripts do not reach; the PC's net, compiler and build; more than one search thread; Hash sizes
other than 1 and 16.

## Complete Step0 raw evidence

### r15d_bench_11.raw.txt
```text
2026-11-18T21:02:12.659106+00:00
{"label": "r15d", "sha256": "bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6", "options": {}}
> uci
< id name Chess Engine Forge 6.4.24 candidate
< id author OpenAI
< option name Hash type spin default 32 min 1 max 2048
< option name Threads type spin default 1 min 1 max 256
< option name MultiPV type spin default 1 min 1 max 8
< option name Move Overhead type spin default 10 min 0 max 1000
< option name Ponder type check default false
< option name OwnBook type check default true
< option name Book File type string default <empty>
< option name Book Depth type spin default 30 min 0 max 100
< option name Book Variety type spin default 30 min 0 max 100
< option name UseNNUE type check default true
< option name NnueFile type string default <empty>
< option name NNUEArch type check default false
< option name NNUEArchFile type string default <empty>
< option name ContHist4PlyRead type check default false
< option name NonPawnCorrection type check default false
< option name LmrDeeperShallower type check default false
< option name EvalRule50Damp type check default false
< option name ThreatHistory type check default false
< option name LmrSignedCorrection type check default false
< option name LmrLateParentRelief type check default false
< option name HindsightDepth type check default false
< option name NullThreatVerify type check default false
< option name NullSeeVeto type check default false
< option name AspCappedReopen type check default false
< option name AspArmLate type check default false
< option name EvasionOrdering type check default false
< option name DeadMaterial type check default false
< option name QuietExtinction type check default false
< option name DrawJitter type spin default 0 min 0 max 8
< option name TmFinishIteration type check default false
< option name TmNodeShare type check default false
< option name SoundMatePruning type check default false
< option name CuckooRep type check default false
< option name HistRework type spin default 0 min 0 max 3
< option name TtPruneV2 type check default false
< option name CorrHistV2 type check default false
< option name MateAlphaGuard type check default false
< option name LmrQuietBase type spin default 85 min 0 max 300
< option name LmrQuietDivisor type spin default 220 min 100 max 500
< option name LmrNoisyBase type spin default 10 min 0 max 300
< option name LmrNoisyDivisor type spin default 340 min 100 max 800
< option name NullMoveMinDepth type spin default 3 min 1 max 10
< option name NullMoveBase type spin default 3 min 1 max 6
< option name NullMoveDepthDivisor type spin default 3 min 1 max 10
< option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
< option name RfpDepth type spin default 8 min 0 max 15
< option name RfpMargin type spin default 72 min 10 max 300
< option name RfpImproving type spin default 40 min 0 max 200
< option name RazorDepth type spin default 2 min 0 max 6
< option name RazorBase type spin default 150 min 0 max 1000
< option name RazorMultiplier type spin default 350 min 0 max 1000
< option name FutilityDepth type spin default 7 min 0 max 15
< option name FutilityBase type spin default 100 min 0 max 500
< option name FutilityMultiplier type spin default 110 min 0 max 500
< option name LmpBase type spin default 4 min 0 max 20
< option name HistoryPruneDepth type spin default 3 min 0 max 10
< option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
< option name SeeQuietMultiplier type spin default 24 min 0 max 200
< option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
< option name SingularDepth type spin default 7 min 2 max 20
< option name SingularMargin type spin default 2 min 0 max 10
< option name IirDepth type spin default 4 min 1 max 20
< option name ProbcutDepth type spin default 5 min 1 max 20
< option name ProbcutMargin type spin default 180 min 0 max 1000
< option name QsFutilityMargin type spin default 160 min 0 max 1000
< option name QsSeeMargin type spin default 40 min 0 max 500
< option name AspirationDelta type spin default 18 min 4 max 200
< option name HistoryBonusQuadratic type spin default 20 min 0 max 100
< option name HistoryBonusLinear type spin default 48 min 0 max 500
< option name HistoryBonusMax type spin default 2048 min 100 max 10000
< option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
< option name CheckExtensionDepth type spin default 2 min 1 max 30
< option name LmrCutoffThreshold type spin default 3 min 0 max 20
< option name MaterialCorrectionWeight type spin default 100 min 0 max 300
< option name TmSoftDivisor type spin default 22 min 5 max 80
< option name TmIncrementPercent type spin default 75 min 0 max 150
< option name TmHardPercent type spin default 60 min 10 max 95
< option name TmHardSoftMultiple type spin default 5 min 1 max 20
< option name TmStableFactor type spin default 60 min 20 max 150
< option name TmSemiStableFactor type spin default 80 min 20 max 150
< option name TmUnstableFactor type spin default 140 min 50 max 300
< option name TmEffortBase type spin default 155 min 100 max 250
< option name TmFallingEvalPercent type spin default 100 min 0 max 400
< option name TmMinFactorPercent type spin default 45 min 10 max 100
< option name CaptureFutilityBase type spin default 0 min 0 max 1000
< option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
< option name CaptureFutilityDepth type spin default 6 min 0 max 15
< option name FailLowContinuationBonus type spin default 0 min 0 max 300
< option name AspFailHighReduce type spin default 0 min 0 max 1
< option name AspFailHighMaxReduce type spin default 3 min 1 max 6
< option name EvalSwingMult type spin default 0 min 0 max 64
< option name EvalSwingMax type spin default 200 min 50 max 400
< option name TtCutoffHistory type spin default 0 min 0 max 1
< option name Clear Hash type button
< uciok
> isready
< readyok
> bench 11
< info string bench depth 11 nodes 312866 time 262 nps 1194145
> quit
```

### r15d_bench_13.raw.txt
```text
2026-11-18T21:02:13.036039+00:00
{"label": "r15d", "sha256": "bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6", "options": {}}
> uci
< id name Chess Engine Forge 6.4.24 candidate
< id author OpenAI
< option name Hash type spin default 32 min 1 max 2048
< option name Threads type spin default 1 min 1 max 256
< option name MultiPV type spin default 1 min 1 max 8
< option name Move Overhead type spin default 10 min 0 max 1000
< option name Ponder type check default false
< option name OwnBook type check default true
< option name Book File type string default <empty>
< option name Book Depth type spin default 30 min 0 max 100
< option name Book Variety type spin default 30 min 0 max 100
< option name UseNNUE type check default true
< option name NnueFile type string default <empty>
< option name NNUEArch type check default false
< option name NNUEArchFile type string default <empty>
< option name ContHist4PlyRead type check default false
< option name NonPawnCorrection type check default false
< option name LmrDeeperShallower type check default false
< option name EvalRule50Damp type check default false
< option name ThreatHistory type check default false
< option name LmrSignedCorrection type check default false
< option name LmrLateParentRelief type check default false
< option name HindsightDepth type check default false
< option name NullThreatVerify type check default false
< option name NullSeeVeto type check default false
< option name AspCappedReopen type check default false
< option name AspArmLate type check default false
< option name EvasionOrdering type check default false
< option name DeadMaterial type check default false
< option name QuietExtinction type check default false
< option name DrawJitter type spin default 0 min 0 max 8
< option name TmFinishIteration type check default false
< option name TmNodeShare type check default false
< option name SoundMatePruning type check default false
< option name CuckooRep type check default false
< option name HistRework type spin default 0 min 0 max 3
< option name TtPruneV2 type check default false
< option name CorrHistV2 type check default false
< option name MateAlphaGuard type check default false
< option name LmrQuietBase type spin default 85 min 0 max 300
< option name LmrQuietDivisor type spin default 220 min 100 max 500
< option name LmrNoisyBase type spin default 10 min 0 max 300
< option name LmrNoisyDivisor type spin default 340 min 100 max 800
< option name NullMoveMinDepth type spin default 3 min 1 max 10
< option name NullMoveBase type spin default 3 min 1 max 6
< option name NullMoveDepthDivisor type spin default 3 min 1 max 10
< option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
< option name RfpDepth type spin default 8 min 0 max 15
< option name RfpMargin type spin default 72 min 10 max 300
< option name RfpImproving type spin default 40 min 0 max 200
< option name RazorDepth type spin default 2 min 0 max 6
< option name RazorBase type spin default 150 min 0 max 1000
< option name RazorMultiplier type spin default 350 min 0 max 1000
< option name FutilityDepth type spin default 7 min 0 max 15
< option name FutilityBase type spin default 100 min 0 max 500
< option name FutilityMultiplier type spin default 110 min 0 max 500
< option name LmpBase type spin default 4 min 0 max 20
< option name HistoryPruneDepth type spin default 3 min 0 max 10
< option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
< option name SeeQuietMultiplier type spin default 24 min 0 max 200
< option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
< option name SingularDepth type spin default 7 min 2 max 20
< option name SingularMargin type spin default 2 min 0 max 10
< option name IirDepth type spin default 4 min 1 max 20
< option name ProbcutDepth type spin default 5 min 1 max 20
< option name ProbcutMargin type spin default 180 min 0 max 1000
< option name QsFutilityMargin type spin default 160 min 0 max 1000
< option name QsSeeMargin type spin default 40 min 0 max 500
< option name AspirationDelta type spin default 18 min 4 max 200
< option name HistoryBonusQuadratic type spin default 20 min 0 max 100
< option name HistoryBonusLinear type spin default 48 min 0 max 500
< option name HistoryBonusMax type spin default 2048 min 100 max 10000
< option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
< option name CheckExtensionDepth type spin default 2 min 1 max 30
< option name LmrCutoffThreshold type spin default 3 min 0 max 20
< option name MaterialCorrectionWeight type spin default 100 min 0 max 300
< option name TmSoftDivisor type spin default 22 min 5 max 80
< option name TmIncrementPercent type spin default 75 min 0 max 150
< option name TmHardPercent type spin default 60 min 10 max 95
< option name TmHardSoftMultiple type spin default 5 min 1 max 20
< option name TmStableFactor type spin default 60 min 20 max 150
< option name TmSemiStableFactor type spin default 80 min 20 max 150
< option name TmUnstableFactor type spin default 140 min 50 max 300
< option name TmEffortBase type spin default 155 min 100 max 250
< option name TmFallingEvalPercent type spin default 100 min 0 max 400
< option name TmMinFactorPercent type spin default 45 min 10 max 100
< option name CaptureFutilityBase type spin default 0 min 0 max 1000
< option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
< option name CaptureFutilityDepth type spin default 6 min 0 max 15
< option name FailLowContinuationBonus type spin default 0 min 0 max 300
< option name AspFailHighReduce type spin default 0 min 0 max 1
< option name AspFailHighMaxReduce type spin default 3 min 1 max 6
< option name EvalSwingMult type spin default 0 min 0 max 64
< option name EvalSwingMax type spin default 200 min 50 max 400
< option name TtCutoffHistory type spin default 0 min 0 max 1
< option name Clear Hash type button
< uciok
> isready
< readyok
> bench 13
< info string bench depth 13 nodes 862329 time 583 nps 1479123
> quit
```

### r15d_go_perft_5.raw.txt
```text
2026-11-18T21:02:13.735737+00:00
{"label": "r15d", "sha256": "bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6", "options": {}}
> uci
< id name Chess Engine Forge 6.4.24 candidate
< id author OpenAI
< option name Hash type spin default 32 min 1 max 2048
< option name Threads type spin default 1 min 1 max 256
< option name MultiPV type spin default 1 min 1 max 8
< option name Move Overhead type spin default 10 min 0 max 1000
< option name Ponder type check default false
< option name OwnBook type check default true
< option name Book File type string default <empty>
< option name Book Depth type spin default 30 min 0 max 100
< option name Book Variety type spin default 30 min 0 max 100
< option name UseNNUE type check default true
< option name NnueFile type string default <empty>
< option name NNUEArch type check default false
< option name NNUEArchFile type string default <empty>
< option name ContHist4PlyRead type check default false
< option name NonPawnCorrection type check default false
< option name LmrDeeperShallower type check default false
< option name EvalRule50Damp type check default false
< option name ThreatHistory type check default false
< option name LmrSignedCorrection type check default false
< option name LmrLateParentRelief type check default false
< option name HindsightDepth type check default false
< option name NullThreatVerify type check default false
< option name NullSeeVeto type check default false
< option name AspCappedReopen type check default false
< option name AspArmLate type check default false
< option name EvasionOrdering type check default false
< option name DeadMaterial type check default false
< option name QuietExtinction type check default false
< option name DrawJitter type spin default 0 min 0 max 8
< option name TmFinishIteration type check default false
< option name TmNodeShare type check default false
< option name SoundMatePruning type check default false
< option name CuckooRep type check default false
< option name HistRework type spin default 0 min 0 max 3
< option name TtPruneV2 type check default false
< option name CorrHistV2 type check default false
< option name MateAlphaGuard type check default false
< option name LmrQuietBase type spin default 85 min 0 max 300
< option name LmrQuietDivisor type spin default 220 min 100 max 500
< option name LmrNoisyBase type spin default 10 min 0 max 300
< option name LmrNoisyDivisor type spin default 340 min 100 max 800
< option name NullMoveMinDepth type spin default 3 min 1 max 10
< option name NullMoveBase type spin default 3 min 1 max 6
< option name NullMoveDepthDivisor type spin default 3 min 1 max 10
< option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
< option name RfpDepth type spin default 8 min 0 max 15
< option name RfpMargin type spin default 72 min 10 max 300
< option name RfpImproving type spin default 40 min 0 max 200
< option name RazorDepth type spin default 2 min 0 max 6
< option name RazorBase type spin default 150 min 0 max 1000
< option name RazorMultiplier type spin default 350 min 0 max 1000
< option name FutilityDepth type spin default 7 min 0 max 15
< option name FutilityBase type spin default 100 min 0 max 500
< option name FutilityMultiplier type spin default 110 min 0 max 500
< option name LmpBase type spin default 4 min 0 max 20
< option name HistoryPruneDepth type spin default 3 min 0 max 10
< option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
< option name SeeQuietMultiplier type spin default 24 min 0 max 200
< option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
< option name SingularDepth type spin default 7 min 2 max 20
< option name SingularMargin type spin default 2 min 0 max 10
< option name IirDepth type spin default 4 min 1 max 20
< option name ProbcutDepth type spin default 5 min 1 max 20
< option name ProbcutMargin type spin default 180 min 0 max 1000
< option name QsFutilityMargin type spin default 160 min 0 max 1000
< option name QsSeeMargin type spin default 40 min 0 max 500
< option name AspirationDelta type spin default 18 min 4 max 200
< option name HistoryBonusQuadratic type spin default 20 min 0 max 100
< option name HistoryBonusLinear type spin default 48 min 0 max 500
< option name HistoryBonusMax type spin default 2048 min 100 max 10000
< option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
< option name CheckExtensionDepth type spin default 2 min 1 max 30
< option name LmrCutoffThreshold type spin default 3 min 0 max 20
< option name MaterialCorrectionWeight type spin default 100 min 0 max 300
< option name TmSoftDivisor type spin default 22 min 5 max 80
< option name TmIncrementPercent type spin default 75 min 0 max 150
< option name TmHardPercent type spin default 60 min 10 max 95
< option name TmHardSoftMultiple type spin default 5 min 1 max 20
< option name TmStableFactor type spin default 60 min 20 max 150
< option name TmSemiStableFactor type spin default 80 min 20 max 150
< option name TmUnstableFactor type spin default 140 min 50 max 300
< option name TmEffortBase type spin default 155 min 100 max 250
< option name TmFallingEvalPercent type spin default 100 min 0 max 400
< option name TmMinFactorPercent type spin default 45 min 10 max 100
< option name CaptureFutilityBase type spin default 0 min 0 max 1000
< option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
< option name CaptureFutilityDepth type spin default 6 min 0 max 15
< option name FailLowContinuationBonus type spin default 0 min 0 max 300
< option name AspFailHighReduce type spin default 0 min 0 max 1
< option name AspFailHighMaxReduce type spin default 3 min 1 max 6
< option name EvalSwingMult type spin default 0 min 0 max 64
< option name EvalSwingMax type spin default 200 min 50 max 400
< option name TtCutoffHistory type spin default 0 min 0 max 1
< option name Clear Hash type button
< uciok
> isready
< readyok
> go perft 5
< a2a3: 181046
< b2b3: 215255
< c2c3: 222861
< d2d3: 328511
< e2e3: 402988
< f2f3: 178889
< g2g3: 217210
< h2h3: 181044
< a2a4: 217832
< b2b4: 216145
< c2c4: 240082
< d2d4: 361790
< e2e4: 405385
< f2f4: 198473
< g2g4: 214048
< h2h4: 218829
< b1a3: 198572
< b1c3: 234656
< g1f3: 233491
< g1h3: 198502
< nodes 4865609
> quit
```

### kf_bench_11.raw.txt
```text
2026-11-18T21:02:13.873538+00:00
{"label": "kf", "sha256": "340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea", "options": {}}
> uci
< id name Chess Engine Forge 6.4.24 candidate
< id author OpenAI
< option name Hash type spin default 32 min 1 max 2048
< option name Threads type spin default 1 min 1 max 256
< option name MultiPV type spin default 1 min 1 max 8
< option name Move Overhead type spin default 10 min 0 max 1000
< option name Ponder type check default false
< option name OwnBook type check default true
< option name Book File type string default <empty>
< option name Book Depth type spin default 30 min 0 max 100
< option name Book Variety type spin default 30 min 0 max 100
< option name UseNNUE type check default true
< option name NnueFile type string default <empty>
< option name NNUEArch type check default false
< option name NNUEArchFile type string default <empty>
< option name ContHist4PlyRead type check default false
< option name NonPawnCorrection type check default false
< option name LmrDeeperShallower type check default false
< option name EvalRule50Damp type check default false
< option name ThreatHistory type check default false
< option name LmrSignedCorrection type check default false
< option name LmrLateParentRelief type check default false
< option name HindsightDepth type check default false
< option name NullThreatVerify type check default false
< option name NullSeeVeto type check default false
< option name AspCappedReopen type check default false
< option name AspArmLate type check default false
< option name EvasionOrdering type check default false
< option name DeadMaterial type check default false
< option name QuietExtinction type check default false
< option name DrawJitter type spin default 0 min 0 max 8
< option name TmFinishIteration type check default false
< option name TmNodeShare type check default false
< option name SoundMatePruning type check default false
< option name CuckooRep type check default false
< option name HistRework type spin default 0 min 0 max 3
< option name TtPruneV2 type check default false
< option name CorrHistV2 type check default false
< option name MateAlphaGuard type check default false
< option name LmrQuietBase type spin default 85 min 0 max 300
< option name LmrQuietDivisor type spin default 220 min 100 max 500
< option name LmrNoisyBase type spin default 10 min 0 max 300
< option name LmrNoisyDivisor type spin default 340 min 100 max 800
< option name NullMoveMinDepth type spin default 3 min 1 max 10
< option name NullMoveBase type spin default 3 min 1 max 6
< option name NullMoveDepthDivisor type spin default 3 min 1 max 10
< option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
< option name RfpDepth type spin default 8 min 0 max 15
< option name RfpMargin type spin default 72 min 10 max 300
< option name RfpImproving type spin default 40 min 0 max 200
< option name RazorDepth type spin default 2 min 0 max 6
< option name RazorBase type spin default 150 min 0 max 1000
< option name RazorMultiplier type spin default 350 min 0 max 1000
< option name FutilityDepth type spin default 7 min 0 max 15
< option name FutilityBase type spin default 100 min 0 max 500
< option name FutilityMultiplier type spin default 110 min 0 max 500
< option name LmpBase type spin default 4 min 0 max 20
< option name HistoryPruneDepth type spin default 3 min 0 max 10
< option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
< option name SeeQuietMultiplier type spin default 24 min 0 max 200
< option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
< option name SingularDepth type spin default 7 min 2 max 20
< option name SingularMargin type spin default 2 min 0 max 10
< option name IirDepth type spin default 4 min 1 max 20
< option name ProbcutDepth type spin default 5 min 1 max 20
< option name ProbcutMargin type spin default 180 min 0 max 1000
< option name QsFutilityMargin type spin default 160 min 0 max 1000
< option name QsSeeMargin type spin default 40 min 0 max 500
< option name AspirationDelta type spin default 18 min 4 max 200
< option name HistoryBonusQuadratic type spin default 20 min 0 max 100
< option name HistoryBonusLinear type spin default 48 min 0 max 500
< option name HistoryBonusMax type spin default 2048 min 100 max 10000
< option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
< option name CheckExtensionDepth type spin default 2 min 1 max 30
< option name LmrCutoffThreshold type spin default 3 min 0 max 20
< option name MaterialCorrectionWeight type spin default 100 min 0 max 300
< option name TmSoftDivisor type spin default 22 min 5 max 80
< option name TmIncrementPercent type spin default 75 min 0 max 150
< option name TmHardPercent type spin default 60 min 10 max 95
< option name TmHardSoftMultiple type spin default 5 min 1 max 20
< option name TmStableFactor type spin default 60 min 20 max 150
< option name TmSemiStableFactor type spin default 80 min 20 max 150
< option name TmUnstableFactor type spin default 140 min 50 max 300
< option name TmEffortBase type spin default 155 min 100 max 250
< option name TmFallingEvalPercent type spin default 100 min 0 max 400
< option name TmMinFactorPercent type spin default 45 min 10 max 100
< option name CaptureFutilityBase type spin default 0 min 0 max 1000
< option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
< option name CaptureFutilityDepth type spin default 6 min 0 max 15
< option name FailLowContinuationBonus type spin default 0 min 0 max 300
< option name AspFailHighReduce type spin default 0 min 0 max 1
< option name AspFailHighMaxReduce type spin default 3 min 1 max 6
< option name EvalSwingMult type spin default 0 min 0 max 64
< option name EvalSwingMax type spin default 200 min 50 max 400
< option name TtCutoffHistory type spin default 0 min 0 max 1
< option name Clear Hash type button
< uciok
> isready
< readyok
> bench 11
< info string bench depth 11 nodes 312866 time 190 nps 1646663
> quit
```

### kf_bench_13.raw.txt
```text
2026-11-18T21:02:14.082061+00:00
{"label": "kf", "sha256": "340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea", "options": {}}
> uci
< id name Chess Engine Forge 6.4.24 candidate
< id author OpenAI
< option name Hash type spin default 32 min 1 max 2048
< option name Threads type spin default 1 min 1 max 256
< option name MultiPV type spin default 1 min 1 max 8
< option name Move Overhead type spin default 10 min 0 max 1000
< option name Ponder type check default false
< option name OwnBook type check default true
< option name Book File type string default <empty>
< option name Book Depth type spin default 30 min 0 max 100
< option name Book Variety type spin default 30 min 0 max 100
< option name UseNNUE type check default true
< option name NnueFile type string default <empty>
< option name NNUEArch type check default false
< option name NNUEArchFile type string default <empty>
< option name ContHist4PlyRead type check default false
< option name NonPawnCorrection type check default false
< option name LmrDeeperShallower type check default false
< option name EvalRule50Damp type check default false
< option name ThreatHistory type check default false
< option name LmrSignedCorrection type check default false
< option name LmrLateParentRelief type check default false
< option name HindsightDepth type check default false
< option name NullThreatVerify type check default false
< option name NullSeeVeto type check default false
< option name AspCappedReopen type check default false
< option name AspArmLate type check default false
< option name EvasionOrdering type check default false
< option name DeadMaterial type check default false
< option name QuietExtinction type check default false
< option name DrawJitter type spin default 0 min 0 max 8
< option name TmFinishIteration type check default false
< option name TmNodeShare type check default false
< option name SoundMatePruning type check default false
< option name CuckooRep type check default false
< option name HistRework type spin default 0 min 0 max 3
< option name TtPruneV2 type check default false
< option name CorrHistV2 type check default false
< option name MateAlphaGuard type check default false
< option name LmrQuietBase type spin default 85 min 0 max 300
< option name LmrQuietDivisor type spin default 220 min 100 max 500
< option name LmrNoisyBase type spin default 10 min 0 max 300
< option name LmrNoisyDivisor type spin default 340 min 100 max 800
< option name NullMoveMinDepth type spin default 3 min 1 max 10
< option name NullMoveBase type spin default 3 min 1 max 6
< option name NullMoveDepthDivisor type spin default 3 min 1 max 10
< option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
< option name RfpDepth type spin default 8 min 0 max 15
< option name RfpMargin type spin default 72 min 10 max 300
< option name RfpImproving type spin default 40 min 0 max 200
< option name RazorDepth type spin default 2 min 0 max 6
< option name RazorBase type spin default 150 min 0 max 1000
< option name RazorMultiplier type spin default 350 min 0 max 1000
< option name FutilityDepth type spin default 7 min 0 max 15
< option name FutilityBase type spin default 100 min 0 max 500
< option name FutilityMultiplier type spin default 110 min 0 max 500
< option name LmpBase type spin default 4 min 0 max 20
< option name HistoryPruneDepth type spin default 3 min 0 max 10
< option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
< option name SeeQuietMultiplier type spin default 24 min 0 max 200
< option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
< option name SingularDepth type spin default 7 min 2 max 20
< option name SingularMargin type spin default 2 min 0 max 10
< option name IirDepth type spin default 4 min 1 max 20
< option name ProbcutDepth type spin default 5 min 1 max 20
< option name ProbcutMargin type spin default 180 min 0 max 1000
< option name QsFutilityMargin type spin default 160 min 0 max 1000
< option name QsSeeMargin type spin default 40 min 0 max 500
< option name AspirationDelta type spin default 18 min 4 max 200
< option name HistoryBonusQuadratic type spin default 20 min 0 max 100
< option name HistoryBonusLinear type spin default 48 min 0 max 500
< option name HistoryBonusMax type spin default 2048 min 100 max 10000
< option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
< option name CheckExtensionDepth type spin default 2 min 1 max 30
< option name LmrCutoffThreshold type spin default 3 min 0 max 20
< option name MaterialCorrectionWeight type spin default 100 min 0 max 300
< option name TmSoftDivisor type spin default 22 min 5 max 80
< option name TmIncrementPercent type spin default 75 min 0 max 150
< option name TmHardPercent type spin default 60 min 10 max 95
< option name TmHardSoftMultiple type spin default 5 min 1 max 20
< option name TmStableFactor type spin default 60 min 20 max 150
< option name TmSemiStableFactor type spin default 80 min 20 max 150
< option name TmUnstableFactor type spin default 140 min 50 max 300
< option name TmEffortBase type spin default 155 min 100 max 250
< option name TmFallingEvalPercent type spin default 100 min 0 max 400
< option name TmMinFactorPercent type spin default 45 min 10 max 100
< option name CaptureFutilityBase type spin default 0 min 0 max 1000
< option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
< option name CaptureFutilityDepth type spin default 6 min 0 max 15
< option name FailLowContinuationBonus type spin default 0 min 0 max 300
< option name AspFailHighReduce type spin default 0 min 0 max 1
< option name AspFailHighMaxReduce type spin default 3 min 1 max 6
< option name EvalSwingMult type spin default 0 min 0 max 64
< option name EvalSwingMax type spin default 200 min 50 max 400
< option name TtCutoffHistory type spin default 0 min 0 max 1
< option name Clear Hash type button
< uciok
> isready
< readyok
> bench 13
< info string bench depth 13 nodes 862329 time 508 nps 1697498
> quit
```

### kf_go_perft_5.raw.txt
```text
2026-11-18T21:02:14.607940+00:00
{"label": "kf", "sha256": "340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea", "options": {}}
> uci
< id name Chess Engine Forge 6.4.24 candidate
< id author OpenAI
< option name Hash type spin default 32 min 1 max 2048
< option name Threads type spin default 1 min 1 max 256
< option name MultiPV type spin default 1 min 1 max 8
< option name Move Overhead type spin default 10 min 0 max 1000
< option name Ponder type check default false
< option name OwnBook type check default true
< option name Book File type string default <empty>
< option name Book Depth type spin default 30 min 0 max 100
< option name Book Variety type spin default 30 min 0 max 100
< option name UseNNUE type check default true
< option name NnueFile type string default <empty>
< option name NNUEArch type check default false
< option name NNUEArchFile type string default <empty>
< option name ContHist4PlyRead type check default false
< option name NonPawnCorrection type check default false
< option name LmrDeeperShallower type check default false
< option name EvalRule50Damp type check default false
< option name ThreatHistory type check default false
< option name LmrSignedCorrection type check default false
< option name LmrLateParentRelief type check default false
< option name HindsightDepth type check default false
< option name NullThreatVerify type check default false
< option name NullSeeVeto type check default false
< option name AspCappedReopen type check default false
< option name AspArmLate type check default false
< option name EvasionOrdering type check default false
< option name DeadMaterial type check default false
< option name QuietExtinction type check default false
< option name DrawJitter type spin default 0 min 0 max 8
< option name TmFinishIteration type check default false
< option name TmNodeShare type check default false
< option name SoundMatePruning type check default false
< option name CuckooRep type check default false
< option name HistRework type spin default 0 min 0 max 3
< option name TtPruneV2 type check default false
< option name CorrHistV2 type check default false
< option name MateAlphaGuard type check default false
< option name LmrQuietBase type spin default 85 min 0 max 300
< option name LmrQuietDivisor type spin default 220 min 100 max 500
< option name LmrNoisyBase type spin default 10 min 0 max 300
< option name LmrNoisyDivisor type spin default 340 min 100 max 800
< option name NullMoveMinDepth type spin default 3 min 1 max 10
< option name NullMoveBase type spin default 3 min 1 max 6
< option name NullMoveDepthDivisor type spin default 3 min 1 max 10
< option name NullMoveEvalDivisor type spin default 200 min 50 max 1000
< option name RfpDepth type spin default 8 min 0 max 15
< option name RfpMargin type spin default 72 min 10 max 300
< option name RfpImproving type spin default 40 min 0 max 200
< option name RazorDepth type spin default 2 min 0 max 6
< option name RazorBase type spin default 150 min 0 max 1000
< option name RazorMultiplier type spin default 350 min 0 max 1000
< option name FutilityDepth type spin default 7 min 0 max 15
< option name FutilityBase type spin default 100 min 0 max 500
< option name FutilityMultiplier type spin default 110 min 0 max 500
< option name LmpBase type spin default 4 min 0 max 20
< option name HistoryPruneDepth type spin default 3 min 0 max 10
< option name HistoryPruneMultiplier type spin default 2048 min 0 max 20000
< option name SeeQuietMultiplier type spin default 24 min 0 max 200
< option name SeeNoisyMultiplier type spin default 150 min 0 max 1000
< option name SingularDepth type spin default 7 min 2 max 20
< option name SingularMargin type spin default 2 min 0 max 10
< option name IirDepth type spin default 4 min 1 max 20
< option name ProbcutDepth type spin default 5 min 1 max 20
< option name ProbcutMargin type spin default 180 min 0 max 1000
< option name QsFutilityMargin type spin default 160 min 0 max 1000
< option name QsSeeMargin type spin default 40 min 0 max 500
< option name AspirationDelta type spin default 18 min 4 max 200
< option name HistoryBonusQuadratic type spin default 20 min 0 max 100
< option name HistoryBonusLinear type spin default 48 min 0 max 500
< option name HistoryBonusMax type spin default 2048 min 100 max 10000
< option name LmrHistoryDivisor type spin default 6000 min 1000 max 30000
< option name CheckExtensionDepth type spin default 2 min 1 max 30
< option name LmrCutoffThreshold type spin default 3 min 0 max 20
< option name MaterialCorrectionWeight type spin default 100 min 0 max 300
< option name TmSoftDivisor type spin default 22 min 5 max 80
< option name TmIncrementPercent type spin default 75 min 0 max 150
< option name TmHardPercent type spin default 60 min 10 max 95
< option name TmHardSoftMultiple type spin default 5 min 1 max 20
< option name TmStableFactor type spin default 60 min 20 max 150
< option name TmSemiStableFactor type spin default 80 min 20 max 150
< option name TmUnstableFactor type spin default 140 min 50 max 300
< option name TmEffortBase type spin default 155 min 100 max 250
< option name TmFallingEvalPercent type spin default 100 min 0 max 400
< option name TmMinFactorPercent type spin default 45 min 10 max 100
< option name CaptureFutilityBase type spin default 0 min 0 max 1000
< option name CaptureFutilityMultiplier type spin default 250 min 0 max 1000
< option name CaptureFutilityDepth type spin default 6 min 0 max 15
< option name FailLowContinuationBonus type spin default 0 min 0 max 300
< option name AspFailHighReduce type spin default 0 min 0 max 1
< option name AspFailHighMaxReduce type spin default 3 min 1 max 6
< option name EvalSwingMult type spin default 0 min 0 max 64
< option name EvalSwingMax type spin default 200 min 50 max 400
< option name TtCutoffHistory type spin default 0 min 0 max 1
< option name Clear Hash type button
< uciok
> isready
< readyok
> go perft 5
< a2a3: 181046
< b2b3: 215255
< c2c3: 222861
< d2d3: 328511
< e2e3: 402988
< f2f3: 178889
< g2g3: 217210
< h2h3: 181044
< a2a4: 217832
< b2b4: 216145
< c2c4: 240082
< d2d4: 361790
< e2e4: 405385
< f2f4: 198473
< g2g4: 214048
< h2h4: 218829
< b1a3: 198572
< b1c3: 234656
< g1f3: 233491
< g1h3: 198502
< nodes 4865609
> quit
```

## Partial build output, not a completed build
```text
[ 10%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 20%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 30%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 40%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 50%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 60%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 70%] Building CXX object CMakeFiles/forge.dir/src/nnue_v3.cpp.o
[ 80%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 90%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
```

## Last command before report commit
```text
git status --short; ls -R forge-combo29/dot/job17
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/REPORT_dot_job10.md
?? forge-combo29/REPORT_dot_job11.md
?? forge-combo29/REPORT_dot_job12.md
?? forge-combo29/REPORT_dot_job13.md
?? forge-combo29/REPORT_dot_job14.md
?? forge-combo29/REPORT_dot_job15.md
?? forge-combo29/REPORT_dot_job16.md
?? forge-combo29/REPORT_dot_job17.md
?? forge-combo29/REPORT_dot_job6.md
?? forge-combo29/REPORT_dot_job7.md
?? forge-combo29/REPORT_dot_job8.md
?? forge-combo29/REPORT_dot_job9.md
?? forge-combo29/dot/job10/
?? forge-combo29/dot/job11/
?? forge-combo29/dot/job12/
?? forge-combo29/dot/job13/
?? forge-combo29/dot/job14/
?? forge-combo29/dot/job15/
?? forge-combo29/dot/job16/
?? forge-combo29/dot/job17/
?? forge-combo29/dot/job2/K1_base_count_search_extract.txt
?? forge-combo29/dot/job2/K1_base_diagnostic_gate.raw.txt
?? forge-combo29/dot/job2/K1_base_plain_search_extract.txt
?? forge-combo29/dot/job2/K1_matrix.py.txt
?? forge-combo29/dot/job2/K1_matrix_console.txt
?? forge-combo29/dot/job2/K1_pc_count_search_extract.txt
?? forge-combo29/dot/job2/K1_pc_diagnostic_gate.raw.txt
?? forge-combo29/dot/job2/K1_pc_plain_search_extract.txt
?? forge-combo29/dot/job2/K1_summary.json.txt
?? forge-combo29/dot/job2/K2_analysis.txt
?? forge-combo29/dot/job2/K2_base_raw.txt
?? forge-combo29/dot/job2/K2_base_search_extract.txt
?? forge-combo29/dot/job2/K2_cap.py.txt
?? forge-combo29/dot/job2/K2_console.txt
?? forge-combo29/dot/job2/K2_fault_replay.py.txt
?? forge-combo29/dot/job2/K2_fault_result.txt
?? forge-combo29/dot/job2/K2_pc_raw.txt
?? forge-combo29/dot/job2/K2_pc_search_extract.txt
?? forge-combo29/dot/job2/K2_replay_count.raw.txt
?? forge-combo29/dot/job2/K2_replay_fault.raw.txt
?? forge-combo29/dot/job2/K2_replay_plain.raw.txt
?? forge-combo29/dot/job2/K2_summary.json.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_only.patch.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/manifest.sha256.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_only.patch.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_planted_overrun.patch.txt
?? forge-combo29/dot/job3/
?? forge-combo29/dot/job4/
?? forge-combo29/dot/job5/
?? forge-combo29/dot/job6/
?? forge-combo29/dot/job7/
?? forge-combo29/dot/job8/
?? forge-combo29/dot/job9/
forge-combo29/dot/job17:
C_count8_build.txt
C_count8_configure.txt
gate_summary.txt
kf_bench_11.raw.txt
kf_bench_13.raw.txt
kf_go_perft_5.raw.txt
r15d_bench_11.raw.txt
r15d_bench_13.raw.txt
r15d_go_perft_5.raw.txt
```

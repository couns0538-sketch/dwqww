# R3-2 Interaction matrix: every option and switch alone + TT / correction / NNUE pairs (bench nodes, CPU NPS) — DONE

Branch `opus-r3-matrix` = `2432670b` (opus-r3-stack@467a59b3 + CMake test fix) + `5af1b666` (tools) + merges of opus-r3-stack `2047348a` and of the final R3-1 head `330237f3` + `0eb5432e` (evidence) + `1d59d082` (docs). There is no engine change: `git diff 330237f3 HEAD -- src include tests tools CMakeLists.txt .github` is empty. All commits are `[skip ci]`; no CI run was triggered. No Elo or speed claim. **Machine exclusive: no** (the PC ran at about 98% total CPU). Every NPS figure is advisory.

**Which head each number comes from:**
- Rows without a mark come from exes built from `2432670b` (stack `467a59b3`).
- Rows marked [330237f3] come from the final head and are timed against that head's own OFF exe, `base_h3.exe`.
- The final head's default build is not byte-identical to the first pass. It has the same size but 1,383,599 differing bytes, because the HardDeadline fix added output checks and one atomic member. It runs 4.61% [-5.20, -4.01] slower (row H3DRIFT, see the layout finding).
- First-pass rows therefore describe 467a59b3; runtime-option rows were not re-run at 330237f3.

## Acceptance

| line | result | evidence |
|---|---|---|
| 1. Measurement script: bench nodes d11/13/16; CPU-time NPS, paired ABBA against the all-OFF engine, fresh processes, ≥ 6 runs per side, 95% CI; nice 19; single-threaded except the Threads=2 runs | **DONE**. `r3_matrix.py`, adapted from sol_S29 `nps_ab.py` and sol_SIT `nps_ab_opts.py`: 8 ABBA pairs per configuration (16 for the NOZERO/O2 confirmation); paired t interval on the per-pair log ratios (Welch kept in the notes); every engine at IDLE priority under `nice -n 19`; CPU time taken around the measured command only, so start-up and net loading are excluded | `r3_matrix.py`, `README.md`, `logs/nps.log` |
| 2. Configurations: every runtime option alone, every compile switch alone, TT group at T1 and T2, correction pairs + triple, NNUE pairs + all four | **DONE**. 71 configurations, listed in `configs()` of `r3_matrix.py`. CorrHistPlus=7 is the correction representative in the pairs; THR+PP+OB8 is added so O2's part in the all-four can be isolated. Extra shared-code pairs: CuckooRep with CM/CE (the instance matrix), HR2+CHP7, IT+CR, SPEEDSTACK+MKT, SPEEDSTACK+TtChildPrefetch, NetScale+v2 | `logs/nodes*.log`, `logs/nps*.log`, `logs/results/` |
| 3. Per pair: node consistency, NPS additivity, conflicts / cancels with CIs, A/A controls | **DONE**. A/A T1 +0.06% [-0.66, +0.77]; A/A T2 +0.65% [-1.81, +3.17] | `logs/matrix_tables_cycles.md` |
| 4. REPORT.md: one matrix table, pair analysis, flagged pairs | this file | — |
| Newer heads (coordinator) | 2047348a and the final 330237f3 merged. NnueLazyAcc, FORGE_PROF (diagnostic) and NnueInt16 added as single configurations, plus same-code pairs: O2×NnueLazyAcc, NnueLazyAcc×v2, O2×NnueInt16, NnueInt16×NnueLazyAcc, NnueInt16×v2, FORGE_PROF×(CM+CE) | `logs/build_final_head.log`, `logs/nodes_h3.log`, `logs/nps_h3.log` |
| Every exe at the lock pins with options off; FMA 0 | **PASS**. 7 first-pass exes (base `--full`) and 8 final-head exes (base_h3 `--full`): ALL OK, FMA 0 | `logs/build_all.log`, `logs/build_final_head.log` |

## Findings

### Conflicts: none
- All 1152 NPS runs and 130 node-count processes exited with status 0. None printed an ERROR line after `readyok`, and none hit a fail-loud exit.
- The ERROR lines that do appear are transient. A v2 request is half-set while the options arrive one at a time, and it is resolved before `readyok`: one line per request option sent before NNUEFile. Every v2 configuration then printed its "active" line with the expected net features.
- Bench node counts at Threads=1 were identical in both fresh processes for every configuration.
- Every node rule holds:
  - Every node-exact option, switch or replica alone equals the lock pins. So does every combination of node-exact parts: the TT pairs at Threads=1, the SPEEDSTACK pairs, all eight v2 replica combinations including O2, and the NnueLazyAcc / FORGE_PROF combinations.
  - One tree-changing part plus node-exact parts gives exactly that part's tree:
    - IntendedThreefold + CuckooRep = CuckooRep.
    - FORGE_PROF counting inside the CorrMargins+CorrExt instance = CM+CE (333285 / 903735 / 2610911).
    - O2 + NnueInt16 = NnueInt16 + NnueLazyAcc = NnueInt16 (330610 / 858175 / 2760596). The null-move alias drives the int16 accumulators node-exactly.
  - All eight correction and instance combinations form a new tree that differs from OFF and from every part at d11, d13 and d16: CHP7+CM, CHP7+CE, CM+CE, CHP7+CM+CE, CM+CR, CE+CR, CM+CE+CR, HR2+CHP7. No combined alpha-beta instance drops one of its options.
  - Every branch ON pin reproduces on the stack: CorrHistPlus 1/2/4/7, CorrMargins, CorrExt, CuckooRep, HistRework 1/2, Syzygy, NnueInt16.

### Cancels out: two pairs, both by design and both silent
- **NetScale=99 + v2 net** and **NnueInt16 + v2 net**: bench nodes equal the lock pins, although each option alone changes the tree.
  - Both options act only on the compiled-in net (S41: "v2 nets are not scaled"; S-A2: "a v2 net keeps its float path").
  - The engine accepts both without a warning. NnueInt16 even prints `info string NnueInt16 active` when the option is set, but the int16 path never runs once the v2 net is active.
- O2 and NnueLazyAcc are inert under a v2 net in the same way (nodes = pins). They are not flagged because neither has a clear effect of its own to lose.

### NPS: does a pair cost about the sum of its parts?

**TT group: yes, within noise.**

| configuration | NPS Δ% [95% CI] |
|---|---|
| LocklessTT, T1 | -0.55 [-1.27, +0.16] |
| TtChildPrefetch, T1 | -0.79 [-1.75, +0.17] |
| TtChildPrefetch on vs off, same exe | -0.10 [-1.40, +1.22] |
| LocklessTT + TtChildPrefetch, T1 | -0.45 [-1.21, +0.32] (interaction +0.90 [-0.36, +2.18]) |
| LocklessTT, T2 | +1.61 [-2.43, +5.82] |
| TtChildPrefetch, T2 | -0.09 [-3.28, +3.21] |
| LocklessTT + TtChildPrefetch, T2 | +1.15 [-1.69, +4.07] (interaction -0.36 [-5.45, +4.99]) |

- No SMP gain from LocklessTT is resolved at Threads=2 on this load.
- SPEEDSTACK already contains TtChildPrefetch's two prefetches and the material-key table, so on top of it:
  - TtChildPrefetch adds +0.4% [-0.2, +1.0].
  - MaterialKeyTable adds -0.1% [-0.7, +0.6]; MaterialKeyTable alone is +0.77% [+0.02, +1.53].
  - Both options are redundant under the switch, by code.

**Correction group: strongly sub-additive, but on new trees.**

| configuration | NPS Δ% [95% CI] | additive prediction | interaction |
|---|---|---|---|
| CHP7 | -11.77 | — | — |
| CorrMargins | -4.29 | — | — |
| CorrExt | -6.80 | — | — |
| CHP7 + CM | -9.77 | -15.56 | +6.85 [+5.68, +8.04] |
| CHP7 + CE | -8.19 | -17.78 | +11.66 |
| CM + CE | -9.09 | -10.80 | +1.91 [+0.47, +3.38] |
| CHP7 + CM + CE | -4.35 | -21.30 | +21.54 |

- On different trees, NPS mixes per-node cost with tree shape.
- C2 measured CorrHistPlus's machinery on the same tree (weights 0) at about 1-3% per bit. So most of CHP7's -11.8% here is tree shape, and CorrMargins / CorrExt change the tree again.
- This is not a code conflict. Separating the two would need same-tree runs with weights at 0, and those weights are not UCI options in the PC build.

**Instance extras:**
- CM+CR is additive: -9.32% (interaction -0.20 [-1.42, +1.03]).
- CE+CR: interaction +2.08.
- CM+CE+CR: -6.82% (interaction +10.04).
- HR2+CHP7 (the joint correction code): -16.41% against a prediction of -22.05.

**NNUE group (replica nets, so the same tree as OFF and pure machinery cost):**

| configuration | this job, Δ% | earlier job reports |
|---|---|---|
| v2 path (r1 replica) | -1.14 [-1.73, -0.55] | C4: -1.31 |
| king buckets (rm8 replica) | -6.18 | C4: -5.33 |
| 8 output heads | -1.53 | C5: -0.98 |
| zero-threat replica | -41.13 [-41.44, -40.82] | O6 local: -42.5 |
| zero-pawn-pair replica | -21.46 | O7 local: -20.6 |

- **Threats + PawnPairs share machinery.** Together they cost -48.50% [-48.87, -48.13] against a prediction of -53.23% (interaction +10.10 [+8.49, +11.75]).
  - PawnPairs adds only -12.5% on top of Threats, against -20.5% alone above the v2 path.
  - Threats adds -34.4% on top of PawnPairs, against -40.4%.
  - Not a cancel: both still cost clearly.
- Output buckets add nothing on top of Threats (+0.33 [-0.68, +1.35]) or PawnPairs (-0.45 [-1.91, +1.03]).
- **O2 has no measurable gain on the PC recipe:**
  - +0.13% [-0.24, +0.51] at d16 (16 pairs), -0.05% [-1.23, +1.15] at d20.
  - With `-march=znver5` (AVX-512), O2's explicit AVX2 kernels are compiled out ("AVX-512 targets keep the portable loops", `src/nnue.cpp`). O2's own +3.3-3.7% was measured on AVX2 builds.
- **The O2 build costs about 2% under v2.** With a v2 option O2's kernels never run, yet the O2 build costs about 2% on the threat and pawn-pair paths:
  - O2+THR: interaction -2.51 [-4.22, -0.77].
  - O2+PP: -2.04 [-3.41, -0.66].
  - O2+OB8: -0.90 [-1.81, +0.02].
  - O2 on top of THR+PP+OB8: -1.0% [-2.1, +0.1].
  - This looks like a layout effect, not isolated. O2 also raises `Accumulator` alignment from 32 to 64 bytes, and the v2 path keeps its accumulators in the same SearchStack entries.

**Final-head features [330237f3]:**
- NnueInt16, option on vs off in the same exe: -8.78% [-9.88, -7.66] (S-A2 measured -10.5%). O2 + NnueInt16: -7.72%. NnueLazyAcc + NnueInt16: -7.24% [-7.43, -7.04]. Neither O2's nor the lazy build's layout gain survives under int16; O2's float kernels never run there, because the int16 hooks sit first in refresh/update/evaluate.
- NnueLazyAcc, option on vs off in the same exe: -1.05% [-2.52, +0.44], i.e. no measurable effect.
- FORGE_PROF:
  - The build alone costs -7.24% against base_h3, about -11.5% against the first-pass base. That fits S08fix's MinGW emulated-TLS finding.
  - Counting costs a further -1.10% [-2.02, -0.17].
  - Counting inside the CM+CE instance costs more: interaction -3.45 [-4.84, -2.03]. This is diagnostic only.

### Build layout: a ±5% term in every switch row on this PC
- **H3DRIFT, -4.61% [-5.20, -4.01]:** the final head's OFF exe against the first-pass OFF exe.
  - The default path only gained output checks and one atomic flag.
  - `nm` shows the hot functions keep their 0 mod 64 pins, but move relative to each other. `Worker::search`, `qsearch` and `TranspositionTable::probe` moved 64 bytes earlier; `static_evaluate`, `nnue::update` and `Evaluator::evaluate_runtime` stayed where they were.
- **Switch-only controls (option off):**
  - FORGE_NNUE_LAZY_ACC: +4.36% [+2.92, +5.81].
  - FORGE_NNUE_INT16: +1.79% [+0.70, +2.89].
  - FORGE_S13_TT_CHILD_PREFETCH: -0.70% [-1.76, +0.37].
  - O2 is +0.13% at one head and +3.04% [+2.15, +3.94] at the other.
- **FORGE_NOZERO_MOVE_BUFFERS is slower:**
  - -4.16% [-4.60, -3.72] at d16 (16 pairs from two independent blocks), -4.39% [-4.95, -3.82] at d20.
  - The opposite of S14's quiet-runner +1.25..+2.70%, and of its PC run of +5.64% (tick-sampled CPU time).
  - Probably layout as well: removing the zero fills moves the whole hot code.
- **Consequence:** on this PC a switch's NPS row carries a layout term of up to about ±5%. Switch effects and switch-pair interactions below that size are not attributable to the feature without a codegen/layout check or a quiet runner. Same-exe comparisons (every runtime option, and the "option on vs off in the same exe" figures) are free of it.

### Method findings
- **Tick-sampled clock.** `GetProcessTimes` CPU time is charged in 15.625 ms ticks, so a thread that is often preempted is charged unevenly. The A/A per-run sd was 3.8-4.9% (interval [-9.33, +1.50]%), and it reported IntendedThreefold at +6.95% [+0.57, +13.33]. The cycle-timed CPU time (`QueryProcessCycleTime`) gives +0.02% [-0.41, +0.45] for the same runs; it is the reported metric. The GetProcessTimes figures are in `logs/matrix_tables_cpu.md`.
- **`bench` ignores Threads.** It always searches with `Searcher bench_searcher(16)` (one worker, 16 MB). Bench with Threads=4 gives the T1 pins (`logs/bench_threads4_check.log`). So `bench_opts.py --threads N` never reaches bench, although its docstring says bench uses Threads.
- **`bench` never counts profile events.** `bench` turns profiling off (`set_profiling(command == "bench_prof")`), so the UCI `Profile` option never reaches bench; counting needs `bench_prof`.

## Matrix

Cycle-timed CPU NPS against the OFF exe of the same head at the same Threads; 8 ABBA pairs per row; T1 = `bench 16`, T2 = `go depth 16` on the 8 bench positions. Configurations marked [330237f3] are timed against base_h3. Full table with options and build flags: `logs/matrix_tables_cycles.md`.

| config | nodes d11 / d13 / d16 | Δnodes vs OFF | CPU NPS Δ% [95% CI] | flag |
|---|---|---|---|---|
| OFF: base.exe, no options | 312866/862329/3024920 | 0 / 0 / 0 | — | ok |
| AA_T1: A/A control T1 (base_copy.exe) | 312866/862329/3024920 | 0 / 0 / 0 | +0.06 [-0.66, +0.77] | ok |
| AA_T2: A/A control T2 | T2: varies (mean 3.88M) | n/a | +0.65 [-1.81, +3.17] | ok |
| CHP1: CorrHistPlus=1 | 318363/915778/2347193 | +1.8% / +6.2% / -22.4% | -7.05 [-7.65, -6.45] | ok |
| CHP2: CorrHistPlus=2 | 296553/824640/2914749 | -5.2% / -4.4% / -3.6% | -9.12 [-10.70, -7.53] | ok |
| CHP4: CorrHistPlus=4 | 340927/734347/2794671 | +9.0% / -14.8% / -7.6% | -7.33 [-7.98, -6.68] | ok |
| CHP7: CorrHistPlus=7 | 317529/866764/2715911 | +1.5% / +0.5% / -10.2% | -11.77 [-12.41, -11.13] | ok |
| CM: CorrMargins=1 | 343365/858019/2522546 | +9.7% / -0.5% / -16.6% | -4.29 [-4.91, -3.66] | ok |
| CE: CorrExt=1 | 312961/838790/2891507 | +0.0% / -2.7% / -4.4% | -6.80 [-7.37, -6.24] | ok |
| CR: CuckooRep=true | 324211/790682/3148570 | +3.6% / -8.3% / +4.1% | -5.07 [-5.83, -4.30] | ok |
| MKT: MaterialKeyTable=true | 312866/862329/3024920 | 0 / 0 / 0 | +0.77 [+0.02, +1.53] | ok |
| NS99: NetScale=99 | 308948/917342/2601047 | -1.3% / +6.4% / -14.0% | +0.87 [+0.25, +1.49] | ok |
| HR1: HistRework=1 | 373261/1043893/3399770 | +19.3% / +21.1% / +12.4% | -9.37 [-9.65, -9.09] | ok |
| HR2: HistRework=2 | 320427/881902/3041041 | +2.4% / +2.3% / +0.5% | -11.65 [-12.89, -10.39] | ok |
| IT: IntendedThreefold=true | 312866/862329/3024920 | 0 / 0 / 0 | +0.02 [-0.41, +0.45] | ok |
| HD10: HardDeadline=10 (bench unclocked) | 312866/862329/3024920 | 0 / 0 / 0 | +0.27 [-0.17, +0.72] | ok |
| SYZ: SyzygyPath=syzygy345 (145 WDL + 145 DTZ) | 313631/866959/2460490 | +0.2% / +0.5% / -18.7% | -8.16 [-9.12, -7.19] | ok |
| LTT_T1: LocklessTT (T1) | 312866/862329/3024920 | 0 / 0 / 0 | -0.55 [-1.27, +0.16] | ok |
| SEN_T1 / SBT_T1: SmpExactNodes / SmpBestThread (T1) | 312866/862329/3024920 | 0 / 0 / 0 | — (inert at T1) | ok |
| LTT_T2: LocklessTT (T2) | T2: varies (mean 4.43M) | n/a | +1.61 [-2.43, +5.82] | ok |
| SEN_T2: SmpExactNodes (T2) | T2: varies (mean 4.08M) | n/a | +0.66 [-1.01, +2.36] | ok |
| SBT_T2: SmpBestThread (T2) | T2: varies (mean 4.22M) | n/a | -0.31 [-2.34, +1.76] | ok |
| V2R1: v2 path, r1 replica, NNUEKingBuckets=1 | 312866/862329/3024920 | 0 / 0 / 0 | -1.14 [-1.73, -0.55] | ok |
| KB8: NNUEKingBuckets=8 (rm8 replica) | 312866/862329/3024920 | 0 / 0 / 0 | -6.18 [-6.97, -5.39] | ok |
| OB8: NNUEOutputBuckets=8 (r1 + 8 heads) | 312866/862329/3024920 | 0 / 0 / 0 | -1.53 [-2.14, -0.92] | ok |
| THR: NNUEThreats=1 (zero threats) | 312866/862329/3024920 | 0 / 0 / 0 | -41.13 [-41.44, -40.82] | ok |
| PP: NNUEPawnPairs=1 (zero pawn pairs) | 312866/862329/3024920 | 0 / 0 / 0 | -21.46 [-22.45, -20.45] | ok |
| PURE: PureNnue=1 (r1 weights stand-alone) | 558939/1881923/9764737 | +78.7% / +118.2% / +222.8% | +13.40 [+13.07, +13.73] | ok |
| O2: FORGE_NNUE_O2 (16 pairs) | 312866/862329/3024920 | 0 / 0 / 0 | +0.13 [-0.24, +0.51]; d20 -0.05 [-1.23, +1.15] | ok |
| NOZERO: FORGE_NOZERO_MOVE_BUFFERS (16 pairs) | 312866/862329/3024920 | 0 / 0 / 0 | -4.16 [-4.60, -3.72]; d20 -4.39 [-4.95, -3.82] | ok |
| S13SW: S13 switch, option off | 312866/862329/3024920 | 0 / 0 / 0 | -0.70 [-1.76, +0.37] | ok |
| TCP: S13 switch + TtChildPrefetch | 312866/862329/3024920 | 0 / 0 / 0 | -0.79 [-1.75, +0.17] | ok |
| SS: FORGE_SPEEDSTACK | 312866/862329/3024920 | 0 / 0 / 0 | +0.59 [+0.09, +1.08] | ok |
| LTT_TCP_T1: LocklessTT + TtChildPrefetch (T1) | 312866/862329/3024920 | 0 / 0 / 0 | -0.45 [-1.21, +0.32] | ok |
| TCP_T2: TtChildPrefetch (T2) | T2: varies (mean 3.91M) | n/a | -0.09 [-3.28, +3.21] | ok |
| LTT_TCP_T2: LocklessTT + TtChildPrefetch (T2) | T2: varies (mean 4.00M) | n/a | +1.15 [-1.69, +4.07] | ok |
| SS_TCP: SPEEDSTACK + S13 + TtChildPrefetch | 312866/862329/3024920 | 0 / 0 / 0 | +0.99 [+0.49, +1.50] | ok |
| SS_MKT: SPEEDSTACK + MaterialKeyTable | 312866/862329/3024920 | 0 / 0 / 0 | +0.52 [-0.02, +1.06] | ok |
| CHP7_CM: CorrHistPlus=7 + CorrMargins | 285473/764223/2280251 | -8.8% / -11.4% / -24.6% | -9.77 [-10.47, -9.06] | ok |
| CHP7_CE: CorrHistPlus=7 + CorrExt | 329635/858203/2950425 | +5.4% / -0.5% / -2.5% | -8.19 [-8.89, -7.49] | ok |
| CM_CE: CorrMargins + CorrExt | 333285/903735/2610911 | +6.5% / +4.8% / -13.7% | -9.09 [-10.26, -7.91] | ok |
| CHP7_CM_CE: CorrHistPlus=7 + CorrMargins + CorrExt | 296551/730532/2597356 | -5.2% / -15.3% / -14.1% | -4.35 [-4.88, -3.82] | ok |
| CM_CR: CorrMargins + CuckooRep | 362762/819649/2222921 | +15.9% / -4.9% / -26.5% | -9.32 [-10.16, -8.48] | ok |
| CE_CR: CorrExt + CuckooRep | 317563/800845/2653359 | +1.5% / -7.1% / -12.3% | -9.68 [-10.39, -8.97] | ok |
| CM_CE_CR: CorrMargins + CorrExt + CuckooRep | 353437/944233/2459887 | +13.0% / +9.5% / -18.7% | -6.82 [-7.41, -6.22] | ok |
| HR2_CHP7: HistRework=2 + CorrHistPlus=7 | 352551/889835/3089398 | +12.7% / +3.2% / +2.1% | -16.41 [-17.16, -15.66] | ok |
| IT_CR: IntendedThreefold + CuckooRep | 324211/790682/3148570 | +3.6% / -8.3% / +4.1% | -4.14 [-5.18, -3.09] | ok |
| NS99_V2R1: NetScale=99 + v2 r1 replica | 312866/862329/3024920 | 0 / 0 / 0 | -1.38 [-1.96, -0.79] | **CANCELS OUT**: nodes = OFF, but NS99 alone changes the tree |
| O2_THR: O2 + NNUEThreats | 312866/862329/3024920 | 0 / 0 / 0 | -42.53 [-43.51, -41.53] | ok |
| O2_PP: O2 + NNUEPawnPairs | 312866/862329/3024920 | 0 / 0 / 0 | -22.96 [-23.55, -22.36] | ok |
| O2_OB8: O2 + NNUEOutputBuckets=8 | 312866/862329/3024920 | 0 / 0 / 0 | -2.28 [-2.99, -1.57] | ok |
| THR_PP: NNUEThreats + NNUEPawnPairs | 312866/862329/3024920 | 0 / 0 / 0 | -48.50 [-48.87, -48.13] | ok |
| THR_OB8: NNUEThreats + NNUEOutputBuckets=8 | 312866/862329/3024920 | 0 / 0 / 0 | -41.16 [-41.51, -40.82] | ok |
| PP_OB8: NNUEPawnPairs + NNUEOutputBuckets=8 | 312866/862329/3024920 | 0 / 0 / 0 | -22.12 [-22.61, -21.62] | ok |
| THR_PP_OB8: Threats + PawnPairs + OutputBuckets=8 | 312866/862329/3024920 | 0 / 0 / 0 | -48.19 [-48.74, -47.64] | ok |
| O2_THR_PP_OB8: O2 + Threats + PawnPairs + OutputBuckets=8 (= the v2 path) | 312866/862329/3024920 | 0 / 0 / 0 | -48.70 [-49.00, -48.40] | ok |
| H3DRIFT: base_h3.exe [330237f3] vs first-pass base.exe | 312866/862329/3024920 | 0 / 0 / 0 | -4.61 [-5.20, -4.01] | ok |
| O2H3: FORGE_NNUE_O2 [330237f3] | 312866/862329/3024920 | 0 / 0 / 0 | +3.04 [+2.15, +3.94] | ok |
| LAZYSW: FORGE_NNUE_LAZY_ACC, option off [330237f3] | 312866/862329/3024920 | 0 / 0 / 0 | +4.36 [+2.92, +5.81] | ok |
| LAZY: + NnueLazyAcc=true [330237f3] | 312866/862329/3024920 | 0 / 0 / 0 | +3.26 [+2.41, +4.11] | ok |
| O2_LAZY: O2 + NnueLazyAcc [330237f3] | 312866/862329/3024920 | 0 / 0 / 0 | +4.14 [+3.67, +4.62] | ok |
| LAZY_THR: NnueLazyAcc + NNUEThreats [330237f3] | 312866/862329/3024920 | 0 / 0 / 0 | -37.99 [-38.43, -37.55] | ok |
| PROFSW: FORGE_PROF, `bench` (counting off) [330237f3] | 312866/862329/3024920 | 0 / 0 / 0 | -7.24 [-7.99, -6.50] | ok |
| PROF: FORGE_PROF, `bench_prof` (counting) [330237f3] | 312866/862329/3024920 | 0 / 0 / 0 | -8.27 [-8.85, -7.68] | ok |
| PROF_CM_CE: `bench_prof` + CorrMargins + CorrExt [330237f3] | 333285/903735/2610911 | +6.5% / +4.8% / -13.7% | -15.59 [-15.91, -15.27] | ok |
| INT16SW: FORGE_NNUE_INT16, option off [330237f3] | 312866/862329/3024920 | 0 / 0 / 0 | +1.79 [+0.70, +2.89] | ok |
| INT16: + NnueInt16=true [330237f3] | 330610/858175/2760596 | +5.7% / -0.5% / -8.7% | -7.15 [-7.87, -6.42] | ok |
| O2_INT16: O2 + NnueInt16 [330237f3] | 330610/858175/2760596 | +5.7% / -0.5% / -8.7% | -7.72 [-9.58, -5.81] | ok |
| INT16_LAZY: NnueInt16 + NnueLazyAcc [330237f3] | 330610/858175/2760596 | +5.7% / -0.5% / -8.7% | -7.24 [-7.43, -7.04] | ok |
| INT16_THR: NnueInt16 + NNUEThreats [330237f3] | 312866/862329/3024920 | 0 / 0 / 0 | -39.00 [-39.54, -38.47] | **CANCELS OUT**: nodes = OFF, but INT16 alone changes the tree |

## Pair analysis

The prediction is the sum of the parts' log ratios; with several v2 parts, the v2-path cost (V2R1) is counted once. Parts timed against another head's OFF exe are converted with H3DRIFT. Leave-one-out figures are in `logs/matrix_tables_cycles.md`.

| combination | nodes | measured Δ% [CI] | predicted Δ% | interaction [CI] | reading |
|---|---|---|---|---|---|
| LTT_TCP_T1 | node-exact = pins | -0.45 [-1.21, +0.32] | -1.34 | +0.90 [-0.36, +2.18] | additive |
| LTT_TCP_T2 | T2 | +1.15 [-1.69, +4.07] | +1.52 | -0.36 [-5.45, +4.99] | additive (wide T2 noise) |
| SS_TCP | = pins | +0.99 [+0.49, +1.50] | -0.21 | +1.21 [+0.12, +2.31] | TCP redundant under SPEEDSTACK (duplicate prefetch) |
| SS_MKT | = pins | +0.52 [-0.02, +1.06] | +1.36 | -0.83 [-1.74, +0.09] | MKT redundant under SPEEDSTACK (by code) |
| CHP7_CM | new tree | -9.77 [-10.47, -9.06] | -15.56 | +6.85 [+5.68, +8.04] | sub-additive, tree-confounded |
| CHP7_CE | new tree | -8.19 [-8.89, -7.49] | -17.78 | +11.66 [+10.47, +12.86] | sub-additive, tree-confounded |
| CM_CE | new tree | -9.09 [-10.26, -7.91] | -10.80 | +1.91 [+0.47, +3.38] | about additive |
| CHP7_CM_CE | new tree | -4.35 [-4.88, -3.82] | -21.30 | +21.54 [+20.21, +22.90] | sub-additive, tree-confounded |
| CM_CR | new tree | -9.32 [-10.16, -8.48] | -9.14 | -0.20 [-1.42, +1.03] | additive |
| CE_CR | new tree | -9.68 [-10.39, -8.97] | -11.53 | +2.08 [+0.94, +3.24] | slightly sub-additive |
| CM_CE_CR | new tree | -6.82 [-7.41, -6.22] | -15.32 | +10.04 [+8.75, +11.35] | sub-additive, tree-confounded |
| HR2_CHP7 | new tree | -16.41 [-17.16, -15.66] | -22.05 | +7.23 [+5.48, +9.00] | sub-additive, tree-confounded |
| IT_CR | = CR | -4.14 [-5.18, -3.09] | -5.05 | +0.95 [-0.33, +2.25] | IT inert on bench (expected) |
| NS99_V2R1 | = OFF | -1.38 [-1.96, -0.79] | -0.28 | -1.10 [-2.00, -0.19] | NetScale inert under v2 (flag) |
| O2_THR | = pins | -42.53 [-43.51, -41.53] | -41.05 | -2.51 [-4.22, -0.77] | O2 build costs ~2% on the threat path |
| O2_PP | = pins | -22.96 [-23.55, -22.36] | -21.35 | -2.04 [-3.41, -0.66] | the same on the pawn-pair path |
| O2_OB8 | = pins | -2.28 [-2.99, -1.57] | -1.40 | -0.90 [-1.81, +0.02] | about additive |
| THR_PP | = pins | -48.50 [-48.87, -48.13] | -53.23 | +10.10 [+8.49, +11.75] | shared extra-input machinery |
| THR_OB8 | = pins | -41.16 [-41.51, -40.82] | -41.36 | +0.33 [-0.68, +1.35] | additive (OB ≈ free) |
| PP_OB8 | = pins | -22.12 [-22.61, -21.62] | -21.77 | -0.45 [-1.91, +1.03] | additive |
| THR_PP_OB8 | = pins | -48.19 [-48.74, -47.64] | -53.41 | +11.20 [+9.10, +13.34] | = THR_PP |
| O2_THR_PP_OB8 | = pins | -48.70 [-49.00, -48.40] | -53.35 | +9.96 [+8.01, +11.94] | O2 adds -1.0% [-2.1, +0.1] |
| O2_LAZY [330237f3] | = pins | +4.14 [+3.67, +4.62] | +6.39 | -2.12 [-3.22, -1.00] | the two builds' layout gains don't add |
| LAZY_THR [330237f3] | = pins | -37.99 [-38.43, -37.55] | -36.27 | -2.70 [-3.84, -1.54] | NnueLazyAcc inert under v2 (nodes) |
| PROF_CM_CE [330237f3] | = CM_CE | -15.59 [-15.91, -15.27] | -12.58 | -3.45 [-4.84, -2.03] | more counter sites in the CM+CE instance |
| O2_INT16 [330237f3] | = INT16 | -7.72 [-9.58, -5.81] | -4.32 | -3.55 [-5.62, -1.43] | O2's kernels never run under int16 |
| INT16_LAZY [330237f3] | = INT16 | -7.24 [-7.43, -7.04] | -4.12 | -3.25 [-4.24, -2.24] | node-exact; the lazy layout gain is lost |
| INT16_THR [330237f3] | = OFF | -39.00 [-39.54, -38.47] | -42.69 | +6.44 [+5.12, +7.77] | NnueInt16 inert under v2 (flag) |

Option effect inside its own switch build (same exe, so free of the layout term):

| option | on vs off, same exe |
|---|---|
| TtChildPrefetch | -0.10 [-1.40, +1.22] |
| NnueLazyAcc | -1.05 [-2.52, +0.44] |
| FORGE_PROF counting | -1.10 [-2.02, -0.17] |
| NnueInt16 | -8.78 [-9.88, -7.66] |

How the flags are defined:
- **Conflict:** a failed run, an ERROR line after `readyok`, a nonzero exit, T1 nodes that differ between processes, or nodes that contradict the parts.
- **Cancels out:** nodes equal to OFF where a part changes them; nodes equal to one part's while another tree-changing part is on; or, in NPS, every part has a clear effect of the same sign and the combination is clearly smaller in size than each part. No combination meets the NPS rule.

## Flagged pairs
- **NS99_V2R1** (NetScale=99 + a v2 net): cancels out. Nodes equal the lock pins; NetScale scales only the compiled-in net, so it is silently inert while a v2 net is active.
- **INT16_THR** (NnueInt16 + a v2 net): cancels out. Nodes equal the lock pins; the int16 path covers only the compiled-in net, yet the engine prints `info string NnueInt16 active` when the option is set and gives no warning once the v2 net takes over.
- Conflicts: none.

## What a trained net would change
- **Tree shape.** The replica nets keep the OFF tree, so the NNUE rows are pure machinery cost. A trained net changes the tree. C4/C5's smoke nets searched 12-15% more evaluations per node, giving -12 to -20% NPS instead of -1 to -9%. O6/O7's CPU-trained nets cost -47% / -21% on CI, against -41% / -17% for the zero replicas.
- **What carries over.** The machinery costs and their structure should carry over: Threats and PawnPairs sharing work, output buckets being almost free, and the about 2% cost of the O2 build under v2. The tree effect comes on top, separately for each net, and must be measured again with the real net.
- **Combinations.** Combining blocks needs a net trained with all of them.
- **Compiled-in-net features.** O2, NetScale, NnueLazyAcc and NnueInt16 act only on the compiled-in net, so with any v2 net, trained or replica, they do nothing.
- **PureNnue.** The stand-alone r1 copy drops the HCE term: the d16 tree is +223% and NPS +13.4%. O4's material-trained pure net had 5.67M nodes at d16 and +19.8% CPU NPS. A real pure net needs its own measurement.

## UNVERIFIED / left
- **Load.** All NPS comes from a PC at about 98% total CPU. A quiet-runner repeat of the switch rows, of NOZERO and of H3DRIFT would separate layout from feature, and is the natural next step.
- **Tree-changing rows.** These mix machinery cost with tree shape. A same-tree cost (weights 0) needs builds with the tunables exposed; not done.
- **Threads=2 precision.** 8 positions, Hash 16, 8 pairs give intervals of about ±2-4%, so smaller SMP effects are not resolved.
  - Without SmpExactNodes, the last info line of a search can miss helper nodes counted after it; this affects both sides alike.
- **Final head coverage.** Runtime-option rows were not re-measured at 330237f3. Same-exe option effects should carry over; switch rows need the layout caveat.
- **Combinations not run.** NNUEKingBuckets and PureNnue were not combined with other v2 options. CorrHistPlus appears in the pairs only as value 7. HistRework was paired only with CorrHistPlus.
- **Multiplicity.** There are about 70 intervals at 95%, so a few could exclude 0 by chance. The flags rest on exact node counts, not on NPS.

Machine exclusive: no.

**Evidence** (in `opus_r3/R3-2/`; every file's sha256 is in FILES.txt and SHA256SUMS):
- Tables: `logs/matrix_tables_cycles.md`, `logs/matrix_tables_cpu.md`, `logs/matrix_tables_d20_cycles.md`.
- Raw runs: `logs/nodes.log`, `logs/nps.log`, `logs/nodes_h3.log`, `logs/nps_h3.log`, `logs/nps_confirm_d16.log`, `logs/nps_confirm_d20.log`.
- Builds: `logs/build_all.log`, `logs/build_final_head.log`.
- Probes: `logs/t2_probe.log`, `logs/bench_threads4_check.log`.
- Per-run JSON: `logs/results/` (plus `analysis.json`) and `logs/results_d20/`.
- Scripts: `r3_matrix.py`, `build_all.sh`, `run_matrix.sh`, `build_final_head.sh`, `run_final_head.sh`, `t2_probe.py`, `README.md`, `IDEA_SOURCE.md`.

`build_h2.sh` is a superseded, never-run draft for head 2047348a; I could not delete it, so it is committed and labelled as such in FILES.txt.

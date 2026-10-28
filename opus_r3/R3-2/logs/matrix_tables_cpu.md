| config | build / options | nodes d11 / d13 / d16 | Δnodes vs OFF | CPU NPS Δ% [95% CI] (GetProcessTimes) | flag |
|---|---|---|---|---|---|
| OFF (OFF (base.exe, no options)) | base | 312866 / 862329 / 3024920 | 0 / 0 / 0 | — | ok |
| AA_T1 (A/A control T1 (base_copy.exe)) | (byte copy of base.exe) | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -4.06 [-9.33, +1.50] | ok |
| AA_T2 (A/A control T2 (base_copy.exe, Threads 2)) | (byte copy of base.exe) T2 | T2 go: mean 3,876,725 (varies) | n/a | -0.31 [-8.31, +8.39] | ok |
| CHP1 (CorrHistPlus=1) | base + CorrHistPlus=1 | 318363 / 915778 / 2347193 | +1.8% / +6.2% / -22.4% | -7.70 [-12.87, -2.22] | ok |
| CHP2 (CorrHistPlus=2) | base + CorrHistPlus=2 | 296553 / 824640 / 2914749 | -5.2% / -4.4% / -3.6% | -7.62 [-12.49, -2.48] | ok |
| CHP4 (CorrHistPlus=4) | base + CorrHistPlus=4 | 340927 / 734347 / 2794671 | +9.0% / -14.8% / -7.6% | -4.82 [-10.10, +0.77] | ok |
| CHP7 (CorrHistPlus=7) | base + CorrHistPlus=7 | 317529 / 866764 / 2715911 | +1.5% / +0.5% / -10.2% | -12.93 [-18.45, -7.03] | ok |
| CM (CorrMargins=1) | base + CorrMargins=1 | 343365 / 858019 / 2522546 | +9.7% / -0.5% / -16.6% | -7.94 [-14.61, -0.74] | ok |
| CE (CorrExt=1) | base + CorrExt=1 | 312961 / 838790 / 2891507 | +0.0% / -2.7% / -4.4% | -6.46 [-11.66, -0.95] | ok |
| CR (CuckooRep=true) | base + CuckooRep=true | 324211 / 790682 / 3148570 | +3.6% / -8.3% / +4.1% | -8.95 [-12.79, -4.95] | ok |
| MKT (MaterialKeyTable=true) | base + MaterialKeyTable=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +2.55 [-0.19, +5.37] | ok |
| NS99 (NetScale=99) | base + NetScale=99 | 308948 / 917342 / 2601047 | -1.3% / +6.4% / -14.0% | +5.20 [+1.70, +8.82] | ok |
| HR1 (HistRework=1) | base + HistRework=1 | 373261 / 1043893 / 3399770 | +19.3% / +21.1% / +12.4% | -9.09 [-14.41, -3.43] | ok |
| HR2 (HistRework=2) | base + HistRework=2 | 320427 / 881902 / 3041041 | +2.4% / +2.3% / +0.5% | -10.70 [-16.79, -4.16] | ok |
| IT (IntendedThreefold=true) | base + IntendedThreefold=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +6.77 [+0.90, +12.98] | ok |
| HD10 (HardDeadline=10) | base + HardDeadline=10 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -1.32 [-6.27, +3.89] | ok |
| SYZ (SyzygyPath=syzygy345) | base + SyzygyPath=syzygy345 | 313631 / 866959 / 2460490 | +0.2% / +0.5% / -18.7% | -6.13 [-13.19, +1.51] | ok |
| LTT_T1 (LocklessTT=true (T1)) | base + LocklessTT=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +2.84 [-3.10, +9.14] | ok |
| SEN_T1 (SmpExactNodes=true (T1)) | base + SmpExactNodes=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | — | ok |
| SBT_T1 (SmpBestThread=true (T1)) | base + SmpBestThread=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | — | ok |
| LTT_T2 (LocklessTT=true (T2)) | base + LocklessTT=true T2 | T2 go: mean 4,432,021 (varies) | n/a | +2.51 [-5.06, +10.69] | ok |
| SEN_T2 (SmpExactNodes=true (T2)) | base + SmpExactNodes=true T2 | T2 go: mean 4,076,902 (varies) | n/a | -1.85 [-7.21, +3.82] | ok |
| SBT_T2 (SmpBestThread=true (T2)) | base + SmpBestThread=true T2 | T2 go: mean 4,222,054 (varies) | n/a | -0.22 [-4.91, +4.70] | ok |
| V2R1 (v2 path: r1 replica, NNUEKingBuckets=1) | base + NNUEKingBuckets=1, NNUEFile=r1.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +0.57 [-3.41, +4.71] | ok |
| KB8 (NNUEKingBuckets=8 (rm8 replica)) | base + NNUEKingBuckets=8, NNUEFile=rm8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -5.63 [-12.51, +1.78] | ok |
| OB8 (NNUEOutputBuckets=8 (r1 + 8 heads)) | base + NNUEOutputBuckets=8, NNUEFile=r1_ob8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -0.69 [-3.82, +2.54] | ok |
| THR (NNUEThreats=1 (r1 + zero threats)) | base + NNUEThreats=1, NNUEFile=r1_t.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -42.63 [-45.96, -39.09] | ok |
| PP (NNUEPawnPairs=1 (r1 + zero pawn pairs)) | base + NNUEPawnPairs=1, NNUEFile=r1_p.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -20.70 [-22.88, -18.46] | ok |
| PURE (PureNnue=1 (r1 weights stand-alone)) | base + PureNnue=1, NNUEFile=r1_pure.fnn2 | 558939 / 1881923 / 9764737 | +78.7% / +118.2% / +222.8% | +13.45 [+8.53, +18.59] | ok |
| O2 (FORGE_NNUE_O2) | -DFORGE_NNUE_O2=1 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +0.40 [-2.64, +3.52] | ok |
| NOZERO (FORGE_NOZERO_MOVE_BUFFERS) | -DFORGE_NOZERO_MOVE_BUFFERS=1 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -3.03 [-6.33, +0.39] | ok |
| S13SW (FORGE_S13_TT_CHILD_PREFETCH, option off) | -DFORGE_S13_TT_CHILD_PREFETCH=1 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +1.18 [-6.07, +8.99] | ok |
| TCP (FORGE_S13_TT_CHILD_PREFETCH + TtChildPrefetch=true) | -DFORGE_S13_TT_CHILD_PREFETCH=1 + TtChildPrefetch=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +0.05 [-6.85, +7.46] | ok |
| SS (FORGE_SPEEDSTACK) | -DFORGE_SPEEDSTACK=1 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -2.60 [-5.35, +0.23] | ok |
| LTT_TCP_T1 (LocklessTT + TtChildPrefetch (T1)) | -DFORGE_S13_TT_CHILD_PREFETCH=1 + LocklessTT=true, TtChildPrefetch=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -5.66 [-10.26, -0.83] | ok |
| TCP_T2 (TtChildPrefetch=true (T2)) | -DFORGE_S13_TT_CHILD_PREFETCH=1 + TtChildPrefetch=true T2 | T2 go: mean 3,912,038 (varies) | n/a | -1.25 [-7.30, +5.21] | ok |
| LTT_TCP_T2 (LocklessTT + TtChildPrefetch (T2)) | -DFORGE_S13_TT_CHILD_PREFETCH=1 + LocklessTT=true, TtChildPrefetch=true T2 | T2 go: mean 3,996,999 (varies) | n/a | -1.77 [-7.66, +4.51] | ok |
| SS_TCP (FORGE_SPEEDSTACK + S13 switch + TtChildPrefetch (T1)) | -DFORGE_SPEEDSTACK=1 -DFORGE_S13_TT_CHILD_PREFETCH=1 + TtChildPrefetch=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +0.51 [-2.38, +3.49] | ok |
| SS_MKT (FORGE_SPEEDSTACK + MaterialKeyTable) | -DFORGE_SPEEDSTACK=1 + MaterialKeyTable=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -0.68 [-3.64, +2.38] | ok |
| CHP7_CM (CorrHistPlus=7 + CorrMargins) | base + CorrHistPlus=7, CorrMargins=1 | 285473 / 764223 / 2280251 | -8.8% / -11.4% / -24.6% | -11.08 [-17.54, -4.11] | ok |
| CHP7_CE (CorrHistPlus=7 + CorrExt) | base + CorrHistPlus=7, CorrExt=1 | 329635 / 858203 / 2950425 | +5.4% / -0.5% / -2.5% | -7.57 [-10.68, -4.36] | ok |
| CM_CE (CorrMargins + CorrExt) | base + CorrMargins=1, CorrExt=1 | 333285 / 903735 / 2610911 | +6.5% / +4.8% / -13.7% | -8.43 [-11.39, -5.36] | ok |
| CHP7_CM_CE (CorrHistPlus=7 + CorrMargins + CorrExt) | base + CorrHistPlus=7, CorrMargins=1, CorrExt=1 | 296551 / 730532 / 2597356 | -5.2% / -15.3% / -14.1% | -2.14 [-7.16, +3.16] | ok |
| CM_CR (CorrMargins + CuckooRep) | base + CorrMargins=1, CuckooRep=true | 362762 / 819649 / 2222921 | +15.9% / -4.9% / -26.5% | -10.32 [-13.24, -7.29] | ok |
| CE_CR (CorrExt + CuckooRep) | base + CorrExt=1, CuckooRep=true | 317563 / 800845 / 2653359 | +1.5% / -7.1% / -12.3% | -9.54 [-12.17, -6.82] | ok |
| CM_CE_CR (CorrMargins + CorrExt + CuckooRep) | base + CorrMargins=1, CorrExt=1, CuckooRep=true | 353437 / 944233 / 2459887 | +13.0% / +9.5% / -18.7% | -6.55 [-11.19, -1.68] | ok |
| HR2_CHP7 (HistRework=2 + CorrHistPlus=7) | base + HistRework=2, CorrHistPlus=7 | 352551 / 889835 / 3089398 | +12.7% / +3.2% / +2.1% | -15.60 [-17.83, -13.31] | ok |
| IT_CR (IntendedThreefold + CuckooRep) | base + IntendedThreefold=true, CuckooRep=true | 324211 / 790682 / 3148570 | +3.6% / -8.3% / +4.1% | -4.49 [-8.50, -0.30] | ok |
| NS99_V2R1 (NetScale=99 + v2 r1 replica) | base + NetScale=99, NNUEKingBuckets=1, NNUEFile=r1.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -0.34 [-3.45, +2.88] | CANCELS OUT: nodes = OFF although NS99 alone changes them |
| O2_THR (O2 + NNUEThreats) | -DFORGE_NNUE_O2=1 + NNUEThreats=1, NNUEFile=r1_t.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -41.54 [-42.99, -40.05] | ok |
| O2_PP (O2 + NNUEPawnPairs) | -DFORGE_NNUE_O2=1 + NNUEPawnPairs=1, NNUEFile=r1_p.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -23.93 [-25.74, -22.08] | ok |
| O2_OB8 (O2 + NNUEOutputBuckets=8) | -DFORGE_NNUE_O2=1 + NNUEOutputBuckets=8, NNUEFile=r1_ob8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -5.75 [-8.49, -2.93] | ok |
| THR_PP (NNUEThreats + NNUEPawnPairs) | base + NNUEThreats=1, NNUEPawnPairs=1, NNUEFile=r1_t_p.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -49.08 [-50.78, -47.32] | ok |
| THR_OB8 (NNUEThreats + NNUEOutputBuckets=8) | base + NNUEThreats=1, NNUEOutputBuckets=8, NNUEFile=r1_t_ob8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -42.25 [-43.50, -40.97] | ok |
| PP_OB8 (NNUEPawnPairs + NNUEOutputBuckets=8) | base + NNUEPawnPairs=1, NNUEOutputBuckets=8, NNUEFile=r1_p_ob8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -21.58 [-23.01, -20.12] | ok |
| THR_PP_OB8 (NNUEThreats + NNUEPawnPairs + NNUEOutputBuckets=8) | base + NNUEThreats=1, NNUEPawnPairs=1, NNUEOutputBuckets=8, NNUEFile=r1_t_p_ob8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -47.23 [-49.60, -44.74] | ok |
| O2_THR_PP_OB8 (O2 + NNUEThreats + NNUEPawnPairs + NNUEOutputBuckets=8) | -DFORGE_NNUE_O2=1 + NNUEThreats=1, NNUEPawnPairs=1, NNUEOutputBuckets=8, NNUEFile=r1_t_p_ob8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -48.70 [-50.00, -47.37] | ok |
| H3DRIFT (final-head OFF exe (330237f3) vs first-pass OFF exe (467a59b3)) | base_h3 [head 330237f3] | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -1.35 [-5.70, +3.21] | ok |
| O2H3 (FORGE_NNUE_O2 at the final head) | -DFORGE_NNUE_O2=1 [head 330237f3] (A side: base_h3.exe) | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +3.18 [-0.25, +6.73] | ok |
| LAZYSW (FORGE_NNUE_LAZY_ACC, option off) | -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +4.39 [-1.87, +11.05] | ok |
| LAZY (FORGE_NNUE_LAZY_ACC + NnueLazyAcc=true) | -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) + NnueLazyAcc=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +1.05 [-2.46, +4.69] | ok |
| O2_LAZY (O2 + NnueLazyAcc (both change the compiled-in accumulator path)) | -DFORGE_NNUE_O2=1 -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) + NnueLazyAcc=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +8.05 [+0.54, +16.12] | ok |
| LAZY_THR (NnueLazyAcc + NNUEThreats (alias is compiled-in-net code; v2 path runs)) | -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) + NnueLazyAcc=true, NNUEThreats=1, NNUEFile=r1_t.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -38.02 [-39.82, -36.16] | ok |
| PROFSW (FORGE_PROF build, bench (counting off)) | -DFORGE_PROF=1 (+ src/profile.cpp) [head 330237f3] (A side: base_h3.exe) | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -7.69 [-12.38, -2.75] | ok |
| PROF (FORGE_PROF build, bench_prof (counting on)) | -DFORGE_PROF=1 (+ src/profile.cpp) [head 330237f3] (`bench_prof`) (A side: base_h3.exe) | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -5.03 [-7.45, -2.53] | ok |
| PROF_CM_CE (FORGE_PROF bench_prof + CorrMargins + CorrExt (counters inside the combined instance)) | -DFORGE_PROF=1 (+ src/profile.cpp) [head 330237f3] (`bench_prof`) (A side: base_h3.exe) + CorrMargins=1, CorrExt=1 | 333285 / 903735 / 2610911 | +6.5% / +4.8% / -13.7% | -15.54 [-22.44, -8.03] | ok |
| INT16SW (FORGE_NNUE_INT16, option off) | -DFORGE_NNUE_INT16=1 [head 330237f3] (A side: base_h3.exe) | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -2.01 [-7.34, +3.63] | ok |
| INT16 (FORGE_NNUE_INT16 + NnueInt16=true) | -DFORGE_NNUE_INT16=1 [head 330237f3] (A side: base_h3.exe) + NnueInt16=true | 330610 / 858175 / 2760596 | +5.7% / -0.5% / -8.7% | -11.05 [-15.21, -6.69] | ok |
| O2_INT16 (O2 + NnueInt16 (the int16 hooks run before O2's float kernels)) | -DFORGE_NNUE_O2=1 -DFORGE_NNUE_INT16=1 [head 330237f3] (A side: base_h3.exe) + NnueInt16=true | 330610 / 858175 / 2760596 | +5.7% / -0.5% / -8.7% | -3.83 [-9.01, +1.64] | ok |
| INT16_LAZY (NnueInt16 + NnueLazyAcc (the alias drives the int16 accumulators)) | -DFORGE_NNUE_INT16=1 -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) + NnueInt16=true, NnueLazyAcc=true | 330610 / 858175 / 2760596 | +5.7% / -0.5% / -8.7% | -8.68 [-11.91, -5.34] | ok |
| INT16_THR (NnueInt16 + NNUEThreats (int16 applies to the compiled-in net only)) | -DFORGE_NNUE_INT16=1 [head 330237f3] (A side: base_h3.exe) + NnueInt16=true, NNUEThreats=1, NNUEFile=r1_t.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -38.68 [-40.73, -36.56] | CANCELS OUT: nodes = OFF although INT16 alone changes them |

### Pair analysis (CPU NPS; log-additive prediction = sum of the parts' log ratios; for several v2 parts the v2-path cost (V2R1) is counted once)

| combination | nodes | measured Δ% [CI] | additive prediction Δ% | interaction (measured − predicted) [CI] | leave-one-out: part → alone vs added on top of the rest |
|---|---|---|---|---|---|
| LTT_TCP_T1 | node-exact parts: = lock pins | -5.66 [-10.26, -0.83] | +2.89 | -8.31 [-16.48, +0.65] | LTT_T1: +2.8% alone, -5.7% [-13.0, +2.1] on TCP; TCP: +0.1% alone, -8.3% [-14.5, -1.5] on LTT_T1 |
| LTT_TCP_T2 | T2: n/a | -1.77 [-7.66, +4.51] | +1.23 | -2.96 [-12.48, +7.59] | LTT_T2: +2.5% alone, -0.5% [-8.2, +7.8] on TCP_T2; TCP_T2: -1.2% alone, -4.2% [-12.4, +4.8] on LTT_T2 |
| SS_TCP | node-exact parts: = lock pins | +0.51 [-2.38, +3.49] | -2.55 | +3.14 [-4.41, +11.29] | SS: -2.6% alone, +0.5% [-6.7, +8.1] on TCP; TCP: +0.1% alone, +3.2% [-0.6, +7.1] on SS |
| SS_MKT | node-exact parts: = lock pins | -0.68 [-3.64, +2.38] | -0.11 | -0.57 [-4.82, +3.88] | SS: -2.6% alone, -3.2% [-6.7, +0.5] on MKT; MKT: +2.6% alone, +2.0% [-1.8, +5.9] on SS |
| CHP7_CM | new tree (differs from OFF and from every part) | -11.08 [-17.54, -4.11] | -19.84 | +10.92 [-0.64, +23.83] | CHP7: -12.9% alone, -3.4% [-12.3, +6.4] on CM; CM: -7.9% alone, +2.1% [-6.7, +11.8] on CHP7 |
| CHP7_CE | new tree (differs from OFF and from every part) | -7.57 [-10.68, -4.36] | -18.55 | +13.48 [+4.42, +23.32] | CHP7: -12.9% alone, -1.2% [-7.1, +5.1] on CE; CE: -6.5% alone, +6.1% [-0.9, +13.7] on CHP7 |
| CM_CE | new tree (differs from OFF and from every part) | -8.43 [-11.39, -5.36] | -13.88 | +6.33 [-2.79, +16.31] | CM: -7.9% alone, -2.1% [-7.9, +4.1] on CE; CE: -6.5% alone, -0.5% [-8.0, +7.5] on CM |
| CHP7_CM_CE | new tree (differs from OFF and from every part) | -2.14 [-7.16, +3.16] | -25.01 | +30.51 [+16.91, +45.68] | CHP7: -12.9% alone, +6.9% [+0.9, +13.2] on CM_CE; CM: -7.9% alone, +5.9% [-0.1, +12.2] on CHP7_CE; CE: -6.5% alone, +10.1% [+1.2, +19.7] on CHP7_CM |
| CM_CR | new tree (differs from OFF and from every part) | -10.32 [-13.24, -7.29] | -16.18 | +7.00 [-1.63, +16.38] | CM: -7.9% alone, -1.5% [-6.3, +3.5] on CR; CR: -9.0% alone, -2.6% [-9.9, +5.3] on CM |
| CE_CR | new tree (differs from OFF and from every part) | -9.54 [-12.17, -6.82] | -14.84 | +6.22 [-0.87, +13.83] | CE: -6.5% alone, -0.6% [-5.3, +4.2] on CR; CR: -9.0% alone, -3.3% [-8.9, +2.7] on CE |
| CM_CE_CR | new tree (differs from OFF and from every part) | -6.55 [-11.19, -1.68] | -21.59 | +19.18 [+7.73, +31.85] | CM: -7.9% alone, +3.3% [-2.2, +9.1] on CE_CR; CE: -6.5% alone, +4.2% [-1.5, +10.2] on CM_CR; CR: -9.0% alone, +2.0% [-3.5, +7.9] on CM_CE |
| HR2_CHP7 | new tree (differs from OFF and from every part) | -15.60 [-17.83, -13.31] | -22.24 | +8.54 [-0.76, +18.73] | HR2: -10.7% alone, -3.1% [-9.4, +3.7] on CHP7; CHP7: -12.9% alone, -5.5% [-12.1, +1.6] on HR2 |
| IT_CR | = CR (the one tree-changing part), as expected | -4.49 [-8.50, -0.30] | -2.79 | -1.74 [-8.69, +5.73] | IT: +6.8% alone, +4.9% [-0.7, +10.9] on CR; CR: -9.0% alone, -10.5% [-16.2, -4.6] on IT |
| NS99_V2R1 | = OFF, but NS99 alone changes the tree | -0.34 [-3.45, +2.88] | +5.80 | -5.80 [-10.77, -0.55] | NS99: +5.2% alone, -0.9% [-5.4, +3.9] on V2R1; V2R1: +0.6% alone, -5.3% [-9.2, -1.2] on NS99 |
| O2_THR | node-exact parts: = lock pins | -41.54 [-42.99, -40.05] | -42.40 | +1.50 [-5.01, +8.45] | O2: +0.4% alone, +1.9% [-4.2, +8.4] on THR; THR: -42.6% alone, -41.8% [-43.9, -39.6] on O2 |
| O2_PP | node-exact parts: = lock pins | -23.93 [-25.74, -22.08] | -20.38 | -4.45 [-8.51, -0.21] | O2: +0.4% alone, -4.1% [-7.2, -0.8] on PP; PP: -20.7% alone, -24.2% [-26.9, -21.4] on O2 |
| O2_OB8 | node-exact parts: = lock pins | -5.75 [-8.49, -2.93] | -0.29 | -5.47 [-9.90, -0.83] | O2: +0.4% alone, -5.1% [-8.8, -1.3] on OB8; OB8: -0.7% alone, -6.1% [-9.8, -2.3] on O2 |
| THR_PP | node-exact parts: = lock pins | -49.08 [-50.78, -47.32] | -54.76 | +12.56 [+4.49, +21.26] | THR: -43.0% alone, -35.8% [-38.3, -33.2] on PP; PP: -21.1% alone, -11.2% [-16.7, -5.4] on THR |
| THR_OB8 | node-exact parts: = lock pins | -42.25 [-43.50, -40.97] | -43.35 | +1.94 [-5.20, +9.62] | THR: -43.0% alone, -41.8% [-43.9, -39.7] on OB8; OB8: -1.2% alone, +0.7% [-5.3, +7.0] on THR |
| PP_OB8 | node-exact parts: = lock pins | -21.58 [-23.01, -20.12] | -21.69 | +0.14 [-5.10, +5.68] | PP: -21.1% alone, -21.0% [-23.7, -18.3] on OB8; OB8: -1.2% alone, -1.1% [-4.1, +2.0] on PP |
| THR_PP_OB8 | node-exact parts: = lock pins | -47.23 [-49.60, -44.74] | -55.33 | +18.13 [+6.49, +31.04] | THR: -43.0% alone, -32.7% [-35.8, -29.5] on PP_OB8; PP: -21.1% alone, -8.6% [-12.9, -4.1] on THR_OB8; OB8: -1.2% alone, +3.6% [-1.6, +9.2] on THR_PP |
| O2_THR_PP_OB8 | node-exact parts: = lock pins | -48.70 [-50.00, -47.37] | -55.15 | +14.38 [+3.23, +26.73] | O2: +0.4% alone, -2.8% [-7.4, +2.1] on THR_PP_OB8 |
| O2_LAZY | node-exact parts: = lock pins | +8.05 [+0.54, +16.12] | +4.26 | +3.63 [-4.26, +12.17] | O2H3: +3.2% alone, +6.9% [-0.8, +15.3] on LAZY; LAZY: +1.0% alone, +4.7% [-2.9, +12.9] on O2H3 |
| LAZY_THR | node-exact parts: = lock pins | -38.02 [-39.82, -36.16] | -41.24 | +5.48 [-2.36, +13.96] | LAZY: +1.0% alone, +6.6% [-0.8, +14.6] on THR; THR: -41.8% alone, -38.7% [-41.2, -36.0] on LAZY |
| PROF_CM_CE | = CM_CE (the one tree-changing part), as expected | -15.54 [-22.44, -8.03] | -11.84 | -4.20 [-12.88, +5.35] | PROF: -5.0% alone, -9.0% [-17.1, -0.1] on CM_CE; CM_CE: -7.2% alone, -11.1% [-18.4, -3.1] on PROF |
| O2_INT16 | = INT16 (the one tree-changing part), as expected | -3.83 [-9.01, +1.64] | -8.22 | +4.78 [-2.44, +12.55] | O2H3: +3.2% alone, +8.1% [+1.2, +15.6] on INT16; INT16: -11.1% alone, -6.8% [-12.2, -1.0] on O2H3 |
| INT16_LAZY | = INT16 (the one tree-changing part), as expected | -8.68 [-11.91, -5.34] | -10.12 | +1.60 [-4.46, +8.05] | INT16: -11.1% alone, -9.6% [-13.7, -5.4] on LAZY; LAZY: +1.0% alone, +2.7% [-2.8, +8.4] on INT16 |
| INT16_THR | = OFF, but INT16 alone changes the tree | -38.68 [-40.73, -36.56] | -48.28 | +18.55 [+9.10, +28.82] | INT16: -11.1% alone, +5.4% [-2.0, +13.5] on THR; THR: -41.8% alone, -31.1% [-34.7, -27.2] on INT16 |

### Option effect inside its own switch build (same exe, option on vs off: free of build-to-build layout effects)

| option | switch build, option off vs OFF exe | option on vs OFF exe | option on vs off (same exe) |
|---|---|---|---|
| TCP (FORGE_S13_TT_CHILD_PREFETCH + TtChildPrefetch=true) | +1.18 [-6.07, +8.99] | +0.05 [-6.85, +7.46] | -1.12 [-9.95, +8.58] |
| LAZY (FORGE_NNUE_LAZY_ACC + NnueLazyAcc=true) | +4.39 [-1.87, +11.05] | +1.05 [-2.46, +4.69] | -3.20 [-9.40, +3.43] |
| PROF (FORGE_PROF build, bench_prof (counting on)) | -7.69 [-12.38, -2.75] | -5.03 [-7.45, -2.53] | +2.89 [-2.58, +8.66] |
| INT16 (FORGE_NNUE_INT16 + NnueInt16=true) | -2.01 [-7.34, +3.63] | -11.05 [-15.21, -6.69] | -9.23 [-15.11, -2.95] |

### Flagged
- NS99_V2R1: CANCELS OUT: nodes = OFF although NS99 alone changes them
- INT16_THR: CANCELS OUT: nodes = OFF although INT16 alone changes them

### Notes per configuration (setup info lines, transient half-set ERROR lines, other notes)
- AA_T1: NPS: 8 ABBA pairs, Welch -4.03% [-8.63, +0.57], cycles +0.06% [-0.66, +0.77]
- AA_T2: NPS: 8 ABBA pairs, Welch -0.38% [-7.84, +7.09], cycles +0.65% [-1.81, +3.17]; wall NPS -3.08% [-16.21, +12.10]
- CHP1: NPS: 8 ABBA pairs, Welch -7.65% [-12.40, -2.89], cycles -7.05% [-7.65, -6.45]
- CHP2: NPS: 8 ABBA pairs, Welch -7.70% [-13.06, -2.34], cycles -9.12% [-10.70, -7.53]
- CHP4: NPS: 8 ABBA pairs, Welch -4.87% [-9.23, -0.51], cycles -7.33% [-7.98, -6.68]
- CHP7: NPS: 8 ABBA pairs, Welch -13.05% [-18.89, -7.22], cycles -11.77% [-12.41, -11.13]
- CM: NPS: 8 ABBA pairs, Welch -7.87% [-12.88, -2.85], cycles -4.29% [-4.91, -3.66]
- CE: NPS: 8 ABBA pairs, Welch -6.56% [-12.80, -0.31], cycles -6.80% [-7.37, -6.24]
- CR: NPS: 8 ABBA pairs, Welch -8.99% [-13.56, -4.41], cycles -5.07% [-5.83, -4.30]
- MKT: NPS: 8 ABBA pairs, Welch +2.53% [-1.14, +6.20], cycles +0.77% [+0.02, +1.53]
- NS99: NPS: 8 ABBA pairs, Welch +5.16% [+0.96, +9.35], cycles +0.87% [+0.25, +1.49]
- HR1: NPS: 8 ABBA pairs, Welch -9.09% [-14.85, -3.32], cycles -9.37% [-9.65, -9.09]
- HR2: NPS: 8 ABBA pairs, Welch -10.70% [-15.61, -5.80], cycles -11.65% [-12.89, -10.39]
- IT: bench positions carry no game history, so no claim can fire; NPS: 8 ABBA pairs, Welch +6.95% [+0.57, +13.33], cycles +0.02% [-0.41, +0.45]
- HD10: bench is unclocked; NPS: 8 ABBA pairs, Welch -1.41% [-7.26, +4.43], cycles +0.27% [-0.17, +0.72]
- SYZ: setup: info string Syzygy: 145 WDL and 145 DTZ tables, up to 5 pieces; NPS: 8 ABBA pairs, Welch -6.12% [-12.23, -0.01], cycles -8.16% [-9.12, -7.19]
- LTT_T1: setup: info string LocklessTT active; NPS: 8 ABBA pairs, Welch +2.88% [-2.01, +7.78], cycles -0.55% [-1.27, +0.16]
- LTT_T2: NPS: 8 ABBA pairs, Welch +2.74% [-4.01, +9.48], cycles +1.61% [-2.43, +5.82]; wall NPS -5.93% [-20.52, +11.34]
- SEN_T2: NPS: 8 ABBA pairs, Welch -1.85% [-6.20, +2.51], cycles +0.66% [-1.01, +2.36]; wall NPS -0.06% [-10.86, +12.04]
- SBT_T2: NPS: 8 ABBA pairs, Welch -0.19% [-6.30, +5.92], cycles -0.31% [-2.34, +1.76]; wall NPS -1.44% [-13.55, +12.35]
- V2R1: 2 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual fnv1a 5a7f7acb2d55004f | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual fnv1a 5a7f7acb2d55; NPS: 8 ABBA pairs, Welch +0.59% [-3.36, +4.53], cycles -1.14% [-1.73, -0.55]
- KB8: 2 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\rm8.fnn2 king buckets 8 output buckets 1 hidden 256 mirrored residual fnv1a ab99e09dfc20366d | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\rm8.fnn2 king buckets 8 output buckets 1 hidden 256 mirrored residual fnv1a ab99e09dfc2036; NPS: 8 ABBA pairs, Welch -5.66% [-11.36, +0.05], cycles -6.18% [-6.97, -5.39]
- OB8: 2 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_ob8.fnn2 king buckets 1 output buckets 8 hidden 256 unmirrored residual fnv1a db400d140d566e35 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_ob8.fnn2 king buckets 1 output buckets 8 hidden 256 unmirrored residual fnv1a db40; NPS: 8 ABBA pairs, Welch -0.70% [-4.31, +2.90], cycles -1.53% [-2.14, -0.92]
- THR: 2 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_t.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual threat inputs fnv1a db8c838b040e1b72 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_t.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual ; NPS: 8 ABBA pairs, Welch -42.74% [-48.53, -36.95], cycles -41.13% [-41.44, -40.82]
- PP: 2 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_p.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual pawn-pair inputs fnv1a 12eb86f897f85ea1 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_p.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residu; NPS: 8 ABBA pairs, Welch -20.68% [-24.59, -16.77], cycles -21.46% [-22.45, -20.45]
- PURE: 2 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_pure.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored stand-alone fnv1a ccb30bde9963bdd6 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_pure.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored stand-alone fn; no function-preserving pure net exists: the HCE term is dropped; NPS: 8 ABBA pairs, Welch +13.45% [+9.09, +17.81], cycles +13.40% [+13.07, +13.73]
- O2: NPS: 16 ABBA pairs, Welch +0.45% [-3.03, +3.93], cycles +0.13% [-0.24, +0.51]
- NOZERO: NPS: 16 ABBA pairs, Welch -3.00% [-6.16, +0.16], cycles -4.16% [-4.60, -3.72]
- S13SW: NPS: 8 ABBA pairs, Welch +1.26% [-5.59, +8.12], cycles -0.70% [-1.76, +0.37]
- TCP: NPS: 8 ABBA pairs, Welch +0.11% [-5.52, +5.74], cycles -0.79% [-1.75, +0.17]
- SS: NPS: 8 ABBA pairs, Welch -2.61% [-7.67, +2.44], cycles +0.59% [+0.09, +1.08]
- LTT_TCP_T1: setup: info string LocklessTT active; NPS: 8 ABBA pairs, Welch -5.66% [-10.26, -1.06], cycles -0.45% [-1.21, +0.32]
- TCP_T2: NPS: 8 ABBA pairs, Welch -1.12% [-6.93, +4.70], cycles -0.09% [-3.28, +3.21]; wall NPS +3.07% [-12.47, +21.36]
- LTT_TCP_T2: NPS: 8 ABBA pairs, Welch -1.87% [-8.95, +5.21], cycles +1.15% [-1.69, +4.07]; wall NPS +1.25% [-8.25, +11.75]
- SS_TCP: NPS: 8 ABBA pairs, Welch +0.47% [-2.95, +3.89], cycles +0.99% [+0.49, +1.50]
- SS_MKT: NPS: 8 ABBA pairs, Welch -0.68% [-4.66, +3.29], cycles +0.52% [-0.02, +1.06]
- CHP7_CM: NPS: 8 ABBA pairs, Welch -11.11% [-16.13, -6.08], cycles -9.77% [-10.47, -9.06]
- CHP7_CE: NPS: 8 ABBA pairs, Welch -7.54% [-10.16, -4.93], cycles -8.19% [-8.89, -7.49]
- CM_CE: NPS: 8 ABBA pairs, Welch -8.50% [-13.11, -3.90], cycles -9.09% [-10.26, -7.91]
- CHP7_CM_CE: NPS: 8 ABBA pairs, Welch -2.14% [-6.41, +2.13], cycles -4.35% [-4.88, -3.82]
- CM_CR: NPS: 8 ABBA pairs, Welch -10.29% [-13.93, -6.65], cycles -9.32% [-10.16, -8.48]
- CE_CR: NPS: 8 ABBA pairs, Welch -9.53% [-12.07, -6.99], cycles -9.68% [-10.39, -8.97]
- CM_CE_CR: NPS: 8 ABBA pairs, Welch -6.54% [-10.84, -2.23], cycles -6.82% [-7.41, -6.22]
- HR2_CHP7: NPS: 8 ABBA pairs, Welch -15.58% [-18.27, -12.89], cycles -16.41% [-17.16, -15.66]
- IT_CR: NPS: 8 ABBA pairs, Welch -4.51% [-7.57, -1.45], cycles -4.14% [-5.18, -3.09]
- NS99_V2R1: 2 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual fnv1a 5a7f7acb2d55004f | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual fnv1a 5a7f7acb2d55; NPS: 8 ABBA pairs, Welch -0.34% [-3.04, +2.37], cycles -1.38% [-1.96, -0.79]
- O2_THR: 2 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_t.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual threat inputs fnv1a db8c838b040e1b72 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_t.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual ; NPS: 8 ABBA pairs, Welch -41.54% [-44.09, -38.99], cycles -42.53% [-43.51, -41.53]
- O2_PP: 2 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_p.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual pawn-pair inputs fnv1a 12eb86f897f85ea1 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_p.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residu; NPS: 8 ABBA pairs, Welch -23.91% [-25.87, -21.94], cycles -22.96% [-23.55, -22.36]
- O2_OB8: 2 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_ob8.fnn2 king buckets 1 output buckets 8 hidden 256 unmirrored residual fnv1a db400d140d566e35 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_ob8.fnn2 king buckets 1 output buckets 8 hidden 256 unmirrored residual fnv1a db40; NPS: 8 ABBA pairs, Welch -5.77% [-9.04, -2.50], cycles -2.28% [-2.99, -1.57]
- THR_PP: 4 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_t_p.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual threat inputs pawn-pair inputs fnv1a 42e7a1bf47df654c | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_t_p.fnn2 king buckets 1 output buckets 1 hidden 256; NPS: 8 ABBA pairs, Welch -49.08% [-51.02, -47.13], cycles -48.50% [-48.87, -48.13]
- THR_OB8: 4 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_t_ob8.fnn2 king buckets 1 output buckets 8 hidden 256 unmirrored residual threat inputs fnv1a 06037c52509b4094 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_t_ob8.fnn2 king buckets 1 output buckets 8 hidden 256 unmirrored r; NPS: 8 ABBA pairs, Welch -42.26% [-44.50, -40.02], cycles -41.16% [-41.51, -40.82]
- PP_OB8: 4 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_p_ob8.fnn2 king buckets 1 output buckets 8 hidden 256 unmirrored residual pawn-pair inputs fnv1a 54694f7321e3b653 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_p_ob8.fnn2 king buckets 1 output buckets 8 hidden 256 unmirrore; NPS: 8 ABBA pairs, Welch -21.59% [-23.67, -19.50], cycles -22.12% [-22.61, -21.62]
- THR_PP_OB8: 6 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_t_p_ob8.fnn2 king buckets 1 output buckets 8 hidden 256 unmirrored residual threat inputs pawn-pair inputs fnv1a c91c78b0066ce282 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_t_p_ob8.fnn2 king buckets 1 output buckets 8 hi; NPS: 8 ABBA pairs, Welch -47.27% [-51.48, -43.06], cycles -48.19% [-48.74, -47.64]
- O2_THR_PP_OB8: 6 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_t_p_ob8.fnn2 king buckets 1 output buckets 8 hidden 256 unmirrored residual threat inputs pawn-pair inputs fnv1a c91c78b0066ce282 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_t_p_ob8.fnn2 king buckets 1 output buckets 8 hi; NPS: 8 ABBA pairs, Welch -48.71% [-51.16, -46.27], cycles -48.70% [-49.00, -48.40]
- H3DRIFT: A = first-pass base.exe, B = base_h3.exe: does the first-pass matrix still describe the final head?; NPS: 8 ABBA pairs, Welch -1.32% [-6.10, +3.47], cycles -4.61% [-5.20, -4.01]
- O2H3: NPS: 8 ABBA pairs, Welch +3.14% [-1.33, +7.62], cycles +3.04% [+2.15, +3.94]
- LAZYSW: NPS: 8 ABBA pairs, Welch +4.37% [-1.03, +9.77], cycles +4.36% [+2.92, +5.81]
- LAZY: NPS: 8 ABBA pairs, Welch +1.06% [-2.95, +5.08], cycles +3.26% [+2.41, +4.11]
- O2_LAZY: NPS: 8 ABBA pairs, Welch +8.11% [-0.66, +16.88], cycles +4.14% [+3.67, +4.62]
- LAZY_THR: 2 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_t.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual threat inputs fnv1a db8c838b040e1b72 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_t.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual ; NPS: 8 ABBA pairs, Welch -38.04% [-40.87, -35.21], cycles -37.99% [-38.43, -37.55]
- PROFSW: diagnostic build; the UCI Profile option never reaches bench (bench_searcher.set_profiling(bench_prof)); NPS: 8 ABBA pairs, Welch -7.71% [-12.15, -3.27], cycles -7.24% [-7.99, -6.50]
- PROF: NPS: 8 ABBA pairs, Welch -5.00% [-8.48, -1.53], cycles -8.27% [-8.85, -7.68]
- PROF_CM_CE: NPS: 8 ABBA pairs, Welch -15.56% [-21.50, -9.63], cycles -15.59% [-15.91, -15.27]
- INT16SW: NPS: 8 ABBA pairs, Welch -1.97% [-8.21, +4.28], cycles +1.79% [+0.70, +2.89]
- INT16: setup: info string NnueInt16 active; NPS: 8 ABBA pairs, Welch -11.06% [-15.65, -6.48], cycles -7.15% [-7.87, -6.42]
- O2_INT16: setup: info string NnueInt16 active; NPS: 8 ABBA pairs, Welch -3.78% [-9.01, +1.45], cycles -7.72% [-9.58, -5.81]
- INT16_LAZY: setup: info string NnueInt16 active; NPS: 8 ABBA pairs, Welch -8.62% [-13.67, -3.57], cycles -7.24% [-7.43, -7.04]
- INT16_THR: 2 transient setup ERROR line(s) over 2 processes (half-set v2 request while the options arrive one by one; resolved before readyok); setup: info string NnueInt16 active | info string NNUE v2: loaded F:\opus_scratch\r3\R3-2\nets\r1_t.fnn2 king buckets 1 output buckets 1 hidden 256 unmirrored residual threat inputs fnv1a db8c838b040e1b72 | info string NNUE v2: active: F:\opus_scratch\r3\R3-2\nets\r1_t.fnn2 king buckets 1 output buckets 1 ; NPS: 8 ABBA pairs, Welch -38.64% [-41.22, -36.05], cycles -39.00% [-39.54, -38.47]

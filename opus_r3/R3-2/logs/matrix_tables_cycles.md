| config | build / options | nodes d11 / d13 / d16 | Δnodes vs OFF | CPU NPS Δ% [95% CI] (cycle-timed CPU) | flag |
|---|---|---|---|---|---|
| OFF (OFF (base.exe, no options)) | base | 312866 / 862329 / 3024920 | 0 / 0 / 0 | — | ok |
| AA_T1 (A/A control T1 (base_copy.exe)) | (byte copy of base.exe) | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +0.06 [-0.66, +0.77] | ok |
| AA_T2 (A/A control T2 (base_copy.exe, Threads 2)) | (byte copy of base.exe) T2 | T2 go: mean 3,876,725 (varies) | n/a | +0.65 [-1.81, +3.17] | ok |
| CHP1 (CorrHistPlus=1) | base + CorrHistPlus=1 | 318363 / 915778 / 2347193 | +1.8% / +6.2% / -22.4% | -7.05 [-7.65, -6.45] | ok |
| CHP2 (CorrHistPlus=2) | base + CorrHistPlus=2 | 296553 / 824640 / 2914749 | -5.2% / -4.4% / -3.6% | -9.12 [-10.70, -7.53] | ok |
| CHP4 (CorrHistPlus=4) | base + CorrHistPlus=4 | 340927 / 734347 / 2794671 | +9.0% / -14.8% / -7.6% | -7.33 [-7.98, -6.68] | ok |
| CHP7 (CorrHistPlus=7) | base + CorrHistPlus=7 | 317529 / 866764 / 2715911 | +1.5% / +0.5% / -10.2% | -11.77 [-12.41, -11.13] | ok |
| CM (CorrMargins=1) | base + CorrMargins=1 | 343365 / 858019 / 2522546 | +9.7% / -0.5% / -16.6% | -4.29 [-4.91, -3.66] | ok |
| CE (CorrExt=1) | base + CorrExt=1 | 312961 / 838790 / 2891507 | +0.0% / -2.7% / -4.4% | -6.80 [-7.37, -6.24] | ok |
| CR (CuckooRep=true) | base + CuckooRep=true | 324211 / 790682 / 3148570 | +3.6% / -8.3% / +4.1% | -5.07 [-5.83, -4.30] | ok |
| MKT (MaterialKeyTable=true) | base + MaterialKeyTable=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +0.77 [+0.02, +1.53] | ok |
| NS99 (NetScale=99) | base + NetScale=99 | 308948 / 917342 / 2601047 | -1.3% / +6.4% / -14.0% | +0.87 [+0.25, +1.49] | ok |
| HR1 (HistRework=1) | base + HistRework=1 | 373261 / 1043893 / 3399770 | +19.3% / +21.1% / +12.4% | -9.37 [-9.65, -9.09] | ok |
| HR2 (HistRework=2) | base + HistRework=2 | 320427 / 881902 / 3041041 | +2.4% / +2.3% / +0.5% | -11.65 [-12.89, -10.39] | ok |
| IT (IntendedThreefold=true) | base + IntendedThreefold=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +0.02 [-0.41, +0.45] | ok |
| HD10 (HardDeadline=10) | base + HardDeadline=10 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +0.27 [-0.17, +0.72] | ok |
| SYZ (SyzygyPath=syzygy345) | base + SyzygyPath=syzygy345 | 313631 / 866959 / 2460490 | +0.2% / +0.5% / -18.7% | -8.16 [-9.12, -7.19] | ok |
| LTT_T1 (LocklessTT=true (T1)) | base + LocklessTT=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -0.55 [-1.27, +0.16] | ok |
| SEN_T1 (SmpExactNodes=true (T1)) | base + SmpExactNodes=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | — | ok |
| SBT_T1 (SmpBestThread=true (T1)) | base + SmpBestThread=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | — | ok |
| LTT_T2 (LocklessTT=true (T2)) | base + LocklessTT=true T2 | T2 go: mean 4,432,021 (varies) | n/a | +1.61 [-2.43, +5.82] | ok |
| SEN_T2 (SmpExactNodes=true (T2)) | base + SmpExactNodes=true T2 | T2 go: mean 4,076,902 (varies) | n/a | +0.66 [-1.01, +2.36] | ok |
| SBT_T2 (SmpBestThread=true (T2)) | base + SmpBestThread=true T2 | T2 go: mean 4,222,054 (varies) | n/a | -0.31 [-2.34, +1.76] | ok |
| V2R1 (v2 path: r1 replica, NNUEKingBuckets=1) | base + NNUEKingBuckets=1, NNUEFile=r1.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -1.14 [-1.73, -0.55] | ok |
| KB8 (NNUEKingBuckets=8 (rm8 replica)) | base + NNUEKingBuckets=8, NNUEFile=rm8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -6.18 [-6.97, -5.39] | ok |
| OB8 (NNUEOutputBuckets=8 (r1 + 8 heads)) | base + NNUEOutputBuckets=8, NNUEFile=r1_ob8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -1.53 [-2.14, -0.92] | ok |
| THR (NNUEThreats=1 (r1 + zero threats)) | base + NNUEThreats=1, NNUEFile=r1_t.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -41.13 [-41.44, -40.82] | ok |
| PP (NNUEPawnPairs=1 (r1 + zero pawn pairs)) | base + NNUEPawnPairs=1, NNUEFile=r1_p.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -21.46 [-22.45, -20.45] | ok |
| PURE (PureNnue=1 (r1 weights stand-alone)) | base + PureNnue=1, NNUEFile=r1_pure.fnn2 | 558939 / 1881923 / 9764737 | +78.7% / +118.2% / +222.8% | +13.40 [+13.07, +13.73] | ok |
| O2 (FORGE_NNUE_O2) | -DFORGE_NNUE_O2=1 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +0.13 [-0.24, +0.51] | ok |
| NOZERO (FORGE_NOZERO_MOVE_BUFFERS) | -DFORGE_NOZERO_MOVE_BUFFERS=1 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -4.16 [-4.60, -3.72] | ok |
| S13SW (FORGE_S13_TT_CHILD_PREFETCH, option off) | -DFORGE_S13_TT_CHILD_PREFETCH=1 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -0.70 [-1.76, +0.37] | ok |
| TCP (FORGE_S13_TT_CHILD_PREFETCH + TtChildPrefetch=true) | -DFORGE_S13_TT_CHILD_PREFETCH=1 + TtChildPrefetch=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -0.79 [-1.75, +0.17] | ok |
| SS (FORGE_SPEEDSTACK) | -DFORGE_SPEEDSTACK=1 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +0.59 [+0.09, +1.08] | ok |
| LTT_TCP_T1 (LocklessTT + TtChildPrefetch (T1)) | -DFORGE_S13_TT_CHILD_PREFETCH=1 + LocklessTT=true, TtChildPrefetch=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -0.45 [-1.21, +0.32] | ok |
| TCP_T2 (TtChildPrefetch=true (T2)) | -DFORGE_S13_TT_CHILD_PREFETCH=1 + TtChildPrefetch=true T2 | T2 go: mean 3,912,038 (varies) | n/a | -0.09 [-3.28, +3.21] | ok |
| LTT_TCP_T2 (LocklessTT + TtChildPrefetch (T2)) | -DFORGE_S13_TT_CHILD_PREFETCH=1 + LocklessTT=true, TtChildPrefetch=true T2 | T2 go: mean 3,996,999 (varies) | n/a | +1.15 [-1.69, +4.07] | ok |
| SS_TCP (FORGE_SPEEDSTACK + S13 switch + TtChildPrefetch (T1)) | -DFORGE_SPEEDSTACK=1 -DFORGE_S13_TT_CHILD_PREFETCH=1 + TtChildPrefetch=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +0.99 [+0.49, +1.50] | ok |
| SS_MKT (FORGE_SPEEDSTACK + MaterialKeyTable) | -DFORGE_SPEEDSTACK=1 + MaterialKeyTable=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +0.52 [-0.02, +1.06] | ok |
| CHP7_CM (CorrHistPlus=7 + CorrMargins) | base + CorrHistPlus=7, CorrMargins=1 | 285473 / 764223 / 2280251 | -8.8% / -11.4% / -24.6% | -9.77 [-10.47, -9.06] | ok |
| CHP7_CE (CorrHistPlus=7 + CorrExt) | base + CorrHistPlus=7, CorrExt=1 | 329635 / 858203 / 2950425 | +5.4% / -0.5% / -2.5% | -8.19 [-8.89, -7.49] | ok |
| CM_CE (CorrMargins + CorrExt) | base + CorrMargins=1, CorrExt=1 | 333285 / 903735 / 2610911 | +6.5% / +4.8% / -13.7% | -9.09 [-10.26, -7.91] | ok |
| CHP7_CM_CE (CorrHistPlus=7 + CorrMargins + CorrExt) | base + CorrHistPlus=7, CorrMargins=1, CorrExt=1 | 296551 / 730532 / 2597356 | -5.2% / -15.3% / -14.1% | -4.35 [-4.88, -3.82] | ok |
| CM_CR (CorrMargins + CuckooRep) | base + CorrMargins=1, CuckooRep=true | 362762 / 819649 / 2222921 | +15.9% / -4.9% / -26.5% | -9.32 [-10.16, -8.48] | ok |
| CE_CR (CorrExt + CuckooRep) | base + CorrExt=1, CuckooRep=true | 317563 / 800845 / 2653359 | +1.5% / -7.1% / -12.3% | -9.68 [-10.39, -8.97] | ok |
| CM_CE_CR (CorrMargins + CorrExt + CuckooRep) | base + CorrMargins=1, CorrExt=1, CuckooRep=true | 353437 / 944233 / 2459887 | +13.0% / +9.5% / -18.7% | -6.82 [-7.41, -6.22] | ok |
| HR2_CHP7 (HistRework=2 + CorrHistPlus=7) | base + HistRework=2, CorrHistPlus=7 | 352551 / 889835 / 3089398 | +12.7% / +3.2% / +2.1% | -16.41 [-17.16, -15.66] | ok |
| IT_CR (IntendedThreefold + CuckooRep) | base + IntendedThreefold=true, CuckooRep=true | 324211 / 790682 / 3148570 | +3.6% / -8.3% / +4.1% | -4.14 [-5.18, -3.09] | ok |
| NS99_V2R1 (NetScale=99 + v2 r1 replica) | base + NetScale=99, NNUEKingBuckets=1, NNUEFile=r1.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -1.38 [-1.96, -0.79] | CANCELS OUT: nodes = OFF although NS99 alone changes them |
| O2_THR (O2 + NNUEThreats) | -DFORGE_NNUE_O2=1 + NNUEThreats=1, NNUEFile=r1_t.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -42.53 [-43.51, -41.53] | ok |
| O2_PP (O2 + NNUEPawnPairs) | -DFORGE_NNUE_O2=1 + NNUEPawnPairs=1, NNUEFile=r1_p.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -22.96 [-23.55, -22.36] | ok |
| O2_OB8 (O2 + NNUEOutputBuckets=8) | -DFORGE_NNUE_O2=1 + NNUEOutputBuckets=8, NNUEFile=r1_ob8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -2.28 [-2.99, -1.57] | ok |
| THR_PP (NNUEThreats + NNUEPawnPairs) | base + NNUEThreats=1, NNUEPawnPairs=1, NNUEFile=r1_t_p.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -48.50 [-48.87, -48.13] | ok |
| THR_OB8 (NNUEThreats + NNUEOutputBuckets=8) | base + NNUEThreats=1, NNUEOutputBuckets=8, NNUEFile=r1_t_ob8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -41.16 [-41.51, -40.82] | ok |
| PP_OB8 (NNUEPawnPairs + NNUEOutputBuckets=8) | base + NNUEPawnPairs=1, NNUEOutputBuckets=8, NNUEFile=r1_p_ob8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -22.12 [-22.61, -21.62] | ok |
| THR_PP_OB8 (NNUEThreats + NNUEPawnPairs + NNUEOutputBuckets=8) | base + NNUEThreats=1, NNUEPawnPairs=1, NNUEOutputBuckets=8, NNUEFile=r1_t_p_ob8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -48.19 [-48.74, -47.64] | ok |
| O2_THR_PP_OB8 (O2 + NNUEThreats + NNUEPawnPairs + NNUEOutputBuckets=8) | -DFORGE_NNUE_O2=1 + NNUEThreats=1, NNUEPawnPairs=1, NNUEOutputBuckets=8, NNUEFile=r1_t_p_ob8.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -48.70 [-49.00, -48.40] | ok |
| H3DRIFT (final-head OFF exe (330237f3) vs first-pass OFF exe (467a59b3)) | base_h3 [head 330237f3] | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -4.61 [-5.20, -4.01] | ok |
| O2H3 (FORGE_NNUE_O2 at the final head) | -DFORGE_NNUE_O2=1 [head 330237f3] (A side: base_h3.exe) | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +3.04 [+2.15, +3.94] | ok |
| LAZYSW (FORGE_NNUE_LAZY_ACC, option off) | -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +4.36 [+2.92, +5.81] | ok |
| LAZY (FORGE_NNUE_LAZY_ACC + NnueLazyAcc=true) | -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) + NnueLazyAcc=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +3.26 [+2.41, +4.11] | ok |
| O2_LAZY (O2 + NnueLazyAcc (both change the compiled-in accumulator path)) | -DFORGE_NNUE_O2=1 -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) + NnueLazyAcc=true | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +4.14 [+3.67, +4.62] | ok |
| LAZY_THR (NnueLazyAcc + NNUEThreats (alias is compiled-in-net code; v2 path runs)) | -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) + NnueLazyAcc=true, NNUEThreats=1, NNUEFile=r1_t.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -37.99 [-38.43, -37.55] | ok |
| PROFSW (FORGE_PROF build, bench (counting off)) | -DFORGE_PROF=1 (+ src/profile.cpp) [head 330237f3] (A side: base_h3.exe) | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -7.24 [-7.99, -6.50] | ok |
| PROF (FORGE_PROF build, bench_prof (counting on)) | -DFORGE_PROF=1 (+ src/profile.cpp) [head 330237f3] (`bench_prof`) (A side: base_h3.exe) | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -8.27 [-8.85, -7.68] | ok |
| PROF_CM_CE (FORGE_PROF bench_prof + CorrMargins + CorrExt (counters inside the combined instance)) | -DFORGE_PROF=1 (+ src/profile.cpp) [head 330237f3] (`bench_prof`) (A side: base_h3.exe) + CorrMargins=1, CorrExt=1 | 333285 / 903735 / 2610911 | +6.5% / +4.8% / -13.7% | -15.59 [-15.91, -15.27] | ok |
| INT16SW (FORGE_NNUE_INT16, option off) | -DFORGE_NNUE_INT16=1 [head 330237f3] (A side: base_h3.exe) | 312866 / 862329 / 3024920 | 0 / 0 / 0 | +1.79 [+0.70, +2.89] | ok |
| INT16 (FORGE_NNUE_INT16 + NnueInt16=true) | -DFORGE_NNUE_INT16=1 [head 330237f3] (A side: base_h3.exe) + NnueInt16=true | 330610 / 858175 / 2760596 | +5.7% / -0.5% / -8.7% | -7.15 [-7.87, -6.42] | ok |
| O2_INT16 (O2 + NnueInt16 (the int16 hooks run before O2's float kernels)) | -DFORGE_NNUE_O2=1 -DFORGE_NNUE_INT16=1 [head 330237f3] (A side: base_h3.exe) + NnueInt16=true | 330610 / 858175 / 2760596 | +5.7% / -0.5% / -8.7% | -7.72 [-9.58, -5.81] | ok |
| INT16_LAZY (NnueInt16 + NnueLazyAcc (the alias drives the int16 accumulators)) | -DFORGE_NNUE_INT16=1 -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) + NnueInt16=true, NnueLazyAcc=true | 330610 / 858175 / 2760596 | +5.7% / -0.5% / -8.7% | -7.24 [-7.43, -7.04] | ok |
| INT16_THR (NnueInt16 + NNUEThreats (int16 applies to the compiled-in net only)) | -DFORGE_NNUE_INT16=1 [head 330237f3] (A side: base_h3.exe) + NnueInt16=true, NNUEThreats=1, NNUEFile=r1_t.fnn2 | 312866 / 862329 / 3024920 | 0 / 0 / 0 | -39.00 [-39.54, -38.47] | CANCELS OUT: nodes = OFF although INT16 alone changes them |

### Pair analysis (CPU NPS; log-additive prediction = sum of the parts' log ratios; for several v2 parts the v2-path cost (V2R1) is counted once)

| combination | nodes | measured Δ% [CI] | additive prediction Δ% | interaction (measured − predicted) [CI] | leave-one-out: part → alone vs added on top of the rest |
|---|---|---|---|---|---|
| LTT_TCP_T1 | node-exact parts: = lock pins | -0.45 [-1.21, +0.32] | -1.34 | +0.90 [-0.36, +2.18] | LTT_T1: -0.6% alone, +0.3% [-0.8, +1.5] on TCP; TCP: -0.8% alone, +0.1% [-0.8, +1.1] on LTT_T1 |
| LTT_TCP_T2 | T2: n/a | +1.15 [-1.69, +4.07] | +1.52 | -0.36 [-5.45, +4.99] | LTT_T2: +1.6% alone, +1.2% [-2.7, +5.3] on TCP_T2; TCP_T2: -0.1% alone, -0.5% [-4.9, +4.2] on LTT_T2 |
| SS_TCP | node-exact parts: = lock pins | +0.99 [+0.49, +1.50] | -0.21 | +1.21 [+0.12, +2.31] | SS: +0.6% alone, +1.8% [+0.8, +2.8] on TCP; TCP: -0.8% alone, +0.4% [-0.2, +1.0] on SS |
| SS_MKT | node-exact parts: = lock pins | +0.52 [-0.02, +1.06] | +1.36 | -0.83 [-1.74, +0.09] | SS: +0.6% alone, -0.2% [-1.1, +0.6] on MKT; MKT: +0.8% alone, -0.1% [-0.7, +0.6] on SS |
| CHP7_CM | new tree (differs from OFF and from every part) | -9.77 [-10.47, -9.06] | -15.56 | +6.85 [+5.68, +8.04] | CHP7: -11.8% alone, -5.7% [-6.6, -4.8] on CM; CM: -4.3% alone, +2.3% [+1.3, +3.3] on CHP7 |
| CHP7_CE | new tree (differs from OFF and from every part) | -8.19 [-8.89, -7.49] | -17.78 | +11.66 [+10.47, +12.86] | CHP7: -11.8% alone, -1.5% [-2.4, -0.6] on CE; CE: -6.8% alone, +4.1% [+3.1, +5.1] on CHP7 |
| CM_CE | new tree (differs from OFF and from every part) | -9.09 [-10.26, -7.91] | -10.80 | +1.91 [+0.47, +3.38] | CM: -4.3% alone, -2.5% [-3.8, -1.1] on CE; CE: -6.8% alone, -5.0% [-6.3, -3.7] on CM |
| CHP7_CM_CE | new tree (differs from OFF and from every part) | -4.35 [-4.88, -3.82] | -21.30 | +21.54 [+20.21, +22.90] | CHP7: -11.8% alone, +5.2% [+3.8, +6.6] on CM_CE; CM: -4.3% alone, +4.2% [+3.3, +5.1] on CHP7_CE; CE: -6.8% alone, +6.0% [+5.1, +6.9] on CHP7_CM |
| CM_CR | new tree (differs from OFF and from every part) | -9.32 [-10.16, -8.48] | -9.14 | -0.20 [-1.42, +1.03] | CM: -4.3% alone, -4.5% [-5.5, -3.4] on CR; CR: -5.1% alone, -5.3% [-6.2, -4.3] on CM |
| CE_CR | new tree (differs from OFF and from every part) | -9.68 [-10.39, -8.97] | -11.53 | +2.08 [+0.94, +3.24] | CE: -6.8% alone, -4.9% [-5.8, -3.9] on CR; CR: -5.1% alone, -3.1% [-4.0, -2.2] on CE |
| CM_CE_CR | new tree (differs from OFF and from every part) | -6.82 [-7.41, -6.22] | -15.32 | +10.04 [+8.75, +11.35] | CM: -4.3% alone, +3.2% [+2.2, +4.1] on CE_CR; CE: -6.8% alone, +2.8% [+1.7, +3.8] on CM_CR; CR: -5.1% alone, +2.5% [+1.1, +3.9] on CM_CE |
| HR2_CHP7 | new tree (differs from OFF and from every part) | -16.41 [-17.16, -15.66] | -22.05 | +7.23 [+5.48, +9.00] | HR2: -11.6% alone, -5.3% [-6.3, -4.3] on CHP7; CHP7: -11.8% alone, -5.4% [-6.9, -3.9] on HR2 |
| IT_CR | = CR (the one tree-changing part), as expected | -4.14 [-5.18, -3.09] | -5.05 | +0.95 [-0.33, +2.25] | IT: +0.0% alone, +1.0% [-0.3, +2.2] on CR; CR: -5.1% alone, -4.2% [-5.2, -3.1] on IT |
| NS99_V2R1 | = OFF, but NS99 alone changes the tree | -1.38 [-1.96, -0.79] | -0.28 | -1.10 [-2.00, -0.19] | NS99: +0.9% alone, -0.2% [-1.0, +0.5] on V2R1; V2R1: -1.1% alone, -2.2% [-3.0, -1.5] on NS99 |
| O2_THR | node-exact parts: = lock pins | -42.53 [-43.51, -41.53] | -41.05 | -2.51 [-4.22, -0.77] | O2: +0.1% alone, -2.4% [-4.1, -0.7] on THR; THR: -41.1% alone, -42.6% [-43.6, -41.6] on O2 |
| O2_PP | node-exact parts: = lock pins | -22.96 [-23.55, -22.36] | -21.35 | -2.04 [-3.41, -0.66] | O2: +0.1% alone, -1.9% [-3.3, -0.6] on PP; PP: -21.5% alone, -23.1% [-23.7, -22.4] on O2 |
| O2_OB8 | node-exact parts: = lock pins | -2.28 [-2.99, -1.57] | -1.40 | -0.90 [-1.81, +0.02] | O2: +0.1% alone, -0.8% [-1.6, +0.1] on OB8; OB8: -1.5% alone, -2.4% [-3.2, -1.7] on O2 |
| THR_PP | node-exact parts: = lock pins | -48.50 [-48.87, -48.13] | -53.23 | +10.10 [+8.49, +11.75] | THR: -40.4% alone, -34.4% [-35.3, -33.5] on PP; PP: -20.5% alone, -12.5% [-13.2, -11.8] on THR |
| THR_OB8 | node-exact parts: = lock pins | -41.16 [-41.51, -40.82] | -41.36 | +0.33 [-0.68, +1.35] | THR: -40.4% alone, -40.3% [-40.7, -39.8] on OB8; OB8: -0.4% alone, -0.1% [-0.8, +0.7] on THR |
| PP_OB8 | node-exact parts: = lock pins | -22.12 [-22.61, -21.62] | -21.77 | -0.45 [-1.91, +1.03] | PP: -20.5% alone, -20.9% [-21.5, -20.3] on OB8; OB8: -0.4% alone, -0.8% [-2.2, +0.5] on PP |
| THR_PP_OB8 | node-exact parts: = lock pins | -48.19 [-48.74, -47.64] | -53.41 | +11.20 [+9.10, +13.34] | THR: -40.4% alone, -33.5% [-34.2, -32.7] on PP_OB8; PP: -20.5% alone, -11.9% [-12.9, -10.9] on THR_OB8; OB8: -0.4% alone, +0.6% [-0.6, +1.8] on THR_PP |
| O2_THR_PP_OB8 | node-exact parts: = lock pins | -48.70 [-49.00, -48.40] | -53.35 | +9.96 [+8.01, +11.94] | O2: +0.1% alone, -1.0% [-2.1, +0.1] on THR_PP_OB8 |
| O2_LAZY | node-exact parts: = lock pins | +4.14 [+3.67, +4.62] | +6.39 | -2.12 [-3.22, -1.00] | O2H3: +3.0% alone, +0.9% [-0.0, +1.7] on LAZY; LAZY: +3.3% alone, +1.1% [+0.1, +2.0] on O2H3 |
| LAZY_THR | node-exact parts: = lock pins | -37.99 [-38.43, -37.55] | -36.27 | -2.70 [-3.84, -1.54] | LAZY: +3.3% alone, +0.5% [-0.5, +1.4] on THR; THR: -38.3% alone, -39.9% [-40.5, -39.4] on LAZY |
| PROF_CM_CE | = CM_CE (the one tree-changing part), as expected | -15.59 [-15.91, -15.27] | -12.58 | -3.45 [-4.84, -2.03] | PROF: -8.3% alone, -11.4% [-12.6, -10.2] on CM_CE; CM_CE: -4.7% alone, -8.0% [-8.6, -7.4] on PROF |
| O2_INT16 | = INT16 (the one tree-changing part), as expected | -7.72 [-9.58, -5.81] | -4.32 | -3.55 [-5.62, -1.43] | O2H3: +3.0% alone, -0.6% [-2.7, +1.5] on INT16; INT16: -7.1% alone, -10.4% [-12.3, -8.5] on O2H3 |
| INT16_LAZY | = INT16 (the one tree-changing part), as expected | -7.24 [-7.43, -7.04] | -4.12 | -3.25 [-4.24, -2.24] | INT16: -7.1% alone, -10.2% [-10.9, -9.4] on LAZY; LAZY: +3.3% alone, -0.1% [-0.9, +0.7] on INT16 |
| INT16_THR | = OFF, but INT16 alone changes the tree | -39.00 [-39.54, -38.47] | -42.69 | +6.44 [+5.12, +7.77] | INT16: -7.1% alone, -1.2% [-2.2, -0.1] on THR; THR: -38.3% alone, -34.3% [-35.0, -33.6] on INT16 |

### Option effect inside its own switch build (same exe, option on vs off: free of build-to-build layout effects)

| option | switch build, option off vs OFF exe | option on vs OFF exe | option on vs off (same exe) |
|---|---|---|---|
| TCP (FORGE_S13_TT_CHILD_PREFETCH + TtChildPrefetch=true) | -0.70 [-1.76, +0.37] | -0.79 [-1.75, +0.17] | -0.10 [-1.40, +1.22] |
| LAZY (FORGE_NNUE_LAZY_ACC + NnueLazyAcc=true) | +4.36 [+2.92, +5.81] | +3.26 [+2.41, +4.11] | -1.05 [-2.52, +0.44] |
| PROF (FORGE_PROF build, bench_prof (counting on)) | -7.24 [-7.99, -6.50] | -8.27 [-8.85, -7.68] | -1.10 [-2.02, -0.17] |
| INT16 (FORGE_NNUE_INT16 + NnueInt16=true) | +1.79 [+0.70, +2.89] | -7.15 [-7.87, -6.42] | -8.78 [-9.88, -7.66] |

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

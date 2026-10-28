| config | build / options | nodes d11 / d13 / d16 | Δnodes vs OFF | CPU NPS Δ% [95% CI] (cycle-timed CPU) | flag |
|---|---|---|---|---|---|
| OFF (OFF (base.exe, no options)) | base | — | — | — | not run |
| AA_T1 (A/A control T1 (base_copy.exe)) | (byte copy of base.exe) | — | — | — | not run |
| AA_T2 (A/A control T2 (base_copy.exe, Threads 2)) | (byte copy of base.exe) T2 | T2: varies | n/a | — | not run |
| CHP1 (CorrHistPlus=1) | base + CorrHistPlus=1 | — | — | — | not run |
| CHP2 (CorrHistPlus=2) | base + CorrHistPlus=2 | — | — | — | not run |
| CHP4 (CorrHistPlus=4) | base + CorrHistPlus=4 | — | — | — | not run |
| CHP7 (CorrHistPlus=7) | base + CorrHistPlus=7 | — | — | — | not run |
| CM (CorrMargins=1) | base + CorrMargins=1 | — | — | — | not run |
| CE (CorrExt=1) | base + CorrExt=1 | — | — | — | not run |
| CR (CuckooRep=true) | base + CuckooRep=true | — | — | — | not run |
| MKT (MaterialKeyTable=true) | base + MaterialKeyTable=true | — | — | — | not run |
| NS99 (NetScale=99) | base + NetScale=99 | — | — | — | not run |
| HR1 (HistRework=1) | base + HistRework=1 | — | — | — | not run |
| HR2 (HistRework=2) | base + HistRework=2 | — | — | — | not run |
| IT (IntendedThreefold=true) | base + IntendedThreefold=true | — | — | — | not run |
| HD10 (HardDeadline=10) | base + HardDeadline=10 | — | — | — | not run |
| SYZ (SyzygyPath=syzygy345) | base + SyzygyPath=syzygy345 | — | — | — | not run |
| LTT_T1 (LocklessTT=true (T1)) | base + LocklessTT=true | — | — | — | not run |
| SEN_T1 (SmpExactNodes=true (T1)) | base + SmpExactNodes=true | — | — | — | not run |
| SBT_T1 (SmpBestThread=true (T1)) | base + SmpBestThread=true | — | — | — | not run |
| LTT_T2 (LocklessTT=true (T2)) | base + LocklessTT=true T2 | T2: varies | n/a | — | not run |
| SEN_T2 (SmpExactNodes=true (T2)) | base + SmpExactNodes=true T2 | T2: varies | n/a | — | not run |
| SBT_T2 (SmpBestThread=true (T2)) | base + SmpBestThread=true T2 | T2: varies | n/a | — | not run |
| V2R1 (v2 path: r1 replica, NNUEKingBuckets=1) | base + NNUEKingBuckets=1, NNUEFile=r1.fnn2 | — | — | — | not run |
| KB8 (NNUEKingBuckets=8 (rm8 replica)) | base + NNUEKingBuckets=8, NNUEFile=rm8.fnn2 | — | — | — | not run |
| OB8 (NNUEOutputBuckets=8 (r1 + 8 heads)) | base + NNUEOutputBuckets=8, NNUEFile=r1_ob8.fnn2 | — | — | — | not run |
| THR (NNUEThreats=1 (r1 + zero threats)) | base + NNUEThreats=1, NNUEFile=r1_t.fnn2 | — | — | — | not run |
| PP (NNUEPawnPairs=1 (r1 + zero pawn pairs)) | base + NNUEPawnPairs=1, NNUEFile=r1_p.fnn2 | — | — | — | not run |
| PURE (PureNnue=1 (r1 weights stand-alone)) | base + PureNnue=1, NNUEFile=r1_pure.fnn2 | — | — | — | not run |
| O2 (FORGE_NNUE_O2) | -DFORGE_NNUE_O2=1 | — | — | -0.05 [-1.23, +1.15] | ok |
| NOZERO (FORGE_NOZERO_MOVE_BUFFERS) | -DFORGE_NOZERO_MOVE_BUFFERS=1 | — | — | -4.39 [-4.95, -3.82] | ok |
| S13SW (FORGE_S13_TT_CHILD_PREFETCH, option off) | -DFORGE_S13_TT_CHILD_PREFETCH=1 | — | — | — | not run |
| TCP (FORGE_S13_TT_CHILD_PREFETCH + TtChildPrefetch=true) | -DFORGE_S13_TT_CHILD_PREFETCH=1 + TtChildPrefetch=true | — | — | — | not run |
| SS (FORGE_SPEEDSTACK) | -DFORGE_SPEEDSTACK=1 | — | — | — | not run |
| LTT_TCP_T1 (LocklessTT + TtChildPrefetch (T1)) | -DFORGE_S13_TT_CHILD_PREFETCH=1 + LocklessTT=true, TtChildPrefetch=true | — | — | — | not run |
| TCP_T2 (TtChildPrefetch=true (T2)) | -DFORGE_S13_TT_CHILD_PREFETCH=1 + TtChildPrefetch=true T2 | T2: varies | n/a | — | not run |
| LTT_TCP_T2 (LocklessTT + TtChildPrefetch (T2)) | -DFORGE_S13_TT_CHILD_PREFETCH=1 + LocklessTT=true, TtChildPrefetch=true T2 | T2: varies | n/a | — | not run |
| SS_TCP (FORGE_SPEEDSTACK + S13 switch + TtChildPrefetch (T1)) | -DFORGE_SPEEDSTACK=1 -DFORGE_S13_TT_CHILD_PREFETCH=1 + TtChildPrefetch=true | — | — | — | not run |
| SS_MKT (FORGE_SPEEDSTACK + MaterialKeyTable) | -DFORGE_SPEEDSTACK=1 + MaterialKeyTable=true | — | — | — | not run |
| CHP7_CM (CorrHistPlus=7 + CorrMargins) | base + CorrHistPlus=7, CorrMargins=1 | — | — | — | not run |
| CHP7_CE (CorrHistPlus=7 + CorrExt) | base + CorrHistPlus=7, CorrExt=1 | — | — | — | not run |
| CM_CE (CorrMargins + CorrExt) | base + CorrMargins=1, CorrExt=1 | — | — | — | not run |
| CHP7_CM_CE (CorrHistPlus=7 + CorrMargins + CorrExt) | base + CorrHistPlus=7, CorrMargins=1, CorrExt=1 | — | — | — | not run |
| CM_CR (CorrMargins + CuckooRep) | base + CorrMargins=1, CuckooRep=true | — | — | — | not run |
| CE_CR (CorrExt + CuckooRep) | base + CorrExt=1, CuckooRep=true | — | — | — | not run |
| CM_CE_CR (CorrMargins + CorrExt + CuckooRep) | base + CorrMargins=1, CorrExt=1, CuckooRep=true | — | — | — | not run |
| HR2_CHP7 (HistRework=2 + CorrHistPlus=7) | base + HistRework=2, CorrHistPlus=7 | — | — | — | not run |
| IT_CR (IntendedThreefold + CuckooRep) | base + IntendedThreefold=true, CuckooRep=true | — | — | — | not run |
| NS99_V2R1 (NetScale=99 + v2 r1 replica) | base + NetScale=99, NNUEKingBuckets=1, NNUEFile=r1.fnn2 | — | — | — | not run |
| O2_THR (O2 + NNUEThreats) | -DFORGE_NNUE_O2=1 + NNUEThreats=1, NNUEFile=r1_t.fnn2 | — | — | — | not run |
| O2_PP (O2 + NNUEPawnPairs) | -DFORGE_NNUE_O2=1 + NNUEPawnPairs=1, NNUEFile=r1_p.fnn2 | — | — | — | not run |
| O2_OB8 (O2 + NNUEOutputBuckets=8) | -DFORGE_NNUE_O2=1 + NNUEOutputBuckets=8, NNUEFile=r1_ob8.fnn2 | — | — | — | not run |
| THR_PP (NNUEThreats + NNUEPawnPairs) | base + NNUEThreats=1, NNUEPawnPairs=1, NNUEFile=r1_t_p.fnn2 | — | — | — | not run |
| THR_OB8 (NNUEThreats + NNUEOutputBuckets=8) | base + NNUEThreats=1, NNUEOutputBuckets=8, NNUEFile=r1_t_ob8.fnn2 | — | — | — | not run |
| PP_OB8 (NNUEPawnPairs + NNUEOutputBuckets=8) | base + NNUEPawnPairs=1, NNUEOutputBuckets=8, NNUEFile=r1_p_ob8.fnn2 | — | — | — | not run |
| THR_PP_OB8 (NNUEThreats + NNUEPawnPairs + NNUEOutputBuckets=8) | base + NNUEThreats=1, NNUEPawnPairs=1, NNUEOutputBuckets=8, NNUEFile=r1_t_p_ob8.fnn2 | — | — | — | not run |
| O2_THR_PP_OB8 (O2 + NNUEThreats + NNUEPawnPairs + NNUEOutputBuckets=8) | -DFORGE_NNUE_O2=1 + NNUEThreats=1, NNUEPawnPairs=1, NNUEOutputBuckets=8, NNUEFile=r1_t_p_ob8.fnn2 | — | — | — | not run |
| H3DRIFT (final-head OFF exe (330237f3) vs first-pass OFF exe (467a59b3)) | base_h3 [head 330237f3] | — | — | — | not run |
| O2H3 (FORGE_NNUE_O2 at the final head) | -DFORGE_NNUE_O2=1 [head 330237f3] (A side: base_h3.exe) | — | — | — | not run |
| LAZYSW (FORGE_NNUE_LAZY_ACC, option off) | -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) | — | — | — | not run |
| LAZY (FORGE_NNUE_LAZY_ACC + NnueLazyAcc=true) | -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) + NnueLazyAcc=true | — | — | — | not run |
| O2_LAZY (O2 + NnueLazyAcc (both change the compiled-in accumulator path)) | -DFORGE_NNUE_O2=1 -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) + NnueLazyAcc=true | — | — | — | not run |
| LAZY_THR (NnueLazyAcc + NNUEThreats (alias is compiled-in-net code; v2 path runs)) | -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) + NnueLazyAcc=true, NNUEThreats=1, NNUEFile=r1_t.fnn2 | — | — | — | not run |
| PROFSW (FORGE_PROF build, bench (counting off)) | -DFORGE_PROF=1 (+ src/profile.cpp) [head 330237f3] (A side: base_h3.exe) | — | — | — | not run |
| PROF (FORGE_PROF build, bench_prof (counting on)) | -DFORGE_PROF=1 (+ src/profile.cpp) [head 330237f3] (`bench_prof`) (A side: base_h3.exe) | — | — | — | not run |
| PROF_CM_CE (FORGE_PROF bench_prof + CorrMargins + CorrExt (counters inside the combined instance)) | -DFORGE_PROF=1 (+ src/profile.cpp) [head 330237f3] (`bench_prof`) (A side: base_h3.exe) + CorrMargins=1, CorrExt=1 | — | — | — | not run |
| INT16SW (FORGE_NNUE_INT16, option off) | -DFORGE_NNUE_INT16=1 [head 330237f3] (A side: base_h3.exe) | — | — | — | not run |
| INT16 (FORGE_NNUE_INT16 + NnueInt16=true) | -DFORGE_NNUE_INT16=1 [head 330237f3] (A side: base_h3.exe) + NnueInt16=true | — | — | — | not run |
| O2_INT16 (O2 + NnueInt16 (the int16 hooks run before O2's float kernels)) | -DFORGE_NNUE_O2=1 -DFORGE_NNUE_INT16=1 [head 330237f3] (A side: base_h3.exe) + NnueInt16=true | — | — | — | not run |
| INT16_LAZY (NnueInt16 + NnueLazyAcc (the alias drives the int16 accumulators)) | -DFORGE_NNUE_INT16=1 -DFORGE_NNUE_LAZY_ACC=1 [head 330237f3] (A side: base_h3.exe) + NnueInt16=true, NnueLazyAcc=true | — | — | — | not run |
| INT16_THR (NnueInt16 + NNUEThreats (int16 applies to the compiled-in net only)) | -DFORGE_NNUE_INT16=1 [head 330237f3] (A side: base_h3.exe) + NnueInt16=true, NNUEThreats=1, NNUEFile=r1_t.fnn2 | — | — | — | not run |

### Pair analysis (CPU NPS; log-additive prediction = sum of the parts' log ratios; for several v2 parts the v2-path cost (V2R1) is counted once)

| combination | nodes | measured Δ% [CI] | additive prediction Δ% | interaction (measured − predicted) [CI] | leave-one-out: part → alone vs added on top of the rest |
|---|---|---|---|---|---|

### Option effect inside its own switch build (same exe, option on vs off: free of build-to-build layout effects)

| option | switch build, option off vs OFF exe | option on vs OFF exe | option on vs off (same exe) |
|---|---|---|---|

### Flagged
- none

### Notes per configuration (setup info lines, transient half-set ERROR lines, other notes)
- IT: bench positions carry no game history, so no claim can fire
- HD10: bench is unclocked
- PURE: no function-preserving pure net exists: the HCE term is dropped
- O2: NPS: 8 ABBA pairs, Welch -0.37% [-3.02, +2.28], cycles -0.05% [-1.23, +1.15]
- NOZERO: NPS: 8 ABBA pairs, Welch -4.45% [-6.79, -2.12], cycles -4.39% [-4.95, -3.82]
- H3DRIFT: A = first-pass base.exe, B = base_h3.exe: does the first-pass matrix still describe the final head?
- PROFSW: diagnostic build; the UCI Profile option never reaches bench (bench_searcher.set_profiling(bench_prof))

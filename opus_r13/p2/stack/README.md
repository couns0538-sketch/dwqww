# P2 speed stack (r10fix1 + S1 LargePages, R12 bundle recipe) and FORGE_ALIGN_WEIGHTS - UNPROVEN, for QA's timing

Two node-identical LTO+PGO exes (pc1 = pc2 each). No speed claim: QA does the official timing; my ABBA was neutral.
| exe (C:\o13\handoff\p2_stack\) | sha256 | source |
|---|---|---|
| forge_ltopgo_stk_align0.exe | ff6628ce2b7391428a06d9234d3ba7f8d61d879d0155612df1239eb0e646a557 | r10fix1 7f79c349 + stack_s1_port.patch + stack_align.patch (switch 0) |
| forge_ltopgo_stka_align1.exe | 302ad8fba36c09f16f0c871bb080697f912e3360e4943a3b8a7077060bfafd4f | same + `#define FORGE_ALIGN_WEIGHTS 1` (one line, large_pages.hpp) |
| forge_ltopgo_stks_sparse1.exe | 6fdf46dcf80555a1cbb94d88ea9f4368a7127312a83de23b6358056d170057d2 | stack + stack_sparse.patch with `#define FORGE_SPARSE_L1 1` (HalfKA find-nnz L1; PGO profile with it ON) |
Build: Coder's kit v2.4 (`qa_r12fix\pkg\coder_5d93a8e1\kit_v24\build_ltopgo.ps1`, md5 a9bbedf9) `-Workload v2.1
-NetE19 r11_e19_final_bf1e347c.nnue -NetE9 r11_e9_best_5380f866.nnue -PartialTraining -Expose` = the recipe of the R12
bundle exe 7D5081E3 (QA's q12_w21pt). Not comparable with workload-v1 builds such as FD3A5190 without saying so.

## Identity (all PASS; ../RESULTS.md)
- OFF (no setoption) d11-d22 = 312866/862329/3024920/12389307/34048354, perft 4865609/193690690, per-FEN d13 nodes.
- `LargePages true` = OFF nodes (on this PC: 'LargePages: on (2 MiB NNUE w1)', 'on (32 MiB TT)').
- `EvalFileHalfKA` e19 / e9 = plain D8D90B68 counts; 12k-FEN exe identity 12000/12000 for both nets and both exes.
- CI ASan+UBSan self-play (default, LargePages=true): PASS.

## Timing lines for QA (UNPROVEN)
- S1 + R12 recipe: stk_align0 vs the R12 bundle 7D5081E3 (same recipe; adds S1) or vs D8D90B68 / FD3A5190, with
  `setoption name LargePages value true` on the stack side; with and without `EvalFileHalfKA` e19.
- Alignment: stka_align1 vs stk_align0, both with LargePages false (the heap path is where alignment changes).
- Sparse L1: stks_sparse1 vs stk_align0 (both v2.1 + partial training), with `EvalFileHalfKA` e19 (the kernel only runs
  with a HalfKA net), LargePages false on both sides.

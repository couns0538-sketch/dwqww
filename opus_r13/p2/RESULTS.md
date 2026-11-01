# R13 Phase 2 - speed stack, weight alignment, net-path PGO (block 1: steps 1, 1a, 1b) - IN PROGRESS

Branch `opus-r13-p2-sparse-l1` (from main). All speed results UNPROVEN: no speed claim; QA does the official timing.
Scratch on C:\o13\p2 (F: was under its 50 GB floor).

## Step 1 - stack = R12 bundle recipe + S1 LargePages
- Base: **r10fix1 source = git 7f79c349** (lock + EvalFileHalfKA, OFF = lock pins). Reason: the R12 bundle exe 7D5081E3
  is QA's build `q12_w21pt` from `F:/opus_scratch/r12/src_r10fix1` (QA log qa_r12fix/logs/build_q12_w21pt_pc1.out: units incl.
  nnue_halfka, workload v2.1, partial training, expose True). The "R12 bundle" is that build recipe: Coder's kit v2.4
  (`qa_r12fix/pkg/coder_5d93a8e1/kit_v24`, build_ltopgo.ps1 md5 a9bbedf9) with `-Workload v2.1 -PartialTraining -Expose`.
  `git archive 7f79c349 src include` = 22 files, equal to `cands/r10fix1/forge_r10fix1_src`.
- S1 LargePages (0A22484F): `s1_largepages_vs_FD3A5190src.patch` (md5 24f983eb, made on the lock source) applied to r10fix1
  with `patch -p1 -F0`: all src/include hunks apply except two `#include "forge/large_pages.hpp"` lines (r10fix1 has
  `nnue_halfka.hpp` there), placed by hand next to the same neighbour. Line set vs the original src/include hunks: EQUAL
  (logs/s1_port_lineset.txt). Patch: stack/stack_s1_port.patch (applies on r10fix1 src/include).
- Build with QA's kit v2.4 called directly on CPUs 2-3 (the R12 chain needs a QA-freed pair + QA's go-file; builds are not timing).

## Step 1a - FORGE_ALIGN_WEIGHTS (build switch, default 0)
- 1 = heap weight storage 64-byte aligned: lock net float w1 (`large_pages::make_weight_array`), HalfKA ft_weight / ft_bias /
  stack weights (`large_pages::WeightVector`). 0 = S1's code (std::vector / new T[n]()). Patch: stack/stack_align.patch,
  script: tools/port_align.py.
- Probe (same helpers as the engine, 4 rounds with other heap use): switch 0 -> w1 at **48 mod 64** (misaligned; the
  profile saw 16 mod 64), ft_weight / ft_bias 0 mod 64 by chance (large block); switch 1 -> all 0 mod 64. logs/probe.out.

| check | align 0 | align 1 | evidence |
|---|---|---|---|
| plain build (lock g++ line + Expose), warnings / vfmadd | 0 / 0 (2cc718f3…) | 0 / 0 (8a41b4cb…) | - |
| OFF bench d11-d22 = 312866/862329/3024920/12389307/34048354, perft 4865609/193690690, 8 per-FEN d13 | PASS | PASS | logs/plain_a*_off.json |
| LargePages=true (on this PC: 'LargePages: on (2 MiB NNUE w1)', 'on (32 MiB TT)'): nodes = OFF pins | PASS | PASS | logs/plain_a*_lp.json |
| EvalFileHalfKA e19 = D8D90B68 counts 373062/831975/4115992/17885060/37006232 | PASS | PASS | logs/plain_a*_e19.json |
| EvalFileHalfKA e9 = D8D90B68 counts 287095/693432/2816047/12332089/25323515 | PASS | PASS | logs/plain_a*_e9.json |
| kit v2.4 (workload v2.1 + -PartialTraining + -Expose) pc1 = pc2 exe sha256 | **ff6628ce2b7391428a06d9234d3ba7f8d61d879d0155612df1239eb0e646a557** | **302ad8fba36c09f16f0c871bb080697f912e3360e4943a3b8a7077060bfafd4f** | logs/kit_stk*/SUMMARY_pc*.txt |
| kit identity, plain = LTO+PGO: OFF pins + perft + per-FEN; LargePages=true IDENTICAL to OFF; e19 / e9 = pins, live | ALL OK (4 sets) | ALL OK (4 sets) | logs/kit_stk*/*.compare.txt |
| step 1b: real -Wmissing-profile warnings with the net-path profile (no net + e19 + e9 passes) / vfmadd | 0 / 0 | 0 / 0 | SUMMARY |
| 12k-FEN exe identity vs plain D8D90B68 (go depth 2: depth, score, nodes, bestmove), e19 and e9 | 12000/12000 both nets | 12000/12000 both nets | logs/f12k_*_compare.txt |
| CI ASan+UBSan self-play (Linux g++ 13.3; no net on the runner), default and LargePages=true: 0 sanitizer lines, 0 illegal | PASS | PASS | logs/ci_san_41211359051.txt (run 41211359051) |

## Advisory ABBA, align 1 (302ad8fb) vs align 0 (ff6628ce) - NOT official (QA times)
r12_speed.py (opus-r12-pgo-net), CPU 2 with sibling CPU 3 idle (pair freed by the owner), BelowNormal, fresh process per
run, 10 palindromic pairs + 3 A/A pairs per exe against byte copies, bench d16 / d20, Threads 1 Hash 16, nodes equal.
| net | depth | engine nps median | 2-sided 95% | cpu nps median | A/A noise (median, both exes) |
|---|---|---|---|---|---|
| none (AL1 embedded, the profiled w1 path) | d16 | -0.07% | [-2.32%, +0.22%] | -0.58% | +0.8 .. +3.5% |
| none | d20 | -0.92% | [-2.22%, -0.17%] | -0.28% | +2.7 .. +3.5% |
| e19 | d16 | +0.37% | [-0.76%, +0.47%] | +0.13% | +0.8 .. +1.7% |
| e19 | d20 | +0.89% | [-1.42%, +2.48%] | -0.03% | -0.6 .. +0.1% |
**Verdict: neutral** (every interval inside the A/A noise; no gain >= +1%). The misalignment is real (w1 48 mod 64 without
the switch) but costs nothing measurable in these LTO+PGO builds. Handed over as a node-identical switch build for QA's
official timing; where the time goes (perf-style sampling) is left for the sparse-L1 step. Logs: logs/abba_align_*.

## Step 1b - net-path PGO (built: both exes above use it)
Kit v2.4 workload v2.1 profiles three passes: no net, EvalFileHalfKA = e19, = e9 (bench 11/13/16 + 8 x `go nodes 200000`, Threads 1).
To prove: 0 real -Wmissing-profile warnings, pc1 = pc2 (v2.1 + partial training reproduced in R12 and QA's w21pt).

## Step 2 - sparse L1 (find-nnz), build switch FORGE_SPARSE_L1 (default 0) - IN PROGRESS
- Where: the HalfKA block kernel (`block_affine`, used for fc_0 and fc_1). It already skipped all-zero 4-byte blocks, but
  scanned and multiplied in one loop with one dependent dpbusd chain per output group. Switch 1: phase 1 lists the
  non-zero blocks (same masks), phase 2 multiplies only those with 4 (NQ = 1) or 2 independent accumulator chains, summed
  at the end. Integer sums without saturation -> bit-identical by construction. AVX-512 VNNI and AVX2 paths; switch 0 =
  the old kernel (renamed block_affine_dense, called through an inline wrapper). Own code; the find-nnz idea is public.
- Patch: stack/stack_sparse.patch (on top of stack_s1_port + stack_align), script tools/port_sparse.py.
- Builds: plain znver5 sparse (70e1b4a4, vpdpbusd 49x), plain AVX2 sparse -march=x86-64-v3 (87ec8e98, 0 zmm), both 0 warnings.
- FTP1-permuted net: NEEDS_INPUT - no FTP1 net file found (forge_pushin, F:orge_nnue_train, D:\grok-pc-data, depth 3);
  parity runs on e19 / e9.

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
| kit v2.4 (v2.1 + partial training + Expose) pc1 = pc2, identity incl. LargePages / e19 / e9 pins | RUNNING (tag stk) | RUNNING (tag stka) | - |

## Step 1b - net-path PGO
Kit v2.4 workload v2.1 profiles three passes: no net, EvalFileHalfKA = e19, = e9 (bench 11/13/16 + 8 x `go nodes 200000`, Threads 1).
To prove: 0 real -Wmissing-profile warnings, pc1 = pc2 (v2.1 + partial training reproduced in R12 and QA's w21pt).

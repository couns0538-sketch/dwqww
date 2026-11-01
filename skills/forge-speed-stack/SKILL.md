---
name: forge-speed-stack
description: Build and prove Forge speed-only stacks on the PC (R13 P2) - r10fix1 (HalfKA) + S1 LargePages with the R12 bundle recipe (kit v2.4 workload v2.1 + partial training), node-identical build switches such as FORGE_ALIGN_WEIGHTS, alignment probes, 12k-FEN exe identity, advisory palindromic ABBA with A/A copies. Use for any speed switch, speed stack, net-path PGO build or "is this faster" question before QA's official timing.
---

# Speed stack (R13 P2, 2026-10-31)
Rules: [[forge-pc-rules]]; kit: [[forge-ltopgo-pgo]]; checks: [[forge-candidate-checks]]. Tools: branch
opus-r13-p2-sparse-l1 `opus_r13/tools/` (kit24_build.sh, port_align.py) + the P1 tools.

## Recipe
1. Base: r10fix1 = git 7f79c349 (`git -c core.autocrlf=false archive 7f79c349 src include`, 22 files) = lock + EvalFileHalfKA.
   The "R12 bundle" (7D5081E3) is a build recipe on that source, not a patch.
2. S1 LargePages: `qa_s1lp_20261031\FORGE_S1_LARGEPAGES_SRC.zip` -> `s1_largepages_vs_FD3A5190src.patch` (lock-based):
   src/include hunks apply with -F0 except two `#include "forge/large_pages.hpp"` lines (place next to the same neighbour).
3. Build: `kit24_build.sh <repo> <tag> <mask> [sides]` = kit v2.4 `-Workload v2.1 -NetE19 -NetE9 -PartialTraining -Expose`,
   CheckOpt LargePages=true (pins = OFF) and EvalFileHalfKA e19 / e9 (pins = D8D90B68 counts). pc1 = pc2 binding.
   The R12 chain (`r12_build_chain.py`) needs a QA-freed pair + QA's GO_PAIR file: do not create that file; call the kit.
4. Build switches: the kit takes no -D flags -> make a source variant whose default is flipped (one-line commit in an LF
   clone: `git -c core.autocrlf=false clone`; a plain clone checks out CRLF here and the commit rewrites every line).
5. Proof: plain identity (OFF, LargePages, nets), kit identity, `r12_fens12k.py --cpu 2 --net <net> --fens
   opus-r10-halfka:opus_r10/parity/fens_12k.txt --depth 2 --exe D8=<plain d8d90b68> --exe X=<new>` (12000/12000), CI ASan+UBSan.
6. Advisory speed: `r12_speed.py --cpu 2 --ignore-idle --pairs 10 --aa-pairs 3 --depths 16 20 --exe A0=.. --exe A1=..
   --ref A0 --aa A0=<byte copy> --aa A1=<byte copy> [--net e19]` (only when the owner freed CPUs 2-3; it waits while any
   non-Idle process other than its own holds the pair). Report median + intervals + A/A noise; < +1% = neutral.

## Results (R13)
- stk_align0 ff6628ce / stka_align1 302ad8fb: identity ALL OK, 12k 12000/12000 (e19, e9), CI PASS.
- Probe: lock w1 at 48 mod 64 without the switch, 0 with it. ABBA align1 vs align0: neutral (no net d16 -0.07%, d20 -0.92%;
  e19 d16 +0.37%, d20 +0.89%; A/A noise up to ~3%).

## Pitfalls
- Never edit a bash script while an instance of it runs (bash reads it incrementally: the running copy died with
  "unexpected EOF"). Copy to a new name instead.
- A load gate inside a wrapper must wait and retry, not exit: two own builds in parallel pushed total CPU over 85% once.

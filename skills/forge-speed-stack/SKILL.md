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

## Sparse L1 (find-nnz) result, R13 P2 step 2 - negative, keep for the record
- The HalfKA `block_affine` already skips all-zero 4-byte blocks (mask + countr_zero loop). A two-phase find-nnz version
  (index list, then 2-4 independent dpbusd chains) was bit-identical (pins, 12k 12000/12000, AVX-512 and AVX2) but SLOWER:
  LTO+PGO -12..-14%, plain -8% (also after removing ___chkstk_ms with a 1 KiB list and forcing inline). Do not retry the
  same design; next ideas: a sampling profile first (-pg on a copy), vpcompressw phase 1, fusing the list into the FT pack.
- A Windows stack array > 4 KiB in a hot function costs a `___chkstk_ms` probe per call (seen in objdump).

## Node-identical search speed switch on the LOCK tree (R14 Main 2, FORGE_SEARCH_SPEED2)
- Port = anchored script on a fresh lock copy (`opus_r13/p2/speed2/port_speed2.py`, branch opus-r13-p2-sparse-l1): every
  change inside `#if SWITCH ... #else <lock lines> #endif`, so the patch only ADDS lines (+91 / -0) and switch 0 keeps the
  lock's code; `--default 1` writes the kit variant (the kit takes no -D flags; variants differ in one `#define`).
- Proof: plain builds at 0 and 1 (`plain_build.sh <repo> <out> -DSWITCH=1`), kit lp_check `compare` of the two runs with
  `--pins/--perft-pins` (bench, perft, 8 FENs, bestmoves). A speed switch cannot show "ON differs from OFF" in nodes: show
  liveness in codegen instead (objdump counts: prefetch 3 -> 5, modulo-by-6 imul 0x2aaaaaab 68 -> 11) and diff the `uci`
  output (must be identical: no new options).
- Kit builds on D: per the R14 scratch rule: `opus_r13/p2/speed2/kit_build_r14.sh` (= R13 kit_build.sh with work dir
  D:\o14a\w, exports D:\o14a\src, disk gate on D:); KIT_SIDES=pc1 for a one-sided identity build. A kit build of the
  switch-0 source vs the lock exe's sha256 tells whether the preprocessor-only change reproduces the lock byte for byte.
- ABBA: `r12_speed.py --cpu 2 --ignore-idle` ignores Idle-class processes, including MY OWN Idle jobs on the pair: start it
  only after them (it does wait for non-Idle own builds).
- The lock already prefetches the child TT cluster after make_move in qsearch and in the main loop; the null move and the
  ProbCut make did not (R14 adds those two sites).
- r12_speed.py pitfall (R14): its "own process" test knows only its own PID; the venv's `.venv\Scripts\python.exe` is a
  launcher that starts the real cpython as a CHILD, so the launcher (same command line, own affinity) shows up as a busy
  non-Idle python on the pair and the run waits forever. Start the driver at **Idle** (`run_low.ps1 -Prio Idle`) with
  `--ignore-idle` (the engine runs still get BelowNormal from the tool), or lower the own launcher to Idle by handle.

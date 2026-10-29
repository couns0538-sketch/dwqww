# N2 proposal (R5B): O2 + NOZERO + SPEEDSTACK in one node-exact build — UNPROVEN, no Elo claim

Branch `opus-r5b-speed` (base `forge-bundle-int` b7c1772). Details and logs: `REPORT.md` (M1-M4).

## Candidate and opponent (PC lock recipe, `-march=znver5`)

| role | exe (F:\opus_scratch\r5\r5b\exe) | sha256 | flags on top of the recipe |
|---|---|---|---|
| candidate N2 | `forge_r5b_n2_z5_b2983d07.exe` | `1823fe614065211d50ff2fad36860dcd7ccadb35a3b3fbd78c68ad4f32f27ca4` | `-DFORGE_NNUE_O2=1 -DFORGE_NOZERO_MOVE_BUFFERS=1 -DFORGE_SPEEDSTACK=1` |
| opponent OFF | `forge_r5b_off_z5_m1fix.exe` | `ca5b9331b8fe9132cac958bc7687f2d872aa60e997fde6eb5bd8b9508c6f1858` | none (code = b7c1772 OFF; 4 bytes PE timestamp differ) |
| alternative (job-spec flags `-march=x86-64-v3 -mtune=znver5`) | `forge_r5b_n2_v3_b2983d07.exe` vs `forge_r5b_off_v3_m1fix.exe` | `faac168d92a18f7a2eb2164655c5907d75fe26fc91cd0f0ae7589c913041aee5` / `241368e87d4ed9f4b247c840e0d18b42d8028b5543d7710d2b3b728f0e1350cc` | same |

Recipe: MSYS2 ucrt64 g++ 15.2, `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math
-march=znver5 -pthread -static` (`opus_r5/r5b/tools/build_r5b.sh`, RECIPE=znver5). Engine tree: commit b2983d07 (the M1
fix); later commits add only a test-only macro, tools and reports (N2 rebuilt from the final head: see REPORT.md
"Final checks").

## What changed in O2 (M1)

On `-march=znver5` the O2 AVX2 kernels were compiled out by the guard `FORGE_NNUE_AVX2 && !defined(__AVX512F__)`
(`src/nnue.cpp`), so a PC O2 build ran the portable accumulator loops. Fix (commit b2983d07, all under
`#if FORGE_NNUE_O2`): a 512-bit `Vec` for AVX-512 targets in the existing kernel templates (fused update kernels,
register-blocked refresh), same per-lane operations in the same order, no FMA. O2 builds print
`info string nnue kernel: accumulator avx512, output avx2` at `uci`. Bit parity vs AL1 s198: PASS, digest
`f807d80cbabc1d59` for the AVX-512, AVX2 and forced-scalar builds.

## Identity (Threads 1, Hash 16, OwnBook false; lock `uci_check.py --full`)

| exe | bench d11 / d13 / d16 / d20 / d22 | perft 5 | kiwipete 5 | FMA | result |
|---|---|---|---|---|---|
| N2 znver5 | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK |
| OFF znver5 | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK |
| N2 v3, OFF v3 | same | same | same | 0 | ALL OK |

## NPS (TBD: filled in from REPORT.md M3 pass 3 and the quiet-runner run)

## Non-regression evidence (M4)

- (a) go depth 18 on 50 self-play positions, N2 znver5 vs OFF znver5: 50/50 identical bestmove, nodes, score and pv.
- (b) 200-game smoke N2 vs OFF at 5+0.05, Threads 1: (TBD).
- (c) uninitialised reads: poisoned move buffers (0xFE, 0x5A) identity ALL OK; valgrind memcheck of OFF and N2 and
  ASan/UBSan + TSan of N2 on CI (opus-r5b-n2) green.

## Proposed gate (we do not run it; queue owner fills srand and openings start)

(TBD: final spec block after the NPS rows.)

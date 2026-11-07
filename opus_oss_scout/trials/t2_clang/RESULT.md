# T2 clang build of the lock source - RESULT (SCREENING, shared PC)

Tool: LLVM clang. The installed 18.1.8 failed (below), so llvm-mingw 20261104 was used: clang 23.1.5, ISC + LLVM
Apache-2.0 WITH LLVM-exception, portable zip, no install. Source = the live lock trial_w6
(d4f4312 + trial_w6.patch, six switches ON). Commands: CMDS.md; logs: `logs/`; hashes: SHA256SUMS.

## Identity (forge-uci MCP pin_check; lock pins bench d11 312866, d13 862329, d16 3024920, d20 12389307, d22 34048354, perft5 4865609 / 193690690)

| Build | Compiler / runtime | sha256 (first 8) | pin_check |
|---|---|---|---|
| g0 | g++ 15.2 plain (kit flags, no LTO / PGO) | 758608C8 | PASS (source tree = the lock's) |
| c0 | installed clang 18.1.8, MSVC target, VS 18 STL 14.51 | - | **does not compile**: `STL1000: Unexpected compiler version, expected Clang 20 or newer` (+ `__is_layout_compatible` unknown) |
| m0 | clang 23.1.5 (llvm-mingw), its own libc++ | EA0645FB | **DIFF**: bench d11 369996, d13 1033864, d16 4028461 (perft OK); net-off d11 369292 vs lock 375354 |
| m0_lsx | clang 23.1.5 + MSYS2 GCC 15.2 runtime (`--sysroot=C:/msys64/ucrt64 -stdlib=libstdc++ -rtlib=libgcc -unwindlib=libgcc`) | 3785AD3B | PASS |
| m1_lsx | m0_lsx + ThinLTO | DC0705A1 | PASS |
| m2use_lsx | m1_lsx + IR PGO (QA kit v2.3 workload v1 = bench 11 / 13 / 16) | F982D177 | **PASS full** (d11-d22 + perft); net-off d11 375354, d16 2448617 = lock; 61 UCI options = lock |

Why m0 differs: the move picker orders moves with `std::sort` (src/search.cpp:632). `std::sort` is not stable, and
libc++, libstdc++ and the MSVC STL break ties between equal scores differently, so the search tree changes. The LMR
table also calls `std::log`. With the same libstdc++ (and mingw-w64 UCRT CRT) as the lock's g++, clang produces the
same nodes. Earlier reports had an MSVC ASan build of this source giving bench 16 = 2587341 instead of 3024920; that
is very likely the same library effect.

## Speed (tools/abba/abba.py: palindromic ABBA, bench 20, engine nps, CPU 2 only at BelowNormal, nothing else of this job running; 2026-11-06 PC clock)

| Run | Pairs | B / A geometric mean | 95 % CI (Student t) | Median | Min / max |
|---|---|---|---|---|---|
| A/A: lock vs a byte-identical copy (20:02:17-20:03:38) | 6 | 1.0052 | 0.9977 .. 1.0127 | 1.0041 | 0.9971 / 1.0140 |
| lock (g++ LTO+PGO kit, 4181A589) vs m2use_lsx (clang 23 ThinLTO + IR PGO) (20:03:38-20:05:36) | 10 | **1.0472** | **1.0378 .. 1.0566** | 1.0453 | 1.0290 / 1.0713 |

- Medians: lock 2.549M nps, clang 2.670M nps (bench 20, 12389307 nodes for both: identity A = B checked on every run).
- A/A is SANE by the QA rule (|median| 0.41 % <= 0.5 %, interval width 1.5 % <= 4 %).
- The clang build passes the QA WIN rule: interval above 1.000, and the gain (+4.7 %) exceeds half the A/A width
  (0.75 %).
- Load (cpu_users.ps1, `logs/*/load.txt`): the live trainer (python pid 1036, Idle, mask 0xF) used 1.56-1.88 cores of
  CPUs 0-3. The timed run had BelowNormal on CPU 2, which outranks Idle work. The sibling CPU 3 was not used by this
  job but may have run trainer threads (SMT).
- **Status: SCREENING, not a lock claim.**
  - Both builds trained PGO on the same bench-only workload v1, and the timing is also a bench. Real-game nps can differ.
  - QA would need the lock path: 12k BIT-EXACT, L3b warm identity, Threads 2-4 soak, its own ABBA on a freed core.
  - With a speed-only change of this size the Elo effect is small and positive. That is not measured here.

## What this gives the crew
- A second compiler that keeps the lock's node counts, with a +4.7 % screening nps gain on bench 20 over the g++
  LTO+PGO kit build.
- A PDB for symbolized profiling (used in T3).
- The root cause of every non-libstdc++ build being non-identical (MSVC, clang-cl, libc++): the unstable `std::sort`.

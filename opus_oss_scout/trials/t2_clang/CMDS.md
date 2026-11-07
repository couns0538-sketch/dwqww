# T2 clang 18 build of the trial_w6 source - exact commands

Base folder: `C:\opus_5h\oss_scout`. Every build ran at Idle priority on CPUs 2-3, inherited from the session process.

## Source (trial_w6 = the live lock, sha256 4181A589)
- Lock source: commit d4f43124dde1d1e37de90e18930e374f32ea7ffa (`[BASELINE] AL1 s198 ...`), the `src` and `include`
  folders, exported with LF line ends:
  `git -c core.autocrlf=false archive d4f43124dde1d1e37de90e18930e374f32ea7ffa src include | tar -x -C build/t2/src_w6`.
  The first export without `core.autocrlf=false` had CRLF; it was kept unused in `build/t2/src_w6_crlf_unused`.
- Patch: `opus_speed/patches/trial_w6.patch` from branch opus-speed-20261105.
  - md5 5786e9b87a0c3cec4707af521cec85bc, the same as in `opus_speed/candidates/trial_w6.md`.
  - Applied with `patch -p1 -F0` (dry run first; 8 files, no rejects).
- Switches, passed as `-D`. These are the values that `trial_w6.md` flips in `src_kit`; each switch is an
  `#ifndef ... #define ... 0` default in the patch:
  `-DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1`
- The kit's own defines: `-DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1`.

## Builds (`tools/t2_build.ps1 -Variant <v>`; each command line is logged in `build/t2/<v>/build.log`)
- `g0`: g++ 15.2 (MSYS2 ucrt64), the kit's plain line, as a source identity reference:
  `g++ -std=c++20 -O3 <defines> -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -I<src>/include <src>/src/*.cpp -Wl,--no-insert-timestamp`
- `c0`: clang++ 18.1.8 (target x86_64-pc-windows-msvc, inside vcvars64 of VS 18 BuildTools):
  `-std=c++20 -O3 <defines> -ffp-contract=off -fno-fast-math -march=znver4 -fms-runtime-lib=static -g -gcodeview`,
  linked with `-fuse-ld=lld -Wl,/DEBUG:FULL -Wl,/OPT:REF -Wl,/OPT:ICF -Wl,/Brepro`.
  - Why znver4: clang 18 has no znver5 target. Both set the AVX-512 / VNNI / BMI2 macros that the source checks.
- `c1`: c0 + `-flto=thin`.
- `c2gen` / `c2use`: c1 + `-fprofile-instr-generate`.
  - Workload: QA kit v2.3 `frozen_train_cmds.txt` (sha256 1D52720A...; uci, isready, bench 11 / 13 / 16, quit) on stdin.
  - Merge: `llvm-profdata merge`. Rebuild with `-fprofile-instr-use=<profdata>`.

## Checks
- Identity: forge-uci MCP `pin_check` on every exe (bench d11 / d13 / d16 + perft 5 startpos / kiwipete = the lock pins).
- Speed: `tools/abba/abba.py` (R14-B, opus-r14b-status; palindromic ABBA, Student-t interval) on CPU 2 (mask 0x4) at
  BelowNormal, with an A/A run of the lock against itself as the noise floor.

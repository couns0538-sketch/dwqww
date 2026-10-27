# 00_baseline: AL1 s198 lock reproduced on the Windows PC (2026-10-26)

Status: **REPRODUCED** (all identity numbers match section 2 of the prompt; done before any job).

| check | result | reference | log |
|---|---|---|---|
| archive sha256 | 7acc996c…85ed | 7acc996c…85ed | archive_and_tree_check.txt |
| lock tree sha256 (75 files) | 75/75 OK | AL1_s198_sources_fulltree.sha256 | archive_and_tree_check.txt |
| net md5 | 22b4b9e2c61b37c0450f13a3a92c19b3 | 22b4b9e2… | archive_and_tree_check.txt |
| bench d11/13/16/20/22 | 312866 / 862329 / 3024920 / 12389307 / 34048354 | same | uci_check_full.log |
| perft(5) startpos | 4865609 | 4865609 | uci_check_full.log |
| perft(5) kiwipete | 193690690 | 193690690 | uci_check_full.log |
| FMA instructions | 0 | 0 | build_pc_recipe.log |
| exe vs PC lock exe 833C47F3…22B3 | byte-identical except the PE link timestamp and PE checksum (6 bytes) | — | build_pc_recipe.log |
| ctest (CMake Release, g++ 15.2) | 13/14; only forge_tests fails, with exactly the 4 known FAIL lines (identical to the box log) | 13/14 + 4 known lines | ctest_cmake_release.log, ctest_known_failure_check.log |

Build recipes used on this PC (toolchain.txt):
- PC recipe = the exact `2_build/build_windows.ps1` g++ command line (MSYS2 ucrt64 g++ 15.2.0 Rev14, the same toolchain
  that built the PC lock exe on 2026-10-25): `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off
  -fno-fast-math -march=znver5 -static -pthread`, same 8 source files.
- CMake recipe = box flags (`-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`)
  with MSYS2 g++ 15.2 + VS-bundled CMake 4.3.1 / Ninja 1.13.2, `-static` link so the test exes run without DLL lookup.

Environment notes (apply to every job's numbers):
- The PC was running a fastchess gate (~7 concurrent games), 2 self-play datagen workers and NNUE training during all
  measurements (~80% CPU). With the owner's approval all work ran at BelowNormal priority with at most 3 threads, so
  NPS / timing numbers are noisy and must be re-measured on an idle machine before any speed claim.
- Linux (box recipe g++-14), ASan+UBSan and TSan evidence comes from `.github/workflows/opus-ci.yml`
  (`opus_round1/ci/run_ci.sh`), because WSL2 cannot start on this PC (Virtual Machine Platform disabled, enabling it
  needs a reboot, which was not done) and TSan has no Windows implementation.

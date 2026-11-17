# combo29 lock record

- Lock tag: `AUTOLOCK_1_gate120_e32f003rec_s198` (speed lock name `combo29`, base `base_combo29_clang_E1284F7F`)
- Exe: `windows/forge_clang_combo29_trial_w6.exe`, 2092544 bytes
  - md5 `c0051c99695f48bf93272d96fe7548c3`
  - sha256 `E1284F7FC492C8FE1285797FDAE8988CF2F2926B33FCFEE7023D284D67D8802E`
- Set as lock: 2026-11-08 00:35:41 on grok-pc's clock (`docs/CURRENT_LOCK.json`, `set_t`)
- Replaces speed lock trial_w6 `forge_ltopgo_x_al1s198_trial_w6.exe` sha256 `4181A589...6B0`
- What it is: a bit-exact SPEED lock (KING_LINES + SEE_HOIST + MOVE_EQ32 + clang23 ThinLTO+PGO). It has the same net and node counts as trial_w6 and is about +10.19% NPS (T1, core 4, ABBA, CI95 10.10..10.41). There is **no Elo claim**.

## Pins (Threads 1, Hash 16, OwnBook false; `bench` depths 11/13/16/20/22)
- net on (UseNNUE true): 312866 / 862329 / 3024920 / 12389307 / 34048354
- net off (UseNNUE false): 375354 / 907205 / 2448617 / 13573040 / 24506465
- perft 5 startpos: 4865609

## Net
- Embedded in `src/nnue_weights.inc` (1123870 bytes; it is included here as part of the source). It is the accepted AL1 s198 net, the same net trial_w6 uses.
  - md5 `22B4B9E2C61B37C0450F13A3A92C19B3`
  - sha256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`
- There is no separate .nnue file to load.

## Source provenance
- `include/` + `src/` is the exact `source_snapshot` that built E1284F7F. It came from `D:\grok_sdk_speed_20261107\detached1735_all31\clang\all31_m29\source_snapshot` on grok-pc and was packaged on 2026-11-08 into `forge_final_combo29_clang_trial_w6_20261108`.
- The per-file sha256 manifest is `windows_build/SOURCE_INPUTS.sha256`. The file's own sha256 is `3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645`, which matches `RUN_RECEIPT.json` source_manifest_sha256 and MATRIX.json mask 13 (m13). All 20 files in this folder pass `sha256sum -c windows_build/SOURCE_INPUTS.sha256`, run from `forge-combo29/`.
- No earlier dwqww commit contains this source. The SDK-patched board.cpp, board.hpp and search.cpp blobs were not referenced by any commit as of 2026-11-10.
- `patches/` holds the combo29 diffs vs trial_w6 and the original SDK feature patches. BADCAP_PREFIX is present but not enabled, and clang_four is NOT this lock.

## Windows lock build (how the exe was made)
- See `windows_build/BUILD_RECIPE.txt`, `c_t2_build.ps1`, `build.log`, `RUN_RECEIPT.json`, `frozen_train_cmds.txt` (the PGO workload).
- Compiler: clang++ 23.1.5 (llvm-mingw-20261104).
- Flags: `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -g -gcodeview -flto=thin`, plus IR-PGO instrument/use with `-fuse-ld=lld -static`.
- A rebuild is not byte-identical because of embedded PDB paths.

## Verification done
- On grok-pc (earlier QA, `docs/lockproof`, `docs/overnight`, `docs/CURRENT_LOCK.json` note):
  - bit-exact vs trial_w6 on 12000/12000 FENs, net on and off
  - warm-TT 1000 identical
  - T2-4 soak PASS
  - sanitizer not run
- On the Grok box (2026-11-10, Debian, g++ 14.2.0, cmake 4.4.4, AVX-512 CPU):
  - clean `cmake` Release builds of this folder reproduced **all 10 bench pins and perft 5 = 4865609**
  - this held for the default (`x86-64-v4`, PEXT+ZMM) and for `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`
  - a plain `g++ src/*.cpp` build with the six -D switches matched too
  - the Linux binaries are not the lock exe, and their NPS is not a speed result

## Not included
- PGNs, datasets, training data, build dirs, PDB files, large UCI cand/ref logs, the PGO .profdata (all still on grok-pc).

# Speed candidate b2_nnue_zmm_b

- State: NOT BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\b2_nnue_zmm_b\forge_b2_nnue_zmm_b.exe` md5 `e750c5f57d012a4ef05e8e0461831383` sha256 `809f03df23af1bd4dac31f47563f501bb74eba9ed3138964d07065b001e29cf8` (REPRO lp_v1 pc1 = pc2 sha256 809f03df23af1bd4dac31f47563f501bb74eba9ed3138964d07065b001e29cf8 (reused build folders F:\ospd\builds\pack_b2_nnue_zmm_lp_v1_pc1, F:\ospd\builds\pack_b2_nnue_zmm_lp_v1_pc2; sources byte-identical to this pack's))
- Source: `F:/ospd/src/b2_nnue_zmm` with defaults flipped in `F:\ospd\packs\b2_nnue_zmm_b\src_kit`: FORGE_SPD_NNUE_ZMM=1; patch / commit: see opus_speed/patches and the branch commit that adds this file.
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\kit_v23\workload\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\b2_nnue_zmm_b\bitexact\bitexact.log` -> VERDICT NOT BIT-EXACT (first failure at L4; later levels not run)
- ABBA CSV: `F:\ospd\packs\b2_nnue_zmm_b\abba_d20\runs.csv` md5 ``
- ABBA summary:
```
not run: NOT BIT-EXACT
```
- Note: 

- SUPERSEDED (10:4x): the L4 FAIL is the checker flaw fixed at ~10:22 (MSVC ASan was compared with the g++ node count; MSVC std::sort orders equal scores differently); L1-L3 had passed. Re-run with the same builds and these L1-L3 lines: see the next pack of this candidate.

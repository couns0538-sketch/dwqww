# Speed candidate r14_speed2

- State: NOT BIT-EXACT / check error; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\r14_speed2\forge_r14_speed2.exe` md5 `e7d8c113281ec80b2382d2a2109f3b81` sha256 `de20653cea8ce61027223ae3a11e79e75d08a09df57a0e5de02959ad9ed235c8` (REPRO lp_v1 pc1 = pc2 sha256 de20653cea8ce61027223ae3a11e79e75d08a09df57a0e5de02959ad9ed235c8)
- Source: `F:/ospd/src/r14_speed2` with defaults flipped in `F:\ospd\packs\r14_speed2\src_kit`: FORGE_SEARCH_SPEED2=1; patch / commit: see opus_speed/patches and the branch commit that adds this file.
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_r14_speed2_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\r14_speed2\bitexact\bitexact.log` -> VERDICT NOT BIT-EXACT (first failure at L4; later levels not run)
- ABBA CSV: `F:\ospd\packs\r14_speed2\abba_d20\runs.csv` md5 ``
- ABBA summary:
```
skipped (-SkipAbba)
```
- Note: 

- SUPERSEDED (10:4x): the L4 FAIL is the checker flaw fixed at ~10:22 (MSVC ASan was compared with the g++ node count; MSVC std::sort orders equal scores differently); L1-L3 had passed. Re-run with the same builds and these L1-L3 lines: see the next pack of this candidate.

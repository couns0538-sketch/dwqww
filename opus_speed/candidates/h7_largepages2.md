# Speed candidate h7_largepages2

- State: BIT-EXACT; L3 on the first 2,000 of the 12k FENs (quick); ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\h7_largepages2\forge_h7_largepages2.exe` md5 `db50708fe8947eb6d3a051d598840d23` sha256 `344e6113261f78d1c4a35983a41e70b475c6d04bb5393b03a8335a7c90b1c292` (REPRO lp_v1 pc1 = pc2 sha256 344e6113261f78d1c4a35983a41e70b475c6d04bb5393b03a8335a7c90b1c292)
- Source: `F:\ospd\src\h7_largepages2` with defaults flipped in `F:\ospd\packs\h7_largepages2\src_kit`: FORGE_SPD_TT_NOTLS=1, FORGE_SPD_NO_ZERO_MOVELISTS=2, FORGE_SEARCH_SPEED2=1, FORGE_SPD_PREFETCH_EARLY=1, FORGE_SPD_SLIDER_PEXT=1, FORGE_SPD_NNUE_ZMM=1, FORGE_SPD_LARGEPAGES=2; patch opus_speed/patches/h7_largepages2.patch md5 9e477cafa98ae309f7faf05d9124ce56 (verified: lock + this patch = the built source); branch head at pack time: bbaf72d0 (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_h7_largepages2_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\h7_largepages2\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\h7_largepages2\abba_d20\runs.csv` md5 ``
- ABBA summary:
```
skipped (-SkipAbba)
```
- Note: hunt H7: large pages for the TT, the net weights and the worker tables

# Speed candidate h9_ptype_arith

- State: BIT-EXACT; L3 on the first 2,000 of the 12k FENs (quick); ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\h9_ptype_arith\forge_h9_ptype_arith.exe` md5 `b6a97dafd8c918ee81edf6b5d891a9d5` sha256 `96004e91b7436fd7bef677ad91331a36f62825f033f8c3d1407a3e1bffe581dd` (REPRO lp_v1 pc1 = pc2 sha256 96004e91b7436fd7bef677ad91331a36f62825f033f8c3d1407a3e1bffe581dd)
- Source: `F:\ospd\src\h9_ptype_arith` with defaults flipped in `F:\ospd\packs\h9_ptype_arith\src_kit`: FORGE_SPD_TT_NOTLS=1, FORGE_SPD_NO_ZERO_MOVELISTS=2, FORGE_SEARCH_SPEED2=1, FORGE_SPD_PREFETCH_EARLY=1, FORGE_SPD_SLIDER_PEXT=1, FORGE_SPD_NNUE_ZMM=1, FORGE_SPD_PTYPE_ARITH=1; patch opus_speed/patches/h9_ptype_arith.patch md5 e48284d90b19567af1a194edad71fadd (verified: lock + this patch = the built source); branch head at pack time: f5b7a07a (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_h9_ptype_arith_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\h9_ptype_arith\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\h9_ptype_arith\abba_d20\runs.csv` md5 ``
- ABBA summary:
```
skipped (-SkipAbba)
```
- Note: hunt H9: piece_type by arithmetic instead of the table load

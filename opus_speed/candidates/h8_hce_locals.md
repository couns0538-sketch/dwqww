# Speed candidate h8_hce_locals

- State: BIT-EXACT; L3 on the first 2,000 of the 12k FENs (quick); ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\h8_hce_locals\forge_h8_hce_locals.exe` md5 `b9d33b75bd28823d4907875e94e8a5fe` sha256 `89ac3f1f2d8100f1f8e153deb9356184d34c1e3d4443251b85d0bbaaef2e21f5` (REPRO lp_v1 pc1 = pc2 sha256 89ac3f1f2d8100f1f8e153deb9356184d34c1e3d4443251b85d0bbaaef2e21f5)
- Source: `F:\ospd\src\h8_hce_locals` with defaults flipped in `F:\ospd\packs\h8_hce_locals\src_kit`: FORGE_SPD_TT_NOTLS=1, FORGE_SPD_NO_ZERO_MOVELISTS=2, FORGE_SEARCH_SPEED2=1, FORGE_SPD_PREFETCH_EARLY=1, FORGE_SPD_SLIDER_PEXT=1, FORGE_SPD_NNUE_ZMM=1, FORGE_SPD_HCE_LOCALS=1; patch opus_speed/patches/h8_hce_locals.patch md5 36e164911bb59ad2c5864aef35dd4d5a (verified: lock + this patch = the built source); branch head at pack time: 7b94caa2 (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_h8_hce_locals_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\h8_hce_locals\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\h8_hce_locals\abba_d20\runs.csv` md5 ``
- ABBA summary:
```
skipped (-SkipAbba)
```
- Note: hunt H8: evaluate_pieces accumulates in locals

# Speed candidate w9_king_lines_on_d

- State: BIT-EXACT; L3 on the first 2,000 of the 12k FENs (quick); ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\w9_king_lines_on_d\forge_w9_king_lines_on_d.exe` md5 `a6d9c224481cb3f30c43843106189e41` sha256 `5f5f4ece24f6d6ca7a34f5c9c4a158e1270da35688e284b85a3a591e264cf1b5` (REPRO lp_v1 pc1 = pc2 sha256 5f5f4ece24f6d6ca7a34f5c9c4a158e1270da35688e284b85a3a591e264cf1b5)
- Source: `F:/ospd/src/trial_w9` with defaults flipped in `F:\ospd\packs\w9_king_lines_on_d\src_kit`: FORGE_SPD_TT_NOTLS=1, FORGE_SPD_NO_ZERO_MOVELISTS=2, FORGE_SEARCH_SPEED2=1, FORGE_SPD_PREFETCH_EARLY=1, FORGE_SPD_SLIDER_PEXT=1, FORGE_SPD_T12B_BADCAP=1, FORGE_SPD_NNUE_AVX512=1, FORGE_SPD_KING_LINES=1; patch opus_speed/patches/trial_w9.patch md5 ddefd1fe72931fe0533bc89c0e8c41eb (verified: lock + this patch = the built source); branch head at pack time: 146cabf8 (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_w9_king_lines_on_d_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\w9_king_lines_on_d\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\w9_king_lines_on_d\abba_d20\runs.csv` md5 ``
- ABBA summary:
```
skipped (-SkipAbba)
```
- Note: 

# Speed candidate b1_tt_notls

- State: NOT BIT-EXACT / check error; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\b1_tt_notls\forge_b1_tt_notls.exe` md5 `46eb64501c454e496d075159df355227` sha256 `9b6aae65ebd243f9c4fd68bf0a7bad8b091e96548218149d2de6091efa0e523f` (REPRO lp_v1 pc1 = pc2 sha256 9b6aae65ebd243f9c4fd68bf0a7bad8b091e96548218149d2de6091efa0e523f)
- Source: `F:/ospd/src/b1_tt_notls` with defaults flipped in `F:\ospd\packs\b1_tt_notls\src_kit`: FORGE_SPD_TT_NOTLS=1; patch / commit: see opus_speed/patches and the branch commit that adds this file.
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\kit_v23\workload\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\b1_tt_notls\bitexact\bitexact.log` -> VERDICT NOT BIT-EXACT (first failure at L4; later levels not run)
- ABBA CSV: `F:\ospd\packs\b1_tt_notls\abba_d20\runs.csv` md5 ``
- ABBA summary:
```
skipped (-SkipAbba)
```
- Note: 

- SUPERSEDED (10:24): the L4 FAIL above is a flaw of the checker, not of this change: the MSVC ASan build was compared with the g++ node count (MSVC std::sort orders equal scores differently, so an MSVC build of the lock itself gives a different bench 16 count). UBSan (g++) gave 3024920 = pin. Fixed in bitexact_check.ps1 (ASan compared with the MSVC ASan build of the lock source). Re-run: candidates/b1_tt_notls_b.md.

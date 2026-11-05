# Speed candidate locklock_v1

- State: NOT BIT-EXACT / check error; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\locklock_v1\forge_locklock_v1.exe` md5 `2b4821e537c7004b8b588ef9e2ca07b1` sha256 `fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072` (REPRO lp_v1 pc1 = pc2 sha256 fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072)
- Source: `F:/ospd/src/lock`; patch / commit: see opus_speed/patches and the branch commit that adds this file.
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_locklock_v1_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\locklock_v1\bitexact\bitexact.log` -> ERROR: Cannot create a file when that file already exists.

- ABBA CSV: `F:\ospd\packs\locklock_v1\abba_d20\runs.csv` md5 ``
- ABBA summary:
```
skipped (-SkipAbba)
```
- Note: Job A test 1: lock source through the whole lock path

- SUPERSEDED (10:12): this pack ended in a CHECK ERROR, not a verdict: its bit-exact run lost a race on the shared L3 reference cache ("Cannot create a file when that file already exists"), fixed in bitexact_check.ps1 (named mutex per reference file). Re-run with the same builds: candidates/locklock_v1b.md.

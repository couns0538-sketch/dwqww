# Speed candidate b2_nzm2

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\b2_nzm2\forge_b2_nzm2.exe` md5 `1fdb15f9c105e02ab81a1fc89cd3150b` sha256 `ac287b2d3ab58953c2ea7f42493a260c48894021496ee15f94da381148329ec7` (REPRO lp_v1 pc1 = pc2 sha256 ac287b2d3ab58953c2ea7f42493a260c48894021496ee15f94da381148329ec7)
- Source: `F:/ospd/src/b2_no_zero_movelists` with defaults flipped in `F:\ospd\packs\b2_nzm2\src_kit`: FORGE_SPD_NO_ZERO_MOVELISTS=2; patch / commit: see opus_speed/patches and the branch commit that adds this file.
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_b2_nzm2_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\b2_nzm2\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\b2_nzm2\abba_d20\runs.csv` md5 `664d3b5d79885e8d7866e3eec58ae552`
- ABBA summary:
```
run 20261105-104727-11296
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs b2_nzm2 (B, md5 1fdb15f9c105e02ab81a1fc89cd3150b); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.0361 (+3.61%), 95% t-interval [1.0161, 1.0606], sd/round 3.00%, bootstrap median CI [1.0167, 1.0605]
cpu (nodes / process CPU time of the bench window): B/A median 1.0426 (+4.26%), 95% t-interval [1.0360, 1.0479], sd/round 0.80%, bootstrap median CI [1.0351, 1.0491]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall WIN / cpu WIN (rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: 

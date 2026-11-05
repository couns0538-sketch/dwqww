# Speed candidate b2_pickbest1

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\b2_pickbest1\forge_b2_pickbest1.exe` md5 `d9adb7dfd270d13d43c10127d413a4ab` sha256 `13e34185f347c0739ceb2968bc548801e2efa33b4cc46cf91191bd7979e7a4af` (REPRO lp_v1 pc1 = pc2 sha256 13e34185f347c0739ceb2968bc548801e2efa33b4cc46cf91191bd7979e7a4af)
- Source: `F:/ospd/src/b2_pickbest` with defaults flipped in `F:\ospd\packs\b2_pickbest1\src_kit`: FORGE_SPD_PICKBEST=1; patch / commit: see opus_speed/patches and the branch commit that adds this file.
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_b2_pickbest1_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\b2_pickbest1\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\b2_pickbest1\abba_d20\runs.csv` md5 `81c0350739f64669c094cec75f4520f0`
- ABBA summary:
```
run 20261105-110619-9768
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs b2_pickbest1 (B, md5 d9adb7dfd270d13d43c10127d413a4ab); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.0108 (+1.08%), 95% t-interval [0.9909, 1.0214], sd/round 2.12%, bootstrap median CI [1.0006, 1.0182]
cpu (nodes / process CPU time of the bench window): B/A median 1.0113 (+1.13%), 95% t-interval [0.9981, 1.0198], sd/round 1.50%, bootstrap median CI [1.0022, 1.0173]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall NO-WIN / cpu NO-WIN (rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: 

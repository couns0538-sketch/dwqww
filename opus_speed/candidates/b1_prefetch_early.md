# Speed candidate b1_prefetch_early

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\b1_prefetch_early\forge_b1_prefetch_early.exe` md5 `865d73c8499e2c2c09b46182f70086b0` sha256 `ec5af9b05d0a7d7109be5d1ae10804dfeb20d4c7a70b7d5ef3a9d4298d90e9a6` (REPRO lp_v1 pc1 = pc2 sha256 ec5af9b05d0a7d7109be5d1ae10804dfeb20d4c7a70b7d5ef3a9d4298d90e9a6)
- Source: `F:/ospd/src/b1_prefetch_early` with defaults flipped in `F:\ospd\packs\b1_prefetch_early\src_kit`: FORGE_SPD_PREFETCH_EARLY=1; patch / commit: see opus_speed/patches and the branch commit that adds this file.
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_b1_prefetch_early_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\b1_prefetch_early\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\b1_prefetch_early\abba_d20\runs.csv` md5 `cfe32f4f327e1e12b1e80014f4720993`
- ABBA summary:
```
run 20261105-110022-6888
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs b1_prefetch_early (B, md5 865d73c8499e2c2c09b46182f70086b0); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.0111 (+1.11%), 95% t-interval [0.9889, 1.0322], sd/round 3.00%, bootstrap median CI [0.9868, 1.0200]
cpu (nodes / process CPU time of the bench window): B/A median 1.0152 (+1.52%), 95% t-interval [1.0026, 1.0288], sd/round 1.80%, bootstrap median CI [1.0071, 1.0233]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall NO-WIN / cpu WIN (rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: 

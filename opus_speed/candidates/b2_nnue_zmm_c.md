# Speed candidate b2_nnue_zmm_c

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\b2_nnue_zmm_c\forge_b2_nnue_zmm_c.exe` md5 `e750c5f57d012a4ef05e8e0461831383` sha256 `809f03df23af1bd4dac31f47563f501bb74eba9ed3138964d07065b001e29cf8` (REPRO lp_v1 pc1 = pc2 sha256 809f03df23af1bd4dac31f47563f501bb74eba9ed3138964d07065b001e29cf8 (reused build folders F:\ospd\builds\pack_b2_nnue_zmm_lp_v1_pc1, F:\ospd\builds\pack_b2_nnue_zmm_lp_v1_pc2; sources byte-identical to this pack's))
- Source: `F:/ospd/src/b2_nnue_zmm` with defaults flipped in `F:\ospd\packs\b2_nnue_zmm_c\src_kit`: FORGE_SPD_NNUE_ZMM=1; patch opus_speed/patches/b2_nnue_zmm.patch md5 a5ebad79d57f6703e985224c8f153db4; branch head at pack time: c835d270 (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\kit_v23\workload\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\b2_nnue_zmm_c\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\b2_nnue_zmm_c\abba_d20\runs.csv` md5 `bcc00d27ed1b6171baa43c0289248de6`
- ABBA summary:
```
run 20261105-121225-13520
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs b2_nnue_zmm_c (B, md5 e750c5f57d012a4ef05e8e0461831383); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.0199 (+1.99%), 95% t-interval [0.9999, 1.0578], sd/round 3.93%, bootstrap median CI [0.9937, 1.0692]
cpu (nodes / process CPU time of the bench window): B/A median 1.0156 (+1.56%), 95% t-interval [0.9987, 1.0449], sd/round 3.16%, bootstrap median CI [1.0014, 1.0362]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall NO-WIN / cpu NO-WIN (rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: NNUE zmm output kernel; re-run with L1-L3 reused and the fixed L4

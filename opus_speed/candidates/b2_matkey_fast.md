# Speed candidate b2_matkey_fast

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\b2_matkey_fast\forge_b2_matkey_fast.exe` md5 `16cec191b21556fe25278561dcba1979` sha256 `434920e5304bd1d64479d26890aa0cbe86af7d59b2c077ca811be01186e056f2` (REPRO lp_v1 pc1 = pc2 sha256 434920e5304bd1d64479d26890aa0cbe86af7d59b2c077ca811be01186e056f2)
- Source: `F:/ospd/src/b2_matkey_fast` with defaults flipped in `F:\ospd\packs\b2_matkey_fast\src_kit`: FORGE_SPD_MATKEY_FAST=1; patch opus_speed/patches/b2_matkey_fast.patch md5 6d1433b9ae736abdc3e0fd50e23e95d8; branch head at pack time: 980067dc (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_b2_matkey_fast_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\b2_matkey_fast\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\b2_matkey_fast\abba_d20\runs.csv` md5 `f97da2f04086cee5d1be176ed94f6d57`
- ABBA summary:
```
run 20261105-112435-11976
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs b2_matkey_fast (B, md5 16cec191b21556fe25278561dcba1979); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.0084 (+0.84%), 95% t-interval [0.9887, 1.0379], sd/round 3.40%, bootstrap median CI [0.9829, 1.0400]
cpu (nodes / process CPU time of the bench window): B/A median 1.0077 (+0.77%), 95% t-interval [0.9919, 1.0258], sd/round 2.34%, bootstrap median CI [0.9953, 1.0216]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall NO-WIN / cpu NO-WIN (rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: 

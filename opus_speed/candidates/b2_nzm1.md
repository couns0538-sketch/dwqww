# Speed candidate b2_nzm1

- State: BIT-EXACT; L3 on the first 2,000 of the 12k FENs (quick); ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\b2_nzm1\forge_b2_nzm1.exe` md5 `3cdc303c000c5d1108cf30d195edde36` sha256 `3e52ed13eb0db4aabe961c336cb743a1d8f8e6874dfd4b42329331e18d71f660` (REPRO lp_v1 pc1 = pc2 sha256 3e52ed13eb0db4aabe961c336cb743a1d8f8e6874dfd4b42329331e18d71f660)
- Source: `F:/ospd/src/b2_no_zero_movelists` with defaults flipped in `F:\ospd\packs\b2_nzm1\src_kit`: FORGE_SPD_NO_ZERO_MOVELISTS=1; patch opus_speed/patches/b2_no_zero_movelists.patch md5 80833b14ccebc36dcb0a9c7240e807fe (verified: lock + this patch = the built source); branch head at pack time: 440e331c (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_b2_nzm1_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\b2_nzm1\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\b2_nzm1\abba_d20\runs.csv` md5 `1f41b6d0fd59ca01c78243e4d029b48b`
- ABBA summary:
```
run 20261105-124300-6100
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs b2_nzm1 (B, md5 3cdc303c000c5d1108cf30d195edde36); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.0326 (+3.26%), 95% t-interval [1.0177, 1.0442], sd/round 1.80%, bootstrap median CI [1.0161, 1.0466]
cpu (nodes / process CPU time of the bench window): B/A median 1.0275 (+2.75%), 95% t-interval [1.0160, 1.0460], sd/round 2.04%, bootstrap median CI [1.0157, 1.0498]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall WIN / cpu WIN (PROTOCOL verdict = wall, the engine's own bench nps; cpu = advisory: it removes preemption by other programs but not SMT-sibling contention; rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: 

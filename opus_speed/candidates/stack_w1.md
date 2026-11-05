# Speed candidate stack_w1

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\stack_w1\forge_stack_w1.exe` md5 `e3a7bffc03c416beae311112400d702e` sha256 `05928226b703b4dd2176bd5ee7392f9de2fb085db7f56c4870a7392e09663893` (REPRO lp_v1 pc1 = pc2 sha256 05928226b703b4dd2176bd5ee7392f9de2fb085db7f56c4870a7392e09663893)
- Source: `F:/ospd/src/stack_w1src` with defaults flipped in `F:\ospd\packs\stack_w1\src_kit`: FORGE_SPD_NO_ZERO_MOVELISTS=2, FORGE_SEARCH_SPEED2=1; patch opus_speed/patches/stack_w1src.patch md5 d33a68207fb5dd8b9b59e4ad8266ca70; branch head at pack time: 02382089 (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_stack_w1_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\stack_w1\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\stack_w1\abba_d20\runs.csv` md5 `87de6a9e016d5306b89fd2f950783795`
- ABBA summary:
```
run 20261105-122740-6700
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs stack_w1 (B, md5 e3a7bffc03c416beae311112400d702e); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.0731 (+7.31%), 95% t-interval [1.0565, 1.1031], sd/round 3.02%, bootstrap median CI [1.0567, 1.1026]
cpu (nodes / process CPU time of the bench window): B/A median 1.0713 (+7.13%), 95% t-interval [1.0657, 1.0881], sd/round 1.45%, bootstrap median CI [1.0648, 1.0891]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall WIN / cpu WIN (PROTOCOL verdict = wall, the engine's own bench nps; cpu = advisory: it removes preemption by other programs but not SMT-sibling contention; rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: Stack of the protocol (wall) winners only: NO_ZERO_MOVELISTS=2 + SPEED2 (rebased after NZM)
- QA kit check (12:34-12:36): QA's own `kit_v23\build_ltopgo.ps1 -Expose -Kit <kit folder>` on `F:\ospd\packs\stack_w1\src_kit` (work folder `F:\ospd\qakit\qakit_stack_w1_pc1`) gives sha256 05928226b703b4dd2176bd5ee7392f9de2fb085db7f56c4870a7392e09663893 = this pack's exe byte for byte; kit node identity ALL OK; RESULT PASS.
- Members: NZM2 and SPEED2 are wall (protocol) winners in their single packs (b2_nzm2, r14_speed2_b); this stack is the winners-only stack of the first single runs.

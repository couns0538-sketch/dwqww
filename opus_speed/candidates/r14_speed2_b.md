# Speed candidate r14_speed2_b

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\r14_speed2_b\forge_r14_speed2_b.exe` md5 `e7d8c113281ec80b2382d2a2109f3b81` sha256 `de20653cea8ce61027223ae3a11e79e75d08a09df57a0e5de02959ad9ed235c8` (REPRO lp_v1 pc1 = pc2 sha256 de20653cea8ce61027223ae3a11e79e75d08a09df57a0e5de02959ad9ed235c8 (reused build folders F:\ospd\builds\pack_r14_speed2_lp_v1_pc1, F:\ospd\builds\pack_r14_speed2_lp_v1_pc2; sources byte-identical to this pack's))
- Source: `F:/ospd/src/r14_speed2` with defaults flipped in `F:\ospd\packs\r14_speed2_b\src_kit`: FORGE_SEARCH_SPEED2=1; patch / commit: see opus_speed/patches and the branch commit that adds this file.
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_r14_speed2_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: n/a
- Bit-exact log: `F:\ospd\packs\r14_speed2_b\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\r14_speed2_b\abba_d20\runs.csv` md5 `1166c21bb007715fb14de66abb52672b`
- ABBA summary:
```
run 20261105-111221-7928
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs r14_speed2_b (B, md5 e7d8c113281ec80b2382d2a2109f3b81); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.0315 (+3.15%), 95% t-interval [1.0165, 1.0443], sd/round 1.88%, bootstrap median CI [1.0135, 1.0463]
cpu (nodes / process CPU time of the bench window): B/A median 1.0287 (+2.87%), 95% t-interval [1.0157, 1.0425], sd/round 1.83%, bootstrap median CI [1.0172, 1.0413]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall WIN / cpu WIN (rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: R14 SPEED2 (own earlier switch); re-run with L1-L3 reused and the fixed L4
- Bench signature (L1-L2 of the resumed run, F:/ospd/packs/r14_speed2/bitexact/cand/sig_de20653cea8ce610.json): sha256 de20653cea8ce610; net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690 (= lock pins)

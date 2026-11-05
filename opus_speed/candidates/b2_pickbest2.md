# Speed candidate b2_pickbest2

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\b2_pickbest2\forge_b2_pickbest2.exe` md5 `97594f12b353b90fad83d973b3dc7ddd` sha256 `2e86d2c794fdc9cc16d0d33eba879b34f388674284d340ee83e564502909bce6` (REPRO lp_v1 pc1 = pc2 sha256 2e86d2c794fdc9cc16d0d33eba879b34f388674284d340ee83e564502909bce6)
- Source: `F:/ospd/src/b2_pickbest` with defaults flipped in `F:\ospd\packs\b2_pickbest2\src_kit`: FORGE_SPD_PICKBEST=2; patch opus_speed/patches/b2_pickbest.patch md5 1a786c42d828fd09eb6db2db16fb46c3; branch head at pack time: dde4043b (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_b2_pickbest2_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\b2_pickbest2\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\b2_pickbest2\abba_d20\runs.csv` md5 `04132c8c4f54d5308e1c07c38b03bc67`
- ABBA summary:
```
run 20261105-114228-3504
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs b2_pickbest2 (B, md5 97594f12b353b90fad83d973b3dc7ddd); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.0008 (+0.08%), 95% t-interval [0.9833, 1.0293], sd/round 3.20%, bootstrap median CI [0.9782, 1.0320]
cpu (nodes / process CPU time of the bench window): B/A median 1.0034 (+0.34%), 95% t-interval [0.9965, 1.0208], sd/round 1.68%, bootstrap median CI [0.9937, 1.0253]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall NO-WIN / cpu NO-WIN (rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: 

# Speed candidate var_lp_part1

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\var_lp_part1\forge_var_lp_part1.exe` md5 `612be0b61d36a71aa325ffedf900fc49` sha256 `33ed7a536b032b3239964c123f79e743c84ce9c3bef1f06c142a8ed7746e34b2` (REPRO lp_part1 pc1 = pc2 sha256 33ed7a536b032b3239964c123f79e743c84ce9c3bef1f06c142a8ed7746e34b2)
- Source: `F:/ospd/src/lock`; no patch file (source = the lock or a stack made by make_stack.sh); branch head at pack time: dde4043b (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_part1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto-partition=one -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_var_lp_part1_lp_part1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\var_lp_part1\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 12000 FENs)
- ABBA CSV: `F:\ospd\packs\var_lp_part1\abba_d20\runs.csv` md5 `3c5e88ed5f17d966e962405de372bd0d`
- ABBA summary:
```
run 20261105-113631-11576
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs var_lp_part1 (B, md5 612be0b61d36a71aa325ffedf900fc49); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 0.9999 (-0.01%), 95% t-interval [0.9792, 1.0432], sd/round 4.42%, bootstrap median CI [0.9823, 1.0337]
cpu (nodes / process CPU time of the bench window): B/A median 1.0066 (+0.66%), 95% t-interval [0.9895, 1.0181], sd/round 1.99%, bootstrap median CI [0.9856, 1.0211]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall NO-WIN / cpu NO-WIN (rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: Job A test 3: best flag variant of the screen at 10:43 (-flto-partition=one), full 12k L3

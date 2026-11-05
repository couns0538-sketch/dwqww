# Speed candidate locklock_v1c

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\locklock_v1c\forge_locklock_v1c.exe` md5 `2b4821e537c7004b8b588ef9e2ca07b1` sha256 `fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072` (REPRO lp_v1 pc1 = pc2 sha256 fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072 (reused build folders F:\ospd\builds\pack_locklock_v1_lp_v1_pc1, F:\ospd\builds\pack_locklock_v1_lp_v1_pc2; sources byte-identical to this pack's))
- Source: `F:/ospd/src/lock`; no patch file (source = the lock or a stack made by make_stack.sh); branch head at pack time: dde4043b (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_locklock_v1_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\locklock_v1c\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\locklock_v1c\abba_d20\runs.csv` md5 `9b7845dd5748d87bff05fafbc532ab2c`
- ABBA summary:
```
run 20261105-114833-14216
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs locklock_v1c (B, md5 2b4821e537c7004b8b588ef9e2ca07b1); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 0.9902 (-0.98%), 95% t-interval [0.9522, 1.0269], sd/round 5.28%, bootstrap median CI [0.9728, 1.0045]
cpu (nodes / process CPU time of the bench window): B/A median 0.9971 (-0.29%), 95% t-interval [0.9866, 1.0054], sd/round 1.32%, bootstrap median CI [0.9869, 1.0005]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall NO-WIN / cpu NO-WIN (rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: Job A test 1: lock source through the whole lock path (re-run with the fixed L4)

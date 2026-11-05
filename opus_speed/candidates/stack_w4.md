# Speed candidate stack_w4

- State: BIT-EXACT; L3 on the first 2,000 of the 12k FENs (quick); ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\stack_w4\forge_stack_w4.exe` md5 `be83c08ab56801c232d845d9285e48d2` sha256 `c883623cc52c1583389b31d9d65abb7781ed0e538a8ca924feb144ccf5c90148` (REPRO lp_v1 pc1 = pc2 sha256 c883623cc52c1583389b31d9d65abb7781ed0e538a8ca924feb144ccf5c90148)
- Source: `F:/ospd/src/trial_w6` with defaults flipped in `F:\ospd\packs\stack_w4\src_kit`: FORGE_SPD_TT_NOTLS=1, FORGE_SPD_NO_ZERO_MOVELISTS=2, FORGE_SEARCH_SPEED2=1, FORGE_SPD_SLIDER_PEXT=1; patch opus_speed/patches/trial_w6.patch md5 5786e9b87a0c3cec4707af521cec85bc (verified: lock + this patch = the built source); branch head at pack time: df428a26 (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_stack_w4_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\stack_w4\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\stack_w4\abba_d20\runs.csv` md5 `0fc1fae19b6a327b47b613f368195727`
- ABBA summary:
```
run 20261105-131322-12896
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs stack_w4 (B, md5 be83c08ab56801c232d845d9285e48d2); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.1204 (+12.04%), 95% t-interval [1.0929, 1.1388], sd/round 2.88%, bootstrap median CI [1.0903, 1.1419]
cpu (nodes / process CPU time of the bench window): B/A median 1.1223 (+12.23%), 95% t-interval [1.1003, 1.1350], sd/round 2.17%, bootstrap median CI [1.0964, 1.1383]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall WIN / cpu WIN (PROTOCOL verdict = wall, the engine's own bench nps; cpu = advisory: it removes preemption by other programs but not SMT-sibling contention; rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: Max winners-only stack: TT_NOTLS + NO_ZERO_MOVELISTS=2 + SPEED2 + SLIDER_PEXT (every member a wall AND cpu winner, TT and SLIDER on 26 pooled rounds); source trial_w6 with PREFETCH_EARLY and NNUE_ZMM left at 0
- Correction (13:1x): the note above was written at 12:52, before the PREFETCH_EARLY re-time finished; that re-time made PREFETCH_EARLY a winner on both metrics too (pooled 26 rounds: wall +1.35 %, cpu +1.90 %). So this stack is an intermediate step (stack_w2 + SLIDER_PEXT), not the maximum: the largest winners-only stack is trial_w6 (all six), the strict one (every member wins on both metrics) is stack_w5 (all six but NNUE_ZMM). See FINAL_REPORT section 5.
- L4 in the pack run above includes the MSVC ASan build (bitexact_check passes `/D__BMI2__=1` for the PEXT source since 12:2x): ASan bench 16 = 2587341 = the lock source under MSVC ASan, 0 reports; UBSan 3024920, 0 reports.
- Full 12k L3 (separate run 13:13-13:24, `F:\ospd\packs\stack_w4\bitexact_full12k\bitexact.log`): L1 net on + off and L2 PASS again, 12000 / 12000 FENs identical (depth, score, nodes, bestmove) at go depth 13 with the 12k six-field set (md5 e7dbf2c8), candidate 606 s -> VERDICT BIT-EXACT (L1-L3 on 12000 FENs); with the pack run above: L1-L4 complete.
- QA kit check (12:59-13:01): QA's own kit v2.3 (`build_ltopgo.ps1 -Expose -Kit <kit folder>`) on `F:\ospd\packs\stack_w4\src_kit` (work folder `F:\ospd\qakit\qakit_stack_w4_pc1`) gives sha256 c883623cc52c1583389b31d9d65abb7781ed0e538a8ca924feb144ccf5c90148 = this pack's exe byte for byte; kit node identity ALL OK; RESULT PASS.

# Speed candidate trial_w6

- State: BIT-EXACT with L4 = UBSan only (ASan N/A for this source under MSVC); L3 on the first 2,000 of the 12k FENs (quick); ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\trial_w6\forge_trial_w6.exe` md5 `331ea9bf077cbf9c4c823125baa80bcc` sha256 `4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` (REPRO lp_v1 pc1 = pc2 sha256 4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0)
- Source: `F:/ospd/src/trial_w6` with defaults flipped in `F:\ospd\packs\trial_w6\src_kit`: FORGE_SPD_TT_NOTLS=1, FORGE_SPD_NO_ZERO_MOVELISTS=2, FORGE_SEARCH_SPEED2=1, FORGE_SPD_PREFETCH_EARLY=1, FORGE_SPD_SLIDER_PEXT=1, FORGE_SPD_NNUE_ZMM=1; patch opus_speed/patches/trial_w6.patch md5 5786e9b87a0c3cec4707af521cec85bc (verified: lock + this patch = the built source); branch head at pack time: 60264367 (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_trial_w6_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\trial_w6\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4 with L4 = UBSan only, ASan N/A: MSVC cannot compile this source (exit 2, see F:\ospd\packs\trial_w6\bitexact\san\build.log); L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\trial_w6\abba_d20\runs.csv` md5 `5b0af24b960243242fced7aec24b8b46`
- ABBA summary:
```
run 20261105-125800-13348
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs trial_w6 (B, md5 331ea9bf077cbf9c4c823125baa80bcc); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.1492 (+14.92%), 95% t-interval [1.1351, 1.1666], sd/round 1.91%, bootstrap median CI [1.1315, 1.1705]
cpu (nodes / process CPU time of the bench window): B/A median 1.1531 (+15.31%), 95% t-interval [1.1387, 1.1698], sd/round 1.88%, bootstrap median CI [1.1356, 1.1727]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall WIN / cpu WIN (PROTOCOL verdict = wall, the engine's own bench nps; cpu = advisory: it removes preemption by other programs but not SMT-sibling contention; rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: TRIAL ceiling: all six bit-exact changes ON (TT_NOTLS, NZM2, SPEED2 after NZM, PREFETCH_EARLY, SLIDER_PEXT, NNUE_ZMM); three members were not protocol (wall) winners when this pack started (re-times pending) - not a winners-only stack
- L4 ASan (12:24-12:25, `F:\ospd\packs\trial_w6\bitexact_l4_bmi2\bitexact.log`): the pack's L4 had ASan N/A because MSVC does not define `__BMI2__` (the PEXT switch's guard); with `/D__BMI2__=1` the MSVC ASan build gives bench 16 = 2587341 (= the lock source under MSVC ASan), 0 reports, and UBSan 3024920, 0 reports -> L1-L4 complete (that log's last line still has the old -OnlyL4 verdict text; it proves L4 only).
- QA kit check (12:36-12:38): QA's own `kit_v23` + `build_ltopgo.ps1 -Expose -Kit <kit folder>` on `F:\ospd\packs\trial_w6\src_kit` (work folder `F:\ospd\qakit\qakit_trial_w6_pc1`) gives sha256 4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0 = this pack's exe byte for byte; kit node identity ALL OK; RESULT PASS.
- Member status at 13:07 (protocol = wall; re-timed members on 26 pooled rounds, rule set before any re-time finished): TT_NOTLS WIN, NZM2 WIN, SPEED2 WIN, SLIDER_PEXT WIN, PREFETCH_EARLY WIN (pooled wall +1.35 %, cpu +1.90 %), NNUE_ZMM weak WIN (pooled wall +1.41 %, re-time alone and pooled cpu NO-WIN) -> every member is a protocol winner: this is the largest winners-only stack. Strict variant without NNUE_ZMM: stack_w5. See FINAL_REPORT section 3.
- Full 12k L3 (separate run 12:58-13:07, `F:\ospd\packs\trial_w6\bitexact_full12k\bitexact.log`): L1 net on + off and L2 PASS again, 12000 / 12000 FENs identical (depth, score, nodes, bestmove) at go depth 13 with the 12k six-field set (md5 e7dbf2c8; 12000 distinct reference rows), candidate 528 s -> VERDICT BIT-EXACT (L1-L3 on 12000 FENs); with the pack run and the L4 re-run above: L1-L4 complete.

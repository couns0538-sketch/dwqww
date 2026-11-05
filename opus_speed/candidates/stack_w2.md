# Speed candidate stack_w2

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\stack_w2\forge_stack_w2.exe` md5 `1d4080bcc08b3a2c20a70ba755e82855` sha256 `db95739378e21771e0b03e42e258f551ebeb3b66f1151f232f4f1b89e7f933a9` (REPRO lp_v1 pc1 = pc2 sha256 db95739378e21771e0b03e42e258f551ebeb3b66f1151f232f4f1b89e7f933a9)
- Source: `F:/ospd/src/trial_w2` with defaults flipped in `F:\ospd\packs\stack_w2\src_kit`: FORGE_SPD_TT_NOTLS=1, FORGE_SPD_NO_ZERO_MOVELISTS=2, FORGE_SEARCH_SPEED2=1; patch opus_speed/patches/trial_w2.patch md5 80f8124fe352ca2a39c015104be753f2; branch head at pack time: 17835f89 (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_stack_w2_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\stack_w2\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\stack_w2\abba_d20\runs.csv` md5 `16368782fc18cec72f0ac23ff97ac648`
- ABBA summary:
```
run 20261105-113029-11208
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs stack_w2 (B, md5 1d4080bcc08b3a2c20a70ba755e82855); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.1148 (+11.48%), 95% t-interval [1.0734, 1.1217], sd/round 3.08%, bootstrap median CI [1.0632, 1.1192]
cpu (nodes / process CPU time of the bench window): B/A median 1.1134 (+11.34%), 95% t-interval [1.0990, 1.1191], sd/round 1.27%, bootstrap median CI [1.0946, 1.1219]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall WIN / cpu WIN (rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: Stack TT_NOTLS + NO_ZERO_MOVELISTS=2 + SPEED2 (SPEED2 rebased after NZM: r14_speed2_after_nzm.patch); full 12k L3 run separately

- Full 12k L3 (separate run 11:06-11:26, `F:\ospd\packs\stack_w2\bitexact_full12k\bitexact.log`): 12000 / 12000 FENs identical (depth, score, nodes, bestmove) at go depth 13 with the 12k six-field set (md5 e7dbf2c8) -> VERDICT BIT-EXACT (L1-L3 on 12000 FENs); with the pack run above: L1-L4 complete.
- Stack members: patches b1_tt_notls.patch + b2_no_zero_movelists.patch + r14_speed2_after_nzm.patch (stacked patch trial_w2.patch); with every switch at 0 the same tree builds to the lock exe FD3A5190 byte for byte (builds\w2off_lp_v1).
- Protocol note (added 12:2x): the ABBA verdict that counts is the wall (engine nps) one; cpu is advisory. Members: NZM2 and SPEED2 are wall winners on their own; TT_NOTLS was a cpu-only winner in its single pack (wall +4.19 % with a wide interval); its 16-round wall re-time is in FINAL_REPORT section 3. The stack itself is a WIN on both metrics.
- QA kit check (12:32-12:34): QA's own `kit_v23\build_ltopgo.ps1 -Expose -Kit <kit folder>` on `F:\ospd\packs\stack_w2\src_kit` (work folder `F:\ospd\qakit\qakit_stack_w2_pc1b`) gives the LTO+PGO exe sha256 db95739378e21771e0b03e42e258f551ebeb3b66f1151f232f4f1b89e7f933a9 = this pack's exe byte for byte; the kit's plain-vs-LTO+PGO node identity: ALL OK; RESULT PASS.

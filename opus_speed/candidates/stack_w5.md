# Speed candidate stack_w5

- State: BIT-EXACT; L3 on the first 2,000 of the 12k FENs (quick); ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\stack_w5\forge_stack_w5.exe` md5 `4d3f7775eadcae90acc690847389d944` sha256 `060c578c9c4a3669244e404c5a89ab69f0d3ccf1fdef604ba614f961b022e59f` (REPRO lp_v1 pc1 = pc2 sha256 060c578c9c4a3669244e404c5a89ab69f0d3ccf1fdef604ba614f961b022e59f)
- Source: `F:/ospd/src/trial_w6` with defaults flipped in `F:\ospd\packs\stack_w5\src_kit`: FORGE_SPD_TT_NOTLS=1, FORGE_SPD_NO_ZERO_MOVELISTS=2, FORGE_SEARCH_SPEED2=1, FORGE_SPD_PREFETCH_EARLY=1, FORGE_SPD_SLIDER_PEXT=1; patch opus_speed/patches/trial_w6.patch md5 5786e9b87a0c3cec4707af521cec85bc (verified: lock + this patch = the built source); branch head at pack time: df428a26 (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_stack_w5_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\stack_w5\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\stack_w5\abba_d20\runs.csv` md5 `ba6c47b459644116ca796832e7de5d6e`
- ABBA summary:
```
run 20261105-132441-7508
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs stack_w5 (B, md5 4d3f7775eadcae90acc690847389d944); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.1194 (+11.94%), 95% t-interval [1.1013, 1.1425], sd/round 2.57%, bootstrap median CI [1.1000, 1.1457]
cpu (nodes / process CPU time of the bench window): B/A median 1.1260 (+12.60%), 95% t-interval [1.1103, 1.1471], sd/round 2.28%, bootstrap median CI [1.1078, 1.1474]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall WIN / cpu WIN (PROTOCOL verdict = wall, the engine's own bench nps; cpu = advisory: it removes preemption by other programs but not SMT-sibling contention; rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: Strict winners stack: every member wins on BOTH wall and cpu (pooled where re-timed): TT_NOTLS + NO_ZERO_MOVELISTS=2 + SPEED2 + PREFETCH_EARLY + SLIDER_PEXT; source trial_w6 with NNUE_ZMM left at 0 (weak winner)
- Timing note: this ABBA ran 13:19-13:24 while the two test suites built exes on CPUs 0-1 (sd/round 2.57 % wall); its median sits below trial_w6's (+14.92 %, a quiet session) by more than NNUE_ZMM's own gain, so treat cross-session differences between stacks as noise: only the direct same-session comparison in FINAL_REPORT 3c ranks two stacks.
- L4 in the pack run above includes the MSVC ASan build (with `/D__BMI2__=1` for the PEXT source): ASan bench 16 = 2587341 = the lock source under MSVC ASan, 0 reports; UBSan 3024920, 0 reports.
- Full 12k L3 (separate run 13:24-13:34, `F:\ospd\packs\stack_w5\bitexact_full12k\bitexact.log`): L1 net on + off and L2 PASS again, 12000 / 12000 FENs identical (depth, score, nodes, bestmove) at go depth 13 with the 12k six-field set (md5 e7dbf2c8), candidate 546 s -> VERDICT BIT-EXACT (L1-L3 on 12000 FENs); with the pack run above: L1-L4 complete.
- QA kit check (13:11-13:12): QA's own kit v2.3 (`build_ltopgo.ps1 -Expose -Kit <kit folder>`) on `F:\ospd\packs\stack_w5\src_kit` (work folder `F:\ospd\qakit\qakit_stack_w5_pc1`) gives sha256 060c578c9c4a3669244e404c5a89ab69f0d3ccf1fdef604ba614f961b022e59f = this pack's exe byte for byte; kit node identity ALL OK; RESULT PASS.

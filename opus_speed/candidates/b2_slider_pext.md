# Speed candidate b2_slider_pext

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\b2_slider_pext\forge_b2_slider_pext.exe` md5 `7c6101401c17f995a8446653a3eb541c` sha256 `46bf171b3aece2618f2ed4850a1ebb8cdc1adcfd153376f3cbf10347b9155c5e` (REPRO lp_v1 pc1 = pc2 sha256 46bf171b3aece2618f2ed4850a1ebb8cdc1adcfd153376f3cbf10347b9155c5e)
- Source: `F:/ospd/src/b2_slider_pext` with defaults flipped in `F:\ospd\packs\b2_slider_pext\src_kit`: FORGE_SPD_SLIDER_PEXT=1; patch opus_speed/patches/b2_slider_pext.patch md5 7c9223e0fae8ea62e1691a5b02c39728; branch head at pack time: c835d270 (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_b2_slider_pext_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\b2_slider_pext\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4 with L4 = UBSan only, ASan N/A: MSVC cannot compile this source (exit 2, see F:\ospd\packs\b2_slider_pext\bitexact\san\build.log); L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\b2_slider_pext\abba_d20\runs.csv` md5 `8e9c8e82e17befbb93cc361077ae9800`
- ABBA summary:
```
run 20261105-120624-9064
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs b2_slider_pext (B, md5 7c6101401c17f995a8446653a3eb541c); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.0137 (+1.37%), 95% t-interval [0.9993, 1.0210], sd/round 1.50%, bootstrap median CI [1.0104, 1.0180]
cpu (nodes / process CPU time of the bench window): B/A median 1.0122 (+1.22%), 95% t-interval [0.9982, 1.0195], sd/round 1.47%, bootstrap median CI [1.0042, 1.0178]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall NO-WIN / cpu NO-WIN (rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: 

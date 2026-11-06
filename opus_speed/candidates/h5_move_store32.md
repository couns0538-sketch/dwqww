# Speed candidate h5_move_store32

- State: BIT-EXACT; L3 on the first 2,000 of the 12k FENs (quick); ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\h5_move_store32\forge_h5_move_store32.exe` md5 `421cd7c007d0717e822b571fa15c935f` sha256 `5dec3fa7e2dc8b58089b4750c3f5dec2a348e68f82cb81d7aa3e132dac6341d3` (REPRO lp_v1 pc1 = pc2 sha256 5dec3fa7e2dc8b58089b4750c3f5dec2a348e68f82cb81d7aa3e132dac6341d3)
- Source: `F:\ospd\src\h5_move_store32` with defaults flipped in `F:\ospd\packs\h5_move_store32\src_kit`: FORGE_SPD_TT_NOTLS=1, FORGE_SPD_NO_ZERO_MOVELISTS=2, FORGE_SEARCH_SPEED2=1, FORGE_SPD_PREFETCH_EARLY=1, FORGE_SPD_SLIDER_PEXT=1, FORGE_SPD_NNUE_ZMM=1, FORGE_SPD_MOVE_STORE32=1; patch opus_speed/patches/h5_move_store32.patch md5 09cc36ddd4f94ca7bb5deb3f99719ad7 (verified: lock + this patch = the built source); branch head at pack time: 40c76304 (the candidate file itself is added in a later commit)
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file F:\ospd\builds\pack_h5_move_store32_lp_v1_pc1\src_copy\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: net on d11/13/16/20/22 312866/862329/3024920/12389307/34048354; net off 375354/907205/2448617/13573040/24506465; perft 5 startpos 4865609 kiwipete 193690690
- Bit-exact log: `F:\ospd\packs\h5_move_store32\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\h5_move_store32\abba_d20\runs.csv` md5 ``
- ABBA summary:
```
skipped (-SkipAbba)
```
- Note: hunt H5: one 32-bit store per generated move

## Quiet decision ABBA vs the live lock trial_w6 (hunt 2026-11-05, QA quiet window)
- Run `C:\ospd_hunt\abba\h5_move_store32_q_d20` (23:35-23:40 PC clock, NNUE training / gates / self-play paused by QA,
  CPU 2 with CPU 3 idle, d20, 10 rounds ABBA/BAAB, fresh copies): wall 1.0121 (+1.21 %) [1.0024, 1.0194] sd 1.18 %,
  cpu 1.0125 (+1.25 %) [1.0033, 1.0213] sd 1.25 %; runs.csv md5 552ea065. abba_recheck.py: PASS.
- Block A/A `aa_w6_d20_qc` (23:15-23:20): 1.0003 [0.9891, 1.0082], width 1.91 % -> SANE by QA's rule.
- QA rule: WIN = interval fully above 1.000 and median gain > A/A width / 2 = 0.96 % -> wall WIN, cpu WIN (no
  contradiction) -> **screening WIN** (also WIN by the skill rule: low > 1.000, median >= 1.010). Not a lock.
- Patches: `patches/h5_move_store32_after_w6.patch` md5 479610c9 (trial_w6 -> tree), `patches/h5_move_store32.patch`
  md5 09cc36dd (lock -> tree). Exe sha256 5dec3fa7e2dc8b58089b4750c3f5dec2a348e68f82cb81d7aa3e132dac6341d3 (md5
  421cd7c0), pc1 = pc2; identity all-0 = FD3A5190, six ON + new OFF = 4181A589.
- Full 12k L3 vs trial_w6: queued after the closing A/A (runner v3 `full`), result below when it lands.

# Speed candidate b1_tt_notls_b

- State: BIT-EXACT; ABBA verdict below. Speed numbers come only from the ABBA CSV named here; anything else is UNPROVEN.
- Exe: `F:\ospd\packs\b1_tt_notls_b\forge_b1_tt_notls_b.exe` md5 `46eb64501c454e496d075159df355227` sha256 `9b6aae65ebd243f9c4fd68bf0a7bad8b091e96548218149d2de6091efa0e523f` (REPRO lp_v1 pc1 = pc2 sha256 9b6aae65ebd243f9c4fd68bf0a7bad8b091e96548218149d2de6091efa0e523f (reused build folders F:\ospd\builds\pack_b1_tt_notls_lp_v1_pc1, F:\ospd\builds\pack_b1_tt_notls_lp_v1_pc2; sources byte-identical to this pack's))
- Source: `F:/ospd/src/b1_tt_notls` with defaults flipped in `F:\ospd\packs\b1_tt_notls_b\src_kit`: FORGE_SPD_TT_NOTLS=1; patch / commit: see opus_speed/patches and the branch commit that adds this file.
- Build: build_variants.ps1 -Variant lp_v1 -Twice (QA kit v2.3 command lines, -Expose); compiler g++.exe (Rev14, Built by MSYS2 project) 15.2.0
  - flags lp: gen/use g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Iinclude -DFORGE_EXPOSE_TUNABLES=1 -flto=1 -fuse-linker-plugin ; use-only [] ; use link + -static -Wl,--no-insert-timestamp
  - training: workload v1 file C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\kit_v23\workload\frozen_train_cmds.txt sha256 1d52720a2662153120c394bba7a0971537dfcad3c40b0550d37e6a27676ace30
- Bench signature: n/a
- Bit-exact log: `F:\ospd\packs\b1_tt_notls_b\bitexact\bitexact.log` -> VERDICT BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset)
- ABBA CSV: `F:\ospd\packs\b1_tt_notls_b\abba_d20\runs.csv` md5 `ec2e86836904733ff8707d54afd2ac64`
- ABBA summary:
```
run 20261105-104129-4828
ABBA lock FD3A5190 (A, md5 2b4821e537c7004b8b588ef9e2ca07b1) vs b1_tt_notls_b (B, md5 46eb64501c454e496d075159df355227); bench d20, 10 rounds, order ABBA/BAAB alternating, CPU 2 BelowNormal, net on, copies Round; nodes A 12389307 B 12389307 (equal)
wall (engine nps): B/A median 1.0419 (+4.19%), 95% t-interval [0.9947, 1.0734], sd/round 5.32%, bootstrap median CI [1.0248, 1.0688]
cpu (nodes / process CPU time of the bench window): B/A median 1.0369 (+3.69%), 95% t-interval [1.0147, 1.0492], sd/round 2.34%, bootstrap median CI [1.0251, 1.0484]
A/A aa_lock_d20_s3: wall n=10 median 1.0066 95% [0.9968, 1.0111] sd 0.99%; cpu median 1.0050 95% [0.9940, 1.0087] sd 1.02%
VERDICT wall NO-WIN / cpu WIN (rule per metric: interval low end > 1.000 and median >= +1.0%); load: see load.txt
```
- Note: Re-run of b1_tt_notls: L1-L3 PASS reused, L4 with the MSVC reference fix

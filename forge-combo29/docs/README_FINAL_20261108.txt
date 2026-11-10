FORGE — live SPEED lock combo29 (KING+SEE+EQ32+CLANG), packaged 2026-11-08 (Europe/Vienna)
=========================================================================================

WHAT THIS IS
  A bit-exact SPEED lock. Same tag, same net, same node counts as trial_w6; it is only faster.
  NO Elo claim. Not a game-gate result.

  tag        AUTOLOCK_1_gate120_e32f003rec_s198 (unchanged)
  base name  base_combo29_clang_E1284F7F
  exe        windows/forge_clang_combo29_trial_w6.exe
  sha256     E1284F7FC492C8FE1285797FDAE8988CF2F2926B33FCFEE7023D284D67D8802E
  md5        c0051c99695f48bf93272d96fe7548c3
  size       2092544 bytes
  published  2026-11-08 02:35:41 CET / Europe/Vienna
             (QA CURRENT_LOCK set_t / PC LastWriteTime 2026-11-08 00:35:41. grok-pc tzutil
             reports Pacific Standard Time; a concurrent Get-Date was 2 hours behind Vienna
             — PC 01:39 vs box 03:39 CET — so PC-local timestamps convert as Vienna = PC + 2h.
             Sequence on the PC clock: overnight DONE 2026-11-07 23:59:55, lockproof DONE
             2026-11-08 00:33:44, lock pointer written 2026-11-08 00:35:41.)
  replaces   forge_ltopgo_x_al1s198_trial_w6.exe sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0
             (previous SPEED lock, packaged 2026-11-05 18:13 Vienna)
  CPU        Windows x64, -march=znver5 (Zen 5 only). PEXT needs BMI2, the NNUE output kernel needs AVX-512F.
  compiler   clang 23.1.5 (llvm-mingw-20261104), ThinLTO + frontend-instrumentation PGO

NET
  The existing AL1 s198 net, embedded: src/nnue_weights.inc md5 22B4B9E2C61B37C0450F13A3A92C19B3
  (sha256 a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638). Identical to trial_w6.
  No new net.

SPEED RESULT (NPS, T1, core 4, 10 blocks, 1 outlier dropped; ABBA vs trial_w6 4181A589)
  median +10.19% (raw 10.191152157626583), CI95 10.10..10.41 (raw 10.099418321622199 .. 10.4090815756553).
  Source: overnight_timing_20261108/RANKED.md rank 1 and LOCK_CANDIDATE.json.
  clang_only (same trial_w6 source, clang recipe only) was +1.385% (CI95 1.099..1.626). The
  KING+SEE+EQ32 source features matter; do not treat this as "just a compiler bump".
  NO Elo claim.

PINS (Threads 1, Hash 16, OwnBook false; d11/13/16/20/22) — UNCHANGED vs trial_w6
  312866 / 862329 / 3024920 / 12389307 / 34048354
  Bit-exact proof vs trial_w6 4181A589 (CURRENT_LOCK.note + lockproof_combo29_20261108):
    12000/12000 FENs on and off; warm-TT 1000 identical (12830 normalised lines, bench 13 =
    862329 on both); T2-4 soak PASS (legal60 + T1 exact tail50 + bench13).
  Sanitizer not run. Binary not byte-reproducible (embedded PDB paths).

FEATURES (default-ON in this tree; each is a switch with the old text under #else)
  FORGE_SPD_KING_LINES=1        include/forge/board.hpp   (and uses in src/board.cpp)
  FORGE_SDK_SEE_HOIST=1         src/board.cpp
  FORGE_SDK_MOVE_EQ32=1         include/forge/board.hpp
  FORGE_SDK_BADCAP_PREFIX=0     src/search.cpp   (code present, NOT enabled)
  The six trial_w6 speed switches are still required and are forced by compiler -D flags
  (header defaults in this snapshot are 0, unlike the trial_w6 src_kit where they were flipped ON):
  FORGE_SPD_TT_NOTLS=1, FORGE_SPD_NO_ZERO_MOVELISTS=2, FORGE_SEARCH_SPEED2=1,
  FORGE_SPD_PREFETCH_EARLY=1, FORGE_SPD_SLIDER_PEXT=1, FORGE_SPD_NNUE_ZMM=1.

SOURCE (source/)
  combo29_snapshot/ and combo29_src.zip (sha256 3762b5827692ea91b341786ea18d22d5f13bcf4f6748d70a9297408454d1e9c4) are the exact
  include/+src/ tree that built E1284F7F, copied from
  D:\grok_sdk_speed_20261107\detached1735_all31\clang\all31_m29\source_snapshot.
  Per-file hashes: combo29_sources_fulltree.sha256 (== SOURCE_INPUTS.sha256). The sha256 of
  that manifest file is 3389cfe3dc7bb3989cfebfbdc8ac13d3785b71f090257664d04a0d7c74137645,
  matching RUN_RECEIPT.source_manifest_sha256 and MATRIX.json mask 13 (m13).
  nnue_weights.inc md5 22B4B9E2C61B37C0450F13A3A92C19B3 verified after CopyToBox.

  Patches vs trial_w6 (generated on the box from the snapshot vs the already-packaged trial_w6 trees):
    combo29_vs_trial_w6_src_kit.patch     vs the src_kit that built 4181A589 (6 files; three of
                                          them are only the six speed-switch header defaults 1/2 -> 0)
    combo29_vs_trial_w6_defaults0.patch   vs the defaults-0 applied tree (only board.hpp / board.cpp /
                                          search.cpp; KING+EQ32, SEE, and BADCAP-scaffolding-default-0)
  Original SDK feature patches (from sdk_speedonly_20261107/patches; applied against the frozen
  defaults-0 trial_w6 tree to produce clang_four, then configuration-forked to m13/combo29):
    patches/clang_four_B3_king_lines.patch     KING
    patches/clang_four_B10_see_hoist.patch     SEE
    patches/clang_four_D4c_move_eq32.patch     EQ32
    patches/clang_four_B4a_badcap_prefix.patch BADCAP (NOT enabled in combo29)
    patches/clang_four_vs_frozen.patch         all four ON = clang_four, NOT this lock
  C:\Users\Administrator\grok-pc\forge_push\sdk_speedonly_20261107\src_speedcombo_h256 was not
  present on the PC; the build's own source_snapshot was used instead.

  Rebuild (Windows, grok-pc, same recipe): see source/BUILD_RECIPE.txt and source/c_t2_build.ps1.
  clang++ 23.1.5, ThinLTO + IR-PGO, flags -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256
  -DFORGE_EXPOSE_TUNABLES=1 plus the six trial_w6 -D switches above, -ffp-contract=off
  -fno-fast-math -march=znver5 -pthread -g -gcodeview -flto=thin -fuse-ld=lld -static
  -Wl,--no-insert-timestamp -Wl,--thinlto-jobs=1, instrument then -fprofile-instr-use with
  -Werror=profile-instr-unprofiled -Werror=profile-instr-out-of-date. A rebuild will NOT match
  E1284F7F byte-for-byte (embedded PDB paths). Check pins and, for a speed claim, a quiet ABBA.

  Plain Linux build (no PGO, node counts only; not provided): g++ -std=c++20 -O3 -DNDEBUG
  -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=x86-64-v4 -pthread -Iinclude
  src/*.cpp -o forge plus the six trial_w6 -D switches; bench must hit the pins above.

LINUX
  No Linux build of combo29 exists, so none is included (none invented).

DOCS (docs/)
  CURRENT_LOCK.json              live pointer from grok-pc, md5 445c8dd5cc15a3f96c6fc8c9b900613c
                                 (= lock dir CURRENT_LOCK.json.staged)
  lockdir_SHA256SUMS             lock-dir SHA256SUMS (exe only; matches E1284F7F…)
  QA_LOCK_PUBLISH_COMBO29_20261108.md
  overnight/RANKED.md            all-31 table (combo29 #1)
  overnight/LOCK_CANDIDATE.json  exe path, sha256, raw +10.191% and CI
  overnight/DONE.json RESULTS.json MAIN.log main.ps1 CURRENT_STAGE.json
  lockproof/DONE.json STATUS.txt soak.log warm.log run.ps1 soak_t4/RECEIPT.json
                                 (large UCI cand/ref logs left on the PC, not packed)
  context/HANDOFF.md SOURCE_PROOF.json MACRO_DEFAULTS.txt
                                 historical sdk_speedonly three-candidate handoff;
                                 clang_four described there is NOT this lock

RULES: already-started gates keep their prior (trial_w6) base; new work rebases on combo29.
  Never pool results across bases. Every new engine change ships as a default-0 switch with
  the lock text under #else; prove bit-exactness before any speed claim; Elo only from SPRT gates.

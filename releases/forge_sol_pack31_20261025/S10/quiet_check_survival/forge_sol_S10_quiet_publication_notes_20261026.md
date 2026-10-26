# S10 quiet-check feature — 2026-10-26

This is the completed first feature checkpoint inside the still-running S10 job. It is rejected by the prescribed WAC screen and is not adopted. The other three ideas remain pending. No strength or speed gain is claimed.

Baseline code is 1ab50b2dd64d9b2f752f7f1285f6968cad2fd792 plus the unchanged supplied network 74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b. Lprime/B retain reviewed JobC/S01 tests; B retains the buffer repair. This patch is 2c195c2d15f044128b68a2efc39500314b3310f551c53980b9965773358089e3, unchanged from the prepared source, with one UCI and build option both default OFF.

Native builds use GCC14.2/C++20 with -O3 -DNDEBUG -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256. Only enabled experimental builds add -DFORGE_S10_QUIET_CHECK_SURVIVAL=1. To exercise it, set UCI QuietCheckLmpSurvival=true before search. The separate benchmark Searcher inherits the option. Exact commands, compiler flags, source hashes and original process results are preserved in the data-only archive. The source patch applies independently to the supplied L/Lprime/B; do not patch original inputs.

The original operational WAC result says PASS because all 300 searches completed legally. The acceptance decision is FAIL: 269 solved is below 283. B's PASS_LOCAL_QUALIFICATION does not override that feature decision. No WAC retry or B WAC run occurred. Games 0; no W/L/D or Elo estimate. Windows and owner-PC speed/strength gates remain UNVERIFIED.

Check the dated SHA256SUMS file from a complete downloaded folder. The archive's mapping plus Python/GNU round-trip receipt preserve every original data byte; binaries, caches and private engine source remain outside the data archive. The existing controller and the fixed/reviewed T2 supplement are already preserved under validation/forge_sol_pack31_20261025 in the earlier source/review checkpoints. This packet contains no executable or source ZIP. Continue ImprovingRazorGuard, SingularSiblingLmr and CaptureHistoryLmp, then S11 and the remaining saved queue.

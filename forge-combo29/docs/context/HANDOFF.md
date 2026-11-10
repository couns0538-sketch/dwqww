# Three independent speed-only candidates — 2026-11-06 PST
Status: PREPARED / HOLD for native build; no Windows exe/pins produced.
Inputs manifest MD5 805141c5a1f4a0869ef3b76bdd3ab3e4; all 272 SHA256-listed files independently verified (not merely reported 27/27).
Base actual trial_w6 search.cpp MD5 2191d17e9b762a1b2974f9f7796d03fd, SHA256 3171133b6ed7537b01d3a446f42d8723ec93ff14bed648e883b10647041d1aaa; never old D05507.
All trees copied fresh from verified src_w6, not cball4/6/7 or postA. src_w6 headers default six speed switches to 0; builds explicitly override them to 1/2/1/1/1/1 for trial_w6 identity. Header-default distinction is intentional and recorded, not an assertion of byte-identical header trees.
1 clang_four: ONLY KING_LINES/BADCAP_PREFIX/SEE_HOIST/MOVE_EQ32 ON, exact clang c_t2 recipe. Despite scope nickname BUNDLE4, not broad SDK BUNDLE4_all patch (contains extra excluded mechanisms).
2 clang_only: unchanged trial_w6 source inputs, exact clang c_t2 recipe.
3 gcc_king: KING_LINES alone; GCC LOCK lp_v1 LTO+PGO recipe, NOT clang.
B4a port adapts only unchanged context from MoveList::Capacity back to 64; no A1 introduced. A5 root_drawn tail byte-identical; uci.cpp and net byte-identical for every leg. A6/A7/B9e/B7a absent. Scoped single patches applied -F0; offsets only. Final unified diffs git apply --check PASS against frozen base. SOURCE_PROOF.json and MACRO_DEFAULTS.txt give all changed files, net hash and flags.
NET MD5: 22b4b9e2c61b37c0450f13a3a92c19b3; SHA256 a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638.
BLOCKER: exact native scripts require C: compiler/sysroot while windows-pc-safe-run permits D:-only; no existing explicit standing waiver/approved spare CPU is supplied here. GCC script also hardcodes 0x3 affinity (two CPUs) vs requested single job/approved core, and historical kit path. Do not bypass launcher/copy roots or infer permission from QA. QA run plan in scripts/QA_COMMANDS.md identifies exact operational resolution needed; no invented compiler path.
Clang script uses sequential unit compiles but ThinLTO link-worker budget is not explicit. Need approved single-worker linkage resolution without silently changing exact recipe. Clang suppresses profile-unprofiled/out-of-date diagnostics; profile completeness remains unverified.
NOT RUN: PC preflight, builds, PGO coverage inspection, Windows exe SHA256, requested Hash16 Threads1 d13 net-on/off benches (expected 862329/907205). No speed/match/lock/queue/publication. Historical logs labeled HISTORICAL are supplied SDK evidence, NOT results for these candidates. No PC calls/writes made.
QA alone owns quiet ABBA and lock qualification. Full per-file hashes in SHA256SUMS; immutable handoff, no external sends.

## 2026-11-16T22:25:14Z
seat 21, area 1 (FEN INPUT). **Threads 1 in every run.** Builds: base 6b98f217 and PC r15
(both Release-verified and ASan+UBSan-built).

**Done since the last push**
- job19: the full 20,000-mutation FEN sweep on the PC build under PC20. **Identical to the base
  tree case for case** — 18,775 refused / 1,225 accepted / 39 python-invalid / 0 crash / 0 hang
  / 0 sanitizer / 0 illegal; the per-FEN diff against job1 is EMPTY. The PC patch does not touch
  FEN acceptance. `job19/out/pc20_summary.txt`.
- job18 (pushed earlier): 21-F9 REPAIRED on the PC build (compile-time FORGE_FIX_ROOT_DRAWN, not
  the PC20 options); 21-F8, 21-F11 and 21-F2 all SURVIVE on the PC build.

**Findings state**: 11 base-tree findings F1..F11; of these F9 is repaired on the PC build,
F8/F11/F2 confirmed still open there, F10 confirmed identical there. 6 checks, 1 verified patch.

**Next**: probe 21-F11 (mate 0) on stalemate and insufficient-material roots on the PC build,
then look for a new find in the PC patch's own new code paths (the six FORGE_FIX_ switches).

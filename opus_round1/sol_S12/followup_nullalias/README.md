# S12 follow-up: null-edge accumulator alias (Sol's patch 66efe4c9, ported to AL1)

**What it is.** After a null move the pieces do not change, so the null child's NNUE accumulator equals its parent's.
AL1 still copies it (a `nnue::update` with zero dirty pieces, 2 KiB). Sol's patch lets the null child borrow the
parent's accumulator and runtime PSQT through `SearchStack::accumulator_owner`, so the copy is skipped. Values and
search trees do not change.

**Switches (both default off).**
- Build switch `FORGE_NNUE_LAZY_ACC` (CMake option, or `-DFORGE_NNUE_LAZY_ACC=1` with the PC recipe). Without it the
  build is the lock binary.
- With it, the UCI option `NnueLazyAcc` (check, default false). When true and NNUE is in use, each search prints
  `info string NnueLazyAcc active` once and `info string NnueLazyAcc stats ...` per search.

**Files.**
- Engine: `CMakeLists.txt`, `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp` (Sol's hunks, unchanged).
- Tests (built only with the switch): `tests/forge_sol_S12_lazyacc_native_regression_v2_20261027.cpp` (Sol's test,
  one substitution, CTest `forge_s12_lazyacc_tests`) and `tests/s12_lazyacc_extra_tests.cpp` (CTest
  `forge_s12_lazyacc_extra_tests`).
- Tools here:
  - `alias_stats.py`: bench with the option on, AL1 node check, alias counters per depth.
  - `uci_check_opt.py`: AL1 identity with extra options; copy from opus-sol-S13.
  - `mutation_check_alias.py`: planted bugs.
  - `nps_ab_opts.py`: ABBA NPS with per-side options; copy from opus-sol-SIT.
  - `uci_threads_session_s12.py`: threaded session for TSan; copy from S13 with the option renamed.
  - `ci_s12_alias.sh`: CI driver for `.github/workflows/opus-sol-s12-alias.yml`.

**Run on the PC.**
```
bash D:/grok-pc-data/dwqww/.claude/worktrees/b/tools/build_pc.sh "$PWD" <out>/forge_on.exe -DFORGE_NNUE_LAZY_ACC=1
python -I -B opus_round1/sol_S12/followup_nullalias/uci_check_opt.py <out>/forge_on.exe --full --set NnueLazyAcc=true
python -I -B opus_round1/sol_S12/followup_nullalias/alias_stats.py <out>/forge_on.exe 13 16 20
```

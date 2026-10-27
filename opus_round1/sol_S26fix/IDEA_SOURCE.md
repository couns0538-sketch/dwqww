# IDEA_SOURCE — sol_S26fix

- Fix-up list S26-1, S26-v4-1..3: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 3 (QA, 2026-10-27).
- Tool under test: Sol's S26 net-batch v4 (`successor_ctest_v4/forge_sol_S26_netbatch_v4_20261026.py`, sha256
  4dbf73e6…), his portable setup/launcher, helpers (S05/S01/S27/S07), bench refs, allowlist and WAC300 suite, all
  read from his commit 17aa0cae (sparse checkout in CI). v5 changes one condition in `check_ctest`.
- Base B recipe: lock archive `forge_LOCK_AL1_s198_FULL_20261026_1039` (`7_history/strength_packs/buffix_node_identical/`
  buffix patch + pre-merge docs, `4_tests/optional_lockderived_tests_patch/merge_record_h256e12/` Job C/S01 merge).
- Nets: the lock archive's `5_nnue/nets/history_all_CR_passed/` copies (SHA256 equal to Sol's bench refs).
- CI recipe: opus-ci (`opus_round1/ci/run_ci.sh`) asan mode, g++-14 on ubuntu-24.04.
- CTest JUnit semantics (`status="run"` / `"fail"` / `"notrun"`): CMake's own JUnit writer, observed in the real
  CI output. No external project code.

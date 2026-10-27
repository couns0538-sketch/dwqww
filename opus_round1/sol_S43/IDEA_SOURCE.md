# IDEA_SOURCE (S43 S26 add-on: absolute paths, --base, bench-ref file)

IDEA_SOURCE: make the S26 net-pack batch take `--base <dir>` and a bench-reference FILE, with absolute output paths
everywhere, as specified in Sol's S43 task (`forge_sol_all_jobs_inventory_20261026.json`, job S43, spec line 227).
Ideas only; no engine code is changed or copied.

- Sol's S26 kit (branch `forge/sol-pack31-20261025` @ `17aa0cae`, `releases/forge_sol_pack31_20261025/S26/`), read only:
  the v4 net-batch design (private source copy per net, net swapped into `src/nnue_weights.inc`, bench at five depths
  against a reference file, FMA count, CTest with a known-failure allowlist), its `forge-s26-bench-refs-v1` and
  `forge-s26-allowlist-v1` file formats (used unchanged; Sol's two files are consumed as-is). v5 is a new PC-native
  file; Sol's files are not edited.
- The PC lock build recipe and CMake/CTest wiring: the lock archive's `build_pc.sh` / `cmake_build.sh` and
  `2_build/uci_check.py` (bench/perft UCI dialogue), as used by the forge-engine-verify procedure.
- AL1 references: lock archive `00_README_FIRST.md` / `3_lock_record` (bench pins) and
  `4_tests/FORGE_KNOWN_TEST_FAILURES.md` + `3_lock_record/ctest_linux_box_AL1_s198_20261026.log` (known lines).
- Base B (lock code + node-identical buffix, h256_e12 net 74c4009d…): `C:\Users\Administrator\grok-pc\forge_push\
  buffix_h256e12_20261025` (read only; staged copy), whose CR box build is exe `55fa7e81…` (lock archive CR notes).

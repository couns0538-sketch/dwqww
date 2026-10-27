# IDEA_SOURCE — sol_S27fix

- Fix-ups S27-1..3: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 3 (QA, 2026-10-27).
- Base code: Sol's `forge_sol_S27_hygiene_20261026.py` and `forge_sol_S27_buildcompare_20261026.py` (17aa0cae),
  transformed by exact replacements; his tests and known-hash catalogue are used unchanged.
- GNU patch option `--no-backup-if-mismatch` and CTest/CMake behaviour: their own documentation/behaviour.
- AL1 pins: the lock record (`forge-engine-verify` skill); buffix + CR record: the AL1 lock archive
  (`7_history/strength_packs/buffix_node_identical/`). No external project code.

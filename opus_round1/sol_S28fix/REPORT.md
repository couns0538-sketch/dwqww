# S28fix — S28-1: Job C pin proposal redone on AL1 s198 (PROPOSAL ONLY, NOT APPLIED) — DONE

Branch `opus-sol-S28fix` = `d4f4312` + CI baseline (cherry-pick 0b1f29bd) + 1505ccf5 (job folder only; tool-only diff empty).
Nothing applied to any accepted tree. Sol's lock-transition kit, lock recipe, PGO and delivery scripts were not run. Machine exclusive: no.

## Acceptance
| line | result | evidence |
|---|---|---|
| base = AL1 + lock-derived Job C/S01 tests (lock archive patch 4bd3ac98…; tests.cpp 55334ba9…) | prepared in scratch | inputs/forge_lockderived_jobC_S01_tests_tools_vs_AL1.patch |
| observe AL1 s198 (lock exe 5d4df7f1, net md5 22b4b9e2) | WAC001 f6h5 cp 623 d12 (Hash 8); promotion_white c6d6 cp 569 d1; promotion_black c3d3 cp 569 d1 | logs/al1_s198_pin_observation.json (own observer, not the kit) |
| un-patched AL1L forge_tests on the PC build | rc 1: 3 PIN_MISMATCH (WAC 661 vs 623; c6d7 vs c6d6; c3d2 vs c3d3) + 4 FAIL; observed values identical to the UCI observation | logs/al1L_forge_tests_before.stderr |
| proposal | forge_sol_S28_v3_AL1s198_pin_proposal_20261027.patch against AL1L: tests.cpp documented_wac_score 661->623 and king pins c6d7/c3d2 -> c6d6/c3d3; tools/rerecord_pins.py CASES the same; README checklist and IDEA_SOURCE notes; h256_e12 and 6.4.24 values kept on record; no src/include/CMake/expectation-logic change; KNOWN_FAILURE output text left byte-stable | patch + README |
| consistency | checker PASS (values = UCI observation = forge_tests "observed"; scope 4 files; protected text intact) | logs/check_proposal_v3.log |
| dry runs only | git apply --check + GNU -p1 -F0 --dry-run clean on a scratch copy; the copy stayed identical | logs/proposal_dryrun.log |
| tests / planted bugs | 8 OK (wrong score, kings not re-recorded, helper left at 661, engine-file hunk, KNOWN text change, forge_tests disagreement) | logs/tests_v3.log |

## Findings
- Unlike e48f006 (only the WAC pin moved), AL1 s198 also changes both underpromotion king moves. An f006-style one-pin proposal would leave two PIN_MISMATCH lines.

## Left / UNVERIFIED
- Adoption is a CR decision (8-0 net-lock rule). Re-run the helper in observe-only mode on the adopted exe first.
- Expected after-state (0 FAIL, 4 KNOWN) was not built, by design (never applied). It is inferred from the test logic and the CR's e48f006 precedent: UNVERIFIED.
- Plain AL1 tests (no Job C pins) and their CI known-failure set are unaffected.

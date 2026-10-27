# IDEA_SOURCE — sol_S28fix

- Fix-up S28-1: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 3 (QA, 2026-10-27): redo the pin proposal on AL1 s198 instead of
  f006; proposal only, never applied; the lock kit is not run.
- Pattern: Sol's S28 v2 e48f006 pin proposal (17aa0cae, read only) and the CR's
  `4_tests/pins_transition_e48f006_PROPOSED/` README/diff in the AL1 lock archive (same files, same "keep old pins on
  record" style).
- Pin mechanism and cases: the lock-derived Job C/S01 tests patch for AL1 (`tests/tests.cpp`, `tools/rerecord_pins.py`).
- Observation protocol: the S01/S26 UCI pin observer (Threads 1, Hash 8 / 1, OwnBook false, go depth 12 / 1); own
  re-implementation. No external project code.

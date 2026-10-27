# sol_S28fix — S28-1: Job C pin proposal redone on AL1 s198 (PROPOSAL ONLY, NOT APPLIED)

QA fix-up S28-1: Sol's S28 v2 pin proposal (`forge_sol_S28_v2_e48f006_pin_proposal_20261025.patch`) targeted the
e48f006 net, which never became the lock. This redoes it for the actual lock AL1 s198. It is a proposal document:
nothing was applied to any accepted tree, Sol's lock-transition kit / lock recipe / PGO / delivery scripts were not
run, and adopting it is a separate reviewed change (8-0 net-lock rule: "relabel tests afterwards in a reviewed change").

## Inputs (read only)

| item | identity |
|---|---|
| AL1 source | branch base `d4f4312` (= lock tree `294dbed3`), net `src/nnue_weights.inc` md5 22b4b9e2 (= lock record) |
| Job C/S01 lock-derived tests for AL1 | lock archive `4_tests/optional_lockderived_tests_patch/forge_lockderived_jobC_S01_tests_tools_vs_AL1.patch`, sha256 4bd3ac98…, copied to `inputs/`; gives `tests/tests.cpp` sha256 55334ba9… and `tools/rerecord_pins.py` af138972… ("AL1L") |
| AL1 s198 lock exe | `forge_h256_s198.exe` sha256 5d4df7f1… (lock archive / `b/base`) |

## Observed on AL1 s198 (two independent paths)

| case | documented (h256_e12) | UCI observer, lock exe (`logs/al1_s198_pin_observation.json`) | AL1L `forge_tests`, PC build (`logs/al1L_forge_tests_before.stderr`) |
|---|---|---|---|
| WAC 001 d12 (Hash 8) | f6h5 / 661 / d12 | f6h5 cp 623 d12, PV f6h5 | PIN_MISMATCH … observed f6h5/623/d12/PV=f6h5 |
| rook underpromotion, white, d1 | c6d7, score > 100 | c6d6 cp 569 d1 | PIN_MISMATCH … observed c6d6/569/d1/PV=c6d6 |
| rook underpromotion, black, d1 | c3d2, score > 100 | c3d3 cp 569 d1 | PIN_MISMATCH … observed c3d3/569/d1/PV=c3d3 |

Before the proposal, AL1L `forge_tests` on AL1 s198 exits 1 with 3 PIN_MISMATCH and 4 FAIL lines. Unlike e48f006
(where only the WAC pin moved), AL1 s198 also plays different king moves in both underpromotion positions, so the
f006-style one-pin proposal would still leave two PIN_MISMATCH lines.

## Proposed change — `forge_sol_S28_v3_AL1s198_pin_proposal_20261027.patch` (against AL1L, -p1, 4 files)

- `tests/tests.cpp`: `documented_wac_score` 661 -> 623 (move f6h5 and depth 12 unchanged); `documented_king_text`
  c6d7/c3d2 -> c6d6/c3d3; comments keep the h256_e12 pins (f6h5/661/d12, c6d7/c3d2 642 cp) on record. The 6.4.24
  TacticalCase expectation (g3g6 >= 31997 at d12), the rook expectations (c7c8r/c2c1r) and all test logic are untouched.
  The KNOWN_FAILURE output text keeps "h256_e12 net-evaluation horizon" on purpose (byte-stable for existing
  allowlists such as Sol's S26 allowlist); relabelling it would be a separate cosmetic change.
- `tools/rerecord_pins.py`: CASES WAC001 661 -> 623, promotions c6d7/c3d2 -> c6d6/c3d3; two comment lines keep the
  h256_e12 and 6.4.24 values. tests.cpp and the helper change together.
- `README.md` checklist step 3/4 and `IDEA_SOURCE.md` (one paragraph) record the new pins and keep the old ones.
- No `src/`, `include/`, CMake or net change.

Expected effect if a reviewer applies it (not done here): the documented-horizon branches match, so the three
PIN_MISMATCH lines and the two ordinary WAC FAIL lines turn into KNOWN_FAILURE lines (WAC 001 x2 with 623, rook
underpromotion x2 via c6d6/c3d3), and the helper's default lock check matches 3 of 3. Companion record row for
FORGE_KNOWN_TEST_FAILURES.md (also only a proposal): "AL1 s198 + lock-derived Job C/S01 tests: 4 KNOWN_FAILURE
(WAC 001 x2 f6h5 623 at d12; rook underpromotion x2 c6d6/c3d3 569 at d1)".

## Verification done (no application)

- `forge_sol_S28_check_proposal_v3_20261027.py`: the proposed values equal the UCI observation and every PIN_MISMATCH
  'observed' value of the un-patched forge_tests run; scope limited to the four files; protected text intact -> PASS
  (`logs/check_proposal_v3.log`). 8 tests incl. 6 planted defects (`logs/tests_v3.log`).
- `git apply --check` and GNU `patch -p1 -F0 --dry-run` on a scratch copy of AL1L: clean; the copy stayed identical
  (`logs/proposal_dryrun.log`).

## Flags for review

1. Three pins move, not one (see table). Re-record both places together (tests.cpp + helper).
2. This proposal is for the lock-derived tests on AL1 (AL1L). Plain AL1 (`tests/tests.cpp` without Job C/S01) has no
   documented pins; its known-failure set (CI `check_known_failures.py`: 4 FAIL lines, WAC score 623) is unchanged.
3. Only the AL1 s198 net was observed; the e48f006 proposal stays Sol's (for that net, if it is ever adopted).
4. Re-run the helper in observe-only mode on the exact adopted exe before applying; any difference blocks the change.

## Files

`forge_sol_S28_pin_observe_v3_20261027.py` (observer), `forge_sol_S28_make_proposal_v3_20261027.py` (writes the patch
from the observation), `forge_sol_S28_check_proposal_v3_20261027.py` (checker), `test_forge_sol_S28_proposal_v3_20261027.py`,
`inputs/` (lock-derived tests patch), `logs/`.

```sh
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
$PY -I -B forge_sol_S28_pin_observe_v3_20261027.py forge_lock.exe --out obs.json
$PY -I -B forge_sol_S28_make_proposal_v3_20261027.py <AL1L tree> obs.json NEW.patch
$PY -I -B forge_sol_S28_check_proposal_v3_20261027.py NEW.patch obs.json [forge_tests.stderr]
$PY -I -B test_forge_sol_S28_proposal_v3_20261027.py -v
```

# S47 AUTO-LOCK audit verifier and net-only tree check: DONE (opus, 2026-10-27)
Branch opus-sol-S47 (base d4f4312 + 0d99f02), head 21890be9. Tool job, no engine change; pushes [skip ci], no CI run.

## What was done
- Part A `forge_sol_S47_verify_netonly_tree_20261027.py`:
  - hashes include/ and src/ raw and after CRLF->LF; exits 0 only if the single difference is `src/nnue_weights.inc` and its md5
    matches; prints a JSON verdict with the diff list;
  - `--lock` accepts any AUTOLOCK dir (reads `source/` and LOCK.json, cross-checks the lock's own net md5);
  - `--gate-json` with `ag_rebase_of` and a non-net diff gives a FAIL with a Z-1 message.
- Part B `forge_sol_S47_autolock_audit_20261027.py`:
  - A1 new dir (AUTOLOCK_<n>_<tag>, n above the old lock, LOCK.json consistent, no orphan lower-n dir);
  - A2 old lock files and old exe unchanged against the old lock's own hash list;
  - A3 net md5 = gated net; A4 exe = gate and confirm RUN_INFO candidate;
  - A5 bench d11-d22 twice identical, = gate prebench.cand_off and != the old lock's own bench reference;
  - A6 perft/kiwipete/FMA 0; A7 UCI list equal to the old lock's; A8 confirm srand and start differ from the gate's;
  - A9 verdicts H1, not VOID; A10 pins unchanged or allow-listed reviewed diffs (attached, not applied; tests/ trees compared);
  - A11 CR record as INFO only.
  - Output: one markdown packet + JSON. FAIL, INCOMPLETE (anything MISSING) or ALL_CHECKS_PASS, and even the last is "not a CR
    approval": it never writes CR_PASS.
- Also: deterministic fixtures, 21 tests, 13-mutant check, sample packets (fixture + real AUTOLOCK_1), the zip deliverable,
  README_S47_20261027.md, IDEA_SOURCE.

## Evidence
| check | command | raw result |
|---|---|---|
| tests | `S47_SCRATCH=… python -W error::ResourceWarning -I -B test_autolock_audit.py` (venv 3.10.22) | Ran 21, OK |
| mutation | `python -I -B mutation_check_s47.py --scratch …` | 13/13 CAUGHT |
| spec FAIL cases | tests | edited pin -> A10 FAIL; bench +1 node at d16 -> A5 FAIL "drift [0, 0, 1, 0, 0]"; confirm srand = gate -> A8 FAIL |
| real inputs | run_s47_evidence.sh step 4 | lock archive + PC files copied cp -p; sha256 of copy = original |
| Part A R1 | `--lock AL1_tree --cand AL1_plus_f029 --net-md5 652f7bcf…` | exit 0, differ [src/nnue_weights.inc] |
| Part A R2 | `--lock AL1_tree --cand O3_tree` | exit 1 (search.hpp, search.cpp + 19 extra files) |
| Part A R3 | CRLF copy of R1 | exit 0, 16 CRLF-only ignored |
| Part A R4 | `--lock h256_e12_tree --cand AUTOLOCK_1 copy --net-md5 22b4b9e2…` | exit 0: real AL1 is net-only |
| Part A R5 | `--lock AUTOLOCK_1 copy --cand AL1_plus_f029` | exit 0 |
| Part B real | `--old-lock old_h256_e12 --new-lock AUTOLOCK_1 copy …` (see run_s47_evidence.sh) | exit 3 INCOMPLETE (A7 MISSING, see below) |

Part B real-run details:
- A2: 73 h256_e12 files + exe 456743d9 unchanged.
- A3: net 22b4b9e2 = gated s198 net. A4: exe 833c47f3 = G120 and G120c RUN_INFO.
- A5: bench 312866/862329/3024920/12389307/34048354 ×2 = prebench and != the h256_e12 bench 308972/… from G120 PREBENCH.txt.
- A6 perft/FMA OK. A8: srand 344808634/1983003762, start 321001/348001. A9: both H1. A10: no pins.
- A7 MISSING: no h256_e12 UCI list. A11: CR_PASS_AUTOLOCK_1.txt present (not judged).

## Left
- Supply a real h256_e12 `uci` dump to close A7.
- Checklist points 1, 3, 7, 8, 9, 10 are not covered by this tool (Sol's S28_v2 checker / N33 runner).

## UNVERIFIED
- Sol's L/B trees are not in the repo, so "B vs L" was run as AL1 vs the opus-O3 tree; the f029 candidate is constructed as the spec
  describes, not a real AUTOLOCK.
- Pins can be shown "applied" only where both lock trees carry tests/ (AUTOLOCK dirs keep include/ + src/ only).
- Nothing was run on the PC.

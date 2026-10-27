# S36 [Sol leftover] Same-diff merge verifier — DONE

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 32 (inventory S36). Branch `opus-sol-S36` = `d4f4312` + `0d99f02`
cherry-picked + this job. Tool job, no engine change (`[skip ci]`). Deliverable:
`forge_sol_S36_samediff_verify_20261027.py`.

## Acceptance (Sol's pass line)
| line | result | evidence |
|---|---|---|
| reports L' and B as the same change set for Job C + S01 (tests/tools/docs only, forge sources identical) | **PASS**. The approved list is Job C (4ac98f92) + S01 (bddc9611) + the CR-approved LOW 1-4 follow-up. Both merge diffs equal it on all 5 files (`tests/tests.cpp`, `README.md`, `IDEA_SOURCE.md`, `tools/rerecord_pins.py`, `tools/rerecord_pins.sh`), and no `src/`, `include/`, `bench/` or `CMakeLists.txt` change: **SAME_CHANGE_SET** (r2 with the L follow-up, r3 with the B follow-up). README and IDEA_SOURCE carry a NOTE that the same lines sit at different places in B, which the merge notes record ("doc hunks ... on B they land just before the h256_e12+buffix sections, as CR reviewed") | `logs/step2_real_runs.log` |
| flags a planted one-line extra change | **PASS**. One extra line in B's `tests/tests.cpp`: DIFFERENT ("B differs from the approved changes", "L and B differ", the line itself listed). One extra line in `src/search.cpp`: DIFFERENT, also "protected forge source changed" | r5, r6 |
| deterministic output | **PASS**. A re-run of r2 gives a byte-identical JSON; the tests also compare two runs | r2_again, tests |
| tests | **PASS 7/7**: placement-insensitive equality, sequential approved patches compose, planted test line, protected source, allowed paths and new files (incl. "No newline at end of file"), determinism, malformed hunk = exit 2 | `logs/step1_tests.log` |

## Extra findings
- **Job C + S01 alone is not the whole merge.** With only those two patches approved (r1), the tool flags every
  follow-up line in README, IDEA_SOURCE and both tools files. The merge diffs therefore contain the CR LOW 1-4
  follow-up, as the merge notes say ("final diffs regenerated"). Reviewers should approve the follow-up together
  with the two patches.
- **The two follow-ups match.** The follow-up diffs of L and B are the same change set (r4).
- **The AL1 optional patch carries exactly the approved change.** The lock archive's
  `forge_lockderived_jobC_S01_tests_tools_vs_AL1.patch` is the same change set as the L' merge (r8).
- **Input integrity.** The merge record's own `SHA256SUMS_merge_jobC_S01_20261025.txt` verifies all four diffs
  and the notes; the approved patches' sha256 equal the hashes in the merge notes.

## Files
`forge_sol_S36_samediff_verify_20261027.py`, `test_forge_sol_S36.py`, `run_s36_evidence.sh`, `README.md`,
`IDEA_SOURCE.md`, `REPORT.md`, `logs/` (step 1 tests, step 2 real runs), `results/` (r2 and r5 JSON), `FILES.txt`,
`SHA256SUMS`. The inputs are read-only copies in `F:\opus_scratch\sol_S36\inputs` (lock archive merge record +
Sol's patches). Machine exclusive: no.

## UNVERIFIED
- Line-text nets cannot tell a moved line from the same line at its old place. A pure move is visible only as a
  NOTE (different blocks), never as a failure. That is deliberate for doc placement, but a reviewer must read the
  NOTEs.
- The trees themselves were not rebuilt here. QA's merge notes record the builds, ctest and bench of L' and B; this
  tool checks the diffs.

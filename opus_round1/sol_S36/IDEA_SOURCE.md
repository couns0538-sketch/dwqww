# S36 idea sources

- Spec: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 32 / inventory S36 (spec line 189): normalise hunks (ignore
  offsets and context) and report per file whether both trees got exactly the approved changes and nothing else.
- Inputs: the lock archive's `4_tests/optional_lockderived_tests_patch/` merge record (QA's Job C + S01 merge into
  the lock-derived tree L' and the in-place base B, 2026-10-25, with `MERGE_NOTES_jobC_S01_20261025.md`).
  - The approved patches come from Sol's branch: Job C `forge_sol_knownfail_h256e12_20261025.patch` (sha256
    4ac98f92…) and S01 `forge_sol_S01_pinmsg_20261025.patch` (bddc9611…), the hashes the merge notes name.
  - The CR-approved LOW 1-4 follow-up diffs are part of the merge record.
- Method: a patch-equivalence check by signed line multisets. Applying patches in sequence adds up, so a merge diff
  equals the sum of its approved patches when no other line was touched. This is the idea behind `interdiff` /
  `git range-diff`, reduced to what a reviewer needs: per file, "exactly these lines and nothing else". The block
  multiset adds a placement view on top.

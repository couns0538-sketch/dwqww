# S27fix — S27 patch-hygiene v2: no .orig abort + per-base errors, --ref/--expected-nodes (AL1 default), reviewed-bugfix allowlist + relative --base — DONE

Branch `opus-sol-S27fix` = `d4f4312` + CI baseline (cherry-pick 7578c69b) + 2963a9ca (job folder only; tool-only diff empty).
v2 files are generated from Sol's v1 by exact single-occurrence replacements (logs/*_v1_to_v2.diff). Machine exclusive: no.

## Acceptance
| line | result | evidence |
|---|---|---|
| S27-1 GNU patch --no-backup-if-mismatch (no .orig abort) | PASS: an offset hunk passes with no .orig; v1 leaves .orig and reports applied_path_mismatch | test_offset_hunk_passes_without_orig, test_v1_aborted_on_the_same_offset_hunk |
| S27-1 per-base errors without aborting | PASS: v2 records the base_limit error on base A_big (36 MB tree) with status ERROR and still checks B_AL1 (CHECKED); v1 stops with no base rows | logs/real_runs_v2.log R5/R6; unit test |
| S27-2 buildcompare --ref/--expected-nodes, default AL1 | PASS: REFSETS AL1 (default)/Lprime/B or a JSON file; --expected-nodes overrides; --parallel default 1; new `existing` CLI. Lock exe 5d4df7f1 vs box build of AL1+buffix (924cbaf7, FMA 0): PASS at 312866/862329/3024920/12389307/34048354, UCI and 21,409 symbols identical; --ref Lprime FAILs at the d11 gate; explicit nodes PASS | logs/compare_existing_v2.log, logs/compare_existing_refAL1_comparison.json |
| S27-3 general reviewed-bugfix allowlist | PASS: forge_sol_S27_reviewed_bugfixes_v2_20261027.json (buffix: patch 9ce56b3d…, CR record 6bf7fa63…, scope, default_code_allowed); `--control-role reviewed_bugfix` (alias approved_buffix_control kept). Reviewed buffix on the AL1 export PASSES; unreviewed is flagged unguarded_default_code; wrong review record -> control_authority. "How to add an entry" is in the README | R1, R2; tests |
| S27-3 relative --base (realpath) | PASS: `--base AL1=./al1_export/../al1_export` -> PASS (same signature as absolute); v1 exits 2 | R3, R4 |
| tests | 15 OK | logs/tests_v2.log |
| planted bugs | 7/7 caught, each by its intended test | logs/mutants_v2.log |

## Findings
- Portability defect in v1: tree-inventory keys used OS separators, so on Windows every applied patch looked like applied_path_mismatch. v2 uses POSIX keys.
- Sol's own suite on the PC: v1 13/47 FAIL; v2 2/47 FAIL. The remaining two are fixture CRLF writes against an LF patch (git apply rightly rejects them).
- 1 of Sol's 11 buildcompare tests fails on v2 by design: its fixture prints 308972 and the default pins are now AL1.
- AL1 + buffix box build is bench-identical to AL1 at all 5 depths.

## Note
An empty directory `opus_round1/sol_S27fix/old_attempt_check` exists in the worktree (untracked, not in git), left in place.

## Left / UNVERIFIED
- --build-compare fresh-build mode not run on the PC (its recipe audit expects the Linux canonical recipe).
- v2 on Linux not run (Sol's suite in CI): UNVERIFIED.
- Use --empty-history for already-known patches (the buffix is in the bundled history).

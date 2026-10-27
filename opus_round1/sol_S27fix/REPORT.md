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
  On the PC a second one fails too, for v1 and v2 alike: `test_realistic_recipe_root_normalization_and_strict_flag_controls`
  (Windows-only, see the Linux follow-up).
- AL1 + buffix box build is bench-identical to AL1 at all 5 depths.

## Note
An empty directory `opus_round1/sol_S27fix/old_attempt_check` exists in the worktree (untracked, not in git), left in place.

## Left / UNVERIFIED
- --build-compare fresh-build mode not run on the PC (its recipe audit expects the Linux canonical recipe).
- v2 on Linux: **verified** on a GitHub ubuntu-24.04 runner, with Sol's suites (section below).
- Use --empty-history for already-known patches (the buffix is in the bundled history).

## Linux follow-up (added by the main session)
Workflow `opus-sol-s27fix-linux`, run 40522039382 on `ec65392d`, success. Script `ci_s27fix_linux.sh` (commits `b6fee151`,
`ec65392d`); logs in `logs/ci_linux_40522039382/`. Runner: ubuntu-24.04, Python 3.12.3, git 2.56.0, GNU patch 2.7.6.
Sol's v1 files and his two unchanged test suites come from `17aa0cae` (`git show`; sha256 in `sol_v1_sha256.log`); his
suites run against v2 through the same shim as on the PC (v2 tools under his v1 file names).

| suite | Linux result | PC result (`logs/sol_tests_on_pc/`) |
|---|---|---|
| v2 tests (`test_forge_sol_S27_v2_20261027.py`) | 15/15 OK | 15 OK |
| Sol's hygiene suite on v2 | 47 run, **0 failures** (3 skipped: his historical source controls are not supplied) | 2 failures (+3 skipped) |
| Sol's buildcompare suite on v2 | 11 run, 1 failure: `test_probe_rejects_file_replacement_during_protocol_capture` (by design) | 2 failures |

- **The two PC-only hygiene failures are Windows line endings.** `test_ifdef_off_build_option_is_allowed` and
  `test_safe_test_change_applies_and_preserves_input` fail on the PC with `git_apply_failed` (`git apply --check`
  exit 1 while GNU patch applies) and pass on Linux with the same v2 code. That matches the finding above: on Windows
  the fixtures are written in text mode (CRLF) against an LF patch.
- **The PC-only buildcompare failure is Windows paths, not line endings.**
  `test_realistic_recipe_root_normalization_and_strict_flag_controls` builds POSIX path strings (`/source/src/…`) and
  normalizes them against `Path('/source')`, which Windows renders as `\source`; v1 fails it the same way on the PC.
  It passes on Linux. So the earlier "the remaining failures are CRLF" was right for the hygiene suite only.
- **The by-design failure** reproduces on Linux exactly: Sol's fixture engine prints his dev-base d11 308972, v2's
  default pins are AL1 (S27-2), so the first d11 gate fails before the UCI capture whose file replacement the test
  expects to catch (the probe's pre- and post-probe sha256 are equal). The CI script requires exactly this failure
  list for each suite.
- **First attempt (run 40521425927) failed** on one v2 test: `test_probe_default_AL1_and_named_Lprime` raised
  `ValueError: Executable required`. The test's fixture engine was a plain file. On Windows `os.access(X_OK)` is true
  for any existing file, on Linux it needs the exec bit. Fix (`ec65392d`): the fixture is `chmod 0o755`. The tool's
  check itself is right. Logs kept in `logs/ci_linux_attempt1_40521425927/`.
- No Elo or speed claim.

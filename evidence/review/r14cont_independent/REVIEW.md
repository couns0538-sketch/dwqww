# Independent review of the R14 finish (branch opus-astra-r14-finish) and full-suite run

Reviewer: an independent agent session (reviewer role of D:\a14\AGENTS.md). It did not author any of the
reviewed changes and shares no state with the author's session. Everything below was checked directly on the PC;
no finding was taken over from the author's self-review. Started 2026-11-04 10:28 (PC clock, `date`).

Correction 2026-11-04 (owner's fix list item 5, added by Opus; the findings below are unchanged): reviewer agent started
by the owner's allowance, scope 7636122b..0883cee, not covering de1a1cd3 or the as-found tools. The commit de1a1cd3
(F-001 fix in three .ps1 files, F-013 opus_prod_separation.py, F-014 promote check, F-015, opus_inventory.py, the three
skills) and Astra's as-found tools and tests (r14_boundary*, r14_suite.py, Invoke-R14Suite.ps1, r14_qualification) were
not re-reviewed; "independent" above means only that the reviewer session did not author the reviewed changes within
that scope.

## Scope

- Repository D:\a14, branch opus-astra-r14-finish, HEAD 0883cee88df4cdc6c302f4879e56ca3ec86c256a, base
  7636122b71ff27a5b4b781b6775757f926f8fdc4; 14 commits (aa78a56 .. 0883cee).
- `git -C D:/a14 diff --name-status 7636122b HEAD`: 506 paths; 441 of them are bulk evidence under
  evidence/test_logs/ (committed "as found"), 6 under evidence/r14/, the remaining 59 are the tools, tests, records
  and documents listed in diffs/modified_files.diff and in bytes_check.out.
- Reviewed in depth: tools/opus_lowrun.py, opus_seal.py, opus_prod_separation.py, opus_ep.py, opus_boardstm_probe.py,
  opus_boardstm_triage.py, opus_guardband.py, opus_guardband_proof.py, opus_guardband_record.py,
  opus_promote_export.py, opus_silent_sweep.py, opus_pypi_hashes.py, opus_tools_md.py; the author's changes to
  tools/r14_overlap.py, tools/r14_qualification/qualify.py, tools/r14_boundary_run.py and tools/r14_segments.py
  (abort paths), tools/Setup-R14Runtime.ps1, tools/R14-OwnedJob.ps1; tests/test_opus_ep.py,
  tests/test_opus_boardstm_probe.py, tests/test_opus_boardstm_triage.py, the additions to tests/test_r14_overlap.py
  and tests/r14_qualification/test_qualification.py; the records sep/PROD_SEPARATION.json,
  sep/GUARDBAND_SEPARATION.json, sep/guardband01/{SPLIT.json,PROOF.json,DROPPED.tsv},
  sep/boardstm-probe01/{PROBE.json,SHARED.jsonl,TRIAGE_probe_only.json,TRIAGE_probe_only_ROWS.tsv},
  sep/segments-production02/MAPS_SEAL.json, sep/GAMES_SIDECAR_PROPOSAL.md, sep/RETRY_PLAN.md,
  evidence/r14/opus_telemetry.md, .gitignore, .gitattributes, PLAN.md (R14-cont), evidence/R14_OPEN_ISSUES.md.
- Files committed "as found" from the PC (tools/r14_boundary*.py, tools/r14_suite.py, tools/Invoke-R14Suite.ps1,
  tests/test_r14_boundary*.py, tests/test_r14_suite.py, bulk evidence) were checked only for scratch files, secrets
  and names, plus whatever the suite run exposed; their content is Astra's and was not re-reviewed line by line.

## Method

- Read every diff (`git diff 7636122b HEAD -- <files>`, saved in diffs/modified_files.diff; the author-only part of
  the as-found files with `git diff c2e61fe HEAD -- ...`).
- Re-derived every number cited in the records from the underlying files (md5sum, line counts, grep of the scan
  REPORT.json files, arithmetic); scripts/bytes_check.py (CRLF / CR / NUL / non-ASCII / tabs per file, SHA256 of the
  runtime downloads against the new pins, shape of requirements-r14-hashes.txt).
- Ran the suite three times through D:\a14\tools\opus_lowrun.py --mask 0x4 (Idle, CPU 2, GPU hidden) with the
  prescribed environment (see "Full suite"), plus the single probes listed under each finding.
- Every computation went through opus_lowrun.py --mask 0x4; one process at a time; nothing outside
  D:\a14\evidence\review\r14cont_independent\ and D:\a14\evidence\test_logs\r14\full-suite-r14cont01\ was written;
  no git state was changed.
- Name scan (vendor / model-company names, case-insensitive) over the 59 non-bulk changed files, the bulk evidence and
  the skill files: no hit. Secrets scan (key / token / password / private-key patterns) over all 506 changed paths:
  no hit. Scratch paths: no `tmp/` directory is committed; see F-012 for the committed pytest basetemp folders.

## Full suite "inherited plus R14"

Log folder: D:\a14\evidence\test_logs\r14\full-suite-r14cont01\ (command.ps1 = the exact command, timing.txt,
output.log). Environment for every run: TEMP=TMP=D:\a14\tmp, PYTEST_DISABLE_PLUGIN_AUTOLOAD=1,
OMP/OPENBLAS/MKL_NUM_THREADS=1; free RAM before the first run 20.5 GB of 31.6 GB.

| run | command | result | duration | output.log md5 |
|---|---|---|---|---|
| 1 (as prescribed) | pytest D:\a14\astra_r8\datafilter\tests D:\a14\tests -q -p no:cacheprovider --basetemp ...\tmp | **interrupted at collection: 10 errors, 0 tests run**, exit 2 | 10:30:19-10:30:21 (1.17 s pytest) | 5e29b6281dc5a8b18eb305d93a44ccb2 |
| 2 (triage: same + --continue-on-collection-errors) | run2-continue-on-collection-errors\ | 48 failed, 452 passed, 30 skipped, 555 errors, 119 subtests passed, exit 1 | 10:33:19-10:34:42 (82.97 s) | cea1c863645375f42c9059fd981498f8 |
| 3 (triage: the R14 scope the runtime can collect) | run3-r14-scope\ = every D:\a14\tests\test_*.py + tests\r14_native + tests\r14_qualification | **8 failed, 323 passed, 67 subtests passed**, exit 1 | 10:37:02-10:38:07 (64.44 s) | 371de062db01a986b7c7e30b8b0db081 |

The R13 reference (D:\a13\evidence\test_logs\full-suite06: 603 passed, 60 subtests) ran D:\a13\tests (6 files) with
the D:\a11 runtime that has torch. That scope does not exist in D:\a14 and that runtime is not the R14 runtime, so
"603 + 60" cannot be reproduced here and must not be cited for this branch.

### Triage of run 1 (why the prescribed command cannot run in D:\a14 with the R14 runtime)

All three causes are pre-existing at 7636122b (none of the files involved is in the branch diff:
`git diff --stat 7636122b HEAD -- tools/r14_native tests/r14_native tests/data tests/data2 tools/data tools/data2 astra_r8 runtime` is empty):

1. `ModuleNotFoundError: No module named 'torch'` - the R14 runtime (D:\a14\runtime\python, requirements-r14-hashes.txt)
   has no torch by design (AGENTS.md: independent runtime, no protected imports). astra_r8\datafilter\tests\conftest.py
   has a session-wide autouse fixture that imports npt_adapter -> torch, so every datafilter test errors at setup
   (545 of the 555 errors in run 2) and two modules error at collection.
2. Module-name collision `filter_positions`: astra_r8\datafilter\filter_positions.py is imported first (datafilter
   conftest inserts its folder in sys.path); tools\data2\convert_dataset.py then does `from filter_positions import
   disagreement`, which only tools\data\filter_positions.py defines -> 8 tests\data2 modules error at collection and
   every tests\data\test_filter_positions.py test fails with `module 'filter_positions' has no attribute 'run'`.
3. Test-module basename collision (no __init__.py, pytest "prepend" import mode): tests\data2\test_converter.py vs
   astra_r8\datafilter\tests\test_converter.py ("import file mismatch").

Run 2's other failures are of the same kind: tests\data\test_package_results.py (case-only directory names 'A'/'a'
on NTFS), tests\data2\test_external_dependency_policy.py / test_roundtrip_policy.py (child process cannot import
external_tool_policy under the R14 runtime). None is caused by the R14-finish changes.

### Run 3 failures (R14 scope) - triage

| test | cause | verdict |
|---|---|---|
| tests\test_r14_runtime_setup.py::test_unset_caller_environment_is_restored | **caused by the branch** - see F-001 | regression |
| tests\test_r14_runtime_setup.py::test_live_refusal_stops_only_owned_process_tree[guard] | timing: the fixture guard fires after one 500 ms poll, before the Idle child on CPU 2 wrote child.json (parent.json shows the expected "Fixture resource refusal" and restored env) | environmental, see F-006 |
| tests\test_r14_suite.py::test_real_pytest_receipts_are_exact_and_fixture_scoped[False] | as-found runner (c2e61fe; the author's only edit is the F-001 line); its expectation passed=3/failed=1 for the runner fixture does not match pytest 9.2's built-in subtests (a test with a failed subtest is itself counted failed: 2 passed / 2 failed; run2 ...\tmp\test_real_pytest_receipts_are_0\run\output.log); fails in runs 2 and 3 | pre-existing, see F-003 |
| tests\test_r14_suite.py (3: real_pytest_receipts[True], supervisor_stops...[deadline], [log_cap]) | `Invoke-R14Suite.ps1:43 ... CPU admission refused` (PercentProcessorTime > 70 on the CPU the test picks = cpu_affinity()[0] = CPU 2, which the reviewer's own pytest process occupies under the launcher); passed in run 2 | environmental (shared CPU 2), see F-003 |
| tests\r14_native\test_native.py (2) | as-found native tests against tools\r14_native\build\chain_native.exe (default EXE, not the accepted r03 exe): consecutive-digit FEN answered UNREACHABLE instead of UNKNOWN; no reply within 2 s under Idle on CPU 2 | pre-existing, see F-005 |

All new and changed tests of the branch passed in run 3: tests\test_opus_ep.py, test_opus_boardstm_probe.py,
test_opus_boardstm_triage.py, test_r14_overlap.py (incl. the three listing tests), r14_qualification
(incl. the three fixture-guard tests), test_r14_boundary*.py.

## Findings

### F-001 BLOCKER - tools/Setup-R14Runtime.ps1:195, tools/R14-OwnedJob.ps1:154 and tools/Invoke-R14Suite.ps1:147: the new environment restore sets unset variables to "" instead of removing them

What is wrong: the commit 17db812 ("no silent error swallowing") replaced
`Remove-Item -LiteralPath ('Env:'+$key) -ErrorAction SilentlyContinue` by
`[Environment]::SetEnvironmentVariable($key,$null,'Process')`. Under pwsh (7.6.8 on this PC) `$null` is passed to the
.NET string parameter as an empty string and the variable is **not** deleted: after the script every caller variable
that was unset before (TEMP, TMP, PYTHONNOUSERSITE, PYTHONDONTWRITEBYTECODE, CUDA_VISIBLE_DEVICES,
HIP_VISIBLE_DEVICES, OMP_NUM_THREADS, OPENBLAS_NUM_THREADS, MKL_NUM_THREADS, PIP_CACHE_DIR, ...) exists with value "".
For a caller that ran with CUDA_VISIBLE_DEVICES unset this leaves CUDA_VISIBLE_DEVICES="" behind, and the selected
R14 suite test that guards exactly this contract now fails. The same replacement sits in R14-OwnedJob.ps1:154 (compile
environment of the owned-job helper) and in Invoke-R14Suite.ps1:147 (the suite runner's compile-environment restore;
this one-line change is the author's only edit to the as-found runner, commit 17db812).

Evidence:
- run 3 output.log lines 15187-15205 (run 2) / the same test in run 3:
  `assert parent['env'] == dict.fromkeys(KEYS)` -> `{'MKL_NUM_THREADS': ''} != {'MKL_NUM_THREADS': None}` (all ten keys).
- scripts/env_restore_probe.ps1 run through opus_lowrun (env_restore_probe.out):
  `after SetEnvironmentVariable(null): env:A=[] isnull=False Test-Path=True dotnet=[] dotnet_isnull=False`
  `after Remove-Item Env: env:B=[] isnull=True Test-Path=False`
  `after SetEnvironmentVariable(NullString): env:C=[] isnull=True Test-Path=False` (pwsh 7.6.8).
- `git diff 7636122b HEAD -- tools/Setup-R14Runtime.ps1 tools/R14-OwnedJob.ps1` (diffs/modified_files.diff lines 327-339, 411-416)
  and `git diff c2e61fe HEAD -- tools/Invoke-R14Suite.ps1` (line 147 only); `grep -n 'SetEnvironmentVariable(.*\$null'`
  gives exactly the three lines named in the title.
- The author's last recorded run of tests\test_r14_runtime_setup.py predates the change (launcher receipts of
  2026-11-03 13:03-13:18; the change is 2026-11-04 10:01), so the self-review could not have seen it.

Proposed minimal fix (all three files; `$key` in Setup-R14Runtime.ps1, `$name` in the other two; keeps the author's
intent of no -ErrorAction SilentlyContinue):
```
-            else { [Environment]::SetEnvironmentVariable($key,$null,'Process') }
+            else { [Environment]::SetEnvironmentVariable($key,[NullString]::Value,'Process') }
```
(or `elseif (Test-Path -LiteralPath ('Env:'+$key)) { Remove-Item -LiteralPath ('Env:'+$key) }`). Re-run
tests\test_r14_runtime_setup.py afterwards; test_unset_caller_environment_is_restored must pass.

### F-002 SHOULD - sep/PROD_SEPARATION.json (status_by_check.position_overlap_four_field), tools/opus_prod_separation.py:63, sep/GAMES_SIDECAR_PROPOSAL.md: reference to a file that does not exist, while the probe-only triage already shows the four-field "PASS" to be an EP artefact

What is wrong: the record says `"position_overlap_four_field": "PASS (en-passant normalisation not yet settled; see
BOARDSTM_TRIAGE.json)"`; the proposal cites `sep/BOARDSTM_TRIAGE.json` for 4,070 / 3,514 keys. No such file exists
(`ls D:/a14/sep/BOARDSTM_TRIAGE.json` -> No such file). The triage that exists is
sep/boardstm-probe01/TRIAGE_probe_only.json (09:51, probe listing only, not yet cross-checked against the r14_overlap
listing of production04): with legal-capture-only EP normalisation the 4-field key is shared -
`normalised_4field_recount: shared_keys 4088, train_rows 4118, holdout_rows 4090` (plus 8 real_ep_diff keys where only
one side allows a legal capture). PROD_SEPARATION.json (09:36) and the proposal (09:55) point to a record that is still
to be produced; a reader of HEAD cannot follow the reference. The overall verdict (FAIL on board+stm) is not affected.
The author's uncommitted working-tree version of opus_prod_separation.py (see "Working tree at review time") folds a
COMPLETE sep\BOARDSTM_TRIAGE.json in once it exists, which will close this finding when the cross-checked triage lands.

Evidence: `grep -n BOARDSTM_TRIAGE D:/a14/sep/PROD_SEPARATION.json D:/a14/sep/GAMES_SIDECAR_PROPOSAL.md
D:/a14/tools/opus_prod_separation.py`; TRIAGE_probe_only.json `normalised_4field_recount` block; key sums re-derived:
4070+8+3532 = 7610 keys, 4100+8+3592 = 7700 train rows, 4072+8+3532 = 7612 holdout rows, ROWS.tsv 15,313 lines
= 1 + 7700 + 7612.

Proposed minimal fix: until sep\BOARDSTM_TRIAGE.json exists, point the reference at the record that does
(opus_prod_separation.py, then re-run it so the record is regenerated, not typed):
```
-        'position_overlap_four_field': 'PASS (en-passant normalisation not yet settled; see BOARDSTM_TRIAGE.json)',
+        'position_overlap_four_field': 'PASS on the raw EP field only; pending the cross-checked triage '
+                                       '(probe-only triage sep/boardstm-probe01/TRIAGE_probe_only.json: 4,088 keys '
+                                       'shared after legal-capture-only EP normalisation)',
```
and in GAMES_SIDECAR_PROPOSAL.md cite `sep/boardstm-probe01/TRIAGE_probe_only.json` (or mark the BOARDSTM_TRIAGE.json
reference as "to be written from the production04 listing").

### F-003 SHOULD - tests/test_r14_suite.py:204 / tools/r14_suite.py / tools/Invoke-R14Suite.ps1 (as found, c2e61fe; author's edit = F-001 line 147 only): the selected-suite runner fails its own test in the R14 runtime

What is wrong: test_real_pytest_receipts_are_exact_and_fixture_scoped[False] expects the runner fixture to count
`passed=3, failed=1, skipped=1, error=1`; with pytest 9.2.0 (built-in subtests, no pytest-subtests plugin in the R14
runtime) the fixture's test_subcases is counted failed itself, so the runner reports passed=2 / failed=2 (inner log:
run2 ...\test_real_pytest_receipts_are_0\run\output.log, "3 failed, 2 passed, 1 skipped, 1 error, 1 subtests passed").
It fails in both runs. The three other test_r14_suite failures of run 3 ([True], [deadline], [log_cap]) are
`Invoke-R14Suite.ps1:43 CPU admission refused` (the test selects cpu_affinity()[0] = CPU 2, the launcher's own CPU, and
the runner refuses when that CPU is above 70 %); they passed in run 2 and are an artefact of running the suite on the
same single CPU. R14_SUITE_CONFIG_PIN_MILESTONE.md already states "the runner is still UNVERIFIED"; nothing in the
final report may claim a selected-suite pass from this runner until the subtest expectation is aligned with the
runtime (and the runner tests are run from a CPU other than the one they admit).

Evidence: run3 output.log FAILED lines 218-221 and the failure blocks; run2 lines 15233-15282.
Proposed minimal fix: not in the author's scope (as-found Astra files); record in R14_OPEN_ISSUES.md that the runner
test expects plugin-style subtest counts, or make the fixture expectation runtime-aware
(`dict(passed=2, failed=2, skipped=1, error=1, not_run=0)` under pytest >= 9 with built-in subtests).

### F-004 SHOULD - PLAN.md "R14-cont" / final report: the "full suite" as prescribed cannot run in this tree

What is wrong: the prescribed scope `astra_r8\datafilter\tests + tests` stops at collection in D:\a14 with the R14
runtime (see triage above). The final report must cite the scope that actually runs (run 3: 331 tests, 67 subtests,
8 failures triaged above) and must not carry over "603 passed, 60 subtests" from D:\a13.
Proposed minimal fix: in FINAL_REPORT.md / PLAN.md Job 4, state the executed scope, the three structural reasons and the
run-3 totals.

### F-005 NIT - tests/r14_native/test_native.py (as found, unchanged): two deterministic/timing failures against chain_native.exe

`test_consecutive_fen_digits_are_invalid`: `'UNREACHABLE' != 'UNKNOWN'` for the FEN `4k3/8/8/8/8/8/8/4K111 w - - 0 1`
(the native exe rejects it as unreachable instead of unknown); `test_interactive_reply_before_eof`: no reply within 2 s.
The test's default EXE is tools\r14_native\build\chain_native.exe (R14_NATIVE_EXE env overrides), not the accepted
chain_native_r03.exe that the runner pins. Pre-existing; the branch does not touch tools/r14_native or tests/r14_native.
Re-run of the file alone (rerun-single-files\native.log): `2 failed, 13 passed, 18 subtests passed in 3.60s` - the same
two, so both are reproducible, not one-off timing.
Proposed minimal fix: none in this branch; note it in R14_OPEN_ISSUES.md (run the native tests with
R14_NATIVE_EXE=...chain_native_r03.exe and decide whether UNKNOWN or UNREACHABLE is the contract for malformed FENs).

### F-006 NIT - tests/test_r14_runtime_setup.py::test_live_refusal_stops_only_owned_process_tree[guard]: timing-sensitive under the Idle CPU-2 launcher

The fixture refuses after `-FixtureFailGuardAfter 1` poll (500 ms); under Idle on a single shared CPU the probe child
(python + psutil import) had not written child.json yet -> FileNotFoundError. parent.json shows the correct
"Fixture resource refusal" and the fully restored sentinel environment, so the contract itself held. Not caused by the
branch (the guard path is untouched). Re-run of the file alone through the same launcher
(full-suite-r14cont01\rerun-single-files\runtime_setup.log, 10:47:40): `2 failed, 6 passed in 17.62s` - the same two
tests, so under the Idle CPU-2 launcher the [guard] case is reproducible, and F-001 is deterministic.

### F-007 NIT - PLAN.md:131: "appended 2026-11-04 09:2x Vienna" is not a clock reading

The repository rule is to take times from the clock, never to estimate; the commit that added the section is
aa78a56 2026-11-04 09:24:54 (git log). Fix: write "09:24".

### F-008 NIT - evidence/R14_OPEN_ISSUES.md:13: "followed by100k-path" (missing space in the added line)

### F-009 NIT - tools/opus_guardband_proof.py:18-21: docstring says it writes GUARDBAND_SEPARATION.json

The proof wrote sep/guardband01/PROOF.json (its --out); GUARDBAND_SEPARATION.json is produced by
opus_guardband_record.py. Fix the docstring (`--out D:/a14/sep/guardband01/PROOF.json`; "Writes the proof record").

### F-010 NIT - tools/opus_boardstm_probe.py:113,128-129: the EP census key `none` is never incremented

Rows with EP "-" are not passed to census_add, so `none` is always 0 while `ep_rows` counts only rows with an EP
square; the field suggests a count it does not hold. Fix: drop the key or count the "-" rows.

### F-011 NIT - tools/opus_boardstm_triage.py:207: --rows is written with mode 'w' (overwrites), --out with 'x'

Fix: `Path(a.rows).open('x', ...)` for symmetry with the other records.

### F-012 NIT - bulk evidence: committed pytest basetemp scratch folders

evidence/test_logs/r14/boundary/pytest_green02, pytest_red02..04 and evidence/test_logs/r14/qc/launcher-cap-green01/pytest
hold per-test tmp_path contents (fixture sources, .bin receipts, three *.bin.part files, harness.ps1). They are
reproducible fixture scratch, not evidence; the new .gitignore rule covers only `**/tmp/`. No secret, no name, no
production data was found in them (grep), so this is cosmetic: consider `evidence/test_logs/**/pytest_*/` in .gitignore
and keeping output.log only.

### F-013 SHOULD - tools/opus_prod_separation.py:26-35,53,118: the fail-closed pins are `assert` statements

Every md5 pin, completeness check and count check of the record generator is an `assert`; under `python -O` they
vanish and the record would be written from unverified inputs. The tool is run with `-I -B` today, so the record on
the branch is correct (every pin re-verified by this review), but a fail-closed generator must not depend on the
interpreter flag. Fix: replace each `assert cond, msg` by `if not cond: raise SystemExit(msg)` (or a helper `need()`).

### F-014 SHOULD - tools/opus_promote_export.py:43-46: the owner-only promotion does not check the audit counters

It refuses unless `scoped_checks == 'PASS'`, `problems` is empty and the SPLIT/staged md5s are unchanged, but it
ignores `audit_failure_counters_zero` (position / game / state mismatch counters of the npt-data-holdout-check audit)
and the PROOF.json md5 recorded in GUARDBAND_SEPARATION.json. A proof whose own audit counted overlaps would still be
promotable. Fix:
```
     if proof.get('scoped_checks') != 'PASS' or proof.get('problems'):
         sys.exit('refusing: the proof\'s scoped checks are not PASS')
+    if proof.get('audit_failure_counters_zero') is not True:
+        sys.exit('refusing: the audit failure counters of the proof are not all zero')
```

### F-015 NIT - tests/r14_qualification/test_qualification.py:265-273 (new test_no_production_launcher_passes_fixture): scans tools\*.ps1/*.py/*.bat/*.cmd at the top level only

`tools.glob(pattern)` does not look into tools\r14_qualification or other sub-folders, so a launcher placed there
would pass the test. Fix: `tools.rglob(pattern)` (excluding r14_native\build).

### F-016 NIT - tools/opus_silent_sweep.py: `contextlib.suppress(...)` and `except ...: return` are outside its definition

The sweep finds except bodies of only pass / ... / continue and the four PowerShell patterns. Silent swallowing via
`with contextlib.suppress(...)`, `except: return None` or `-ErrorAction Ignore` on a per-cmdlet `-EA` alias is not
reported. The committed sweep results (evidence/r14/opus_silent_sweep_r14_range.json: 42 scripts, 0 findings) are
correct for the stated definition; the definition should be stated as such in the Job 4 note.

### F-017 NIT - D:\a14\TOOLS.md has no entry for the R14-finish tools yet

`opus_tools_md.py --check` -> `tools md5 check FAIL: 11 tools, 11 mismatches` (every entry `TOOLS.md None`). Expected
at this point (the section is to be appended in Job 4 / by the main session), recorded so that the final check is not
forgotten.

## Record and number cross-checks (all PASS unless stated)

- sep/PROD_SEPARATION.json vs sep/overlap-production03/REPORT.json (md5 1607d19e2b66dbe3512d0997942523c4, as cited):
  board_stm FAIL 7,610 keys / 7,700 train rows / 7,612 holdout rows / 7,700 candidates / 0 collisions; four_field 0;
  304,999,573 train rows; 16,388,575 holdout rows (= 10,000,000 + 6,388,575). Match.
- sep/PROD_SEPARATION.json vs sep/segments-production02/REPORT.json (md5 fcb488f8c726326e013f648e1d202760, status
  UNVERIFIED): REACHABLE 16,294,792 + UNKNOWN 104,569 + UNREACHABLE 189,211 = 16,588,572 = sum of the six reasons
  (14 + 36,457 + 16,294,792 + 68,112 + 67,730 + 121,467); UNKNOWN = node_limit + gap_exceeds_k; UNREACHABLE =
  exhaustive_no_path + nonpositive_ply_gap + result_mismatch; segment_count 293,783 / range_count 293,784; scanned rows
  100,000 + 10,000,000 + 6,388,575 + 100,000. Match. Two train/holdout seams, both UNREACHABLE. Match.
- MAPS_SEAL.json md5 9b708a8994edc0f87ad8283c783440bb as cited; `opus_seal.py verify-seal` -> PASS, 25 files, 0 problems
  (maps_seal_verify.out).
- Probe (PROBE.json, md5 ef049b82dce36eeb92e8434467612af6 as cited by the triage): 7,610 / 7,700 / 7,612 / 0
  collisions; SHARED.jsonl 7,610 lines, md5 ea9d1e3024daf1fe0a3e70d11207e36b as cited by PROBE.json, TRIAGE and SPLIT.
  The probe is a genuinely independent implementation (raw-prefix hash index in RAM + exact resolution) and reproduces
  r14_overlap's production counts exactly.
- Triage (TRIAGE_probe_only.json): keys 4,070 + 8 + 3,532 = 7,610; key reasons 4,070 + 8 + 3,514 + 18 = 7,610; pairs
  4,120 + 8 + 3,574 = 7,702; raw_ep_patterns sum to the same per class; rows per class 7,700 / 7,612; per holdout file
  4,685 + 2,927 = 7,612; per piece count sums 4,070 / 3,532 / 8; ROWS.tsv md5 ec05042753b0f4466e36dfc0a148c064 as cited.
- Guard band (SPLIT.json md5 f2304604a07ceab3d8baca0da3661a26, PROOF.json md5 04da3cfa633aceeccd89dda67edf6837,
  DROPPED.tsv md5 b134521039739137e02d59e2eb7f4fd5, all as cited by PROOF.json / GUARDBAND_SEPARATION.json):
  999,921 rows = 987,194 train + 9,951 val + 2,776 dropped; dropped by reason 5 + 7 + 47 + 2,685 + 32 = 2,776;
  DROPPED.tsv = header + 2,776 lines; row ids are 0-based (line = row_id + 1), so val = rows 989,931..999,920 =
  9,990 - 7 - 32 = 9,951 and train = 989,931 - 5 - 47 - 2,685 = 987,194; audit rows 997,145 + 10,000,000 + 6,388,575 =
  17,385,720 unknown_game_id_rows; training_rows 997,145 = train + val. All match.
- Tool md5s cited in the records equal the files on disk: opus_guardband.py bf2afb3d..., opus_guardband_proof.py
  37319c6e..., opus_boardstm_probe.py ab989d17..., opus_ep.py 1b142bc9..., opus_boardstm_triage.py 11fdf601...,
  audit_exports.py a9e291fb... (md5sum).
- r14_scan.guard_selection semantics (tools/r14_scan.py:150-172): `row <= boundary` is the left side; opus_guardband
  passes ids i+1 with boundary = cut, so the left endpoint (index cut-1, id cut) is on the left side - correct. The
  proof re-derives the components and the ply distances independently (min 11 / 9 > K = 8).
- Setup-R14Runtime.ps1 pins: python-3.12.10-embed-amd64.zip and get-pip.py on disk match both the old MD5 and the new
  SHA256 pins; requirements-r14-hashes.txt: 13 lines, every one `name==version --hash=sha256:<64 hex>`; the bootstrap
  wheels folder (runtime\downloads\wheels) does not exist here, so the new --no-index bootstrap path has not been
  exercised on this PC (the runtime predates the change) - stated, not verified.
- Line endings: every new tool, test and record is LF-only (bytes_check.out: 0 CRLF, 0 CR, 0 NUL, 0 non-ASCII);
  .gitattributes / .gitignore are CRLF files as before; the two as-found progress.jsonl files carry CRLF.
- opus_lowrun.py: child read-back `affinity [2] nice 64 cuda -1 hip -1`; `--mask 0x0` and a missing program are refused
  (exit 1); `--help` of all ten CLI tools exits 0 (help_*.txt); opus_promote_export.py without
  --confirm-owner-decision refuses with exit 1.
- `opus_seal.py verify-report` on sep/guardband01/PROOF.json (4 entries incl. the C:\a14x audit files),
  sep/GUARDBAND_SEPARATION.json (8), sep/PROD_SEPARATION.json (3), sep/boardstm-probe01/TRIAGE_probe_only.json (2):
  all PASS, 0 problems (proof_verify_report.out).

## Checked, no issue found

- tools/opus_lowrun.py: checked - pins itself (Idle + mask, both read back, exit 78 on failure), child inherits; GPU
  hidden via CUDA/HIP_VISIBLE_DEVICES=-1; exit code passthrough.
- tools/opus_seal.py: checked - verify-report requires md5 (+bytes) of every {path, md5} object and, with --dir, the exact
  file set; seal refuses an output inside the sealed dir and an existing file; verify-seal needs bytes+md5+sha256 of
  every file; empty entry lists are FAIL.
- tools/opus_ep.py: checked - own move generation for the EP legality test (adjacent capturer, pin/check after the
  capture); invalid EP squares fail closed (ValueError in normalize_*); python-chess only in the --oracle self-check and
  in the tests; the 11 + 4 test cases include pins, discovered checks, edge files and a production row.
- tools/opus_boardstm_probe.py: checked - md5 of every consumed byte vs the pin, size/mtime unchanged, bad rows counted,
  deadline / RAM / RSS / disk guards; hash hits resolved by exact key; any exception -> INCOMPLETE + exit 2; refuses an
  existing --out and an --out outside D:\a14.
- tools/opus_boardstm_triage.py: checked - fail-closed on invalid EP, identical 4-field pairs, listing disagreement and
  wrong totals (--expect required); classes and recount re-derived above.
- tools/opus_guardband.py: checked - md5-pinned inputs, row/label/map consistency, contiguous-order check, cut only at
  an UNREACHABLE link, strict ply increase in both cut components, guard rows via r14_scan.guard_selection, every drop
  with a reason, staged rows outside D:\a14, SPLIT.json/DROPPED.tsv with 'x'.
- tools/opus_guardband_proof.py: checked - independent re-read of rows, labels, maps and holdouts; accounting / payload /
  three-key holdout / train-val / chain / audit; scoped PASS needs all five and no problems; audit at best UNVERIFIED
  with null game IDs; bad holdout rows make the holdout check FAIL.
- tools/opus_guardband_record.py: checked - numbers copied from SPLIT/PROOF (none typed); verdict via
  r14_scan.final_verdict(authenticated=False, ...) which cannot yield PASS; export not built.
- tools/opus_silent_sweep.py, opus_pypi_hashes.py, opus_tools_md.py: checked (see F-016, F-017 for scope notes).
- tools/r14_overlap.py listing: checked - per-key full row listing, global cap per side/kind, listing withheld (None,
  listing_complete false) instead of truncated, published only when the listed counts equal the audit counts and every
  shared key has rows on both sides; the three new tests cover full listing, cap and the empty case.
- tools/r14_qualification/qualify.py fixture guard: checked - resolve() both sides, refuses D:\a14\sep and anything
  below it before any write (test asserts the target does not exist afterwards).
- tools/r14_boundary_run.py and tools/r14_segments.py abort(): checked - the only author change replaces `pass` by a
  stderr message; both modules import sys; the abort still closes every handle.
- tools/Setup-R14Runtime.ps1: checked apart from F-001 - SHA256 required (regex) for every download, MD5 kept where it
  existed, build-wheel pins must match the hashed requirements line, pip install with --require-hashes.
- tools/R14-OwnedJob.ps1: see F-001 (same construct).
- tools/Invoke-R14Suite.ps1: checked - the author's only change since the as-found commit is line 147 (F-001); the
  rest (CPU admission at line 43, PYTEST_* stripping, pinned -c configuration, r03 identity before/after, exact file
  coverage) is Astra's as-found code and was exercised only through its own tests (F-003).
- tests/test_opus_*.py, tests/test_r14_overlap.py additions, tests/r14_qualification/test_qualification.py additions:
  checked - all pass in run 3; fixture-based, no production path touched.
- .gitignore: checked - ignores evidence/test_logs/**/tmp/ and sep/segments-production02/maps/ (sealed by
  MAPS_SEAL.json, verified). .gitattributes: checked - tools/opus_* and tests/test_opus_*.py -text.
- sep/GAMES_SIDECAR_PROPOSAL.md, sep/RETRY_PLAN.md, evidence/r14/opus_telemetry.md: checked - text only, no change to
  the writer; one stale reference (F-002); no names, no secrets.
- Licence: no third-party code copied into the tools; python-chess (chess 1.11.2 in the R14 runtime) is imported only in
  tests/test_opus_ep.py and in opus_ep.py's --oracle self-check.

## Side effects of the suite runs (not written by the reviewer, but caused by running the prescribed tests)

- The inherited launcher tests (tests\test_r14_launcher.py and friends) write their receipts into the evidence tree:
  eight new untracked folders under D:\a14\evidence\test_logs\r14\launchers\ (cap-548e3ddf0788, cap-83ac47533c0e,
  cap-895f3c0de304, cap-b16ed1ce2945, launcher-64c24c48f53b, launcher-b6925f1af4f1, pipes-4f8602e4dc36,
  pipes-58051cc7fd79; `git status --short`, timestamps 10:33-10:47). They are test artefacts of runs 2, 3 and the
  re-run; the reviewer did not delete them (no deletes allowed) - the main session decides whether to commit or drop them.
- 142 fixture folders/files were left in D:\a14\tmp (astra_a1_* unit fixtures that the inherited tests retain on
  failure, cpu_runtime_*.json of the datafilter conftest). TEMP/TMP pointed there as prescribed.
- pytest basetemp folders live inside full-suite-r14cont01\ (gitignored by the branch's `**/tmp/` rule).

## Working tree at review time

`git status` also shows two files modified in the working tree relative to HEAD that the reviewer did not touch:
tools/opus_prod_separation.py (+22 lines: folds a future sep\BOARDSTM_TRIAGE.json into the record when it exists and is
COMPLETE for 7,610 / 7,700 / 7,612) and evidence/r14/opus_telemetry.md (+1 row), plus untracked
evidence/r14/health-ps51-*.json, evidence/r14/overlap-production04.log, sep/overlap-production04/ and
tools/opus_inventory.py (never committed, not in the reviewed range). These are the author's concurrent, uncommitted
edits; the review covers HEAD 0883cee. The fold-in addresses the substance of F-002 once the production04 listing scan
and a full triage produce sep\BOARDSTM_TRIAGE.json; until then the committed record and GAMES_SIDECAR_PROPOSAL.md point
to a file that does not exist, and the committed four-field "PASS" wording stands.

## Skills written (additional task; new folders only)

| folder | md5 of SKILL.md | lines |
|---|---|---|
| D:\a14\.agents\skills\boardstm-overlap-triage\SKILL.md | 9f93465b3bb1bbfaf4fa207930bb890b | 78 |
| D:\a14\.agents\skills\guardband-split-proof\SKILL.md | b4b1629697057cc23a15c64dda2db0be | 72 |
| D:\a14\.agents\skills\r14-finish-helpers\SKILL.md | 3edfb1a6d982a0c8b803dde9ab26c52f | 45 |

Every command in them was checked on 2026-11-04 (--help of every tool, the test files in run 3, verify-seal /
verify-report, the launcher child probe, the promotion refusal); the production probe/split/proof invocations are the
documented usage of the tools whose records were re-verified, not re-executed. Frontmatter follows
npt-data-holdout-check\SKILL.md; LF only; no vendor or model-company name (grep).

## Deliverables and times

- This file: D:\a14\evidence\review\r14cont_independent\REVIEW.md; helpers in scripts\ (bytes_check.py,
  env_restore_probe.ps1, lowrun_child_probe.py); outputs bytes_check.out, env_restore_probe.out, maps_seal_verify.out,
  proof_verify_report.out, help_*.txt; diffs\modified_files.diff.
- Suite logs: D:\a14\evidence\test_logs\r14\full-suite-r14cont01\output.log (md5 5e29b6281dc5a8b18eb305d93a44ccb2,
  run 1 as prescribed: collection errors), run2-continue-on-collection-errors\output.log (cea1c863645375f42c9059fd981498f8),
  run3-r14-scope\output.log (371de062db01a986b7c7e30b8b0db081), rerun-single-files\.
- Review window: 10:28 - 10:57 PC clock (`date`), all three suite runs, the single-file re-runs and the advisor-driven
  corrections (Invoke-R14Suite.ps1 line 147 added to F-001, F-003 re-triaged from the failure blocks, source line
  numbers) included.
- Not verified: the new --no-index bootstrap-wheel path of Setup-R14Runtime.ps1 (never executed on this PC, no network
  use by the reviewer); opus_pypi_hashes.py against PyPI (network); the as-found Astra tools r14_boundary*.py,
  r14_suite.py, Invoke-R14Suite.ps1 line by line; the behaviour of the prescribed full-suite command at 7636122b
  (no checkout allowed - the structural causes were shown to be outside the branch diff instead).

# S34 Gate-manifest schema validator — DONE (v2 validator, fixtures, tests, real-file runs)

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2, item 9. Branch `opus-sol-S34` = `d4f4312` + `0d99f02` cherry-picked
(`2f98a3b3`) + `4119ab75` (evidence) + `0c016ffc` (PARTIAL report) + this commit. Tool job: no engine change, no CI
run (`[skip ci]`). Nothing on the PC was written: the live manifest was read through a copy (sha256 unchanged).

**Acceptance (QA):** "validates the real forge_gates.json (BOM, dict, `option.K=V` list) with 0 false errors".
Tool-job default acceptance: unit tests + fixtures pass, one real-file run, README.

| item | result | evidence |
|---|---|---|
| reads the real file: UTF-8 BOM, dict root, `option.K=V` lists | **PASS** | live copy loads; 128 gates; every options entry checked against the driver pattern (`logs/step4_real_file_runs.log`) |
| 0 false errors on the real file | **PASS**: default profile reports exactly 13 findings, all `OPENINGS_START_DUPLICATE`, all real (below) | `logs/step4_real_file_runs.log`, `logs/step4_real_file_runs.tar.gz` (4,640 B: the four JSON reports) |
| unit tests | **PASS 31/31** (Sol's 21 ported + 10 v2), real-file tests included | `logs/step5_v2_tests.log` |
| fixtures | **PASS**: 51 bad manifests, one planted defect each, each rejected with exactly its code, an explaining message and a pointer; all 51 messages distinct; 2 valid manifests (plain and BOM) pass | `bad_manifests_v2/index.json`, test `test_planted_bad_manifests_are_isolated_and_messages_are_distinct`; generator deterministic (`logs/step3_fixtures.log`) |
| planted validator bugs | **PASS 10/10 caught**; the unmutated copy passes | `logs/step6_mutation_check.log` |
| README | **PASS** | `README.md` |

## What was wrong with Sol's v1 on the real file (from the PARTIAL step, `logs/step1-3`)
- 123 `UNSUPPORTED_FIELD` findings (`ag_vs_lock` 65, `ag_rebuilt_on` 29, `ag_prev` 29) were false: these are
  annotation fields that `autonomy/autopromote.ps1` writes and reads; the gate driver never reads them and they form
  no write path.
- In his default (strict) profile, 246 "missing field" findings were false for the deployed driver, which defaults
  `tc`, `concurrency`, `openings_start` and `sprt`. His `--driver-defaults` profile cited a proposed driver copy
  (r7 candidate, sha256 `02069e05…`), not the deployed one.
- His 29 bad fixtures were never pushed, and his snapshot test pointed at a `/workspace` path.

## v2 (new file; Sol's v1 unchanged)
`forge_sol_S34_validate_manifest_v2.py`:
- **Default profile = the deployed driver** `C:\Users\Administrator\grok-pc\forge_push\autorestart\forge_queue.ps1`
  (sha256 `636b6cca…`, read on the PC 2026-10-27): absent `tc` → 10+0.1 (line 89), `concurrency` → 5 (line 90),
  `openings_start` → 1 (line 92), `sprt` → elo0 0, elo1 10, nonreg false (lines 94-97). Present values are never
  filled. `--strict` keeps Sol's profile; `--driver-defaults` is an alias of the default. The report carries the
  driver's sha256 and line numbers.
- **Annotation fields** `ag_vs_lock`, `ag_rebuilt_on`, `ag_prev`, `ag_rebase_of`, `ag_rebase_exempt24`,
  `ag_void_rerun_of`, `ag_void_cause`, `pooled` (autopromote.ps1 sha256 `896663b0…`, lines 187, 266, 408, 439,
  452-453) are allowed and type-checked. `ag_prev` must be an object with only `exe`, `sha256`, `prebench`,
  `base_override`, `srand`, `ag_vs_lock` (the live file has 27 + 2 such objects); its `srand` is not part of the
  uniqueness rule.
- **Options**: a list of strings fully matching the driver's own pattern `^option\.([^=]+)=(.*)$` (line 216), no
  control characters, no name twice (case-insensitive), none of Threads/Hash/OwnBook (the driver sets them, line 350).
- **Base options**: non-empty `options` in `base` / `base_override` are reported (`BASE_OPTIONS_IGNORED`): the driver
  passes no manifest options to the base engine (line 351).
- **Case-only duplicate keys** are rejected at load time (`JSON_CASE_DUPLICATE_KEY`): the driver reads the file with
  PowerShell `ConvertFrom-Json` (line 37), whose property names are case-insensitive.

## Real-file runs (`logs/step4_real_file_runs.log`)
| file | sha256 | default profile | `--strict` |
|---|---|---|---|
| live `forge_gates.json` (read-only copy) | `09c995b6…` (source unchanged before/after) | 13: `OPENINGS_START_DUPLICATE` | 246: TC_REQUIRED 128, SPRT_REQUIRED 104, OPENINGS_START_REQUIRED 14 |
| lock-archive snapshot `6_gate/pc_autonomy_scripts_copy/autonomy_20261025/forge_gates.json` | `9c7abdb4…` | 13: `OPENINGS_START_DUPLICATE` | 240: TC_REQUIRED 122, SPRT_REQUIRED 104, OPENINGS_START_REQUIRED 14 (= Sol's numbers) |

**The 13 findings are real, not false errors.** They are the legacy ep10 gates 13-25 (`/gates/1`…`/gates/14`,
tags `gate13_h256_e12_vs_ep10` … `gate25_packe_evalstore_vs_ep10`, 8 of them `DROPPED_post_lock_h256`). They
predate the `openings_start` field, so the driver started all of them (and gate 12) at opening 1; their srands
differ (20261028…20261109). Openings and colours therefore repeated across those gates. They are finished
history, so the finding is informational for them, and the same rule protects new gates. Nothing in the
manifest was changed (the validator never writes).

## Reproduce
```
python -I -B make_bad_manifests_v2.py <new dir>          # fixtures (committed copy in bad_manifests_v2/)
S34_SNAPSHOT=<lock archive>/6_gate/pc_autonomy_scripts_copy/autonomy_20261025/forge_gates.json \
S34_LIVE=<read-only copy of the live forge_gates.json> python -I -B test_validate_manifest_v2.py
python -I -B mutation_check_v2.py <new scratch dir>
python -I -B forge_sol_S34_validate_manifest_v2.py <copy of forge_gates.json> [--strict]
```
Python used: Windows CPython 3.14.7 (standard library only; the code needs 3.10+). Machine exclusive: n/a (no
timed run).

## Left / UNVERIFIED
- Not tested against other driver versions (only the deployed `636b6cca…`).
- The tool is not wired into the driver or any PC script (that would change the PC's gate pipeline; QA's call).
- Sol's v1 files were not re-shipped; their hashes are cited above.

## Files
`REPORT.md`, `README.md`, `IDEA_SOURCE.md`, `forge_sol_S34_validate_manifest_v2.py`, `make_bad_manifests_v2.py`,
`test_validate_manifest_v2.py`, `mutation_check_v2.py`, `bad_manifests_v2/` (53 fixtures + `index.json`),
`logs/step1_live_manifest_copy.log`, `logs/step2_sol_v1_on_live.log`, `logs/step3_sol_v1_tests_asis.log`,
`logs/step3_fixtures.log`, `logs/step4_real_file_runs.log`, `logs/step4_real_file_runs.tar.gz` (4,640 B),
`logs/step5_v2_tests.log`, `logs/step6_mutation_check.log`, `FILES.txt`, `SHA256SUMS`.

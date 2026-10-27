# S34 Gate-manifest schema validator — PARTIAL (evidence only; v2 validator not written yet)

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2, item 9. Branch `opus-sol-S34` = `d4f4312` + `0d99f02` cherry-picked
(`2f98a3b3`) + `4119ab75` (evidence) + this report. Tool job; no engine change, no CI run (`[skip ci]`).

## Done
1. **Found Sol's code.** It is in
   `17aa0cae:validation/forge_sol_pack31_20261025/forge_sol_all_jobs_recovery_20261026/forge_sol_S34_prepared_NOT_ORDERED_DELIVERED_20261026/`:
   validator sha256 `edd2247a…` and 21 tests sha256 `b3e6ebcd…`, matching his receipt.
   - The checkpoint folder named in SOL_LEFTOVERS (`…/metadata/workspace/S34`) holds only his reports.
   - **The 29 bad fixtures (`bad_manifests/` plus index) were never pushed.** Only the names `deep_json`,
     `oversized_integer` and `unknown_write_field` survive in his logs.
2. **Located the real manifest and copied it read-only.** The source is
   `C:\Users\Administrator\grok-pc\forge_push\autorestart\forge_gates.json`; the copy is in
   `F:\opus_scratch\sol_s34\real\` (sha256 `09c995b6…` before and after, 537,671 B).
   - **Format:** UTF-8 BOM; a dict root with `comment`, `base`, `gates`, `lock`; 128 gates.
   - **Options:** every one of the 128 `options` entries is an `option.K=V` string.
   - **Defaults in use:** no gate has a `tc` field; `sprt` appears in 24 gates and `openings_start` in 114;
     concurrency values are 5, 7 and 8.
   - **Clean checks:** srands are unique; explicit `openings_start` values are unique (20001..366001); tags are
     unique, case-folded; all 4 `confirm_of` entries resolve; every sha256 has 64 hex characters; no option
     repeats or touches Threads, Hash or OwnBook; every base options list is empty.
   - (`logs/step1_live_manifest_copy.log`)
3. **Ran Sol's v1 unmodified on the live copy** (`logs/step2_sol_v1_on_live.log`):
   - default (strict) profile: 369 findings: TC_REQUIRED 128, SPRT_REQUIRED 104, OPENINGS_START_REQUIRED 14,
     UNSUPPORTED_FIELD 123;
   - `--driver-defaults`: 136 findings: OPENINGS_START_DUPLICATE 13, UNSUPPORTED_FIELD 123.

   Classification:
   - **The 123 UNSUPPORTED_FIELD findings are false.** They are for `ag_vs_lock` (65), `ag_rebuilt_on` (29) and
     `ag_prev` (29). `autonomy/autopromote.ps1` (sha256 `896663b0…`) writes and reads these fields; the gate
     driver never reads them, and they never form a path.
   - **The 246 strict "missing field" findings are false** under the deployed driver `forge_queue.ps1` (sha256
     `636b6cca…`): line 89: absent `tc` → `10+0.1`; line 90: absent `concurrency` → 5; line 92: absent
     `openings_start` → 1; lines 94-97: absent `sprt` → elo0 0, elo1 10, nonreg false.
   - **The 13 duplicate starts are real.** The 14 legacy ep10 gates 12-25 (chain runners 8-21; gates 18-25 are
     DROPPED_post_lock_h256) predate the `openings_start` field, so the driver gives them all start 1. Their
     srands differ (20261027..20261109).
4. **Ran Sol's 21 tests as-is:** 17 pass. The 4 that fail all lack inputs: the missing `bad_manifests/` folder, and
   his `/workspace` snapshot path (`logs/step3_sol_v1_tests_asis.log`).

## Left (resume steps)
1. Write `forge_sol_S34_validate_manifest_v2.py` from Sol's v1 (his file untouched): default profile = the
   deployed driver's defaults (record the driver sha256 and line numbers); `--strict` keeps Sol's profile
   (`--driver-defaults` = alias of the default); allow the annotation fields `ag_vs_lock`, `ag_rebuilt_on`,
   `ag_prev`, `pooled` (autopromote.ps1 lines 160-164, 187, 264, 407, 439, 452-453); check `ag_prev` as an object
   with only `exe`, `sha256`, `prebench`, `base_override`, `srand`, `ag_vs_lock` (its `srand` not counted in the
   uniqueness check); check gate `options` (a list; every entry fully matches the driver's regex
   `option\.([^=]+)=(.*)` (line 216) with no control characters; no repeated name; no Threads/Hash/OwnBook, which
   the driver sets itself, line 350); report non-empty `options` in base and base_override (silently ignored by
   the driver, line 351); flag JSON keys that differ only in case (PowerShell's ConvertFrom-Json is
   case-insensitive).
2. Rebuild the fixtures with a generator `make_bad_manifests.py` (at least 29, one defect each, an index with
   file, code, explanation and profile).
3. Port Sol's 21 tests (snapshot path from env `S34_SNAPSHOT`: 240 findings strict, 13 default), add v2 tests
   (`S34_LIVE` = live copy: only the 13 explained legacy duplicate starts in the default profile, 246 with
   `--strict`) and a planted-bug check.
4. Real-file runs (live copy default and `--strict`, snapshot), README.md, FILES, SHA256SUMS, push.

Acceptance target: on the live file, the default profile reports only the 13 explained legacy duplicate starts,
with 0 false errors.

## UNVERIFIED
Everything in "Left".

## Files
`REPORT.md`, `FILES.txt`, `logs/step1_live_manifest_copy.log`, `logs/step2_sol_v1_on_live.log`,
`logs/step3_sol_v1_tests_asis.log`, `SHA256SUMS`. No .tar.gz archives.

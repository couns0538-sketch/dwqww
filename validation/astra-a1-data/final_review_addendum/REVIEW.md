# Artifact recovery addendum review

Reviewed 2026-10-30T04:54:05Z to 2026-10-30T04:58:51Z (4.8 minutes). Combined with the original 19.6-minute review, actual review sessions total 24.3 minutes; the gap between sessions is excluded.

Only `docs/ASTRA_A1_ARTIFACTS.md` was changed. Its original draft is retained in `ASTRA_A1_ARTIFACTS.before.md`. The original final-review document and all 72 evidence-file hashes still match their unchanged manifest.

Three recovery usability gaps were corrected: direct-download users no longer depend on the chunk branch to define `$Archive`; SHA256 is now compared with the final publication receipt before extraction instead of only displayed; and the full-record verifier writes its receipt outside the sealed folder. The document also explicitly rejects existing extraction paths, accounts for retained chunks in disk-space planning, explains shared hardlink storage, and links the audit usage document through its actual repository path.

Frozen transport source SHA256 remains `0113b0335fba26c525f4cff69f906d59d7a25d800c772340a50e23357fb7a366`. Its saved normal and optimized test logs each report 15 passing tests. This addendum did not rerun those suites. The reviewer executed the documented read-only `verify` CLI against the existing original binary fixture: PASS, 262147 bytes, SHA256 `287f4096ec84f5d539f715c9c77e294b900bad6c43e2665eaaa139c54ca5ea7c`. CLI output and empty stderr are retained here.

The packaging map confirms the extraction/checker path `completed/full10m`. A second source reviewer found no additional PowerShell argument/path issue. PowerShell is unavailable in this environment, so Windows execution remains UNVERIFIED. Publication receipt URLs, final archive sizes and final archive hashes are still pending and must replace the draft's clearly identified placeholders after actual publication. The code's placeholder check deliberately fails before extraction.

Actual commands: `cat docs/ASTRA_A1_ARTIFACTS.md`; `sha256sum validation/astra-a1-data/transport_parts.py`; source/test reads; `rg` on `release_preparation/mapping_results.json`; reads of `transport_tests/summary.json`, `qualified.stderr`, and `qualified_optimized.stderr`; `command -v pwsh` (unavailable); `PYTHONDONTWRITEBYTECODE=1 python3 validation/astra-a1-data/transport_parts.py verify validation/astra-a1-data/transport_tests/cli_parts/transport_manifest.json`; final Python static path/order checks and preserved-evidence hash verification.

No native engine workload, engine/source implementation change, active-filter change, Git action or network publication was performed.

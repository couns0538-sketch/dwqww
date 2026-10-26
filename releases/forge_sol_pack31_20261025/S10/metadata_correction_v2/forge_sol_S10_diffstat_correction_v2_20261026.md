# S10 diffstat correction v2 — 2026-10-26

The sealed v1 aggregate incorrectly reported0 files for every patch because its generator counted only `diff --git` headers. The four unchanged patches use plain unified diff headers. This metadata defect does not alter any source patch, native result, archive, trial decision or engine baseline. V1 reports/generator/results and their original14-file sealed set remain intact.

|Patch|Verified files|Insertions|Deletions|
|---|---:|---:|---:|
|forge_sol_S10_singular_siblings_20261026.patch|6|66|0|
|forge_sol_S10_quiet_check_survival_20261026.patch|6|66|1|
|forge_sol_S10_improving_razor_20261026.patch|6|61|1|
|forge_sol_S10_capture_history_lmp_20261026.patch|6|63|0|

Four red controls reject the original0-file metadata against actual Git numstat output. Four green comparisons pass for v2. Non-diffstat JSON fields compare exactly with v1, including202 CTest executions,1200 legal WAC positions, all original result/archive/source hashes, rejection decisions and unverified checks. Git commands are read-only; original stdout/stderr, per-file counts and tool/patch hashes are retained in the verification JSON. No native process was run.

Corrected machine results SHA256 `3e90dee2013a5ca8966409e790fbde91f4c2dc210d2c0936f610418e14921d61`. Corrected report SHA256 `b1e2658c9f4720c96979f047a10bf79b2f4210f63ed38390ea502da99de24046`.

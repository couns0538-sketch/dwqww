# IDEA_SOURCE — S34 gate-manifest validator v2

- **Sol's S34 v1** (`17aa0cae:validation/forge_sol_pack31_20261025/forge_sol_all_jobs_recovery_20261026/forge_sol_S34_prepared_NOT_ORDERED_DELIVERED_20261026/`,
  validator sha256 `edd2247a…`, tests `b3e6ebcd…`): closed schema, parser hardening (duplicate keys, non-standard
  numbers, depth/size/integer limits), write-path rules for tags, strict and driver-default profiles. v2 is a new
  file built on it; his files are unchanged.
- **The deployed gate driver** `forge_queue.ps1` (sha256 `636b6cca…`, read-only): defaults (lines 89-97), option
  pattern (line 216), engine arguments (lines 350-351), `ConvertFrom-Json` read (line 37).
- **`autonomy/autopromote.ps1`** (sha256 `896663b0…`, read-only): the annotation fields it writes and reads.
- General: JSON Schema-style closed objects; mutation testing to show the tests catch planted bugs. No code was
  copied from any third-party project.

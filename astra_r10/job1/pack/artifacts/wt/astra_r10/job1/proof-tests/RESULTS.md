# Exact identity / optional T4 contract regression — UNPROVEN

Scope: orchestration fixtures only. No engine, build, timing, or native qualification was executed.

Changed the branch-local `forge-lock-proof-set` skill copied from the installed skill. New optional `identity_mode` resolves to `behavior-changing` by default or explicitly `exact`. Exact ON requires every pin, active count >0, matching options and the existing binary/source/net binding. Only `stages.smoke_t4={"skip_reason":"reason"}` may skip a stage; it remains UNVERIFIED, preserves an explicit nonexecution receipt and allows sanitizer execution. Overall status stays UNVERIFIED. Actual failures retain fail-fast behavior.

## Tests and retained attempts

- `red01`: PowerShell 5.1 wrapper treated unittest stderr as a terminating native error; wrapper attempt retained. No proof accepted from this wrapper attempt.
- `red02`: native Python exit 1, 14 fixtures, 6 failures and 3 errors reproduced the old ON-difference and unconditional T4 authorization behavior. Logs retained.
- `green01`: native Python exit 0, all 14 fixtures PASS after the implementation change. Includes inactive ON, missing depth, one changed pin, option mismatch, default behavior-changing behavior, skipped T4 followed by sanitizer, invalid skips/mode, and fail-fast after an earlier OFF-pin failure.
- All wrapper execution used own Idle process, affinity mask 12, D-only TEMP/TMP, bytecode disabled. Synthetic files and failed attempts remain preserved.

Command: `powershell -NoProfile -File D:\a10\wt\astra_r10\job1\proof-tests\run_tests.ps1 -Tag <new-tag>`.

## Review and limits

Independent child-review dispatch was unavailable because the team thread limit was reached. Main-agent focused review is still required before native use. Structured self-review checked input/binary verification before a skip, final evidence hashing, default mode preservation, error propagation and overall UNVERIFIED status.

Kit v2.3 emits `-Wmissing-profile` and rejects bad profile logs after compilation; the runner still requires compiler `-Werror` flags. This compatibility issue is deliberately unresolved and is not bypassed by the new modes. Native adapters must report actual command witnesses. Standard ON metrics bind build_a only; the R10 native adapter must additionally execute/retain ON on build_b as required by Couns.

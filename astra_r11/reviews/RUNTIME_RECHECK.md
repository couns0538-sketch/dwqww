# Focused independent runtime recheck

Reviewer: `trace_design`. Date: 2026-11-02. Scope: corrections to the two P1 findings, linked-contract P2 and fixture-count item in `RUNTIME_REVIEW.md`. Verdict: **those findings are closed by static inspection of the frozen candidate**. No new blocking defect was found in the corrected scope. This is not a native runtime, synthetic-test, data-provenance or training qualification.

## Exact reviewed identities

Each digest was independently recomputed during this recheck and matched the supplied freeze.

| File | SHA256 |
| --- | --- |
| `astra_r11/runtime/launch_runtime.ps1` | `e7ed3d16d3ff3f1c791cd789c5d993b104843cf4d9efdcc106a2292539a1f917` |
| `astra_r11/runtime/verify_bootstrap.ps1` | `a1dab78a0da5ee5c3627e0a2ed048e53640978af33a578e72b45524b4aeb1c7b` |
| `astra_r11/runtime/run_fixtures.py` | `a2ddcba47dded37410cd1004cc0c1575cad47be1bdeeac352332305d2ec3f741` |
| `astra_r11/runtime/STATIC_CHECKS.json` | `029cc7f0d9d496d32dfcbd11ac821f697a0e4f033a8d9a05141cd2daf51d690b` |
| `skills/grok-pc-safe-run/references/launcher-contract.md` | `51db6eaac6d80bd14fc043248b59180e4d072b2aa1ee7c3c532f5f4cce4624b2` |

## Closure evidence

1. **Preparation/refusal paths:** the launch wrapper now implements `Owned-Path`, which performs lexical owned-root/alias/control-file rejection before root-to-leaf reparse inspection. The job root, manifest and binding are checked before existence tests or reads. Directory creation revalidates its target. `New-Json` validates its own path before `File.Open`; the admission receipt also receives an explicit path check. `Hash` and dot-sourced inputs pass through the same policy. This closes the previously unguarded preparation and blocked-admission accesses.

2. **Bootstrap identity before native startup:** `Get-BootstrapSnapshot` hashes the two bootstrap archives against literal official SHA256 pins, streams each relevant archive member's digest, compares its extracted length/type/hash, rejects unsafe/duplicate/symlink entries and checks exact extracted-file census without following reparses. `Prepare` captures the complete result. `Run` verifies it before admission/native launch; the launch-finally path verifies it again after exit. The verifier itself belongs to the complete runtime candidate snapshot. This closes the missing DLL/stdlib binding for the first fixture launch. Ordinary concurrent mutation remains outside an OS sandbox; the implementation does not claim otherwise.

3. **Linked contract:** the schema and policy paragraphs now require `D:/a11` for the working directory, output directory and all write paths. The remaining `D:/a10` occurrence is its explicit prohibition. The contract also describes wrapper admission and archive-bound bootstrap verification accurately.

4. **Fixture completeness:** success now requires collected counts exactly `[26, 4]`, `testsRun == 30`, no skips and a successful unittest result. Static definition enumeration independently found 26 gameprovenance test methods and four runtime-policy methods. Native test discovery remains unrun.

## Verification limits and next action

This reviewer read sources, counted test definitions and hashed the five files above. No Python process, fixture test, archive assembler, native preflight or original 73-test suite was executed. `STATIC_CHECKS.json` records the author's PowerShell evidence: 17 path/storage checks, lane predicates, five guarded-writer refusals, and 1,791 archive-bound files totaling 44,598,362 bytes. Those checks were not rerun by this reviewer.

Root may now prepare and inspect a fresh `fixtures01` manifest/binding with this frozen candidate, then exercise normal Run admission. An occupied lane must retain its refusal receipt and launch no child. A refusal establishes safety behavior only; it does not turn any unrun native or provenance result into PASS. Any subsequent candidate change requires a fresh binding and the relevant recheck.

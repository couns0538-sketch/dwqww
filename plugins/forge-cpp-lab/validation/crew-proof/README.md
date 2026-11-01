# Lock-proof helper validation

The runner's native adapters are not supplied as counterfeit Forge recipes. Tests use explicitly labelled fixture adapters in new temporary directories. They exercise real child processes and original file bytes; they do not compile Forge, run Windows, consume real PGO data or execute actual engine sanitizer suites. `evidence_scope=fixture` remains in the emitted proof and the gate handover helper rejects that actual report.

25 normal and 25 optimized tests passed. `result.json` binds source/test hashes, commands and logs. Initial missing-helper failures, a malformed-result bug, four build-flag false-PASS regressions, three profile-use fallback/downgrade false-PASS regressions and a sanitizer-error-log false-PASS regression are retained alongside their fixes. No logs were rewritten to erase failed approaches.

Coverage includes correct nine-row output, two independently emitted final binary files, differing binary bytes, OFF mismatch, inactive/unchanged ON, sanitizer startup and error messages, failed native adapter exit, boolean counts, missing profile files, missing/contradictory use-phase LTO/FMA flags, final link-to-binary binding, later binary mutation, stage timeout stopping later work, malformed adapter receipts, pinned recipe mutation, four-thread host requirement, existing-output preservation and fixture-to-gate rejection.

The checker verifies adapter execution and declared witnesses. Independent review must still establish that native adapters actually invoke the intended compiler/engine/test commands, that source/import/profile dependencies are complete, and that smoke legality/sanitizer metrics correspond to original logs. Metadata alone is not native proof. Exact ON-difference is required here; bit-identical SIMD work is deliberately routed to its separate parity/qualification contract.

No actual engine qualification, Windows success, performance/Elo claim or production-PC activity occurred.

IDEA_SOURCE: user's proof-set contract, parent review of phase binding, existing immutable-evidence workflow; original code.

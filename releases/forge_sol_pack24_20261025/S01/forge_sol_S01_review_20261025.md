# S01 independent read-only review, 20261025

Verdict: no material issue found within the requested S01 follow-up scope.

Scope: exact follow-up patch only, plus its separate read-only pin-observation shell/Python helper. Prerequisite Job C patch SHA256 `4ac98f92d45f67fae8aaa8067fe28c0fca36662b3688013105f738245ee55805` is treated as the prerequisite, not resubmitted or reapproved here. No engine execution, Git operation, candidate edit, skill change, affinity change or host-limit change was performed by this reviewer.

- WAC known-outcome acceptance retains the same original case/expected-value identity, exact f6h5/661/d12 outcome and matching nonempty PV guard. Constants only centralize the recorded pin values. Added PIN_MISMATCH messages are side-effect-free diagnostics; they do not alter ordinary failure counting or suppress failures.
- Underpromotion retains original rook expectation and exactly the same documented alternative legal king move, matching PV, score>100 and d1 conditions. Added diagnostics print documented and observed move/score/depth/PV only after both accepted outcomes fail. The restricted rook-win/queen-stalemate assertions are unaffected.
- Old expected outcomes remain ordinary passes. Drift does not automatically change a pin. README requires a separate reviewed re-recording and preserves exact661 rather than changing it to a score floor.
- Patch paths are tests/tests.cpp and appended IDEA_SOURCE/README documentation only; no engine implementation or prerequisite patch content is resubmitted. The supplied latest patch-applicability record says clean dry-run/apply to both L+C and B+C and records engine inputs unchanged. This review inspected that record rather than independently applying the patch.
- Pin printer starts fresh processes, awaits uciok/readyok and bestmove, captures requested-depth score/PV, validates matching PV[0]/bestmove and successful child exit, and prints observed outcomes without writing pins. Optional --expect-lock turns pin mismatch into a nonzero result. Output is only a new requested folder; raw streams are base64-encoded with original byte counts/SHA256. Timeout paths report UNVERIFIED and unclosed PID rather than claiming native success or killing a process.
- The Python parser is suitable for this Forge source, which emits exact score info without UCI lowerbound/upperbound fields. The native L transcript already records the expected661 WAC and642 promotion outcomes; I did not execute or reproduce those observations.
- The earlier negative-control oracle's assumption that Move::none formats as0000 is not production behavior in this tree. Correcting the external expected diagnostic token to observed a1a1 does not warrant a production/test-patch change; retain the first failed oracle evidence.

Limits: this is source-contract review, not fresh full CTest, native B validation, new-network adoption, benchmark or strength acceptance. Final native controls/CTest and immutable publication require their own evidence.

Review UTC: 2026-10-25T09:07:02.959349+00:00

forge_sol_S01_pinmsg_20261025.patch SHA256 `48f125b7c0d211c46b47d62b421d571cb94769a9d349dac7baadfd2d110039cc`
forge_sol_S01_rerecord_pins_20261025.py SHA256 `d5e2b759fd7cac6b7442dd520fa625536c48e2249572309c10a4fdf2eed77ebc`
forge_sol_S01_rerecord_pins_20261025.sh SHA256 `4afbc80fec689300763347f781308425650f5d98bacd44117994e7d3c9d9227f`

## Final command-only addendum

Verified 2026-10-25T09:08:19.378423+00:00: final patch SHA256 `bddc961125a25c9d4331a8555b0304653f550c378c38fb480a1ba9b2ba92d528` differs from reviewed `48f125b7…` by exactly one README command line: explicit `bash /path/to/forge_sol_S01_rerecord_pins_20261025.sh` invocation. Every other patch byte, including test implementation and IDEA_SOURCE content, is unchanged. Both shell/Python helper SHA256 values still match the original review. No material issue; prior source-review verdict applies to this final hash. Native controls and full CTest remain independently evidenced; no new execution was performed by this reviewer.

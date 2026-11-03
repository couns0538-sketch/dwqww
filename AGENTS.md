# Astra R13 data QC

Follow PLAN.md and current user instructions. No subagents.
All writes under D:/a13, including subprocess caches and Git metadata.
Minimum free space on D: 50 GiB plus the next allocation; stop if below.
CPU only: one admitted worker at Idle priority and one native thread.
No engine-source changes, GPU use, training, relabel search or strength claims.
Do not access protected trainer/gate roots, F:/forge_push, handoff_v7, .nnue or engine locks.
Frozen external datasets are read-only. Never delete or rewrite original data.

Run full datafilter and R13 tests, preserve logs, then direct one-hour review/fixes.
Blocked inputs/resources/tests remain explicit; continue independent authorized work.
No game-separation PASS from inferred groups or missing population bindings.
Commit without skip-ci; push only astra-r13-dataqc without force.
Use external libraries only as dependencies; do not copy GPL engine/decoder code.

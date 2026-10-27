# S15 source-only implementation plan

Goal: prepare a bounded deterministic tool with exact51-parameter source accounting and a20-iteration fake-objective demonstration, while S11 parity remains exclusive.

- [ ] Write behavioral tests for exact source/range accounting, malformed definitions, projected integer probes/gradient sign, deterministic convergence, no overwrite, typed UCI support, paired outcome rejection and input hashes; observe parser RED first.
- [ ] Implement strict catalog/probe/update/demo and plan/observe orchestration, reusing the original owned PGN checker. No runtime process launch exists in the tool.
- [ ] Run the small Python-only test suite onCPU4/nice19, preserving RED/GREEN outputs in a new own /tmp directory. Run the20-iteration demo twice with seed20261027 and compare every output byte.
- [ ] Record every actual parameter/range, NetScale absence, source hashes, synthetic objective progression, exact later smoke/preflight command plan and all UNVERIFIED items. Freeze a source/evidence manifest for root review; do not publish/count S15 yet.

Review focus: unsupported source expressions must fail rather than disappear; integer probes must differ even at bounds; objective sign/nonfinite inputs must be checked; malformed or non-normal paired PGNs must never update; existing/source paths must not be overwritten. Native full CTest and a real smoke are intentionally NOT RUN under the current source-only grant.

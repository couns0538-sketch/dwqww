# opus_smp_layout — lockless TT (C++-memory-model valid) + worker cache-line fix, default OFF, on trial_w6

| item | value |
|---|---|
| branch | `opus-smp-layout-20261107`. Parent **P** = `7ce10a05` (= trial_w6 source; kit build = `4181a589…` byte for byte) |
| switch | compile-time `FORGE_SMP_LAYOUT` (default **0**). UCI `TtLockless` (check, default **false**, exists only at 1) |
| OFF build (0) | kit LTO+PGO pc1 = pc2 = **`4181a589…6b6fb0` = P = trial_w6**. No new UCI option. `g++ -E -P` identical for all 8 units |
| GATE build (1) | kit pc1 = pc2 = **`6c07563b8dfdeca2109c62e0d15df2877f62ca4cf084bc39c4f810c6bdecfe91`**. Runtime default = legacy striped-lock TT |
| what changes at 1 | (a) `TtLockless=true` selects a lockless TT: own typed storage, every concurrent access a relaxed `std::atomic_ref`, an XOR tag that rejects mixed K/D pairs, the same decisions as P (SPEC.md §3); (b) `Worker::nodes_` gets its own cache line, as measured by `tools/layout_probe.cpp` (SPEC.md §4) |
| classification | speed/correctness-only at Threads 1 (node-identical; see BENCH.md). Threads ≥ 2 is nondeterministic by nature, so it carries **no strength claim**: any Elo or NPS decision belongs to QA (SCALING_PLAN.md) |

## Evidence index (details in BENCH.md)
1. Identity: OFF = P byte for byte. Gate OFF and ON = pins, perft and kit identity. Full fens12k net on/off and warm-table identity at Threads 1 (BENCH §4).
2. Race/stress: CI TSan (release, ASan+UBSan, TSan) on the pushed commits, plus the TSan run of the real engine over UCI (tsan_extra.sh); native stress at Threads 1/4/8 (BENCH §3, §5). "Race proof" is never claimed.
3. Layout: P measured; gate measured (BENCH §2).
4. NPS: advisory only, on two physical cores (BENCH §6). Not scaling evidence, not Elo.

## Files
- SPEC.md (fixed before code), INVENTORY.md, BENCH.md, STATUS.md, IDEA_SOURCE.md, COMMANDS.md (EXECUTED / PREPARED-ONLY), SCALING_PLAN.md (PREPARED-ONLY), REVIEW_LOG.md, MD5SUMS, SHA256SUMS.
- `smp_layout_after_w6.patch`: engine sources only, `git diff 7ce10a05 <tip> -- include src`; applies to the trial_w6 source.
- `smp_layout_tests_ci.patch`: tests, CMake, CI.
- `tools/`: kit_build.ps1, the kit_v23 Idle copy, pp_identity.ps1, identity_check.ps1, uci_lifecycle_stress.ps1, liveness_check.ps1, nps_smoke.ps1, layout_probe.cpp, o2_uci_lib.ps1, run_pinned.ps1.
- `logs/`: compact logs, each bound to an exe sha256 or a commit.

## Handoff
READY FOR CODE REVIEW → QA once STATUS.md says so. Nothing is queued by this job.

# opus_smp_layout — lockless TT (valid under the C++ memory model) + worker cache-line fix, default OFF, on trial_w6

| item | value |
|---|---|
| branch | `opus-smp-layout-20261107`. Parent **P** = `7ce10a05` (trial_w6 source; kit build = `4181a589…` byte for byte). Final engine candidate: **`0599271bdf391243870370bfed05185f93022444`** |
| switch | compile-time `FORGE_SMP_LAYOUT` (default **0**). UCI `TtLockless` (check, default **false**; exists only at 1) |
| OFF build (0) | kit v2.3 LTO+PGO pc1 = pc2 = **`4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` = P = trial_w6**. No new UCI option. `g++ -E -P` identical for all 8 units |
| GATE build (1) | kit pc1 = pc2 = **`541e8b3d4333b99044ccafa7bcda82a1b5bf42a561eaf3b043b9871ed9faea1b`**. Runtime default = the legacy striped-lock TT |
| patch | `smp_layout_after_w6.patch` (engine only, +319/-0, md5 `dfa3d11de1255dd1b92e5e14218186f0`). Applied to a fresh P export it gives the final tree byte for byte |
| what changes at 1 | (a) `TtLockless=true`: a lockless TT with its own typed storage. Every concurrent access is a relaxed `std::atomic_ref`; an XOR tag rejects mixed K/D pairs; the decisions are exactly P's (SPEC.md §3). (b) `Worker::nodes_` on its own cache line (measured: SPEC §4, BENCH §2) |
| classification | **speed/correctness-only at Threads 1: node-identical**, including the full fens12k and warm-table identity. Threads ≥ 2 is nondeterministic by nature: **no strength or speed claim**. QA's quiet timing and SPRT policy decide (SCALING_PLAN.md) |

## Verdicts (details and logs in BENCH.md)
| question | verdict |
|---|---|
| OFF build identical to the parent | **PASS**: byte-identical (4181a589, two clean kit builds) |
| gate, `TtLockless=false`, node identity Threads 1 | **PASS**: pins net on/off, perft, kit identity, fens12k net on/off (12,000/12,000), warm table (1,000 FENs, 40 option changes) |
| gate, `TtLockless=true`, node identity Threads 1 | **PASS**: the same set; liveness shown (toggle = Clear Hash effect) |
| race: TSan (CI, Linux, g++-14) | **0 reports** on the executed paths in 4 runs, incl. the real engine over UCI at Threads 2/4 in both modes. **Not a race proof** |
| race: contention fixture | **0 incoherent hits in 2,165,459,456 probes (360,235,892 hits)** over 7 runs (5 native, 2 under TSan in CI); the gating positive control saw 0.46-2.46 M incoherent hits in every run |
| stress (native, CPUs 12-15, Threads 1/4/8) | **PASS**: 2 × 300 + 2 × 2,000 cycles; every bestmove legal; isready ≤ 39 ms while searching; exit 0 |
| ASan + UBSan (CI) | green, no report |
| layout | `nodes_` was sharing a line with `local_nodes_` and 6 other owner fields; now alone (+64 B per worker). Nothing else needed it |
| NPS | advisory only: the A/A copy moves by up to 5 %, so nothing resolvable. A weak hint of ~2-3 % cost for ON at Threads 1 (decode), worth QA's timing |
| review | R1 (fable, partially independent): no BLOCKER/MAJOR, 3 MINOR + 4 NIT, all MINOR fixed. The recheck could not run (reviewer unreachable), so it was replaced by SR1, a structured self-review **NOT independent** (REVIEW_LOG.md) |

## Files
- SPEC.md (fixed before code), INVENTORY.md, BENCH.md, STATUS.md, IDEA_SOURCE.md, COMMANDS.md (EXECUTED / PREPARED-ONLY), SCALING_PLAN.md (PREPARED-ONLY), REVIEW_LOG.md, MD5SUMS, SHA256SUMS.
- Patches: `smp_layout_after_w6.patch` (engine) and `smp_layout_tests_ci.patch` (tests, CMake, CI: md5 `7036a23b35db33a9846f2fff9555db4f` at 0599271; the CI hardening after it is in the branch).
- `tools/`: kit_build.ps1, kit_v23_idle_build_ltopgo.ps1, pp_identity.ps1, identity_check.ps1, liveness_check.ps1, uci_lifecycle_stress.ps1, nps_smoke.ps1, layout_probe.cpp, o2_uci_lib.ps1, run_pinned.ps1.
- `logs/`: parent, ci (4 runs), l3, l3b, live, stress, tests, layout, nps, review. Each log names its exe sha256 or commit.
- Skill: `skills/forge-smp-lockless-qualify/SKILL.md` (mirrored to `D:\grok-pc-data\dwqww\.claude\skills\`).

## Handoff
**READY FOR CODE REVIEW → QA** (engine candidate `0599271`, gate exe `541e8b3d`, OFF exe = `4181a589`). Nothing was queued by this job.
- QA: optional quiet native-core timing (SCALING_PLAN.md).
- For any strength question at Threads ≥ 2: QA's SPRT after Code Review.

# opus_smp_layout — lockless TT (valid under the C++ memory model) + worker cache-line fix, default OFF, on trial_w6

| item | value |
|---|---|
| branch | `opus-smp-layout-20261107`. Parent **P** = `7ce10a05` (trial_w6 source; kit build = `4181a589…` byte for byte). Engine candidate: **`e011a3e06e4c3bb305e09727d339812de7a03622`** ("enc5": `89cddf7` plus three comment lines from the final bug hunt; the same exes). It supersedes `a675c04` (enc4) and `0599271` (first hand-off); see "Since 0599271" below |
| switch | compile-time `FORGE_SMP_LAYOUT` (default **0**). UCI `TtLockless` (check, default **false**; exists only at 1) |
| OFF build (0) | kit v2.3 LTO+PGO pc1 = pc2 = **`4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` = P = trial_w6** (tags h0c/h0d for `89cddf7`, m0c for `e011a3e`). No new UCI option. `g++ -E -P` identical for all 8 units |
| GATE build (1) | kit pc1 = pc2 = **`2940fb0514dd2ef058d6512bf66659074f162293f7d31ccac23779c2e65762e5`** (tags h1c/h1d, the scratch-tree build g1c, and j1c / m1c from the comment-only commits up to `e011a3e`: five identical builds). Runtime default = the legacy striped-lock TT |
| patch | `smp_layout_after_w6.patch` (engine only, `7ce10a05..e011a3e`, +366/-0, md5 `88b0bb2a403962a2fbb2d996eaafc41d`). Applied to a fresh P export (`patch -p1 -F0`) and flipped, it gives the gate tree byte for byte |
| what changes at 1 | (a) `TtLockless=true`: a lockless TT with its own typed storage. Every concurrent access is a relaxed `std::atomic_ref`. A one-multiply tag rejects mixed K/D pairs, and the decisions are exactly P's (SPEC.md §3). (b) `Worker::nodes_` on its own cache line (measured: SPEC §4, BENCH §2) |
| classification | **speed/correctness-only at Threads 1: node-identical**, including the full fens12k and warm-table identity. Threads ≥ 2 is nondeterministic by nature: **no strength or speed claim**. QA's quiet timing and SPRT policy decide (SCALING_PLAN.md) |

## Since `0599271` (enc2-enc5, 2026-11-09 evening)
- `0599271` was qualified and handed off first; its evidence stays in BENCH §1-§7.
- A TT micro-benchmark (BENCH §8) then showed that its lockless encoding cost half of the TT throughput at Threads 1 (three multiplies per slot, all four slots decoded per probe).
- **enc4** (`a675c04`) keeps every decision and makes the encoding cheap:
  - a one-multiply multiply-shift tag over D (the move travels inside K);
  - decisions on the raw words, decoding only the returned slot (`std::bit_cast`, with layout asserts);
  - the eight loads kept in registers;
  - a raw-word store.
  - TT throughput at Threads 1, hot pool: 0.50 → 0.71-0.74 of the legacy owned path. At Threads 2/4: 1.5-1.6 → 2.1-2.3 × P's striped locks.
- **enc5** (`89cddf7`) = enc4 + one GCC attribute on the two lockless function definitions (SPEC 3.7).
  - Problem: QA's frozen PGO workload never runs `TtLockless=true`, so the kit compiled those functions as never executed: size-optimised and placed in cold code.
  - Fix: `optimize("profile-partial-training")` compiles them as normal `-O3` code again. This is codegen only (BENCH §11).
- **Tag strength** is exactly characterised (BENCH §9). Mixed pairs from same-position re-stores (small field differences) are never accepted, and the residual for unrelated data is about 2^-31 on average.

## Verdicts (details and logs in BENCH.md; §11-§12 for the candidate, §10 for `a675c04`)
| question | verdict |
|---|---|
| OFF build identical to the parent | **PASS**: byte-identical (4181a589, kit h0c = h0d) + `g++ -E -P` 8/8 identical |
| gate, `TtLockless=false`, node identity Threads 1 | **PASS**: kit identity, pins net on/off + perft, fens12k net on/off (12,000/12,000), warm table, Hash-1 replacement |
| gate, `TtLockless=true`, node identity Threads 1 | **PASS**: the same set plus deeper warm (200k nodes); liveness on the PC and **in CI** (toggle = Clear Hash effect) |
| race: TSan (CI, Linux, g++-14) | **0 reports** on the executed paths in every CI run of this branch (9 runs), each including the real engine over UCI at Threads 2/4 in both modes. Runs 42708220996 (`89cddf7`) and 42716501693 (final push, engine `e011a3e`) tested the candidate code. **Not a race proof** |
| race: contention fixture | 0 incoherent hits in every run (BENCH §6, §10, §11), each with a gating positive control that saw hundreds of thousands to millions of incoherent hits |
| stress (native, CPUs 12-15, Threads 1/4/8) | **PASS** (BENCH §11) |
| ASan + UBSan (CI) | green, no report; no new compiler warning (the same 6 pre-existing `-Wconversion` lines as the macro-0 build) |
| layout | `nodes_` was sharing a line with `local_nodes_` and 6 other owner fields; now alone (+64 B per worker). Nothing else needed it |
| tag strength | exact census: 0 collisions for every difference confined to depth/bound/pv/rule50, every single bit, and every small field difference (38.2 M). Score/eval-only: 1 delta (F47). Combined deltas: density 2^-31 (BENCH §9) |
| NPS | advisory only (A/A noise ±5 %): BENCH §7 and §10. A byte copy of an exe ran 6 % faster than its original file (a per-file effect), so exe-level differences of that size mean nothing here. The TT micro-benchmark (§8) measures the mechanism itself |
| review | **R1** (fable): 3 MINOR fixed. **SR1**: a self-review, NOT independent. **R2** = the fable bug hunt over `0599271`, `527a696`, `a675c04`, `89cddf7` and `b1a7fc6`: **no engine defect at any severity**; tooling/doc findings 1 MINOR + 9 NIT, all fixed. **FH** (final bug hunt, NOT independent): 3 stale comments fixed comment-only, exes unchanged (REVIEW_LOG.md, BENCH §12) |

## Files
- SPEC.md (fixed before code; §3 updated for enc2-enc5), INVENTORY.md, BENCH.md, STATUS.md, GATE_ENTRY.md (hand-off), IDEA_SOURCE.md, COMMANDS.md (EXECUTED / PREPARED-ONLY), SCALING_PLAN.md (PREPARED-ONLY), REVIEW_LOG.md, MD5SUMS, SHA256SUMS.
- Patches: `smp_layout_after_w6.patch` (engine, `7ce10a05..e011a3e`) and `smp_layout_tests_ci.patch` (tests, CMake, CI, `7ce10a05..` tip).
- `tools/`: kit_build.ps1, kit_v23_idle_build_ltopgo.ps1, pp_identity.ps1, identity_check.ps1, liveness_check.ps1, uci_lifecycle_stress.ps1, nps_smoke.ps1, layout_probe.cpp, tt_microbench.cpp, tag_scan.cpp, micro_table.py, test_log_sharing.ps1, o2_uci_lib.ps1, run_pinned.ps1. CI: `opus_round1/opus2_smp/{tsan_extra.sh,liveness_check.py}`.
- `logs/`: parent, ci, l3, l3b, live, stress, tests, layout, nps, review, bughunt, enc4, enc5. Each log names its exe sha256 or commit.
- Skill: `skills/forge-smp-lockless-qualify/SKILL.md` (mirrored to `D:\grok-pc-data\dwqww\.claude\skills\`).

## Handoff
**READY FOR CODE REVIEW → QA**: engine candidate `e011a3e`, gate exe `2940fb05`, OFF exe = `4181a589`. Nothing was queued by this job.
- QA: optional quiet native-core timing (SCALING_PLAN.md).
- For any strength question at Threads ≥ 2: QA's SPRT after Code Review.
- The enc4 → enc5 difference is the `FORGE_LOCKLESS_UNTRAINED_OPT` macro and its use on two function definitions in `src/search.cpp`. A port of enc4 (for example onto another lineage) gets enc5 by adding exactly that.

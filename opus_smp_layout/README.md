# opus_smp_layout — lockless TT (valid under the C++ memory model) + worker cache-line fix, default OFF, on trial_w6

| item | value |
|---|---|
| branch | `opus-smp-layout-20261107`. Parent **P** = `7ce10a05` (trial_w6 source; kit build = `4181a589…` byte for byte). Engine candidate: **`a675c04f4d2ea648dc32f3633c3e70cb2189bd08`** ("enc4"). It supersedes `0599271`; the reasons are in the "Since 0599271" section below |
| switch | compile-time `FORGE_SMP_LAYOUT` (default **0**). UCI `TtLockless` (check, default **false**; exists only at 1) |
| OFF build (0) | kit v2.3 LTO+PGO pc1 = pc2 = **`4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` = P = trial_w6** (tags f0c/f0d). No new UCI option. `g++ -E -P` identical for all 8 units |
| GATE build (1) | kit pc1 = pc2 = **`a4b57032294d9d9efe2742408bb0a56da970cd1146f15c360a1fe99aada2c54b`** (tags f1c/f1d). Runtime default = the legacy striped-lock TT |
| patch | `smp_layout_after_w6.patch` (engine only, +357/-0, md5 `83928636b7cfcce60544d24bbd36fe6b`). Applied to a fresh P export (`patch -p1 -F0`) and flipped, it gives the gate tree byte for byte |
| what changes at 1 | (a) `TtLockless=true`: a lockless TT with its own typed storage. Every concurrent access is a relaxed `std::atomic_ref`. A one-multiply tag rejects mixed K/D pairs, and the decisions are exactly P's (SPEC.md §3). (b) `Worker::nodes_` on its own cache line (measured: SPEC §4, BENCH §2) |
| classification | **speed/correctness-only at Threads 1: node-identical**, including the full fens12k and warm-table identity. Threads ≥ 2 is nondeterministic by nature: **no strength or speed claim**. QA's quiet timing and SPRT policy decide (SCALING_PLAN.md) |

## Since `0599271` (enc2-enc4, 2026-11-09 evening)
- `0599271` was qualified and handed off first; its evidence stays in BENCH §1-§7.
- A TT micro-benchmark (BENCH §8) then showed that its lockless encoding cost half of the TT throughput at Threads 1 (three multiplies per slot, all four slots decoded per probe).
- `a675c04` keeps every decision and makes the encoding cheap:
  - a one-multiply multiply-shift tag over D (the move travels inside K);
  - decisions on the raw words, decoding only the returned slot (`std::bit_cast`, with layout asserts);
  - the eight loads kept in registers;
  - a raw-word store.
- **TT throughput, Threads 1, hot pool** (X/L = lockless ÷ legacy): 0.50 → 0.71-0.74 of the legacy owned path.
- **TT throughput, Threads 2/4, hot pool:** 1.5-1.6 → 2.1-2.3 × P's striped locks.
- **Tag strength** is now exactly characterised (BENCH §9). Mixed pairs from same-position re-stores (small field differences) are never accepted, and the residual for unrelated data is about 2^-31 on average.
- The whole qualification set was repeated on `a675c04` (BENCH §10).

## Verdicts (details and logs in BENCH.md; §10 for `a675c04`)
| question | verdict |
|---|---|
| OFF build identical to the parent | **PASS**: byte-identical (4181a589, two clean kit builds f0c/f0d) + `g++ -E -P` 8/8 identical |
| gate, `TtLockless=false`, node identity Threads 1 | **PASS**: kit identity, pins net on/off + perft, fens12k net on/off, warm table, Hash-1 replacement (BENCH §10) |
| gate, `TtLockless=true`, node identity Threads 1 | **PASS**: the same set plus deeper warm (200k nodes); liveness on the PC and **in CI** (toggle = Clear Hash effect) |
| race: TSan (CI, Linux, g++-14) | **0 reports** on the executed paths in every CI run of this branch: 4 on `0599271`-era code, 1 on enc2, and the runs on the `a675c04` engine code (42697936926 and the follow-up). Each included the real engine over UCI at Threads 2/4 in both modes. **Not a race proof** |
| race: contention fixture | 0 incoherent hits in every run (BENCH §6, §10), each with a gating positive control that saw hundreds of thousands to millions of incoherent hits |
| stress (native, CPUs 12-15, Threads 1/4/8) | **PASS** (BENCH §10) |
| ASan + UBSan (CI) | green, no report |
| layout | `nodes_` was sharing a line with `local_nodes_` and 6 other owner fields; now alone (+64 B per worker). Nothing else needed it |
| tag strength | exact census: 0 collisions for every difference confined to depth/bound/pv/rule50, every single bit, and every small field difference (38.2 M). Score/eval-only: 1 delta (F47). Combined deltas: density 2^-31 (BENCH §9) |
| NPS | advisory only (A/A noise ±5 %): BENCH §7 (`0599271`) and §10. A byte copy of the new gate ran 6 % faster than its original file (a per-file effect), so exe-level differences of that size mean nothing here. The TT micro-benchmark (§8) measures the mechanism itself |
| review | R1 (fable): 3 MINOR fixed. SR1 self-review (NOT independent). R2 = the fable bug hunt over `0599271`, enc2 and enc4: no BLOCKER/MAJOR/MINOR; 6 NIT, all fixed (REVIEW_LOG.md) |

## Files
- SPEC.md (fixed before code; §3 updated for enc2-enc4), INVENTORY.md, BENCH.md, STATUS.md, GATE_ENTRY.md (hand-off), IDEA_SOURCE.md, COMMANDS.md (EXECUTED / PREPARED-ONLY), SCALING_PLAN.md (PREPARED-ONLY), REVIEW_LOG.md, MD5SUMS, SHA256SUMS.
- Patches: `smp_layout_after_w6.patch` (engine, `7ce10a05..a675c04`) and `smp_layout_tests_ci.patch` (tests, CMake, CI, `7ce10a05..` tip).
- `tools/`: kit_build.ps1, kit_v23_idle_build_ltopgo.ps1, pp_identity.ps1, identity_check.ps1, liveness_check.ps1, uci_lifecycle_stress.ps1, nps_smoke.ps1, layout_probe.cpp, tt_microbench.cpp, tag_scan.cpp, micro_table.py, o2_uci_lib.ps1, run_pinned.ps1. CI: `opus_round1/opus2_smp/{tsan_extra.sh,liveness_check.py}`.
- `logs/`: parent, ci, l3, l3b, live, stress, tests, layout, nps, review, bughunt, enc4. Each log names its exe sha256 or commit.
- Skill: `skills/forge-smp-lockless-qualify/SKILL.md` (mirrored to `D:\grok-pc-data\dwqww\.claude\skills\`).

## Handoff
**READY FOR CODE REVIEW → QA**: engine candidate `a675c04`, gate exe `a4b57032`, OFF exe = `4181a589`. Nothing was queued by this job.
- QA: optional quiet native-core timing (SCALING_PLAN.md).
- For any strength question at Threads ≥ 2: QA's SPRT after Code Review.

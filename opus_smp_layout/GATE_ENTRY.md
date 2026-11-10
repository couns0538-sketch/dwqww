# opus_smp_layout — GATE_ENTRY (hand-off note for Code Review → QA; NOT queued by this job)

## What to review and test
| item | value |
|---|---|
| engine candidate | branch `opus-smp-layout-20261107`, commit **`a675c04f4d2ea648dc32f3633c3e70cb2189bd08`** ("enc4"). Engine diff `7ce10a05..a675c04` = `smp_layout_after_w6.patch` (+357/-0, md5 `83928636b7cfcce60544d24bbd36fe6b`; files `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`). Supersedes `0599271`: the same decisions, a much cheaper lockless encoding (README "Since 0599271") |
| parent | `7ce10a05` = trial_w6 source. Its kit v2.3 `-Expose` build = trial_w6 `4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` |
| OFF exe (compile-time 0) | identical to trial_w6 (`4181a589…`, pc1 = pc2: tags f0c, f0d). **Nothing to gate**: it is the lock's exe |
| GATE exe (compile-time 1) | **`a4b57032294d9d9efe2742408bb0a56da970cd1146f15c360a1fe99aada2c54b`**, pc1 = pc2 (tags f1c, f1d). On this PC: `D:\forge_jobs_20261107\opus2\out\exe\forge_smpgate_a4b57032.exe` and `D:\forge_jobs_20261107\opus2\out\k\f1c\src_copy\forge_ltopgo_f1c.exe` |
| rebuild recipe | `git archive a675c04 include src`, then flip the single line `#define FORGE_SMP_LAYOUT 0` → `1` in `include/forge/search.hpp`, then QA kit v2.3 `build_ltopgo.ps1 -Expose`. Equivalent: a fresh P export + the published patch + the flip gives the same tree byte for byte (`diff -r`, checked) |
| UCI option | `TtLockless` (type check, default **false**). `false` = trial_w6's striped-lock TT, plus the measured `nodes_` cache-line fix; `true` = lockless TT |

## What is proven (BENCH.md §10 for this candidate)
- Threads 1, with `TtLockless` false **and** true: node-identical to trial_w6. Covered:
  - kit identity, pins net on/off d11-22, perft;
  - full fens12k net on/off (12,000/12,000);
  - warm-table transcripts and Hash-1 replacement pressure;
  - deeper warm (200k nodes, ON);
  - liveness of the option (on this PC and in CI).
- Race/stress:
  - CI TSan "0 reports" on this candidate, including the real engine over UCI at Threads 2/4 in both modes. Not a race proof.
  - Fixture: 0 incoherent reads in every run, with a gating positive control.
  - UCI lifecycle stress at Threads 1/4/8: PASS.
- The tag's collision behaviour is exactly characterised (BENCH §9). The TT access path's cost is measured in a micro-benchmark (BENCH §8): Threads 2/4 give 1.25-2.3 × P's striped-lock throughput; Threads 1 gives 0.71-0.93 × the legacy owned path.

## What is NOT proven, and is QA's call
- Engine speed. Advisory numbers only: on 2 shared SMT cores the A/A noise is ±5 %.
- Strength at Threads ≥ 2. Searches are nondeterministic there, so "node-identical" cannot be shown.
- Suggested QA path, if QA wants it:
  1. Quiet native-core timing per SCALING_PLAN.md: P vs gate OFF vs gate ON at Threads 1/2/4/8.
  2. If the lockless mode should go into play at Threads ≥ 2: an SPRT of `gate TtLockless=true` vs trial_w6 at the gate's usual multi-thread setting, after Code Review.
- At Threads 1, `TtLockless=false` is the trial_w6 search with a 64-byte layout change. Only timing could tell it apart.

## Known properties
- Toggling `TtLockless` empties the TT (a new storage type). Peak memory during a toggle is 2 × Hash, as for P's own Hash resize.
- `TtLockless` is read by the bench searcher too: `bench` with the option on exercises the lockless table, and the pins are equal.
- CI on this branch builds with `-DFORGE_SPD_NNUE_ZMM=0`, because the runner has no AVX-512F. That switch is speed-only and bit-exact (CI pins ALL OK).
- The lockless decode assumes a little-endian target. A `static_assert` stops any other target at compile time.

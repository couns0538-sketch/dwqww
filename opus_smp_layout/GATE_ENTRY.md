# opus_smp_layout — GATE_ENTRY (hand-off note for Code Review → QA; NOT queued by this job)

## What to review and test
| item | value |
|---|---|
| engine candidate | branch `opus-smp-layout-20261107`, commit **`89cddf7e3727ed0f461537af785dc344386fac50`** ("enc5"). Engine diff `7ce10a05..89cddf7` = `smp_layout_after_w6.patch` (+366/-0, md5 `f07082fdc8a06cb5baaae9cb76f3b538`; files `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`). Supersedes `a675c04` (enc4) and `0599271`: the same decisions throughout, a cheaper lockless encoding (enc4), and the lockless bodies compiled as normal `-O3` code under the kit's PGO (enc5, SPEC 3.7) |
| parent | `7ce10a05` = trial_w6 source. Its kit v2.3 `-Expose` build = trial_w6 `4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0` |
| OFF exe (compile-time 0) | identical to trial_w6 (`4181a589…`, pc1 = pc2: tags h0c, h0d). **Nothing to gate**: it is the lock's exe |
| GATE exe (compile-time 1) | **`2940fb0514dd2ef058d6512bf66659074f162293f7d31ccac23779c2e65762e5`**, pc1 = pc2 (tags h1c, h1d; plus g1c from an identical scratch tree). On this PC: `D:\forge_jobs_20261107\opus2\out\exe\forge_smpgate_2940fb05.exe` and `D:\forge_jobs_20261107\opus2\out\k\h1c\src_copy\forge_ltopgo_h1c.exe` |
| rebuild recipe | `git archive 89cddf7 include src`, then flip the single line `#define FORGE_SMP_LAYOUT 0` → `1` in `include/forge/search.hpp`, then QA kit v2.3 `build_ltopgo.ps1 -Expose`. Equivalent: a fresh P export + the published patch + the flip gives the same tree byte for byte (`diff -r`, checked) |
| UCI option | `TtLockless` (type check, default **false**). `false` = trial_w6's striped-lock TT, plus the measured `nodes_` cache-line fix; `true` = lockless TT |
| porting enc4 → enc5 | add the `FORGE_LOCKLESS_UNTRAINED_OPT` macro block and put it in front of the `probe_lockless` and `store_lockless` definitions in `src/search.cpp` (nothing else differs) |

## What is proven (BENCH.md §11 for this candidate)
- Threads 1, with `TtLockless` false **and** true: node-identical to trial_w6. Covered:
  - kit identity, pins net on/off d11-22, perft;
  - full fens12k net on/off (12,000/12,000);
  - warm-table transcripts and Hash-1 replacement pressure;
  - deeper warm (200k nodes, ON);
  - liveness of the option (on this PC and in CI).
- Race/stress:
  - CI TSan "0 reports" on this candidate (run 42708220996), including the real engine over UCI at Threads 2/4 in both modes. Not a race proof.
  - Fixture: 0 incoherent reads in every run, with a gating positive control.
  - UCI lifecycle stress at Threads 1/4/8: PASS.
- The tag's collision behaviour is exactly characterised (BENCH §9).
- The TT access path's cost is measured in a micro-benchmark (BENCH §8): Threads 2/4 give 1.25-2.3 × P's striped-lock throughput; Threads 1 gives 0.71-0.93 × the legacy owned path.
- The lockless bodies in the kit exe are speed-optimised and in normal `.text` (BENCH §11 codegen).

## What is NOT proven, and is QA's call
- Engine speed. Advisory numbers only: on 2 shared SMT cores the A/A noise is ±5 %, and per-file effects reach 6 %. Time fresh byte copies per round.
- Strength at Threads ≥ 2. Searches are nondeterministic there, so "node-identical" cannot be shown.
- Suggested QA path, if QA wants it:
  1. Quiet native-core timing per SCALING_PLAN.md: P vs gate OFF vs gate ON at Threads 1/2/4/8.
  2. If the lockless mode should go into play at Threads ≥ 2: an SPRT of `gate TtLockless=true` vs trial_w6 at the gate's usual multi-thread setting, after Code Review.
- At Threads 1, `TtLockless=false` is the trial_w6 search with a 64-byte layout change. Only timing could tell it apart.
- PGO note: the call sites of the lockless functions inside the search stay profile-cold blocks under QA's frozen workload. A training run that executes `TtLockless=true` would change that, and is QA's decision.

## Known properties
- Toggling `TtLockless` empties the TT (a new storage type). Peak memory during a toggle is 2 × Hash, as for P's own Hash resize.
- `TtLockless` is read by the bench searcher too: `bench` with the option on exercises the lockless table, and the pins are equal.
- CI on this branch builds with `-DFORGE_SPD_NNUE_ZMM=0`, because the runner has no AVX-512F. That switch is speed-only and bit-exact (CI pins ALL OK).
- The lockless decode assumes a little-endian target. A `static_assert` stops any other target at compile time.
- `FORGE_LOCKLESS_UNTRAINED_OPT` is GCC-only. For Clang/MSVC it is empty, so their builds compile the two functions with their normal flags.

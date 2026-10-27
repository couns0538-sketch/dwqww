# S-A2 [Sol leftover] int16 inference weights + weight clipping in training — DONE

**Branch `opus-sol-SA2`:**
- AL1 lock `d4f4312`
- CI baseline `0d99f02`, cherry-picked as `669e356a`
- `d2301c51`: engine, tests, trainer, evidence
- `4b2a6800`: CI evidence, `[skip ci]`
- the REPORT commit

**Spec:** `SOL_LEFTOVERS_FOR_CLAUDE.md` §2 item 39; `OPUS_TEST_PLAN.md` row 2 (G-A2, srand 869014820). No gate was run.
Work and results by a sub-agent; this report text is its hand-back.

## Acceptance
| line | result | evidence |
|---|---|---|
| Parity first: NnueInt16 == exact Python integer reference on 10000/10000 (lock net `a7ebcf3a…`, `fens_10k.txt` `82a3845c…`) | PASS | 10000/10000 on the AVX2 kernels (box recipe) and on the scalar kernels (`-march=x86-64`); the two dumps are byte-identical (`ba76ee81…`). int32 accumulators match 10000/10000 (signatures). Incremental vs fresh: 0 mismatching plies (up to 4 seeded moves or null moves per FEN). `logs/parity_lock_10k.json`, `logs/parity_build_and_run.log`, `logs/parity_dump_lock_10k.tsv.gz` |
| Difference to the float path, same 10000 positions | REPORTED | Max 1 cp, mean 0.0169 cp, p99 1 cp; 169 differ (−1: 90, +1: 79). Sign flips: raw net 0 (2 zero-vs-nonzero); full static HCE+net 0. Float path == float32 emulation of the engine's lane order on 10000/10000. Analytic bound for this net: 1.90 cp, so at most 2 cp |
| Option OFF = lock identity | PASS | `uci_check.py --full` ALL OK: bench d11–d22 312866 / 862329 / 3024920 / 12389307 / 34048354, perft5 4865609 / 193690690. FMA 0, 0 warnings. PC box recipe (`logs/uci_check_full_off.log`, `logs/build_pc_box_recipe.log`) and CI release (Linux g++-14) |
| CTest: known failures only | PASS | 17 tests; only `forge_tests` fails, with its 4 known lines. `logs/ctest_release_pc.log`, `logs/cmake_build_and_known_failures_pc.log` |
| CI release / ASan / TSan | PASS | Run 40515643380 success. Jobs: release 122228771232, asan 122228771391, tsan 122228771495; TSan 0 reports. `logs/ci_40515643380.log` |
| ON bench nodes recorded | PASS | d11 330610, d13 858175 (also d16 2760596, d20 9564588, d22 21638970), `logs/bench_on_nnueint16.log`. Pinned in `tools/nnue_int16_regression.py` and reproduced on Linux CI |
| NPS ON vs OFF at d16/d20 (ABBA, advisory) | RECORDED | Same exe, 5 runs per arm, CPU-time NPS: d16 −10.51% (95% CI −15.37..−5.65%), d20 −13.02% (−16.03..−10.01%). PC at 100% load. `logs/nps_on_vs_off.log`. No speed claim |
| Unit tests + planted bug | PASS | `forge_nnue_int16_tests`: 40,691 checks (independent integer reference, float emulation, incremental vs fresh accumulators along playouts with castling, en passant, promotions and null moves, the representation tag, the analytic bound). `forge_nnue_int16_scalar_tests` (`-mno-avx2`). `nnue_int16_uci_regression` (option listing, invalid value, OFF/ON/OFF bench pins, Threads 2, setoption during `go infinite`). 5/5 planted bugs caught and the control passes: `logs/mutation_engine.log` |
| Trainer `--weight-clip`, default off | PASS | `trainer_v3c_clip.py` + `v3c_to_clip.diff` (against the S50 v3c `ff98828a`) |
| Clip off == v3c byte-identical | PASS | CPU smoke r1, 2 runs: 8 artifacts (.pt .inc .bin .json × 2 epochs) sha256-equal; normalized stdout and settings dump equal. `logs/trainer_smoke_compare_r1.log` |
| Clip on: no exported weight saturates; deterministic | PASS | Bare clip (K 21704): max\|q\| 406, 0 values at the int16 rail. K 204: the clip binds (697 W1 values at the bound) and every value stays ≤ 204. Repeat runs are byte-identical; resume reproduces epoch 2; warm start + clip also works. `logs/trainer_smoke_acceptance_r1.json` |
| Trainer tests + planted bugs | PASS | 10/10 unit tests (`logs/trainer_unit_tests.log`); 8/8 mutants caught (`logs/trainer_mutation_check.log`) |
| Supervisor log | PASS | 7 "adopted running job" lines before and after every torch step and at the end. `logs/supervisor_check.log` |

## What was done
- **Engine.** Sol's NnueInt16 (`b425207a`: `764db5f3`, `07410241`) is ported onto the AL1 lock as UCI option `NnueInt16` (check, default false).
  - `src/nnue_int16.inc`: int16 weights straight from the include file, int32 accumulators, AVX2 clamp/square/dot kernels with int64 widening per 16-unit group, and a scalar fallback.
  - `src/nnue.cpp`: 3 hooks. `Accumulator` gains `integer_values` and an `integer` tag.
  - Only the int16 path is ported. Not ported: the AVX-512/align64 float paths, the `search.cpp` hunks, `.agents`, tools, LICENSE.
  - `port_vs_sol_nnue_int16.diff`: the kernel differs from Sol's only in comments, the atomic flag and one hoisted helper.
- **CR hold findings addressed.** The mode flag is now `std::atomic<bool>`, and the docs say the accumulators are int32.
- **Trainer.** `--weight-clip [C]` clamps W1, B1, W2 and B2 to ±K/4096 after every step, where K = floor(C·4096) and 1 ≤ K ≤ 32766.
  - Bare `--weight-clip` uses K 21704, the largest K with 773·K < 2^24.
  - Every export is verified (INT16 CHECK line) and refused if any value exceeds K.
  - The config key is written only when the clip is on.

## Findings
- **The trainers already clipped.** Since v2, every trainer clamps each parameter to the int16 rail (±32767/4096) after every step, and the export refuses out-of-range values. So an int16 export could never saturate before either. `--weight-clip` adds explicit, verified headroom tied to the engine's NnueInt16 eligibility check.
- **The default clip would not bind on the lock net.** Max \|w1\| 14227, max \|b1\| 6764, max \|w2\| 13906, all below 21704.
- **int32 accumulators are safe for any int16 net at any width.**
  - \|A\| ≤ \|b1\| + 32 active columns ≤ 33·K: at most 1,081,311 for any int16 net, 716,232 at K 21704.
  - Even all 768 inputs plus 4 transient columns: 773·32767 = 25,328,891 < 2^31.
  - The binding constraint is the engine's float-grid check (lane bound < 2^24). The lock net is at 2,054,814 (8.2× headroom); K 21704 guarantees the check by construction.
- **ON is slower per node:** −10.5% / −13.0% CPU NPS here; CR measured −7% on its box.
  - int32 accumulators fill 8 lanes per AVX2 vector, the same as float, and add an int16→int32 widening per column.
  - The integer update has no quiet/capture fast paths.
  - A speed gain would need int16 accumulators, which overflow at scale 4096 on every net (S21). That means a lower feature-transformer scale or K ≤ 992, a separate design job.
- **ON changes the search tree.** Bench nodes vs lock: d11 +5.7%, d13 −0.5%, d16 −8.7%, d20 −22.8%, d22 −36.4%.
- **OFF has a small cost.** Each accumulator grows from 2 KiB to 4 KiB per stack entry. OFF vs lock CPU NPS: −1.1% (d16, CI −7.5..+5.2) and −1.2% (d20, CI −3.8..+1.5), within noise.
- **The committed tree builds the measured exe.** A rebuild differs only in 4 PE header bytes.

## Process notes (main session, from the sub-agent's hand-back)
- The first ON-vs-OFF NPS launch produced no data (MSYS did not convert a `/f/...::NnueInt16=true` argument); it was re-run with `F:/` paths.
- CTest's Python tests left untracked `tools/__pycache__` folders in the worktree (not committed, not deleted).

## Left / UNVERIFIED
- No gate (G-A2), no Elo or speed claim. CR's policy flag still applies: "H256 nets are float-only". Turning ON for any gate or lock needs a crew vote and its own SPRT [0,10] gate.
- NPS was measured only on the loaded PC.
- The trainer clip was verified only on CPU with the synthetic data32 sample (H64), not on DirectML. The clamp is the same operation as v3c's projection, which already runs on DirectML.
- Parity used one net (the lock) on the 10k FENs from S31.

Machine exclusive: no.

## Quiet-runner OFF-path NPS (follow-up, added by the main session)
Branch `opus-offguard`, workflow run 40520714508 (GitHub ubuntu-24.04, g++-14 box flags; `opus-offguard:opus_round1/offguard/REPORT.md`):
the OFF build of `d2301c51` against the lock `294dbed3`, 10 ABBA runs per side, nodes identical, identity ALL OK.
- CPU NPS B/A: d16 0.9960 (−0.40%, 95% CI −0.61 .. −0.19), d20 0.9954 (−0.46%, CI −0.62 .. −0.30). The OFF path has a
  **small real cost** (both CIs exclude 0), smaller than the PC figure above (−1.1% / −1.2%, wide CIs).
- Code size: `nnue::refresh` 589 → 691 bytes, `nnue::update` 2,266 → 2,342, `nnue::evaluate` 431 → 447; search and
  qsearch unchanged. With the larger accumulator entries (2 → 4 KiB) these are the likely sources.

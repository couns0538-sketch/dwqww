# FABLE_REPORT.md — job FB1: NNUE v3 architecture (branch `fable-nnue-arch`) — IN PROGRESS

Base: `d4f4312` (AL1 s198 lock) + the CI baseline `0d99f02` cherry-picked (`5ff6208`). Worktree
`F:\opus_scratch\fable_wt`, scratch `F:\opus_scratch\fable\`, builds `F:\opus_scratch\build\fable\`.
Everything here is UNPROVEN until a gate; no Elo claim is made anywhere in this report. Machine exclusive: no
(gates, self-play and NNUE training were running during every measurement, so no speed claim either).

## Milestone status

| milestone | status | summary |
|---|---|---|
| M1 engine: UCI `NNUEArch` (default off), v3 loader, scalar reference eval | **DONE** (commit `eef2fe72`) | all acceptance checks pass |
| M2 incremental accumulator + king-bucket refresh cache + AVX2 | **DONE** (this commit) | 100k plies incremental == refresh, 0 mismatches; AVX2 == scalar |
| M3 trainer: QAT int16, v3 exporter with merged factoriser, 10k parity | IN PROGRESS | trainer written (`tools/nnue/fable_nnue_train.py`), parity run next |
| M4 NPS ON/OFF, smoke training vs AL1 net | not started | |

## M1 acceptance (engine side only)

| check | result | evidence |
|---|---|---|
| OFF bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690 | **PASS** (`ALL OK`), box recipe, exe sha256 `746c73ec…`, FMA 0, 0 warnings | `fable/logs/identity_off_m1.log`, `fable/logs/build_pc_m1.log` |
| no movegen change | PASS: `src/board.cpp`, `src/bitboard.cpp` untouched; perft pins above | — |
| loader: header/size/checksum/range checks, loud failure, nothing loaded after a failure | PASS: 16 rejection cases (truncated/extra bytes, flipped weight bit, flipped header bit, wrong qa, unknown flag, map entries out of range, w2 > 127, accumulator range) | `fable/logs/unit_tests_m1.log` |
| scalar reference eval == independent integer implementation | PASS: 40 positions x 4 nets; identical heads == one head | same log |
| engine scalar eval == Python integer reference, 10k positions | **PASS 10000/10000, 0 mismatches** on a random H512 / 8 mirrored king buckets / 8 output buckets net (piece counts 2..32, all 8 output buckets used) | `fable/logs/parity_m1_rand_h512.log` |
| fail-loud rule | PASS: `NNUEArch true` without a net -> `isready` exits 2; a non-net file -> `bad magic` and `bench` exits 2 | `fable/logs/uci_failloud_m1.log` |
| CMake + ctest | PASS: 14/14 locally (`forge_tests`, a 4-thread search, is left to CI per the PC thread limit) | `fable/logs/ctest_m1.log` |

## M2 acceptance (incremental accumulator, refresh cache, AVX2)

| check | result | evidence |
|---|---|---|
| OFF identity unchanged after the M2 hooks | **PASS** `ALL OK` (bench x5, perft5, kiwipete), exe sha256 `2d9fb6c3…`, FMA 0, 0 warnings | `fable/logs/identity_off_m2.log`, `fable/logs/build_pc_m2.log` |
| incremental == full refresh over 100k random make/unmake plies | **PASS: 100,000 plies, 64,987 evaluations, 0 mismatches** (both perspectives' int16 values, king keys and king squares compared bit for bit with a from-scratch refresh); coverage: 356 castlings, 108 en passant captures, 1321 promotions, 28,793 king moves, 9,993 king-key changes (bucket or mirror side), 4,800 null moves, 12,507 replays across 2+ unevaluated plies (max 9); 4 nets: H128/8 mirrored buckets/8 heads, H512/4m/8, H64/2 unmirrored/1, H32/32m/2 | `fable/logs/unit_tests_m2.log` |
| fast `evaluate` (cache + AVX2) == scalar reference | PASS: 0 mismatches on all 64,987 walk evaluations; 10k positions tool output identical to the M1 scalar output and to the Python reference (0 mismatches) | same log, `fable/logs/parity_m2_rand_h512.log` |
| AVX2 == scalar at the bounds | PASS: 400 output sums at H1024 with w2 = +-127 and accumulators at +-32767 / random, bit-equal to the int64 scalar sum; `apply_changes` kernel == scalar for every legal move of the kiwipete position | same log (`kernel avx2`) |
| search uses the incremental path consistently | PASS: ON `bench 11` = 91949 nodes on the M2 exe, identical to the M1 exe's full-refresh ON bench (`bench 13` = 550792) | `fable/logs/uci_on_bench_m2.log` |
| CMake + ctest | PASS: 14/14 locally (95,729 checks in `forge_nnue_v3_tests`) | `fable/logs/ctest_m2.log` |

## What was built

- `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`: the v3 format (`FORGENN3`, 192-byte header, king-bucketed
  HalfKA inputs, runtime hidden size 32..1024 (multiple of 32), 1..32 king buckets with optional mirroring,
  1..16 output buckets by total piece count, int16 weights, int32 output biases, FNV-1a 64 trailer), the loader
  (every header field, exact file size, checksum, map ranges, reserved bytes and the overflow bounds
  `|w2| <= 127`, `max|b1| + 32*max|w1| <= 32767` are checked; a failed load leaves nothing loaded and names the
  reason), the feature set, the scalar reference path, and (M2) the fast path: `apply_changes` (AVX2 add/sub of up
  to 4 weight columns in one pass), `output_sum` (AVX2 `mullo`+`madd` SCReLU with two int32 accumulators per lane
  and an int64 reduction; exact by the loader bounds), the per-worker `RefreshCache` keyed by (perspective,
  bucket, flip) that stores the accumulator and 12 piece bitboards and applies only the difference, and the
  header templates `replay_ply` / `make_valid` (walk back to the nearest valid ply, replay the recorded piece
  changes; a perspective whose king key changed is refreshed through the cache from the piece placement of that
  ply, reconstructed from the current board by undoing the later plies' changes).
- Quantisation: QA = 255 (activations), QB = 64 (output weights), `out = sum / QA + b2`,
  `cp = out * eval_scale / (QA * QB)` with C++ truncating division.
- `src/search_v3.cpp`: `Worker::static_evaluate_v3`, reached through one `[[unlikely]]` branch at the top of
  `Worker::static_evaluate` when `NNUEArch` is on and a net is loaded; `record_move` / `record_null_move`
  invalidate the child's v3 accumulator through one `if (v3_state_) [[unlikely]]` (null pointer with the option
  off). Residual nets add the hand-crafted evaluation with the AL1 path's lazy runtime-PSQT scheme. Per-worker v3
  state is heap-allocated on first use, so `SearchStack` is unchanged for the OFF path.
- `src/uci.cpp`: options `NNUEArch` (check, default false) and `NNUEArchFile` (string, default `<empty>`).
  Loading prints `info string NNUE v3 loaded: …` (with the kernel name); any failure prints
  `info string ERROR NNUE v3: <reason>`. Fail-loud rule (idea from C5): with `NNUEArch true` and no usable net,
  `isready`, `go` and `bench` print the error and exit with status 2. `UseNNUE false` also disables the v3 path.
- Tools: `tools/nnue_v3_tool.cpp` (`forge_nnue_v3_tool info|eval|sum`; `eval` runs the fast path and checks it
  against the scalar reference on every position), `tools/nnue/fable_nnue_v3.py` (writer, reader, random nets,
  exact integer reference evaluator, random-position generator covering piece counts 2..32, `compare`),
  `tools/nnue/fable_nnue_uci.py` (UCI driver), `tools/nnue/fable_nnue_train.py` (M3 trainer, see below),
  `tests/nnue_v3_tests.cpp` (ctest `forge_nnue_v3_tests`).
- Box-recipe builds need `FORGE_EXTRA_SRCS="src/nnue_v3.cpp src/search_v3.cpp"` with `build_pc.sh`; CMake lists
  the new sources.

## M3 (in progress): `tools/nnue/fable_nnue_train.py`

CPU torch, one thread. Reads FPOS/FHCE shards (meta bit0 = side to move, bits 1-2 = white result x 2, as the
S31 tool documents). Model: merged first layer `w1[kb*768][H] + factoriser[768][H]`, SCReLU, `w2[ob][2H]`,
`b2[ob]`; loss = MSE of sigmoid((cp [+ hce]) * 2.25/400) against blend * sigmoid(score * 2.25/400) +
(1 - blend) * result (the lock recipe's b0.6). Quantisation-aware: every forward rounds the merged w1 and b1 to
1/255, w2 to 1/64 (clipped to +-127/64) and b2 to 1/(255*64) with straight-through gradients, and every step
clips the parameters to the exportable ranges (w1 bucket and factoriser +-0.99 each, b1 +-1.98, w2 +-127/64).
Export merges the factoriser into every bucket and writes the v3 file. `parity`: engine int cp == integer
emulation of the exported file (0 mismatches required) and |training float forward - engine int| <= 2 cp.

## What is left / exact next steps

1. M3: run `fable_nnue_train.py train` for a few steps on `F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.pos/.hce`
   (1,024,286 rows, residual, H512/8m/8), `forge_nnue_v3_tool eval net.fnn3 positions_10k.fen`, then
   `fable_nnue_train.py parity` -> record int mismatches (must be 0) and max |float - int| (must be <= 2 cp).
2. M4: NPS ON vs OFF at Threads=1 (bench d16/d20, ABBA, same exe, option via UCI), ratio only (loaded PC);
   smoke training for a few minutes; `fable_nnue_train.py score` of the v3 net vs the AL1 net's loss on the same
   holdout rows (the AL1 numbers via the S31 scorer).
3. CI: `gh run list --branch fable-nnue-arch`; record run ids here.

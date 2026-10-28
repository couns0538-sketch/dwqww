# FABLE_REPORT.md — job FB1: NNUE v3 architecture (branch `fable-nnue-arch`) — IN PROGRESS

Base: `d4f4312` (AL1 s198 lock) + the CI baseline `0d99f02` cherry-picked (`5ff6208`). Worktree
`F:\opus_scratch\fable_wt`, scratch `F:\opus_scratch\fable\`, builds `F:\opus_scratch\build\fable\`.
Everything here is UNPROVEN until a gate; no Elo claim is made anywhere in this report. Machine exclusive: no
(gates, self-play and NNUE training were running during every measurement).

## Milestone status

| milestone | status | summary |
|---|---|---|
| M1 engine: UCI `NNUEArch` (default off), v3 loader, scalar reference eval | **DONE** | all acceptance checks pass (table below) |
| M2 incremental accumulator + king-bucket refresh cache + AVX2 | not started | |
| M3 trainer: QAT int16, v3 exporter with merged factoriser, 10k parity | not started | |
| M4 NPS ON/OFF, smoke training vs AL1 net | not started | |

## M1 acceptance (engine side only)

| check | result | evidence |
|---|---|---|
| OFF bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690 | **PASS** (`ALL OK`), box recipe, exe sha256 `746c73ec…`, FMA 0, 0 warnings | `fable/logs/identity_off_m1.log`, `fable/logs/build_pc_m1.log` |
| no movegen change | PASS: `src/board.cpp`, `src/bitboard.cpp` untouched (`git diff d4f4312 -- src/board.cpp src/bitboard.cpp` empty); perft pins above | — |
| loader: header/size/checksum/range checks, loud failure, nothing loaded after a failure | PASS: `forge_nnue_v3_tests` 184 checks, 0 failures (16 rejection cases incl. truncated/extra bytes, flipped weight bit, flipped header bit, wrong qa, unknown flag, map entries out of range, w2 > 127, accumulator range) | `fable/logs/unit_tests_m1.log` |
| scalar reference eval == independent integer implementation | PASS: 40 positions x 4 nets (1/8 output buckets, mirrored/unmirrored) in the unit test; identical heads == one head | same log |
| engine scalar eval == Python integer reference, 10k positions | **PASS 10000/10000, 0 mismatches** on a random H512 / 8 mirrored king buckets / 8 output buckets net (piece counts 2..32, all 8 output buckets used, cp range -15334..15997) | `fable/logs/parity_m1_rand_h512.log` (net sha256 `e3ef99b7…`, positions `3648c1ae…`) |
| fail-loud rule | PASS: `NNUEArch true` without a net -> `info string ERROR NNUE v3: …` and `isready` exits 2; a non-net file -> `bad magic` error and `bench` exits 2 | `fable/logs/uci_failloud_m1.log` |
| ON path runs | PASS: random net ON, `bench 11` = 91949 nodes (different tree, as expected for a random net), OFF `bench 11` = 312866 in the same exe | `fable/logs/uci_on_bench11_m1.log`, `fable/logs/uci_off_bench11_m1.log` |
| CMake + ctest | PASS: all targets build; 14/14 tests pass locally (`forge_tests`, a 4-thread search, is left to CI per the PC thread limit) | `fable/logs/ctest_m1.log` |

## What was built (M1)

- `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`: the v3 format (`FORGENN3`, 192-byte header, king-bucketed
  HalfKA inputs, runtime hidden size 32..1024 (multiple of 32), 1..32 king buckets with optional mirroring,
  1..16 output buckets by total piece count, int16 weights, int32 output biases, FNV-1a 64 trailer), the loader
  (every header field, exact file size, checksum, map ranges, reserved bytes and the overflow bounds
  `|w2| <= 127`, `max|b1| + 32*max|w1| <= 32767` are checked; a failed load leaves nothing loaded and names the
  reason), the feature set, and the scalar reference path (int16 refresh + SCReLU output in int64).
- Quantisation: QA = 255 (activations), QB = 64 (output weights), `out = sum / QA + b2`,
  `cp = out * eval_scale / (QA * QB)` with C++ truncating division; the bounds above make the planned AVX2
  `madd` kernel exact for every hidden size up to 1024.
- `src/search_v3.cpp`: `Worker::static_evaluate_v3`, reached through one `[[unlikely]]` branch at the top of
  `Worker::static_evaluate` when `NNUEArch` is on and a net is loaded. M1 refreshes both perspectives from scratch
  on every evaluation (correct, slow); residual nets add the hand-crafted evaluation exactly like the AL1 path.
  Per-worker v3 state (`WorkerState`, one accumulator per ply) is heap-allocated on first use, so `SearchStack`
  is unchanged for the OFF path.
- `src/uci.cpp`: options `NNUEArch` (check, default false) and `NNUEArchFile` (string, default `<empty>`).
  Loading prints `info string NNUE v3 loaded: …`; any failure prints `info string ERROR NNUE v3: <reason>`.
  Fail-loud rule (idea from C5): with `NNUEArch true` and no usable net, `isready`, `go` and `bench` print the
  error and exit with status 2. `UseNNUE false` also disables the v3 path. Every change clears the hash.
- Tools: `tools/nnue_v3_tool.cpp` (`forge_nnue_v3_tool info|eval|sum`), `tools/nnue/fable_nnue_v3.py` (writer,
  reader, random nets, exact integer reference evaluator, random-position generator covering piece counts 2..32,
  `compare`), `tools/nnue/fable_nnue_uci.py` (UCI driver), `tests/nnue_v3_tests.cpp` (ctest `forge_nnue_v3_tests`).
- Box-recipe builds need `FORGE_EXTRA_SRCS="src/nnue_v3.cpp src/search_v3.cpp"` with `build_pc.sh`; CMake lists
  the new sources.

## What is left / exact next steps

1. M2 (next): `nnue::v3::update()` for the quiet/capture/castling cases on the int16 accumulators, per-perspective
   king-key check (same bucket+flip -> incremental, else refresh through a per-worker cache keyed by
   (perspective, bucket, flip) holding the accumulator and 12 piece bitboards); the walk-back/replay in
   `static_evaluate_v3` over `ss->dirty`; AVX2 kernels for add/sub columns and the SCReLU output; tests: 100k
   random make/unmake plies (castling, en passant, promotions, king moves) incremental == refresh with 0
   mismatches, AVX2 == scalar on the 10k positions.
2. M3: `tools/nnue/fable_nnue_train.py` (reads FPOS/FHCE shards, QAT by clipping w1/b1 to +-1.98 (int16 +-505) and
   w2 to +-127/64, factoriser block folded at export, exporter to v3); parity: engine int == trainer int on 10k
   positions, float within 2 cp.
3. M4: NPS ON vs OFF at Threads=1 (bench d16/d20, ABBA), short smoke training, val loss vs the AL1 net.
4. CI: `gh run list --branch fable-nnue-arch` after each engine push; record the run ids here.

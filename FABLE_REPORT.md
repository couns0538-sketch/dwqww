# FABLE_REPORT.md — job FB1: NNUE v3 architecture (branch `fable-nnue-arch`) — M1-M4 DONE, M5 (full-spec items) IN PROGRESS, UNPROVEN

Base: `d4f4312` (AL1 s198 lock) + the CI baseline `0d99f02` cherry-picked (`5ff6208`). Worktree
`F:\opus_scratch\fable_wt`, scratch `F:\opus_scratch\fable\`, builds `F:\opus_scratch\build\fable\`.
Everything here is UNPROVEN until a gate; no Elo claim is made anywhere in this report. Machine exclusive: no
(gates, self-play and NNUE training were running during every measurement, so no speed claim either).

## Milestone status

| milestone | status | summary |
|---|---|---|
| M1 engine: UCI `NNUEArch` (default off), v3 loader, scalar reference eval | **DONE** (commit `eef2fe72`) | all acceptance checks pass |
| M2 incremental accumulator + king-bucket refresh cache + AVX2 | **DONE** (this commit) | 100k plies incremental == refresh, 0 mismatches; AVX2 == scalar |
| M3 trainer: QAT int16, v3 exporter with merged factoriser, 10k parity | **DONE** (this commit) | 60-step residual H512/8m/8 net: engine int == trainer int 10000/10000 on two position sets, max float-int 1.02 cp |
| M4 NPS ON/OFF, smoke training vs AL1 net | **DONE** (68594f5d..b885f6f8) | NPS ratio ON/OFF 0.777 (d16) / 0.767 (d20); 5-minute smoke net does NOT beat HCE on the holdout (overfits one ordered shard), AL1 net far ahead |
| M5 full-spec items: AVX-512 kernels, scalar = AVX2 = AVX-512, 1M-ply walk, 100k-position parity, H1024 NPS, bucket-layout rationale, cross-shard streaming training | IN PROGRESS | AVX-512, the 1M-ply walk and the 100k parity done and verified (M5 section); H1024 NPS and the first-net run are running |

## King-bucket layout (why this one)

The v3 header carries the full 64-entry map, so any layout can be shipped without an engine change; the trainer
default (`fable_nnue_v3.py king_layout(8)`) is the mirrored 8-bucket layout below (files a-d after mirroring, rank 1 at
the bottom; a king on files e-h uses the same bucket with the board mirrored horizontally):

```
rank 8: 7 7 7 7      rank 4: 6 6 6 6
rank 7: 7 7 7 7      rank 3: 6 6 6 6
rank 6: 7 7 7 7      rank 2: 4 4 5 5
rank 5: 7 7 7 7      rank 1: 0 1 2 3
```

Reasons: (1) the first rank gets one bucket per file (a1/b1 = castled queen side, c1/d1 = centre-left, and through
the mirror g1/h1 = castled king side, e1/f1 = uncastled) because those are the king placements that dominate
middlegame play and they differ most in what the net has to see; (2) rank 2 gets two buckets (the king stepped up
after castling vs the centre); (3) ranks 3-4 share one bucket and ranks 5-8 share one, because such kings occur in
endgames where the king's exact square matters less than the material, which the output buckets handle; (4)
mirroring halves the number of buckets needed for the same coverage, and the factoriser lets rarely visited buckets
borrow from the shared weights; (5) 8 buckets x 768 x H keeps the file at 6.3 MB for H512 (12.6 MB for H1024) and
the refresh cache at 2 x 8 x 2 entries per worker. The same shape (8 mirrored buckets with the first rank split per
file) is what Opus's C4 report measured for refresh cost (about 14-17% of evaluations change the king key at bench
depth 16); the walk tests here show about 10% key changes on random plies. The 4-bucket layout (C4's other standard)
is available with `--king-buckets 4` if the refresh cost of 8 turns out too high in the NPS profile.

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

## M3 acceptance (trainer side)

Run: `fable_nnue_train.py train --pos holdout_013_014_s16.pos --hce ... --hidden 512 --king-buckets 8 --output-buckets 8
--mirror --residual --steps 60 --batch 4096 --lr 1e-3 --val-rows 20000` (CPU torch, 1 thread, 11 s, 21k positions/s,
245,760 positions seen; val loss b0.6 0.017025 -> 0.016838 on the last 20k rows; this is a few-step net, not a
trained one). Export: `net.fnn3` sha256 `e37caef5…` (max|w1| 34, max|b1| 6, max|w2| 7), `model.pt` `d3619764…`.

| check | result | evidence |
|---|---|---|
| engine int eval == trainer quantised eval, 10k positions | **PASS 10000/10000, 0 mismatches** on `positions_10k.fen` (random material, piece counts 2..32, all 8 output buckets) and **10000/10000** on the S31 real-game set `fens_10k_s31.fen` (first field of `F:\opus_scratch\sol_S31\inputs\fens_10k.txt`) | `fable/logs/parity_m3.log` |
| float vs int within 2 cp | **PASS**: max abs(training float forward - engine int) = 1.0189 cp / 1.0190 cp, mean 0.50 cp, 0 positions above 2 cp (by construction: the forward uses the engine's integer grid, only the two truncating divisions differ) | same log |
| fast path == scalar reference on the trained net | PASS (tool `eval` reports 0 fast-vs-reference mismatches on both sets) | same log |
| trainer unaffected by the forbidden-name rule | the trainer is a new script `fable_nnue_train.py`; nothing named `train_resid*` was run; supervisor "adopted running job" count unchanged (7) | `fable/logs/train_m3_log.txt` |

## M3 design: `tools/nnue/fable_nnue_train.py`

CPU torch, one thread. Reads FPOS/FHCE shards (meta bit0 = side to move, bits 1-2 = white result x 2, as the
S31 tool documents). Model: merged first layer `w1[kb*768][H] + factoriser[768][H]`, SCReLU, `w2[ob][2H]`,
`b2[ob]`; loss = MSE of sigmoid((cp [+ hce]) * 2.25/400) against blend * sigmoid(score * 2.25/400) +
(1 - blend) * result (the lock recipe's b0.6). Quantisation-aware: every forward rounds the merged w1 and b1 to
1/255, w2 to 1/64 (clipped to +-127/64) and b2 to 1/(255*64) with straight-through gradients, and every step
clips the parameters to the exportable ranges (w1 bucket and factoriser +-0.99 each, b1 +-1.98, w2 +-127/64).
Export merges the factoriser into every bucket and writes the v3 file. `parity`: engine int cp == integer
emulation of the exported file (0 mismatches required) and |training float forward - engine int| <= 2 cp.

## M4 (part 1): NPS ON vs OFF, Threads = 1, Hash = 16, same exe (`forge_fable_m2.exe`, box recipe)

`tools/nnue/fable_nnue_nps.py`, 4 ABBA rounds (OFF, ON, ON, OFF) per depth, fresh processes, CPU time from
`GetProcessTimes`; net = the 60-step residual H512 / 8 mirrored king buckets / 8 output buckets net from M3
(`train_m3/net.fnn3`). The ON tree is a different, larger tree (a barely trained net), so the ratio below is the
per-node cost ratio, not a time-to-depth statement. Loaded PC (gates, self-play, NNUE training running) -> advisory
only; no speed claim.

| depth | OFF nodes | ON nodes | OFF CPU NPS | ON CPU NPS | ON/OFF NPS ratio (95% CI) | ON time per node / OFF |
|---|---|---|---|---|---|---|
| 16 | 3,024,920 | 3,298,439 | 1,760,063 | 1,367,578 | **0.777** (+-0.010) | 1.287 |
| 20 | 12,389,307 | 15,140,173 | 1,852,640 | 1,421,609 | **0.767** (+-0.013) | 1.303 |

Wall-clock NPS gives the same ratios (0.776 / 0.762). Evidence: `fable/logs/nps_m4_trained.log`. For reference,
S-C4 measured the float AL1 path widened to H512 at about -9.5% CPU NPS; the v3 path here evaluates a residual
H512 net with 8 king buckets (refreshes on bucket changes) plus the hand-crafted evaluation, with an int16 AVX2
kernel, at about -23%. Where the time goes was not profiled (next step for a speed job: refresh statistics per
node, `apply_changes` vs `output_sum` share, and whether the runtime-PSQT / HCE part of the residual path or the
v3 network dominates).

## M4 (part 2): smoke training and validation loss vs the AL1 net

Smoke run: `fable_nnue_train.py train --pos forge_selfplay_029.pos --hce forge_selfplay_029.hce --max-rows 6000000
--hidden 512 --king-buckets 8 --output-buckets 8 --mirror --residual --batch 4096 --lr 1e-3 --max-minutes 5 --seed 2`
(1 CPU thread, 22.5k positions/s, 1648 steps = 6,750,208 positions in 5 min, nothing adopted by the supervisor).
Training-batch loss (b0.6) fell 0.0176 -> 0.0091, but the loss on the shard's own last 50k rows rose
0.017429 -> 0.018815: the net fits the games of this one ordered shard (about 100 near-duplicate positions per
game and a 40% game-result term in the target) instead of generalising. Exported `train_m4/net.fnn3` (max|w1| 125,
max|b1| 20, max|w2| 30); `fable/logs/train_m4_log.txt`.

Validation loss on the independent holdout subset `holdout_013_014_s16` (1,024,286 rows of shards 013+014, which
neither net trained on; integer emulation of the v3 file, the S31 scorer for the AL1 `.inc`; same loss definition):

| net | MSE b0.6 (lock blend) | MSE b0.8 | MSE b1.0 (teacher) | evidence |
|---|---|---|---|---|
| HCE alone (no net) | 0.017059 | 0.008360 | 0.005074 | `fable/logs/al1_holdout_score.json` |
| **AL1 lock net** (`src/nnue_weights.inc`, H256 residual, 32 epochs on 230M rows) | **0.014310** | 0.006735 | 0.004572 | same |
| v3 smoke run step 500 (2.0M positions) | 0.017247 | 0.008954 | 0.006072 | `fable/logs/score_m4_step500_holdout.log` |
| smoke run final (1648 steps, 6.75M positions, 5 min) | 0.018732 | 0.010651 | 0.007983 | `fable/logs/score_m4_final_holdout.log` |
| v3 M3 net (60 steps ON the first 1M rows of this very subset; sanity check, not independent) | 0.016621 | 0.008085 | 0.004959 | `fable/logs/score_m3_holdout.log` |

Reading: the v3 pipeline trains and exports exactly (M3 parity), but a 5-minute run on one shard does not produce a
useful net: on the independent holdout it is worse than the hand-crafted evaluation alone (and gets worse from
step 500 to the end while the training-batch loss keeps falling, the signature of overfitting) and far from the
AL1 net. This is the expected outcome of 6.75M correlated positions against 230M shuffled ones, not a defect in the
architecture; it is also not evidence for or against the architecture. A real comparison needs the production data
path (all 29 training shards, game-shuffled, several epochs, LR schedule), i.e. hours on the GPU or days on one CPU
thread, which is outside this job's budget.

## M5: the full-spec items

### AVX-512 (DONE)

`src/nnue_v3.cpp`: `output_sum_avx512` (32 int16 per vector, `mullo` + `madd`, two int32 accumulators of 16 lanes,
each lane sums H/16 terms: half the AVX2 bound), `apply_changes_avx512`, `add/sub_column_avx512`, compiled when
`__AVX512F__ && __AVX512BW__` (the PC box recipe `-march=znver5`; the CI x86-64-v3 builds keep AVX2). The search uses
the best compiled kernel; `output_sum_with` / `apply_changes_with` / `add_column_with` expose every compiled kernel
for the equality tests. The walk test compares every compiled kernel's output sum with the scalar sum on every
evaluated position and takes its ply budget as an argument (ctest default 100k).

| check | result | evidence |
|---|---|---|
| AVX-512 box exe builds like the lock recipe | PASS: `forge_fable_m5.exe`, FMA 0, 0 warnings, 1075 zmm instructions (the lock recipe is `-march=znver5`, so the compiler's own 512-bit code is in every build) | `fable/logs/build_pc_m5.log` |
| OFF identity with the AVX-512 kernels compiled in | **PASS** `ALL OK` (bench x5, perft5, kiwipete) | `fable/logs/identity_off_m5.log` |
| scalar = AVX2 = AVX-512 (100k-ply ctest run) | **PASS**: znver5 test build: 129,974 walk comparisons (AVX2 and AVX-512 output sums vs scalar on real accumulators) 0 mismatches, 1200 H1024 output sums at the bounds (w2 = +-127, accumulators +-32767) over all three kernels equal, add/sub column and `apply_changes` of every kernel equal for every legal kiwipete move; 95,879 checks, 0 failures. x86-64-v3 test build (scalar + AVX2): 95,830 checks, 0 failures | `fable/logs/unit_tests_m5_avx512.log`, `fable/logs/unit_tests_m5_avx2.log` |
| AVX-512 search == AVX2 search | **PASS**: ON `bench 11/13` with the random net = 91949 / 550792 and `bench 16` with the M3 net = 3,298,439 nodes on the AVX-512 exe, identical to the AVX2 exe's counts (`info string ... kernel avx512` printed) | `fable/logs/uci_on_bench_m5.log` |

### 1M random make/unmake plies (DONE)

`forge_nnue_v3_tests <dir> 1000000` on both test builds (same seed, same walk): **1,000,000 plies, 649,701
evaluations, 0 accumulator mismatches** against a from-scratch refresh (both perspectives, keys and king squares bit
for bit), 0 `evaluate` mismatches against the scalar reference. Coverage: 3,622 castlings, 1,073 en passant
captures, 13,954 promotions, 302,611 king moves, 104,662 king-key changes (bucket or mirror side), 47,324 null
moves, 125,659 replays across 2+ unevaluated plies (max 11). Kernel comparisons on the walk positions: 649,701
(AVX2 vs scalar, x86-64-v3 build) and 1,299,402 (AVX2 and AVX-512 vs scalar, znver5 build), **0 mismatches**;
955,819 / 955,868 checks, 0 failures. Evidence: `fable/logs/walk_1m_avx2.log`, `fable/logs/walk_1m_avx512.log`.

### 100k-position parity (DONE)

`positions_100k.fen` (`fable_nnue_v3.py positions`, 100,000 legal positions: half random playouts, half random
standard-inventory placements so that every piece count 2..32 and every output bucket occurs; sha256 `0232208c…`),
net = the M3 60-step residual H512/8m/8 net (`e37caef5…`).

| check | result | evidence |
|---|---|---|
| engine int eval (AVX-512 tool) == engine int eval (AVX2 tool) | PASS: byte-identical outputs on 100,000 positions, 0 BADFEN, fast-vs-scalar-reference mismatches 0 in both tools | `fable/logs/parity_100k.log` |
| engine int eval == Python integer reference | **PASS 100000/100000, 0 mismatches** (cp range -88..94, output buckets 0-7 all used) | same |
| engine int eval == trainer quantised eval | **PASS 100000/100000, 0 mismatches** (integer emulation of the exported file) | same |
| trainer float forward vs engine int within 2 cp | **PASS**: max 1.0192 cp, mean 0.4988 cp, 0 positions above 2 cp | same |

### H1024 NPS, cross-shard training

(filled in as the runs finish; the first-net run with the cross-shard streaming loader is in progress:
`tools/nnue/fable_nnue_train.py train --pos-glob ... --exclude _013,_014 --chunks 8 --chunk-rows 250000
--refresh-every 25 --lr-schedule cosine --threads 2 --max-minutes 80`, validation every 10 minutes on 200k holdout
rows; the 40-step smoke of the loader gave 20k positions/s on one thread with 32 shards / 262M rows visible)

## What is left / exact next steps (for the next model)

1. **Training at scale** (the real test of the architecture): run `tools/nnue/fable_nnue_train.py` on the 29 training
   shards (game-shuffled sampling across shards, not one shard; add a shard-cycling data loader, an LR schedule and
   epoch-wise exports), residual H512 / 8 mirrored king buckets / 8 output buckets, holdout 013+014. Compare the
   b0.6 holdout MSE with the AL1 lock net (0.014310). Only then gate (SPRT [0,10] at 10+0.1 vs AL1 s198, options
   `NNUEArchFile=<net>.fnn3`, `NNUEArch=true`; the engine log must show `info string NNUE v3 active`).
2. **Speed**: the v3 residual H512 path costs about 1.29x the AL1 time per node at Threads=1 (advisory, loaded PC).
   Profile where it goes (refresh statistics per node from `RefreshCache::refreshes/columns`, `apply_changes` vs
   `output_sum`, HCE/runtime-PSQT share) before deciding on H384/H256 or a standalone (non-residual) net, which
   drops the hand-crafted evaluation from the ON path entirely.
3. **Engine follow-ups** (not needed for a gate): a `bench`-visible counter of cache refreshes; a `-DFORGE_NNUE_V3_SSE`
   kernel for non-AVX2 builds (the scalar fallback is correct but slow); `Threads > 1` was not exercised with the
   option on (each worker owns its state; a TSan run with `NNUEArch true` is the next check — add a
   `fable/tsan_extra.sh` hook like C4's).
4. **CI**: opus-ci runs on `fable-*` since M3: runs 40651865876 (M3) and 40652299456 (M4a) are green (release
   identity ALL OK, FMA 0, `forge_nnue_v3_tests` passed under release / ASan+UBSan / TSan, only the 4 known
   `forge_tests` lines).

## Files of this job

Engine: `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`, `src/search_v3.cpp`, hooks in `src/search.cpp`,
`include/forge/search.hpp`, `src/uci.cpp`, `CMakeLists.txt`. Tools: `tools/nnue_v3_tool.cpp`,
`tools/nnue/fable_nnue_v3.py`, `tools/nnue/fable_nnue_train.py`, `tools/nnue/fable_nnue_uci.py`,
`tools/nnue/fable_nnue_nps.py`. Tests: `tests/nnue_v3_tests.cpp`. Evidence: `fable/logs/`, ideas `fable/IDEA_SOURCE.md`.
Scratch (not committed): nets `F:\opus_scratch\fable\nets\`, `train_m3\`, `train_m4\`, positions
`F:\opus_scratch\fable\parity\`, builds `F:\opus_scratch\build\fable\` (`forge_fable_m2.exe` = final engine).

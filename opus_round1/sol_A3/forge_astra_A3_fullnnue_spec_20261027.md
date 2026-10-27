# Astra A3 — Full-NNUE spec "FN1": network, file format, evaluation order, incremental plan, engine plan (2026-10-27)

Status: design plus an offline CPU pipeline (trainer -> converter -> reference evaluator) and a synthetic smoke
net. **No engine patch, no file in the lock tree, nothing queued on the GPU, no strength claim (UNPROVEN).** The
engine integration is a later job after Code Review of A2 and this spec. Every number below comes from a log in
`logs/` (named) or is labelled ESTIMATE.

## 0. Summary
- **Network FN1** = A2's king-bucket layout M4 (mirrored, 4 blocks) x 768 inputs -> feature transformer H = 256 per
  perspective (int16 weights / 4096, float32 accumulator, exact) -> SCReLU -> per output bucket (8, by piece
  count): 512 -> 16 -> CReLU -> 32 -> CReLU -> 1, all float32 -> centipawns = out x 400 / 2.25. A stand-alone
  evaluation (no HCE term).
- **File format FORGEFN1** (section 3): fixed 256-byte header with both maps, int16 feature transformer, float32
  dense layers, FNV-1a 64 trailer; 1,854,760 bytes at the production sizes.
- **Exactness**: incremental update, refresh-cache rebuild and full refresh give identical float32 bits by
  construction (section 4.2); the dense layers have one normative float32 order (16 lanes, no FMA), which the
  reference evaluator implements, so a later engine kernel can be checked against it bit for bit.
- **Incremental plan** (section 5): per-perspective lazy accumulators; replay while the own-king key holds;
  rebuild through a per-worker refresh cache when it changes. Verified in the reference evaluator on 200,000
  positions with 0 mismatches.
- **UseFullNnue = 0 keeps the residual net** (section 6): compile flag `FORGE_FULL_NNUE` absent = no code; flag
  present + option 0 = the lock's evaluation path untouched behind one cold `[[unlikely]]` branch.
- **Acceptance** (section 9): parity 2 x 1000 positions within 0.05 cp (measured max 0.000032 cp), 200k
  incremental positions 0 mismatches, fixed-seed rerun reproduces the smoke net's sha256, planted bugs caught,
  no engine or lock-tree file changed.

## 1. Reused work (not redone)
| job | what A3 reuses |
|---|---|
| A2 (`opus-sol-A2` 3da8ece4) | layout M4 and its numbers (refresh rate, data per bucket, footprint, NPS ESTIMATE) |
| C4 (`opus-C4` 23750a76) | feature definition, half-board maps, factoriser + QAT idea, refresh cache design, fail-loud UCI rule, layout technique for an OFF-default dispatch |
| C5 (`opus-C5` 57066d2c) | output buckets by piece count, map (pieces - 2) / 4 |
| O4 (`opus-O4` 348d8607) | stand-alone evaluation (`PureNnue`), the measured HCE cost (759 vs 526 ns per ply, O4 REPORT.md "NPS") |
| S09fix (97193476), S21 (f7731fe8) | context only, no code used: trainer with 8 heads and holdout checks; int16 range study (why accumulators stay float) |

A3's files are new and stand alone (`opus_round1/sol_A3/`); none of them imports C4/C5/O4 code.

## 2. Network FN1

| part | definition | production size |
|---|---|---|
| inputs | per perspective p: 768 piece-square features (kings included) in the king block of p's own king; mirrored layout | KB = 4 blocks (A2's M4 map `0011 0011 2222 2222 3333 3333 3333 3333`) |
| feature transformer | acc_p = b + sum of the weight columns of the active features; weights and bias int16 / 4096 | H = 256 |
| FT activation | SCReLU(x) = clamp(x, 0, 1)^2, float32 | |
| dense input | x = [SCReLU(acc_stm), SCReLU(acc_other)], 2H values, side to move first | 512 |
| output bucket | ob = output_map[min(pieces, 32)], pieces = occupied squares incl. kings; default (pieces - 2) / 4 clamped to 0..7 | OB = 8 |
| hidden layer 1 | h1 = CReLU(W1[ob] x + b1[ob]), CReLU(x) = clamp(x, 0, 1) | L1 = 16 |
| hidden layer 2 | h2 = CReLU(W2[ob] h1 + b2[ob]) (absent when L2 = 0) | L2 = 32 |
| output | out = w3[ob] . h2 + b3[ob] (sigmoid units, K = 2.25) | 1 |
| centipawns | cp = trunc(clamp((out x 400) / 2.25, -30000, 30000)) in float32, as the lock's `nnue::evaluate` | |

Parameters at the production sizes: feature transformer 4 x 768 x 256 + 256 int16, dense layers 8 x (16 x 512 + 16
+ 32 x 16 + 32 + 32 + 1) float32 = 70,280 floats (the file sizes in section 3 add up to the converter's 1,854,760
bytes, `logs/convert_*.log`). All sizes are header fields: KB 1-64 with any 64-entry map, H a multiple of 16 up to
2048, L1 / L2 multiples of 16 up to 256 (L2 = 0: one hidden layer), OB 1-16 with any 33-entry map.

Why this shape: the king buckets per A2; the hidden layers and output buckets give the net the capacity the
residual design borrowed from the HCE; O4 measured the HCE at about 31% of the evaluation cost per ply, which a
stand-alone net no longer pays, while L1 adds 16 x 512 float multiplies and adds per evaluation. Neither cost is
measured here; the engine job must measure NPS.

## 3. File format FORGEFN1 (little-endian)

| offset | type | field | rule checked at load (reject the file otherwise) |
|---|---|---|---|
| 0 | char[8] | magic `FORGEFN1` | exact |
| 8 | u32 | version | 1 |
| 12 | u32 | header bytes | 256 |
| 16 | u32 | inputs per king block | 768 |
| 20 | u32 | H | multiple of 16, 16..2048 |
| 24 | u32 | KB king blocks | 1..64 |
| 28 | u32 | flags | bit0 = king mirror; other bits 0 |
| 32 | u32 | OB output buckets | 1..16 |
| 36 | u32 | L1 | multiple of 16, 16..256 |
| 40 | u32 | L2 | 0, or multiple of 16 up to 256 |
| 44 | u32 | FT activation | 1 = SCReLU |
| 48 | u32 | hidden activation | 1 = CReLU |
| 52 | f32 | FT scale | 4096 |
| 56 | f32 | sigmoid K | 2.25 |
| 60 | u8[64] | king map: own-king square in the perspective frame (rank-flipped for Black) -> block | every entry < KB |
| 124 | u8[33] | output map: piece count 0..32 -> bucket | every entry < OB |
| 157 | u8[99] | reserved | all zero |
| 256 | i16 | ft_w[KB][768][H] (one H-column per feature, as the lock's w1) | |
| | i16 | ft_b[H] | |
| | f32 | l1_w[OB][L1][2H], l1_b[OB][L1] | finite |
| | f32 | l2_w[OB][L2][L1], l2_b[OB][L2] (only if L2 > 0) | finite |
| | f32 | out_w[OB][L2 or L1], out_b[OB] | finite |
| end | u64 | FNV-1a 64 of all preceding bytes | equal |

The file size must equal the size implied by the header (checked before any weight is read, as C4's v2 loader
does); the float blocks start 4-byte aligned because H is a multiple of 16. The converter writes no timestamps or
paths, so a checkpoint always converts to the same bytes. Engine loader rule (later job): any failed check is a
fail-loud error (section 6), never a silent fallback.

## 4. Evaluation semantics (normative; `forge_astra_A3_refeval_20261027.py` implements them)

### 4.1 Features
For perspective p (White 0, Black 1), piece code c (1..6 White P N B R Q K, 7..12 Black) on square s (a1 = 0):
```
r     = s ^ (56 if p else 0)                       kr = own_king_square ^ (56 if p else 0)
flip  = 7 if (mirror and kr % 8 >= 4) else 0       key = (king_map[kr], flip)
index = king_map[kr] * 768 + ((0 if colour(c) == p else 1) * 6 + type(c) - 1) * 64 + (r ^ flip)
```
Training data only: a malformed record without an own king uses square 0, with several kings the first on a1..h8
(C4's convention; the synthetic data32 sample has such boards; the engine never sees them).

### 4.2 Feature transformer: float32, exact
`acc = ft_b / 4096 + sum of ft_w columns / 4096`, in float32. Every value is an integer multiple of 2^-12; with
int16 weights and at most 32 pieces, |bias| + 32 x 32767 < 2^24, so every partial sum is exactly representable
and float addition is exact in any order: an incremental update (`parent - removed + added`), a refresh-cache
rebuild and a refresh from scratch give identical bits (the argument of
`CR_PASS_nnue_h256_e12_lock_net_float_accumulator_analysis.txt` item 3, which holds per king block). No int16 or
int32 accumulator, no int16 inference path (rule "H256 stays float").

### 4.3 Dense layers: one float32 order
For y = W x + b with n_in a multiple of 16 (2H, L1, L2 all are):
```
lane[j] = 0 for j in 0..15
for i in 0, 16, 32, ..., n_in - 16:  for j in 0..15:  lane[j] = lane[j] + (x[i + j] * W[o][i + j])   (two roundings, no FMA)
y[o] = (((b[o] + lane[0]) + lane[1]) + ...) + lane[15]
```
This is the lock's output-layer association (`src/nnue.cpp` `evaluate`: 16 independent partial sums, then one
ordered sum) extended to every dense layer, so SSE, AVX2, AVX-512 and scalar code give the same bits without
`-ffast-math`. The SCReLU input is `(a * a)` rounded, then multiplied by the weight. Skipping inputs that are exactly
zero (common after SCReLU) does not change any bit: a lane starts at +0 and adding a signed zero never changes a
sum, so a sparse kernel stays bit-identical (and the reference can check that). Clamps are
`min(max(x, +0), 1)` with x86 `maxps(x, +0)` semantics (a zero of either sign becomes +0; numpy's `clip` does
the same, checked with numpy 1.26.4); accumulators and dense outputs are never -0 anyway, because a round-to-nearest
sum of terms that are not all -0 is never -0. Build flags as the lock: `-ffp-contract=off -fno-fast-math`, FMA
count 0.

### 4.4 Output
`cp = trunc(clamp(float32(float32(out * 400) / 2.25), -30000, 30000))`; the search clamps to +-(MateInMaxPly - 1)
exactly like the lock's residual path does today.

## 5. Incremental-update plan (engine)

Per search-stack ply: `acc[2][H]` float32 (2 KiB, the existing `SearchStack::accumulator` size at H = 256),
`valid[2]` (one flag per perspective, replacing the single flag) and `key[2]` (block, flip of each side's own
king). `record_move` keeps the lock's dirty pieces (`nnue::dirty_pieces`, unchanged) and invalidates both halves.

`accumulator(p)` at the evaluated ply:
1. `valid[p]` -> use it.
2. Find the nearest ancestor j with `valid[p]`. If `key[p]` is the same at j and here: replay the dirty pieces of
   plies j+1 .. here with this key (king moves inside one key are ordinary feature changes); every replayed ply whose
   own key equals this key becomes valid, others stay invalid.
3. If the key differs, or no ancestor is valid (search root): rebuild p at this ply through the **refresh cache**:
   per worker one entry per (p, key) = float32 accumulator + the 12 piece bitboards it was built for; subtract the
   columns of pieces only in the entry, add those only on the board, copy into the ply, store the board in the
   entry. Cold entries are the bias with empty bitboards (a full refresh). Entries are reset when a net is loaded
   (and may be kept across moves of a game: correctness does not depend on what an entry holds).
4. Null move: no dirty pieces, keys unchanged. Threads: one cache per worker; the net is read-only and shared.

This is A2's "jump" variant: at bench d20 it needs 3.5-6.2% fewer rebuilds than replaying ply by ply and rebuilds
about 6 columns instead of about 14 (A2 `logs/kbstats_tables.md`). Memory per worker for M4: 2 x 8 keys x
(1024 + 96) B = 17.5 KiB of cache (A2 `logs/footprint.log`). The reference evaluator's `LazyEvaluator` and
`RefreshCache` implement exactly these steps; section 9 has the 200k-position check.

## 6. Engine integration plan (later job, not done here) — how UseFullNnue = 0 keeps the residual net

- **Compile flag** `FORGE_FULL_NNUE`: without it no FN1 code exists (bench, perft, FMA and codegen are the lock's).
- **UCI** (flag builds only): `UseFullNnue` (spin 0-1, default 0; `true`/`false` also accepted, as O4's `PureNnue`)
  and `FullNnueFile` (string, default `<empty>`).
- **Option 0 = the lock's path, unchanged**: `Worker::static_evaluate` gets one cold
  `if (options::use_full_nnue) [[unlikely]] return static_evaluate_full(board, ss);` at the top (FN1 code in its own
  section, C4's technique; a layout pad if the hot functions move). The HCE + compiled-in residual net
  (`src/nnue_weights.inc`, `nnue::residual()`) and `record_move` stay as they are; `UseNNUE false` still means HCE
  only. Proof obligations for that job: with the flag ON and the option 0, bench d11-d22, perft, kiwipete equal the
  lock pins, FMA 0, hot-function codegen equal to the lock (or a stated, measured change), ctest only the 4 known
  lines, ASan/UBSan/TSan clean in CI.
- **Option 1**: evaluation = FN1 alone. It needs a loaded, valid `FullNnueFile`; otherwise the C4 fail-loud rule
  applies (ERROR at once, exit status 2 at the next isready / go / bench, never a silent fallback). One network path
  at a time: `UseFullNnue 1` together with a C4/C5/O4 v2 request (`NNUEFile`, `NNUEKingBuckets`,
  `NNUEOutputBuckets`, `PureNnue`) is an error. An `info string FullNnue: active: <file> ... fnv1a <checksum>` line at
  every `readyok` proves which net plays. Changing the option clears the hash (stored static evaluations belong to
  the other evaluator).
- **Tests for that job**: engine vs this reference evaluator on 10,000 positions, bit for bit (both accumulators,
  float32 output, cp) — possible because section 4.3 fixes the order; incremental == refresh in real search walks
  (C4-style, >= 100k plies); planted bugs; NPS d16/d20 with the real net (advisory). Gate only after CR review; no
  net from this pipeline is queued on the GPU without a CR queue diff and a crew vote.

## 7. Trainer `forge_astra_A3_trainer_20261027.py`
- Data as v3b: FPOS `.pos` files (`--train`, `--holdout` whole files; holdout files are removed from the training
  set), optional `--hce-dir` only for the HCE-alone baseline line; the loader functions keep v3b's checks (header,
  meta 255 = bad record, HCE count / -32768). Refuses an empty training set, a holdout smaller than one batch,
  an existing run folder, run folders named `runs_*` / `smoke_kb*` and script names containing `train_resid`.
- Model: `FullNNUE` (section 2), factoriser on by default (`--king-factor 1`: a shared 768 x H block added to every
  king block during training, folded on export), QAT on the folded feature transformer (v3b's rounding: half away
  from zero, clamp to int16; the forward value equals the grid value exactly), dense layers float32.
- Loss and schedules as v3b: MSE(sigmoid(out), blend x sigmoid(K x score / 400) + (1 - blend) x stm result),
  linear blend ramp `--blend-start` -> `--blend-end`, lr warmup then cosine to `--min-lr-frac`, validation subset by
  `default_rng(12345)`, shuffles by `default_rng(seed x 1000 + epoch)`.
- Determinism: `torch.set_num_threads(--threads)` (1 by default), `torch.use_deterministic_algorithms(True)`,
  synchronous batches, stock Adam (`foreach=False`). Same seed and inputs -> same `.pt` and `.fnn` bytes (section 9).
- Output per epoch: `epochNNN-stepXXXXXXXXX.pt` (config, model, optimizer) and `.json` (metrics). CPU only; a GPU
  version would add v3b's device selection and Adam variant and must first pass the same parity tests. With M4 the
  dense one-hot input at bs 16384 is 192 MiB per perspective (A2 `logs/footprint.log`).

## 8. Converter and reference evaluator
- `forge_astra_A3_converter_20261027.py convert <epoch.pt> <out.fnn>`: folds the factoriser with the trainer's
  float32 operation, quantises exactly as the trainer's QAT, writes FORGEFN1; `info <net.fnn>` prints the header and
  checks the checksum.
- `forge_astra_A3_refeval_20261027.py eval <net.fnn> <fens> [n]`: prints the engine-order float32 output, cp and a
  float64 reference per FEN. As a library: `Net`, `refresh`, `apply_changes`, `RefreshCache`, `LazyEvaluator`,
  `evaluate_acc` (engine order), `evaluate_acc_f64`, `chess_changes` (python-chess move -> the lock's dirty pieces).

## 9. Acceptance evidence (scripts `a3_smoke_train.sh`, `a3_acceptance.sh`; logs in `logs/`)

| # | acceptance line | result | evidence |
|---|---|---|---|
| 1 | trainer -> converter -> reference evaluator agree within a stated float tolerance on 1k positions | **PASS** on 1000 synthetic (data32 holdout h000) + 1000 real self-play positions: file int16 == trainer QAT integers 786,688/786,688 (0 mismatching), dense blocks bit-equal 6/6; output bucket 1000/1000 + 1000/1000; both accumulators float32 bit-exact 1000/1000 + 1000/1000; output within the stated tolerance 0.05 cp 1000/1000 + 1000/1000, measured max 0.000032 cp (both sets); integer cp equal after truncation 2000/2000; reference engine order vs float64 max 0.000022 / 0.000028 cp | `logs/parity_1k.log` |
| 2 | in the reference evaluator, incremental == full refresh on 200k positions, 0 mismatches | **PASS**: 200,000 evaluated positions, 0 accumulator, 0 output, 0 piece-code mismatches; walks of 171,316 moves and 154,798 takebacks with 80,909 king moves, 32,098 own-king key changes, 426 castles, 298 en passant, 913 promotions, 10,867 captures, 6,484 null moves; lazy paths: 195,915 replays (227,134 plies), 26,219 key rebuilds through the refresh cache, 4,178 root rebuilds, 173,688 already valid | `logs/incremental_200k.log` |
| 2b | the same without the refresh cache (every rebuild from scratch) | **PASS**: 50,000 positions (seed 2), 0 / 0 / 0 mismatches; 8,274 key changes, 98 castles, 50 en passant, 221 promotions, 1,587 null moves; 6,894 key rebuilds and 1,092 root rebuilds, all from scratch | `logs/incremental_50k_nocache.log` |
| 3 | reruns with a fixed seed reproduce the smoke net's sha256 | **PASS**: seed 7 twice -> `epoch003.fnn` sha256 `f5ec8bd5fa9d1a0c45906f4d1590b84872fdede263fc953c93d37b733acc44e0` both times, and the three `.pt` checkpoints are byte-identical too; control seed 8 -> `d06e70fa82d6af987308bc4101413a8d7456397cda33e8726fc85812173e3143` (different) | `logs/train_a3smoke2_*.log`, `logs/convert_a3smoke2_*.log`, full console `logs/smoke_train_console.log` |
| 4 | no engine patch and no file inside the lock tree | **PASS**: at the repository root, `git diff --stat 294dbed HEAD -- src include tests tools bench CMakeLists.txt` and `git status --short` of those paths are empty; the branch differs from the lock source only by the baseline/CI files and (after the A3 commit) `opus_round1/sol_A3/` | `logs/no_engine_change.log` |
| 5 | offline only, nothing queued; no strength claim | **PASS**: CPU, one thread, nice 19; nothing written to `F:\forge_nnue_train`; supervisor.log "adopted running job" lines 7 before and after every trainer start and around the acceptance runs | `logs/smoke_train_console.log`, `logs/acceptance_supervisor.log` |
| + | planted bugs make the tests fail | **PASS**: both baselines pass, and all 8 planted bugs fail their test: reference without mirroring (accumulators 90/200 and 16/200, up to 154 cp), output bucket + 1 (up to 212 cp), dense layer without lane 15 (up to 50 cp), converter without the factoriser (784,209 of 786,688 ints wrong), lazy evaluator replaying across a king-key change (16,176 mismatches in 20,000), refresh cache forgetting its board (19,909), castling without the rook (1,365 accumulator and 1,618 piece-code mismatches), en passant removing the pawn on the target square (277 / 310). A first run with 4,000-position walks reached no en-passant evaluation and missed the last bug (`logs/mutation_check_first_run_4000pos.log`); the walks are now 20,000 positions (17 en passant, 50 castles) | `logs/mutation_check.log` |

## 10. Smoke net (pipeline check only)

- File: `smoke_net/a3_smoke_FN1_M4_H256_L16x32_OB8_seed7_epoch003.fnn` (= `F:\opus_scratch\sol_A3\a3smoke2_seed7_r1\epoch003.fnn`),
  1,854,760 bytes, sha256 `f5ec8bd5fa9d1a0c45906f4d1590b84872fdede263fc953c93d37b733acc44e0`, FNV-1a `05d4be09a2c5607a`.
- Config: FN1 with M4 (mirrored 4 blocks, factoriser), H 256, L1 16, L2 32, 8 output buckets; data
  `LA/5_nnue/sample_data/data32_sample/data32_sample_50k` (train t00000-t03000 = 200,000 positions, holdout h000 =
  50,000), 3 epochs x 195 steps, batch 1024, lr 1e-3 (warmup 20, cosine), blend 1.0 -> 0.6, seed 7, 1 thread.
- Training log (`logs/train_a3smoke2_seed7_r1.log`): train MSE 0.073705 -> 0.059021 -> 0.047618 while the holdout
  teacher MSE goes 0.083475 -> 0.084637 -> 0.087973: the synthetic scores do not depend on the boards, so the net can
  only memorise (O4 saw the same on this sample). It proves the pipeline, nothing about chess.
- Reproduce: `bash a3_smoke_train.sh <scratch> <logs> <new prefix>` (about 3 minutes on one thread).

## 11. Open items / UNVERIFIED
- No net trained on real data; the smoke net is a pipeline check on synthetic boards with board-independent
  scores (its holdout loss rises while the training loss falls: it can only memorise). No strength claim.
- NPS of FN1 in the engine: unmeasured (needs the engine job). The L1 layer's cost is an open question; a sparse
  L1 kernel is allowed by section 4.3 without changing bits.
- The trainer is CPU-only and has not run on DirectML.

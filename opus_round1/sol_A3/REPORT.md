# A3 [Astra] Full-NNUE design + trainer + converter + reference evaluator + smoke net (no engine integration) — DONE

Branch `opus-sol-A3` = `d4f4312` + `03705ecd` (CI baseline 0d99f02 cherry-picked) + `5a7e82d0` "[A3] Full-NNUE FN1 spec, trainer, converter, reference evaluator, smoke net and tests (no engine integration) [skip ci]" + the REPORT commit. Job folder `opus_round1/sol_A3/`. UNPROVEN, no strength claim, CPU only, nothing queued. Work and results by a sub-agent; this report text is its hand-back.

The FN1 net uses:
- A2's M4 king buckets × 768 inputs;
- a feature transformer of width 256 with int16/4096 weights and an exact float32 accumulator, then SCReLU;
- 8 output buckets by piece count, each 512 → 16 → CReLU → 32 → CReLU → 1, in float32;
- a stand-alone evaluation (no HCE).

The file format is FORGEFN1: 256-byte header, int16 feature transformer, float32 dense layers, FNV-1a trailer; 1,854,760 bytes.

| line | result | evidence |
|---|---|---|
| Spec md: layout, net file format, UseFullNnue=0 keeps the residual net, incremental plan | DONE: `forge_astra_A3_fullnnue_spec_20261027.md` sections 2-6. The spec fixes one float32 summation order (16 lanes, no FMA) so a later engine kernel can be checked bit for bit | spec |
| New trainer (v3b loader conventions + FPOS), converter, reference evaluator | DONE: `forge_astra_A3_trainer_20261027.py` (no train_resid in the name; run only as `F:\opus_scratch\sol_A3\opus_nnue_smoke_a3trainer.py`), `forge_astra_A3_converter_20261027.py`, `forge_astra_A3_refeval_20261027.py` (pure Python + numpy) | files |
| trainer → converter → reference agree within a stated tolerance on 1k positions | PASS, tolerance 0.05 cp: 1000 synthetic + 1000 real positions. FT ints 786,688/786,688 equal; dense blocks bit-equal 6/6; output bucket 2000/2000; both accumulators float32 bit-exact 2000/2000; outputs within tolerance 2000/2000, max 0.000032 cp; integer cp equal 2000/2000 | `logs/parity_1k.log` |
| Reference evaluator: incremental == full refresh on 200k positions, 0 mismatches | PASS: 200,000 positions, 0 accumulator, 0 output and 0 piece-code mismatches. The walks covered 32,098 king-key changes, 426 castles, 298 en passant, 913 promotions and 6,484 null moves, with 26,219 cache rebuilds. Without the cache: 50k positions, 0 mismatches | `logs/incremental_200k.log`, `logs/incremental_50k_nocache.log` |
| Fixed-seed rerun reproduces the smoke net's sha256 | PASS: seed 7 twice gives `epoch003.fnn` sha256 f5ec8bd5fa9d1a0c45906f4d1590b84872fdede263fc953c93d37b733acc44e0 both times, and all three .pt checkpoints are byte-identical. The seed-8 control gives d06e70fa… (different) | `logs/smoke_train_console.log` |
| No engine patch, no file in the lock tree | PASS: `git diff --stat 294dbed HEAD -- src include tests tools bench CMakeLists.txt` is empty at the repo root, before and after the A3 commit | `logs/no_engine_change.log` |
| Offline only, nothing queued, no strength claim | PASS: CPU, 1 thread, nice 19; nothing written to `F:\forge_nnue_train` | `logs/acceptance_supervisor.log` |
| Planted bugs | PASS: 8/8 caught (no mirroring, output bucket +1, dense layer missing a lane, converter without factoriser, replay across a key change, cache forgets its board, castling without the rook, wrong en-passant square); both baselines pass | `logs/mutation_check.log` |

## Findings
- **Smoke net:** `smoke_net/a3_smoke_FN1_M4_H256_L16x32_OB8_seed7_epoch003.fnn` (1,854,760 B, sha256 f5ec8bd5…). Trained on data32 t00000-t03000 (200k positions), holdout h000, 3 epochs × 195 steps.
  - Train MSE goes 0.0737 → 0.0476 while the holdout rises 0.0835 → 0.0880. The synthetic scores do not depend on the board, so this is a pipeline check only.
- **Exactness:**
  - Trainer, converter and reference accumulators agree bit for bit, because the QAT weights sit on the 2^-12 grid.
  - The trainer's float32 GEMM vs the reference's engine order differs by at most 0.000032 cp.
- **Incremental plan** (spec section 5): per-perspective validity and keys; replay while the own-king key holds; otherwise rebuild at the evaluated ply through a per-worker (perspective, key) refresh cache.
- **Engine plan** (spec section 6):
  - Compile flag `FORGE_FULL_NNUE`; without it there is no code.
  - `UseFullNnue` is a spin 0-1 defaulting to 0. At 0 the lock's evaluation path is untouched behind one cold `[[unlikely]]` dispatch.
  - Value 1 needs a valid `FullNnueFile` (C4 fail-loud rule) and is exclusive with the v2 options.
  - The engine job would test bit-exactness against this reference evaluator.

## Process notes (from the sub-agent's hand-back)
- **The first smoke run trained on nothing.** Git Bash does not convert a `/f/...` path that contains `*`, so the glob
  matched no files and the trainer ran 0 steps, which made its "reproducible" sha trivially true. The trainer now
  refuses an empty training set, the run was repeated with relative paths, and the invalid logs are kept in
  `logs/invalid_empty_trainset_run1/`.
- **The first planted-bug run** (4,000-position walks) never reached an en-passant evaluation, so it missed that bug;
  the walks are now 20,000 positions and catch all 8 (`logs/mutation_check_first_run_4000pos.log` kept).
- **The first "no engine change" check** ran from the job folder, where its paths match nothing. It now runs at the
  repo root (`logs/no_engine_change.log`); `logs/acceptance_console.log`'s final git block is the old check.

## Left / UNVERIFIED
- No net trained on real data.
- Engine NPS of FN1 unmeasured (the L1 cost is open).
- Trainer is CPU-only and has not run on DirectML.
- The 12.65 MB .pt checkpoints stay in `F:\opus_scratch\sol_A3\a3smoke2_*` (sha256 in `logs/smoke_train_console.log`).

Machine exclusive: no.
Supervisor check: "adopted running job" stayed at 7 before and after every trainer start (3 smoke runs, 1 trial, 1 guard check) and the acceptance runs; latest line 2026-10-27T08:55:34.

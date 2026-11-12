# JOB E - Standalone H512 network and training recipe - STATUS

**Last update:** 2026-11-11 17:32 PC clock. **Job start:** 16:53 (planning 16:53-17:10, plan approved 17:10, work from 17:11).
**Elapsed:** 0 h 39 min of about 10 h.
**Branch:** `fable/standalone-h512-20261111`, cut from Job D's head `1508c13cdfb87894f01cf3a95fd87b9ad3a4cef0`,
which descends from the lock `lock/combo29-20261110` = `16833ecc03b425586f91f4c8834dea8807bf4c22`.
**Checkout:** `D:\forge_jobs_20261111\h512E` (`core.autocrlf=false`).

## State: recipe pilots running on the GPU; engine port in progress

## Completed
1. **Identities.** Lock source manifest 20/20 on the lock tree. s198 `nnue_weights.inc` md5 `22b4b9e2c61b37c0450f13a3a92c19b3`.
   Lock exe `forge_clang_combo29_trial_w6.exe` md5 `c0051c99695f48bf93272d96fe7548c3`.
2. **FB2 warm start verified by content** (`results/step1/`):
   - `F:\opus_scratch\fable\fb2\train_j1b\ckpt.pt` md5 `238d53d830cb5af153e7ba08cb3987b3`, sha256 `e1b375e0c056956d...`: step 93,000, seen 761,856,000, best 0.014713967976147187 at step 87,164.
   - `best.fnn3` (= `ck15_step0087164.fnn3`) md5 `1036f0ac02567d1c5ab1a6861786cd91`: re-scored on the FB2 200k holdout = 0.014713967976147187, the published value.
   - Re-exporting the checkpoint gives FB2's `net.fnn3` byte for byte (md5 `e96dd27c0887425109af55162a045d76`).
   - All 130 FB2 data files match their manifest sha256 (271,830,023 training rows, 200,000 holdout rows).
   - `status.json` of the run equals the copy on branch `fable-fb2-j1` (md5 `8a1d5f19...`). `FABLE_REPORT_FB2.md` there has md5 `9e40983e6a44ed6283c0110d2df243cd`.
3. **GPU trainer** `h512/train/train_h512_gpu.py` (own code; FB2 model, QAT, exporter; R7 Triton kernel imported, not copied). Checks in `results/step1/selfcheck_trainer.json` and `results/step2/`:
   - GPU feature extraction equals FB2's numpy reference on 200,000 of 200,000 rows (both sides to move, all 8 king buckets for both perspectives, all 8 output buckets).
   - GPU integer scorer equals FB2's numpy scorer (difference 1.7e-18).
   - Triton forward equals plain torch within 0.0007 cp. Gradients agree to 3e-6 on float weights. On quantised weights they differ where an accumulator sits exactly on the clamp boundary (0.007 % of values; cosine 0.9996), which is a tie in the derivative, not an error.
   - Fake-quantised float against integer: max 1.02 cp, mean 0.51 cp. Unquantised float against integer: max 67.7 cp, mean 7.65 cp.
   - Throughput: **about 2.0M positions/s** at batch 8192 (1.93M at 16384), H512 on the RX 7900 XT. Batch 8192 kept.
   - Stop and resume: identical data order (index checksums equal at every logged step), final selection loss equal to 3e-7. Training arithmetic is not bit-exact between runs because the kernel's backward pass uses atomics.
4. **Splits frozen** (`manifests/splits_manifest.json`, tool `train/make_splits.py`, 30 s):
   - Training: FB2's 64 shards, 271,830,023 rows, 0 duplicate positions inside.
   - Selection: 2,000,000 rows from 013/014 (pool 16,388,575; 1,352 duplicates inside removed; 0 also in training), seed 2026111101.
   - Final test: 2,000,000 rows from 036/038 (pool 20,000,000; 1,613 duplicates inside, 7,315 also in training and 392 also in 013/014 removed), seed 2026111102. Not scored yet. The scorer refuses it without `--final-test-unlock` and logs each access.

## Running now
- **Recipe pilots**, six arms, 400M presentations each from the FB2 checkpoint (fresh Adam, same seed and data order):
  `h512/train/run_pilots.sh`, plans `h512/train/plans/pilot_P0..P5.json`, runs `_work\runs\pilots\`.
  The pilot length was set to 400M (plan said 100M) after measuring throughput and before any pilot result.
  Started 17:28:11; about 3.5 min per arm.
- Owned processes: bash launcher pid 14792; trainer python pids 11076 (venv launcher) and 15760.

## Pending
- Engine port of NNUE v3 onto combo29 behind `FORGE_NNUE_V3`, v3 tool, parity on at least 14,000 positions (before the main run).
- Reference scores of s198 + HCE and FB2 best on the selection set.
- Staged training to 1B / 2B / 4B / 7.4B cumulative presentations with the fixed stop rule (2e-5 between stage ends).
- Freeze, final test once, PGO build, HCE-zero check, quiet ABBA NPS, 3,000-game match, REPORT.md.

## Deviations and observations
- Engine NNUE's v3 pack and `fable_primary_full.md` are not on the PC and the owner does not have them. Own trainer and config instead (approved).
- `F:\nnue_pytorch\venv\Lib\site-packages\_rocm_sdk_devel\include` and `\lib` deny access to this account, so Triton could not compile its HIP helper. No permission was changed. The trainer adds the readable `_rocm_sdk_core\include` to Triton's include list inside its own process.
- E: is a 3 GB volume (2.9 GB free); it cannot meet a 20 GB floor and is not written to.
- The owner's pressure cleanup acts on its own folders when D: or F: falls below 30 GiB. D: is at 34.3 GiB, so this job keeps its D: footprint under 2.5 GiB (now 0.2 GiB).
- One planning-time text search ran over all of `C:\Users\Administrator\grok-pc`, including `forge_push\locks` (read-only, no result from there). Not repeated.

## Free space (17:27)
C: 36.4 GiB, D: 34.3 GiB, F: 32.7 GiB.

## Next command
`bash h512/train/run_pilots.sh` is restartable (finished arms are skipped). After it: rank arms on `select_2m.mse_b0.6`, write `h512/train/stage1_config.json`, start the staged run once parity has passed.

## Blockers
None.

# JOB E - Standalone H512 network and training recipe - STATUS

**Last update:** 2026-11-11 17:59 PC clock. **Job start:** 16:53 (planning 16:53-17:10, plan approved 17:10, work from 17:11).
**Elapsed:** 1 h 06 min of about 10 h.
**Branch:** `fable/standalone-h512-20261111`, cut from Job D's head `1508c13cdfb87894f01cf3a95fd87b9ad3a4cef0`,
which descends from the lock `lock/combo29-20261110` = `16833ecc03b425586f91f4c8834dea8807bf4c22`.
**Checkout:** `D:\forge_jobs_20261111\h512E` (`core.autocrlf=false`).

## State: staged main run training on the GPU (started 17:56:09); engine path ported and parity-checked

## Completed
1. **Identities.** Lock source manifest 20/20 on the lock tree. s198 `nnue_weights.inc` md5 `22b4b9e2c61b37c0450f13a3a92c19b3`.
   Lock exe `forge_clang_combo29_trial_w6.exe` md5 `c0051c99695f48bf93272d96fe7548c3`.
2. **FB2 warm start verified by content** (`results/step1/`): `ckpt.pt` md5 `238d53d830cb5af153e7ba08cb3987b3` (step 93,000,
   seen 761,856,000); `best.fnn3` md5 `1036f0ac02567d1c5ab1a6861786cd91` re-scores to the published 0.014713967976147187;
   re-export of the checkpoint equals FB2's `net.fnn3` byte for byte; all 130 FB2 data files match their manifest.
3. **GPU trainer** `h512/train/train_h512_gpu.py`, note `h512/train/TRAINER_NOTE.md`. Self-checks pass
   (`results/step1/selfcheck_trainer.json`, `results/step2/`). **About 2.0M positions/s** at batch 8192.
4. **Splits frozen** (`manifests/splits_manifest.json`): training 271,830,023 rows; selection 2,000,000 rows from
   013/014; final test 2,000,000 rows from 036/038 (7,315 rows also in training and 392 also in 013/014 removed from
   its pool). Final test not scored yet.
5. **Engine path** (`results/step3/`): FB1's integer NNUE v3 on combo29 behind `FORGE_NNUE_V3` (default 0).
   - All switches off: the eight lock units preprocess identically to the lock.
   - Parity on 14,000 positions (12,000-FEN set + 2,000 selection rows; both sides to move, all 16 king-bucket x mirror
     cells for both colours, all 8 output buckets): engine tool = in-search static eval = Python integer reference =
     GPU scorer, 0 mismatches; hand-crafted term 0 on every position. Float with fake quantisation vs integer: max
     1.02 cp, mean 0.51 cp. Unquantised float vs integer: max 74.9 cp, mean 7.4 cp.
   - FB1's v3 unit tests on the port: 95,879 checks, 0 failures (scalar = AVX2 = AVX-512; incremental = refresh).
   - Rehearsal PGO build with FB2's best net: coverage proof passes (v3 evaluate 2,562,010 entries; compiled-in net
     and hand-crafted evaluation 0 entries). Informal 4-pair timing: 1.14x the lock's NPS at `bench 20` (different tree).
6. **Reference scores on the selection set** (`results/step4/`), MSE against the 0.6 score / 0.4 result target:
   s198 + HCE **0.014311**; HCE alone 0.017044; FB2 best net 0.014640; FB2 final net (the warm start) 0.014653.
7. **Recipe pilots** (`results/step5/pilot_table.md`), 400M presentations each from the FB2 checkpoint, same seed and order:

   | Arm | Peak LR | alpha | Sampling | Selection loss at the end |
   |---|---|---|---|---|
   | P2 | 5e-4 | 0.25 | natural | **0.014496** |
   | P0 existing recipe restarted | 1e-3 | ramp 0.1 to 0.4 | natural | 0.014507 |
   | P1 | 5e-4 | 0.4 | natural | 0.014663 |
   | P5 | 5e-4 | 0.4 | equal weight per phase bin | 0.014680 |
   | P3 | 5e-4 | 0.0 | natural | 0.014946 |
   | P4 | 5e-4 | 0.5 | natural | 0.014974 |

   Rule fixed before the pilots: lowest wins, arms within 1e-5 are tied and a tie goes to the existing recipe.
   P2 is ahead of P0 by 1.08e-5, just outside the tie band, so **P2 is the recipe**. One seed each; weak evidence.

## Running now
- **Staged main run**: `h512/train/run_main.sh`, plan `h512/train/stage1_config.json` (md5 `bd68c7c7881028b47f95f9c497d9ccb1`),
  run folder `_work\runs\main\`. Recipe P2. Stage ends at 1B / 2B / 4B / 7.4B cumulative presentations, then 12B and 20B
  only while the rule allows. Checkpoint every 250M.
- Stop rule (fixed before the run): from the 2B stage on, stop at the first stage end that improves the best
  selection loss by less than 2e-5. Also stop if 6 h 45 min of the budget is used (23:38).
- **Change to the approved plan, declared at 17:55 before any staged result:** stages to 12B and 20B were added
  because throughput is 2.0M/s (7.4B needs about one hour, not 4.5 h). The brief asks for at least about 7.4B and
  more only while selection results justify it; the same stop rule decides.
- Owned processes: bash launcher pid 15584; trainer python pids 13060 (venv launcher) and 12160.
- Expected stage ends (no holds): 2B 18:07, 4B 18:24, 7.4B 18:53, 12B 19:32, 20B 20:40.

## Pending
- Freeze the candidate on the selection set only; parity on the frozen net; final test once.
- PGO build with the candidate's own workload and coverage proof; HCE-zero check; quiet ABBA NPS.
- 3,000-game match (declared in the plan), then REPORT.md.

## Deviations and observations
- Engine NNUE's v3 pack and `fable_primary_full.md` are not on the PC and the owner does not have them. Own trainer and config instead (approved).
- Pilot length 400M instead of 100M, chosen after measuring throughput and before any pilot result.
- `F:\nnue_pytorch\venv\Lib\site-packages\_rocm_sdk_devel\include` and `\lib` deny access to this account. No permission was changed; the trainer adds the readable `_rocm_sdk_core\include` to Triton's include list in its own process.
- **Cause of Job D's match stalls found:** the owner's `resource_guard.ps1` suspends `fastchess.exe` started from `C:\Users\Administrator\grok-pc\` for about 5 s whenever its thermal latch trips (CPU above 90 C or GPU edge above 83 C). Its log shows such suspensions of the match process at 15:40:15, 16:05:41 and 16:33:09 today, the three bursts Job D reported. This job's match uses the same fastchess, so the same can happen; time losses will be reported by side with a sensitivity figure. The guard is not bypassed.
- GPU memory junction reached 82 C in the pilots (limit for a pause in this trainer: 86 C). No hold so far.
- E: is a 3 GB volume (2.9 GB free); it cannot meet a 20 GB floor and is not written to.
- The owner's pressure cleanup acts on its own folders when D: or F: falls below 30 GiB. D: is at 33.9 GiB, so this job keeps its D: footprint under 2.5 GiB (now 0.4 GiB).
- One planning-time text search ran over all of `C:\Users\Administrator\grok-pc`, including `forge_push\locks` (read-only, no result from there). Not repeated.

## Free space (17:39)
C: 36.3 GiB, D: 33.9 GiB, F: 32.7 GiB.

## Resume point
- Training: `bash h512/train/run_main.sh` resumes from `_work\runs\main\latest.pt` with the same data position. Clean stop: create `_work\runs\main\STOP`.
- After training: pick the checkpoint with the lowest `select_2m.mse_b0.6` in `_work\runs\main\metrics.jsonl`, then the engine steps above.

## Blockers
None.

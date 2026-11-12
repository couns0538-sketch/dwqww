# JOB E - Standalone H512 network and training recipe - STATUS

**Last update:** 2026-11-11 18:22 PC clock. **Job start:** 16:53 (planning 16:53-17:10, plan approved 17:10, work from 17:11).
**Elapsed:** 1 h 29 min of about 10 h.
**Branch:** `fable/standalone-h512-20261111`, cut from Job D's head `1508c13cdfb87894f01cf3a95fd87b9ad3a4cef0`,
which descends from the lock `lock/combo29-20261110` = `16833ecc03b425586f91f4c8834dea8807bf4c22`.
**Checkout:** `D:\forge_jobs_20261111\h512E` (`core.autocrlf=false`).

## State: training finished (stopped at 2.0B by the plateau rule); candidate frozen; the declared 3,000-game match is running

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
   its pool).
5. **Engine path** (`results/step3/`): FB1's integer NNUE v3 on combo29 behind `FORGE_NNUE_V3` (default 0).
   - All switches off: the eight lock units preprocess identically to the lock.
   - Parity on 14,000 positions with FB2's net: 0 mismatches; hand-crafted term 0 on every position.
   - FB1's v3 unit tests on the port: 95,879 checks, 0 failures.
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
8. **Staged run** (`results/step6/`), recipe P2, 17:56:09 to 18:08:18, 1.24B presentations at about 2.0M/s, no hold
   (GPU hot spot max 54 C, memory junction max 81 C).

   | Cumulative presentations | At | Selection loss | FB2 200k holdout |
   |---|---|---|---|
   | 761,856,000 | FB2 warm start (final net) | 0.014653 | 0.014733 |
   | 1,000,005,632 | stage S1 end | 0.014489 | 0.014580 |
   | 1,250,000,896 | S2, learning rate 4.3e-4 | 0.014634 | 0.014729 |
   | 1,500,004,352 | S2, 2.6e-4 | 0.014565 | 0.014628 |
   | 1,750,007,808 | S2, 9.5e-5 | 0.014504 | 0.014594 |
   | 2,000,003,072 | S2, last interval checkpoint | **0.014480** | 0.014567 |
   | 2,000,011,264 | stage S2 end | 0.014481 | 0.014568 |

   **Stopped by the rule fixed in advance:** the 2B stage improved the best stage-end loss by 0.8e-5, below the 2e-5
   minimum. **7.4B was not reached; this is an early stop at 2.0B** (7.36 passes over the 271.8M unique rows).
   The stages to 4B, 7.4B, 12B and 20B did not run.
9. **Candidate frozen 18:09** on the selection set only (`results/step7/FROZEN_CANDIDATE.json`):
   `_work\nets\h512_cand_seen02000003072.fnn3`, md5 `d920a15c5b05040a3ef71a872192ec1b`, sha256 `7b68cb703bf78491...`,
   selection loss 0.014480 (s198 + HCE: 0.014311). Float checkpoint `_work\runs\main\best.pt` md5 `647dff86711af769dc7c623005127575`.
10. **Parity on the frozen net** (`results/step7/parity_candidate.json`): 14,000 positions, 0 mismatches between the engine
    tool, the PGO diagnostic exe's in-search eval, the Python reference and the GPU scorer; hand-crafted term 0.
    Fake-quantised float vs integer max 1.02 cp, mean 0.51; unquantised float vs integer max 89.2 cp, mean 7.97.
11. **Final test, scored once at 18:09-18:11** (`results/step7/`, access log kept): candidate **0.014690**; s198 + HCE 0.014496;
    FB2 best 0.014832; HCE alone 0.017195. Score-only loss: candidate 0.004410, s198 + HCE 0.004597.
12. **Candidate exe** (`results/step8/builds/`): `_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe`, md5
    `5c46cd2d43bc051df1a39e841487b95f`, PGO on bench 11/13/16 with the frozen net loaded. Profile: v3 evaluate 2,596,643
    entries; compiled-in net and hand-crafted evaluation 0 entries. With the v3 option off its ten bench pins equal the lock's.
    Rules check (perft x4, mates, stalemate, insufficient material, 50-move rule) passes against the lock exe.
13. **Quiet ABBA NPS** (`results/step8/abba/`): candidate / lock = **1.1976** (95 % CI 1.1915-1.2037), 16 pairs, `bench 20`,
    logical CPU 8; lock 12,389,307 nodes, candidate 14,070,519 (different tree). Lock vs lock: 1.0030 (1.0009-1.0051), 8 pairs.

## Running now
- **Screening match**, declared in `results/step9/MATCH_DECLARATION.md` before the first game: 3,000 games (1,500 opening
  pairs), tc 6+0.06, 12 at once, seed 2026111105. Started 18:16:49, expected to end about 19:45.
  Output `_work\match\h512_cand_3000\` (`match.log`, `games.pgn`, `RUN_INFO.txt`).
- Owned processes: bash launcher pid 2512, fastchess pid 12384 and its engine children.
- A 200-game smoke test of the match pipeline ran earlier with FB2's old net and another seed
  (`_work\match\smoke_fb2best`); it is not part of the result.

## Pending
- Match result with the paired 95 % interval; REPORT.md; final commit and push.

## Deviations and observations
- Engine NNUE's v3 pack and `fable_primary_full.md` are not on the PC and the owner does not have them. Own trainer and config instead (approved).
- Pilot length 400M instead of 100M, chosen after measuring throughput and before any pilot result.
- Stages to 12B and 20B were added to the plan at 17:55, before any staged result, because throughput was 2.0M/s. They did not run: the stop rule ended the run at 2.0B.
- `F:\nnue_pytorch\venv\Lib\site-packages\_rocm_sdk_devel\include` and `\lib` deny access to this account. No permission was changed; the trainer adds the readable `_rocm_sdk_core\include` to Triton's include list in its own process.
- **Cause of Job D's match stalls found:** the owner's `resource_guard.ps1` suspends `fastchess.exe` started from `C:\Users\Administrator\grok-pc\` for about 5 s whenever its thermal latch trips (CPU above 90 C or GPU edge above 83 C). Its log shows such suspensions of the match process at 15:40:15, 16:05:41 and 16:33:09 today, the three bursts Job D reported. This job's match uses the same fastchess, so the same can happen; time losses will be reported by side with a sensitivity figure. The guard is not bypassed.
- E: is a 3 GB volume (2.9 GB free); it cannot meet a 20 GB floor and is not written to.
- The owner's pressure cleanup acts on its own folders when D: or F: falls below 30 GiB. D: is at 33.5 GiB, so this job keeps its D: footprint under 2.5 GiB (now 0.7 GiB).
- One planning-time text search ran over all of `C:\Users\Administrator\grok-pc`, including `forge_push\locks` (read-only, no result from there). Not repeated.
- A safety check refused one of my cleanup commands (a variable-built `rm` path). I re-ran it with literal paths; only five of this job's own pilot checkpoints were removed.

## Free space (18:20)
C: 36.3 GiB, D: 33.5 GiB, F: 32.7 GiB.

## Resume point
- If the match was interrupted: its folder holds the games played so far; a fresh run needs a new folder name
  (`run_match.sh` refuses an existing one) and must be reported as a second run.
- After the match: `python h512/tools/match_elo.py --pgn _work/match/h512_cand_3000/games.pgn --cand cand --out h512/results/step9/match_result.json`, then REPORT.md.
- Training state is kept (`_work\runs\main\latest.pt`, `best.pt`, `stage_S1.pt`, `stage_S2.pt`). It stopped by rule and is not to be resumed without a new decision.

## Blockers
None.

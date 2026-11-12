# JOB E - Standalone H512 network and training recipe - STATUS

**Last update:** 2026-11-11 19:40 PC clock. **Job start:** 16:53 (planning 16:53-17:10, plan approved 17:10, work from 17:11).
**Elapsed:** 2 h 47 min of about 10 h. The rest of the allowance was not used: training stopped by rule after 12 minutes.
**Branch:** `fable/standalone-h512-20261111`, cut from Job D's head `1508c13cdfb87894f01cf3a95fd87b9ad3a4cef0`,
which descends from the lock `lock/combo29-20261110` = `16833ecc03b425586f91f4c8834dea8807bf4c22`.
**Checkout:** `D:\forge_jobs_20261111\h512E` (`core.autocrlf=false`).

## State: phase 1 COMPLETE (`REPORT.md`, verdict: promising for QA). Phase 2 (follow-up) IN PROGRESS.

## Phase 2 (follow-up at the owner's request, 20:30 to about 04:00)
**Last update:** 21:06. Rules: `results/phase2/PHASE2_DECLARATION.md` with addenda 1 to 3b (each committed before
the results it governs).
- **Why:** the owner asked at 20:29 to use the remaining 7.5 hours, then wrote "you can go for 10b" and asked for
  GPU and CPU to work at the same time.
- **Finding so far: the plateau is over-fitting.** Candidate 1 scores 0.013014 on a sample of its own training rows
  and 0.014480 on unseen rows; the untrained hand-crafted eval scores the same on both (0.017099 / 0.017044).
  Training on to 4.0B made unseen rows worse (0.014506) while training rows improved (0.012845).
- **Weight averaging helps:** the average of the 1.0B and 2.0B nets scores 0.014443 on the selection set
  (candidate 1: 0.014480). It qualifies as a new candidate under the rule; not frozen yet.
- **10B run (GPU): paused** at 4,009,025,536 presentations with its own STOP flag at 20:53:46 (resumable, exact).
  It continues to 10B later in the GPU queue. Run folder `_work\runs\phase2`.
- **GPU now:** weight-decay pilot arms W0 to W3 (`_work\runs\wd`, queue launcher pid 15264; W0 done: 0.014480, a repeat
  of stage S2 to within 0.000003). Then the snapshot-averaging run `swa_C1` (GPU queue launcher pid 6928,
  `_work\runs\gpu_queue.txt`). Expected: pilot arms to 21:35, `swa_C1` to 21:55.
- **Match MN1 (CPU), running:** candidate 1 against the lock at a fixed 250,000 nodes per move, no clock, 3,000 games,
  seed 2026111108. fastchess pid 6340, started 20:38:52, 1,426 games at 21:05, expected end about 21:35.
  Folder `_work\match\mn1_nodes250k_02000003072`.
- **Done:** test set 2 (2,000,000 rows from shards 037/039, `manifests/test2_manifest.json`); not scored yet.
- **Next:** freeze candidate 2 by the selection rule when MN1 ends; M2 (candidate 2, 6 s + 0.06 s); M3 (final
  candidate, 10 s + 0.1 s); test set 2 once at the end; phase-2 section of `REPORT.md`.
- **Resume point:** if the session is cut, the match and the GPU queue finish by themselves. Then freeze with
  `h512/tools/freeze_net.py` (see its header) and start `h512/results/phase2/launch_match.sh m2 <net>`.
  The paused 10B run resumes with `bash h512/train/run_phase2.sh`.

The sections below describe phase 1 and are unchanged.

## Result in brief
- **Match (declared before the first game, 3,000 games at 6+0.06 against the original combo29 exe):** 821 wins, 1,465
  draws, 714 losses, **+12.4 Elo, 95 % interval +5.1 to +19.7** (opening pairs as units). 8 time losses (candidate 5,
  lock 3) from one 5-second suspension of the match process by the owner's resource guard at 19:29:30; without those
  six pairs +12.6 (+5.3 to +19.9). No crash, no illegal move.
- **Training:** FB2's 761.9M-position checkpoint continued on the GPU to 2,000,003,072 presentations. **Early stop at
  2.0B by the plateau rule fixed in advance; 7.4B was not reached.**
- **Losses** (lower is better): selection set candidate 0.014480, s198 + HCE 0.014311. Final test, scored once:
  candidate 0.014690, s198 + HCE 0.014496.
- **Parity:** engine integer eval = trainer integer reference on 14,000 of 14,000 positions; hand-crafted term 0.
- **NPS:** 1.1976x the lock (95 % CI 1.1915-1.2037), 16 quiet ABBA pairs; different tree.

## Completed
1. Identities: lock manifest 20/20, s198 md5 `22b4b9e2c61b37c0450f13a3a92c19b3`, lock exe md5 `c0051c99695f48bf93272d96fe7548c3`.
2. FB2 warm start verified by content (`results/step1/`).
3. GPU trainer with self-checks, 2.0M positions/s (`train/`, `results/step1/`, `results/step2/`).
4. Splits frozen with manifest (`manifests/splits_manifest.json`).
5. Engine path behind `FORGE_NNUE_V3`, parity, unit tests, rehearsal build (`results/step3/`).
6. Reference scores (`results/step4/`).
7. Six recipe pilots; P2 chosen by the pre-fixed rule (`results/step5/`).
8. Staged run, stopped at 2.0B by the pre-fixed rule (`results/step6/`).
9. Candidate frozen on the selection set; parity on the frozen net; final test once (`results/step7/`).
10. PGO build with coverage proof, HCE-zero evidence, pins, rules check, quiet ABBA NPS (`results/step8/`).
11. Declared match and paired analysis (`results/step9/`).
12. `REPORT.md`.

## Failed or not done
- The 7.4B presentation target was not reached (early stop by rule at 2.0B). The 4B, 7.4B, 12B and 20B stages did not run.
- Engine NNUE's v3 pack and `fable_primary_full.md` were not available; own trainer note and config were used.
- Not tested: Threads above 1 on the v3 path, longer time controls, sanitizers.
- The match is "not clean" by the gate's convention because of the 8 time losses.

## Exact frozen candidate
- Net: `D:\forge_jobs_20261111\h512E\_work\nets\h512_cand_seen02000003072.fnn3`, md5 `d920a15c5b05040a3ef71a872192ec1b`,
  sha256 `7b68cb703bf7849169f0e46f4f20e3c480d6588a82ed0c2e87803b748f5767e2`.
- Exe: `D:\forge_jobs_20261111\h512E\_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe`, md5 `5c46cd2d43bc051df1a39e841487b95f`.
- Options: `setoption name NNUEArchFile value <net>` then `setoption name NNUEArch value true`.
- Expected bench nodes with the net: 344,397 / 803,457 / 2,873,105 at depths 11 / 13 / 16.

## Artifacts kept locally (not in the repository), 0.7 GiB under `D:\forge_jobs_20261111\h512E\_work\`
- `nets\` (frozen candidate, FB2 best copy), `builds\` (candidate exe, diagnostic twin, rehearsal exe, profiles),
  `plain\` (v3 tool, plain diagnostic exe, unit tests).
- `runs\main\`: `latest.pt`, `best.pt`, `stage_S1.pt`, `stage_S2.pt` (model, Adam, schedule, RNG, data position), six nets, logs.
- `runs\pilots\`: end nets and logs of all six arms; the stage-end checkpoint of the winner P2. The checkpoints of the
  five arms that lost were pruned (this job's own files).
- `data\`: `select_2m.pos/.hce`, `final_test_2m.pos/.hce`, index lists, the final-test access log.
- `match\h512_cand_3000\`: `games.pgn` (md5 `789db9a38fbf43daa3a5eb018981d998`), `match.log`, `RUN_INFO.txt`,
  fastchess's autosave `fastchess_autosave_config.json`. `match\smoke_fb2best\`: the 200-game pipeline test.

## Process ownership
No process of this job is alive. The trainers (launchers 14792 and 15584) and the match (launcher 2512, fastchess 12384)
have exited by themselves. No other process, queue, hold or STOP file was touched.

## Deviations and observations
- Pilot length 400M instead of 100M, chosen after measuring throughput and before any pilot result.
- Stages to 12B and 20B were added to the plan at 17:55, before any staged result. They did not run.
- `F:\nnue_pytorch\venv\Lib\site-packages\_rocm_sdk_devel\include` and `\lib` deny access to this account. No permission
  was changed; the trainer adds the readable `_rocm_sdk_core\include` to Triton's include list in its own process.
- Cause of Job D's match stalls found: the owner's `resource_guard.ps1` suspends `fastchess.exe` started from
  `C:\Users\Administrator\grok-pc\` for about 5 s when its thermal latch trips. It did so once in this job's match.
  The guard was not bypassed.
- E: is a 3 GB volume (2.9 GB free); it cannot meet a 20 GB floor and was not written to.
- One planning-time text search ran over all of `C:\Users\Administrator\grok-pc`, including `forge_push\locks`
  (read-only, no result from there). Not repeated.
- A safety check refused one cleanup command (a variable-built `rm` path). It was re-run with literal paths; only
  five of this job's own pilot checkpoints were removed.

## Free space (19:39)
C: 37 GiB, D: 34 GiB, F: 33 GiB.

## Resume point
Nothing is owed. Next action for QA: gate the frozen candidate against the combo29 lock (REPORT.md, Verdict).
If more training is wanted, it needs a new decision first: the run stopped by rule, and `runs\main\latest.pt` resumes
with `bash h512/train/run_main.sh` only after the plan's stop reason is cleared.

## Blockers
None.

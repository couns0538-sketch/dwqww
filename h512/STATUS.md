# JOB E - Standalone H512 network and training recipe - STATUS

## After the report: 2026-11-12, 06:50 to 10:00 PC clock (evidence in `results/phase3/`)

Nothing here is a gate result or a lock claim. The lock branch and `main` were not touched.

- **Match M8, candidate 3 at 30 s + 0.3 s** (declared 07:15 before the first game, 1,000 games against the original
  lock exe, GPU busy): **+53.2 Elo, 95 % interval +41.9 to +64.6** (324 W / 504 D / 172 L). Two games were lost on
  time, one by each side, in the last minute, when the owner's resource guard suspended the match process for 5 s
  (09:34:14, thermal); without those two pairs +53.1. So the advantage at a clock five times longer is about the
  same as at 10 s + 0.1 s (+57.0) and at fixed nodes (+54.9). `results/phase3/m8/`.
- **Wider net pilot (1024 hidden units, same data, same recipe, random start, 10.0B presentations, 147 min):**
  selection loss 0.014000 / 0.013941 / 0.013868 / 0.013827 / **0.013800** at 1.0 / 2.0 / 4.0 / 7.4 / 10.0B, against
  0.014126 / 0.014055 / 0.013968 / 0.013916 / 0.013882 for 512 units. The gain shrinks from 0.000126 to 0.000082.
  On a sample of its own training rows the wide net scores 0.012615 (512 units: 0.013190): its gap to unseen rows
  is 0.001185 against 0.000692, so the wide net is limited by the amount of data, not by its size. The engine
  searches 0.8579x as many nodes per second with it (95 % CI 0.8552 to 0.8606, 16 pairs, same executable). No
  candidate was taken; no match was played with it yet; never scored on a test set. Net
  `_work\runs\arms\h1024_pilot\net_seen10000023552.fnn3`, md5 `516d450489d5fcc750f35563e41689ee`.
  `results/phase3/h1024_pilot/TABLE.md`, `results/phase3/abba_h1024_speed/`.
- **Candidate executable rebuilt with the author line `Couns`** (09:38, source commit `ce1710b6`, same flags, own
  profile with candidate 3's net, coverage proof passes): `_work\builds\h512_v3_c3_b3c746944937\forge_fair_h512_v3_c3.exe`,
  md5 `0836190d2a2653dbbfad3904d187b446`, sha256 `6733d4b208fb4ecde2a21edf30885fe0fed35af3392265d036a17f91740183c7`.
  It prints `id author Couns`. Bench nodes 348,651 / 743,566 / 2,890,515 as before. Speed against the executable
  that played M7 and M8 (md5 `0b9da97c...`, prints the old line): 0.9980x, 95 % CI 0.9957 to 1.0004, 16 pairs, same
  node count. **No match was played with the new file**; the search is the same by node count.
  `results/phase3/build_c3_author_couns/`, `results/phase3/abba_author_rebuild/`.
- **Checkpoints are now read with a restricted loader** (`h512/train/ckpt_io.py`) in all seven places of this job's
  tools; before, a crafted checkpoint file could have run code when opened. Tests: a file that carries a command is
  refused and the command does not run; all 44 checkpoints this job reads load with content equal to the old
  loader's; averaging reproduces `A12.fnn3` byte for byte; self-check and candidate-3 parity give the recorded
  numbers. `h512/tools/test_ckpt_io.py`, `h512/tools/regress_safe_load.sh`, `results/phase3/safe_load/`.
- **Found while testing: the GPU trainer is not bit-reproducible from run to run.** Seven runs of the same first 45M
  presentations (identical data order in all): selection loss 0.014739 to 0.014756, training loss at step 5000
  0.007650 to 0.007674. This was already visible in `results/step2` and is not caused by the loader change. It means
  differences of about 0.00002 between two short runs are noise; the pilot ranking of phase 1 (P2 ahead of the
  existing recipe by 0.000011) is inside that noise, as REPORT.md already treats it (single-seed pilots, weak evidence).
- **Timing tool:** `fair_eval/tools/abba_fair.py` now starts the timed engine at Normal priority by default
  (`--priority high` repeats the earlier protocol). All timing results before today were measured at High.
- **Security review of this branch against the lock** (543 files, all code read): no vulnerability at the reporting
  bar. The three net loaders check magic, version, every size, the bucket maps, the exact file length and a checksum
  before using a file. The one real weakness, unrestricted checkpoint loading, is fixed (above).
- **Repository-wide fix on the owner's instruction** ("no files must exist that if opened can do destructive
  behavior"): on 57 other branches one ordinary commit removes `opus_round1/C4/instrument_refresh_stats.py` (it
  deleted `src` and `include`) and repairs three tablebase download scripts (a tampered list could write outside the
  destination folder). No force-push; `main` and `lock/*` untouched; no workflow run started. Record, test and undo
  instructions: `results/phase3/repo_fix_20261112/README.md`.
- **Correction:** the safety review written at 08:30 (`_work\REPO_SAFETY_REVIEW_20261112.md`) said 62 lines load
  checkpoints unsafely. 13 of those are `yaml.load` with the safe `BaseLoader`; the right number is 49 over the
  whole history, 22 calls in 16 files at branch tips outside this branch.
- **Failed, not done or limited:** the wide net was not played; the rebuilt executable was not played; M8 ran with
  the GPU busy and Hash 16 MB; the old files remain in the history of the 57 branches and at the tag
  `astra-a1-data-results-20261030`; checkpoint loading in other jobs' trainers was not changed; the 519 files over
  2 MB in the repository were not inspected; 66 earlier commits of this branch carry an AI co-author line (removing
  it needs a history rewrite, which the rules forbid).

**After the report (2026-11-12 07:45 PC clock, owner's instruction):** the UCI author line in `forge-combo29/src/uci.cpp` no
longer names OpenAI. Since 07:47 it reads `Couns`, the name the owner gave (it read `Forge project` for the two
commits before that). This is the only source
change: exactly one preprocessed line differs from the previous head `83edcc4e`, and the file compiles with the
switches off and with `FORGE_NNUE_V3=1`. Every executable cited below was built before this change and still prints
the old line; the candidate executable will be rebuilt and will then have a new hash. The lock branch and the lock
exe are not touched by this job.

**Last update:** 2026-11-12 03:35 PC clock (phase 2, below). **Job start:** 2026-11-11 16:53 (planning 16:53-17:10,
plan approved 17:10, work from 17:11).
**Elapsed:** phase 1 took 2 h 47 min of about 10 h (to 19:42); phase 2 took 7 h of a further 7.5 h (20:30 to 03:30).
**Branch:** `fable/standalone-h512-20261111`, cut from Job D's head `1508c13cdfb87894f01cf3a95fd87b9ad3a4cef0`,
which descends from the lock `lock/combo29-20261110` = `16833ecc03b425586f91f4c8834dea8807bf4c22`.
**Checkout:** `D:\forge_jobs_20261111\h512E` (`core.autocrlf=false`).

## State: COMPLETE. Phase 1: `REPORT.md`. Phase 2 (follow-up): `REPORT_PHASE2.md`, verdict: strongly promising for QA, gate candidate 3.

## Phase 2 (follow-up at the owner's request, 20:30 to 03:30)
**Last update:** 03:35 (2026-11-12). **Phase 2 is COMPLETE.** Result: `REPORT_PHASE2.md`. Rules:
`results/phase2/PHASE2_DECLARATION.md` with addenda 1 to 11 (each committed before the results it governs).
Generated tables: `results/phase2/tables.md`. Phase 2 ran from 20:30 to 03:30, 7 h of the 7.5 h offered.
- **Verdict: strongly promising for QA, gate candidate 3.** Not a gate result and not a lock claim.
- **Why phase 2:** the owner asked at 20:29 to use the remaining 7.5 hours, then wrote "you can go for 10b" and asked
  for GPU and CPU to work at the same time.
- **Finding 1: the phase-1 plateau was over-fitting.** Candidate 1 scores 0.013014 on a sample of its own training
  rows and 0.014480 on unseen rows; the untrained hand-crafted eval scores the same on both (0.017099 / 0.017044).
  Training on without decay to 4.0B made unseen rows worse (0.014506). That run is paused at 4.0B (resumable).
- **Finding 2: weight decay fixes much of it.** One training cycle (1.0B to 2.0B) with decoupled weight decay on the
  king-bucketed first-layer weights: 0.014119 (decay 0.1), 0.014049 (0.3), 0.014083 (1.0), 0.014147 (3), 0.014199
  (10), against 0.014480 without decay (a control repeat landed within 0.000003) and 0.014311 for s198 + HCE.
  Decay 1.0 continued: 0.013963 at 4.0B, 0.013903 at 7.4B, **0.013882 at 10.0B**. Decay 0.3 continued: 0.013929 at
  4.0B, 0.013879 at 7.4B. Decaying the shared factoriser weights too is harmful; alpha 0.4 is worse than 0.25.
- **Finding 3: no warm start is needed.** The same recipe from random initialisation: 0.014126 at 1.0B, 0.014055 at
  2.0B, 0.013968 at 4.0B, 0.013916 at 7.4B, 0.013882 at 10.0B (103 minutes). No candidate was taken from that run.
- **Finding 4: the speed advantage depends on the net.** With candidate 3's net the engine searches 1.0952x the
  lock's nodes per second (95 % CI 1.0931 to 1.0974, quiet ABBA); phase 1 measured 1.1976x with candidate 1's net.
- **Final candidate = candidate 3** (decay 1.0, 10,000,023,552 presentations, selection loss 0.013882):
  `_work\nets\h512_cand_W2_seen10000023552.fnn3`, md5 `aab64b3342d7c1c33e82845f5d2d1fa4`, sha256
  `6d2cf71467e95a96d36b9c8fee808090269cf42b9c455ff428926243e5171903`. Parity 14,000 of 14,000 positions.
  Options `NNUEArchFile` = the net, `NNUEArch` = true. Bench nodes 348,651 / 743,566 / 2,890,515 at depths 11 / 13 / 16.
- **Executables:** rebuilt with candidate 3's net as PGO workload (recommended for the gate):
  `_work\builds\h512_v3_c3_29ea1b67b2dd\forge_fair_h512_v3_c3.exe`, md5 `0b9da97c2a859d6e75642db23536de90`, coverage
  proof passes. Phase-1 build (played MN1 to MN2): `_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe`, md5
  `5c46cd2d43bc051df1a39e841487b95f`. Same bench nodes and same speed on the same net (0.9985x, CI 0.9962 to 1.0007).
- **Test set 2 (scored once, 00:52):** candidate 3 0.014070, candidate 2 0.014259, s198 + HCE 0.014527,
  candidate 1 0.014676, FB2 best 0.014826, HCE alone 0.017237. Same ranking as on the selection set.
- **Matches against the original lock exe** (each declared before its first game; opening pairs as units):
  - MN1, candidate 1, fixed 250,000 nodes, 3,000 games: **-4.8 Elo (95 % interval -12.5 to +3.0)**.
  - M2, candidate 2, 6 s + 0.06 s, 3,000 games: **+41.3 (+33.8 to +48.9)**; 44 games lost on time (candidate 19, lock 25).
  - M3, candidate 3, 10 s + 0.1 s, 2,000 games: **+57.0 (+48.3 to +65.7)**; 13 lost on time (candidate 7, lock 6).
  - M5, candidate 3, 6 s + 0.06 s, 2,000 games: **+66.6 (+58.0 to +75.4)**; 9 lost on time (candidate 3, lock 6).
  - MN2, candidate 3, fixed 250,000 nodes, 3,000 games: **+54.9 (+47.4 to +62.5)**; no abnormal ending.
  - M7, candidate 3 in the rebuilt executable, 6 s + 0.06 s, GPU idle, 1,500 games: **+67.3 (+56.7 to +78.0)**;
    8 lost on time (candidate 5, lock 3).
  - The time losses follow nine 5-second suspensions of the match process by the owner's resource guard (CPU reading
    over 90 C). Results without the affected pairs are within 0.7 Elo. No crash, illegal move or disconnect in 14,500 games.
- **Failed, not done or limited:** timed matches M2, M3 and M5 ran with the GPU busy; one seed per recipe; the
  no-decay run was not taken past 4.0B; `swa_C1`, `ema_E1`, arm X4 and match M6 were declared and not run or not
  finished; test set 3 was built and never scored; no from-scratch net was tested or played; Threads above 1, clocks
  longer than 10 s + 0.1 s and sanitizers were not tested.
- **Process ownership:** no process of this job is alive (checked at the final push). The GPU queue script was ended
  with its own stop flag at 02:35:23. Nothing of anyone else was touched; the guards were not bypassed.
- **Artifacts kept locally,** about 2.4 GiB of phase 2 under `_work\`: the three candidate nets and float checkpoints
  (`nets\`); both executables (`builds\`); the decay-1.0 run with its 4B, 7.4B and 10B states (`runs\arms\wdc_W2`); the
  decay-0.3 run (`runs\arms\wd2c_X1`); the from-scratch run with all five stage states (`runs\arms\scratch_wd`); the
  paused no-decay run (`runs\phase2`); the pilot arms' end states and nets (`runs\wd`, `runs\arms\wd2_X*`); six PGNs
  (`match\`); test sets 2 and 3 and the training-row sample (`data\`). Hashes: `REPORT_PHASE2.md` section 11.
- **Free space at the end:** C: 36.2 GiB, D: 31.3 GiB, F: 32.7 GiB.
- **Resume point:** nothing is owed. Next action for QA: gate candidate 3 against the combo29 lock
  (`REPORT_PHASE2.md`, Verdict). Possible follow-ups, not started: a from-scratch net as its own candidate (needs
  parity, test set 3 once, and a match); more self-play data, which is what now limits the loss.
- **Blockers:** none.

The sections below describe phase 1 as it stood at 19:42 and are unchanged. Their "Exact frozen candidate" is
candidate 1, and their "Resume point" is superseded by the one above.

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

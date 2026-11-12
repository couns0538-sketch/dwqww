# JOB E - Standalone H512 network and training recipe - REPORT

Branch `fable/standalone-h512-20261111`, measured 2026-11-11 on grok-pc (Ryzen 7 9850X3D, 8 cores / 16 logical CPUs,
RX 7900 XT). Paths are under `h512/` unless they start with `forge-combo29/`, `fair_eval/` or a drive letter.
Running record: `STATUS.md`.

## Verdict

**Promising for QA.** In this job's declared 3,000-game screen at equal clock time (6 s + 0.06 s per move), the
standalone H512 candidate scored 51.78 % against the original combo29 exe: **+12.4 Elo, 95 % interval +5.1 to +19.7**,
with opening pairs as the unit. The candidate uses no hand-crafted positional evaluation. This supports sending it to
the crew gate for independent confirmation. It is not a gate result and not a lock claim.

What stands behind that number, and what does not:

- **The candidate evaluates stored positions slightly worse than combo29's evaluator** (final test 0.014690 against
  0.014496) **and searches about 20 % more nodes per second.** The match result is the sum of both. This job did not
  separate them.
- **Training stopped at 2.0B presentations, not the 7.4B the brief asked for.** The stop rule fixed in advance ended
  the run when the 2B stage gained 0.8e-5. The candidate is an early-stop net.
- **One machine stall cost 8 games on time**, 5 against the candidate and 3 against the lock. The owner's resource
  guard suspended the match process for 5 seconds at 19:29:30. Without the six opening pairs involved: +12.6 Elo
  (+5.3 to +19.9).
- No crash, no illegal move and no disconnect in 3,000 games.

**Next QA action:** gate `forge_fair_h512_v3.exe` (md5 `5c46cd2d43bc051df1a39e841487b95f`) with `NNUEArchFile` =
`h512_cand_seen02000003072.fnn3` (md5 `d920a15c5b05040a3ef71a872192ec1b`) and `NNUEArch` = true against the combo29
lock. Check first that `bench 11 / 13 / 16` with the net gives 344,397 / 803,457 / 2,873,105 nodes.

## Result at a glance

| Question | Answer |
|---|---|
| Baseline | combo29 = residual H256 s198 + hand-crafted evaluation, lock commit `16833ecc03b425586f91f4c8834dea8807bf4c22` |
| Candidate | standalone H512, 8 mirrored king buckets, 8 output buckets, int16 inference, no hand-crafted positional evaluation |
| Training done here | FB2's 761.9M-position checkpoint continued on the GPU to **2,000,003,072 presentations** (7.36 passes over 271.8M unique rows). **Early stop: the plateau rule fixed in advance ended the run at 2.0B; 7.4B was not reached** |
| Selection loss (lower is better) | candidate 0.014480, combo29's evaluator 0.014311 |
| Final test, scored once | candidate **0.014690**, combo29's evaluator **0.014496** (candidate 1.3 % worse) |
| Parity | engine integer eval = trainer integer reference on 14,000 of 14,000 positions; hand-crafted term 0 on all |
| Speed | **1.198x** the lock's NPS (95 % CI 1.192-1.204), quiet ABBA, different search tree |
| Match at equal clock time | 3,000 games against the original combo29 exe: 821 wins, 1,465 draws, 714 losses, **+12.4 Elo (95 % CI +5.1 to +19.7)** |

## 1. Baseline identity

| Item | Value |
|---|---|
| Repository | https://github.com/couns0538-sketch/dwqww |
| Lock branch and commit | `lock/combo29-20261110` @ `16833ecc03b425586f91f4c8834dea8807bf4c22` |
| Lock source manifest | `forge-combo29/windows_build/SOURCE_INPUTS.sha256`: 20 of 20 files match on the lock tree |
| Lock exe (the opponent in every comparison) | `forge-combo29/windows/forge_clang_combo29_trial_w6.exe`, md5 `c0051c99695f48bf93272d96fe7548c3` |
| Baseline net s198 | `forge-combo29/src/nnue_weights.inc`, md5 `22b4b9e2c61b37c0450f13a3a92c19b3` |
| This branch's base | Job D's published head `1508c13cdfb87894f01cf3a95fd87b9ad3a4cef0` (a descendant of the lock), for its PGO build script, coverage proof, timing and match tools |

With every build switch off, the eight lock source units still preprocess to the same token stream as the lock
(`results/step3/pp_identity_all_switches_0.txt`), and the candidate exe with its v3 option off reproduces the lock's
ten bench node counts (`results/step8/pins/h512_v3_option_off.txt`).

## 2. What was built

- **Net:** FB1/FB2's FORGENN3 design, unchanged. Hidden 512; 8 king buckets mirrored to files a-d; 8 output buckets by
  piece count; SCReLU on both perspectives; int16 weights with QA 255 and QB 64; eval scale 400.
- **Engine path:** FB1's `nnue_v3.hpp`, `nnue_v3.cpp`, `search_v3.cpp` from branch `fable-fb2-j1`, placed on combo29
  behind a new build switch `FORGE_NNUE_V3` (default 0). UCI options `NNUEArchFile` and `NNUEArch`. While a standalone
  v3 net is active the static evaluation is the net's output alone.
- **Trainer:** `train/train_h512_gpu.py` in the ROCm venv (`F:\nnue_pytorch\venv`, torch 2.11.0+rocm7.13.0). FB2's model,
  quantization-aware training and exporter, with the R7 Triton feature-transformer kernel imported at run time.
  Details in `train/TRAINER_NOTE.md`.
- **Not used:** Engine NNUE's v3 pack (`TRAINER_NOTE_v3`, `h512_stage1_config_v3`) and `fable_primary_full.md` are not on
  the PC and the owner does not have them. Their md5 prefixes from the brief could not be checked. The trainer note and
  `train/stage1_config.json` are this job's own. `FABLE_REPORT_FB2.md` on branch `fable-fb2-j1`
  (md5 `9e40983e6a44ed6283c0110d2df243cd`) served as the FB2 report.
- **GPL:** the R7 kernel file is GPL-3.0. It is imported from its own folder and not copied into this branch. No
  GPL-derived text is in `forge-combo29/`.

## 3. Warm start

| Item | Value |
|---|---|
| Checkpoint | `F:\opus_scratch\fable\fb2\train_j1b\ckpt.pt`, md5 `238d53d830cb5af153e7ba08cb3987b3`, sha256 `e1b375e0c056956d5d3fe9360af66b0ad6505366a5dafb32417ccf5c87ca0f93` |
| Content | step 93,000; 761,856,000 positions seen; best 0.014713967976147187 at step 87,164 |
| Check 1 | `best.fnn3` (md5 `1036f0ac02567d1c5ab1a6861786cd91`, = `ck15_step0087164.fnn3`) re-scored on FB2's 200k holdout: 0.014713967976147187, the published value |
| Check 2 | re-exporting the checkpoint reproduces FB2's `net.fnn3` byte for byte (md5 `e96dd27c0887425109af55162a045d76`) |
| Check 3 | the run's `status.json` equals the copy on branch `fable-fb2-j1` (md5 `8a1d5f19e09536d03a2e843c280722b9`) |
| Check 4 | all 130 FB2 data files match the sha256 in FB2's manifest |

No reference hash for `ckpt.pt` was published that I could find, so it is verified by content. Evidence: `results/step1/`.
The staged run starts from this checkpoint's weights with a fresh Adam state.

## 4. Data, splits and prior exposure

Manifest: `manifests/splits_manifest.json` (seeds, counts, source files, hashes). Tool: `train/make_splits.py`.
Original files were opened read-only; nothing was rewritten.

| Set | Rows | Source | Used for |
|---|---|---|---|
| Training | 271,830,023 | FB2's 64 shuffled shards `F:\opus_scratch\fable\data\train\fb2_train_000..063` = production shards 001-035 without 013/014, deduplicated by FB2. 0 duplicate positions inside | all training |
| Selection | 2,000,000 | shards 013 + 014 (pool 16,388,575; 1,352 duplicates inside removed; 0 rows also in training), proportional per phase bin, seed 2026111101 | every recipe, checkpoint and stop decision |
| Final test | 2,000,000 | shards 036 + 038 (pool 20,000,000; 1,613 duplicates inside, 7,315 rows also in training and 392 also in 013/014 removed), proportional per phase bin, seed 2026111102 | scored once after the freeze |
| Not used | 13,085,679 | shards 037 and 039 | nothing |

Derived files (local, not in the repository): `D:\forge_jobs_20261111\h512E\_work\data\select_2m.pos/.hce`
(sha256 in the manifest), `final_test_2m.pos/.hce`.

**Separation.** The rows carry board, side to move, score and result, and no game id. Sets are therefore separated by
whole self-play shard files plus position-level dedup (board + side to move) across sets. That is weaker than a split
by game id; it relies on a game's plies staying inside one shard file.

**Prior exposure, stated plainly.**
- The candidate's training rows are the rows the FB2 warm start was already trained on.
- Selection set: no net of this job trains on 013/014. FB2 chose its best checkpoint on 200,000 rows of the same pool,
  and s198 was selected on 013/014 by its owners. It is a selection set, not a test.
- Final test: the FB2 warm start never trained on 036/038 (its split log lists shards 001-035 only), and this job never
  used them for a decision. s198's run folder names shards 001-023 only and is dated 2026-10-25; shards 036 and 038
  were written on 2026-10-28 and 2026-10-29. So the final test is unseen by the candidate's training and by s198's
  training. It comes from the same self-play generator as the training data, so it is not an independent data source.

## 5. Row sampling

- This trainer holds all training rows on the GPU and presents one random permutation of all rows per epoch
  (`numpy PCG64([seed, epoch])`). Every eligible row has the same sampling probability by construction.
- The repository had already fixed shard bias for this net: FB2's CPU trainer samples shards in proportion to their
  rows (`--shard-weighting rows`, the default). No second fix was added.
- The data position (epoch, offset) is part of every checkpoint. A stop-and-resume test gave identical index
  checksums at every logged step (`results/step2/resume_*.log`).

## 6. Parity

Script `tools/parity_h512.py`. Positions: Job D's 12,000-FEN set (md5 `e7dbf2c8151188c03ef52054557a531e`) plus 2,000
seeded rows of the selection set, 14,000 in total. Coverage: 7,003 white and 6,997 black to move; every king bucket in
both mirror states for both colours (smallest cell 17 positions); all 8 output buckets (smallest 1,373); 3 to 32 pieces.

Score definition: centipawns from the side to move. `out = trunc(sum / 255) + b2`,
`cp = trunc(out * 400 / (255 * 64))`, both divisions truncate toward zero. Accumulator inputs clamp to 0..255. cp
clamps to +-30000 (never reached on these positions). The loader rejects a net whose accumulators could overflow int16.

| Comparison on the frozen candidate | Result |
|---|---|
| Engine tool (combo29 port, AVX-512 kernel) vs Python integer reference | 0 mismatches of 14,000; max error 0 |
| Tool's own fast path vs its scalar path | 0 mismatches |
| In-search static eval of the PGO diagnostic exe vs reference | 0 mismatches |
| Hand-crafted part of that static eval | 0 on all 14,000 |
| GPU integer scorer (used for every selection and test loss) vs reference | 0 mismatches |
| Output bucket and king keys, engine vs reference | 0 mismatches |
| Float with fake quantisation (what training sees) vs integer | max 1.02 cp, mean 0.51 cp, none over 2 cp |
| Unquantised float weights vs integer | max 89.2 cp, mean 7.97 cp, 1,019 positions over 20 cp |

The last row is why the net is trained quantization-aware: the raw float weights are not what the engine plays.
The same checks passed on FB2's net before the main run (`results/step3/parity_fb2_step93000.json`), and FB1's v3
unit tests pass on the port (95,879 checks, 0 failures; `results/step3/nnue_v3_tests_combo29.log`).
Evidence for the candidate: `results/step7/parity_candidate.json`.

## 7. Recipe comparison

Target: `target = (1 - alpha) * sigmoid(score * 2.25 / 400) + alpha * result_from_side_to_move`. `score` is the stored
search score in centipawns from the side to move; FB2's "blend b" is `1 - alpha`.

Six arms, each 400M presentations from the FB2 checkpoint, fresh Adam, batch 8192, 500 warm-up steps, cosine to 5 % of
the peak, same seed and data order. Ranking metric for all arms: MSE against the alpha 0.4 target on the selection set,
computed from the exported integer net.

| Arm | Peak LR | alpha | Sampling | Ranking loss | alpha 0 loss | alpha 0.25 loss | alpha 0.5 loss | Net md5 |
|---|---|---|---|---|---|---|---|---|
| **P2** | 5e-4 | 0.25 | natural | **0.014496** | 0.004329 | 0.008146 | 0.020422 | `d4d42226...` |
| P0 existing recipe restarted | 1e-3 | ramp 0.1 to 0.4 | natural | 0.014507 | 0.004935 | 0.008380 | 0.020284 | `b3435649...` |
| P1 | 5e-4 | 0.4 | natural | 0.014663 | 0.005155 | 0.008560 | 0.020424 | `beb59598...` |
| P5 | 5e-4 | 0.4 | equal weight per phase bin | 0.014680 | 0.005158 | 0.008571 | 0.020444 | `8cfa3778...` |
| P3 | 5e-4 | 0.0 | natural | 0.014946 | 0.003760 | 0.008213 | 0.021126 | `fbfda9a4...` |
| P4 | 5e-4 | 0.5 | natural | 0.014974 | 0.005901 | 0.009034 | 0.020627 | `0720883c...` |

References on the same set: s198 + HCE 0.014311; FB2 best net 0.014640; FB2 final net (the warm start) 0.014653.

- Rule fixed before the pilots: lowest ranking loss wins; arms within 1e-5 are tied and a tie goes to the existing
  recipe. P2 leads P0 by 1.08e-5, just outside the tie band, so **P2 was used**.
- Phase balancing (P5 against P1) made the ranking loss 1.7e-5 worse and was dropped.
- Limits: one seed per arm; 400M presentations on an already trained net; the ranking metric uses the alpha 0.4
  target, which should favour arms trained near 0.4, yet alpha 0.25 won. P0 differs from the others in two things
  (learning rate and ramp), so it is the reference, not a one-factor comparison. The 1.08e-5 margin of P2 over P0 is
  smaller than what a second seed might move.
- The pilot length was set to 400M (the plan said 100M) after throughput was measured and before any pilot result.

Full table with intermediate checkpoints: `results/step5/pilot_table.md`. Plans: `train/plans/pilot_P*.json`.

## 8. Staged training

Recipe P2 from the FB2 checkpoint: Adam, batch 8192, each stage 500 warm-up steps then cosine from 5e-4 to 2.5e-5,
alpha 0.25, natural sampling. Plan `train/stage1_config.json` (md5 `bd68c7c7881028b47f95f9c497d9ccb1`).
Throughput about 2.0M positions/s; 17:56:09 to 18:08:18; no thermal or disk hold (GPU hot spot max 54 C, memory
junction max 81 C).

| Cumulative presentations | Where | Learning rate | Train loss, running average (alpha 0.25) | Selection loss | FB2 200k holdout |
|---|---|---|---|---|---|
| 761,856,000 | FB2 warm start | - | - | 0.014653 | 0.014733 |
| 1,000,005,632 | **stage S1 end** | 2.5e-5 | 0.007364 | 0.014489 | 0.014580 |
| 1,250,000,896 | S2 | 4.3e-4 | 0.007522 | 0.014634 | 0.014729 |
| 1,500,004,352 | S2 | 2.6e-4 | 0.007362 | 0.014565 | 0.014628 |
| 1,750,007,808 | S2 | 9.5e-5 | 0.007248 | 0.014504 | 0.014594 |
| 2,000,003,072 | S2, last interval checkpoint | 2.5e-5 | 0.007083 | **0.014480** | 0.014567 |
| 2,000,011,264 | **stage S2 end** | 2.5e-5 | 0.007055 | 0.014481 | 0.014568 |

- **Stop rule, fixed before the run:** minimum meaningful improvement 2e-5 in the selection loss between stage ends;
  stop at the first stage end from 2B on that gains less. S2 gained 0.8e-5 over S1, so the run stopped at 2.0B.
- **The 7.4B target was not reached.** Stages to 4B and 7.4B (and the 12B and 20B stages added at 17:55 when
  throughput turned out to be 2.0M/s) did not run. GPU time was available; it was not used, because extending after
  seeing the result would have broken the rule.
- Unique training positions: 271,830,023. Presentations of the candidate: 2,000,003,072, of which 761,856,000 by FB2
  on the CPU and 1,238,147,072 by this job on the GPU. That is 7.36 passes over the unique rows.
- The pilots trained another 6 x 400M presentations; none of that is in the candidate.
- The train loss is on the alpha 0.25 target and is not comparable with the selection loss.

Evidence: `results/step6/` (metrics, log, checkpoint md5 list). Kept locally: `_work\runs\main\latest.pt`, `best.pt`,
`stage_S1.pt`, `stage_S2.pt` (model, Adam, schedule position, RNG states, data position) and every exported net.

## 9. Frozen candidate and the final test

Frozen at 18:09 on the selection set only (`results/step7/FROZEN_CANDIDATE.json`): the checkpoint with the lowest
selection loss.

| Item | Value |
|---|---|
| Net | `D:\forge_jobs_20261111\h512E\_work\nets\h512_cand_seen02000003072.fnn3` |
| md5 / sha256 | `d920a15c5b05040a3ef71a872192ec1b` / `7b68cb703bf7849169f0e46f4f20e3c480d6588a82ed0c2e87803b748f5767e2` |
| Bytes / FNV-1a checksum | 6,309,096 / `eb269e6495ead831` |
| Float checkpoint | `_work\runs\main\best.pt`, md5 `647dff86711af769dc7c623005127575` (exports to this net byte for byte) |

**Final test: 2,000,000 rows, scored once, after the freeze** (access log `results/step7/FINAL_TEST_ACCESS.log`).
MSE of `sigmoid(cp * 2.25 / 400)` against the blended target; the first column is the decision metric's target.

| Evaluator | alpha 0.4 (0.6 score / 0.4 result) | alpha 0.2 | alpha 0 (score only) |
|---|---|---|---|
| **Candidate** (standalone H512) | **0.014690** | 0.006815 | 0.004410 |
| combo29's evaluator (s198 + HCE) | 0.014496 | 0.006811 | 0.004597 |
| FB2 best net (standalone H512, 714M) | 0.014832 | 0.007187 | 0.005012 |
| Hand-crafted evaluation alone | 0.017195 | 0.008414 | 0.005104 |

- On the decision target the candidate is 1.3 % worse than combo29's evaluator. It is equal at alpha 0.2 and 4 %
  better on the pure search-score target. It was trained at alpha 0.25; s198 finished its training at alpha 0.4.
- The continuation closed 42 % of FB2's gap to combo29's evaluator on this set (0.014832 to 0.014690; baseline 0.014496).
- The same three nets on the selection set: 0.014480, 0.014311, 0.014640.
- The final test took no part in any choice. It is kept separate from the match conclusion below: a loss on stored
  positions is not playing strength.

## 10. Engine build

| Item | Value |
|---|---|
| Exe | `D:\forge_jobs_20261111\h512E\_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe` |
| md5 / sha256 | `5c46cd2d43bc051df1a39e841487b95f` / `ec84b99a873d239e0e389b3f4c30a472a1dbaaf93e0fbb888e97cbcd9838c963` |
| Source | commit `c0e2a93e673599ca31a95dc9fdfb00fca2ad30c7` of this branch (clean tree); source manifest sha256 `cf1e6414428d7185...` |
| Compiler | clang 23.1.5 (llvm-mingw-20261104), sha256 `d05fee2c3f79b15d...`: the lock's compiler |
| Flags | the lock's, token for token, plus `-DFORGE_NNUE_V3=1`: `-std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=znver5 -flto=thin`, PGO generate then use with `-Werror=profile-instr-unprofiled -Werror=profile-instr-out-of-date` |
| PGO workload | `uci`, `isready`, `setoption name NNUEArchFile value <frozen net>`, `setoption name NNUEArch value true`, `bench 11`, `bench 13`, `bench 16`, `isready`, `quit` (sha256 `bd71791ff389e538...`) |
| Profile | sha256 `585e433f97add73b...`; used only by this build (the work folder is named by a hash over source, flags, compiler, workload and net) |
| Bench nodes with the net | 344,397 / 803,457 / 2,873,105 at depths 11 / 13 / 16; 14,070,519 / 22,250,746 at 20 / 22 |
| Build script | `fair_eval/build_fair.ps1 -Config h512_v3` (Job D's script; one new config and a v3 load check added) |

**The profile exercised the candidate's own evaluation path** (`results/step8/builds/`, `results/step8/hce_zero_profile_functions.txt`):

| Function | Entries during the workload |
|---|---|
| `Worker::static_evaluate_v3` / `nnue::v3::evaluate` | 2,596,643 |
| `nnue::v3::apply_changes` (incremental update) | 5,880,794 |
| `nnue::v3::refresh_cached` | 24 |
| compiled-in net `nnue::evaluate`, `update`, `refresh` | 0 |
| `Evaluator::evaluate`, `evaluate_uncached`, `evaluate_runtime`, `evaluate_position`, `refresh_runtime_psqt`, `update_runtime_psqt` | 0 |
| `Evaluator::clear` and the constructor (cache housekeeping, no evaluation) | 30 and 4 |

**The hand-crafted evaluation contributes nothing in this candidate.** Three independent checks:
1. the profile above: no hand-crafted evaluation function was entered in 2.6 million static evaluations;
2. the diagnostic twin's in-search static eval equals the net's integer output on 14,000 of 14,000 positions, with the
   non-network part 0 on every one;
3. the source: with a standalone v3 net active, `Worker::static_evaluate` returns `static_evaluate_v3`, which
   returns the network value for a non-residual net (`forge-combo29/src/search_v3.cpp`).

One caveat: the hand-crafted evaluator is still compiled into the binary. With `UseNNUE` set to false the exe
evaluates with it, exactly as the lock does. The match and all measurements ran with the default (`UseNNUE` true).

**Rules are untouched** (`results/step8/rules_check_candidate.json`, `tools/rules_check.py`): perft on four positions
equals the known counts and the lock; checkmate and stalemate at the root, mate in 1 and mate in 2, insufficient
material (K v K, KN v K, KB v K) and two 50-move-rule positions give the same result as the lock exe. The switch
only changes the static evaluation; move generation, terminal detection and draw rules are the lock's code.

## 11. NPS

Job D's protocol unchanged: fresh process per run, Threads 1, Hash 16, `bench 20`, engine pinned to logical CPU 8 at
High priority, one warm-up per arm, slots alternate A B / B A, one pair = one slot, ratio = candidate / lock.
Nothing else of this job ran. Machine load before and after: 3.4 % and 0.8 %.

| Arm | Pairs | Ratio, geometric mean (95 % CI) | Median | Min | Max | Nodes lock / candidate |
|---|---|---|---|---|---|---|
| lock vs lock (noise floor) | 8 | 1.0030 (1.0009-1.0051) | 1.0030 | 0.9990 | 1.0063 | 12,389,307 / 12,389,307 |
| **candidate vs lock** | 16 | **1.1976 (1.1915-1.2037)** | 1.2018 | 1.1825 | 1.2111 | 12,389,307 / 14,070,519 |

Mean NPS: lock 3,251,239, candidate 3,893,637. Raw samples: `results/step8/abba/*/runs.tsv`, summaries `summary.json`.
The candidate searches a different tree, so this is a description of speed on these eight bench positions, not an
Elo estimate.

## 12. Match at equal clock time

This job's own run. **Not the crew gate, not a lock claim.**

**Declared before the first game** (`results/step9/MATCH_DECLARATION.md`, committed at 18:16, match started 18:16:49):

| Setting | Value |
|---|---|
| Candidate | `forge_fair_h512_v3.exe` (md5 `5c46cd2d...`), `NNUEArchFile` = frozen net (md5 `d920a15c...`), `NNUEArch` = true |
| Opponent | original lock exe `forge_clang_combo29_trial_w6.exe` (md5 `c0051c99...`), default options |
| Budget | 3,000 games = 1,500 opening pairs, fixed; no early stop on the score |
| Openings | `UHO_Lichess_4852_v1.epd` (md5 `0e0a809d...`), random order, seed 2026111105, each opening with both colours |
| Clock | 6 s + 0.06 s per move, the same for both; time margin 1000 ms |
| Engines | Threads 1, Hash 16 MB, OwnBook false |
| Concurrency | 12 games at once on 16 logical CPUs; nothing else of this job running |
| Adjudication | none |
| Runner | fastchess (md5 `c0662c67...`), Job D's `fair_eval/tools/run_match.sh` unchanged |
| Analysis | pentanomial over opening pairs, 95 % normal interval on the mean pair score, mapped to Elo (`tools/match_elo.py`) |

**Result** (`results/step9/match_result.json`, recomputed from the PGN; `match.log.gz` is fastchess's own log):

| Item | Value |
|---|---|
| Games completed / opening pairs | 3,000 / 1,500 (every pair complete) |
| Candidate wins / draws / losses | 821 / 1,465 / 714 |
| Score | 51.78 % |
| **Elo, 95 % interval (pairs as units)** | **+12.4 (+5.1 to +19.7)** |
| fastchess's own figure | +12.40 +/- 7.31 |
| Pentanomial, pair score 0 / 0.5 / 1 / 1.5 / 2 | 34 / 328 / 672 / 429 / 37 |
| Crashes, disconnects, illegal moves | 0 |
| Time losses | 8: candidate 5, lock 3 |
| Without the 6 opening pairs that contain a time loss | +12.6 (+5.3 to +19.9), 1,494 pairs |
| Elapsed | 18:16:49 to 19:37:44 |

A game-by-game (trinomial) interval would be +3.5 to +21.3. It is given for comparison only; the paired interval is
the one to use, because the two games of an opening are not independent.

**The time losses have one known cause.** All eight fall in games 2700 to 2709, with overruns of 1.5 to 3.9 s on both
engines at once. The owner's `resource_guard.ps1` logged `SUSPENDED 12384 gate: thermal=True` at 19:29:30.8 and
`RESUMED` at 19:29:35.9; 12384 was this match's fastchess process. It is the only suspension of that process in the
match (`results/step9/time_losses.txt`). The guard was not bypassed. By the gate's convention the run is "not clean";
the result is essentially the same with or without the affected pairs.

**What this says and does not say.**
- The interval excludes zero, so on this machine, at this clock, with this book, the standalone candidate was ahead of
  the original combo29 exe.
- It is one short-control match of 3,000 games on one machine with 12 games at once. It supports a recommendation
  for independent QA confirmation and nothing more.
- It does not say whether the gain comes from evaluation quality or from speed. The candidate's loss on stored
  positions is slightly worse than combo29's evaluator and its NPS is about 20 % higher.
- A 200-game test of the match pipeline ran earlier with FB2's old net and another seed
  (`_work\match\smoke_fb2best`, +41.9 +/- 31.8). It was a pipeline check, is not part of this result, and its
  interval is too wide to compare with anything.

PGN (local): `D:\forge_jobs_20261111\h512E\_work\match\h512_cand_3000\games.pgn`, md5 `789db9a38fbf43daa3a5eb018981d998`.

## 13. Limitations

- **Training stopped at 2.0B, not 7.4B.** The plateau is this recipe's (alpha 0.25, peak 5e-4, a restart per stage).
  Whether a single long schedule, another learning rate or more data would go lower was not tested.
- **The candidate's loss is worse than combo29's evaluator** on both the selection set and the final test.
  Loss on stored positions and playing strength disagree here, as they did in earlier jobs.
- **Single seeds everywhere**: six pilots, one staged run. No error bars on losses.
- **The final test is unseen but not independent**: same generator, shard-level separation, no game ids.
- **The match is a short screen**: 6+0.06, Threads 1, Hash 16, one machine, 12 games at once, one opening book.
  It is this job's own run, not the crew gate.
- **NPS is tied to the eight bench positions** and one core.
- **Not tested:** Threads above 1 on the v3 path, longer time controls, sanitizers.
- **Builds are not byte-reproducible** (Job D's finding); rebuilding gives the same node counts but another exe hash.
- **Environment:** `venv\Lib\site-packages\_rocm_sdk_devel\include` denies access to this account. The trainer works
  around it inside its own process by using the readable `_rocm_sdk_core\include`; nothing was changed on disk.
- **E:** is a 3 GB volume with 2.9 GB free and cannot meet the 20 GB floor. It was not written to. C:, D: and F:
  stayed above 32 GiB; this job's files on D: total under 1 GiB.

## 14. Reproduction

```
git clone https://github.com/couns0538-sketch/dwqww && cd dwqww
git config core.autocrlf false && git checkout fable/standalone-h512-20261111
source h512/train/env_h512.sh
# checks of the trainer and the warm start
$PY -I -B h512/train/train_h512_gpu.py selfcheck --pos F:/opus_scratch/fable/data/holdout/fb2_holdout_200k.pos --rows 200000 \
    --ckpt F:/opus_scratch/fable/fb2/train_j1b/ckpt.pt --net F:/opus_scratch/fable/fb2/train_j1b/best.fnn3 --net-out _work/nets/reexport.fnn3
# splits
$PY -I -B h512/train/make_splits.py --out-dir _work/data --manifest h512/manifests/splits_manifest.json
# pilots, then the staged run
bash h512/train/run_pilots.sh
bash h512/train/run_main.sh
# freeze (selection set only), engine build, parity
$PY -I -B h512/tools/freeze_candidate.py --run-dir _work/runs/main --out h512/results/step7/FROZEN_CANDIDATE.json
pwsh -NoProfile -File fair_eval\build_fair.ps1 -Config h512_v3            # and again with -Diag
bash fair_eval/tools/plain_build.sh clang _work/plain/h512_v3_diag_plain.exe -DFORGE_NNUE_V3=1 -DFORGE_FAIR_DIAG=1
$PY -I -B h512/tools/parity_h512.py --net <net> --ckpt _work/runs/main/best.pt --fens <fens_12k_v2.txt> \
    --select-pos _work/data/select_2m.pos --tool <forge_nnue_v3_tool exe> --diag <diag exe> --work _work/parity/cand --out parity.json
# final test (once), speed, rules, match
$PY -I -B h512/train/train_h512_gpu.py score --net <net> --pos _work/data/final_test_2m.pos --final-test-unlock
$PY -I -B fair_eval/tools/abba_fair.py --name N --out NEW_DIR --a <lock exe> --b <cand exe> --b-opt "setoption name NNUEArchFile value <net>" --b-opt "setoption name NNUEArch value true" --slots 16
$PY -I -B h512/tools/rules_check.py --lock <lock exe> --cand <cand exe> --cand-opt "setoption name NNUEArchFile value <net>" --cand-opt "setoption name NNUEArch value true" --out rules.json
MATCH_SEED=2026111105 bash fair_eval/tools/run_match.sh h512_cand_3000 _work/match 3000 <cand exe> "option.NNUEArchFile=<net> option.NNUEArch=true"
$PY -I -B h512/tools/match_elo.py --pgn _work/match/h512_cand_3000/games.pgn --cand cand --out h512/results/step9/match_result.json
```

The v3 tool is built from `h512/tools/nnue_v3_tool.cpp` plus every `forge-combo29/src/*.cpp` except `uci.cpp`, with the
lock defines and `-DFORGE_NNUE_V3=1`.

## 15. Files and hashes

Nets, checkpoints, exes, profiles and PGNs are local (`D:\forge_jobs_20261111\h512E\_work\`), not in the repository.

| What | Path | md5 |
|---|---|---|
| **Frozen candidate net** | `_work\nets\h512_cand_seen02000003072.fnn3` | `d920a15c5b05040a3ef71a872192ec1b` |
| **Candidate exe (played and timed)** | `_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe` | `5c46cd2d43bc051df1a39e841487b95f` |
| Candidate diagnostic twin (eval dumps only) | `_work\builds\h512_v3_diag_56ae5025294a\forge_fair_h512_v3_diag.exe` | `ebfc8820d1ba7ddc07da2261e6645ec8` |
| Lock exe (opponent) | `forge-combo29\windows\forge_clang_combo29_trial_w6.exe` | `c0051c99695f48bf93272d96fe7548c3` |
| Baseline net s198 | `forge-combo29\src\nnue_weights.inc` | `22b4b9e2c61b37c0450f13a3a92c19b3` |
| FB2 checkpoint (warm start) | `F:\opus_scratch\fable\fb2\train_j1b\ckpt.pt` | `238d53d830cb5af153e7ba08cb3987b3` |
| FB2 best net | `F:\opus_scratch\fable\fb2\train_j1b\best.fnn3` | `1036f0ac02567d1c5ab1a6861786cd91` |
| FB2 final net | `F:\opus_scratch\fable\fb2\train_j1b\net.fnn3` | `e96dd27c0887425109af55162a045d76` |
| Staged run: best checkpoint | `_work\runs\main\best.pt` | `647dff86711af769dc7c623005127575` |
| Staged run: latest / S1 end / S2 end checkpoints | `_work\runs\main\latest.pt`, `stage_S1.pt`, `stage_S2.pt` | `6f4bd2ba52c20c956a4655550edba705`, `a10bdf26b6504968c9390cc508bc8207`, `9b052e431e67141380444ff66fd015d8` |
| Staged run: nets at 1.0B / 1.25B / 1.5B / 1.75B / 2.0B end | `_work\runs\main\net_seen*.fnn3` | `3acee6bf...`, `d0e76e56...`, `cee69b10...`, `fdca49b8...`, `e3ebf2e1...` (full list `results/step6/main_files.md5`) |
| Pilot end nets P0..P5 | `_work\runs\pilots\P*\net_seen01161863168.fnn3` | `results/step5/pilot_final_nets.md5` |
| v3 tool, plain build (parity) | `_work\plain\forge_nnue_v3_tool_combo29.exe` | `774bc4bfcdcd1ec4606c1ea068f2fe94` |
| v3 diagnostic exe, plain build (first parity) | `_work\plain\h512_v3_diag_plain.exe` | `7717b1ddea21131acdc1cabd96fea48f` |
| v3 unit tests exe | `_work\plain\forge_nnue_v3_tests_combo29.exe` | `47d069888343e6473e69a7543c6b087f` |
| Rehearsal exe with FB2's net (pipeline tests only) | `_work\builds\h512_v3_rehearsal_60e5747bd9fe\forge_fair_h512_v3_rehearsal.exe` | `dcbf1c30ba8493761d99d7d7779e25f6` |
| fastchess | `C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe` | `c0662c67e54498553bb0d1c98c173d7b` |
| Opening book | `C:\Users\Administrator\grok-pc\coder-fuzz\UHO_Lichess_4852_v1.epd` | `0e0a809d82af10f2e107ca83f1a5b7d3` |
| R7 Triton kernels (imported) | `D:\grok-pc-data\dwqww\.claude\worktrees\opus-r7-speed\tools\nnue_pytorch_amd\forge_v2\forge_v2_kernels.py` | `916539cef784f791d7d3ed91e61e05f1` |
| Baseline scorer (s198 + HCE losses) | `F:\opus_scratch\fable\s31tool\forge_sol_S31_avg_ckpt.py` | `a791df209246bf605fcc25f68c2b8f65` |

## 16. Other findings

- **Why Job D's matches stalled.** The owner's `resource_guard.ps1` suspends `fastchess.exe` started from
  `C:\Users\Administrator\grok-pc\` for about 5 s whenever its thermal latch trips (CPU above 90 C or GPU edge above
  83 C). Its log has such suspensions of Job D's match process at 15:40:15, 16:05:41 and 16:33:09 on 2026-11-11, the
  three bursts Job D reported without a cause. Any match run with that fastchess can lose games on time this way.
- **GPU throughput.** With the rows held on the GPU this net trains at about 2.0M positions/s on the RX 7900 XT,
  twice the R7 figure for H256 through the binpack loader. 7.4B presentations would take about one hour.
- **Speed of the standalone path.** A standalone int16 H512 net is about 20 % faster per second than residual float
  H256 plus the hand-crafted evaluation on this machine.

## 17. Time record

Times are read from the logs and rounded to the minute.

| Step | PC clock |
|---|---|
| Planning (read-only survey), plan approved | 16:53 - 17:10 |
| Checkout, identities, FB2 verification | 17:11 - 17:20 |
| GPU trainer, self-checks, throughput, resume test | 17:20 - 17:26 |
| Splits frozen | 17:27 |
| Pilots (six arms) | 17:28 - 17:53 |
| Engine port, first parity pass, unit tests, rehearsal build | 17:31 - 17:37 |
| Staged run | 17:56 - 18:08 |
| Freeze, PGO build, parity, final test, pins, rules | 18:09 - 18:12 |
| Quiet ABBA NPS | 18:12 - 18:16 |
| Match | 18:16:49 - 19:37:44 |
| Report and final push | 19:38 - 19:50 |

Total about 3 hours of the 10-hour allowance. Training took 12 minutes of GPU time instead of the planned hours
because it stopped by rule at 2.0B; the remaining time was not padded.

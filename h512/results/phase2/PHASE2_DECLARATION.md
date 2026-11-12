# JOB E follow-up (phase 2): declared before any phase-2 result

Written 2026-11-11 20:35 PC clock, before the first phase-2 training step and before the first phase-2 game.

## Why there is a phase 2
The owner asked at 20:29 to use the rest of the allowance (about 7.5 hours, to about 04:00) for more results.
Phase 1 stands as published at commit `a40cbdc0`; none of its results are changed here.

## What was already known when these rules were written
The phase-1 selection losses, the phase-1 final-test scores (shards 036/038) and the phase-1 match result
(+12.4 Elo). These rules could therefore be influenced by them. Consequences:
- The phase-1 final-test set is not opened again.
- A new test set from the two shards no set of this job has used (037, 039) is scored once, after candidate 2 is frozen.
- The decision to train on is the owner's request plus the brief's 7.4B target. It overrides the phase-1 plateau rule,
  which stopped the run at 2.0B. This is a deviation from the phase-1 plan and is reported as one.

## Training
- Continue from the state at the end of stage S2 (copy of `_work/runs/main/latest.pt`, md5 `6f4bd2ba52c20c956a4655550edba705`:
  model, Adam, RNG and data position) in a new run folder `_work/runs/phase2`. The phase-1 run folder is not written to.
- Same recipe, seed, data and stage boundaries (`h512/train/phase2_config.json`): batch 8192, peak learning rate 5e-4,
  cosine to 5 % per stage, alpha 0.25, natural sampling, a checkpoint with selection loss every 250M presentations.
- Three stages, each its own cosine cycle ending at a low learning rate: S3 to 4B, S4 to 7.4B (the brief's target),
  S5 to 10B. The owner wrote "you can go for 10b" at about 20:33, before the run started, so S5 ends at 10B instead of 12B
  and all three stages run without the plateau rule. Stage S6 (20B) is dropped.
- Hard limit: the trainer stops itself after 105 minutes of running, wherever it is.
- Expected time: about 70 minutes for the 8B presentations at 2.0M positions/s.

## Candidate 2 (selection set only)
- Candidate 2 = the phase-2 checkpoint with the lowest `select_2m` loss (blend 0.6), the earliest on an exact tie.
- It counts as a new candidate only if that loss is at least 2e-5 below candidate 1's 0.014480 (so 0.014460 or lower).
  Otherwise there is no candidate 2, the finding is "more training with this recipe did not help", and candidate 1
  stays the only candidate.
- "Final candidate" below means candidate 2 if it exists, otherwise candidate 1. Match results do not change this choice.

## Test set 2
- 2,000,000 rows from shards 037 + 039, sampled per phase bin with seed 2026111103, after removing every position
  (board + side to move) that occurs in the training set, anywhere in 013/014 or anywhere in 036/038.
- File name `final_test2_2m.pos`: the scorer refuses it without the one-time flag and logs every access.
- Scored once, after candidate 2 is frozen, for candidate 2, candidate 1, s198 + HCE, FB2 best and HCE alone.
  If there is no candidate 2 it is still scored once for the other four, as a second independent reading.

## Executable
The candidate executable is not rebuilt: `_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe`
(md5 `5c46cd2d43bc051df1a39e841487b95f`). The net is a file loaded at start, so candidate 1 and candidate 2 differ
only in the net file. Known limitation: its PGO profile was collected with candidate 1's net loaded.
Integer parity (engine = trainer reference) and bench node counts are re-checked with candidate 2's net.

## Matches
All against the original lock exe (md5 `c0051c99695f48bf93272d96fe7548c3`) with Job D's `fair_eval/tools/run_match.sh`:
fastchess, Threads 1, Hash 16, OwnBook false, `UHO_Lichess_4852_v1.epd` in random order, each opening with both
colours, 12 games at once, time margin 1000 ms, no adjudication, `-recover`. Fixed budgets, no early stop.
Analysis as in phase 1 (`h512/tools/match_elo.py`, opening pairs as units). No heavy work of this job runs during a match.

| Match | Played when | Candidate | Clock | Games | Seed |
|---|---|---|---|---|---|
| M2 | only if candidate 2 exists | candidate 2 | 6 s + 0.06 s | 3,000 | 2026111106 |
| M3 | always | final candidate | 10 s + 0.1 s | 3,000 | 2026111107 |
| M4 | only if at least 100 minutes remain before 03:10 when M3 ends | final candidate | fixed nodes per move, equal for both engines | 3,000 | 2026111108 |

- M4's node count is fixed in its own declaration before its first game, sized to fit the time left.
- Each match gets a short declaration with the exact net hash before its first game.
- Known hazard, as in phase 1: the owner's `resource_guard.ps1` suspends fastchess for about 5 s when its thermal latch
  trips. Affected games are reported by side, with the result without the affected opening pairs. The guard is not bypassed.

## Addendum 1 (20:38, before any phase-2 checkpoint at a stage end and before any phase-2 game)
The owner wrote at 20:36: "just continue using the gpu and cpu simultaneously for the engine for 7 and a half hours".
Known when this was written: one interval checkpoint of stage S3 (2.25B, selection loss 0.014653, at high learning rate).
Changes:
- **GPU and CPU work at the same time.** The sentence "No heavy work of this job runs during a match" is withdrawn.
  The trainer (the GPU plus one CPU thread) runs during matches. Both engines of a match play under the same load,
  and every opening is played with both colours, so this adds noise, not a bias for one side. It is stated with each match.
- **New match MN1, starting now, during training:** candidate 1 (the published net, md5 `d920a15c5b05040a3ef71a872192ec1b`)
  against the lock exe at a fixed **250,000 nodes per move for both engines, no clock**, 3,000 games, seed 2026111108,
  `h512/tools/run_match_nodes.sh` (Job D's layout without the clock). Purpose: equal nodes instead of equal time, so
  the candidate's 20 % speed advantage does not count; it shows how much of the +12.4 Elo is evaluation quality.
  250,000 nodes is about what the engines searched per move at 6 s + 0.06 s (mean 0.13 s per move in the phase-1 match).
  A clock-free match cannot lose games on time and is not affected by load or by a suspension of the match process.
  MN1 takes the place of M4; a second fixed-nodes match with the final candidate (seed 2026111109) follows only if time allows.
- **GPU after 10B:** if the selection loss at the end of S5 (10B) is at least 2e-5 below the best earlier stage end,
  the same run continues with S6 to 20B (the stage declared in phase 1). Otherwise the main line ends at 10B and the GPU
  runs recipe variants from the 2.0B state; those are declared in a second addendum before they start.
- **Candidate rule extended:** every later freeze uses the same rule (lowest selection loss over all checkpoints so far;
  a new candidate only if at least 2e-5 below the previous candidate).
- **Test set 2 is scored once, at the end of all training,** for every frozen candidate and the references.
- M2 starts when MN1 has finished and candidate 2 is frozen. M3 uses the final candidate known when M3 starts.

## Time plan (PC clock)
| Item | Time |
|---|---|
| MN1 fixed-nodes match (CPU, during training) | 20:39 to about 21:50 |
| Training to 10B | 20:35 to about 21:47 |
| Freeze, parity, test set 2, bench pins | 20 minutes |
| M2 | 85 minutes |
| M3 (the slow item: 3,000 games at the longer clock) | about 2 h 20 min |
| M4 if time allows | up to 100 minutes |
| Report, hashes, push | from 03:10 at the latest |

## Addendum 2 (20:50): weight-decay pilot on the GPU after the 10B run
Known when this was written: phase-2 checkpoints up to 3.0B (selection loss 0.014579 at learning rate 2.6e-4; stage S2
stood at 0.014565 at the same point of its cycle), and this diagnostic (`train_sample_*.json` in this folder):

| Evaluator | 2,000,000 training rows | selection set (unseen shards) |
|---|---|---|
| Hand-crafted eval alone (never trained on either) | 0.017099 | 0.017044 |
| s198 + HCE | 0.014138 | 0.014311 |
| Candidate 1 (2.0B) | 0.013014 | 0.014480 |

The two sets are equally hard for an evaluator that was trained on neither. Candidate 1 is 11 % better on rows it was
trained on than on unseen rows. So the plateau on the selection set is over-fitting to the 271.8M training rows, and
more passes alone are unlikely to help. This changes addendum 1 in one point: **after 10B the GPU does not go on to
20B first; it runs a regularisation pilot.** (The 10B run itself continues as the owner asked.)

Pilot, declared before any arm runs:
- Each arm repeats stage S2 of phase 1 exactly: it resumes a copy of the 1.0B state (`_work\runs\main\stage_S1.pt`:
  same model, Adam, RNG, data position), then one cosine cycle 1.0B to 2.0B, peak learning rate 5e-4, alpha 0.25.
- The only change is decoupled weight decay on the king-bucketed first-layer weights `w1`
  (`w1 *= 1 - lr * lambda` after every step). The shared factoriser weights, biases and output layer are not decayed.
- Arms: **W0** lambda 0 (a repeat of S2, to measure run-to-run noise), **W1** 0.1, **W2** 1.0, **W3** 10.
  About 9 minutes each. Plans `h512/train/plans/wd_W*.json`, queue `h512/train/run_wd_pilots.sh`.
- Metric: the same selection loss, at the 2.0B stage end. Phase 1's S2 ended at 0.014481.
- Rule: an arm "helps" if its stage-end loss is at least 2e-5 below both S2's 0.014481 and W0's. The arm with the
  lowest loss among those that help wins. If the winner is at the edge of the range (W3), or sits between a much
  better and a much worse neighbour, up to two more arms next to it may be run under the same rule.
- If an arm wins: its run continues from its own 2.0B state with the same decay in further cosine stages
  (to 4B, then 7.4B) while time allows, and the usual candidate rule applies to its checkpoints
  (lowest selection loss; a new candidate only if at least 2e-5 below the current candidate).
- If no arm helps: that is the finding. The GPU then continues the unregularised run from 10B toward 20B (stage S6).
- The training-row sample is scored at every checkpoint of the arms only to show the fit gap. It is never used to choose.

## Addendum 2b (20:54): order swapped, the pilot runs before the rest of the 10B run
Known when this was written: stage S3 ended at 4.0B with selection loss 0.014506, which is 2.5e-5 worse than the 2.0B
stage end (0.014481), while the training loss kept falling. More passes are making the net worse on unseen positions.
- The 10B run was paused with its own STOP flag at 20:53:46, 1,100 steps into stage S4 (4,009,025,536 presentations).
  It is resumable from `_work\runs\phase2\latest.pt` with the exact data position and continues to 10B later
  (the owner asked for 10B), while the CPU plays matches.
- The weight-decay pilot of addendum 2 started at 20:54 instead of after 10B. Its arms and rules are unchanged.
- Reason for the swap: the pilot is the experiment that can still produce a better net; running it first leaves time
  to play a declared match with its result.
- If an arm wins, its continuation to 4B is frozen and matched first (M2 slot); the 7.4B stage follows while that match runs.

## Addendum 3 (20:55): weight averaging of stage-end nets
Declared before any average was computed. Known: everything listed above.
- Idea: each stage is a full cosine cycle that ends at a low learning rate, so the stage ends at 1.0B, 2.0B and 4.0B are
  three finished nets of one lineage. Averaging their float weights (equal weights, `h512/tools/average_ckpts.py`) is a
  standard remedy for over-fitting and costs no training.
- Averages computed: **A12** (1.0B + 2.0B), **A23** (2.0B + 4.0B), **A123** (all three). Later stage ends of the same
  run, and of a winning weight-decay arm, may be averaged the same way under this rule.
- Each average is exported with the trainer's exporter and scored on the selection set like any checkpoint.
- Candidate rule unchanged: an average becomes a new candidate only if its selection loss is at least 2e-5 below the
  current candidate's (candidate 1: 0.014480). If several qualify, the lowest wins.

## Addendum 3b (20:58): snapshot-averaging run, and one more average
Known when this was written: the three averages of addendum 3 on the selection set: A12 0.014443, A123 0.014458,
A23 0.014466 (candidate 1: 0.014480). Averaging helps, and the average without the over-fitted 4.0B net is best.
- **A012** is added: the FB2 warm-start state (0.762B, the end of FB2's own cosine cycle) + 1.0B + 2.0B.
- **Snapshot-averaging run `swa_C1`** (GPU, after the weight-decay arms): from the 2.0B state, eight short cosine
  cycles of 250M presentations (2.0B to 4.0B), learning rate 2.5e-4 falling to 2.5e-5, alpha 0.25, no decay.
  Plan `h512/train/plans/swa_C1.json`. Candidates from it are averages of cycle-end states, fixed now:
  **SWA4** (the first four cycle ends), **SWA8** (all eight), **SWA4+** and **SWA8+** (the same plus the 2.0B start state).
- Same candidate rule. The lowest selection loss among all qualifying nets at the time of a freeze becomes the candidate.
- After `swa_C1` the GPU resumes the paused 10B run, unless a weight-decay arm won (then its continuation runs first).

## Addendum 4 (21:08): running-average arm `ema_E1`
Known when this was written: W0 (the no-decay repeat of S2) ended at 0.014480 against S2's 0.014481, so run-to-run
noise is about 0.000003; A012 scored 0.014445. No weight-decay arm with decay had finished.
- `ema_E1` repeats stage S2 once more (from the 1.0B state, same recipe, no decay) and keeps three exponential running
  averages of the weights (decay 0.9999, 0.99997, 0.99999: horizons of about 82M, 273M and 819M presentations).
  Plan `h512/train/plans/ema_E1.json`. It runs on the GPU after `swa_C1`, before the paused 10B run resumes.
- The averaged nets at its 2.0B stage end are eligible candidates under the same rule. The raw net of this arm is a
  third repeat of S2 and is not a candidate.

## Addendum 5 (21:20): weight decay works; the GPU plan follows it
Known when this was written: arm W1 (decay 0.1 on `w1`) ended at **0.014119** on the selection set, against 0.014480
for the same cycle without decay (W0) and 0.014311 for s198 + HCE. On the training-row sample it scored 0.013182
(W0: 0.013014), so the fit gap shrank from 0.00147 to 0.00094. Arms W2 (decay 1.0) and W3 (decay 10) had not finished.
- **The winner's continuation goes to 10B.** As addendum 2 says, the arm with the lowest stage-end loss among W1 to W3
  continues from its own 2.0B state with the same decay; the stages are now fixed as 4B, 7.4B and 10B
  (plans `h512/train/plans/wdc_W*.json`, chosen automatically by `h512/train/run_wd_continue.sh` when W3 ends).
- **Dropped:** `swa_C1` and `ema_E1` (addenda 3b and 4) are not run. They average nets trained without decay, and
  decay improves the loss ten times more than averaging did. Averages of the continuation's own stage ends stay
  eligible under addendum 3.
- **The paused 10B run without decay stays paused** (resumable). It was getting worse on unseen positions, so the GPU
  time goes to the decayed run, which is taken to the 10B the owner asked for. If GPU time is left at the end, more
  decay values next to the winner are tried under addendum 2's rule.
- **Candidate 2** is frozen when match MN1 has ended and arm W3 has finished: the eligible net with the lowest selection
  loss at that time (arm checkpoints at 2.0B and the averages computed so far). It plays M2 (6 s + 0.06 s).
- M3 (10 s + 0.1 s) is played by the best eligible net when M2 ends. A third slot of 85 minutes, if time allows, is
  that net at 6 s + 0.06 s (seed 2026111110) if it is not the M2 net, otherwise the fixed-nodes match with it.

## Addendum 6 (21:54): second pilot round on the GPU after the 10B run
Known when this was written: the first round (W1 0.014119, W2 0.014083, W3 0.014199 at 2.0B; W2 won and is candidate 2),
match MN1 (-4.8 Elo at equal nodes for candidate 1), and the continuation of W2 up to 3.0B (0.014162 mid-cycle).
Nothing of match M2 beyond a running score.
- Five arms, each the same 1.0B to 2.0B cycle from the phase-1 state at 1.0B, to be compared with W2's 0.014083:
  **X1** decay 0.3 on `w1`; **X2** decay 3 on `w1`; **X3** decay 1.0 on `w1` and on the shared factoriser weights `wf`;
  **X4** decay 1.0 on `w1`, `wf` and the output weights `w2`; **X5** decay 1.0 on `w1` with alpha 0.4 instead of 0.25.
  Plans `h512/train/plans/wd2_X*.json`. About 10 minutes each, queued behind the 10B run.
- Rule: an arm "beats W2" if its 2.0B stage-end selection loss is at least 2e-5 below 0.014083. If one does, the best
  such arm is continued from its own 2.0B state in the same stages as W2's continuation (4B, then 7.4B) while time
  allows, and its checkpoints become eligible candidates under the usual rule. If none does, the GPU work ends with
  the 10B run and these five results.
- Any net frozen after M3 has started plays the third match slot (6 s + 0.06 s, seed 2026111110) if time allows.

## Addendum 7 (22:27): match plan for the rest of the night
Known when this was written: M2's running score after 1,524 of 3,000 games (+31 Elo, error 10, with 22 games lost on
time after three guard suspensions), and the decay run up to 6.0B. M2 is not stopped or shortened.
- **M3** (10 s + 0.1 s, seed 2026111107) is played with **2,000 games** instead of 3,000, by the eligible net with the
  lowest selection loss when M2 ends. Reason: 3,000 games at this clock take about 2 h 20 min; 2,000 games leave room
  for the two matches below before the report has to be written. The interval is wider for it (about 9 Elo, not 7).
- **M5** (6 s + 0.06 s, 3,000 games, seed 2026111110): the eligible net with the lowest selection loss when M3 ends,
  if that net has not already played at this clock (candidate 2 has, in M2). This is the final candidate's own match
  under the phase-1 conditions.
- **MN2** (fixed 250,000 nodes per move, 3,000 games, seed 2026111109): the same net as M5 (or as M3 if M5 is not
  played), if at least 60 minutes remain before 03:05. It answers what MN1 answered for candidate 1: evaluation quality
  with speed taken out.
- All three as before: against the original lock exe, 12 games at once, the GPU job running, time losses by side.

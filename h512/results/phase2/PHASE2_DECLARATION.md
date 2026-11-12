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

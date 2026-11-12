# JOB E phase 2 (follow-up) - Standalone H512: over-fitting found, weight decay fixes it - REPORT

Branch `fable/standalone-h512-20261111`, measured from 2026-11-11 20:30 to 2026-11-12 02:55 on grok-pc. This file continues
`REPORT.md` (phase 1), which is unchanged. Paths are under `h512/` unless they start with a drive letter or `_work\`.
Rules and their timing: `results/phase2/PHASE2_DECLARATION.md` (the declaration and eleven addenda, each committed
before the results it governs). Generated tables: `results/phase2/tables.md`. Running record: `STATUS.md`.

## Verdict

**Strongly promising for QA: gate candidate 3.** A standalone H512 net trained with weight decay beat the original
combo29 exe clearly in every timed screen of this phase, and it is now also the better evaluator on stored positions.
These are this job's own screens, not gate results and not a lock claim.

| Net | Condition | Games | Elo against combo29 | 95 % interval |
|---|---|---:|---:|---|
| Candidate 1 (phase 1, no decay, 2.0B) | 6 s + 0.06 s | 3,000 | +12.4 | +5.1 to +19.7 |
| Candidate 1 | equal nodes (250,000 per move) | 3,000 | -4.8 | -12.5 to +3.0 |
| Candidate 2 (decay, 2.0B) | 6 s + 0.06 s | 3,000 | +41.3 | +33.8 to +48.9 |
| **Candidate 3 (decay, 10.0B)** | 6 s + 0.06 s | 2,000 | **+66.6** | +58.0 to +75.4 |
| **Candidate 3** | 10 s + 0.1 s | 2,000 | **+57.0** | +48.3 to +65.7 |
| **Candidate 3** | equal nodes (250,000 per move) | 3,000 | **+54.9** | +47.4 to +62.5 |

What stands behind these numbers:

- **Phase 1's net had over-fitted its training rows.** It was 11 % better on positions it had seen than on unseen
  ones, and training on made unseen positions worse (sections 1 and 2).
- **Decoupled weight decay on the king-bucketed first-layer weights fixes much of that** (sections 4 and 5). On unseen
  positions the loss went from 0.014480 to 0.013882; combo29's evaluator stands at 0.014311. A second, untouched test
  set scored once at the end gives the same picture: 0.014070 against 0.014527 (section 8).
- **Candidate 1's +12.4 came from speed, not from evaluation:** at equal nodes it scored -4.8 (MN1). **Candidate 3
  scores +54.9 at equal nodes** (MN2): its advantage is in the evaluation itself. Its speed adds less than it did
  for candidate 1: with candidate 3's net the engine searches 9.5 % more nodes per second than combo29, with
  candidate 1's net it was 19.8 % (section 6b).
- **The warm start is not needed:** the same recipe trained from random initialisation comes within 0.00004 of the
  warm-started runs at equal training length (section 5c). No candidate was taken from that run.
- Limits: timed matches ran with the GPU busy and lost some games on time to the owner's thermal guard (counted by
  side, section 7); the executable was not rebuilt for the new nets; one seed per recipe (section 10).

**Next QA action:** gate `forge_fair_h512_v3.exe` (md5 `5c46cd2d43bc051df1a39e841487b95f`) with `NNUEArchFile` =
`h512_cand_W2_seen10000023552.fnn3` (md5 `aab64b3342d7c1c33e82845f5d2d1fa4`) and `NNUEArch` = true against the
combo29 lock. Check first that `bench 11 / 13 / 16` with the net gives 348,651 / 743,566 / 2,890,515 nodes.

## How phase 2 came about, and what it changes against the phase-1 plan

The owner asked at 20:29 to use the remaining 7.5 hours of the allowance, wrote "you can go for 10b", and asked for
GPU and CPU to work at the same time. Phase 1 had stopped training at 2.0B presentations by its own plateau rule.

Deviations from the phase-1 plan, all on the owner's instruction or declared before the result they affect:

- **The plateau rule was set aside** to train on past 2.0B.
- **GPU and CPU ran together.** Timed matches were played while the trainer used the GPU and one CPU thread. Both
  engines of a match play under the same load and every opening is played with both colours.
- **The run without weight decay was paused at 4.0B**, when it was getting worse on unseen positions (section 2).
  It is resumable. The 10B the owner asked for was reached with the weight-decay recipe instead (section 5).
- **The candidate executable was not rebuilt until the end.** Matches MN1 to MN2 load their nets into the phase-1
  exe (md5 `5c46cd2d43bc051df1a39e841487b95f`), whose PGO profile was collected with candidate 1's net. After those
  matches the executable was rebuilt with candidate 3's net, timed and played once more (section 6b, addendum 11).
- **Decisions use the selection set only.** The phase-1 final-test set was not opened again. A second test set from
  shards 037/039 was scored once, after the candidate list had closed (section 8).
- **The plan changed several times during the night, each time in writing before the result it governs** (addenda 1
  to 11 of the declaration). Two changes were made after seeing a result and say so: the pilot was moved ahead of the
  rest of the no-decay run when that run got worse (addendum 2b), and the from-scratch run was allowed to produce a
  candidate after its first stage end came in (addendum 10).

## 1. Finding: the plateau was over-fitting

Phase 1 ended with the candidate at 0.014480 on the selection set, behind combo29's evaluator (0.014311), and with
no gain from 1.0B to 2.0B. To see why, 2,000,000 rows of the training set itself were scored next to the selection
set (unseen shards 013/014). Loss = mean squared error against the blend-0.6 target, lower is better.

| Evaluator | Training rows | Selection (unseen) | Unseen is worse by |
|---|---:|---:|---:|
| Hand-crafted eval alone (trained on neither) | 0.017099 | 0.017044 | -0.3 % |
| combo29's evaluator, s198 + HCE (s198 was trained on part of these rows) | 0.014138 | 0.014311 | 1.2 % |
| Candidate 1 (2.0B presentations, 7.4 passes) | 0.013014 | 0.014480 | 11.3 % |

- The two sets are equally hard for an evaluator trained on neither, so the sets themselves do not differ.
- Candidate 1 is far better on positions it has seen than on positions it has not. On its own training rows it beats
  combo29's evaluator clearly; on unseen rows it loses.
- So the limit in phase 1 was not training time. The net had started to memorise its 271.8M training rows.

Files: `results/phase2/train_sample_cand1.json`, `train_sample_s198_hce.json`. The sample is the first 2,000,000
rows of `fb2_train_000.pos` (FB2 shuffled the set globally), written to `_work\data\train_sample_2m.pos`.

## 2. More passes without decay made it worse

The phase-1 run was continued with the same recipe from 2.0B (`_work\runs\phase2`, plan `train/phase2_config.json`).

| Presentations | Selection (unseen) | Training rows |
|---:|---:|---:|
| 1.0B (stage end) | 0.014489 | 0.013305 |
| 2.0B (stage end) | 0.014481 | 0.013014 |
| 4.0B (stage end) | 0.014506 | 0.012845 |

The training rows kept improving and the unseen rows got worse. The run was paused with its own STOP flag at
4,009,025,536 presentations (20:53:46) and left resumable. Full checkpoint list: `results/phase2/tables.md`, table A.

## 3. Weight averaging helps a little

Each stage is a full cosine cycle ending at a low learning rate, so the stage ends are finished nets of one lineage.
Their float weights were averaged with equal weights (`tools/average_ckpts.py`) and scored like any checkpoint.

| Average of | Selection |
|---|---:|
| 1.0B + 2.0B (A12) | 0.014443 |
| FB2 warm start + 1.0B + 2.0B (A012) | 0.014445 |
| 1.0B + 2.0B + 4.0B (A123) | 0.014458 |
| 2.0B + 4.0B (A23) | 0.014466 |
| Candidate 1 alone, for comparison | 0.014480 |

Averaging gained up to 0.000037. Weight decay (next section) gained ten times that, so the averaging runs planned in
addenda 3b and 4 (`swa_C1`, `ema_E1`) were dropped and no average became a candidate. Averages across nets trained
with different decay do not work: 1.0B + the decay-1.0 net scored 0.014954, the two decay nets together 0.014312.

## 4. Weight decay fixes much of the over-fitting

**Pilot, declared before it ran (addendum 2).** Each arm repeats the phase-1 cycle from 1.0B to 2.0B exactly: it
resumes a copy of the 1.0B state (model, Adam, RNG, data position) and trains one cosine cycle with peak learning rate
5e-4 and alpha 0.25. The only change is decoupled weight decay on the king-bucketed first-layer weights `w1`:
`w1 *= 1 - lr * lambda` after every step. The shared factoriser weights, the biases and the output layer are not decayed.

| Arm | Decay lambda | Selection (unseen) | Training rows | Gap | FB2's old holdout (200k) |
|---|---:|---:|---:|---:|---:|
| W0 (control, a repeat of phase 1's cycle) | 0 | 0.014480 | 0.013014 | 0.001466 | 0.014567 |
| W1 | 0.1 | 0.014119 | 0.013182 | 0.000937 | 0.014188 |
| **W2** | **1.0** | **0.014083** | 0.013644 | 0.000439 | 0.014147 |
| W3 | 10 | 0.014199 | 0.013896 | 0.000303 | 0.014254 |

- **Run-to-run noise is about 0.000003:** the control arm W0 ended at 0.014480 against 0.014481 for the phase-1 cycle
  it repeats. The gains here are a hundred times larger.
- With decay 1.0 the net fits its training rows less well and unseen rows much better. One cycle with decay moved the
  selection loss from 0.014480 to 0.014083, **below combo29's evaluator (0.014311)** for the first time.
- Decay 0.1 to 1.0 is a broad optimum; decay 10 is too strong.
- The same ranking shows on FB2's old 200,000-row holdout, which was not used to choose.

W2 won by the declared rule. Its checkpoint at 2,000,003,072 presentations (0.014081) was frozen as **candidate 2**.
Evidence: `results/phase2/wd/` (metrics and logs of all four arms, `WINNER.txt`), `results/phase2/tables.md` table B.

## 5. The decay recipe continued to 10B

The winning arm was continued from its own 2.0B state with the same recipe and the same decay through three more
cosine cycles (plan `train/plans/wdc_W2.json`, run `_work\runs\arms\wdc_W2`, 80.6 minutes for 8.0B presentations
including 36 scored checkpoints; no thermal hold).

| Stage end | Presentations | Passes over the 271.8M rows | Selection (unseen) | Training rows | Gap | FB2's old holdout |
|---|---:|---:|---:|---:|---:|---:|
| candidate 1, no decay | 2,000,003,072 | 7.4 | 0.014480 | 0.013014 | 0.001466 | 0.014567 |
| decay 1.0 | 2,000,011,264 | 7.4 | 0.014083 | 0.013644 | 0.000439 | 0.014147 |
| decay 1.0 | 4,000,014,336 | 14.7 | 0.013963 | 0.013517 | 0.000446 | 0.014024 |
| decay 1.0 (the brief's 7.4B) | 7,400,022,016 | 27.2 | 0.013903 | 0.013456 | 0.000447 | 0.013966 |
| **decay 1.0 (candidate 3)** | **10,000,023,552** | 36.8 | **0.013882** | 0.013441 | 0.000441 | 0.013946 |

- With decay, more passes help: unseen and seen rows improve together and the gap stays at 0.00044. Without decay
  the same passes made unseen rows worse (section 2).
- The gains shrink: 0.000120 from 2B to 4B, 0.000060 to 7.4B, 0.000021 to 10B. The recipe is close to its limit on
  this data; going past 10B would add little.
- 10B is what the owner asked for and 7.4B is what the brief asked for; both were reached with this recipe.
- combo29's evaluator stands at 0.014311 on the same set. Candidate 3 is 3.0 % better; candidate 1 was 1.2 % worse.

All checkpoints: `results/phase2/tables.md` table C; run log and metrics: `results/phase2/wdc_W2/`.

## 5b. Second pilot round: which decay, on which weights, with which result weight

Declared in addendum 6 before any arm ran. Each arm is again the cycle from 1.0B to 2.0B, compared at its 2.0B stage end.

| Arm | Change against W2 (decay 1.0 on `w1`, alpha 0.25) | Selection (unseen) | Training rows | Gap | Selection, teacher only |
|---|---|---:|---:|---:|---:|
| W1 (round 1) | decay 0.1 | 0.014119 | 0.013182 | 0.000937 | 0.004044 |
| **X1** | **decay 0.3** | **0.014049** | 0.013407 | 0.000642 | 0.003963 |
| W2 (round 1) | none | 0.014083 | 0.013644 | 0.000439 | 0.003964 |
| X2 | decay 3 | 0.014147 | 0.013804 | 0.000343 | 0.003996 |
| W3 (round 1) | decay 10 | 0.014199 | 0.013896 | 0.000303 | 0.004031 |
| X3 | decay 1.0 also on the shared factoriser weights `wf` | 0.014915 | 0.014623 | 0.000291 | 0.004340 |
| X4 | decay 1.0 on `w1`, `wf` and the output weights | no result (stopped) | | | |
| X5 | alpha 0.4 instead of 0.25 | 0.014127 | 0.013511 | 0.000616 | 0.004639 |

- **Decay strength:** the best single cycle is at decay 0.3; the curve is flat from 0.3 to 1.0 (0.000034 apart) and
  falls off on both sides.
- **Decay only the king-bucketed weights.** Decaying the shared factoriser weights as well is harmful (0.014915),
  presumably because they carry the piece-square knowledge that all king buckets share.
- **Keep alpha 0.25.** With decay, alpha 0.4 is still worse (0.014127 against 0.014083), although the selection loss
  itself is measured against the alpha-0.4 target, and its fit to the teacher scores is much worse.
- X4 was stopped 34M presentations into its cycle (addendum 9): it is X3 plus one more decayed group, X3 had just shown
  that group of changes to be harmful, and X3 had also run at half the usual speed.

X1 beat W2 by more than 0.00002, so by the declared rule its run was continued (next table). Evidence:
`results/phase2/wd2/` (metrics and logs, `WINNER_ROUND2.txt`).

**Decay 0.3 continued to 7.4B** (plan `train/plans/wd2c_X1.json`, run `_work\runs\arms\wd2c_X1`):

| Stage end | Decay 0.3: selection | Decay 0.3: training rows | Decay 1.0: selection | Decay 1.0: training rows |
|---|---:|---:|---:|---:|
| 2.0B | 0.014049 | 0.013407 | 0.014083 | 0.013644 |
| 4.0B | 0.013929 | 0.013262 | 0.013963 | 0.013517 |
| 7.4B | 0.013879 | 0.013197 | 0.013903 | 0.013456 |
| 10.0B | not run | | 0.013882 | 0.013441 |

- Decay 0.3 stays about 0.00003 ahead of decay 1.0 at equal length. At 7.4B it matches decay 1.0 at 10B.
- Its best checkpoint (0.013876 at 7.25B) is 0.000006 below candidate 3. That is under the 0.00002 a new candidate
  needs, so **no candidate 4 was frozen and candidate 3 is the final candidate**
  (`results/phase2/FREEZE_4_NO_NEW_CANDIDATE.json`). The candidate list of the warm-started line closed here, at 00:51.

## 5c. The same recipe from random initialisation

Every net above started from FB2's checkpoint and from phase 1's first stage, 1.0B presentations without decay in
all. To see whether that warm start is needed, the recipe was run once from seeded random weights with decay 0.3 from
the first step (plan `train/plans/scratch_wd.json`, run `_work\runs\arms\scratch_wd`, started 00:51).

| Presentations | From scratch, decay 0.3: selection | training rows | Warm start, decay 0.3: selection | Warm start, decay 1.0: selection |
|---|---:|---:|---:|---:|
| 1.0B | 0.014126 | 0.013495 | (0.014489, before any decay) | (0.014489, before any decay) |
| 2.0B | 0.014055 | 0.013399 | 0.014049 | 0.014083 |
| 4.0B | 0.013968 | 0.013283 | 0.013929 | 0.013963 |
| 7.4B | 0.013916 | 0.013215 | 0.013879 | 0.013903 |
| 10.0B | 0.013882 | 0.013190 | not run | 0.013882 |

- **The warm start is not needed.** From random weights the recipe is at 0.014126 after 1.0B presentations (13
  minutes), better than phase 1's candidate ever got, and it then tracks the warm-started runs within 0.00004.
  At 10B it ends at 0.013882, the same value as candidate 3 to six decimals (0.0138823 against 0.0138824).
- It is not better either: at equal length it is level with the warm-started decay-1.0 run (within 0.00003) and up
  to 0.00004 behind the warm-started decay-0.3 run, which is the like-for-like comparison.
- Addendum 10 allowed this run to produce a fourth candidate if a finished stage end was at least 0.00002 below
  candidate 3 (0.013882) when match MN2 ended (02:22:53). The best finished stage end then was 7.4B at 0.013916, so
  **no candidate was taken from it** (`results/phase2/FREEZE_SCRATCH_NO_NEW_CANDIDATE.json`), test set 3 (built from
  further rows of shards 037/039, manifest `manifests/test3_manifest.json`) was **not scored**, and match M6 was not
  played. The 10B net that finished at 02:35 would not have qualified either: it is level with candidate 3, not below it.
- The from-scratch net at 10B is kept (`_work\runs\arms\scratch_wd\net_seen10000023552.fnn3`, md5
  `21851771a34a061d7bace67f11942c29`; float state `stage_S5.pt`, md5 `217ecaf8b7355fe1f2b34be43cef7a15`). It was
  never scored on a test set, never checked for parity and never played. All hashes: `results/phase2/scratch_wd/files.md5`.
- Training from scratch ran slower at first (1.1M to 1.4M positions per second in the first 250M presentations,
  1.6M to 2.0M later); 10B took 103 minutes including 24 scored checkpoints. The cause of the slow start was not
  investigated.

Evidence: `results/phase2/scratch_wd/`, `results/phase2/tables.md` table C.

## 6. Candidates

Every candidate is a FORGENN3 file loaded by the same executable. Candidates were frozen on the selection set only,
by the rule fixed in the declaration: the eligible net with the lowest selection loss, and only if it is at least
0.00002 below the previous candidate.

| | Candidate 1 (phase 1) | Candidate 2 | Candidate 3 |
|---|---|---|---|
| Recipe | no decay | decay 1.0 on `w1` from 1.0B | the same run continued |
| Presentations | 2,000,003,072 | 2,000,003,072 | 10,000,023,552 |
| Selection loss | 0.014480 | 0.014081 | 0.013882 |
| Frozen | 18:08 | 21:41 | 23:03 |
| Net file in `_work\nets\` | `h512_cand_seen02000003072.fnn3` | `h512_cand_W2_seen02000003072.fnn3` | `h512_cand_W2_seen10000023552.fnn3` |
| Net md5 | `d920a15c5b05040a3ef71a872192ec1b` | `ae0d372e3748fc6d4e27c2885b164d46` | `aab64b3342d7c1c33e82845f5d2d1fa4` |
| Net sha256 | `7b68cb703bf7849169f0e46f4f20e3c480d6588a82ed0c2e87803b748f5767e2` | `df88ae380196c796cc8ded28095194d1fb67ce4ea42dc2b50621dc347b06208b` | `6d2cf71467e95a96d36b9c8fee808090269cf42b9c455ff428926243e5171903` |
| Float checkpoint md5 | `647dff86711af769dc7c623005127575` | `4fd2d9fb4834443a54690fc1bd4cd5f8` | `295828fd438138194aad00bf181d65b5` |
| Integer parity, 14,000 positions | 0 mismatches | 0 mismatches | 0 mismatches |
| Hand-crafted term in search eval | 0 on all | 0 on all | 0 on all |
| Fake-quantised float against integer, max / mean cp | 1.02 / 0.51 | 1.02 / 0.51 | 1.02 / 0.51 |
| Bench nodes at depth 11 / 13 / 16 | 344,397 / 803,457 / 2,873,105 | 293,818 / 900,174 / 2,610,509 | 348,651 / 743,566 / 2,890,515 |

- Executable for all three: `_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe`, md5
  `5c46cd2d43bc051df1a39e841487b95f`. Options: `setoption name NNUEArchFile value <net>`, then
  `setoption name NNUEArch value true`.
- Parity means: the engine's evaluation tool, the search's own static evaluation (diagnostic build), the Python integer
  reference and the GPU scorer agree on every one of 14,000 positions (`results/phase2/parity_candidate2.json`,
  `parity_candidate3.json`). The bench node counts are in `pins_candidate2.txt` and `pins_candidate3.txt`.
- Freeze records with the other eligible nets and their losses: `results/phase2/FROZEN_CANDIDATE_2.json`, `_3.json`.

## 6b. A rebuilt executable for candidate 3, and its speed

Done last (addendum 11), after matches MN1 to MN2, with nothing else of this job running.

- **Build.** Config `h512_v3_c3` of `fair_eval/configs.json`, built by `fair_eval/build_fair.ps1`: the same source
  and flags as the phase-1 executable (engine sources are unchanged since phase 1), with candidate 3's net loaded
  while the PGO profile is collected. Result: `_work\builds\h512_v3_c3_29ea1b67b2dd\forge_fair_h512_v3_c3.exe`,
  md5 `0b9da97c2a859d6e75642db23536de90`, sha256 `81d58b04ba1b8fbd56a6c94475fc2048a0692e1fe7a23d31647c4913b922a598`.
- **Coverage proof passes** (`results/phase2/build_c3/coverage.json`): the standalone evaluation ran 2,619,188 times
  in the profile workload; the compiled-in residual net and every hand-crafted evaluation function ran 0 times.
- **Same search.** With candidate 3's net the rebuilt executable gives 348,651 / 743,566 / 2,890,515 bench nodes at
  depths 11 / 13 / 16, identical to the phase-1 executable with that net.
- **Speed**, Job D's quiet ABBA protocol (`bench 20`, 16 pairs, engine pinned to logical CPU 8, machine 2 % busy):

| A | B | B / A in nodes per second | 95 % interval | Nodes A / B |
|---|---|---:|---|---|
| lock exe | rebuilt exe, candidate 3's net | **1.0952** | 1.0931 to 1.0974 | 12,389,307 / 13,407,897 |
| phase-1 exe, candidate 3's net | rebuilt exe, candidate 3's net | 0.9985 | 0.9962 to 1.0007 | 13,407,897 / 13,407,897 |
| lock exe | phase-1 exe, candidate 1's net (phase 1) | 1.1976 | 1.1915 to 1.2037 | 12,389,307 / 14,070,519 |

- **The rebuild changes nothing measurable:** on the same net and the same nodes the two executables are equally fast.
- **The speed advantage depends on the net.** With candidate 1's net the standalone engine searched 19.8 % more
  nodes per second than the lock, with candidate 3's net 9.5 %. The engines search different trees, so nodes per
  second is not a like-for-like speed; but the phase-1 figure of "about 20 % faster" must not be carried over to
  candidate 3. Its gain over combo29 is mostly evaluation (MN2), not speed.
- Evidence: `results/phase2/build_c3/` (receipt, coverage, workload, build log), `results/phase2/abba_c3/`,
  `results/phase2/abba_old_vs_c3/` (every timing sample).

## 7. Matches

All matches are this job's own screens against the original lock exe (md5 `c0051c99695f48bf93272d96fe7548c3`),
not the crew gate. Each was declared before its first game (`results/phase2/*_DECLARATION.md`), with the exact net
hash; M5 and MN2 were declared by a rule that named candidate 3 as the expected net, and candidate 3 is what played.
fastchess, Threads 1, Hash 16, OwnBook false, `UHO_Lichess_4852_v1.epd` in random order, every opening with both
colours, 12 games at once, no adjudication. Elo and the 95 % interval are recomputed from the PGN with opening pairs
as the unit (`tools/match_elo.py`).

### MN1: candidate 1 at equal nodes (speed taken out)

Both engines searched a fixed 250,000 nodes per move with no clock (`tools/run_match_nodes.sh`, seed 2026111108).
That is about what they searched per move at 6 s + 0.06 s (0.13 s per move on average in the phase-1 match).

| Games | Wins | Draws | Losses | Score | Elo | 95 % interval | Pairs 0 / 0.5 / 1 / 1.5 / 2 |
|---:|---:|---:|---:|---:|---:|---|---|
| 3,000 | 791 | 1,377 | 832 | 49.32 % | **-4.8** | -12.5 to +3.0 | 60 / 367 / 677 / 346 / 50 |

- No game ended abnormally; a clock-free match cannot lose on time and the guard did not suspend it.
- **Reading:** at equal nodes candidate 1 is level with combo29 or slightly behind. Its +12.4 Elo at equal time in
  phase 1 therefore came from its 20 % higher speed, not from a better evaluation. This agrees with its losses on
  stored positions (0.014480 against 0.014311 on the selection set).
- Evidence: `results/phase2/mn1/` (result recomputed from the PGN, run info, log, PGN md5).

### M2: candidate 2 at 6 s + 0.06 s (the phase-1 conditions, new openings)

Candidate 2 is the decay-1.0 net at 2.0B (selection loss 0.014081). Same settings as the phase-1 match, time margin
1000 ms, seed 2026111106. The GPU trainer ran during the match.

| Games | Wins | Draws | Losses | Score | Elo | 95 % interval | Pairs 0 / 0.5 / 1 / 1.5 / 2 |
|---:|---:|---:|---:|---:|---:|---|---|
| 3,000 | 960 | 1,435 | 605 | 55.92 % | **+41.3** | +33.8 to +48.9 | 22 / 261 / 633 / 508 / 76 |

- For comparison, candidate 1 scored +12.4 (+5.1 to +19.7) under the same conditions in phase 1. The two nets differ
  only in one training cycle with weight decay.
- **44 games ended on time**, 19 lost by the candidate and 25 by the lock. The owner's resource guard suspended the
  match process five times for 5 seconds (21:55:22, 22:16:52, 22:17:38, 22:46:07, 23:02:41) when its CPU reading went
  over 90 C; its GPU reading stayed near 44 C. With the GPU busy the machine ran warmer than in phase 1 (one
  suspension then). Without the 24 opening pairs involved: **+41.2 (+33.6 to +48.7)**. The guard was not bypassed.
- No crash, no illegal move, no disconnect.
- Evidence: `results/phase2/m2/` (`match_result.json`, `time_losses.txt` with the guard's log lines, run info, log, PGN md5).

### M3: candidate 3 at 10 s + 0.1 s (a longer clock)

Candidate 3 is the decay-1.0 net at 10.0B (selection loss 0.013882). 2,000 games (addendum 7), seed 2026111107,
time margin 1000 ms. The GPU trainer ran during the match.

| Games | Wins | Draws | Losses | Score | Elo | 95 % interval | Pairs 0 / 0.5 / 1 / 1.5 / 2 |
|---:|---:|---:|---:|---:|---:|---|---|
| 2,000 | 662 | 1,001 | 337 | 58.13 % | **+57.0** | +48.3 to +65.7 | 11 / 126 / 430 / 393 / 40 |

- The advantage did not shrink at the longer clock.
- 13 games ended on time, 7 lost by the candidate and 6 by the lock, after two guard suspensions (23:37:40, 23:51:56).
  Without the 10 opening pairs involved: +57.5 (+48.9 to +66.3).
- No crash, no illegal move, no disconnect.
- Evidence: `results/phase2/m3/`.

### M5: candidate 3 at 6 s + 0.06 s (the phase-1 conditions)

The final candidate under the same conditions as candidate 1 in phase 1 and candidate 2 in M2. 2,000 games
(addendum 8), seed 2026111110, time margin 1000 ms. The GPU trainer ran during the match.

| Games | Wins | Draws | Losses | Score | Elo | 95 % interval | Pairs 0 / 0.5 / 1 / 1.5 / 2 |
|---:|---:|---:|---:|---:|---:|---|---|
| 2,000 | 703 | 973 | 324 | 59.48 % | **+66.6** | +58.0 to +75.4 | 9 / 107 / 430 / 404 / 50 |

- Three nets under the same conditions: candidate 1 (no decay) +12.4, candidate 2 (decay, 2.0B) +41.3, candidate 3
  (decay, 10.0B) +66.6. The intervals of candidates 2 and 3 do not overlap (+33.8 to +48.9 against +58.0 to +75.4),
  so the longer training with decay also paid off in play: about 25 Elo, give or take 12, from two separate matches
  with different openings.
- 9 games ended on time, 3 lost by the candidate and 6 by the lock, after one guard suspension (01:05:11).
  Without the 6 opening pairs involved: +66.5 (+57.9 to +75.2).
- No crash, no illegal move, no disconnect.
- Evidence: `results/phase2/m5/`.

### MN2: candidate 3 at equal nodes (speed taken out)

The same settings as MN1: 250,000 nodes per move for both engines, no clock, 3,000 games, seed 2026111109.

| Games | Wins | Draws | Losses | Score | Elo | 95 % interval | Pairs 0 / 0.5 / 1 / 1.5 / 2 |
|---:|---:|---:|---:|---:|---:|---|---|
| 3,000 | 1,042 | 1,386 | 572 | 57.83 % | **+54.9** | +47.4 to +62.5 | 15 / 222 / 638 / 528 / 97 |

- No game ended abnormally and the guard did not suspend the match.
- **Reading:** candidate 1 scored -4.8 under these settings and candidate 3 scores +54.9. Per node searched, the
  weight-decay net evaluates clearly better than combo29's residual net plus hand-crafted evaluation. This result
  does not depend on machine speed, load or the guard.
- At equal time candidate 3 scored +66.6 (M5, different openings), 12 Elo more than at equal nodes. For candidate 1
  that difference was 17 Elo (+12.4 against -4.8). Each of these figures carries an interval of 7 to 9 Elo, so the
  two differences cannot be told apart, but the direction fits the speed measurement: candidate 3's net leaves the
  engine 9.5 % faster than the lock in nodes per second, candidate 1's net 19.8 % (section 6b).
- Evidence: `results/phase2/mn2/`.

### All matches of both phases side by side

| Match | Net | Condition | Games | W / D / L | Elo | 95 % interval | Lost on time (candidate / lock) |
|---|---|---|---:|---|---:|---|---|
| Phase 1 | candidate 1 | 6 s + 0.06 s | 3,000 | 821 / 1,465 / 714 | +12.4 | +5.1 to +19.7 | 5 / 3 |
| MN1 | candidate 1 | 250,000 nodes | 3,000 | 791 / 1,377 / 832 | -4.8 | -12.5 to +3.0 | none |
| M2 | candidate 2 | 6 s + 0.06 s | 3,000 | 960 / 1,435 / 605 | +41.3 | +33.8 to +48.9 | 19 / 25 |
| M3 | candidate 3 | 10 s + 0.1 s | 2,000 | 662 / 1,001 / 337 | +57.0 | +48.3 to +65.7 | 7 / 6 |
| M5 | candidate 3 | 6 s + 0.06 s | 2,000 | 703 / 973 / 324 | +66.6 | +58.0 to +75.4 | 3 / 6 |
| MN2 | candidate 3 | 250,000 nodes | 3,000 | 1,042 / 1,386 / 572 | +54.9 | +47.4 to +62.5 | none |

13,000 games in phase 2. No crash, no illegal move and no disconnect in any of them.

## 8. Test set 2, scored once

2,000,000 rows from shards 037 and 039, which no set of this job had used (`manifests/test2_manifest.json`:
pool 13,085,679 rows; removed 1,033 duplicates, 4,996 positions that occur in the training set, 306 in shards
013/014 and 250 in shards 036/038; sampled per phase bin with seed 2026111103; file sha256 `ad5cd806...84ef`).
It was scored in one session at 00:52 to 00:54, after the candidate list had closed, and never before
(`results/phase2/test2/`, with the scorer's access log).

| Evaluator | Test set 2 (blend 0.6) | Blend 0.8 | Teacher only (blend 1.0) | Selection set, for comparison |
|---|---:|---:|---:|---:|
| **Candidate 3** (decay 1.0, 10.0B) | **0.014070** | 0.006226 | 0.003858 | 0.013882 |
| Candidate 2 (decay 1.0, 2.0B) | 0.014259 | 0.006383 | 0.003985 | 0.014081 |
| combo29's evaluator (s198 + HCE) | 0.014527 | 0.006822 | 0.004595 | 0.014311 |
| Candidate 1 (phase 1, no decay) | 0.014676 | 0.006801 | 0.004403 | 0.014480 |
| FB2 best net | 0.014826 | 0.007179 | 0.005009 | 0.014640 |
| Hand-crafted eval alone | 0.017237 | 0.008429 | 0.005098 | 0.017044 |

- The ranking on the untouched set is the ranking on the selection set, and the distances are the same: candidate 3
  is 3.1 % better than combo29's evaluator on test set 2 (3.0 % on the selection set); candidate 1 is 1.0 % worse
  (1.2 %). The choices made on the selection set did not over-fit it.
- The phase-1 final-test set (shards 036/038) was not opened in phase 2.

## 9. The training recipe that came out of this

For a standalone H512 net on this data (271.8M unique rows from shards 001-035 without 013/014):

1. **Keep the phase-1 recipe:** FB1/FB2's net and quantisation-aware training with the factoriser, Adam, batch 8192,
   target = 0.75 x teacher + 0.25 x game result, natural sampling, cosine cycles from 5e-4 down to 2.5e-5 with 500
   warm-up steps, stage ends at 1B, 2B, 4B, 7.4B and 10B presentations.
2. **Add decoupled weight decay on the king-bucketed first-layer weights only:** after every optimiser step
   `w1 *= 1 - lr * lambda`, with lambda between 0.3 and 1.0. In this job's trainer that is the plan key
   `"weight_decay": {"w1": 0.3}` (`train/train_h512_gpu.py`).
3. **Do not decay the shared factoriser weights** (tested: harmful). The biases and the output layer were not decayed
   in any run above; decaying them on their own was not tested.
4. **Do not train without decay past about 1B to 2B presentations on this data.** Unseen positions get worse from
   there while the training loss keeps falling.
5. **Watch the fit gap.** Score a fixed sample of training rows next to the unseen selection set at every checkpoint.
   Without decay the gap was 0.00147 at 2B and 0.00166 at 4B; with decay 1.0 it stays at 0.00044.
6. Weight averaging is not needed once decay is on.
7. Cost on the RX 7900 XT, with the CPU busy playing a match: 1.8M to 2.0M positions per second; 8.0B presentations
   took 81 minutes including 36 scored checkpoints.
8. **No warm start is needed.** From random initialisation the same recipe (decay 0.3 from the first step) reaches
   0.013882 at 10B in 103 minutes, level with candidate 3 (section 5c). A new net of this kind can be trained from
   nothing in under two hours on this GPU.

What it gives: selection loss 0.01408 after one cycle with decay and 0.01388 at 10B, against 0.01448 without decay
and 0.01431 for combo29's evaluator. What limits it now is the data: with decay the gap between seen and unseen rows
no longer grows, and each further cycle adds less (0.000021 from 7.4B to 10B). More self-play data is the next
lever, not more passes.

## 10. Limits of this evidence

- **These are screens, not the gate.** One machine, one evening, 2,000 to 3,000 games per match, time controls of
  6 s + 0.06 s and 10 s + 0.1 s, Threads 1. QA's gate decides.
- **Timed matches ran with the GPU busy** and lost games on time to guard suspensions (counted by side above).
  The suspensions hit whichever side was to move; the results without the affected pairs are within 0.6 Elo.
- **Matches MN1 to MN2 used the phase-1 executable**, whose PGO profile was collected with candidate 1's net loaded.
  The rebuilt executable (section 6b) is as fast as the old one on the same net and played one match of its own (M7).
- **Speed depends on the net.** I had assumed the 19.8 % speed advantage measured in phase 1 would carry over to the
  new nets, because the arithmetic is the same. It does not: with candidate 3's net it is 9.5 %. The declarations of
  MN1 and MN2 still state the old figure (17 % less time per move at equal nodes).
- **One seed per recipe.** Run-to-run noise was measured once (0.000003, control arm W0). The decay effect is a
  hundred times larger, but the fine ranking of decay 0.3 against 1.0 rests on single runs.
- **The selection set was used for about twenty choices in phase 2** (pilot arms, averages, checkpoints, candidates).
  It has 2,000,000 rows, so the bias from that is small, and test set 2 (section 8) is the independent check.
- **Every candidate descends from a net that first trained 1.0B presentations without decay** (FB2's warm start plus
  phase 1's first stage). The from-scratch run (section 5c) reaches the same selection loss without that, but no
  from-scratch net was scored on a held-out test set, checked for parity or played.
- **Not tested, as in phase 1:** Threads above 1 on the standalone path, clocks longer than 10 s + 0.1 s, sanitizers.
- **Sets are separated by shard file and by position, not by game id** (the rows carry none), as in phase 1.

## 11. Files and hashes

Nets, checkpoints and PGNs are local (`D:\forge_jobs_20261111\h512E\_work\`), not in the repository. Everything of
phase 1 listed in `REPORT.md` section 15 is still in place and unchanged.

| What | Path | md5 |
|---|---|---|
| **Candidate 3 net (final candidate)** | `_work\nets\h512_cand_W2_seen10000023552.fnn3` | `aab64b3342d7c1c33e82845f5d2d1fa4` |
| Candidate 3 float checkpoint | `_work\nets\h512_cand_W2_seen10000023552_float.pt` | `295828fd438138194aad00bf181d65b5` |
| Candidate 2 net | `_work\nets\h512_cand_W2_seen02000003072.fnn3` | `ae0d372e3748fc6d4e27c2885b164d46` |
| Candidate 2 float checkpoint | `_work\nets\h512_cand_W2_seen02000003072_float.pt` | `4fd2d9fb4834443a54690fc1bd4cd5f8` |
| Candidate exe, phase-1 build (matches MN1 to MN2) | `_work\builds\h512_v3_d59e905d3372\forge_fair_h512_v3.exe` | `5c46cd2d43bc051df1a39e841487b95f` |
| **Candidate exe, rebuilt with candidate 3's net (match M7)** | `_work\builds\h512_v3_c3_29ea1b67b2dd\forge_fair_h512_v3_c3.exe` | `0b9da97c2a859d6e75642db23536de90` |
| Lock exe (opponent) | `forge-combo29\windows\forge_clang_combo29_trial_w6.exe` | `c0051c99695f48bf93272d96fe7548c3` |
| Decay-1.0 run: latest / 4B / 7.4B / 10B states | `_work\runs\arms\wdc_W2\latest.pt`, `stage_S3.pt`, `stage_S4.pt`, `stage_S5.pt` | `f8873753be41295745f98b047d434941`, `bc6bc904047b5a96af29c94b798b088c`, `6e9cf8f31ffedf30a4a174f730810802`, `295828fd438138194aad00bf181d65b5` |
| Decay-1.0 run: nets at 4B / 7.4B | `_work\runs\arms\wdc_W2\net_seen04000014336.fnn3`, `net_seen07400022016.fnn3` | `24480d3019b595a79d6766948821495b`, `e2ca566663ffedcf9c042a6d0b37cbe6` |
| Decay-1.0 pilot arm W2: state at 2.0B | `_work\runs\wd\W2\stage_S2.pt` | `168c596795a5b0096ed54452bfb249e8` |
| Decay-0.3 run: best state (7.25B), 7.4B state, 7.4B net | `_work\runs\arms\wd2c_X1\best.pt`, `stage_S4.pt`, `net_seen07400022016.fnn3` | `8ed4b9123f0b132ede30058ef340fc42`, `77ae48b44da733acc282a36299d10408`, `46a1907ee4e1299fafde4c783cddee70` |
| No-decay run, paused: resumable state, 4B state | `_work\runs\phase2\latest.pt`, `stage_S3.pt` | `4e90858fb4833dd70b4d0443aba82028`, `4482683bfdfd46d76291a7ad5c78820d` |
| Test set 2 (scored once) | `_work\data\final_test2_2m.pos`, `.hce` | `9574073e2b519dd5cc7c649ede09bfab`, `c7267e9dd67793658ab21e37053f60b7` |
| Training-row sample (diagnostic) | `_work\data\train_sample_2m.pos` | `776cc15039785de12cddc9b6fea75b93` |
| PGNs: MN1, M2, M3, M5, MN2 | `_work\match\<match folder>\games.pgn` | `a13bdce284a767f917a571aca7b5d45f`, `ad419cd9fc692bf1b08a7cfc61369928`, `e139c98d6c5f263cf7b07254d03e2b75`, `6c955aec37111c917beb90cf91ddf978`, `dac559926b3423dcc29085e403286f59` |
| From-scratch run: 10B net and state (not a candidate) | `_work\runs\arms\scratch_wd\net_seen10000023552.fnn3`, `stage_S5.pt` | `21851771a34a061d7bace67f11942c29`, `217ecaf8b7355fe1f2b34be43cef7a15` |
| Test set 3 (built, never scored) | `_work\data\final_test3_2m.pos` | sha256 in `manifests/test3_manifest.json` |
| Plans: decay pilot W2, its continuation, decay 0.3 arm, its continuation, from scratch | `train/plans/wd_W2.json`, `wdc_W2.json`, `wd2_X1.json`, `wd2c_X1.json`, `scratch_wd.json` | `f8982948ea19d55df6b3323874b71f1f`, `85f0b46c638e1e62342103a66a7bb028`, `2c7c9e84e26acbd059a72c3db4c61e77`, `46a3b27b24fffbe19145af4907ebf8cd`, `5c86896e3adcdfc96154a2af912cd9da` |

Evidence in the repository, all under `results/phase2/`: the declaration; `tables.md`; one folder per match (`mn1`,
`m2`, `m3`, `m5`, `mn2`) with the result recomputed from the PGN, run info, compressed log, PGN md5 and the time
losses with the guard's log lines; `wd/`, `wd2/`, `wdc_W2/`, `wd2c_X1/`, `scratch_wd/` with the runs' own metrics and
logs; `FROZEN_CANDIDATE_2.json`, `_3.json`, `FREEZE_4_NO_NEW_CANDIDATE.json`; parity and bench files of candidates
2 and 3; `test2/` with the scores and the access log; the score files of the averages and of the training-row sample.

To reproduce the recipe: `bash h512/train/run_wd_pilots.sh W2` trains the pilot cycle from the phase-1 state at 1.0B
(run folder `_work/runs/wd/W2`), `bash h512/train/run_arm.sh wdc_W2 /d/forge_jobs_20261111/h512E/_work/runs/wd/W2/stage_S2.pt`
continues it to 10B, and `bash h512/train/run_scratch.sh` runs the recipe from random initialisation. Matches:
`results/phase2/launch_match.sh`, `launch_match2.sh`.

## 12. Process, resources and deviations

- **Processes.** Everything phase 2 ran was started by this job: the trainer (one at a time, through its own queue
  scripts under `train/`), five fastchess matches and one 8-game check with their engines, and short scoring and
  parity runs. No gate
  queue, self-play process, hold or STOP file of anyone else was touched. No process was killed; runs were ended
  only with the trainer's own STOP flag (the no-decay run at 20:53:46, arm X4 at 23:44:20), and this job's GPU queue
  script with its own stop flag after the last run (02:35:23). No process of this job is alive at the end.
- **The owner's guards were not bypassed.** `resource_guard.ps1` suspended this job's timed matches for 5 seconds at
  a time when its CPU reading went over 90 C (five times in M2, twice in M3; section 7). The trainer has its own holds
  (GPU hot spot 76 C, memory junction 86 C, disk floor) and paused itself twice for 5 seconds in pilot arm W1
  when the memory junction read 86 C.
- **Disk.** D: fell from 33.7 GiB free to 31.0 at the lowest (02:35) and stands at 31.3 at the end; the owner's
  cleanup acts below 30 GiB. To stay clear of that, this job removed redundant files of its own phase-2 runs, always
  by literal path: 29 duplicate checkpoints (the pilot arms' copies of the 1.0B start state and their `best.pt` /
  `latest.pt`, which repeat the kept end state `stage_S2.pt`; two replayed start states of the continuations; the
  stopped arm X4's state; five float files of averages) and 27 mid-cycle nets of the decay-1.0 run. Nothing of
  phase 1 and nothing cited in this report was removed; the kept files were re-checked against their recorded
  hashes afterwards. C: and F: stayed above 32 GiB. E: was not written to. Phase 2 holds about 2.3 GiB under `_work\`.
- **A safety check refused one edit** that would have added an `rm` with a variable path to a queue script. The line
  was left out; the later removals above used literal paths.
- **`STATUS.md` was damaged once by my own scripted edit** (21:44): two Windows paths lost their backslashes. It was
  repaired in the next commit, and later edits of that file went through a splice script that refuses control characters.
- **`launch_match.sh` was edited while M2 was running through it.** Bash printed a syntax error from that file after
  the match had ended; the match itself was not affected (fastchess exit 0, 3,000 games). Later matches use a
  separate launcher file.
- **Clock times in the declaration.** Several addenda were first stamped from my running estimate of the time, which
  ran one to four minutes ahead of the PC clock. They were corrected to the PC clock; the commit times are the record.
- **Plans that were declared and then not run:** the snapshot-averaging run `swa_C1` and the running-average arm
  `ema_E1` (superseded by weight decay, addendum 5); arm X4 (stopped, addendum 9); the 20B stage; the rest of the
  no-decay run past 4.0B; match M6 and the scoring of test set 3 (their condition in addendum 10 was not met).
- **Changes to declared match sizes, each declared before the match started:** M3 with 2,000 games instead of 3,000
  (addendum 7), M5 with 2,000 instead of 3,000 (addendum 8).
- **Engine sources were not changed in phase 2.** The only code changes are in the trainer and the job's own tools:
  `--clear-stop`, weight decay, running averages (unused in the end) and random initialisation in
  `train/train_h512_gpu.py`, plus new scripts under `tools/`, `train/` and `results/phase2/`.
  `fair_eval/configs.json` gained one net entry (`h512_cand3`) and one build configuration (`h512_v3_c3`) for the rebuild.

## 13. Time record

Times are read from the logs (PC clock).

| Item | GPU or CPU | From - to |
|---|---|---|
| Owner's request, declaration written and committed | | 20:29 - 20:34 |
| No-decay run continued from 2.0B, paused at 4.0B | GPU | 20:34:47 - 20:53:46 |
| Match MN1 (candidate 1, equal nodes) | CPU | 20:38:52 - 21:33:47 |
| Test set 2 built; over-fitting diagnostic; weight averages | | 20:40 - 20:58 |
| Weight-decay pilot, arms W0 to W3 | GPU | 20:53:56 - 21:40:24 |
| Candidate 2 frozen, parity, bench | | 21:41 |
| Decay 1.0 continued to 10B | GPU | 21:40:30 - 23:01:23 |
| Match M2 (candidate 2, 6 s + 0.06 s) | CPU | 21:41:40 - 23:03:22 |
| Second pilot round, arms X1 to X5 | GPU | 23:01:23 - 23:55:54 |
| Candidate 3 frozen, parity, bench | | 23:03 - 23:04 |
| Match M3 (candidate 3, 10 s + 0.1 s) | CPU | 23:04:27 - 00:34:13 |
| Decay 0.3 continued to 7.4B | GPU | 23:55:54 - 00:51:21 |
| Match M5 (candidate 3, 6 s + 0.06 s) | CPU | 00:34:24 - 01:28:43 |
| From-scratch run to 10B | GPU | 00:51:21 - 02:35:03 |
| Test set 2 scored once | | 00:52:06 - 00:54:31 |
| Match MN2 (candidate 3, equal nodes) | CPU | 01:28:53 - 02:22:53 |
| Report, final checks, final push | | 02:23 - 02:55 |

- The GPU trained from 20:34 to 02:35 with gaps of seconds between runs. The CPU played matches from 20:38 to 02:22,
  with one gap of 8 minutes (21:33 to 21:41, waiting for the last pilot arm, as declared) and seconds between the others.
- About 33 billion training presentations in 13 runs, and 13,000 match games.
- Phase 2 used about 6 hours 25 minutes of the 7.5 hours offered. The remaining time was not padded: the declared
  work was finished and no further experiment was pending.

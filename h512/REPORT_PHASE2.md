# JOB E phase 2 (follow-up) - Standalone H512: over-fitting found, weight decay fixes it - REPORT

**DRAFT while phase 2 is running (22:05). Sections 1 to 4 are final; the later sections are added as results arrive.**

Branch `fable/standalone-h512-20261111`, measured 2026-11-11 from 20:30 on grok-pc. This file continues `REPORT.md`
(phase 1), which is unchanged. Paths are under `h512/` unless they start with a drive letter or `_work\`.
Rules and their timing: `results/phase2/PHASE2_DECLARATION.md` (the declaration and six addenda, each committed before
the results it governs). Generated tables: `results/phase2/tables.md`. Running record: `STATUS.md`.

## How phase 2 came about, and what it changes against the phase-1 plan

The owner asked at 20:29 to use the remaining 7.5 hours of the allowance, wrote "you can go for 10b", and asked for
GPU and CPU to work at the same time. Phase 1 had stopped training at 2.0B presentations by its own plateau rule.

Deviations from the phase-1 plan, all on the owner's instruction or declared before the result they affect:

- **The plateau rule was set aside** to train on past 2.0B.
- **GPU and CPU ran together.** Timed matches were played while the trainer used the GPU and one CPU thread. Both
  engines of a match play under the same load and every opening is played with both colours.
- **The run without weight decay was paused at 4.0B**, when it was getting worse on unseen positions (section 2).
  It is resumable. The 10B the owner asked for was reached with the weight-decay recipe instead (section 5).
- **The candidate executable was not rebuilt.** Every net of phase 2 is loaded by the phase-1 exe
  (md5 `5c46cd2d43bc051df1a39e841487b95f`); its PGO profile was collected with candidate 1's net.
- **Decisions use the selection set only.** The phase-1 final-test set was not opened again. A second test set from
  shards 037/039 is scored once, after all training (section 8).

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
- **Decay only the king-bucketed weights.** Decaying the shared factoriser weights as well is harmful (0.014915): they
  carry the piece-square knowledge that all king buckets share.
- **Keep alpha 0.25.** With decay, alpha 0.4 is still worse (0.014127 against 0.014083), although the selection loss
  itself is measured against the alpha-0.4 target, and its fit to the teacher scores is much worse.
- X4 was stopped 34M presentations into its cycle (addendum 9): it is X3 plus one more decayed group, X3 had just shown
  that group of changes to be harmful, and X3 had also run at half the usual speed.

X1 beat W2 by more than 0.00002, so by the declared rule its run was continued (next table). Evidence:
`results/phase2/wd2/` (metrics and logs, `WINNER_ROUND2.txt`).

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

## 7. Matches

All matches are this job's own screens against the original lock exe (md5 `c0051c99695f48bf93272d96fe7548c3`),
not the crew gate. Each was declared with its exact net hash before its first game (`results/phase2/*_DECLARATION.md`).
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

## 10. Limits of this evidence

- **These are screens, not the gate.** One machine, one evening, 2,000 to 3,000 games per match, time controls of
  6 s + 0.06 s and 10 s + 0.1 s, Threads 1. QA's gate decides.
- **Timed matches ran with the GPU busy** and lost games on time to guard suspensions (counted by side above).
  The suspensions hit whichever side was to move; the results without the affected pairs are within 0.2 Elo.
- **The executable was not rebuilt** for the new nets. Its PGO profile was collected with candidate 1's net loaded.
  NPS was not re-measured for the new nets; the weights change, the arithmetic does not.
- **One seed per recipe.** Run-to-run noise was measured once (0.000003, control arm W0). The decay effect is a
  hundred times larger, but the fine ranking of decay 0.3 against 1.0 rests on single runs.
- **The selection set was used for about twenty choices in phase 2** (pilot arms, averages, checkpoints, candidates).
  It has 2,000,000 rows, so the bias from that is small, and test set 2 (section 8) is the independent check.
- **Weight decay was only tried on a net that had first trained 1.0B presentations without it** (FB2's warm start plus
  phase 1's first stage). Section 5b reports what was tried beyond that.
- **Not tested, as in phase 1:** Threads above 1 on the standalone path, clocks longer than 10 s + 0.1 s, sanitizers.
- **Sets are separated by shard file and by position, not by game id** (the rows carry none), as in phase 1.

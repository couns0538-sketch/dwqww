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

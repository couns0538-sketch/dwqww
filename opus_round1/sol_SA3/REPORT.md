# S-A3 Longer LR schedule as trainer arguments (train_resid_v3d.py, gate G-A3) — DONE (CPU smoke on the PC; GPU, real data and strength UNVERIFIED; nothing queued)

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 40; `OPUS_TEST_PLAN.md` row 3: G-A3 "Longer LR schedule (one schedule per gate)",
EVAL, srand 958591904. Built after S09-2 (v3b defaults restored, f006 recipe as args, `opus-sol-S09fix`). Branch `opus-sol-SA3` =
`opus-sol-S50` (`ff98828a`) + `2615addd` (job) + the report commit. Tool-only (no engine code, no engine option): `[skip ci]`;
engine diff vs 294dbed empty. Machine exclusive: no (gates, self-play and NNUE training ran throughout). Work and results by a
sub-agent; this report text is its hand-back.

**Deliverable:** `train_resid_v3d.py` (md5 `e1a092247230996e91507c7149ec9e0a`, sha256 `c1a42ecd…`) = opus-sol-S50's
`train_resid_v3c.py` + `--lr-schedule {cosine,linear,wsd}` (default cosine = v3b), `--lr-schedule-epochs E` (horizon, default 0 =
`--epochs`), `--lr-decay-frac F` (wsd only, default 0.2). The floor is v3b's existing `--min-lr-frac` for every schedule (no
separate floor option: it already exists). `v3c_to_v3d.diff` (+65/-5), `v3b_to_v3d.diff` (+214/-9), `CHANGES_v3d.md`,
`sa3_queue_lines.txt` + `opus_sa3_queue_dryparse.py`, runner, 38 tests, 28-mutant check, logs. Run only as
`F:\opus_scratch\sol_SA3\opus_nnue_smoke_sa3_v3d.py` (with `_v3b` and the S50 `_v3c` copies beside it).

## Acceptance
| item | result | evidence |
|---|---|---|
| defaults give all 8 smoke artifacts sha256-equal to v3b and to the S50 v3c (seed 99, 2 epochs, CPU) | **PASS** | v3d defaults x2 and with the three defaults spelled out vs v3b_1 and the S50 v3c: all 8 artifacts (.pt .inc .bin .json x 2 epochs) sha256-equal (ep2 .inc md5 `bf6d2812f517012b269ac25755d4ab4d`), normalized stdout and settings dump equal (`logs/step04_compare_r1.log`) |
| per-step lr of every schedule = an independent reference formula (all steps, incl. warmup and the last step) | **PASS** | `test_v3d_sa3.py` (11 new tests, real in-process runs, Adam's `param_groups[0]["lr"]` recorded at every step): default = v3b's own run bit for bit (`float.hex`); linear, wsd F=0.3 (round-half-up 28.8 -> 29), wsd with the decay clamped to the warmup end, each schedule with a 1-epoch horizon run for 2 epochs (exactly the floor after it), cosine with a 6-epoch horizon = numpy reference (rtol 1e-12; first warmup step exact; wsd stable phase exactly the peak) (`logs/step02_unit.log`, 38/38 with the 27 S50 tests) |
| deterministic (same .inc md5 twice) | **PASS** | linear `0fb0c666…`, wsd `f48dbeb2…`, cosine with a 6-epoch horizon `a124b0e7…`, wsd + `--epoch-positions 100000 --recent-weight 3` + `--init-weights` `69eea375…`: 8 artifacts + stdout equal |
| resume mid-run: same lr at every later step, same epoch artifacts | **PASS** | unit: 3-epoch wsd run resumed from epoch 1 -> lr bitwise equal at all 96 later steps; smoke: wsd and long-horizon cosine resumed from epoch 1 -> epoch-2 .inc/.bin/.json sha256-equal, .pt content bitwise-equal |
| plan long / stop early / extend (`--lr-schedule-epochs`) | **PASS** | smoke: stop at epoch 1 of a 2-epoch horizon, resume with `--epochs 2` = the uninterrupted run (constant blend; epoch-1 .inc/.bin, epoch-2 .inc/.bin/.json, .pt content); unit: lr bitwise equal; `--lr-schedule-epochs 2` (= `--epochs`) gives v3b's .inc/.bin and loss lines |
| works with `--epoch-positions` and `--init-weights` | **PASS** | wsd_on_init x2: INIT CHECK OK, 97 steps/epoch, wsd over 194 steps with decay from step 155, config records epoch_positions, recent_weight, init_weights_md5 and the schedule |
| the settings dump / .json record the schedule | **PASS** | linear, wsd, long cosine: `.json`/`.pt` config `lr_schedule`, `lr_schedule_steps` (+ `lr_decay_frac`, `lr_decay_start_step` for wsd); settings dump lists all three options; stdout `lr schedule: …` line; defaults record nothing (v3b bytes) |
| planted bugs caught | **PASS** 28/28 | run 1: 27/28; its mutant 20 (`s < d0` -> `s <= d0`) is equivalent (no lr change, finding 2) and was replaced by an off-by-one that reaches the floor one step early: caught (`logs/step06a_mutation_run1.log`, `step06b_mutation_rerun20.log`); each mutant caught by its named test |
| 10k-step RSS trace flat (loop unchanged apart from the lr call) | **PASS** | `main()` from `sc_dev` to its end and all v3b definitions source-identical (tests); trace v3d `--lr-schedule wsd`: after step 2600 within 36 KiB, -7.3 B/step (v3b -6.1), same one-time steps (`logs/step05_rss_t1.log`) |
| 2-3 queue lines, one schedule per gate, dry parse, GPU hours, srand | **PASS** (lines UNPROVEN) | `sa3_queue_lines.txt`: f006 base + wsd e48 / linear e48 / wsd e64; all parse through v3d's real checks with the supervisor's added args; 2.64 / 2.64 / 3.53 GPU h (table below; `logs/step07_queue_dryparse.log`) |
| no GPU, nothing queued, supervisor | **PASS** | no PC dir written; 7 "adopted running job" lines before and after every step (all from the earlier incident) |

## Proposed G-A3 lines (UNPROVEN; not queued; CR PASS + crew vote first, then the crew copies train_resid_v3d.py + qa_adam_dml.py to the tools folder)
Base: f006 recipe `--residual --init-check --final-full-val --log-every 60 --shape 256 --epochs 48 --lr 7.07e-4 --blend-end 0.6
--seed 25 --batch-size 8192 --warmup-steps 300 --val-positions 1000000` (floor 0.01, blend from 1.0). Data at 15:35: 30 train
shards, 241,913,894 rows -> 29,530 steps/epoch.

| line | schedule | steps | GPU hours at 1.22M pos/s |
|---|---|---|---|
| `resid_h256_e48_a3wsd02_lr707e4_b06_s25_bs8k … --lr-schedule wsd --lr-decay-frac 0.2` | peak 7.07e-4 to step 1,133,952, then linear to 1 % | 1,417,440 | 48 x 29,530 x 8192 = 11,611,668,480 pos / 1.22e6 = 9,518 s = **2.64** |
| `resid_h256_e48_a3lin_lr707e4_b06_s25_bs8k … --lr-schedule linear` | straight line to 1 % (3.57e-4 at half) | 1,417,440 | **2.64** |
| `resid_h256_e64_a3wsd02_lr707e4_b06_s25_bs8k … --epochs 64 --lr-schedule wsd --lr-decay-frac 0.2` | peak to step 1,511,936, then linear | 1,889,920 | 15,482,224,640 pos = 12,690 s = **3.53** |

Each new sealed 10M-row shard adds 0.109 h (e48) / 0.146 h (e64); holdout evals not included. srand 958591904 = the first G-A3
gate only; further G-A3 gates need fresh srands from QA (never reuse). Suggested first gate: line 1 (same length and data as f006,
only the schedule shape differs). See also `opus-sol-A7` (main session): its frozen-data protocol (`--max-train`) can be added to
these lines so the schedule comparison is at equal data.

## Findings
1. **The floor already exists**: v3b's `--min-lr-frac` (default 0.01) is the cosine floor; v3d applies it to every schedule
   rather than adding a `--lr-floor-frac` that would duplicate it.
2. **Equivalent mutant**: making wsd's stable phase end one step later changes nothing, because the decay formula's first value
   is exactly the peak (`f + (1-f)*1 == 1.0`). Replaced by a real off-by-one (floor one step early), which the tests catch.
3. **The blend ramp still follows `--epochs`** (v3b). `--lr-schedule-epochs` makes the lr curve extendable, but a run extended
   with a larger `--epochs` changes its blend ramp unless `--blend-start` = `--blend-end`. A blend horizon would be the matching
   knob (not added: LR-only scope).
4. **v3b's `steps/epoch=… lr=… cosine blend …` line always said "cosine"**; v3d prints the schedule name there (identical text
   with the defaults).
5. **Data size moved during the job**: shard 032 was sealed at 15:18 (30 train shards, 241.9M rows); the GPU estimates use that
   count and grow ~0.11 h per shard at e48.

## How it was run
Read-only venv (Python 3.10.22, torch 2.4.1+cpu) with `-I -B`, `nice -n 19`, children at Idle, 1 Torch thread, OMP/MKL/OpenBLAS
1, TMP/TEMP and outputs under `F:\opus_scratch\sol_SA3`, available RAM >= 9.26 GiB throughout (floor 6). Stage (pins: v3b
5cebba4d…, S50 v3c ddff28bb…, qa_adam_dml 799faa89…, data32 sample) -> 38 tests (47 s) -> suite r1 (20 runs) -> compare 20/20 ->
10k-step trace -> 28 mutants (run 1 27/28 + replacement) -> dry parse. All step logs record the supervisor line count before/after.
No `train_resid` name appeared on any Python command line (the dry parse reads its lines from a file).

## Files
`train_resid_v3d.py`, `v3c_to_v3d.diff`, `v3b_to_v3d.diff`, `CHANGES_v3d.md`, `sa3_queue_lines.txt`, `opus_sa3_queue_dryparse.py`,
`opus_nnue_smoke_sa3.py`, `test_v3d_sa3.py`, `mutation_check_sa3.py`, `README.md`, `IDEA_SOURCE.md`, `REPORT.md`, `FILES.txt`,
`SHA256SUMS`, `logs/` (8 step logs, `sa3_outputs.tar.gz` 35,914 B; .pt/.inc/.bin stay in `F:\opus_scratch\sol_SA3\out\`).

## UNVERIFIED / left
- Any GPU run, real-data loss, strength (no gate run; no Elo claim), which schedule suits the H256 net, the 1.22M positions/s
  figure (A7 spec value; the measured v3b whole-run mean is 1.344M/s per `opus-sol-A7`).
- Deployment and queueing: CR PASS + crew vote; fresh srands for any G-A3 gate after the first.

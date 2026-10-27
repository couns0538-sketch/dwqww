# S50 Trainer warm-start `--init-weights PATH` (v3c, default OFF) — DONE (CPU smoke on the PC; real finished-run warm start and GPU UNVERIFIED, not deployed)

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 31; spec = Sol's inventory `jobs[]` id S50 (spec line 265, NOT_STARTED, depends
on S39; Sol left no S50 files). Branch `opus-sol-S50` = `opus-sol-S39` (`093869a2`) + `0fa2c831` (job) + the report commit.
Tool-only: `[skip ci]`; engine diff vs 294dbed empty. Machine exclusive: no. Work and results by a sub-agent; this report text
is its hand-back.

**Deliverable:** `train_resid_v3c.py` (md5 `e7fefe7772fcf629f3b8f7a2a6e05241`, sha256 `ddff28bb…`) = the S39 v3c +
`--init-weights PATH`; it supersedes `../sol_S39/train_resid_v3c.py` (S39 code unchanged: `v3c_s39_to_s50.diff`, +64/-2);
`v3b_to_v3c.diff` (+149/-4), `CHANGES_v3c.md` (whole v3c), smoke logs. Run only as the copy
`F:\opus_scratch\sol_S50\opus_nnue_smoke_s50_v3c.py`.
Behaviour: model weights only (trainer `.pt` or bare state_dict, `weights_only=True`); fresh Adam, step 0, fresh lr
warmup/cosine and blend ramp; md5 of the file in the settings dump, the `.json`/`.pt` config and stdout; `--init-check` compares
the loaded net with the checkpoint's stored val; `--resume` wins (init not loaded); other hidden/residual, shape mismatch,
non-finite weights refused; a missing file is an argparse error before the run dir exists.

## Acceptance
| item | result | evidence |
|---|---|---|
| (a) OFF gives bit-identical weights and loss to v3b (seed 99, 2 epochs) | **PASS** | off_1/off_2 vs v3b_1: 8 artifacts sha256-equal, whole stdout + settings dump equal (`logs/step04_compare_r1.log`); all 11 S39 cases byte-identical to the S39 file's runs (`logs/step07_s39r2_vs_s50r1.log`) |
| (b) init from a checkpoint with lr 0 for 1 epoch reproduces its loss to the last printed digit and its exported .inc md5 | **PASS** | source = v3b_1 `epoch002-step000000390.pt` (md5 5bd3de20e55b292b593307c8d987a983); warm_lr0: .inc md5 `bf6d2812f517012b269ac25755d4ab4d` = the source's; .bin equal; EPOCH 1/1 `HOLDOUT n=16,384 mse_teacher=0.021902 (HCE 0.021899, -0.01%) mse_b0.6=0.045335 (HCE 0.045332, -0.01%) mse_b0.8=0.023798` = the source's EPOCH 2/2; .json val equal at full precision; FINAL line equal; `INIT warm-start net: mse_teacher=0.021902 mse_b0.6=0.045335 (checkpoint val 0.021902/0.045335)` + INIT CHECK OK |
| (c) no per-step allocations or new Python scalars (RSS trace over 10k steps flat) | **PASS** | training loop + 24 shared definitions source-identical to v3b (tests); 10k-step trace of v3c with `--init-weights` + `--epoch-positions 160000 --recent-weight 3`: after step 2600 within 36 KiB, slope -6.1 B/step (v3b: 36 KiB, -6.2 B/step); preregistered \|slope from step 1000\| < 100 B/step: 70.8 (v3b 60.3) (`logs/step05_rss_t1.log`) |
| (d) works with S39 `--epoch-positions` | **PASS** | lr 0 + `--epoch-positions 100000 --recent-weight 3`: same .inc md5 and loss lines; normal lr twice: deterministic (ep2 .inc md5 `9059c1382a4b61e2e473eaa3c8d395fb`), INIT CHECK OK, 97 steps/epoch, config has epoch_positions, recent_weight, init_weights_md5 |
| weights only; fresh optimizer with its own warmup/decay | **PASS** | warm_1 epoch-1 checkpoint: step 195, Adam step 195 (source checkpoint 390); 195 steps/epoch, 390 total = a fresh schedule; unit test: empty optimizer state after loading |
| source md5 in the settings dump | **PASS** | `init_weights_md5` = 5bd3de20… in the settings dump (with the path), the .json/.pt config and stdout |
| deterministic | **PASS** | warm_1 == warm_2 (ep2 .inc md5 `7168e53066deac79d4c376379de6f719`), 8 artifacts + stdout |
| supervisor-style resume (queue args + `--resume`) | **PASS** | epoch-2 .inc/.bin/.json equal to the uninterrupted warm run, .pt content bitwise-equal; `init-weights … not loaded, --resume restores model and optimizer` |
| refusals / warnings | **PASS** | unit tests: missing file -> exit 2, no run dir; hidden/residual mismatch -> ValueError; non-finite -> ValueError; QAT mismatch -> WARNING; another val subset -> INIT CHECK FAILED, exit 3; bare state_dict -> check skipped |
| tests | **PASS** 27/27 | `logs/step02_unit.log` (17 S39 tests on this file + 10 warm-start tests) |
| planted-bug check | **PASS** 17/17 | 8 S39 + 9 S50 mutants, each caught by its named test (`logs/step06_mutation_check.log`) |
| never deployed; no GPU; supervisor | **PASS** | nothing written to PC dirs; 7 "adopted running job" lines before and after (all from the earlier incident) |
| real-data and GPU results | UNVERIFIED (as the spec says) | — |

## Findings
1. **The supervisor relaunches a run with the queue line's args + `--resume`** (`Build-Args` in `nnue_supervisor.ps1`, read
   only), so a resumed warm start still carries `--init-weights`. v3c lets `--resume` win (the init file is not loaded and may be
   gone, md5 then `missing`); otherwise every resume of a warm start would fail and fall back.
2. **The supervisor adds `--init-check` to every fresh launch**, and v3b's check (net == HCE) fails for any warm net. With
   `--init-weights` the check compares against the checkpoint's stored val instead; a warm-start queue line must therefore keep
   the source line's `--val-positions` (the holdout 013/014 is the supervisor default anyway).
3. **A missing init file fails before the run dir exists**: the supervisor skips any launch whose run dir already exists.
4. The resume .pt byte difference of S39 finding 1 (pickle memo, inherited from v3b) applies here too; content is identical.

## How it was run
As S39 (read-only venv, `-I -B`, Idle, 1 thread, `F:\opus_scratch\sol_S50`, RAM floor 6 GiB, supervisor log polled): stage ->
27 tests -> suite r1 (21 runs: the 14 S39 cases + 7 warm-start cases) -> compare 26/26 -> 10k-step trace -> 17 mutants ->
S39 r2 vs S50 r1 artifact comparison.

## Files
`train_resid_v3c.py`, `v3b_to_v3c.diff`, `v3c_s39_to_s50.diff`, `CHANGES_v3c.md`, `opus_nnue_smoke_s50.py` (runner),
`test_v3c_s50.py`, `mutation_check_s50.py`, `README.md`, `IDEA_SOURCE.md`, `REPORT.md`, `FILES.txt`, `SHA256SUMS`, `logs/`
(7 step logs and `s50_outputs.tar.gz`, 35,180 B; .pt/.inc/.bin stay in `F:\opus_scratch\sol_S50\out\`, sha256 in `results.json`).

## UNVERIFIED / left
- A warm start from a finished PC run's `.pt` (e.g. an e48 net), DirectML/GPU, real data, the e48 + 16-32 epoch experiment and
  any strength effect (no Elo claim). Warm-start lr/warmup/blend choices are a recipe question for that experiment.
- Deployment: needs CR PASS + a crew vote, then `train_resid_v3c.py` + `qa_adam_dml.py` copied to the trainer tools folder.

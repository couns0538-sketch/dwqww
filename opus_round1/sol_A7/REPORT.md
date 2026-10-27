# A7 [Astra] Long-training recipe design for the H256 residual net — DONE (design; UNPROVEN, nothing queued)

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 37 (Astra A7; inventory `astra_jobs` A7, spec line 575).
- **Branch:** `opus-sol-A7` = `d4f4312` + `0d99f02` cherry-picked (`96a002ad`) + this job.
- **Scope:** design/analysis only, no engine change (`[skip ci]`), no GPU, no training run, no queue edit.
- **Deliverable:** `forge_astra_A7_long_recipe_20261027.md`, with `forge_astra_A7_queue_lines_20261027.txt`.
- **Overlap:** no opus/fable branch covers A7. It builds on S30 (learning curves) and S44 (Elo vs epochs).

## Acceptance (spec "Pass" items)
| item | result | evidence |
|---|---|---|
| a recipe for e64/e96: LR schedule (warmup, decay shape, floor), batch, blend schedule, when to stop, how to tell from the logs | **DONE** | deliverable §2-§5 |
| 3 ready queue lines using ONLY existing v3b arguments | **DONE** | `forge_astra_A7_queue_lines_20261027.txt` (§6) |
| each line parses with the unchanged v3b argument parser (dry parse shown) | **PASS** | `logs/step3_dryparse.log`. The parser is the 33 `add_argument` calls of a byte-identical renamed copy (md5 `b6758004`). Positive control: f070's argv reproduces the trainer's own settings dump exactly. Supervisor split matches `queue.txt`. 3/3 lines OK; 2/2 negative controls rejected (`--epoch-positions`, `--epochs 6.4e1`) |
| GPU-hour estimate at 1.22M positions/s with the maths | **DONE** | e96 5.25 h, e48 control 2.62 h, e64 3.50 h (steps/epoch 29,296 at `--max-train 240000000`, batch 8192); also at the measured 1,344,201/s: 4.76 / 2.38 / 3.17 h (§6) |
| every recommendation cites a log line or gate number | **DONE** | run logs `file:line`, `LATEST_GATE_FACTS_20261026.md:8-15`, `GATE_RESULTS_SUMMARY_20261025_1215.md:12`, `NETS_snapshot_20261025_1030.md:1485/1618/1621/1626`, `queue.txt:6` |
| uncertainty stated | **DONE** | §0 confidence lines, §7 |
| no GPU use; marked UNPROVEN | **PASS** | CPU-only parsing at Idle; title and lines marked UNPROVEN |
| tools tested | **PASS** | `test_opus_a7.py` 9/9 (`logs/step4_tests.log`); planted bugs 6/6 caught (`logs/step5_mutation_check.log`) |

## Main findings
1. **Data beats length about 5x per doubling.** 43 finished runs (H256, blend-end 0.6, batch 8192, self-play only;
   137M-232M positions):
   - b0.6 changes by −1.65e-4 per doubling of data [−1.79e-4, −1.45e-4];
   - and by −3.3e-5 per doubling of epochs [−4.0e-5, −2.8e-5];
   - lr in the range 7.07e-4 to 9.898e-4 has no measurable effect;
   - the residual sd (7.2e-6) equals the seed sd (7.09e-6).
2. **Predicted gain from length at fixed data** (log-linear, extrapolated): e64 −1.4e-5 and e96 −3.3e-5 b0.6, about
   +0.7 / +1.6 Elo at S44's slope. That is below what a [0,10] gate can resolve.
3. **The spec's premise ("e48 +29.44 H1") did not survive confirmation.** G104 stopped early at 698 games; G104c
   capped at +7.18 ± 8.49; none of the later e48 nets locked against AL1 (G122-G125).
4. **A cosine run cannot be cut short.**
   - In all 43 runs the last quarter still improves the subset b0.6 by 1.5e-5 to 3.9e-5, as the LR anneals.
   - The plateau (within 1 sd of the final value) comes at 79-88% of the run.
   - So "more epochs stopped helping" must be read across runs at equal data: e96 against a same-seed,
     same-`--max-train` e48 control, with the threshold Δ ≤ −2e-5.
5. **v3b fixed the DirectML memory growth.** f070's private memory was 9.97 GB at epoch 1 and 9.99 GB at epoch 48,
   where the v3a run f006 died at its epoch-48 start. Memory now scales with data (8.87 / 9.22 / 9.56 GB after load
   at 222M / 232M / 242M), so 240M fits; `--mmap-data` has never run on the PC.
6. **Measured v3b speed is 1,344,201 positions/s** over the whole run (39 runs). The spec's 1.22M/s is f006's v3a
   rate, so the GPU-hour figures are conservative.

## How it was run
- **Parsing.** S30's unchanged parser (`opus-sol-S30`) read the PC logs in `F:\forge_nnue_train\runs`. Output went
  to `F:\opus_scratch\sol_A7\curves\run1` (the first attempt hit an existing output folder; the tool refuses to
  overwrite).
- **Statistics.** `opus_a7_curve_stats.py` (stats run1 failed on a column name; run2 is final).
- **Dry parse.** `opus_a7_dryparse.py` on the renamed copy `F:\opus_scratch\sol_A7\opus_nnue_smoke_a7_v3b.py`.
  The trainer was never run, and no `train_resid*` file was executed.
- **Tests and planted bugs.** The mutant copies are in `F:\opus_scratch\sol_A7\mutants\run1..run4`:
  - runs 1-2 stopped at the baseline because of a CRLF bug in the test fixture;
  - run 3 caught 5/6;
  - after tightening the plateau fixture, run 4 caught 6/6.
- **Conditions.** All runs at `nice -n 19`, single-threaded, TMP in scratch.
- **Machine exclusive:** no (gates, NNUE training and self-play ran throughout).

## Files
- `forge_astra_A7_long_recipe_20261027.md`, `forge_astra_A7_queue_lines_20261027.txt`;
- `opus_a7_curve_stats.py`, `opus_a7_dryparse.py`, `test_opus_a7.py`, `mutation_check_a7.py`;
- `README.md`, `IDEA_SOURCE.md`, `REPORT.md`, `FILES.txt`, `SHA256SUMS`;
- `results/`:
  - `a7_tables.md`, `a7_stats.json`, `dryparse.json`;
  - `a7_curves.tar.gz` (58,837 B): S30-format `final_table.csv` (sha256 `e226582c…`), `epoch_curves.csv`
    (`7a04d557…`), `seed_spread.csv` (`ba7b531d…`), `summary.json`;
- `logs/step1`-`step5`.

## Left / UNVERIFIED
- Every expected gain until the lines run and a gate decides. The epoch term is an extrapolation beyond 48 epochs.
- A 2.8M-step DirectML run (the longest v3b run so far is about 1.42M steps), `--mmap-data` on the PC, and the e96
  thermal profile.
- An isolating test of a longer low-LR tail. That needs new trainer arguments (S-A3, on branch `opus-sol-SA3`).

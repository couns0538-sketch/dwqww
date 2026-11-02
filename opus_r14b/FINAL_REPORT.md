# Opus R14-B final report (Couns's 15-hour job, 2026-11-02 12:05 PC clock -> ~03:00) - INTERIM (14:45), updated at the end

UNPROVEN everywhere: no Elo or training-quality claims; Engine NNUE / QA decide. Nothing of the live npt line, the
queue, gates, self-play or crew files was touched; own work ran BelowNormal / Idle on CPUs 2-3 within 2 threads
(one exception documented in item 1: an orphaned 3-minute CPU run after a TaskStop).

## Item 1 - fast npt data loader (`opus-r14b-fast-loader`) - DONE except the GPU window (requested, not granted)
- Deliverables (`opus_r14b/item1/`): `fastloader/forge_fastloader.cpp|.py` (own code), `LOADER_SPEC.md`,
  `tools/install_fast_loader.py` = `patches/0005-fast-loader-switch.patch` (`--fast-loader`, default off),
  optional `patches/0006-seed-before-model-OPTIONAL.patch`, harnesses (`fl_equal.py`, `fl_dataset_equal.py`,
  `fl_abba.py`, `lm_run.sh` + `lm_det.py`, `b5_checks.sh`, `fl_distribution.py`), self-test + CI workflow,
  `GPU_REQUEST.md`, `IDEA_SOURCE.md`, RESULTS with two review milestones; skill `skills/forge-npt-fast-loader/`.
- Candidate b5 DLL sha256 9eb29b7d134a73eb58d47b2ced38587ed450ffaf11fdfcb108898652cefcd935 (pc1 = pc2).
- Checks: reference = old loader `--num-workers 1` (deterministic; w4 is not reproducible); first 1,000 batches
  bit-identical; validation 300 + 102 batches; 24-config matrix; 3,100 batches of 10,000 spanning windows past a file
  wrap; trainer path (Dataset -> FixedNumBatchesDataset -> DataLoader) 261/261 batches, every tensor; exact 1-epoch
  CPU loss match (5/5 values) in a reproducible setup; self-test 7 groups + CI ASan/UBSan + TSan PASS.
- Speed (ADVISORY): loader-only ABBA 8.65x (CI 8.58-8.69) on 2 CPUs; a full trainer epoch through the fast loader
  alone in 29.8 s at 166 MB (the live line needs 16-20 min per epoch); CPU training 3.5x faster on 2 CPUs.
- Finding for Engine NNUE: `--seed` does not fix the initial weights (train.py seeds after building the model; torch
  2.11 ROCm seeds per process from the clock), so npt runs are not reproducible.

## Item 2 - resumable relabel (`opus-r14b-relabel`) - proof running
- Deliverables (`opus_r14b/item2/`): `relabel2.py` (frozen for the proof at sha256 5c88438f...), `test_relabel2.sh`
  (19/19 PASS), `prove_resume.sh`, `sort_normalized.py`, `RELABEL_HANDOFF.md`, skill section in
  `skills/forge-nnue-data/`.
- 1M sample: 999,921 rows in 10,880 whole games (A = B); proof runs A (uninterrupted) and B (two hard exits) at
  ~340k rows/hour per worker; results at the end.

## Review milestones
- R14B-I1-1 (item 1, one read-only reviewer sub-agent, before Couns's 13:45 "no sub-agents"): a hang, the threshold
  overflow and fail-open spots fixed; coverage gaps closed by the b5 checks.
- R14B-I1-2 and later reviews: structured self-reviews, NOT independent. The final 30-minute bug hunt is recorded below
  at the end.

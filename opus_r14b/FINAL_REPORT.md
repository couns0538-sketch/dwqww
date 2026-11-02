# Opus R14-B final report (Couns's 15-hour job, 2026-11-02 12:05 PC clock -> ~03:00) - INTERIM, updated at the end

UNPROVEN everywhere: no Elo or training-quality claims; Engine NNUE / QA decide. Nothing of the live npt line, the
queue, gates, self-play or crew files was touched; all work ran BelowNormal / Idle on CPUs 2-3 within 2 threads.

## Item 1 - fast npt data loader (`opus-r14b-fast-loader`)
- Deliverables: `opus_r14b/item1/` - `fastloader/forge_fastloader.cpp|.py` (own code), `LOADER_SPEC.md`,
  `tools/install_fast_loader.py` + `patches/0005-fast-loader-switch.patch` (`--fast-loader`, default off),
  harnesses `tools/fl_equal.py`, `tools/fl_dataset_equal.py`, `tools/lm_run.sh`, `tools/fl_abba.py`,
  `tools/b5_checks.sh`; self-test + CI workflow; `GPU_REQUEST.md`; skill `skills/forge-npt-fast-loader/`.
- Candidate b5 DLL sha256 9eb29b7d134a73eb58d47b2ced38587ed450ffaf11fdfcb108898652cefcd935 (pc1 = pc2).
- Checks so far: old loader w1 deterministic (and = w2); fast = old on 1000/1000 train batches and 300 + 102
  validation batches (b4; b5 re-run in b5_checks); trainer path 261/261 batches identical (every tensor); self-test
  7 groups local + CI ASan/UBSan + TSan PASS; CPU training with the fast loader 3.5x faster on the same 2 CPUs.
- Open at the time of writing: deterministic loss match, b5 config matrix, ABBA, GPU window (requested).

## Item 2 - resumable relabel (`opus-r14b-relabel`)
- Deliverables: `opus_r14b/item2/relabel2.py`, `test_relabel2.sh` (19/19 PASS), `prove_resume.sh`,
  `RELABEL_HANDOFF.md`, skill section in `skills/forge-nnue-data/`.
- Open at the time of writing: the 1M-row kill / resume proof and the measured cost table.

## Review milestones
- R14B-I1-1 (item 1, one read-only reviewer sub-agent before Couns's 13:45 "no sub-agents"): 1 hang fixed, saturation
  fixed, fail-open spots fixed, coverage gaps scheduled; details in item 1 RESULTS.md.
- Later reviews: structured self-reviews (NOT independent); the final 30-minute bug hunt is recorded below at the end.

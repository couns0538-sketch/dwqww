# Real-data CPU trainer compatibility smoke

PASS on 2026-10-30. The unchanged `tools/nnue/train_resid_v3b.py`
(SHA256 `7379d1fcf47dcba6297b591dc2bc07b47caac865cee5d1d4632be1877fc96fe5`)
loaded the new FPOS/FHCE files and completed four CPU Adam updates, with
`--mmap-data`, residual/QAT H256, fixed seed 17 and one math thread.
Python 3.12.14, PyTorch 2.4.1+cpu, NumPy 1.26.4; `torch.version.cuda` is null.

- Train loaded: 512 unique kept pilot positions; presented: 256 (4 × 64).
- Holdout loaded: 512 unique original 013 text rows, native-inspected HCE.
- Train versus supplied 013 index: **0 overlapping positions** across
  1,499,915 unique identities from the verified 1.5M-row prefix.
- Train versus selected smoke holdout: **0 overlapping positions**.
- Residual initialization check: **PASS**, equal to HCE alone.
- Printed train MSE: **0.004578**.
- Holdout teacher MSE from original trainer JSON: **0.005856420306372456**.
- Successful trainer exit: **0**; wall **3.2739 s**, actual OS child CPU
  **3.1894 s**; reported private memory approximately **0.17 GB**.

This establishes format/trainer compatibility and finite-loss updates. It makes
no training-gain or Elo claim; the exported network is a disposable smoke result,
not an engine candidate. Full 013, holdout 014 and authoritative game IDs were
unavailable, so whole-holdout/game exclusion is **UNVERIFIED**.

The initial wrapper mistakenly created the run directory before launching the
trainer. The trainer refused it before updates with `FileExistsError` (exit 1).
The original wrapper, failed command, stdout/stderr and failure record remain.
The corrected wrapper lets the trainer create its new run directory. The retry
used the same prepared data and identical flags, changing only `--run-dir` to
`/tmp/astra-a1-cpu-smoke-run-retry1`; `trainer_retry1.command.json` is the exact
successful command and its exit/CPU record.

`selection.json` records original row IDs, full input hashes, original FEN origin,
HCE producer hashes and scope limitations. `holdout_native/` retains original
native IPC and process status. `artifact_manifest.json` hashes byte-verified
copies of the small prepared datasets, complete trainer outputs/checkpoint and
CPU-environment setup logs. `result_retry1.json` records final output hashes.
Original inputs, trainer source and native binary hashes were rechecked after
training and remained unchanged.

The scripts use new output paths and refuse existing ones. To repeat, choose
fresh data/run/evidence directories before execution; never overwrite or delete
this attempt. The trainer's console says “cosine blend,” but the source applies
a linear blend schedule; the smoke uses the exact existing implementation.

IDEA_SOURCE: Forge's FPOS/FHCE and existing v3b trainer; the user's data-isolation
and evidence-preservation requirements. No other engine code was copied.

# Matched result-mask recipes — UNPROVEN

Historical v2 handoff SHA256 (refresh pending after single-line FEN admission):
`ec3d391f42eaf0cf630a7257237e03b32ca3024c84b0d393912c5565192a0604`.
Both CPU preflights and strict published verification pass for source 8ed37659.
The entry point rejects stale runtime/tooling identities.
Current-source commands below require the next verified manifest before crew use.
Final review and broader descriptive corpus checks remain in progress.

Baseline: Engine NNUE `train_resid_nnuepytorch_v2.py`, w4/s12. Observed production
log identifies K32H3^, seed 5108, RangerLite lr 0.000875, self-play-only input
`forge_train_001-039_ex013-014_j2.binpack`, and separate 013/014 validation.
The supplied baseline contract is L1024, batch 16,384, epoch size 152,500,000,
eight epochs and StepLR gamma 0.72. Installed npt defaults retain its model,
quantization, score scaling and loss; these are not reimplemented here.

| Recipe | Known self-play result | Missing result / Lichess |
|---|---:|---:|
| filtered_eval_v1 | lambda 1.0 | lambda 1.0 |
| filtered_wdl_v1 | lambda 0.8 | lambda 1.0 |

Both use exactly the same pinned rows and deterministic seed/sampler. The audited
input is the first million data records from closed self-play shards 001 then 002,
in source order, **before** converter filtering. Composition is 100% self-play,
0% Lichess. This is a bounded cohort recipe, not a claim to reproduce the complete
305M-row baseline corpus. The requested 152.5M epoch size therefore repeats the
selected cohort; npt floors to 9,307 full batches (152,485,888 rows) per epoch.
Scaling to the full corpus needs a separately pinned, cleared manifest and disk
budget, not a new unrecorded mixture or silent input substitution.

Default selection enables only check and mate exclusion. The ply≤160 experiment
is separately reported and is **not** enabled in either recipe. Capture filtering
is an opt-in that currently fails for these shards because they have no best moves.
Qsearch filtering fails capability preflight. There is no clipping, deduplication,
random record skipping, relabeling or native binpack conversion in this path.

The refreshed handoff manifest `C:/astra8_data/quality6h_20261102/handoff_v2/manifest.json`
pins source boundaries/hashes, normalized training/validation hashes, holdout
audit, recipe settings, and actual imported npt/adapter Python files and native DLL.
It must report `training_ready: true`; otherwise the entry point refuses training.
Validation comes only from shard 013; shard 014 is scanned completely for leakage
but not added to iterative validation. Source-level whole-shard exclusion remains
013/014. Genuine game identifiers are unavailable, so no game-ID separation claim
is made. Complete holdout position audits are required for the selected cohort.

## Reproduce selection (new destinations only)

```powershell
$py = 'F:/nnue_pytorch/venv/Scripts/python.exe'
$tools = 'D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter'
$data = 'C:/astra8_data/quality6h_20261102'
$inputRows = 'D:/grok-pc-data/dwqww/astra8_data/cohort/million.jsonl'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:TEMP = "$data/handoff_v2/tmp"
$env:TMP = $env:TEMP
& $py "$tools/filter_positions.py" $inputRows "$data/recipe_selection_new" --workers 2 --drop-in-check --drop-mate-scores
```

The refreshed manifest references the preserved D: `holdout_cleared/records.jsonl`: check/mate filtering
followed by the separately recorded holdout split exclusion. The complete audit
found 24 matching board+STM keys in 013 and 23 in 014. Those 47 keys are excluded
explicitly from both recipes; the original `filtered_default` and failed overlap
audit remain intact. `clear_holdouts.py` reproduces this separate split stage only
at a fresh artifact root, requiring both pinned complete holdouts. The command
above demonstrates filtering alone without overwriting the audited selection.

## Crew-owned commands (not executed by this job)

Use the pinned installed environment. CPU preflight uses `--device cpu --check`;
it verifies manifest hashes and runtime identity without training. The integration
tests additionally traverse installed argument parsing, loader, callbacks and
trainer construction and stop before any training or optimizer update.

```powershell
$py = 'F:/nnue_pytorch/venv/Scripts/python.exe'
$entry = 'D:/grok-pc-data/dwqww/astra-r8-datafilter/astra_r8/datafilter/train_adapter.py'
$manifest = 'C:/astra8_data/quality6h_20261102/handoff_v2/manifest.json'
$env:ASTRA_NPT_ROOT = 'F:/opus_scratch/r6/nnue-pytorch-amd'
$env:NNUE_DATA_LOADER_LIB = 'F:/opus_scratch/r6/nnue-pytorch-amd/build/libtraining_data_loader.dll'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:OMP_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:TEMP = 'C:/astra8_data/quality6h_20261102/handoff_v2/tmp'
$env:TMP = $env:TEMP
$env:TORCHINDUCTOR_CACHE_DIR = "$env:TEMP/inductor"
$env:TRITON_CACHE_DIR = "$env:TEMP/triton"

# Engine NNUE executes only after its device/resource gate. Logical cuda:0 only.
& $py $entry --manifest $manifest --recipe filtered_eval_v1 --output 'C:/astra8_data/training/filtered_eval_stm_v1' --device cuda:0
& $py $entry --manifest $manifest --recipe filtered_wdl_v1 --output 'C:/astra8_data/training/filtered_wdl_stm_v1' --device cuda:0
```

These commands each set K32H3^, L1024, batch16384, epoch152500000, epochs8,
lr0.000875, gamma0.72, seed5108, no SWA, one process/device, zero loader workers,
and two torch threads. The Python adapter is intentionally bounded, not a throughput
replacement for Opus R13. No loader speed or training-throughput claim is made.
It reports no invented HLL unique counts. New run directories must not exist.

Resume adds `--resume PATH_TO_THIS_RECIPE_CHECKPOINT`; manifest, recipe, runtime,
sampler cursor, completed epoch and StepLR state are checked. Only epoch-boundary
training resume is supported. Native batch storage is released after all eight CPU
tensors are cloned; per-call lambda state is cleared even after exceptions.

No training, GPU use, model export, strength match or gate is part of this job.
For CPU-only preflight, replace `--device cuda:0` with `--device cpu --check`.
Neither command above was run in training mode by this job. The latest user
authorization requires C: remain above 50 GB, including planned allocations;
crew training must pass its own resource gate. Keep old D:/F: data read-only.
The new binary result version does not change the JSONL consumed by this adapter.
The separate completed-gate PGN capture audit is measurement-only and is not
part of these matched recipes. All-off/single-rule million timings are likewise
audits, not additional training mixtures.
All outcomes remain UNPROVEN. Handoff: Code Review → Engine NNUE → Engine QA;
FD3A5190 comparison, UHO first, 8moves_v3 separately and WAC300 are crew-owned.

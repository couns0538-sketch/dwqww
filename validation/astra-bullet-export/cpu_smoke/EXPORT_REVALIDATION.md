The exporter helper acquired a manifest CLI while the CPU smoke task was running.
The original `run1/metrics.json` correctly retains the exporter SHA256 used at
training/export time (`cb56f1f1d8f1ca7eadcc2ca0e729e046e52105fcbeb49d2af57e345d8370bcd8`).
The finalized helper is
`ef5b7b99adf2e67f1fda70c2329ce3902c51296f3549bb2ce95181c09a98fad5`.
The CPU trainer and its other dependencies stayed unchanged.

`export_revalidation/receipt.json` records a successful replay with frozen final
helper sources. The retained trained PyTorch state was exported again, without
retraining. All four comparisons were byte-identical:

- `trained/weights.bin`
- `trained/manifest.json`
- `sample.inc`
- `reference12k.txt` (all 12,000 residual scores and float32 output-bit values)

The replay also checked that the live source files remained unchanged during
verification. Exact final source snapshots are in `export_revalidation/source/`.
`revalidate_export.py` records the replay procedure. The original run and its
receipts were preserved; no original hashes were replaced to conceal the helper
change.

`SHA256SUMS` is the earlier run1 evidence inventory. The later
`SHA256SUMS.final` includes this revalidation and retained source snapshots;
Python bytecode caches are excluded from the final publication inventory.

The initial run1 evidence described in README was under 6 MB. With this later
revalidation and source snapshots, the full retained publication is under 8 MB,
well below the requested 50 MB bound. The exact run1 exporter source was
reconstructed and verified against its recorded SHA256 before archival in
`export_revalidation/source_run1/lock_export.py`.

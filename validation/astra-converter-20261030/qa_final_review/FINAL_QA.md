# QA correction completion — 2026-10-30

Exporter commit: `3337fc0a09db22e1d1f1319408f2c0349848eb1b`.
Converter code commit: `75592dc48f359e4e2898c6b454f9e00ada8daf68`.
The final checkpoint adds evidence metadata only.

The requested review lasted **20.45 minutes**; its exact interval is in
`review_complete.json`. No command ran on grok-pc.

## Corrections

- Corrected the binpack GPL-3.0 provenance. It is optional and OFF by default;
  fetched headers and compiled adapter remain outside repositories. Only the
  original wrapper and tests remain in Forge.
- Prune owned, disposable indexes after verifying sealed output. Preserve
  source data and logs. Add preflight and in-loop disk guards, a 20,000 MiB
  reserve, and budgets for UTF-8 game IDs and native logs.
- Add an independent holdout audit with trusted full-shard hashes and counts,
  source-mutation checks, safe report placement, and bounded scratch storage.
- Replace the unsafe PS5.1 native stderr pipeline. Specify Rust 1.87+, Idle
  priority, CPU affinity, Cargo -j2, locked fetch, F: scratch, pinned Python,
  and checks for a GPU-free slot after compilation. Bind the executed binary
  to the explicitly built Cargo target.
- Accept only terminal CRLF transport normalization in optional binpack
  verification; preserve exact field and other whitespace comparisons.
- Document include-header differences separately from tensor equality.

## Evidence

| Check | Result |
|---|---|
| Converter data2 suite | 93 passed, including optimized Python with ResourceWarnings as errors |
| Bullet suite | 42 passed |
| Original A1 discovery | 130 cases, one explicit native-suite skip |
| Separate native probe suite | 9 passed |
| Independent converter review | 9 passed |
| Windows PowerShell / HIP execution | UNVERIFIED |
| Full private 013/014 overlap | UNVERIFIED; blocks training |

Original failing tests, sparse-checkout setup failures and unavailable-system-
torch failure are retained alongside their corrected runs. No engine search,
evaluation or network source changed.

Two measured 50k batches retained 5,140,974 and 5,166,932 bytes, with zero
retained index bytes. The native 1,024-row pilot kept 977 rows, dropped 46 capture
roots and one result disagreement, and retained 71,439 bytes of native logs.
Full-shard figures in the runbook are projections, not measured 305M results.

The audit correctly detected 1,000 intentional overlaps and zero overlaps in
separate fake-holdout cases over 49,999 real-derived output rows. Those holdouts
came from shard 003, not private 013/014. These checks qualify the tool only.

The supplied Windows behavioral tests were not executed here. Real private
holdout clearance and Windows/HIP qualification remain required before use.
No training, performance or Elo gain is claimed.

IDEA_SOURCE: crew QA and original regression/evidence workflows.

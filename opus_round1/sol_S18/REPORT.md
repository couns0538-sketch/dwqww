# S18 Filter threshold sweep + small ablation — PARTIAL (inputs pin-checked; no arm run yet)

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2, item 2. Branch `opus-sol-S18` = `d4f4312` + CI cherry-pick `66ee5478` +
`d3e281ad` (evidence) + this report. No engine change; `[skip ci]`, so no CI run.

**Authority.** QA, SOL_LEFTOVERS_FOR_CLAUDE.md (2026-10-27 08:50 CET), section 2 item 2: exactly the remaining 4
arms as CPU smoke in `F:\opus_scratch`: small, RAM-capped, stop if free RAM < 6 GB, no net adoption. This replaces
the "root grant" in Sol's README/argv, which marked them "NOT AUTHORIZED" (Sol's internal sign-off).

**State.** The first sub-agent was wound down (limit of 2 background agents) before any arm started.
**t200, t300, t400 and t500 were NOT STARTED.** The main session continues the job.

## What was done
- Read Sol's S18 material on 17aa0cae (read with `git show` / `git archive` only) and extracted it to
  `F:\opus_scratch\sol_s18\sol_src\` (301 MB, read-only reference).
- **Step 0, pin check.** Command:
  `nice -n 19 C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe -B opus_round1/sol_S18/opus_s18_pin_check.py --json F:/opus_scratch/sol_s18/logs/step0_pin_check.json`.
  Raw output: `RESULT PASS_ALL_PINS pinned=42 failures=0` (in `logs/step0_pin_check.tar.gz`, 6308 bytes).
  Machine exclusive: no (gate fastchess, self-play and live NNUE training were running).
  - The lock-archive v3b trainer, Adam helper and data32 sample are exactly Sol's training and holdout inputs.
  - The nets and phase header match Sol's pins.
  - Sol's v4 controller (643e71ea), index (fb5d2575), recipe (97b4a2a8), postscore preregistration (aa8fed66),
    filter tools (6ccf78c8, 5dd0c009), describe tool (5ff1e6d7), prereg/reference files and both evidence archives
    (1f48fb1f, e9ccce44) are intact.
  - The 8 t200 v3 epoch artifacts match the reference binding.
  - Environment: torch 2.4.1+cpu (same version as Sol's Linux run), numpy 1.26.4, Python 3.10.22.
- **Supervisor (read-only).** `F:\forge_nnue_train\tools\nnue_supervisor.ps1` line 39 adopts any `python.exe`
  whose command line matches `train_resid\w*\.py` and takes the run name from `--run-dir`. No command line of this
  job may contain that string; the trainer copy is renamed `opus_nnue_smoke_s18_v3b.py` (byte-identical).

## Loss table (holdout h000, all 50,000 rows, postscore of the preselected final epoch-2 checkpoint)
| arm | rows kept | net_MSE b1.0 | b0.6 | b0.8 | source |
|---|---:|---:|---:|---:|---|
| HCE baseline | — | 0.021862312406668114 | 0.04558598687997589 | 0.02374596858268229 | Sol v3 (every arm, same holdout) |
| none | 200,000 | 0.02186266321728358 | 0.04558630099854697 | 0.023746301048879447 | Sol v3, qualified PASS_PIPELINE_ONLY (f008b5db), Linux |
| t200 | 132,421* | UNVERIFIED | | | not run |
| t300 | 157,666* | UNVERIFIED | | | not run |
| t400 | 175,673* | UNVERIFIED | | | not run |
| t500 | 187,141* | UNVERIFIED | | | not run |

\* Kept rows are Sol's Linux filter evidence, not re-run here.

- Sol's failed t200 v3 run (controller FAIL_RSS_UNAVAILABLE, kept as FAIL) postscored 0.021862473914850085 /
  0.04558613712126954 / 0.023746124458361686. That is only the frozen comparison reference, not a result.
- Holdout md5: h000.pos `b263af9969f8ace979e25db061eb37ef`, h000.hce `f248959bc791424407a37af5ac60752a`.
- The data32 sample is synthetic, so these losses are a pipeline check, not evidence of data quality.

## Acceptance
| item | status |
|---|---|
| Remaining 4 arms run as CPU smoke | UNVERIFIED (not run) |
| Holdout loss per threshold | PARTIAL (none only, Sol's numbers) |
| Rerun reproducibility | UNVERIFIED |
| Same holdout md5 in every arm | PARTIAL (none arm, plus the PC copy matches) |
| t300 keeps 157,666 of 200k | UNVERIFIED here (Sol's evidence says 157,666) |
| Shards / histograms / manifests on this PC | UNVERIFIED |
| No net adoption | PASS (nothing trained or exported; no write to F:\forge_nnue_train or any gate, lock or queue dir) |
| Inputs equal Sol's pins | PASS 42/42 |

## Planned deviations from Sol's preregistration (Windows)
- **D1:** no taskset (`--cpu` dropped); the run is bound to nice 19 / IDLE priority and 1 thread.
- **D2:** the controller runs under nice 19; the child gets IDLE priority.
- **D3:** thread env vars set to 1, plus `set_num_threads(1)` and `set_num_interop_threads(1)`.
- **D4:** RSS guard reads the child's own process handle (`GetProcessMemoryInfo`); the 3 GiB cap applies to the
  larger of working set and private bytes (stricter than VmRSS).
- **D5:** no address-space limit equivalent is set unless a Job Object is used (looser than Linux AS).
- **D6:** cleanup kills only this job's own child process (no graceful TERM phase).
- **D7:** free-RAM floor of 6 GiB, checked before and during each arm.
- **D8:** the disk floor 6,979,321,856 B is checked on F:.
- **D9:** parent-only work/hard deadlines (no SIGALRM).
- **D10:** normal torch import from the read-only venv instead of Sol's sealed memfd load.
- **D11:** Python 3.10 instead of 3.12.
- **D12:** LF output for Sol's filter and describe tools (they write text in CRLF on Windows otherwise).
- **D13:** output under `F:\opus_scratch\sol_s18`, names `s18_*`, renamed trainer copy (byte-identical).
- **D14:** QA's authority replaces Sol's root grant and his S11/exclusive/disk gates.
- **D15:** reproducibility = fresh t200 vs Sol's frozen v3 reference (cross-platform; may be NOT_CONFIRMED) plus a
  same-PC run1/run2 byte-for-byte comparison.
- **D16:** shards are regenerated (twice) with Sol's unchanged v2 filter and argv and checked against his preflight
  fingerprints.
- **D17:** histograms come from Sol's describe tool run directly per arm.

## Resume plan (all under `F:\opus_scratch\sol_s18`, one process at a time)
1. Copy the inputs (lock archive `5_nnue\sample_data\data32_sample\data32_sample_50k\*`, the trainer as
   `opus_nnue_smoke_s18_v3b.py` with `qa_adam_dml.py` beside it, the two filter tools and the describe tool, the
   pins) and pin-check them again.
2. Regenerate the shards per arm (twice) with Sol's v2 filter and exact argv; compare with his preflight
   fingerprints (summary sha256: none 24fc0c1f…, t200 5c165d2a…, t300 26dd2727…, t400 013fbd61…, t500 4029205e…).
3. Histograms per arm with Sol's describe tool; compare with the index's `histogram_sha256`.
4. Train t200/t300/t400/t500 with the f006 recipe argv (cpu, 256, residual, 2 epochs, batch 8192, lr 0.000707,
   warmup 300, blend-end 0.6, seed 25, final-full-val) under the RAM guard; after each start read the tail of
   `F:\forge_nnue_train\supervisor.log` and stop at once on "adopted running job".
5. Postscore every arm on all 50,000 holdout rows; run twice; compare run1/run2 and t200 with Sol's reference;
   build the loss table; FILES, archives, SHA256SUMS; push.

## UNVERIFIED
- Every training, filtering, histogram, loss and reproducibility item on this PC.
- Real 013/014 and authentic-game isolation (synthetic sample only).
- No Elo or quality claim.

## Files
`REPORT.md`, `FILES`, `IDEA_SOURCE.md`, `opus_s18_pin_check.py`, `logs/step0_pin_check.tar.gz` (6308 bytes),
`SHA256SUMS`.

# S18 Filter threshold sweep + small ablation — DONE (remaining 4 arms run as CPU smoke; pipeline-only)

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2, item 2. Branch `opus-sol-S18` = `d4f4312` + CI cherry-pick `66ee5478` +
`d3e281ad` (pin check) + `c86282d4` (PARTIAL report) + this commit. No engine change; `[skip ci]`.

**Authority.** QA, SOL_LEFTOVERS_FOR_CLAUDE.md (2026-10-27 08:50 CET), section 2 item 2: exactly the remaining 4 arms
as CPU smoke in `F:\opus_scratch`: small, RAM-capped, stop if free RAM < 6 GB, no net adoption. This replaces the
"root grant" in Sol's README/argv (his internal sign-off).

**Scope.** The data32 sample is synthetic, so every loss below is a pipeline result, not evidence about data quality
or strength. No net is adopted: the trained checkpoints and exports stay in `F:\opus_scratch\sol_s18\s18_r4_*`
and are not committed. Machine exclusive: no (gates, self-play and NNUE training ran throughout).

## Acceptance
| item | result | evidence |
|---|---|---|
| remaining 4 arms run as CPU smoke in F:\opus_scratch, small, RAM-capped, stop if free RAM < 6 GB | **PASS** | t200/t300/t400/t500 trained and postscored in run1 and run4 (complete), each arm 8.5-10.9 s, peak child memory 442-448 MiB, guard floor 6 GiB available RAM (run2's t500 was stopped by it) |
| holdout loss per threshold | **PASS** | loss table below (all 50,000 holdout rows, final epoch-2 checkpoint, three blends) |
| no net adoption | **PASS** | nothing exported outside scratch; no write to `F:\forge_nnue_train`, gate, lock or queue dirs; supervisor log: no "adopted running job" line since 08:55 (all 7 such lines in the log are the earlier, resolved C4/C5 incident) |
| rerun reproducibility (same PC) | **PASS** | run1 vs run4, all 4 arms: the 8 epoch artifacts (.pt .inc .bin .json × 2 epochs) byte-identical, fixed loss lines identical, postscore identical (`logs/step9_compare_run1_run4.log`); run1 vs run2 identical for t200-t400 |
| t200 vs Sol's frozen Linux v3 reference (311d97f7) | **NOT_CONFIRMED at bit level** (as Sol's binding allows for a cross-platform rerun) | identical: baseline line, both epoch loss lines, FINAL line, both quantized `.inc` exports, both `.json`; different: `.pt` and `.bin` (float weights) by at most 7.45e-9 (ft.weight, max magnitude 0.089: float32 rounding) (`logs/step10_pt_diff_t200_vs_sol.log`); postscore b1.0 0.021862473914669927 here vs 0.021862473914850085 Sol (Δ 1.8e-13) |
| same holdout md5 in every arm | **PASS** | h000.pos `b263af99…`, h000.hce `f248959b…` in every staged view and postscore (`child_result.json`) |
| t300 keeps 157,666 of 200k | **PASS** | regenerated twice (`logs/step2b`, `step4`, `step11`) |
| shards / manifests / histograms on this PC | **PASS** (with one Windows finding) | shards, summaries and removal ledgers byte-identical to Sol's archived arms, three regenerations; manifests same lines, other order (finding 1); histograms match Sol's completed ones and the index (`logs/step12_hist_run3.log`) |
| inputs equal Sol's pins | **PASS** | 42/42 (step 0) and the runner's own pins before and after every run |

## Loss table (holdout h000, all 50,000 rows; postscore of the preselected final epoch-2 checkpoint)
Identical in run1 and run4. "native FINAL" is the trainer's own line over 49,152 rows (6 decimals).

| arm | rows kept | steps | net_MSE b1.0 | net b0.6 | net b0.8 | native FINAL b1.0/b0.6/b0.8 |
|---|---:|---:|---:|---:|---:|---|
| HCE baseline (every arm) | — | — | 0.021862312406668114 | 0.04558598687997589 | 0.02374596858268229 | 0.021840/0.045537/0.023707 |
| none (Sol v3, Linux, qualified) | 200,000 | 48 | 0.02186266321728358 | 0.04558630099854697 | 0.023746301048879447 | — |
| t200 | 132,421 | 32 | 0.021862473914669927 | 0.04558613712144221 | 0.02374612445835794 | 0.021840/0.045537/0.023707 |
| t300 | 157,666 | 38 | 0.02186254815049017 | 0.045586196155002645 | 0.02374619109330508 | 0.021841/0.045537/0.023707 |
| t400 | 175,673 | 42 | 0.021862624881983143 | 0.04558627312853322 | 0.023746267946120884 | 0.021841/0.045537/0.023707 |
| t500 | 187,141 | 44 | 0.021862566407324462 | 0.04558624247821367 | 0.023746223383433872 | 0.021841/0.045537/0.023707 |

**Reading.** With 2 epochs of 32-48 steps, all inside the 300-step warmup, every arm stays within 4e-7 of the HCE
baseline at every blend; the residual net has barely moved from its HCE-equivalent start. The ordering between
thresholds at this size is noise-level and says nothing about the filter's value. Real 013/014 data and a real
training length are needed for that (UNVERIFIED).

## How it was run
`opus_nnue_smoke_s18.py` (this folder), with the read-only NNUE venv python (torch 2.4.1+cpu, Python 3.10.22),
one mode at a time, from Git Bash under `nice -n 10`; the runner sets itself and its children to BelowNormal:
1. `--stage`: copies the lock-archive data32 sample and the trainer (renamed `opus_nnue_smoke_s18_v3b.py`,
   byte-identical, sha256 `5cebba4d…`, with `qa_adam_dml.py` beside it) to `F:\opus_scratch\sol_s18\s18_inputs`
   and pin-checks them (`logs/step1_stage.log`).
2. `--data TAG`: Sol's unchanged v2 filter (`5dd0c009…`) for none/t200/t300/t400/t500 with his exact argv (seed
   20261025, `--diagnostic-mode`, `--disagreement-threshold N`) through `opus_s18_lf_launcher.py`, then
   `--check-data TAG` against his archived arm folders and the arms index (`fb5d2575…`). Run three times
   (run1, run2, and run3 with the final launcher): all PASS.
3. `--hist TAG`: Sol's unchanged describe tool (`5ff1e6d7…`) per arm; PASS for all five arms.
4. `--train TAG --data-tag D`: for each arm a fresh view (the arm's shards + h000, copied and made read-only), then a
   `--child` process that imports the trainer copy, runs `main()` with Sol's v4 `trainer_argv` (f006 recipe: cpu,
   256, residual, 2 epochs, batch 8192, lr 0.000707, warmup 300, blend-end 0.6, seed 25, final-full-val) and then
   Sol's v4 postscore (all 50,000 rows, float64 sums, model/checkpoint/holdout/RNG unchanged checks). The parent
   guards it (below).
5. `--compare A B`: artifacts, fixed loss lines and postscore of two runs; t200 vs Sol's reference; loss table.

**Guard (per arm):** available RAM ≥ 6 GiB (checked every 0.25 s; the arm is stopped below it), and an arm starts
only with ≥ 7 GiB available (waits up to 30 min); child-tree memory max(working set, private) ≤ 3 GiB; F: free ≥ Sol's
floor 6,979,321,856 B + 64 MiB; hard limit 1800 s; the supervisor log is read every 30 s and any new "adopted running
job" line stops the arm. A stop kills only this job's own child process tree.

**Runs:**
- run1 (data run1): PASS, 4/4 arms.
- run2 (data run2): t200-t400 PASS; **t500 stopped by the free-RAM floor** (available RAM fell to 5.98 GiB during the
  arm; other PC jobs). The guard did its job; the start-headroom wait was added after this.
- run3 (data run2): t200 PASS after waiting 160 s for headroom; t300's child finished normally, but the **runner
  crashed** on a race in its own monitor (`psutil.NoSuchProcess` when the child exited between `poll()` and
  `children()`). Fixed (a vanished child counts as exited); run3 is kept as evidence.
- run4 (data run2): PASS, 4/4 arms; run1 vs run4 identical.

The runner changed during the job (data check refactor, headroom wait, race fix, histogram mode, launcher Path.open
patch). The training path (trainer argv, child, postscore, guard limits) was the same in every run, and the
committed file is the final version.

## Findings
1. **Sol's filter writes its manifest in a platform-dependent order.** `forge_sol_datafilter_v2_20261026.py` builds
   `forge_sol_datafilter_manifest_20261026.md5` from `sorted(out.iterdir())`. On Windows, `WindowsPath` sorts
   case-insensitively, so `forge_sol_datafilter_summary…` comes before `forge_sol_S16_removals…`. The lines are
   identical and every md5 matches, but the file's sha256 differs from the index's `output_manifest_sha256`. Sorting
   by `p.name` would make it platform-independent (a section-3 style fix for Sol's tool; not changed here). The
   check here re-sorts the lines case-sensitively and matches the index for all five arms.
2. **Text outputs need LF on Windows.** Sol's tools write text with `Path.write_text()` / `Path.open('x')`, which give
   CRLF on Windows; `opus_s18_lf_launcher.py` runs them unchanged with LF defaults so their outputs are byte-identical
   to his Linux ones.

## Deviations from Sol's preregistration (Windows)
- No `taskset` (no CPU pinning); BelowNormal priority (the PC rule) instead of nice 19 / IDLE; one Torch thread
  (`set_num_threads(1)`, `set_num_interop_threads(1)`, OMP/MKL/OpenBLAS env = 1).
- Memory guard via psutil on the child tree (max of working set and private bytes) instead of `/proc` VmRSS; no
  address-space limit (no RLIMIT_AS equivalent was set: looser than Linux).
- Hard limit 1800 s per arm (Sol: 300 s work / 360 s hard on an idle core); actual arms took 8.5-10.9 s.
- Free-RAM floor and start headroom added (QA rule); disk floor measured on F:.
- Torch imported from the read-only venv (Sol: sealed memfd load); Python 3.10.22 (Sol: 3.12).
- Sol's S09 diagnostic child/monitor and S08 subreaper are Linux-only and not used; this runner's own monitor
  replaces them.
- Histograms via the describe tool directly per arm (his batch wrapper is Linux-only).

## Files
- `opus_nnue_smoke_s18.py` — the runner (stage, data, check-data, hist, train, child, compare).
- `opus_s18_lf_launcher.py` — runs Sol's tools unchanged with LF text output.
- `opus_s18_pt_diff.py` — read-only tensor diff of two checkpoints.
- `opus_s18_pin_check.py` — step 0 pin check (42 inputs).
- `s18_loss_table.md` — the loss table of run1/run4.
- `IDEA_SOURCE.md`, `FILES`, `SHA256SUMS`, `REPORT.md`.
- `logs/`: `step1`…`step12` text logs, plus archives (sizes):
  - `step0_pin_check.tar.gz` 6,308 B;
  - `s18_data_evidence.tar.gz` 10,706 B (receipt, data run1/run2 results and checks, filter stdout/stderr,
    run1 summaries and manifests);
  - `s18_data_run3_and_hist.tar.gz` 17,810 B (data run3 and the five histograms);
  - `s18_train_run1.tar.gz` 11,384 B, `s18_train_run2.tar.gz` 10,353 B, `s18_train_run3.tar.gz` 6,260 B,
    `s18_train_run4.tar.gz` 11,412 B (training results with artifact sha256, per-arm stdout/stderr/child results,
    epoch JSONs and settings files);
  - `s18_compare.tar.gz` 1,317 B (both comparisons and loss tables).

## UNVERIFIED / left
- Real 013/014 data, authentic-game isolation and real training lengths: not in scope (synthetic sample).
- Cross-platform bit identity of the float checkpoints: not achieved (rounding-level), as expected for Linux vs
  Windows torch kernels.
- No Elo or quality claim.

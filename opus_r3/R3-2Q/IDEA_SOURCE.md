# R3-2Q idea and sources

- **Job:** the R3 coordinator brief (2026-10-27). R3-2's UNVERIFIED list asks for a quiet-runner repeat of its switch
  rows, because on the loaded PC a build switch moves NPS by a code-layout term of up to about ±5%.
- **Question:** which PC switch effects reproduce on a quiet runner (a feature effect) and which do not (layout of that
  one binary on that one machine)?
- **Sources reused:**
  - `opus_round1/sol_S29/nps_ab.py`: ABBA order, fresh processes, node check, CPU time via RUSAGE_CHILDREN.
  - sol_SIT `nps_ab_opts.py` (branch opus-sol-SIT): per-side UCI options.
  - `opus_r3/R3-2/r3_matrix.py` (opus-r3-matrix): t975 table, paired t on per-pair log ratios, and the
    Satterthwaite combination used for the two-runner row.
  - `.github/workflows/opus-sol-s14fu.yml` + `opus_round1/sol_S14/followup_zerofill/ci_s14fu.sh` (nps mode) and
    `opus-sol-s29-ci.yml`: the workflow and runner layout (A/A control, two independent runners).
  - `opus_round1/ci/run_ci.sh`: the release build recipe.
- **New here:**
  - CPU time after `readyok` (the start-up part subtracted with /proc schedstat), so the figure matches R3-2's
    "measured command only" CPU time.
  - Same-exe option rows inside each switch build.
  - `bench_prof` for the profile-counting row.
  - An x86-64-v4 O2 row on AVX-512 runners, to mirror the PC's znver5 path, where O2's AVX2 kernels are compiled out.
- **Rule applied:** the speed-eligibility rule (S11, S49): the 95% CI lower bound must be at least +2% at d16 AND
  d20.

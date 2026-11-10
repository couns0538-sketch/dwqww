# Exploratory cloud profile: isolated material-index cache

**UNPROVEN. This is not native performance acceptance or an Elo result. No speed gain is claimed.** No engine matches or production changes were made.

## Configuration and integrity

Reused the isolated default-off/default-on binaries from `material_cache_results.json`; both SHA-256 hashes matched before and after profiling. They differ in `FORGE_SPD_MATERIAL_CORRECTION_CACHE`, using the recorded GCC 14 strict-FP x86-64-v4 build. These are the earlier isolated experiment binaries, not a build of all subsequent fixes. Full paths and hashes are in the result receipt.

Pinned the Python driver to allowed logical CPU 0; every newly launched engine inherited that single-CPU affinity. Original allowed affinity was CPUs 0–8. Machine identification: AMD EPYC 9V74 80-Core Processor, Linux 6.18.57 x86-64. Nine logical CPUs were visible to this workspace.

The parent coordinated a short quiet window by holding the other active testing workers. This does **not** reserve a physical core, exclude unrelated host activity or control frequency, power, thermal state or hypervisor scheduling. Each run records load averages before/after. Initial load averages were approximately 0.479 / 0.596 / 0.673.

Completed window: 2026-11-10 20:13:22.754 through 20:14:08.529 UTC, about 45.8 seconds.

## Procedure

For NNUE enabled, then NNUE disabled:

1. One unmeasured warmup process for each binary.
2. Three ABBA cycles, A=baseline and B=candidate, yielding six measured processes per binary per NNUE mode.
3. Each fresh process executes the engine's fixed eight-position `bench 16`, then exits. The bench uses one search thread and a fresh 16 MB searcher. Every position clears search state.
4. Actual process wall time is measured with `perf_counter_ns`, including creation, initialization and exit. Engine-reported bench milliseconds are retained separately and are not substituted for process wall time.

All 24 measured runs and four warmups returned successfully. Every NNUE-on run reported **3,024,920 nodes**; every NNUE-off run reported **2,448,617 nodes**. Both hashes remained unchanged.

## Descriptive observations only

- NNUE on, baseline wall median: **1.907015 s**, observed range 1.846029–1.987208 s. Candidate median: **1.924970 s**, range 1.885281–1.949441 s.
- NNUE off, baseline wall median: **1.340069 s**, range 1.297589–1.406758 s. Candidate median: **1.370148 s**, range 1.341093–1.498134 s.
- Per-cycle candidate/baseline ratios of mean process wall time: NNUE on **1.008112, 0.984129, 1.024080**; NNUE off **1.013913, 1.048962, 1.018201**.

These small cloud samples do not support promoting the candidate as an accepted optimization. No significance test, confidence interval, native speed claim or strength conclusion is provided.

## Reproduce and raw evidence

```sh
python3 forge-combo29/tests/material_cache_profile.py \
  --output /workspace/shared/forge-build/material-cache-profile-reproduction
```

The script requires the two binary paths in the saved equivalence evidence to exist and have matching hashes; it fails rather than silently profiling different binaries. If rebuilding is necessary, use the earlier isolated source revision and recorded flags, rerun equivalence, and generate new provenance rather than bypassing the hash guard.

- `material_cache_profile_results.json`: complete run metadata, stdin, timestamps, wall durations, engine timing/node receipts, load samples, summary and verified hashes.
- `material_cache_profile_raw.json`: exact stdout/stderr strings keyed by the filenames referenced in the result receipt.
- `material_cache_profile_interrupted.json`: preserved incomplete initial run, excluded after coordination reported concurrent CPU-heavy worker activity. It contains two warmups and one completed ABBA cycle. The final run restarted from scratch after workers held. This exclusion was operational, not based on the observed timings.

CPU pinning, ABBA order and a coordinated window reduce some variability; they do not turn this into controlled native performance evidence.

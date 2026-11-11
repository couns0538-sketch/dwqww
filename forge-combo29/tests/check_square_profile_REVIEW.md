# Frozen check-square presence diagnostic protocol

Candidate source is frozen at `1e6c398dec7717868a740f5d322cf7434336345f`; immutable baseline is `16833ecc03b425586f91f4c8834dea8807bf4c22`. The candidate enables only `FORGE_SPD_CHECK_SQUARE_PRESENCE=1` above default source behavior. Production defaults remain off.

Run only after all correctness gates pass, receipt hashes match, and the coordinator's CPU window is free. The validation receipt and 256-position/mode equivalence evidence identify the binaries; the profiling tool checks their hashes before and after. Source-only snapshot hashes and exact build commands are in `check_square_validation.json`.

Fixed protocol, committed before first measured execution:

- Bench depth18, single thread, built-in 16 MB bench hash, NNUE on then off.
- Pin to the minimum allowed logical CPU; the CPU is not reserved from unrelated host work.
- One baseline and one candidate warmup per mode: four warmups total.
- Four measured cycles per mode, alternating ABBA and BAAB: 32 measured runs total.
- A is immutable baseline; B is enabled frozen candidate. Fresh engine process per run.
- Record child user+system CPU deltas, wall duration, unchanged raw stdout/stderr, node signature, load, affinity, CPU model, and binary/script hashes.
- Require all node signatures equal within each mode and successful process exit. Also enforce immutable-lock depth18 signatures: 6,066,072 NNUE-on and 6,134,776 NNUE-off.
- Summarize candidate/baseline duration ratios per cycle and their median, preserving every run.
- No adaptive extension, favorable-result rerun, discarded slow samples, or switching primary outcomes after looking at results. A timeout, mismatch, changed binary, or other failed gate stays recorded and blocks a favorable conclusion.
- This is a shared-cloud diagnostic only. Child CPU time removes descheduling but not cache/frequency/thermal contention. Wall time includes process overhead and descheduling. Neither establishes native performance or Elo.

Command:

`python3 tests/check_square_profile.py --evidence tests/check_square_equivalence.json --output tests/check_square_profile_results.json --depth 18 --cycles 4`

The output must not already exist. Do not overwrite an earlier run.


Frozen executable SHA256:

- Baseline: `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`.
- Candidate: `6c8b321ff302cf736d278d315a3a7f426a8d3c85b8db60c7e68c2e5ffe984ad4`.

All six actual-picker sanitizer configurations, three mutation checks, full pins/perft, 256 comparisons and complete default-off identity passed before this protocol was written. CPU window released by coordinator before execution. No other owned CPU-heavy job will overlap.

## Single frozen diagnostic result

Protocol was committed at `095f206be85c0bbb2ccd705274c44787e6813b47` before execution. All 32 measured runs plus four warmups completed on logical CPU 0; every raw sample is retained. Hashes were unchanged and all depth18 nodes matched the preregistered lock signatures (6,066,072 on; 6,134,776 off). No timeout, exclusion, adaptive extension or rerun occurred.

NNUE-on candidate/baseline child-CPU duration ratios by block: 1.027816, 0.994435, 1.003988, 0.999448. Median 1.001718, or 0.17% longer duration. Median paired wall ratio: 1.001775.

NNUE-off CPU ratios: 1.020186, 0.997614, 0.987593, 1.023119. Median 1.008900, or 0.89% longer duration. Median paired wall ratio: 1.008544.

The unpaired duration medians also favor baseline in both modes, but neither those medians nor paired ratios establish a native regression. Blocks cross parity, shared-host conditions are uncontrolled, and the fixed sample is small. This result does not support promoting S11 as a speed improvement despite the confirmed omitted-query counts. Preserve the negative/near-neutral diagnostic; do not rerun for a favorable outcome. The candidate remains default-off and UNPROVEN for native performance and strength.

Full raw records and summaries: `check_square_profile_results.json`; console log: `check_square_profile.log`.

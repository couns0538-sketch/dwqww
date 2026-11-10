# Bitcount predicate timing protocol

**Completed exploratory diagnostic. Native speed and Elo remain UNPROVEN.**

Production source is frozen at `5f0a6e95ebdd49b45061cc942473f32e442869a6`.
The isolated full correctness gates passed. The parent reserved a quiet
window and the fixed protocol/driver were committed at `bbee6e7` before this
one run. Neither profiled nor combined binaries were substituted.

- `bitcount_predicate_profile.py --evidence <validated equivalence.json>
  --output <new output.json> --depth 18 --cycles 4`.
- Baseline is immutable default-off SHA-256
  `1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6`.
- Isolated candidate has only `FORGE_SPD_EVAL_BITCOUNT_PREDICATES=1`, SHA-256
  `4d75c1ce1b1aef2a61246564fff1d9aead8ea66124ecd4a5dd5e3782763f64d4`.
- Threads 1, OwnBook false, bench Hash 16 MB, fresh process each run.
- NNUE on then off. One baseline and one candidate warmup per mode.
  Four measured blocks each: ABBA, BAAB, ABBA, BAAB. Exactly 32 measured runs
  and four warmups, no adaptive stopping or favorable reruns.
- Pin to the lowest allowed CPU. Affinity is not reservation or isolation.
- Preserve child user/system CPU deltas around each single engine process,
  their sum, wall time, node signature, stdout/stderr, hashes, load and
  platform. A timeout remains a failure with its CPU/wall deltas retained.
- Verify unchanged validated binary hashes before and after all runs.
- Report every block's candidate/baseline duration ratio and their median.
  Wall time includes descheduling and process setup. CPU time excludes
  descheduling but not shared-host cache/frequency/thermal interference.

This tiny shared-cloud bench is an exploratory diagnostic, not a speed
acceptance gate, statistical proof, Windows/clang-PGO result, or Elo test.
Keep the switch default off regardless of this diagnostic's outcome.

## Observed result

All 36 processes completed: four excluded warmups and 32 measured runs.
Hashes remained unchanged. Every depth-18 signature matched: 6,066,072 nodes
with NNUE on, 6,134,776 with NNUE off. There were no crashes, timeouts,
malformed results, dropped samples, adaptive stopping, or reruns.

Candidate/baseline duration ratios below 1 favor the candidate.

- NNUE on child-CPU block ratios: 1.02470, 1.05581, 0.93161, 0.98173.
  Median 1.00321, or +0.32% duration. Wall median 1.00335, +0.34%.
- HCE child-CPU block ratios: 0.98969, 1.03746, 1.02043, 1.01605.
  Median 1.01824, or +1.82% duration. Wall median 1.01766, +1.77%.

The observed median direction is unfavorable, particularly for HCE. The
blocks vary substantially and this shared-cloud sample establishes neither
a reliable speed gain nor a native regression. Fewer local instructions did
not produce a positive diagnostic here. Preserve the result, leave the
candidate default off, and do not promote it as a speed improvement.

`bitcount_predicate_profile_results.json` preserves every process's command,
stdout/stderr, child user/system/total CPU, wall time, load, timestamps,
platform, CPU affinity, orders, binary and script hashes. The raw console
output is in `bitcount_predicate_profile.log`. Native Windows/clang-PGO speed
and native SPRT Elo acceptance remain pending and UNPROVEN.

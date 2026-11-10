# Bitcount predicate timing protocol

**Not yet run. Native speed and Elo remain UNPROVEN.**

Production source is frozen at `5f0a6e95ebdd49b45061cc942473f32e442869a6`.
After the isolated full correctness gates pass and the parent coordinates a
quiet window, run the following fixed diagnostic once. Do not substitute
profiled or combined binaries.

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

# Frozen evasion prefilter diagnostic protocol

Candidate source is frozen at `8c447f4e676f86ee034f82b33cd0856b00eed230`; immutable baseline is `16833ecc03b425586f91f4c8834dea8807bf4c22`. The candidate enables only `FORGE_SPD_CHECK_EVASION_PREFILTER=1` above default source behavior. Production defaults remain off.

Run only after all correctness gates pass, receipt hashes match, and the coordinator's CPU window is free. The validation receipt and 256-position/mode equivalence evidence identify the binaries; the profiling tool checks their hashes before and after. Source-only snapshot hashes and exact build commands are in `evasion_prefilter_validation.json`.

Fixed protocol, committed before first measured execution:

- Bench depth18, single thread, built-in 16 MB bench hash, NNUE on then off.
- Pin to the minimum allowed logical CPU; the CPU is not reserved from unrelated host work.
- One baseline and one candidate warmup per mode: four warmups total.
- Four measured cycles per mode, alternating ABBA and BAAB: 32 measured runs total.
- A is immutable baseline; B is enabled frozen candidate. Fresh engine process per run.
- Record child user+system CPU deltas, wall duration, unchanged raw stdout/stderr, node signature, load, affinity, CPU model, and binary/script hashes.
- Require all node signatures equal within each mode and successful process exit.
- Summarize candidate/baseline duration ratios per cycle and their median, preserving every run.
- No adaptive extension, favorable-result rerun, discarded slow samples, or switching primary outcomes after looking at results. A timeout, mismatch, changed binary, or other failed gate stays recorded and blocks a favorable conclusion.
- This is a shared-cloud diagnostic only. Child CPU time removes descheduling but not cache/frequency/thermal contention. Wall time includes process overhead and descheduling. Neither establishes native performance or Elo.

Command:

`python3 tests/evasion_prefilter_profile.py --evidence tests/evasion_prefilter_equivalence.json --output tests/evasion_prefilter_profile_results.json --depth 18 --cycles 4`

The output must not already exist. Do not overwrite an earlier run.

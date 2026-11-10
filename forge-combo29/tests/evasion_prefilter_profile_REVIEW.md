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

## Single frozen run result

Protocol/evidence freeze: `77c6ed24e7d7ac1bcd445565a51da372a3f3c1c8`. Completed all 32 measured runs plus four warmups on logical CPU 0, retaining every sample. Binary hashes were unchanged and all node signatures matched: NNUE on 6,066,072; NNUE off 6,134,776.

NNUE on candidate/baseline child-CPU duration ratios by cycle: 0.987622, 0.962480, 1.063806, 0.996601. Median 0.992111 (0.79% shorter duration). Wall median ratio 0.992367.

NNUE off CPU ratios: 1.034183, 0.964051, 1.007787, 0.965485. Median 0.986636 (1.34% shorter duration). Wall median ratio 0.986668.

Cycles cross parity substantially in both modes. These medians are descriptive results from this single noisy cloud diagnostic, not established speed gains. No repeat, adaptive extension, or favorable sample exclusion was performed. Native performance and Elo remain unproven; defaults stay off. Exact records are in `evasion_prefilter_profile_results.json` and `evasion_prefilter_profile.log`.

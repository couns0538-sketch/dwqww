# Picker self-swap guard: exploratory cloud timing

Status: **UNPROVEN** for speed and strength. No promotion or native acceptance.

Source candidate fccd2c79c8367f577ebe4ed6d54b556555f94cce; correctness checkpoint 42b8a05. Only FORGE_SPD_PICKER_SELF_SWAP_GUARD differs between the measured strict-FP binaries. Both use FORGE_SEARCH_SPEED2=1; other new candidate/fix switches are off. See picker_self_swap_results.json and picker_self_swap_check.sh for source-only reproduction, compiler, exact build flags, hashes and correctness scope. This experiment does not measure the SPEED2=0 configuration.

## Method and integrity

Run on 2026-11-10, 23:18:21–23:19:06 UTC. AMD EPYC 9V74 cloud host, nine visible logical CPUs, driver and children pinned to allowed CPU 0. Parent coordinated a quiet window for our workers, after TT profiling and before weak-queen validation. Host CPU was not reserved; other tenants, scheduler, frequency, power and thermal state remain uncontrolled. Initial load averages were 0.555/0.702/0.441; per-run loads are in the receipt.

Each NNUE mode had one warmup for each binary, then three ABBA cycles: baseline, candidate, candidate, baseline. Every sample used a fresh process, Threads=1, OwnBook=false, built-in eight-position bench at depth16. Wall measurements include process startup, initialization and exit. NNUE-on includes residual HCE, not just NNUE computation. Four warmups and 24 measured runs all succeeded. Every on run had 3,024,920 nodes; every off run had 2,448,617 nodes. Hashes verified before and after measurement. Baseline is byte-identical to the immutable lock:

- Baseline SHA-256: 1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6
- Candidate SHA-256: 16a3913d97fdefc34d9a5f8551f679500660b06a0eadbd5a49418fac2d2dfa9b

## Observations

Each median below contains six measured process wall times.

- NNUE on: baseline median 1.867825 s (range 1.828141–1.966303), candidate 1.821249 s (1.814772–1.939926). Per-cycle candidate/baseline mean-wall ratios: 0.989525, 0.975008, 0.981872.
- NNUE off: baseline median 1.328438 s (1.264186–1.363815), candidate 1.325676 s (1.276800–1.397476). Ratios: 1.050508, 0.970331, 1.008885.

All three on cycles were lower for the candidate in this small run; off cycles were mixed. These descriptive observations do not establish a repeatable gain, explain causality, or support Elo or native performance claims. The previously measured self-swap rate motivated the guard but is not a timing result. Limited fixed workload, short runs, uncontrolled host state and small sample count prevent acceptance conclusions.

## Reproduce

After reproducing and checking the isolated binaries with picker_self_swap_check.sh:

```
python3 tests/picker_self_swap_profile.py \
  --evidence tests/picker_self_swap_results.json \
  --output /workspace/shared/forge-build/picker-self-swap-profile \
  --cycles 3 --cpu 0
```

Select an allowed CPU if CPU 0 is unavailable; the driver rejects unavailable affinity or mismatched binary hashes. It asserts expected depth and node signatures. It writes individual stdout/stderr and timing metadata. Committed picker_self_swap_profile_raw.json preserves all 56 raw streams by filename; picker_self_swap_profile_results.json preserves commands, timestamps, individual wall times, engine-reported time, load, binary/source provenance and summary values. No binaries are committed.

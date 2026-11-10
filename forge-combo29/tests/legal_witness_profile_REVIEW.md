# Exploratory cloud profile: bounded legal witnesses

**UNPROVEN. No native performance acceptance, speed gain or Elo claim.** No production edits or engine matches.

## Validation and isolation

Production candidate: `4d9815a1e1a0807a8891be624a1c865af32299a3`, switch `FORGE_SPD_LEGAL_WITNESSES`. The implementation worker supplied isolated off/on binaries after both passed all ten depth pins plus perft, and the 128-FEN × two NNUE-mode equivalence screen passed all 256 comparisons. The profiling manifest preserves the validation receipt path and hash, source commit, binary paths and expected SHA-256 hashes. These binaries differ only by this switch, not by the other subsequent review candidates.

Both hashes were verified against the validation receipt before timing and checked again afterward. No rebuild or material-cache timing was performed.

## Timing procedure and environment

The parent confirmed its combined run and the implementation worker's isolated validation had ended, then granted a quiet window. The driver and inherited engine processes were pinned to allowed logical CPU 0 (original allowed affinity 0–8). Pinning does not reserve an exclusive physical core or control unrelated host work.

Machine: AMD EPYC 9V74 80-Core Processor; Linux 6.18.57 x86-64; nine logical CPUs visible. Initial load averages: approximately 0.707 / 0.795 / 0.702. Load samples before and after every run are preserved.

Window: 2026-11-10 20:23:58.215–20:24:43.836 UTC, about 45.6 seconds. The parent and implementation worker were notified immediately when timing ended.

For each NNUE mode, run one unmeasured warmup per binary, then three ABBA cycles: baseline, candidate, candidate, baseline. Each measured sample is a fresh process running the engine's fixed eight-position `bench 16` and exiting. The benchmark uses one thread and a 16 MB searcher, clearing search state per position. Actual process wall time uses `perf_counter_ns` and includes creation, initialization and exit. Engine-reported bench time remains a separate raw field.

## Results: descriptive only

All **24 measured runs and four warmups** completed successfully. NNUE on always reported **3,024,920 nodes**; NNUE off always reported **2,448,617 nodes**. Binary hashes remained unchanged.

- NNUE on: baseline median wall **1.874776 s**, range 1.845083–1.959716 s; candidate median **1.863541 s**, range 1.818039–1.997063 s.
- NNUE off: baseline median **1.306752 s**, range 1.263211–1.392160 s; candidate median **1.357482 s**, range 1.284490–1.452386 s.
- Per-cycle candidate/baseline ratios of mean process wall time: NNUE on **1.001063, 0.971474, 1.036336**; NNUE off **1.044075, 1.022123, 1.033360**.

The small cloud sample is not evidence for accepting this as a speed optimization. No significance test, confidence interval, native parity claim or strength conclusion is supplied. Frequency, thermal state, power management, host contention and hypervisor scheduling remain uncontrolled despite coordinated worker inactivity.

## Reproduction and receipts

```sh
python3 forge-combo29/tests/legal_witness_profile.py \
  --evidence forge-combo29/tests/legal_witness_profile_input.json \
  --output /workspace/shared/forge-build/legal-witness-profile-reproduction
```

The script requires matching validated binaries at the manifest's paths and fails on mismatch. If binaries must be rebuilt, reproduce the isolated source/configuration and validate them again rather than bypassing the hash guard.

- `legal_witness_profile_input.json`: source commit and validation provenance, plus off/on paths and hashes.
- `legal_witness_profile_results.json`: run order, commands, timing, nodes, load samples, original/effective affinity and summary.
- `legal_witness_profile_raw.json`: exact stdout/stderr keyed by the receipt's filenames.

Candidate status remains **UNPROVEN**, regardless of individual ratios or medians.

# Exploratory compact-pawn-cache cloud timing

**UNPROVEN for speed and strength. No native acceptance or speed-gain claim.** The verified cache-storage reduction is a separate result and must not be interpreted as a timing percentage.

## Preconditions and method

Used the isolated off/on binaries validated in `compact_pawn_cache_results.json`, source freeze `703562d`. Both passed focused cache/layout tests, all ten locked pins plus perft, and 256 position/configuration comparisons before timing. Off is byte-identical to the immutable lock. Binary hashes were checked before and after this profile; no rebuild or source edits occurred during the run.

The parent confirmed the combined validation run had ended and other workers were idle. The driver and inherited child processes were pinned to allowed logical CPU 0, from original affinity 0–8. The shared host was an AMD EPYC 9V74 80-Core Processor, Linux 6.18.57 x86-64, with nine logical CPUs visible. Initial load averages were approximately 0.437 / 0.584 / 0.413.

For NNUE on, then off: one warmup per binary, followed by three ABBA cycles (baseline, candidate, candidate, baseline). Each sample launched a fresh process for the fixed eight-position `bench 16`, one thread and 16 MB searcher, then exit. Wall time includes process startup/initialization/exit and uses `perf_counter_ns`; engine-reported milliseconds are retained separately.

The window ran 2026-11-10 **21:18:20.841–21:19:07.093 UTC**, about 46.3 seconds. Completion was reported immediately to release the quiet window.

## Descriptive results

All **24 measured runs plus four warmups** completed. Every NNUE-on run reported **3,024,920 nodes**, every NNUE-off run **2,448,617 nodes**. Both binary hashes remained unchanged.

- NNUE on baseline median wall **1.888297 s**, range 1.825805–1.954489 s. Candidate median **1.895714 s**, range 1.879780–1.969022 s.
- NNUE off baseline median **1.405813 s**, range 1.339527–1.486579 s. Candidate median **1.421149 s**, range 1.336035–1.541128 s.
- Per-cycle candidate/baseline ratios of mean process wall time: NNUE on **1.047608, 1.019884, 0.970990**; NNUE off **1.104096, 0.966852, 0.960533**.

Ratios vary in both directions. These six samples per binary/mode do not establish a speed benefit. CPU pinning and coordinated worker inactivity do not reserve the physical core, control frequency/power/thermal state, or eliminate unrelated host scheduling and contention. No significance test, confidence interval, native-parity claim or Elo result is supplied.

The layout result remains independently valid on the tested ABI: entry size 40→32 bytes, saving **262,144 bytes per Evaluator** at unchanged capacity. That is a payload/footprint reduction, not a measured performance improvement.

## Reproduction and evidence

```sh
python3 forge-combo29/tests/compact_pawn_cache_profile.py \
  --evidence forge-combo29/tests/compact_pawn_cache_results.json \
  --output /workspace/shared/forge-build/compact-pawn-cache-profile-reproduction
```

The script requires binary paths/hashes matching the completed correctness manifest. It fails rather than silently profiling replacement binaries. For rebuilt binaries, first repeat isolated correctness validation and record new provenance.

- `compact_pawn_cache_profile_results.json`: manifest, hashes, run order, stdin, wall times, engine receipts, per-run load samples and summary.
- `compact_pawn_cache_profile_raw.json`: exact stdout/stderr keyed by the result receipt's filenames.
- `compact_pawn_cache_profile.py`: bounded hash-verified ABBA procedure.

No production changes, engine matches, Windows binaries or bundled inputs were involved in this timing follow-up.

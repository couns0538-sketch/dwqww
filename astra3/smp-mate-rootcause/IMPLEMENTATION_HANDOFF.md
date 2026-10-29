# A2 native diagnostic implementation handoff

Engine source: `926c55f33227bc4a030d7ce5b1140528aeba75af`; branch base: integration `93c51b3`. IDEA_SOURCE: the user's Round 3 A2 handoff and Forge's own public `Worker`, `SharedSearchState`, TT, Board and atomic-node interfaces. No engine/header/CMake changes or foreign engine code.

**Compile and runtime status: UNVERIFIED; awaiting parent GO.** This source is a diagnostic, not a fix or an acceptance test. Root owns Git and publication.

## First build and bounded run

Run from this worktree after A1 qualification permits native workloads:

```sh
python3 astra3/smp-mate-rootcause/source/build_a2_repro.py \
  --repo /tmp/forge-astra3-smp-mate-rootcause \
  --core-build /tmp/forge-astra3-build-integration \
  --out /tmp/forge-astra3-smp-mate-rootcause/astra3/smp-mate-rootcause/build_first
```

The helper checks all frozen engine/header/CMake hashes against both the diagnostic worktree and A1 build's source tree; checks Release flags, H256 and ABI-sensitive build switches; checks archive freshness; then records the exact compile command, archive/driver hashes, output, exit code and binary hash. It links only the existing qualified archive. Matching source/flags/timestamps is not a substitute for the original A1 build evidence. The underlying invocation is:

```sh
/usr/bin/g++-14 -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off \
  -DFORGE_NNUE_HIDDEN=256 -O3 -DNDEBUG -std=gnu++20 -Wall -Wextra -Wpedantic -Wconversion -Wshadow \
  -ffp-contract=off -I/tmp/forge-astra3-smp-mate-rootcause/include \
  /tmp/forge-astra3-smp-mate-rootcause/astra3/smp-mate-rootcause/source/a2_tt_seed_repro.cpp \
  /tmp/forge-astra3-build-integration/libforge_core.a -pthread \
  -o /tmp/forge-astra3-smp-mate-rootcause/astra3/smp-mate-rootcause/build_first/a2_tt_seed_repro
```

Choose one currently permitted CPU from the verified affinity mask (do not assume CPU 0 is available):

```sh
astra3/smp-mate-rootcause/build_first/a2_tt_seed_repro \
  --mode serial --trials 1 --max-seed-depth 14 --main-depth 14 \
  --seed 20261029 --cpu CPU_NUMBER --smp-v2 1 --max-seconds 120 --trial-seconds 10 \
  --out astra3/smp-mate-rootcause/serial_first
```

Redirect stdout/stderr to NEW files outside that still-nonexistent output folder. Every run requires a new output directory; the harness refuses an existing one. It never kills another process. Exit 0 means the requested diagnostic workload completed, including any observed chess misses; exit 2 means harness/IO error; exit 3 means a timeout/budget interruption. Original partial files remain on failure. CPU affinity is verified and recorded; child threads inherit it.

## Experiment semantics and limits

- Serial mode runs independent `empty_control` and `serial_seeded` conditions per K=1..14/trial. Each condition gets fresh workers and a 16 MB TT, then **two** logical searches retaining TT and worker history between rounds. Each seeded round completes helper id 1 at nominal K, then main id 0 at requested depth 14, with the same TT generation and no active helper during main. Main is fresh at round 1; round 2 deliberately keeps its history. Controls also perform two searches.
- Optional `--mode concurrent --trials 100 --max-seed-nodes 16384` uses two simultaneous workers. A seeded PRNG chooses main-start target helper nodes; waiting reads only public atomic `nodes()` or an acquire/release completion flag. Log includes target, observed published nodes, elapsed wait, and whether the helper had already finished. Targets are deterministic; **OS scheduling and outcomes are not**. Both workers use main-depth 14, with SmpV2 helper diversification controlled by `--smp-v2 0|1`.
- Watchdog stop is per trial (both searches) and bounded by the run wall deadline. Stop reset and watchdog publication share a mutex, preventing a late reset from erasing timeout. Results marked `ABORTED_TIMEOUT` are excluded from complete-result counts.
- Raw `worker_results.tsv` logs main/helper before any selector: actual/nominal depth, score, move, PV, reported total nodes, per-worker published nodes and elapsed milliseconds. The driver does not call `smp_select_result`. Published counters reset between logical rounds; this affects accounting, not depth-limited search.
- `final_tt_snapshots.tsv` contains root/first-three-ply unique keys **only after both measured searches finish** and helpers join. `probe()` ages entries, so snapshots never run before another measured search in that trial. They have no per-store worker provenance and cannot prove an interleaving or GHI. Position paths identify watched keys, not the path that produced the entry.
- Aggregate summary mixes conditions; derive per-condition/search-round counts from original TSV. `CP` means outside either mate band. `EXPECTED_EXACT` means 31995/d5c5. Other mate scores are explicitly UNVERIFIED, not certified by an oracle here.
- The harness freezes the embedded H256 network and default options besides SmpV2; no external Syzygy network/file or UCI process is involved. Bound checks and provenance tracing remain later experiments if this first sweep reproduces the symptom.

No speed, strength, root-cause or fix claim is made. Do not interpret a zero-miss serial sweep as refuting concurrency-sensitive contamination.

# Public NNUE update microbenchmark

`tools/nnue_update_benchmark.cpp` measures calls to the actual out-of-line
`forge::nnue::update` in the linked frozen core. It contains no replacement
arithmetic and does not train or change weights. This is a microkernel result,
not engine NPS, playing strength, Windows performance, or physical Ryzen evidence.
At authoring, no compilation or timing run was performed.

The default invocation performs 2,000,000 timed updates from a deterministic
corpus of real legal transitions, with up to 16,384 separate warmup calls.
`--iterations N` changes the timed count; N must cover the selected corpus.
`--group quiet` is the primary two-change remove/add experiment and is the
default. These transitions can include noncapturing promotions. Other groups
are diagnostics: `capture` uses three changes (including promotion captures and
en passant), `castle` four, `null` zero, and `all` concatenates the capped groups.
The `all` mix is not an estimate of actual search-category frequencies.

Corpus construction is outside timing: ten FENs, every legal first move and
96-ply fixed-seed legal walks provide freshly refreshed parent accumulators and
the public dirty-piece API's changes. Real null transitions are included.
Deterministic reservoir sampling retains at most 64 transitions per dirty
count. The input hash covers every retained parent lane, validity, and active
dirty field. Preparation and warmup are excluded from reported timings.

Timed calls use distinct parent/output objects in a bounded output ring, with
one output per selected corpus entry. After timing, FNV-1a hashes every final
output float lane and validity. Per-call hashing is deliberately excluded from
the kernel measurement. Every update must remain an actual external call:
compile **both core and driver without LTO** and inspect the final call site.
Out-of-line calls have observable effects and cannot be removed merely because
later calls reuse an output slot. The checksum is not a cryptographic proof or
a digest of every intermediate overwritten output; use the separate differential
snapshot driver for correctness.

JSON output records timed/warmup call counts, selected corpus size, dirty counts
0..4 actually used by the timed traversal, pre-reservoir counts, full input/output
hashes, elapsed steady-clock nanoseconds, process CPU ticks and CLOCKS_PER_SEC,
hidden size, accumulator size, initial MXCSR controls, compiler identity,
optimization/AVX2 macros, and a caller-supplied flags label. Category call counts
are calculated from the exact cyclic traversal outside timing. Round-to-nearest
is required; FTZ/DAZ and other controls must match across binaries. Compilation
rejects fast-math/finite-math macros; the strict FP and non-LTO flags of the
linked core must still be verified independently.

Compile this exact same driver against each frozen core, using identical flags:

```sh
g++ -std=c++20 -O3 -march=x86-64-v3 -mtune=znver5 \
  -fno-fast-math -ffp-contract=off -fno-lto \
  -DFORGE_NNUE_BENCH_FLAGS='"-O3 -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto"' \
  -I "$BASE_SOURCE/include" "$BENCHMARK_SOURCE/tools/nnue_update_benchmark.cpp" \
  "$BASE_BUILD/libforge_core.a" -pthread -o "$BASE_BUILD/nnue_update_benchmark"
g++ -std=c++20 -O3 -march=x86-64-v3 -mtune=znver5 \
  -fno-fast-math -ffp-contract=off -fno-lto \
  -DFORGE_NNUE_BENCH_FLAGS='"-O3 -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto"' \
  -I "$CANDIDATE_SOURCE/include" "$BENCHMARK_SOURCE/tools/nnue_update_benchmark.cpp" \
  "$CANDIDATE_BUILD/libforge_core.a" -pthread -o "$CANDIDATE_BUILD/nnue_update_benchmark"
```

A later preregistered experiment may invoke `--group quiet --iterations 2000000`
on a separately calibrated host. Freeze iterations, binaries, weights, compiler
commands, corpus/checksums, affinity and stopping/noise rules before comparing.
Require same-binary A/A calibration, then counterbalanced A/B order such as ABBA;
retain raw JSON and all failures. Compare input/output hashes and category counts
before ratios. Do not repeat the already failed same-host calibration or infer
whole-engine speed or Elo from this tool. Other groups remain diagnostic.

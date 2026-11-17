# Prediction for Step 1 — committed BEFORE the profile, never edited

File 7 requires the prediction in its own commit, ahead of the measurement. This file is that commit. Anything I
learn afterwards goes in `PROFILE_RESULT.md`, not here.

## What I am predicting about

`bench 13` under PC20 + the test net, `Threads 1`, on the build verified by Step 0
(`227aae56ef1678…`, `-DFORGE_NNUE_V3=1`, g++ 13.3.0, generic x86-64, AVX-512 kernel).

Step 0 passed 11 of 11, so this build evaluates through the v3 path, not the built-in net.

## The two candidate hot spots, and why they are the candidates

Reading `src/nnue_v3.cpp` and the call site at `src/search.cpp:3139`, an evaluation does two separable things:

1. **The accumulator update** — `make_valid` → `apply_changes_pair` → `apply_changes_pair_avx512`, which for each
   dirty piece adds one column and subtracts another, for **both perspectives**. A column is `hidden` = 512
   `int16` = 1 KB. A move touches ~2 pieces, so ~2 pieces × 2 perspectives × 2 columns = **~8 KB of reads per
   move**, gathered from `w1`.
2. **The forward pass** — `evaluate` → `output_sum_avx512`, a dot product of 2 × 512 `int16` against `w2`, i.e.
   **1,024 multiply-adds**, then `finish` scales and clamps.

## The prediction

| # | claim | my number |
|---|---|---|
| P1 | hottest single v3 item | **the accumulator update** (`apply_changes_pair_avx512` and the column add/sub it calls), **40–65 %** of the v3 total |
| P2 | forward pass | `output_sum_avx512` plus `finish`, **10–25 %** of the v3 total |
| P3 | all v3 functions together | **15–40 %** of `bench 13` wall time; the search around them is the rest |
| P4 | the update is **memory-bound**, not instruction-bound | `w1` is 8 × 768 × 512 × 2 B = **6,291,456 B ≈ 6.0 MiB**, far past a core's L2, so the update's cost is dominated by the column gathers, not by the 512-wide adds. Consequence: making the adds cheaper buys little; making the *reads* more local is where the speed is. |

## What would kill each claim

- **K1 (kills P1)**: the accumulator update comes in under **20 %** of the v3 total, or is not the top item.
- **K2 (kills P2)**: the forward pass exceeds **40 %**, i.e. the path is compute-bound on `w2`, not on `w1` reads.
- **K3 (kills P3)**: all v3 functions under **10 %** or over **60 %** of `bench 13`.
- **K4 (kills P4)**: the update's share barely moves when the same profile is taken with a net small enough to sit
  in L2 — if it scales with instruction count rather than with `w1` footprint, my memory-bound story is wrong.

I expect P4 to be the interesting one either way: it decides whether Step 2 should be about vector width or about
memory layout, and those are different patches.

## Why I trust a wide range

Because I have not measured this path once, and my record on this swarm says a confident number written before
measuring is wrong about half the time (`S-F110`: three transcription errors in one harness). A range with a named
kill condition is worth more than a point estimate, because a kill is information and a missed point estimate only
looks like bad luck.

## A limit on the tool, stated before I use it

`perf` is not installed here and `/proc/sys/kernel/perf_event_paranoid` is `2`, so userspace sampling through
`perf` is unavailable. I will use `gprofng`, which is present. **Its symbol attribution may differ from `perf`'s**,
especially for inlined `inline void add_column_avx512(...)`. If the column adds are inlined into
`apply_changes_pair_avx512` and cannot be separated, the profile still answers P1 but not the split between the
reads and the adds — and I will say so rather than invent the split.

TO ASTRA for independent verification and a vote. Fable, for the "For later, once the engine is stronger" addendum list once both seats agree.

PROPOSAL N21 — For later, once the engine is stronger (Fable #5): Candidate NNUE architectures after `1024 x 8kb x 8ob`, their `W9` integer-headroom requirements, zero-confounded NPS costs, and the one fixed-clock test that decides between shapes at equal cost.

KIND: exact `W9` integer-overflow proof + live AVX-512 & AVX2 zero-confounded end-to-end engine benchmarks (zero-padded `r67`, bit-identical `1,667,608`-node `bench 15`) + 2,000,000-iteration AVX-512/VNNI kernel microbenchmarks on unmodified `source/src/nnue_v3.cpp`.

### Five Required Later-Plan Fields
- **WHEN:** After `W8` (large-store trainer) qualifies, the `>= 2B`-row store is verified, and `W13 (b)` finishes its matched `1024 x 8kb x 8ob` vs `768 x 8kb x 8ob` comparison — specifically once `1024 x 8kb x 8ob` is adopted (or plateaued) and `>= 2B`–`4B` unique kept rows are available to feed higher-capacity architectures without bucket starvation.
- **WHAT:** Evaluate candidate shapes past `1024 x 8kb x 8ob` in order of implementation risk and measured speed-per-parameter efficiency (comparing at most two candidates head-to-head per training budget):
  1. **Candidate A — `1024 x 16kb x 8ob` (or `16ob`, more mirrored king buckets, ZERO C++ format change):** Already supported by `source/src/nnue_v3.cpp` (`MaxKingBuckets = 32`, `MaxOutputBuckets = 16`, `MaxHidden = 1024`). Doubles `w1` capacity (`6.31M -> 12.60M` params, same total parameter budget as `2048 x 8kb`), keeps per-worker accumulator+Finny cache at `608 KiB` (`+32 KiB`, well inside 1 MiB L2), stays 100% inside `W9`'s proven `H=1024` `int32` headroom, and measured **`0.00%` end-to-end `bench 15` NPS loss on AVX-512** (`-2.51%` on AVX2) even with doubled rank-parity bucket crossings. *Trade-off:* halves training samples per `(king_bucket, piece, square)` feature — requires the `>= 2B`-row store so buckets do not overfit.
  2. **Candidate B — `1536 x 8kb x 8ob` (wider single-layer SCReLU):** `9.46M` params (`1.5x`), `864 KiB` worker cache, shares features across more king positions than `16kb` (less data-hungry per bucket), kernel latency `+45.9%` vs `1024` (`72.8 -> 106.2 ns` AVX-512; forecast `~-6%` to `-10%` end-to-end NPS on target CPU). **Mandatory `W9` kernel prerequisite before ANY `H > 1024`:** fix `source/src/nnue_v3.cpp:125` (`hsum_epi32_pair_avx2`)! Unmodified AVX2 sums `sum0 + sum1` in `int32` (`H/4` terms/lane) and **silently wraps negative starting at `H = 1056`** (`-16,918,472,768` vs exact `+17,441,265,600`), while AVX-512 (`H/8` terms/lane) stays exact up to `H = 2048` — a silent cross-ISA divergence! Widening `sum0` and `sum1` separately to `int64` before adding (`avx2_wide`, 4 post-loop instructions, 0 extra loop instructions) extends exact AVX2 parity to `H = 2048` (`2,114,092,800 <= INT32_MAX`).
  3. **Candidate C — `2048 x 8kb x 8ob` (2x wider single-layer SCReLU):** `12.62M` params, hits the exact `H = 2048` ceiling of both `avx2_wide` and `avx512_prod` (`H > 2048` requires periodic `int64` block drains), `+93.5%` kernel latency (`72.8 -> 140.9 ns` AVX-512; forecast `~-12%` to `-18%` end-to-end NPS), and `1,152 KiB` per-worker stack+Finny state (exceeds 1 MiB L2 per core — must be timed on the target Zen 5 CPU!).
  4. **Candidate D — Multi-layer pairwise+VNNI head (`768` or `1024 -> 16 -> 32 -> 1`, Stockfish SFNNv9 style):** Adds nonlinear piece-interaction capacity with only `+0.09M–0.12M` head parameters and eliminates cubic `255^2 * 127` `int32` scaling (`uint8 * int8` `vpdpbusd` max `1024 * 127 * 127 = 16.5M << INT32_MAX`), **but** requires a new `.fnn3` v4 format, trainer export, and cross-ISA `VNNI`/`AVX2`/`scalar` kernels, and measured `+194%` kernel latency (`72.8 -> 214.3 ns` at `H=1024` AVX-512+VNNI; forecast `~-15%` to `-28%` end-to-end NPS). Only worthwhile once single-layer scaling (`16kb` / `1536`) visibly saturates.
- **TEST (the ONE test that decides between two shapes at equal cost):**
  1. **Pre-training safety & zero-confounded speed check (CPU seconds):** Verify `W9` worst-case `int16`/`int32` bounds + cross-ISA bit-exact parity (`AVX-512 == AVX2 == scalar` under `-DFORGE_NNUE_V3_VERIFY=1` on worst-case `b1=255, w2=±127` and realistic nets), and measure target-CPU end-to-end NPS delta (using zero-padded / identical-eval fixtures where applicable, plus real trained-net `bench 15`).
  2. **Matched training:** Train both candidate shapes on the **EXACT SAME frozen data window**, same teacher/target recipe, same optimizer/schedule, and equal declared GPU training budget (recording actual GPU wall-hours and final validation loss, while still judging by games per `J1`).
  3. **The deciding match — FIXED-CLOCK paired match on the target PC (`10+0.1` screen, then `60+0.6` LTC confirmation, reversed opening pairs, `Threads 1`, pinned `Hash`):** A fixed-node match (`250k` nodes) hides the `-4%` to `-25%` real-world speed penalty of wider/deeper shapes and cannot decide between architectures of different speed. Run a secondary fixed-node diagnostic (`250k` nodes, 2,000–4,000 games) only to separate raw eval quality from NPS cost; **the fixed-clock match decides**.
- **BAR:**
  - Zero `W9` overflow / cross-ISA parity mismatches across all compiled ISAs.
  - Between two candidate shapes (or candidate vs `1024 x 8kb` incumbent) trained on the same window and budget, advance the winner only if its **fixed-clock** paired match clears its predeclared positive lower bound (`95%` opening-pair LB `> 0` on the `10+0.1` screen and confirmed on `60+0.6` LTC, plus `R1` `-3/0` self-play non-regression at equal CPU wall-time or `2k` soft-nodes per `W5(g)` economics before replacing the self-play net).
- **WHY IT WAITS:** `W13 (b)` has not yet trained or tested `1024 x 8kb` on the 2B store (`W8`), and larger bucket counts (`16kb`) or widths (`1536`/`2048`) need both the verified large data store and the target PC's measured `1024` baseline before spending GPU hours or altering the `.fnn3` v3 format.

### Reproducible Proof (measured on this AVX-512/VNNI Linux VM on unmodified `source/src/nnue_v3.cpp`)
1. **Exact `W9` AVX2 vs AVX-512 `int32` overflow boundary (`b1 = 255, w2 = +127`, exact formula `2 * H * 255^2 * 127`):**
   - `H = 768`: exact `12,684,556,800` | `avx2_prod`: OK | `avx2_wide`: OK | `avx512_prod`: OK.
   - `H = 1024`: exact `16,912,742,400` | `avx2_prod`: OK (`256` terms/lane = `2,114,092,800`, `1.55%` below `INT32_MAX`) | `avx2_wide`: OK | `avx512_prod`: OK.
   - **`H = 1056`**: exact `+17,441,265,600` | **`avx2_prod`: `-16,918,472,768` (OVERFLOW!)** | `avx2_wide`: OK | `avx512_prod`: OK.
   - **`H = 1536`**: exact `+25,369,113,600` | **`avx2_prod`: `-8,990,624,768` (OVERFLOW!)** | `avx2_wide`: OK | `avx512_prod`: OK.
   - **`H = 2048`**: exact `+33,825,484,800` | **`avx2_prod`: `-534,253,568` (OVERFLOW!)** | `avx2_wide`: OK | `avx512_prod`: OK.
2. **Zero-confounded end-to-end real-engine NPS (`bench 15`, 5 repeats median, BIT-IDENTICAL `1,667,608` nodes via zero-padded `r67` & duplicated rank-parity `16kb`):**
   - `768 x 8kb -> 1024 x 8kb`:
     - AVX-512 (`-march=x86-64-v4`): `2,355,378 -> 2,253,524` NPS (**`-4.32%`**).
     - AVX2 (`-march=x86-64-v3`): `2,185,593 -> 1,992,363` NPS (**`-8.84%`**).
   - `1024 x 8kb -> 1024 x 16kb` (doubled king-bucket crossings + `2x` `w1` RAM):
     - AVX-512: `2,247,450 -> 2,247,450` NPS (**`0.00%`**).
     - AVX2: `2,048,658 -> 1,997,135` NPS (**`-2.51%`**).
3. **Standalone kernel latency (2,000,000 iters, 2-col quiet update + eval, ~25% active L1 sparsity) & per-worker memory (`136` plies + `2*kb` Finny cache):**
   - `H = 768`: `1L AVX-512 = 55.9 ns`, `1L AVX2-wide = 85.5 ns`, `2L VNNI (768->16->32->1) = 163.4 ns` | `4.73M` / `4.82M` params | `432 KiB`.
   - `H = 1024`: `1L AVX-512 = 72.8 ns`, `1L AVX2-wide = 116.9 ns`, `2L VNNI (1024->16->32->1) = 214.3 ns` | `6.31M` / `6.43M` params | `576 KiB`.
   - `H = 1536`: `1L AVX-512 = 106.2 ns`, `1L AVX2-wide = 161.1 ns`, `2L VNNI (1536->16->32->1) = 326.3 ns` | `9.46M` / `9.64M` params | `864 KiB`.
   - `H = 2048`: `1L AVX-512 = 140.9 ns`, `1L AVX2-wide = 217.6 ns`, `2L VNNI (2048->16->32->1) = 430.4 ns` | `12.62M` / `12.85M` params | `1,152 KiB`.
   - Note: End-to-end NPS deltas for `1536`/`2048`/`2L` are **forecasts** until measured on the target Zen 5 PC (where L2 size and VNNI throughput differ from this Intel Xeon VM).

COST: Zero now; future cost is matched trainings + fixed-clock matches when `W13 (b)` finishes.

WHAT WOULD CHANGE MY MIND: If `1024 x 16kb` underfits/overfits on the `2B`-row store compared to `1536 x 8kb`, the fixed-clock head-to-head match decides directly; if a target-PC zero-padded `1536` or `2048` build shows much smaller or larger L2 spill than forecast here, re-rank candidates by the target-PC measurement.

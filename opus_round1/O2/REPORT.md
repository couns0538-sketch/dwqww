# O2 [Engine QA] NNUE accumulator speed rewrite with exact parity — DONE (speed target not reached)

Branch `opus-O2` = `opus-O3` (`0d99f02`: verbatim AL1 s198 + [BASELINE] CI + O3 no-op refactor) + [O2] commits.
Code commit: `edcf163`. Patch: `patch.diff` (`git diff 0d99f02 edcf163`, engine tree and tests).
Speed-only job: output is bit-identical, so there is no UCI option and no gate. NPS numbers are measurements,
not Elo claims.

## Result in one table

| # | acceptance line | result |
|---|---|---|
| 1 | profile first (perf/VTune, tools/nnue_update_benchmark.cpp) | done: callgrind on CI (lock and O2, `bench 13`) + the update microbenchmark (no perf/VTune on the Windows PC) |
| 2 | lazy accumulator updates | already lazy in AL1 s198 (described below); kept unchanged |
| 3 | SIMD (AVX2 + SSE2 + scalar fallback) for every update/refresh kernel incl. castling and promotion-capture; aligned memory; weight layout | done: explicit SSE2/AVX2 kernels for quiet, capture/en passant/promotion-capture, castling, refresh; portable fallback; 64-byte aligned w1/b1/w2/accumulators |
| 4 | no FMA; same float order; document the guarantee | done: FMA 0 in every build; two independent guarantees, below |
| 5 | parity harness (deliver it), >= 1,000,000 positions on random make/unmake walks and the 5_nnue sample data, bit-for-bit, scalar / SSE2 / AVX2 builds | **PASS**: `tests/nnue_parity_tests.cpp` (CTest), 1,303,743 positions in CTest and 1,578,127 with the 5_nnue `.pos` sample, 0 differences, same digest on scalar, SSE2, AVX2 and AVX-512-target builds, on Windows (g++ 15.2) and Linux CI (g++ 14) |
| 6 | bench node counts identical at all 5 depths; FMA 0 | **PASS** (PC recipe build and box recipe build, Windows and Linux CI) |
| 7 | speed: microbenchmark and bench NPS, 10 runs each, mean and stdev; target >= +10% bench NPS (report actual) | microbenchmark, mixed corpus: update **−16% per call** on a quiet runner (Intel 8370C, AVX2); −9% / −7% on the loaded PC (AVX2 / AVX-512 target). Castling −55% to −60%. Bench NPS on quiet runners: **O2 alone (O3 → O2) +3.3%** (d16 and d20, intervals ±0.2-0.4%); lock → O2 +3.5% to +3.7%. Loaded PC, d20: +3.0%. **The +10% target is not reached**; the profile shows why it cannot be with bit-exact NNUE-only changes (section 3) |
| 8 | compile-time path selection only | done (`FORGE_NNUE_FORCE_SCALAR`, `__AVX2__`, `__SSE__`, `__AVX512F__`); no UCI change |
| §3 | ctest only known failures; ASan+UBSan, TSan | **PASS**: local ctest 17/18 with only the 4 known lines; CI run 40410897141 release/asan/tsan green |

## 1. What changed

- `src/nnue.cpp`
  - **Kernels.** The accumulator kernels are written once against four vector helpers (`vec_load`, `vec_store`,
    `vec_add`, `vec_sub`). At compile time these become AVX2 (`__m256`) or SSE2 (`__m128`) intrinsics, or plain
    floats, which give the portable fallback.
    - Quiet moves and noncapturing promotions: one pass computing `(in - r) + a`.
    - Captures, en passant and capturing promotions: one pass computing `((in - r0) - r1) + a`.
    - **Castling (new):** one pass computing `(((in - r0) + a0) - r1) + a1`. AL1 copied the parent and then made
      four passes.
    - Null moves and any other change list: the AL1 copy-then-apply loop.
    - **Refresh:** collects the piece columns in AL1 order and adds them while a block of 8 vectors (64 lanes
      with AVX2) stays in registers. AL1 loaded and stored the accumulator once per piece.
  - **Selection.** AVX2 kernels on AVX2 targets, SSE2 kernels on SSE2-only targets, and the portable loops for
    `FORGE_NNUE_FORCE_SCALAR` and for AVX-512 targets. On the PC recipe (`-march=znver5`), GCC widens the portable
    loops to 512 bits itself, as it already did for AL1. Explicit AVX-512 kernels are Astra's N25, not this job.
    The AVX2 and SSE2 kernels are not used on AVX-512 targets, because they would replace the 512-bit code GCC
    generates there.
  - **Alignment.** `w1` (768 x 256 floats) is allocated with `operator new[](..., std::align_val_t{64})`, and `b1`
    and `w2` are `alignas(64)`. Every 1 KB feature column now starts on a cache line.
  - `evaluate()` is unchanged: the same AVX2 / SSE / scalar output layer with the same lane association. Two
    small edits: `FORGE_NNUE_FORCE_SCALAR` now also selects its scalar path, and the `__AVX2__` test goes through
    a macro.
- `include/forge/nnue.hpp`: `Accumulator::values` is `alignas(64)`, up from 32. `SearchStack` grows from
  2720 bytes (an odd multiple of 32) to 2752 bytes (43 x 64), so every ply's accumulator is cache-line aligned.
  In AL1 every other ply's accumulator sat at 32 mod 64, which split each 512-bit access in the PC build.
- `tests/nnue_parity_tests.cpp` + `tests/data/nnue_selfplay_sample_916.txt` (the 916 real self-play FENs from
  `5_nnue/sample_data/forge_text_sample`) + CTest `forge_nnue_parity_tests`.
- CI: `.github/workflows/opus-o2-parity.yml` builds every kernel target on Linux, checks the digests, bench and
  FMA. `.github/workflows/opus-o2-perf.yml` runs callgrind, NPS A/B, and the microbenchmark on a quiet runner.
- Tools (`opus_round1/O2/`): `verify_lock_ref.py`, `mutation_check.py`, `update_bench.py`.

### Lazy updates (already in AL1, unchanged)
`Worker::record_move` (before make-move) only stores the move's `DirtyPieces` and marks the child accumulator
invalid. `Worker::static_evaluate` (src/search/evaluation.inc) is the only place where accumulators are
computed. It walks back to the nearest valid ancestor and replays the stored changes, or refreshes when no
ancestor is valid (in practice only at the root, where `iterative.inc` refreshes once per search). Nodes that
never reach `evaluate()` (TT cutoffs, mate-distance pruning, aborted nodes) never pay for an update. O2 makes
each replayed update cheaper and does not change when updates happen.

## 2. Why the output is bit-identical (two independent guarantees)

**(a) Same operations, same order.** In every kernel, each accumulator lane gets exactly the float operations the
AL1 code applies to it, in the same order:
- the parent value;
- then the changes in `DirtyPieces` order (subtract a removed piece, add an added piece);
- for refresh, `b1` followed by the piece columns in ascending square order.

Lanes never interact, so vector width only changes how many lanes one instruction handles. `evaluate()` is
the AL1 code. There is no FMA: `-ffp-contract=off` is used, and every build has an FMA count of 0. There is no
`-ffast-math`, and no reassociation. This is the guarantee the job asked for.

**(b) The accumulator arithmetic is exact anyway.** Every `w1` and `b1` value is an `int16` divided by
`WeightScale` = 4096, i.e. `k * 2^-12` with |k| <= 32767. The int16 type and the 4096 scale are fixed by
`nnue_weights.inc` and its `static_assert`s. Every accumulator value, and every intermediate value of every
kernel, is a signed sum of at most 69 such terms: the bias, at most 64 pieces, and at most 4 changes in
flight. So it is a multiple of 2^-12 with magnitude at most 69 x 8 = 552 < 2^12, i.e. an integer below 2^24
times 2^-12. It therefore fits in the 24-bit float significand, and no addition or subtraction producing it is
ever rounded. As a consequence:
- any order or grouping of the accumulator sums gives the same bits;
- incremental updates always equal a full refresh.

The parity harness checks this invariant on every accumulator it compares. The mutation check confirms it:
four reassociated kernels give the same bits, and only the output layer, where products are rounded, is
order-sensitive.

So the only rounding happens in `evaluate()`'s output layer, which O2 does not touch.

## 3. Profile: where the time goes

Callgrind, `bench 13` (862,329 nodes), box recipe + `-g`, g++-14 on the CI runner (CI run 40410897098,
`logs/ci_perf_edcf163/profile_self_*.txt`). The unit is instructions (Ir), not cycles.

| function (self Ir) | AL1 s198 | O2 |
|---|---:|---:|
| program total | 5,009,901,526 | 4,990,221,300 |
| start-up (magic tables, hash clearing memset) | 723.8M (14.4%) | 723.9M (14.5%) |
| HCE `evaluate_position` (residual base) | 782.7M (15.6%) | 782.7M (15.7%) |
| `MovePicker::next` | 536.8M (10.7%) | 536.8M (10.8%) |
| **`nnue::update`** | **414.0M (8.3%)** | **363.0M (7.3%)**, −12.3% |
| `nnue::evaluate` | 260.2M (5.2%) | 260.2M (5.2%) |
| `nnue::refresh` | below 0.1% | below 0.1% |

- NNUE (update + evaluate) is **15.7% of the search's instructions**, start-up excluded. Even a free NNUE would
  give at most 1/(1−0.157) = +19% NPS.
- The output layer is fixed by the bit-exactness requirement: same lane association, and a final sum of 16
  lanes in order. The accumulator part was already vectorised in AL1. So +10% total NPS would need about −64%
  of the whole NNUE time, which bit-exact NNUE-only changes cannot deliver.
- The HCE `evaluate_position` is as large as the whole NNUE (the shipped net is a residual on top of the HCE).
  It is outside this job.
- O2's instruction savings are small (−0.4% total). Most of the gain comes from cycles: the fused castling
  pass, no cache-line-split loads, and fewer loads and stores per update.
  - With glibc, AL1's 768 KB `w1` block comes from `mmap` and starts 16 bytes after a page boundary. Half of all
    AVX2 column loads therefore crossed a cache line.
  - In the PC build every other ply's accumulator did the same for 512-bit accesses.
  - O2 aligns both to 64 bytes.

## 4. Parity harness (`tests/nnue_parity_tests.cpp`)

- **Oracle.** `forge::nnue::lock_ref` is a verbatim copy of AL1 s198 `src/nnue.cpp`:
  - lines 8-20: the SIMD selection;
  - lines 46-76: the weights and feature helpers;
  - lines 84-216: `refresh`, `update`, `evaluate`.

  `verify_lock_ref.py` checks the copy against `git show 294dbed:src/nnue.cpp` (PASS, 3 sections). The copy
  builds its own `w1` from `nnue_weights.inc`, so the comparison is between two independent implementations.
- **Comparisons.** Every accumulator float is compared as a bit pattern, both perspectives and all 256 lanes,
  along with the `valid` flag and every `evaluate()` result. Each accumulator value must also satisfy the
  exactness invariant from section 2(b). Children are pre-filled with a sentinel, so a lane that a kernel fails
  to write is caught.
- **Inputs:**
  - *Random make/unmake walks.* Legal moves; null moves (1/16 of the steps, never in check or twice in a
    row); back-tracking 1-6 plies on 1/8 of the steps as a search does; plies capped at 160. Castles, en
    passant and promotions are preferred on half of the steps when available. Every walked position is
    compared after its incremental update, 1/32 also after a full refresh, and 1/4 also through an **in-place**
    update (`update(acc, acc, ...)`, which `tools/nnue_update_snapshot.cpp` relies on).
  - *Exhaustive 3-ply trees* from 11 fixtures (castling both sides and colours, en passant, quiet and capturing
    promotions, kiwipete, two open middlegames).
  - *The 916 self-play FENs:* refreshed, then used as walk roots.
  - *5_nnue v3b `.pos` files* (`--pos`). The synthetic `data32_sample` boards are made legal deterministically:
    back-rank pawns dropped, one king per side, impossible inventories trimmed, side to move swapped if needed.
    Of 250,000 boards, 179,439 were used and 70,561 skipped. Every 16th used board also gets an 8-step walk.
  - *100,000 synthetic accumulators* for `evaluate()`, including SCReLU edge values: −0.0, the smallest
    denormal, values next to 1.0, negative and saturated values.

**Runs** (`logs/parity_*.log`). Run 1 is the CTest configuration; run 2 adds the five 5_nnue
`data32_sample_50k/*.pos` files.

| build | flags | run 1: positions, digest | run 2: positions, digest |
|---|---|---|---|
| portable scalar | `-march=x86-64 -fno-tree-vectorize -fno-tree-slp-vectorize -DFORGE_NNUE_FORCE_SCALAR=1` | 1,303,743, `f807d80cbabc1d59` | 1,578,127, `d298486662e26f6f` |
| SSE2 | `-march=x86-64` | 1,303,743, `f807d80cbabc1d59` | 1,578,127, `d298486662e26f6f` |
| AVX2 (box) | `-march=x86-64-v3 -mtune=znver5` | 1,303,743, `f807d80cbabc1d59` | 1,578,127, `d298486662e26f6f` |
| AVX-512 target (PC) | `-march=znver5` | 1,303,743, `f807d80cbabc1d59` | 1,578,127, `d298486662e26f6f` |
| Linux CI g++-14: scalar, SSE2, AVX2 | as above | 1,303,743, `f807d80cbabc1d59` (`logs/ci_parity_edcf163/`) | — |

The CI runner (AMD EPYC 7763) has no AVX-512, so the CI job skips that target. It runs on the PC.

Run 2's move mix:
- quiet 1,179,315, captures 91,700, en passant 226;
- promotions 12,343, capture-promotions 1,129;
- castles 8,267, null moves 58,813.

Every run: **PASS, 0 differences**.

**Planted bugs** (`mutation_check.py`, AVX2 build, `logs/mutation_check.log`). All 12 cases came out as
expected.
- Must FAIL, and did: wrong column in the quiet kernel; capture skips its second removal; castling swaps the
  rook squares; refresh drops the last piece; last vector of the quiet kernel left unwritten; output layer
  without the upper clamp; output lane sum reversed.
- Must PASS, and did: the clean tree, and the four reassociated accumulator kernels (quiet, capture, castling,
  reversed refresh order). This is the exactness of 2(b) in action.

## 5. Bench identity (all 5 depths) and FMA

| build | d11 | d13 | d16 | d20 | d22 | perft5 / kiwipete | FMA |
|---|---|---|---|---|---|---|---|
| PC recipe (`build_pc.sh`, g++ 15.2, znver5), sha256 `ee002548…` | 312866 | 862329 | 3024920 | 12389307 | 34048354 | 4865609 / 193690690 | 0 |
| box recipe (CMake, x86-64-v3) | 312866 | 862329 | 3024920 | 12389307 | 34048354 | same | 0 |
| SSE2, scalar, znver5 CMake builds | 312866 | 862329 | 3024920 | (not run) | (not run) | same | 0 |
| Linux CI g++-14 (release, scalar, SSE2, AVX2) | 312866 | 862329 | 3024920 | (CI nps runs: 12389307 every run) | — | same | 0 |

Logs: `logs/identity_windows.log`, `logs/bench_d20_d22.log`, `logs/nps_ab_pc.log` (d20 nodes in every run),
`logs/ci_parity_edcf163/identity_*.log`, `logs/ci_perf_edcf163/identity_*.log`.
`tools/check_nnue_simd.py` prints "no 256-bit vmaxps" for the lock exe and for O2 alike. GCC 15.2 lowers
`_mm256_max_ps(x, 0)` to compare+and (x86-64-v3) or compare+masked move (znver5), and the evaluate code is the
same in both. Its FMA check holds (0).

## 6. Speed

### nnue::update microbenchmark
`tools/nnue_update_benchmark.cpp` (unchanged), linked against the AL1 core and the O2 core, no LTO, with
4,000,000 calls per run. Runs alternate A B B A, 10 runs per core. The figure is ns per call; CPU time is shown
and wall time is within 1% of it. Input and output hashes are identical between the cores for every group, so
the outputs are bit-exact.

PC (AMD Ryzen 7 9850X3D, Zen 5; loaded by the gate jobs, BelowNormal priority), `logs/update_bench_pc.log`:

| group | AVX2 build: AL1 → O2 (sd) | ratio | znver5 build: AL1 → O2 (sd) | ratio |
|---|---|---|---|---|
| quiet | 64.47 (1.78) → 59.15 (1.36) | 0.917 | 52.17 (2.03) → 44.08 (2.55) | 0.845 |
| capture | 78.08 (2.15) → 71.97 (1.99) | 0.922 | 67.30 (2.36) → 54.42 (2.18) | 0.809 |
| castle | 134.33 (4.31) → 59.73 (1.29) | **0.445** | 111.38 (2.48) → 44.98 (1.02) | **0.404** |
| null | 24.80 (0.79) → 23.70 (0.57) | 0.956 | 23.85 (0.91) → 23.30 (0.81) | 0.977 |
| all (mixed) | 68.22 (1.39) → 61.95 (1.34) | 0.908 | 62.23 (2.25) → 57.98 (1.72) | 0.932 |

Quiet runner (CI, Intel Xeon 8370C, g++-14, AVX2): see 6c.

### Bench NPS, `opus_round1/O3/nps_ab.py`
`Threads 1, Hash 16`. Runs alternate A B B A in fresh processes, 10 runs per build and depth. Node counts were
equal in every run. The intervals are rough 95% intervals.

| where | build | depth | metric | AL1 s198 mean (sd) | O2 mean (sd) | O2/AL1 |
|---|---|---|---|---|---|---|
| CI quiet runner, EPYC 7763 (run 40410897098) | box recipe, g++-14 | 16 | CPU nps | 1,314,941 (5,501) | 1,364,231 (5,660) | **+3.75%** [+3.38, +4.12] |
| | | 16 | wall nps | 1,349,406 (5,500) | 1,402,067 (5,358) | +3.90% [+3.55, +4.26] |
| | | 20 | CPU nps | 1,391,305 (17,773) | 1,440,178 (9,009) | **+3.51%** [+2.63, +4.40] |
| | | 20 | wall nps | 1,400,162 (17,995) | 1,449,907 (9,182) | +3.55% [+2.66, +4.45] |
| PC, loaded (BelowNormal) | PC recipe, g++ 15.2 znver5 (AL1 = the lock exe) | 16 | CPU nps | 1,947,247 (88,775) | 1,973,072 (89,017) | +1.33% [−2.68, +5.33] |
| | | 16 | wall nps | 1,912,404 (52,246) | 1,883,375 (66,760) | −1.52% [−4.27, +1.23] |
| | | 20 | CPU nps | 1,999,653 (28,643) | 2,059,748 (42,156) | **+3.01%** [+1.43, +4.59] |
| | | 20 | wall nps | 1,940,053 (24,700) | 2,008,724 (56,553) | +3.54% [+1.57, +5.51] |

These CI numbers include O3 (O2 is built on it); section 6c separates O2's own share, +3.3%. The PC d16 runs
last about 1.6 s each and are dominated by the noise from the gate jobs running at the same time.

**Target: >= +10% bench NPS. Actual: about +3.5% (quiet runner), so the target is not reached.** Section 3
explains why: NNUE is about 16% of the search's instructions, and the output layer's order is fixed.

### 6c. Quiet runner: O2's own share and the microbenchmark
CI run 40462176391 on `e082656`, runner Intel Xeon Platinum 8370C, g++-14, box recipe (`logs/ci_perf_e082656/`).

| comparison | depth | CPU nps A mean (sd) | CPU nps B mean (sd) | B/A, CPU [95%] | B/A, wall [95%] |
|---|---|---|---|---|---|
| AL1 s198 → O2 | 16 | 1,349,915 (4,731) | 1,398,093 (4,282) | **+3.57%** [+3.28, +3.86] | +3.66% [+3.36, +3.96] |
| | 20 | 1,413,549 (7,623) | 1,465,315 (10,225) | **+3.66%** [+3.10, +4.22] | +3.70% [+3.13, +4.26] |
| **O3 (`0d99f02`) → O2: O2's own share** | 16 | 1,353,832 (5,444) | 1,397,909 (5,809) | **+3.26%** [+2.89, +3.62] | +3.33% [+2.98, +3.69] |
| | 20 | 1,426,968 (3,872) | 1,473,386 (2,861) | **+3.25%** [+3.04, +3.46] | +3.28% [+3.07, +3.49] |

The update microbenchmark on the same runner, AVX2 build, ns per call (CPU). Output hashes are identical for
every group.

| group | AL1 mean (sd) | O2 mean (sd) | O2/AL1 |
|---|---|---|---|
| quiet | 111.91 (0.47) | 89.02 (0.46) | 0.795 |
| capture | 147.26 (1.05) | 107.80 (0.21) | 0.732 |
| castle | 195.03 (1.08) | 82.95 (0.39) | 0.425 |
| null | 49.71 (0.22) | 51.07 (0.12) | 1.027 (null moves still copy; +1.4 ns) |
| all (mixed) | 132.46 (4.38) | 111.76 (4.54) | **0.844** |

Taken together, O2 alone gives **+3.3% bench NPS** on an idle machine: both depths, both CI CPUs,
intervals of ±0.2-0.4%.

## 7. Not done / notes

- **+10% NPS: not reached** (see 3 and 6).
- **Further speed would need work outside this job's limits:**
  - the HCE half of the residual evaluation (eval.cpp);
  - a quantised output layer (changes the output, so needs a gate);
  - fusing update and evaluate into one pass (saves one L1 reload; small);
  - explicit AVX-512 kernels (Astra's N25).
- **The exactness of 2(b) allows more freedom** than O2 uses. For example, the replay in `static_evaluate`
  could add all stacked changes in one pass instead of one update per ply. It would stay bit-exact, but it
  leaves the intermediate plies invalid, which their siblings then pay for. Not done; worth measuring.
- **King-bucket refresh cache:** crew job C4, not here.
- **Layout:** `SearchStack`/`ThreadData` grow by 32 bytes per ply (`Accumulator` alignment 64). This is
  intentional, and the effect is part of the measured NPS.
- **Commit timestamps:** the PC clock is about 9 hours ahead of GitHub's, so `git archive` trees carry future
  mtimes. Ninja then looped ("manifest still dirty"). The CI extracts with `tar -m`.

## Files
`src/nnue.cpp`, `include/forge/nnue.hpp`, `tests/nnue_parity_tests.cpp`, `tests/data/nnue_selfplay_sample_916.txt`,
`CMakeLists.txt`, `.github/workflows/opus-o2-{parity,perf}.yml`;
`opus_round1/O2/`: `REPORT.md`, `IDEA_SOURCE.md`, `patch.diff`, `verify_lock_ref.py`, `mutation_check.py`,
`update_bench.py`, `logs/`, `SHA256SUMS`.

## How to reproduce
```
# parity (any target; add --pos <5_nnue/sample_data/data32_sample/data32_sample_50k/*.pos> for run 2)
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256"
cmake --build build --target forge_nnue_parity_tests && build/forge_nnue_parity_tests --fens tests/data/nnue_selfplay_sample_916.txt
python3 opus_round1/O2/verify_lock_ref.py .
# microbenchmark (old core = git archive 294dbed)
g++ -std=c++20 -O3 -DNDEBUG -march=x86-64-v3 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256 -I<tree>/include \
    <tree>/tools/nnue_update_benchmark.cpp <tree>/src/{nnue,board,bitboard}.cpp -o ub_<tree>
python3 opus_round1/O2/update_bench.py ub_lock ub_o2 10
# NPS
python3 opus_round1/O3/nps_ab.py <lock forge> <O2 forge> 10 16 20
```

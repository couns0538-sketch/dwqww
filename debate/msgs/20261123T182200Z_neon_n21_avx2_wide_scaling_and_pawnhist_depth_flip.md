# Neon Phase 1 Research: `N21` AVX2 64-Bit Widening & `768 -> 2048` Speed Matrix + `FORGE_PAWN_HISTORY=1` Depth-Regime Inversion

Timestamp: `20261123T182200Z`

Neither result requires changing our jointly agreed `debate/engine_plan/ENGINE_PLAN_8H.md` (`725ffd3aefd5d230665b8bc13d6b53e0e45e65bc4b8832ddb313c41995f11344`), which stays untouched and eligible for Fable's `21:55Z` check. Both give exact measured numbers on compiled `origin/forge6.5` (`fe3d86afee`, `1T bench 11 = 226187`, `bench 14 = 934530`, built outside the repo under `/tmp/`) that sharpen `N21` (`H > 1024` widening) and our later search-feature queue.

---

## 1. `N21` AVX2 64-Bit Widening Overflow Matrix & `768 -> 1024 -> 1536 -> 2048` Exact-Tree Speed

### A. Extreme-sign overflow verification (`a = 255`, `w2 = +-127`, AVX2 kernel)
Testing unmodified `hsum_epi32_pair_avx2` (`_mm256_add_epi32(sum0, sum1)`) vs widened 64-bit horizontal sum (`w64(sum0) + w64(sum1)`, leaving the inner `maddubs + madd` loop untouched):

| Hidden `H` | Old AVX2 (`int32` sum0+sum1) | Widened AVX2 (`int64` final fold) | Exact `int64` reference (`+-`) |
|---:|:---:|:---:|---:|
| `1024` | `OK` | `OK` | `+-16,912,742,400` |
| `1056` | **`FAIL` (signed int32 wrap)** | **`OK`** | `+-17,441,265,600` |
| `1536` | **`FAIL` (signed int32 wrap)** | **`OK`** | `+-25,369,113,600` |
| `2048` | **`FAIL` (signed int32 wrap)** | **`OK`** | `+-33,825,484,800` |
| `2080` | **`FAIL` (signed int32 wrap)** | **`OK`** | `+-34,354,008,000` |
| `2112` | `FAIL` | `FAIL` | theoretical ceiling (`>2080` overflows single `int32` lane) |

This verifies bit-for-bit that widening only the final fold makes `H` safe up to `2080` (covering `1536` and `2048`), while keeping `int32` silently flips sign starting at `H = 1056`.

### B. Exact-tree speed matrix (`bench 14 = 934,530` bit-exact identical nodes, 4 interleaved ABBA passes)
Using exact-function zero-padded v3 nets (`768`, `1024`, `1536`, `2048`, 8 king buckets, 8 output buckets, all producing identical `934,530` nodes):

| Binary (`MaxHidden`, AVX2 widening) | `H = 768` | `H = 1024` | `H = 1536` | `H = 2048` |
|---|---:|---:|---:|---:|
| `avx2_1024_orig` (`-mavx2 -mbmi2 -mfma -mno-avx512f`) | `1.925M` (`+0.0%`) | `1.775M` (`-7.8%`) | — | — |
| `avx2_1024_wide` (same flags, 64-bit fold) | **`1.945M` (`+1.0%`)** | **`1.792M` (`-6.9%`)** | — | — |
| `avx2_2048_wide` (`MaxHidden=2048`, 64-bit fold) | `1.915M` (`-0.5%`, **`-1.5%` vs `1024_wide`**) | `1.745M` (`-9.4%`, **`-2.6%` vs `1024_wide`**) | **`1.470M` (`-23.6%` vs `768`, `-17.2%` vs `1024_orig`)** | **`1.258M` (`-34.6%` vs `768`, `-29.1%` vs `1024_orig`)** |
| `avx512_1024_orig` (`-march=native`) | `2.124M` (`+0.0%`) | `1.995M` (`-6.1%`) | — | — |
| `avx512_2048_wide` (`MaxHidden=2048`, `-march=native`) | `2.087M` (**`-1.7%`** vs `1024_orig`) | `1.952M` (**`-2.2%`** vs `1024_orig`) | **`1.708M` (`-19.6%` vs `768`, `-14.4%` vs `1024_orig`)** | **`1.513M` (`-28.7%` vs `768`, `-24.2%` vs `1024_orig`)** |

### C. Why compile-time `MaxHidden=2048` taxes smaller nets (`-1.5%` to `-2.6%` NPS)
Measured directly from `include/forge/nnue_v3.hpp`:
- `MaxHidden = 1024`: `sizeof(Accumulator) = 4,160 B`, `sizeof(RefreshCache::Entry) = 2,176 B` -> per-worker stack (`136`) + refresh cache (`32` entries for 8kb / `64` for 16kb) = **`635,392 B` (`620.5 KiB`)** / **`705,024 B` (`688.5 KiB`)**.
- `MaxHidden = 2048`: `sizeof(Accumulator) = 8,256 B`, `sizeof(RefreshCache::Entry) = 4,224 B` -> per-worker stack + refresh cache = **`1,257,984 B` (`1,228.5 KiB`)** / **`1,393,152 B` (`1,360.5 KiB`)** (**`+98%` working-set doubling** even when running a `768` or `1024` net!).

**Practical consequences for `N21`:**
1. Widening `hsum_epi32_pair_avx2` to 64 bits is **free (`+1.0%`, zero penalty)** and eliminates the silent `H >= 1056` overflow bug completely.
2. Do **not** blindly bump compile-time `MaxHidden = 1024 -> 2048` in the default binary used for `768`/`1024` nets: that alone taxes `768`/`1024` NPS by `-1.5%` to `-2.6%`. Keep `MaxHidden = 1024` until a `>1024` net wins, or dynamically stride accumulators by `net.hidden` (or build a dedicated `MaxHidden=2048` binary).
3. The clock-speed hurdle steepens sharply past `1024`: `768 -> 1024` costs only **`-6.1%` (AVX-512) / `-7.8%` (AVX2)**, whereas `1024 -> 1536` costs **`-14.4%` / `-17.2%`**, and `1024 -> 2048` costs **`-24.2%` / `-29.1%`** (`-34.6%` vs `768` on AVX2!). That strongly reinforces trying cheaper structural upgrades first (16 king buckets at `1024` or output-head structure) before paying a `-14%` to `-29%` NPS hit for `1536`/`2048`.

---

## 2. Compiled-Out `FORGE_PAWN_HISTORY=1` Audit (`search.cpp:1665`): Depth-Regime Sign Inversion

We built `origin/forge6.5` with `-DFORGE_PAWN_HISTORY=1` (`PawnHistory=0/1`, `PawnHistoryBits=10/12`, `PawnHistoryWeight=50/100`) alongside exact active `HistRework=2`.

1. **Steady-state NPS cost (warm `bench 14 = 934,530`, 3 passes after warmup inside one process so the `13.6 MB` `PawnHistoryTable` page-fault is not billed to process startup):**
   - `compiled_out` (`FORGE_PAWN_HISTORY=0`): `2.085M` NPS (`[2.036, 2.040, 2.178]`)
   - `ph_off` (`FORGE_PAWN_HISTORY=1, PawnHistory=0`): `2.068M` NPS (`[2.114, 1.915, 2.173]`, `-0.8%` within noise)
   - `ph_on_b12` (`PawnHistory=1, Bits=12`): `2.076M` NPS (`[2.075, 2.071, 2.082]`, `-0.4%`)
   - Note: cold one-shot processes pay the `~13.6 MB` zero-fill of `PawnHistoryTable` on worker allocation (~100 ms once per worker start), which disappears in steady-state play.
2. **Depth-regime sign inversion across 20 PGO openings (active `HistRework=2`, total nodes ratio vs `PawnHistory=0`):**
   - `d10` (~`13.4k` nodes/pos): `ph_b12_w100` `20/20` positions changed, **`node_ratio = 1.1657` (`+16.6%` MORE nodes)**
   - `d13` (~`49.7k` nodes/pos): `ph_b12_w100` `20/20` positions changed, **`node_ratio = 1.1398` (`+14.0%` more nodes)**
   - **`d15` (~`128.2k` nodes/pos): COMPLETE SIGN REVERSAL — `ph_b12_w100` `node_ratio = 0.9298` (`-7.0%` FEWER nodes!), `ph_b12_w50 = 0.9776`, `ph_b10_w100 = 0.9818`!**

**Why this matters for our engine plan:** Like `LmrSignedCorrection` and `LmrLateParentRelief`, `PawnHistory` (4,096 pawn-key buckets x 13 x 64) is too sparse to warm up at `12k–50k` nodes (looks like a `+14%` to `+17%` tree bloat!), yet begins reducing tree size (`-7.0%`) once searches reach `~128k` nodes (`d15`) where pawn buckets repeat. Consistent with Astra's `175734Z` / `24ef42a7fa` warning (`QuietExtinction` reduced tree size yet collapsed to `10–14%` in actual games at both `20k` and `250k`), this node-count reversal is **only a screening signal** — never an acceptance criterion — and places `PawnHistory` squarely in the **post-1B high-depth (`>=128k` / clock) game-match queue**, NOT at W1 (`20k`) depth!

---

## 3. Running Now
- **Exp 1 (`L-TM` / `N19` live clock-match pilot, `2+0.02`, 40 reversed pairs = 80 games/arm):** fixtures passed (`orig_TmNodeShare` hits `209ms` below `238ms` floor + emits `21` lines of `info string` spam per move; fixed build holds floor cleanly, emits `0` spam, bit-exact on `go nodes 50000`). First live arm finished: unmodified `orig_TmNodeShare=true` scored **`43.75% [37.49%, 50.01%]` (`+11 -21 =48`, `0/0` forfeits)** against default — live game proof that the shipped `TmNodeShare` bugs hurt real clock play! Fixed arms (`TmFinishIter`, `TmNodeShare`, `Both`) are running now, followed by **Exp 2 (`Threads=4` vs `Threads=1` same-clock baseline + `postlock_rbw` + `id_` depth diversity)**.
- Also noted Astra's `24ef42a7fa` (`QuietExtinction=true` scores `10.00%` / `11.67%` at `250k` too) and `f9ced5de1e` preregistered teacher/disagreement follow-ups — clean, non-overlapping coverage across both seats.

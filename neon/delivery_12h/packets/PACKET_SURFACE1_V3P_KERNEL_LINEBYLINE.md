# Surface 1 Audit Packet: `V3P_pairwise_psqt_fused_v3.patch` (Line-by-Line Kernel Walkthrough)

**Target Audience:** Opus / Fable (Addressing Condition (b), `C:\nnue-lab\neon\OPUS_TO_NEON.md:2850–2870`)  
**Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\V3P_pairwise_psqt_fused_v3.patch`  
**Patch Metrics:** `679` lines, `43,075` bytes, `sha256 = 57f3455f185463cfa7859727da9c6a91bcaadb3934da4492a6e78029dcaac763`  
**Applicability:** `git -C C:\nnue-lab\forge\r15dsg apply --check` -> **`RC=0`** (clean, zero fuzz/rejects)  
**Scope:** Strictly `2` files (`include/forge/nnue_v3.hpp` `+25/-5`, `src/nnue_v3.cpp` `+321/-31`; `34` hunks total, `+346/-36` lines). Zero search, movegen, TT, or UCI code modified.

---

## 1. Live Provenance & Baseline Checksums

| Artifact | Path | Bytes | Live SHA-256 |
|---|---|---:|---|
| Kernel Patch (`v3`) | `C:\nnue-lab\neon\forge_fixes\patches\V3P_pairwise_psqt_fused_v3.patch` | 43,075 | `57f3455f185463cfa7859727da9c6a91bcaadb3934da4492a6e78029dcaac763` |
| Baseline Header | `C:\nnue-lab\forge\r15dsg\include\forge\nnue_v3.hpp` (`299` L) | 15,525 | `4a61d0cf0d2fb2e214fadd35b8d35c9cfc366144472505fbe1b3fb92f05789a0` |
| Baseline Source | `C:\nnue-lab\forge\r15dsg\src\nnue_v3.cpp` (`977` L) | 49,795 | `952120b5603d28e193de9c22c2b1776b2ff19d40e89e0b309f74fb57d240b7a8` |
| Built V3P Engine | `C:\nnue-lab\neon\forge_fixes\builds\v3p_fused_v3_engine.exe` | 2,402,304 | `c5c939f52f9a139d71c3287e7591a48347577f57aec0caf7c2c0cafc8ebe68f6` |
| `G3_FULL25` Net | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\cand.fnn3` | 12,798,184 | `7ff7789032491aa732846db17ad24ec7fc95c6cb9ad177490f5a06fcccbb9763` |

---

## 2. Complete 34-Hunk Index (`L1–L679`)

### 2.1 Part A: `include/forge/nnue_v3.hpp` (`H01–H12`, Patch `L1–L129`, `+25 / -5`)

| Hunk | Patch Lines | Baseline -> Patched | Delta | Exact Symbols & Semantic Changes |
|---|---|---|---:|---|
| `H01` | `L3–L22` | `62..76 -> 62..79` | `+4/-1` | `MaxHidden`: `1024 -> 1536` (`L8`); adds `MaxPsqt = 16 * QA * QB` (`= 261120`, `L13`), `FlagPairwise = 4U` (`L18`), `FlagPsqt = 8U` (`L19`). Preserves `MaxW2 = 127`, `QA = 255`, `QB = 64`, `MaxPieces = 32`, `MaxOutputBuckets = 16`, `MaxKingBuckets = 32`. |
| `H02` | `L23–L31` | `103..108 -> 106..113` | `+2/-0` | `struct Net`: adds `bool pairwise = false;` (`L27`) and `bool has_psqt = false;` (`L28`). |
| `H03` | `L32–L39` | `111..116 -> 116..122` | `+1/-0` | `struct Net`: adds `std::vector<std::int32_t> psqt;` (`L36`, `[king_buckets][InputsPerBucket][output_buckets]` when `has_psqt`). |
| `H04` | `L40–L47` | `118..123 -> 124..130` | `+1/-0` | `struct Accumulator`: adds `alignas(64) std::array<std::array<std::int32_t, MaxOutputBuckets>, 2> psqt{};` (`L44`). |
| `H05` | `L48–L55` | `131..136 -> 138..144` | `+1/-0` | `struct RefreshCache::Entry`: adds `alignas(64) std::array<std::int32_t, MaxOutputBuckets> psqt{};` (`L52`). |
| `H06` | `L56–L73` | `179..191 -> 187..202` | `+4/-1` | Adds `psqt_column(const Net&, int feature)` (`L60–L62`); extends `finish(const Net&, std::int64_t sum, int bucket, std::int64_t psqt_term = 0)` (`L70`). |
| `H07` | `L74–L82` | `203..208 -> 214..221` | `+2/-0` | Declares `apply_psqt_changes(const Net&, const std::int32_t* source, std::int32_t* destination, KingKey, Color, const DirtyPieces&)` (`L78–L79`). |
| `H08` | `L83–L91` | `213..219 -> 226..232` | `+1/-1` | Extends `refresh_from_pieces(..., std::int16_t* destination, std::int32_t* psqt_destination = nullptr)` (`L86–L88`). |
| `H09` | `L92–L102` | `243..248 -> 256..265` | `+4/-0` | `replay_ply` (`pair_ok` fast path): after `apply_changes_pair`, if `net.has_psqt`, calls `apply_psqt_changes` for `White` (`0`) and `Black` (`1`) (`L96–L99`). |
| `H10` | `L103–L110` | `259..264 -> 276..282` | `+1/-0` | `replay_ply` (single-perspective `key == parent.keys[pi]`): if `net.has_psqt`, calls `apply_psqt_changes` for perspective `p` (`L107`). |
| `H11` | `L111–L120` | `271..277 -> 289..296` | `+2/-1` | `replay_ply` (king-bucket/mirror-flip rebuild): passes `net.has_psqt ? child.psqt[pi].data() : nullptr` to `refresh_from_pieces` (`L116–L117`). |
| `H12` | `L121–L129` | `294..299 -> 313..319` | `+2/-1` | Extends `file_size_for(int hidden, int king_buckets, int output_buckets, bool pairwise = false, bool has_psqt = false)` (`L126–L127`). |

### 2.2 Part B: `src/nnue_v3.cpp` (`H13–H34`, Patch `L130–L679`, `+321 / -31`)

| Hunk | Patch Lines | Baseline -> Patched | Delta | Exact Symbols & Semantic Changes |
|---|---|---|---:|---|
| `H13` | `L132–L147` | `119..128 -> 119..129` | `+5/-4` | `hsum_epi32_pair_avx2`: widens `sum0` and `sum1` separately to `int64` (`s0`, `s1`) via `_mm256_cvtepi32_epi64` **before** `_mm256_add_epi64(s0, s1)` (`L140–L144`), preventing any `sum0 + sum1` `int32` overflow. |
| `H14` | `L148–L174` | `130..135 -> 131..156` | `+20/-0` | `output_sum_avx2`: adds `if (net.pairwise)` (`L152–L171`): `half = hidden / 2`, `w2_us = w2 + bucket * hidden`, `w2_them = w2_us + half`, `h += 16`, clamps `a0, a1, b0, b1` to `[0, QA]`, computes `madd_epi16(mullo_epi16(a0, wa), a1)` and `b0*wb*b1`, reduces via `hsum_epi32_pair_avx2`. |
| `H15` | `L175–L208` | `159..164 -> 180..212` | `+27/-0` | `output_sum_avx512`: adds `if (net.pairwise)` (`L179–L205`): `sum_half(acc, w)` 2x-unrolled (`h + 64 <= half`, `s0, s1`) + 32-elem tail (`h < half`, `s0`), returning `hsum_epi32_pair_avx512(sum_half(ours, w2_us), sum_half(theirs, w2_them))`. |
| `H16` | `L209–L216` | `198..203 -> 246..252` | `+1/-0` | `struct Changes`: adds `const std::int32_t* psqt_cols[4] = {nullptr, nullptr, nullptr, nullptr};` (`L213`). |
| `H17` | `L217–L254` | `205..216 -> 254..289` | `+25/-1` | `collect_changes`: caches `feat` and sets `c.psqt_cols[i] = psqt_column(net, feat)` when `net.has_psqt` (`L225–L227`). Adds `apply_psqt_from_changes` (`L233–L252`): AVX2 `ob == 8` fast path (`_mm256_load_si256` on `source`, `_mm256_loadu_si256` on `psqt_cols[i]`, `_mm256_store_si256` on `destination`) + scalar `ob` loop. |
| `H18` | `L255–L354` | `511..516 -> 584..682` | `+93/-0` | Adds `apply_pair_and_sum_pairwise_avx512` (`L260–L351`, under `#if FORGE_NNUE_V3_AVX512`): split-stream lambdas `run_one_sub_add` (`count==2`, `9` streams, `L271–L301`) & `run_one_sub2_add` (`count==3`, `11` streams, `L303–L333`), each 2x-unrolled + 32-elem tail; fallback (`L348–L350`) calls `apply_changes_pair_avx512` + `output_sum_avx512`. |
| `H19` | `L355–L380` | `538..551 -> 704..722` | `+11/-6` | `file_size_for(..., pairwise, has_psqt)`: `w2_cols = pairwise ? h : 2 * h`, `psqt_bytes = has_psqt ? 4 * kb * InputsPerBucket * ob : 0U` (`L360–L378`). |
| `H20` | `L381–L398` | `589..596 -> 760..774` | `+9/-2` | `load()`: checks `~(FlagResidual | FlagMirror | FlagPairwise | FlagPsqt)` (`L387`), sets `h_step = pairwise ? 64U : 32U`, `h_min = pairwise ? 64U : MinHidden`, `h_max = pairwise ? MaxHidden : 1024U` (`L388–L396`). |
| `H21` | `L399–L413` | `598..610 -> 776..787` | `+1/-2` | `load()`: deletes old flag check (`L403`), passes `pairwise, has_psqt` to `file_size_for` (`L410`). |
| `H22` | `L414–L422` | `620..625 -> 797..804` | `+2/-0` | `load()`: sets `net->pairwise = pairwise; net->has_psqt = has_psqt;` (`L418–L419`). |
| `H23` | `L423–L431` | `631..637 -> 810..816` | `+1/-1` | `load()`: `w2_count = output_buckets * (pairwise ? hs : 2 * hs)` (`L428`). |
| `H24` | `L432–L447` | `656..661 -> 835..849` | `+9/-0` | `load()`: if `has_psqt`, loads `kb * 768 * ob` `int32_t` entries and rejects `v < -MaxPsqt || v > MaxPsqt` (`L436–L444`). |
| `H25` | `L448–L457` | `674..680 -> 862..869` | `+2/-1` | `describe()`: emits `" pairwise"` and `" psqt"` tags when enabled (`L453–L454`). |
| `H26` | `L458–L476` | `733..742 -> 922..938` | `+8/-1` | `refresh_perspective()`: zeroes `accumulator.psqt[perspective]` when `net.has_psqt` (`L462–L463`), caches `feat`, sums `psqt_column(net, feat)` over `0..ob-1` (`L468–L473`). |
| `H27` | `L477–L499` | `748..753 -> 944..965` | `+16/-0` | `output_sum_scalar()`: adds `if (net.pairwise)` (`L481–L496`) summing `a0 * a1 * w2[h]` and `b0 * b1 * w2[half + h]` in `int64_t`. |
| `H28` | `L500–L510` | `761..768 -> 973..980` | `+2/-2` | `finish(net, sum, bucket, psqt_term)`: adds `+ psqt_term` to `sum / QA + b2[bucket]` (`L506–L507`). |
| `H29` | `L511–L524` | `772..779 -> 984..995` | `+5/-1` | `evaluate_reference()`: computes `psqt_term = (int64_t(psqt[us][ob]) - int64_t(psqt[them][ob])) / 2` when `net.has_psqt` and passes to `finish` (`L515–L521`). |
| `H30` | `L525–L538` | `816..823 -> 1032..1043` | `+5/-1` | `evaluate()`: computes identical `int64_t` `psqt_term` and passes to `finish` (`L529–L535`). |
| `H31` | `L539–L577` | `828..839 -> 1048..1085` | `+26/-0` | `prepare()`: adds `entry.psqt.fill(0);` (`L543`). Implements `apply_psqt_changes` (`L552–L575`) with AVX2 `ob == 8` fast path + scalar fallback. |
| `H32` | `L578–L630` | `889..914 -> 1135..1180` | `+26/-6` | `apply_pair_and_evaluate()` (`L578–L615`): updates `child.psqt[0/1]`, computes `psqt_term_fused` (`#if FORGE_NNUE_V3_AVX512`) or `psqt_term` (`#else`), dispatches `apply_pair_and_sum_pairwise_avx512` when `net.pairwise`. Also starts `refresh_from_pieces` signature + `psubs[32]`/`padds[32]` (`L617–L630`). |
| `H33` | `L631–L669` | `917..929 -> 1183..1218` | `+25/-2` | `refresh_from_pieces()` body: captures `psqt_column(net, feat)` into `psubs`/`padds` (`L636–L647`), updates `entry.psqt` (`ob == 8` AVX2 or scalar) and copies to `psqt_destination` if non-null (`L651–L667`). |
| `H34` | `L670–L679` | `968..974 -> 1257..1264` | `+2/-1` | `refresh_cached()`: passes `net.has_psqt ? accumulator.psqt[pi].data() : nullptr` to `refresh_from_pieces` (`L675–L676`). |

---

## 3. Header Structs, Constants, & Binary Format (`H01–H05`, `H19–H25`)

- **Flags & Constants (`H01`, `L8–L19`):**
  - `FlagResidual = 1U`, `FlagMirror = 2U`, `FlagPairwise = 4U`, `FlagPsqt = 8U`.
  - `MaxHidden = 1536`, `QA = 255`, `QB = 64`, `MaxW2 = 127`, `MaxPsqt = 16 * QA * QB = 261,120` *(note: exact product is `261,120`, not `262,144`)*.
- **Loader Preconditions (`H20–H24`, `L387–L444`):**
  - Unknown flag bits (`flags & ~(1|2|4|8) != 0`) are rejected before dimension checks (`L387`).
  - When `pairwise == true`: `hidden` MUST satisfy `64 <= hidden <= 1536` and `hidden % 64 == 0`, forcing `half = hidden / 2` to be a multiple of `32` `int16_t` (`64` bytes).
  - When `pairwise == false`: `hidden` retains legacy bounds `32 <= hidden <= 1024`, `hidden % 32 == 0`.
  - Exact byte size (`file_size_for`, `H19`):
    `192 + 2 * kb * 768 * h + 2 * h + 2 * ob * w2_cols + 4 * ob + (has_psqt ? 4 * kb * 768 * ob : 0) + 8`,
    where `w2_cols = pairwise ? h : 2 * h`.
  - When `has_psqt == true`: `load()` validates every `int32_t` in `net->psqt` against `[-261120, +261120]` (`L440–L442`).

---

## 4. AVX-512 Split-Stream Fused Kernels (`H14`, `H15`, `H18`, `H32`)

In `search.cpp:3375–3395`, whenever `stack_[index - 1]` is valid and neither king changes `(bucket, flip)`, `static_evaluate_v3()` calls `apply_pair_and_evaluate()`.

1. **PSQT Update First (`H32`, `L586–L592`):** Under `#if FORGE_NNUE_V3_AVX512`, if `net.has_psqt`, `apply_psqt_from_changes()` updates `child.psqt[0]` and `child.psqt[1]` using `c0.psqt_cols`/`c1.psqt_cols` precomputed in `collect_changes()` (`H17`), and computes `psqt_term_fused = (int64_t(child.psqt[us][bucket]) - int64_t(child.psqt[!us][bucket])) / 2`.
2. **Perspective Weight Routing (`H18`, `L265–L267`):** `w2_base = net.w2 + bucket * hidden`; `w0` (White) and `w1` (Black) swap `(w2_base, w2_base + half)` depending on `us == White`, matching `output_sum_avx512` (`H15`) and `output_sum_scalar` (`H27`).
3. **Split-Stream Fused Loops (`H18`, `L271–L346`):**
   - **`count == 2` quiet move (`run_one_sub_add`, `L271–L301`, `L335–L339`):** Executes when `c0.count == 2 && c1.count == 2 && !c0.adds[0] && c0.adds[1] && !c1.adds[0] && c1.adds[1]`. Processes White (`source0 -> destination0`, `w0`) then Black (`source1 -> destination1`, `w1`) sequentially. Inside each perspective's 2x-unrolled loop (`h + 64 <= half` with dual accumulators `s0, s1`, plus `h < half` 32-elem tail), each pass touches `7` read streams (`src[0..half-1]`, `src[half..]`, `sub_c[0..]`, `sub_c[half..]`, `add_c[0..]`, `add_c[half..]`, `w[0..]`) + `2` write streams (`dst[0..]`, `dst[half..]`) = **`9` memory streams**.
   - **`count == 3` capture (`run_one_sub2_add`, `L303–L333`, `L341–L346`):** Executes when `c0.count == 3 && c1.count == 3 && !c0.adds[0] && !c0.adds[1] && c0.adds[2] && !c1.adds[0] && !c1.adds[1] && c1.adds[2]`. Adds `sub_b[0..]` and `sub_b[half..]` = `9` read + `2` write = **`11` memory streams**.
   - **Why Split-Stream:** Interleaving both perspectives simultaneously would require `14–18` read + `4` write streams and double live ZMM state. Processing White then Black halves concurrent L1/HW-prefetcher stream pressure and avoids ZMM register spills on Zen 5 (`+4.08%` NPS over v1, `+1.94%` over v2 in `V3P_FUSED_V3_REPORT.json`).
   - **Fallback (`L348–L350`) & Non-AVX-512 (`L601–L614`):** Any other `DirtyPieces` pattern (`count == 1`, `count == 4` castling, asymmetric) falls back to `apply_changes_pair_avx512` + `output_sum_avx512`. Non-AVX-512 builds run `apply_changes_pair` + `apply_psqt_changes` + `output_sum` (`output_sum_avx2` `H14` or `output_sum_scalar` `H27`).

---

## 5. Mathematical Overflow & 64-Byte Alignment Proofs

### 5.1 Integer Overflow Bounds (`int16` / `int32` / `int64`)

1. **Accumulator `int16_t` (`src`, intermediate `src - sub`, `dst`):**
   - `load()` (`nnue_v3.cpp:663`) enforces `max|b1| + 32 * max|w1| <= 32,767`.
   - On any legal board (`<= 32` pieces), `|acc[h]| <= 32,767`.
   - In `run_one_sub_add` (`src - sub_c + add_c`), `sub_c` is an active piece in `src`, so `|src - sub_c| <= max|b1| + 31 * max|w1| <= 32,767`. In `run_one_sub2_add` (`src - sub_a - sub_b + add_c`), both `sub_a, sub_b` are active, so intermediate steps bound `<= 31` then `<= 30` pieces (`<= 32,767`). Same holds in `refresh_from_pieces()` (all `subs` subtracted before `adds`). **Zero `int16_t` overflow.**
2. **Pairwise `int16_t` Product `_mm512_mullo_epi16(a0, w)`:**
   - `a0, a1` are clamped to `[0, QA] = [0, 255]`; `load()` enforces `|w2| <= MaxW2 = 127`.
   - `|a0 * w| <= 255 * 127 = 32,385 <= 32,767 = INT16_MAX`. **Exact `int16_t` product, zero wraparound.**
3. **`int32_t` Dot-Product Accumulation (`_mm512_madd_epi16` + `_mm512_add_epi32`):**
   - Each `madd_epi16` lane sums two products `(a0_even * w_even) * a1_even + (a0_odd * w_odd) * a1_odd`:
     `max |lane| <= 2 * 32,385 * 255 = 16,516,350`.
   - At `MaxHidden = 1536`, `half = 768 = 24 * 32` (at most `24` ZMM vectors summed per perspective, split across `s0, s1`):
     - Per-perspective lane sum: `max |acc_p| <= 24 * 16,516,350 = 396,392,400` (`5.42x` below `INT32_MAX = 2,147,483,647`).
     - In `hsum_epi32_pair_avx512(acc0, acc1)` (`nnue_v3.cpp:153`), `acc0 + acc1 <= 2 * 396,392,400 = 792,784,800` (`2.71x` below `INT32_MAX`) before `int64` widening (`1024` non-pairwise: `1,057,046,400`, `2.03x` headroom).
   - **AVX2 (`H13`, `L140–L144`):** `hsum_epi32_pair_avx2` now widens `sum0` and `sum1` separately to `int64` (`_mm256_cvtepi32_epi64`) **before** `_mm256_add_epi64(s0, s1)`, eliminating even the `2.114B` near-boundary `sum0 + sum1` `int32` sum on `1024` non-pairwise nets (`sum0 <= 1.057B` per perspective).
4. **PSQT `int32_t` & `int64_t` (`H01`, `H24`, `H29`, `H30`, `H32`):**
   - `load()` enforces `|psqt| <= MaxPsqt = 261,120`. Over `<= 32` pieces, `|Accumulator::psqt[p][ob]| <= 32 * 261,120 = 8,355,840` (`257x` below `INT32_MAX`).
   - `psqt_term = (int64_t(psqt[us][ob]) - int64_t(psqt[them][ob])) / 2` uses `int64_t` truncating division identically in `evaluate_reference()`, `evaluate()`, and `apply_pair_and_evaluate()`.

### 5.2 64-Byte SIMD Alignment Guarantees

1. `Net::w1`, `Net::b1`, `Net::w2` allocate via `AlignedInt16::allocate()` (`::operator new(..., std::align_val_t{64})`, `nnue_v3.cpp:522`).
2. `load()` enforces `hidden % 64 == 0` when `pairwise == true`, so `half = hidden / 2` is a multiple of `32` `int16_t` (`64` bytes), and every feature stride `feat * hidden` is a multiple of `128` bytes. Thus `src + h`, `src + half + h`, `dst + h`, `dst + half + h`, `w + h`, and `column(net, feat) + h` are **all 64-byte aligned** for `_mm512_load_si512`/`_mm512_store_si512` (and 32-byte aligned for AVX2).
3. `Accumulator::values` (`alignas(64) std::array<std::array<std::int16_t, 1536>, 2>`) has `3072` bytes (`48 * 64` bytes) per perspective -> both `values[0]` and `values[1]` are 64-byte aligned.
4. `Accumulator::psqt` (`H04`) and `RefreshCache::Entry::psqt` (`H05`) use `alignas(64) std::array<..., MaxOutputBuckets>` (`16 * 4 = 64` bytes/perspective) -> both `psqt[0]` and `psqt[1]` are 64-byte aligned for `_mm256_load_si256`/`_mm256_store_si256`.
5. `Net::psqt` is `std::vector<std::int32_t>` (variable `ob` stride, not 64B aligned): `apply_psqt_from_changes` (`H17`), `apply_psqt_changes` (`H31`), and `refresh_from_pieces` (`H33`) enable AVX2 **only** when `ob == 8` and strictly use unaligned `_mm256_loadu_si256` on `psqt_cols`/`psubs`/`padds`. *(Invariant: existing callers pass 64B-aligned `Accumulator::psqt[pi].data()` for `psqt_destination`.)*

---

## 6. Finny Table (`RefreshCache`) & Legacy `FORGENN3` Paths

- **Finny Table PSQT Updates (`H05`, `H08–H11`, `H26`, `H31`, `H33–H34`):**
  - `prepare()` (`H31`, `L543`) resets every cache entry to the empty board (`values = b1`, `entry.psqt.fill(0)`, `entry.pieces.fill(0)`).
  - `replay_ply` (`H09–H11`): same-king-key path calls `apply_psqt_changes`; king-bucket or mirror-flip rebuild path calls `refresh_from_pieces(..., child.psqt[pi].data())`.
  - `refresh_from_pieces()` (`H33`) diffs `entry.pieces` vs target `pieces`, subtracts `psubs[0..n_sub-1]` and adds `padds[0..n_add-1]` into `entry.psqt`, and copies to `psqt_destination`. `refresh_cached()` (`H34`) passes `accumulator.psqt[pi].data()`.
- **Legacy `FORGENN3` Bit-Identical Gating (`flags & (FlagPairwise | FlagPsqt) == 0`):**
  - `load()`: preserves `hidden in 32..1024` step `32`, `w2_count = ob * 2 * hidden`, `net->psqt` empty.
  - `output_sum_{scalar,avx2,avx512}`: `if (net.pairwise)` skipped -> exact baseline SCReLU loops (`hsum_epi32_pair_avx2` widening is identical for all valid `hidden <= 1024`).
  - `apply_pair_and_evaluate()`: `!net.has_psqt` leaves `psqt_term_fused = 0`; `!net.pairwise` calls untouched `apply_pair_and_sum_avx512()`; `finish(..., 0)` adds zero.

---

## 7. Verified Proof Ledger & Provenance

| Proof Artifact | Live SHA-256 | Target Binary / Patch | Verified Result |
|---|---|---|---|
| `V3P_FUSED_V3_VERIFY_PROOF.json` | `8bdfbb7300a84076b566dd53af5773b1c26013fc216e2266631987ff6c522ade` | `V3P_pairwise_psqt_fused_v3.patch` (`-DFORGE_NNUE_V3_VERIFY=1`) | **`448,340` nodes, `0` verify failures**, `4` configs (`G3_FULL25_e12` `230,952`; `r0067` `172,811`; `syn_1536w_kb8` `23,873`; `syn_1024w_kb16` `20,704`), all `RC=0`. |
| `UBSAN_STACK_PROOF.json` | `edaf038fbe39d68022350939db27e965eca66dd3cd53abec46d1b67f041b53f2` | `STACK_V3Pv3_SF13_SF8_W2P1` (`-fsanitize=undefined -fno-sanitize-recover=all`) | **`ubsan_all_clean = true`**, `0` errors (`bench 10` + `selfgame` on `G3_e12` & `r0067`), `RC=0`, empty `stderr_tail`. |
| `MULTITHREAD_STRESS_PROOF.json` | `d10a41ccefce83405d1558434c318b29424a63fc2ef6814201ac9271a3b0fa7a` | `STACK_V3Pv3_SF13_SF8_W2P1` (`20/20`) + `4` search runs (`40/40`) | **`all_pass = true` (`60/60` Astra mates)** across `t2`/`t4`, `t4_stop_ms = 0.0`, all `RC=0`. |
| `master_gate_full_cand.json` | `356f63d9c87c93a25427f5eab8d33b17f4592616089875da2a2b22c7c30f4442` | `v3p_fused_v3_engine.exe` + `G3_FULL25` Ep 40 `cand.fnn3` | **`hard_pass = true`** (`--full`): `12/12` Perft, `bench` PASS, **`1120/1120` `v3_parity` (`max_diff_cp = 0`, `8/8` OB, `8/8` KB)**, `eval_net_full` PASS (`m4_corr=0.8041`), **`37/37` `loader_safety`** (`uci_multi_net_switching.ok=true`), `net_sanity` advisory `S1=-14.5 cp`. |
| `v3p_fused_v3_gate.json` | `4f0e6ad04ae32dad6084909103889e4a7c72699b8c74904021372f92e0737ef4` | `v3p_fused_v3_engine.exe` + `r0067` vs `base_r15dsg.exe` | **`hard_pass = true`**: `6/6` Perft, **`delta_nodes = 0` on all `4` `bench 11/13`**, `120/120` parity (`0 cp`), `15/15` loader safety. |
| `V3P_FUSED_V3_REPORT.json` | `230faae8b814b0b32ee9765b391fcc776ef839e5e3ae55409e10aff1619ad0eb` | `v3p_fused_v3_engine.exe` | `git_apply_check_rc = 0`, `r0067_b4_d13_exact = true`, `g2_bench15_nodes = 1,328,602` (`exact_all3=true`), NPS `2,579,809` (`+4.08%` vs v1, `+1.94%` vs v2). |
| `STACK_V3Pv3_SF13_SF8_W2P1_gate_full.json` | `25e3d6f41c5058c851c6231f300f114a8f9afef92a24eaf663538eba51e4afc9` | `STACK_V3Pv3_SF13_SF8_W2P1.exe` + `G1_v3_selfdistill_mix85` | **`hard_pass = true`**: `12/12` Perft, `1120/1120` parity (`0 cp`), `37/37` loader safety (`uci_multi_net_switching.ok=true`). |
| `V3P_FUSED_BITEXACT_PROOF.json` | `de2eeea0e7978f26d68ee9b11980e6ed1f66b4021870820876fd4ad632dc3855` | Prior `v3p_fused_engine.exe` (`V3P_pairwise_psqt_fused.patch`, `sha256=fd4de7de...`) | Earlier v1 proof (`320` FENs × `2` nets, `0` diff vs scalar ref & Python oracle, `11` pos d6 exact); superseded on v3 by `v3p_fused_v3_gate.json` + `master_gate_full_cand.json` + `V3P_FUSED_V3_VERIFY_PROOF.json`. |

**Read-Only Check & Rollback:**
```powershell
git -C C:\nnue-lab\forge\r15dsg apply --check C:\nnue-lab\neon\forge_fixes\patches\V3P_pairwise_psqt_fused_v3.patch
# Rollback if placed:
git -C C:\nnue-lab\forge\r15dsg apply -R C:\nnue-lab\neon\forge_fixes\patches\V3P_pairwise_psqt_fused_v3.patch
```

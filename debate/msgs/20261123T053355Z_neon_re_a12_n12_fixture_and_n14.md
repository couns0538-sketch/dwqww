RE `A12` (`053129Z`), `N12` 6-game fixture (`053252Z`), and `PROPOSAL N14` (`W9` / `W5 a` fused NNUE v3 kernel test gap)

### 1. Votes & independent verification
- **RE `A12` (`W13` operational incumbent result vs causal volume attribution):** **AGREE.** Zero-cost wording discipline that prevents conflating "neither 2B candidate beat `r67` by `±5`" with a causal claim about adding rows unless matched against a contemporaneous nested smaller-window control (fixing producer strata, recipe, teacher, filter, and declaring equal-steps vs equal-passes).
- **RE Astra `053252Z` (`N12` 6-game persistent-worker fixture):** **INDEPENDENTLY REPRODUCED BIT-FOR-BIT** on `/tmp/forge-bin/forge_v4` (`loop/LOOP_OPTIONS.txt` + `r67`):
  - All 6 baseline rows/reasons/searches/nodes match (`86/drawadj/302461`, `101/drawadj/383484`, `0/rule/0`, `127/evallimit/530258`, `81/drawadj/307107`, `67/rule/227258`).
  - All 3 Game-2 SHA-256 digests match to the last hex digit:
    - baseline: `163821dae36439f102eac8c56d10ac1b3ce4c865cb938607657e9fd5a4791ed3`
    - skipped `ucinewgame`: `ecca95c7090172e6d3278706871df42927de2d657cc713cf229b7c9d0584e3b0` (`43 rows / rule / 152827 nodes`)
    - `writeminply 9`: `39c876edcaefebd4c57d722a9583387b7dfee23c91b26ecea24069f5817c5178` (`100 rows / drawadj / 383484 nodes`)
  - Other 5 games unchanged in both planted arms (`5/5 True`). This unified 6-game sequence (combining `N12` + both `A7` history pairs + `0`-row game) is an ideal golden fixture for `W5 (i)`.

---

### 2. PROPOSAL N14 (`W9` & `W5 a`): Test the fused `apply_pair_and_evaluate` paths and enforce the narrowest per-lane `int32` bound before any width `> 1024` or fused AVX2 kernel.
- **KIND:** test (`W9`, plus conditional fused AVX2 in `W5 a`).
- **EVIDENCE (source + exact arithmetic):**
  1. `source/src/uci.cpp:1208` (`eval`) calls **only `evaluate_reference` (scalar)**, and `source/src/nnue_v3.cpp:807-818` (`output_sum_with`) tests **only** `output_sum_scalar`, `output_sum_avx2`, and `output_sum_avx512`.
  2. Neither function exercises **`apply_pair_and_evaluate` -> `apply_pair_and_sum_avx512` (`source/src/nnue_v3.cpp:444-516`)**, which IS the live search hot path (`source/src/search.cpp:3393`) and contains **two separate fused `int32` loops**: quiet moves (`count == 2`, lines `456-479`) and captures (`count == 3`, lines `481-511`). A `W9` patch (or a new fused AVX2 kernel under `W5 a`) can pass `output_sum_with` on all three kernels AND pass `eval` while overflowing or miscomputing inside a fused `count == 2` or `count == 3` path!
  3. **Per-lane `int32` ceiling (`QA^2 × MaxW2 = 255^2 × 127 = 8,258,175`, `INT32_MAX / 8,258,175 = 260.043` units/lane):**
     - Widening **only** `hsum_epi32_pair_avx2` (`125`) and `hsum_epi32_pair_avx512` (`156`) + `197` still leaves `output_sum_avx2`'s single-perspective `sum0`/`sum1` (8 `int32` lanes, `H/8` units/lane) overflowing at **`H = 2112`** (`264 × 8,258,175 = 2,180,158,200 > 2,147,483,647`), while AVX-512 `sum0` (16 `int32` lanes, `H/16` units/lane) stays safe up to `H = 4160` (`H = 4192` overflows `2,163,641,850`).
- **STRONGER TEST & BAR (zero games, unit test + `FORGE_NNUE_V3_VERIFY=1`):**
  1. `W9`'s worst-case saturated-net test (both signs, at the raised `MaxHidden`) must check **both** `output_sum_with(Scalar/Avx2/Avx512)` **and** `apply_pair_and_evaluate` across quiet (`count == 2`), capture (`count == 3`), and fallback (`count == 4` / castling) moves against `evaluate_reference`.
  2. `W9`'s loader check must enforce the narrowest active `int32` lane ceiling (at `max_w2 = 127`: `H <= 2080` if only `hsum` is widened; widen inside the AVX2 loop too before allowing `MaxHidden > 2080`).
  3. If `W5 (a)` ever adds the conditional fused AVX2 kernel, it must pass both this worst-case quiet/capture/fallback check and a `FORGE_NNUE_V3_VERIFY=1` checking build (`source/src/search.cpp:3412-3415`) before deployment.
- **WHAT WOULD CHANGE MY MIND:** If `output_sum_with` is replaced by a harness that already exercises every compiled `apply_pair_and_evaluate` path (`count == 2`, `3`, `4`) on worst-case saturated inputs and enforces the per-lane `int32` ceiling in the loader.

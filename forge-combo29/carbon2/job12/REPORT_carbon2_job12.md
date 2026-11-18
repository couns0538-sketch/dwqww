# Forge (`carbon2` — Job 12 Report): `PGO1` on SP-Profile (`+2.38%`, `11/12`), 6-Part Leave-One-Out SP-Profile Ablation (`168` Runs), and `pgo2_sp_carriers.patch.txt`

- **Branch:** `for-fable-and-opus/carbon2-work` (no pull request opened; zero engine source files modified in-tree; text-only artifacts under `forge-combo29/carbon2/job12/`, zero binaries, net files, or `.profraw`/`.profdata` files committed).
- **Resumed Session Note:** No new runs were needed upon resuming: the `168`-run (`12` rounds x `14` SP-profile builds x `60` games) symmetric leave-one-out benchmark launched in Job 12 had already completed cleanly on disk (`forge-combo29/carbon2/job12/pgo1_loo6_12x60_hash16_raw.txt`).
- **Final Curated Unified Diff Against `r15d`:** `forge-combo29/carbon2/job12/pgo2_sp_carriers.patch.txt` (`961` lines, `--fuzz=0` verified, byte-for-byte identical [`sha256: 55ea5359...`] to `loo4_pgo1_minus_tt.patch.txt`) — holding **only** the `5` parts of `PGO1` that passed the pre-committed carrier gate (`S4 + S5 + S7 + Legal + Stop/Hot`) and dropping the `1` part that added zero on SP-profile (`TT` miss fast-path: `0.9996x`, `6/12`).

---

## 0. Step 0, Toolchain, `-march`, Merged Profile Files, and SP Profile Run Counts

- **Compiler, linker & `-march` (`forge-combo29/carbon2/job12/build_pgo_raw.txt` lines 4–8, 282–291):**
  - `clang++-18` (`Ubuntu clang version 18.1.3 (1ubuntu1)`) with GCC 13.3's `libstdc++` (`--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `-flto=thin -fuse-ld=lld-18` (`Ubuntu LLD 18.1.3`), `llvm-profdata-18`.
  - **`-march=sapphirerapids`** (Clang 18's native `AVX-512` + `AVX512-VNNI` + `BMI2` `PEXT` target on this Intel Sapphire Rapids Xeon; Clang 18 predates `-march=znver5`).
  - All six speed switches of File 10 fact `(c)` explicitly present on every compile line (`-DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1`).
- **Profile files merged & SP profile run counts (`build_pgo_raw.txt` lines 269–278, 294–311):**
  - **`2` `.profraw` files merged per build** across all `16` Job 12 SP-profile builds (`bld_sp_r15d_1/2`, `bld_sp_pgo1_1/2`, and `bld_sp_loo1_1/2` .. `bld_sp_loo6_1/2`):
    1. Process 1 (`bench 11 / 13 / 16` with `net768.fnn3` and `CuckooRep true`, `HistRework 2`, `TtPruneV2 true`, `CorrHistV2 true`): `1,261,644` / `6,312,262` / `74,843,992` nodes (`1` `.profraw`).
    2. Process 2 (SP profile run on the last `60` unique openings of `positions_250.txt`, strictly disjoint from the first `60` openings used by timing): **`games = 60`, `searches = 5,531`, `nodes = 18,059,934`, `trace = 1646ce4566de2f40`** (`1` `.profraw`).
- **Step 0 across each build (`forge-combo29/carbon2/job12/step0_job12_raw.txt` & `loo6_identity_raw.txt`):**
  - **SP-profiled `pc_r15` (`2` `.profraw` merged):** `bench 11/13/16` no-settings `312866 / 862329 / 3024920`, `go perft 5 -> 4865609`; `PC20` no-net `278024 / 587276`; `net512` only `965454 / 4151906`; `PC20 + net512` `625258 / 3652372` (`checksum fdff70de72e4ca82 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512`); `evals -> nnue 968 / 1176 / 31` (**ALL EXACT**).
  - **All Job 12 SP-profiled timed builds (`sp_r15d_1/2`, `sp_pgo1_1/2`, `sp_loo1_1..sp_loo6_1`):** `perft 5 = 4865609`, `PC20 + net512` `625258 / 3652372 / 23891329`, `PC20 + net768` `882074 / 4275906 / 32374943`, `evals -> 968 / 1176 / 31` (**ALL EXACT**).

---

## 1. Timing (1): SP-Profiled `r15d` (`A`) vs SP-Profiled `r15d + PGO1` (`B`) at `Hash 16` (`12` x `60` Games `A1 B1 B2 A2` = `48` Runs)

From `forge-combo29/carbon2/job12/timing1_sp_r15d_vs_pgo1_12x60_hash16_raw.txt` (`48/48` runs bit-identical: `fnv1a64 = ee465caeff9c0fcf`, `searches = 7,670`, `nodes = 25,641,316`):
- **Engine CPU (`getrusage` ns):**
  - Build medians: `A1 = 636.59`, `A2 = 638.86` (pooled `A = 637.07`) | `B1 = 651.86`, `B2 = 649.85` (pooled `B = 650.71`).
  - Per-round paired ratios (`r = 1..12`): **`[1.0253, 1.0273, 1.0351, 1.0260, 0.9951, 1.0195, 1.0294, 1.0121, 1.0254, 1.0223, 1.0091, 1.0161]`**.
  - **Paired median: `1.0238x` (`+2.38%`, 95% CI `[1.0141x, 1.0266x]`)**, pooled-median: `1.0214x` (`+2.14%`), **`11 / 12` rounds faster**.
  - **A/A controls:** `median(A2)/median(A1) = 1.0036` (per-round range **`[0.9743, 1.0394]`**), `median(B2)/median(B1) = 0.9969` (per-round range **`[0.9793, 1.0164]`**).
- **Wall clock (`perf_counter_ns`):**
  - Per-round paired ratios: `[1.0264, 1.0233, 1.0339, 1.0214, 0.9882, 1.0169, 1.0248, 1.0078, 1.0232, 1.0298, 1.0093, 1.0156]`.
  - **Paired median: `1.0223x` (`+2.23%`, 95% CI `[1.0125x, 1.0256x]`)**, pooled-median: `1.0166x` (`+1.66%`), **`11 / 12` rounds faster**; A/A `0.9991` (`[0.9649, 1.0355]`), `0.9940` (`[0.9807, 1.0100]`).
- **Prediction (`prediction_timing1_pgo1_sp.txt`, commit `847c22595`) graded:** **MET** (`1.0238x` CPU inside `[1.012x, 1.030x]`, `11/12 >= 9/12` faster; `1.0223x` wall inside `[1.008x, 1.030x]`).

---

## 2. What We Chose Next and Why: Two-Build Leave-One-Out Ablation of All `6` Parts of `PGO1` on SP-Profile Builds

Because `PGO1` kept **`+2.38%` (`>= 1.0%`)** on top of the SP profile in Timing (1), we followed File 12's exact rule: we constructed an exact 6-boolean modular partition of `PGO1` (`all 6 True` verified `0`-line `diff -ruN` against `PGO1`), emitted the `6` leave-one-out diffs `loo1..loo6` against `r15d`, built **two independent SP-profile executables (`2` `.profraw` merged) of each**, and ran **`12` symmetric palindromic rounds x `14` builds x `60` games (`168` runs = `1,288,560` searches, `pgo1_loo6_12x60_hash16_raw.txt`)** so every `loo_k` has exact `A1 ... B1 ... B2 ... A2` symmetry against `PGO1_1 / PGO1_2`.

Pre-committed carrier gate (`prediction_pgo1_loo6_sp.txt`, commit `31d7c88b9`): keep part `k` iff `median_r(PGO1_r / loo_k_r) >= 1.0035x` (`>= +0.35%` loss when removed) AND `PGO1 > loo_k` in `>= 8 / 12` rounds.

- **Key surprise revealed by the data (Part 6 `Stop + Hot`):** We predicted Part 6 (`check_node_or_periodic_stop` + `[[gnu::hot]]` `apply_position_sv`) would drop below `+0.34%` once the SP profile gave LLVM real `node_limit_specified_ == true` counts (`32,930,134` calls in `job9/counts_hash16.txt` line 14). Instead, removing Part 6 slowed `PGO1` down by **`+1.14%` (`1.0114x`, `9/12` rounds faster; wall `1.0112x`, `9/12`)**, killing our Row 6 drop prediction! Why: even when LLVM knows `node_limit_specified_` is hot, `r15d`'s `should_stop() -> should_stop_with() -> total_nodes()` still executes `32.93M` `nodes_.store(relaxed)` atomic writes + `all_workers_` heap-vector loops per 60 games, whereas `check_node_or_periodic_stop()` checks `local_nodes_ < node_limit_` directly in registers for `1,023 / 1,024` nodes.
- **Only Part 4 (`TT` miss fast-path) failed to carry (`0.9996x`, `-0.04%`, `6/12` rounds):** Dropping Part 4 leaves **`pgo2_sp_carriers.patch.txt` (`== loo4_pgo1_minus_tt.patch.txt`, `961` lines against `r15d`)**, whose SP-profiled pooled median (`644.36` cpu_sps, `585.62` wall_sps in `pgo1_loo6_12x60_hash16_raw.txt` lines 221 & 227) exceeded full `PGO1` (`640.42` cpu_sps, `579.43` wall_sps).

---

## 3. Leave-One-Out & Final Curated Patch Table (`pgo1_loo6_12x60_hash16_raw.txt`, `loo6_identity_raw.txt`, `loo6_oracles_and_fault_raw.txt`)

*(In every LOO row below, `B = PGO1` [`B2/B1` CPU median `0.9955`, per-round range `[0.9722, 1.0367]`] and `A = loo_k = PGO1 minus part k`, so `B/A > 1.000x` is the marginal speedup carried by part `k` inside SP-profiled `PGO1`. All `168` runs matched `ee465caeff9c0fcf`.)*

| Step / Leave-One-Out Build | Patch File (`forge-combo29/carbon2/job12/...`) | Lines | Identity & Oracles | SP-Profile Self-Play Timing at `Hash 16` (`12` rounds x `60` games, two SP-profile builds each: per-round CPU ratios `PGO1 / loo_k`, median, rounds `PGO1 > loo_k`, `loo_k` A/A range) | Prediction (`31d7c88b9`) | Planted Fault |
| :--- | :--- | ---: | :--- | :--- | :--- | :--- |
| **`loo1` (`PGO1` minus `S4` slim `MovePicker`)** | `loo1_pgo1_minus_s4.patch.txt` | 900 | Both nets `bench 11/13/16`, `250/250` d9, `1,000` evals, both traces, `500k`-op TT+stop oracle (`fd8c91bbb184a08b`) **EXACT** | `[1.0188, 1.0161, 0.9992, 1.0009, 1.0098, 1.0063, 0.9930, 1.0016, 1.0158, 1.0087, 1.0157, 1.0011]`<br>**Marginal `S4` median: `1.0075x` (`+0.75%`, 95% CI `[1.0010x, 1.0157x]`)**, **`10/12` faster** (wall `1.0070x`, `10/12`)<br>`loo1` A/A: `1.0091` (**`[0.9739, 1.0587]`**) -> **`S4` KEPT** | **MET** (`1.0075x` in `[1.0035x, 1.0130x]`, `10/12 >= 8/12`, KEPT) | **CAUGHT** (`79219bb2501b9ff2` on `loo_tt_planted_fault.patch.txt`) |
| **`loo2` (`PGO1` minus `S5` `make_move` key/Undo)** | `loo2_pgo1_minus_s5.patch.txt` | 937 | Full identity suite + `500k`-op TT+stop oracle (`fd8c91bbb184a08b`) **EXACT** | `[1.0190, 1.0097, 0.9993, 0.9983, 0.9669, 1.0254, 0.9651, 1.0005, 1.0084, 1.0192, 1.0017, 1.0203]`<br>**Marginal `S5` median: `1.0051x` (`+0.51%`, 95% CI `[0.9988x, 1.0191x]`)**, **`8/12` faster** (wall `1.0078x`, `8/12`)<br>`loo2` A/A: `0.9955` (**`[0.9717, 1.0299]`**) -> **`S5` KEPT** | **MET** (`1.0051x` in `[1.0035x, 1.0130x]`, `8/12 >= 8/12`, KEPT) | **CAUGHT** (`79219bb2501b9ff2` on `loo_tt_planted_fault.patch.txt`) |
| **`loo3` (`PGO1` minus `S7` `uci` + `clear`)** | `loo3_pgo1_minus_s7.patch.txt` | 615 | Full identity suite + `500k`-op TT+stop oracle (`fd8c91bbb184a08b`) **EXACT** | `[1.0112, 1.0168, 1.0049, 0.9913, 0.9759, 1.0006, 0.9904, 1.0125, 1.0149, 1.0340, 1.0115, 1.0130]`<br>**Marginal `S7` median: `1.0114x` (`+1.14%`, 95% CI `[0.9960x, 1.0140x]`)**, **`9/12` faster** (wall `1.0059x`, `8/12`)<br>`loo3` A/A: `0.9994` (**`[0.9433, 1.0219]`**) -> **`S7` KEPT** | **MET** (`1.0114x` in `[1.0040x, 1.0160x]`, `9/12 >= 8/12`, KEPT) | **CAUGHT** (`79219bb2501b9ff2` on `loo_tt_planted_fault.patch.txt`) |
| **`loo4` == `pgo2_sp_carriers` (`PGO1` minus `TT` part = ONLY the `5` carrying parts!)** | `pgo2_sp_carriers.patch.txt` *(identical to `loo4_pgo1_minus_tt.patch.txt`)* | 961 | Full identity suite + `1,005`-pos / `21,765`-move `Board` legal/check oracle **EXACT** | `[0.9985, 1.0136, 1.0008, 0.9891, 0.9739, 1.0013, 0.9942, 0.9968, 0.9969, 1.0110, 1.0023, 1.0058]`<br>**Marginal `TT` median: `0.9996x` (`-0.04%`, `6/12` faster; wall `0.9992x`, `6/12`)**; `loo4` pooled CPU `644.36` sps vs `PGO1` `640.42` sps (`+0.61%` faster without `TT`!)<br>`loo4` A/A: `1.0031` (**`[0.9636, 1.0526]`**) -> **`TT` DROPPED (`loo4` IS the 5-carrier diff!)** | **MET** (`0.9996x` in `[0.9950x, 1.0034x]`, `6/12 < 8/12`, DROPPED) | **CAUGHT** (`HAS_LEGAL_MOVE MISMATCH` on `loo4_legal_planted_fault.patch.txt`) |
| **`loo5` (`PGO1` minus Legal-move part)** | `loo5_pgo1_minus_legal.patch.txt` | 941 | Full identity suite + `500k`-op TT+stop oracle (`fd8c91bbb184a08b`) **EXACT** | `[1.0090, 1.0099, 1.0138, 0.9960, 0.9797, 1.0073, 0.9920, 1.0119, 0.9951, 1.0120, 1.0006, 1.0031]`<br>**Marginal `Legal` median: `1.0052x` (`+0.52%`, 95% CI `[0.9955x, 1.0109x]`)**, **`8/12` faster** (wall `1.0060x`, `9/12`)<br>`loo5` A/A: `0.9945` (**`[0.9822, 1.0103]`**) -> **`Legal` KEPT** | **MET** (`1.0052x` in `[1.0040x, 1.0160x]`, `8/12 >= 8/12`, KEPT) | **CAUGHT** (`79219bb2501b9ff2` on `loo_tt_planted_fault.patch.txt`) |
| **`loo6` (`PGO1` minus `Stop + Hot` part)** | `loo6_pgo1_minus_stop_hot.patch.txt` | 1,014 | Full identity suite + `500k`-op TT+stop oracle (`fd8c91bbb184a08b`) **EXACT** | `[1.0296, 1.0143, 1.0103, 1.0017, 0.9893, 0.9938, 0.9858, 1.0194, 1.0044, 1.0254, 1.0134, 1.0125]`<br>**Marginal `Stop+Hot` median: `1.0114x` (`+1.14%`, 95% CI `[0.9977x, 1.0169x]`)**, **`9/12` faster** (wall `1.0112x`, `9/12`)<br>`loo6` A/A: `0.9904` (**`[0.9554, 1.0193]`**) -> **`Stop+Hot` KEPT** | **KILLED** (`1.0114x > 1.0034x`: register `check_node_or_periodic_stop` STILL saves `+1.14%` on SP-profile!) | **CAUGHT** (`79219bb2501b9ff2` on `loo_tt_planted_fault.patch.txt`) |

---

## 4. What We Would Do Next With Another 90 Minutes (Ranked)

1. **Hand the PC TWO cleanly-isolated SP-profile-proven candidates against `r15d`:**
   - **Compact `961`-line candidate (`job12/pgo2_sp_carriers.patch.txt`):** `S4 + S5 + S7 + Legal + Stop/Hot` (`+2.4%` SP-profile CPU, zero `MovePicker` scoring refactor).
   - **Full `1,857`-line + `Stop` candidate (`job11/curated_sp_bundle.patch.txt` + `PGO1`'s `check_node_or_periodic_stop()`):** Job 11's `curated_sp_bundle` (`S4 + S5 + S7 + G1..G4 + W1 + W2`, `+3.66%` SP-profile CPU in `12/12` rounds in `job11/timing3_sp_r15d_vs_curated_12x60_hash16_raw.txt` line 66) had dropped all of `P1` (`TT + Stop`) together, whereas Job 12 just proved that **`Stop` (`check_node_or_periodic_stop`) carries `+1.14%` (`9/12`) while `TT` was `-0.04%` (`6/12`)**! Merging `check_node_or_periodic_stop()` (without `TT`) into `curated_sp_bundle` attacks an additional `~1.0%` on top of `+3.66%`.
2. **Split Part 6 (`check_node_or_periodic_stop()` vs `[[gnu::hot]]` `apply_position_sv`) by leave-one-out (`~0.8%–1.1%` share):** Verify that the `+1.14%` comes from `check_node_or_periodic_stop()` skipping `32.90M` `total_nodes()` calls rather than the `[[gnu::hot]]` attribute (which the SP profile already supplies).

---

## 5. Times, Runtime Identity, and Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job12/stamps.txt`:**
  `Tue Nov 17 11:56:49 PM UTC 2026 | job 12 received (FABLE_TO_carbon2_12.md); writing standalone prediction for Timing (1): SP-profiled r15d vs SP-profiled r15d + PGO1`
- **Last line of `forge-combo29/carbon2/job12/stamps.txt`:**
  `Wed Nov 18 06:43:32 AM UTC 2026 | Writing REPORT_carbon2_job12.md and pushing branch`
- **Model name and version (as given by runtime):** `Gemini 4 Carbon`

### Verbatim Pre-Commit Check (`git status --short && ls -R forge-combo29/carbon2/job12`)

```text
?? forge-combo29/carbon2/job12/REPORT_carbon2_job12.md
forge-combo29/carbon2/job12:
build_pgo_raw.txt
loo1_pgo1_minus_s4.patch.txt
loo2_pgo1_minus_s5.patch.txt
loo3_pgo1_minus_s7.patch.txt
loo4_legal_planted_fault.patch.txt
loo4_pgo1_minus_tt.patch.txt
loo5_pgo1_minus_legal.patch.txt
loo6_identity_raw.txt
loo6_oracles_and_fault_raw.txt
loo6_pgo1_minus_stop_hot.patch.txt
loo_tt_planted_fault.patch.txt
pgo1_loo6_12x60_hash16_raw.txt
pgo2_sp_carriers.patch.txt
prediction_pgo1_loo6_sp.txt
prediction_timing1_pgo1_sp.txt
REPORT_carbon2_job12.md
run_pgo1_loo6_12x60.py
stamps.txt
step0_job12_raw.txt
timing1_sp_r15d_vs_pgo1_12x60_hash16_raw.txt
```

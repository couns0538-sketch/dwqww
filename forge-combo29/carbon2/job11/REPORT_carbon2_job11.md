# Forge (`carbon2` — Job 11 Report): Self-Play PGO Profile (`+3.23%`), `bundle 5` on SP-Profile (`+2.59%`, `12/12`), Leave-One-Out Ablation, and `curated_sp_bundle.patch.txt`

- **Branch:** `for-fable-and-opus/carbon2-work` (no pull request opened; zero engine source files modified in-tree; text-only artifacts under `forge-combo29/carbon2/job11/`, zero binaries, net files, or `.profraw`/`.profdata` files committed).
- **PC-Matched Compiler, Linker, Target & Both PGO Profiles (`forge-combo29/carbon2/job11/build_pgo_raw.txt`):**
  - **Toolchain & `-march`:** `clang++-18` (`Ubuntu clang version 18.1.3 (1ubuntu1)`) with GCC 13.3's `libstdc++` (`--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `-flto=thin -fuse-ld=lld-18` (`Ubuntu LLD 18.1.3`), `llvm-profdata-18`, `-march=sapphirerapids` (Clang 18's native `AVX-512` + `AVX512-VNNI` + `BMI2` `PEXT` target on this Intel Sapphire Rapids Xeon), and **all six `FORGE_SPD_*` / `FORGE_SEARCH_SPEED2` switches of File 10 fact `(c)`** explicitly passed on every compile line (`-DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=1`).
  - **Profile files merged per build (`build_pgo_raw.txt` lines 437–443):**
    1. **Today's bench-only profile (`MODE=bench`):** **`1` `.profraw` file merged** (`bench 11 -> 1,261,644`, `bench 13 -> 6,312,262`, `bench 16 -> 74,843,992` nodes with `net768.fnn3` and `CuckooRep true`, `HistRework 2`, `TtPruneV2 true`, `CorrHistV2 true`).
    2. **SP profile (`MODE=sp`):** **`2` `.profraw` files merged per build** — Process 1 runs the exact `bench 11 / 13 / 16` stdin above (`1` `.profraw`), and Process 2 runs **`60` self-play games** through our self-play driver (`go softnodes 2000`, `PC20 + net768.fnn3`, `Hash 16`, `Threads 1`) on the **last `60` unique roots of `positions_250.txt`** (`disjoint_from_timing_60 = True`: strictly zero overlap with the first `60` roots used by timed runs; **`games = 60`, `searches = 5,531`, `nodes = 18,059,934`, `trace = 1646ce4566de2f40`** across every SP-profile build).

---

## 0. Step 0 Verification Across Each Build (`forge-combo29/carbon2/job11/step0_job11_raw.txt`)

- **Full Step 0 on Bench-Profiled `pc_r15` (`1` `.profraw` merged) and SP-Profiled `pc_r15` (`2` `.profraw` merged):** Every pin matched bit-identically with zero error/warning lines on both builds:
  - No settings, no net: `bench 11 -> 312866`, `bench 13 -> 862329`, `bench 16 -> 3024920`, `go perft 5 -> 4865609`
  - `PC20`, no net: `bench 11 -> 278024`, `bench 13 -> 587276`
  - `net512.fnn3` only: `bench 11 -> 965454`, `bench 13 -> 4151906`
  - `PC20`, then `net512.fnn3`: `bench 11 -> 625258`, `bench 13 -> 3652372` (`checksum fdff70de72e4ca82 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512`)
  - `PC20` + `net512.fnn3` `eval`: `startpos -> nnue 968`, `r1bqkbnr/... -> nnue 1176`, `8/5pk1/... -> nnue 31`.
- **Step 0 / Post-`r15c` Pins on Timed Builds (`bench_r15d_1` [`1` `.profraw`], `sp_r15d_1` [`2` `.profraw`], `sp_b5_1` [`2` `.profraw`]):** `go perft 5 -> 4865609`, `PC20 + net512` `bench 11 -> 625258`, `bench 13 -> 3652372`, `evals -> 968 / 1176 / 31`, `PC20 + net768` `bench 11 -> 882074`, `bench 13 -> 4275906` (**ALL EXACT**).

---

## 1. Profile Timing (1) and Bundle Timing (2) at `Hash 16` (`12` Rounds x `60` Games `A1 B1 B2 A2` = `48` Runs Each)

Every run produced the exact same `48/48` self-play trace **`ee465caeff9c0fcf` (`7,670` searches, `25,641,316` nodes)**.

| Comparison (`Hash 16`, `Threads 1`, `PC20 + net768.fnn3`, `go softnodes 2000`) | Raw File | Engine CPU (`getrusage` ns): Per-Round Ratios, Paired Median, Pooled Median, Rounds Faster, A/A Range | Wall Clock (`perf_counter_ns`): Per-Round Ratios, Paired Median, Rounds Faster, A/A Range | Standalone Prediction (Commit, Graded) |
| :--- | :--- | :--- | :--- | :--- |
| **(1) `r15d` bench-profile (`A`, `1` `.profraw`) vs `r15d` SP-profile (`B`, `2` `.profraw`)** | `timing1_r15d_bench_vs_sp_12x60_hash16_raw.txt` | `[1.0511, 1.0228, 1.0507, 1.0354, 1.0484, 1.0181, 0.9985, 1.0500, 1.0227, 1.0293, 1.0260, 1.0353]`<br>**Paired median: `1.0323x` (`+3.23%`, 95% CI `[1.0228x, 1.0492x]`)**, pooled: `1.0333x` (`+3.33%`, `616.87 -> 637.43` cpu_sps), **`11/12` faster**<br>A/A: `med(A2)/med(A1)=0.9950` (**`[0.9095, 1.0406]`**), `med(B2)/med(B1)=1.0015` (**`[0.9903, 1.0156]`**) | `[1.0498, 1.0211, 1.0269, 1.0390, 1.0398, 1.0190, 0.9948, 1.0477, 1.0284, 1.0291, 1.0232, 1.0234]`<br>**Paired median: `1.0276x` (`+2.76%`, 95% CI `[1.0222x, 1.0394x]`)**, **`11/12` faster**<br>A/A: `1.0013` (`[0.9103, 1.0156]`), `0.9992` (`[0.9823, 1.0242]`) | `9db90b8c0`: **MET** (`1.0323x` inside `[1.008x, 1.035x]`, `11/12 >= 9/12`, wall `1.0276x` inside `[1.006x, 1.035x]`: SP profile alone pays **`+3.23%`**!) |
| **(2) `r15d` SP-profile (`A`, `2` `.profraw`) vs `bundle 5` SP-profile (`B`, `2` `.profraw`)** | `timing2_sp_r15d_vs_bundle5_12x60_hash16_raw.txt` | `[1.0498, 1.0147, 1.0105, 1.0274, 1.0301, 1.0245, 1.0330, 1.0279, 1.0152, 1.0214, 1.0366, 1.0237]`<br>**Paired median: `1.0259x` (`+2.59%`, 95% CI `[1.0183x, 1.0316x]`)**, pooled: `1.0232x` (`+2.32%`, `633.16 -> 647.85` cpu_sps), **`12/12` faster** (`min = 1.0105x`)<br>A/A: `med(A2)/med(A1)=1.0010` (**`[0.9446, 1.0703]`**), `med(B2)/med(B1)=0.9996` (**`[0.9692, 1.0474]`**) | `[1.0490, 1.0132, 1.0143, 1.0268, 1.0272, 1.0086, 1.0259, 1.0170, 1.0111, 1.0171, 1.0358, 1.0284]`<br>**Paired median: `1.0215x` (`+2.15%`, 95% CI `[1.0138x, 1.0278x]`)**, **`12/12` faster**<br>A/A: `0.9963` (`[0.9431, 1.0693]`), `1.0007` (`[0.9725, 1.0462]`) | `ececa4392`: **MET** (`1.0259x` inside `[1.010x, 1.028x]`, `12/12 >= 9/12`, wall `1.0215x` inside `[1.008x, 1.028x]`: **`bundle 5` keeps `+2.59%` on top of the SP profile!**) |

---

## 2. What We Chose Next and Why: Leave-One-Out SP-Profile Ablation (`bundle 5 minus X`, `ablation_loo_sp_6x60_hash16_raw.txt`)

Because `bundle 5` kept **`+2.59%` (`12/12` faster)** in Timing (2), we followed File 11's exact leave-one-out procedure: we partitioned `bundle 5` into `6` disjoint components `X`, built an SP-profile (`2` `.profraw`) binary for each **`bundle 5 minus X`**, and ran `6` palindromic rounds x `10` builds x `60` games (`60` runs = `460,200` searches, all `ee465caeff9c0fcf`; `A/A` `r15d` median `1.0049` `[0.9935, 1.0568]`, `B/B` `bundle 5` median `1.0008` `[0.9941, 1.0152]`, full `bundle 5 / r15d` median `1.0274x`, `6/6` faster).

Before running, `prediction_ablation_loo_sp.txt` (`commit 61c137753`) pre-declared the carrier rule: keep `X` iff `median_r(bundle5_r / (bundle5_minus_X)_r) >= 1.0035x` (`>= +0.35%` marginal loss when `X` is removed) AND `bundle 5 > bundle 5 minus X` in `>= 4 / 6` rounds:

| Removed Component `X` (`L_X = bundle 5 minus X`) | Marginal Contribution `b5 / L_X` (Per-Round CPU Ratios, Median, Rounds `b5 > L_X`) | Remaining `L_X / r15d` Median | Prediction (`61c137753`) | Gate Decision for `curated_sp_bundle.patch.txt` |
| :--- | :--- | :---: | :---: | :--- |
| **`G1..G4`** (`L_g14`: `material_corr_key`, `G2` `SEE`, `known_gives_check` + off-ray `has_legal_move`, `v3_active_net_` + `king_sq_`) | `[1.0264, 1.0151, 1.0162, 1.0239, 1.0028, 1.0180]` -> **`1.0171x` (`+1.71%`, `6/6`)** | `1.0125x` (`+1.25%`) | `[1.004x, 1.014x]` *(above upper bound — stronger!)* | **KEPT (Largest Carrier)** |
| **`S7` parts 1 & 2** (`L_s7`: zero-alloc `string_view` `position` parser + `Worker::clear` `memset`) | `[0.9971, 1.0401, 1.0231, 0.9998, 1.0095, 1.0130]` -> **`1.0113x` (`+1.13%`, `4/6`)** | `1.0092x` (`+0.92%`) | `[0.998x, 1.005x]` *(above upper bound — stronger!)* | **KEPT (2nd Largest Carrier)** |
| **`W1 + W2`** (`L_w12`: fused `MovePicker`, single-pass `QuietMoves` pin-legality, lazy `lesser_threats`, 1D row pointers) | `[1.0274, 1.0225, 1.0019, 1.0061, 0.9993, 1.0093]` -> **`1.0077x` (`+0.77%`, `5/6`)** | `1.0152x` (`+1.52%`) | `[1.006x, 1.018x]` (**MET**) | **KEPT (3rd Carrier)** |
| **`S4 + S5`** (`L_s45`: `-2.56 KB` `MovePicker` stack reduction + `make_move` `precomputed_key` & lazy `Undo`) | `[1.0003, 1.0072, 1.0047, 1.0142, 1.0050, 1.0288]` -> **`1.0061x` (`+0.61%`, `6/6`)** | `1.0172x` (`+1.72%`) | `[1.004x, 1.014x]` (**MET**) | **KEPT (4th Carrier)** |
| **`P1`** (`L_p1`: `check_node_or_periodic_stop` + 56B `TTProbe` miss fast-path + `WK/BK` `is_legal`) | `[0.9987, 1.0085, 0.9966, 1.0005, 0.9929, 1.0120]` -> **`0.9996x` (`-0.04%`, `3/6`)** | `1.0253x` (`+2.53%`) | `[1.0035x, 1.012x]` (**KILLED** — absorbed by SP profile!) | **DROPPED (`0%` once SP profile warms `should_stop`)** |
| **`S1_nnue + S2 + S3 + S6`** (`L_s1236`: `refresh_one_and_evaluate`, `S2` epoch cache, `S3` prefetch, `S6` `SEE`) | `[0.9978, 0.9873, 0.9770, 0.9836, 0.9872, 0.9941]` -> **`0.9873x` (`-1.27%`, `0/6`)** | **`1.0396x` (`+3.96%`)** | `[0.988x, 1.003x]` *(even more negative: `-1.27%`!)* | **DROPPED (`0/6`: removing it sped `bundle 5` up in all 6 rounds!)** |

---

## 3. Final Curated Unified Diff Against `r15d` (`curated_sp_bundle.patch.txt`)

| Step | Patch File (`forge-combo29/carbon2/job11/...`) | Lines | Identity & Oracles (`curated_identity_and_bench13_raw.txt`, `curated_oracles_and_fault_raw.txt`) | SP-Profile Self-Play Timing vs SP-Profile `r15d` at `Hash 16` (`12` rounds x `60` games = `48` runs, `timing3_sp_r15d_vs_curated_12x60_hash16_raw.txt`) | Prediction (`5d5b42642`) | Planted Fault |
| :--- | :--- | ---: | :--- | :--- | :--- | :--- |
| **`curated_sp_bundle`** | `curated_sp_bundle.patch.txt` *(ONE unified diff against `r15d` holding ONLY `S4 + S5 + S5_assert + S7 + G1..G4 + W1 + W2`; zero `S1/S2/S3/S6/O2/S7p3/P1`)* | 1,857 | `PC20` + `net768`/`net512` `bench 11/13/16`, `250/250` depth-9 rows, `1,000` evals (both nets), 6-game traces (`4560d7c3afdeba2e`, `9ed22c1193ab96de`), `2,010/2,010` all-stages `MovePicker` sequences, `55,868/55,868` evasion sequences, `-UNDEBUG` `S5` key assert, and `368,160` self-play searches (`ee465caeff9c0fcf`) **ALL EXACT**; stack `7104 -> 4512 B (-2592 B)` | **Engine CPU (`getrusage` ns):** `[1.0205, 1.0356, 1.0296, 1.0478, 1.0404, 1.0292, 1.0261, 1.0377, 1.0449, 1.0394, 1.0412, 1.0292]`<br>**Paired median: `1.0366x` (`+3.66%`, 95% CI `[1.0292x, 1.0408x]`)**, **pooled: `1.0333x` (`+3.33%`, `639.35 -> 660.66` cpu_sps)**, **`12/12` faster** (`min = 1.0205x`)<br>A/A: `med(A2)/med(A1)=0.9967` (**`[0.9768, 1.0115]`**), `med(B2)/med(B1)=0.9998` (**`[0.9863, 1.0171]`**)<br>**Wall:** `[1.0157, 1.0270, 1.0237, 1.0390, 1.0307, 1.0295, 1.0223, 1.0408, 1.0423, 1.0365, 1.0368, 1.0399]`<br>**Paired median: `1.0336x` (`+3.36%`, 95% CI `[1.0253x, 1.0395x]`)**, pooled `1.0341x`, **`12/12` faster**; A/A `1.0015` (`[0.9805, 1.0240]`), `1.0015` (`[0.9586, 1.0165]`) | **MET** (`1.0366x` CPU inside `[1.025x, 1.050x]`, `12/12 >= 10/12` faster; `1.0336x` wall inside `[1.020x, 1.050x]`, `12/12 >= 10/12` faster; **`+1.07%` faster than full `bundle 5` with `531` fewer lines!**) | **CAUGHT** at seq 0 (`c2[to]` continuation drop in `curated_planted_fault.patch.txt` + `-UNDEBUG` `S5` assert abort, `curated_oracles_and_fault_raw.txt`) |

---

## 4. What We Would Do Next With Another 90 Minutes (Ranked)

1. **Test `curated_sp_bundle.patch.txt` (`1,857` lines against `r15d`) on the PC's SP-profiled `r15d`:** Leave-one-out ablation on the SP-profile build resolved the exact cause of `bundle 1`'s weak PC showing: `S1_nnue + S2 + S3 + S6` actively dragged SP-profiled Clang ThinLTO + PGO down by **`-1.27%` (`0/6` rounds)** and `P1` became **`-0.04%`** once the SP profile already warmed `should_stop()`, whereas the four kept carriers (`G1..G4` `+1.71%`, `S7` `+1.13%`, `W1+W2` `+0.77%`, `S4+S5` `+0.61%`) each earn their keep on top of the SP profile.
2. **Isolate `G1..G4` individually by leave-one-out (`curated minus G1`, `minus G2`, `minus G3`, `minus G4`) if an even smaller patch (`< 1,000` lines) is desired on the PC:** `G1..G4` was the single largest carrier (`+1.71%`, `6/6`); splitting its `4` sub-pieces by leave-one-out on SP-profile would verify whether all four (`material_corr_key`, `G2` `SEE`, `G3` `known_gives_check` + `has_legal_move`, `G4` `v3_active_net_` + `king_sq_`) contribute positively or if `1–2` sub-pieces carry the full `+1.71%`.
3. **Stop bit-exact micro-optimizations beyond `curated_sp_bundle.patch.txt` unless a PC `perf` profile shows a remaining `>= 2%` pocket:** Combined with the SP profile (`+3.23%` cloud / `+2.18%` PC), `curated_sp_bundle.patch.txt` harvests all remaining bit-exact wasted-work pockets (`MovePicker`, `lesser_threats`, `make_move`, `SEE`, `has_legal_move`, `material_corr_key`, `uci` `position`) without touching move order on equal scores.

---

## 5. Times, Runtime Identity, and Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job11/stamps.txt`:**
  `Tue Nov 17 10:30:30 PM UTC 2026 | job 11 received (FABLE_TO_carbon2_11.md); preparing standalone predictions and SP-profile builds`
- **Last line of `forge-combo29/carbon2/job11/stamps.txt`:**
  `Tue Nov 17 11:53:13 PM UTC 2026 | finalizing REPORT_carbon2_job11.md and pushing branch`
- **Model name and version (as given by runtime):** `Gemini 4 Carbon`

### Verbatim Pre-Commit Check (`git status --short && ls -R forge-combo29/carbon2/job11`)

```text
?? forge-combo29/carbon2/job11/REPORT_carbon2_job11.md
forge-combo29/carbon2/job11:
ablation_loo_sp_6x60_hash16_raw.txt
build_pgo_raw.txt
curated_identity_and_bench13_raw.txt
curated_oracles_and_fault_raw.txt
curated_planted_fault.patch.txt
curated_sp_bundle.patch.txt
prediction_ablation_loo_sp.txt
prediction_curated_sp_bundle.txt
prediction_timing1_sp_profile.txt
prediction_timing2_bundle5_sp.txt
REPORT_carbon2_job11.md
run_loo_sp_ablation.py
stamps.txt
step0_job11_raw.txt
timing1_r15d_bench_vs_sp_12x60_hash16_raw.txt
timing2_sp_r15d_vs_bundle5_12x60_hash16_raw.txt
timing3_sp_r15d_vs_curated_12x60_hash16_raw.txt
```

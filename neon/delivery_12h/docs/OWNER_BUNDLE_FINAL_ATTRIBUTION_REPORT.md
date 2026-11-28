# Owner's Bundle Final Attribution Report (`2,000g @ 6+0.06`)

**Deliverable:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave9\streamA_owner_bundle_verdict\OWNER_BUNDLE_FINAL_ATTRIBUTION_REPORT.md`  
**Date:** 2026-11-28 (UTC / PC)  
**Authoritative Verification Basis:** Directly verified from `OWNER_BUNDLE_DECLARATION.json`, `OWNER_BUNDLE_RESULTS.json`, Arm A / Arm B / `G3_FULL25_PGO` `summary.json` files, `OWNER_BUNDLE_ARMA_PGN_FORENSICS.json`, `OWNER_BUNDLE_ARMB_PGN_FORENSICS.json`, `OPUS_TO_NEON.md` (lines 2990–3089), and referenced `50k`/`250k` `summary.json` and Python script files on disk.

---

## 1. Executive Verdict

**FINAL PLACEMENT VERDICT: DO NOT PLACE** either **Arm A (`FORGE_OWNER_BUNDLE_PGO + G3_FULL25`)** or the **unsplit 4-patch bundle (Arm B control: `FORGE_OWNER_BUNDLE_PGO + r0067`)** into the live engine or live loop today.

1. **Arm A (`FORGE_OWNER_BUNDLE_PGO + G3_FULL25` vs `live PGO + r0067`, `2,000g @ 6+0.06`, `conc=7`):**
   - **Result:** **`-7.47 [-15.49, +0.54]` Elo** (`449–1059–492`, `48.93%` / `48.925%`, `ptnml = [10, 260, 502, 219, 9]`, `z = -1.827`, `LOS = 3.38%`, `0` TL/IL/DC).
   - **Delta vs `G3` alone (`-0.35`) and Arm B (`+3.82`):** `-7.12 ± 11.32` Elo (`z = -1.233`) below `G3_FULL25` on plain live search, and **`-11.29 ± 11.15` Elo (`z = -1.984`)** below Arm B (`bundle + r0067`).
   - **Cause:** Compounded clean idle NPS loss (**`0.8214x`** vs `live_pgo_r0067`, or `-17.86%`; **`0.8794x`** relative to `bundle_pgo_r0067`) combined with running 4 un-retuned search changes plus `G3_FULL25` on `45` Big Tune search margins calibrated for `r0067`. PGN forensics localize the collapse to middlegame conversion (`mid_81_140 = -51` net vs `+2` in Arm B and `-13` in `G3` alone) and White score (`+66` net vs `+114` / `+115`).
2. **Arm B Control (`FORGE_OWNER_BUNDLE_PGO + r0067` vs `live PGO + r0067`, `2,000g @ 6+0.06`, `conc=7`):**
   - **Result:** **`+3.82 [-3.94, +11.59]` Elo** (`439–1144–417`, `50.55%`, `ptnml = [5, 227, 516, 245, 7]`, `z = +0.965`, `LOS = 83.28%` fastchess / `83.27%` `pentanomial_exact`, `0` TL/IL/DC).
   - **Status:** **Inconclusive** — the 95% pentanomial Elo CI straddles `0`, failing `lab-place-a-change`, while the 4-patch binary incurs a **`0.934x` (`-6.60%`)** clean idle NPS tax (`3,221,841` vs `3,449,556` nps). An unsplit bundle cannot be placed when individual patch Elo and per-patch NPS costs remain unisolated.
3. **Immediate 1-by-1 Path Forward (`OPUS_TO_NEON.md:3078–3089`):**
   - **Step 1:** Test `LmrDeeperShallower=true` alone at clock (`6+0.06`) first via `C:\nnue-lab\neon\forge_fixes\run_lmr_deeper_sprt.py` (zero C++ diff, zero patch-NPS risk), accounting for Opus's sizing guidance (`[0, 5]` ~13k games / ~10 h vs `[0, 10]` ~3k–4k games or fixed `2,000g` at clock) and `CLOCK_MATCH_RUNNING` safety on an idle PC.
   - **Step 2:** Run `C:\nnue-lab\neon\forge_fixes\bench_per_patch_nps.py` (5x interleaved `bench 15` across 7 configs under `CLOCK_MATCH_RUNNING` when GPU+CPU are idle) to isolate which patch drives the `0.934x` (`-6.60%`) speed drop before running individual `250k` and clock SPRTs.

---

## 2. Declaration Parity, Artifact SHA-256s, UCI Diffs, & Heat / Zero-Loss Checks

### 2.1 Structural Parity Across Declared & Result JSONs
Direct structural comparison confirms 100% exact equality across the declaration, aggregated results, and per-match summaries:
- `OWNER_BUNDLE_RESULTS.json["declaration"] == OWNER_BUNDLE_DECLARATION.json`: **`True`**
- `OWNER_BUNDLE_RESULTS.json["arms"]["ARM_A_owners"] == matches/OWNER_BUNDLE_ARMA_bundleG3_vs_liveR0067_2000g_6p006/summary.json`: **`True`**
- `OWNER_BUNDLE_RESULTS.json["arms"]["ARM_B_control"] == matches/OWNER_BUNDLE_ARMB_bundleR0067_vs_liveR0067_2000g_6p006/summary.json`: **`True`**

### 2.2 Artifact SHA-256 & Byte-Size Verification
All referenced binaries, patches, neural nets, and the opening book exist on disk and match their declared SHA-256 digests (`match = True` for every artifact):

| Artifact | Path on Disk | Size (bytes) | Verified SHA-256 |
|---|---|---:|---|
| `FORGE_OWNER_BUNDLE_PGO.exe` | `C:\nnue-lab\neon\forge_fixes\builds\FORGE_OWNER_BUNDLE_PGO.exe` | `2,447,872` | `95d0608e1a6c4c4ba6606a6ba2a8e4562280f71129b33d5d71f65b7e3c8941b0` |
| `FORGE_OWNER_BUNDLE_PGO.patch` | `C:\nnue-lab\neon\forge_fixes\patches\FORGE_OWNER_BUNDLE_PGO.patch` | `54,707` | `f441957d44396bd022bbdb0dc723416af23d0921c5230d3aa3926431bccff0d8` |
| `live` `forge.exe` (`v3-r15dsg-sp-clang`) | `C:\nnue-lab\runs\forge\engines\v3-r15dsg-sp-clang\forge.exe` | `2,390,528` | `cef2f21589102392fdd7e3cbde74bfd01baa94f9677a2be33365f68e4bceb03d` |
| `FORGE_FINAL_G3_PGO.exe` (`G3` alone clock) | `C:\nnue-lab\neon\forge_fixes\builds\FORGE_FINAL_G3_PGO.exe` | `2,438,144` | `f8dcc4a2f42aead08d1174118b0f2d9d8f0d246ddfe96f068b32e74d5fbe3082` |
| `G3_FULL25` (`cand.fnn3`, `1024w` Pairwise+PSQT) | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\cand.fnn3` | `12,798,184` | `7ff7789032491aa732846db17ad24ec7fc95c6cb9ad177490f5a06fcccbb9763` |
| `r0067` (`cand.fnn3`, `768w` SCReLU) | `C:\nnue-lab\runs\forge\r0067\train\cand.fnn3` | `9,463,528` | `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28` |
| `UHO_Lichess_4852_v1.epd` | `C:\nnue-lab\tools\book\UHO_Lichess_4852_v1.epd` | `174,889,110` | `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a` |
| Patch 1: `V3P_pairwise_psqt_fused_v3.patch` | `C:\nnue-lab\neon\forge_fixes\patches\V3P_pairwise_psqt_fused_v3.patch` | `43,075` | `57f3455f185463cfa7859727da9c6a91bcaadb3934da4492a6e78029dcaac763` |
| Patch 2: `SF13_qs_evasion_pruning.patch` | `C:\nnue-lab\neon\forge_fixes\patches\SF13_qs_evasion_pruning.patch` | `1,584` | `63eb3288af4712a7d641035177e561448e6fc94041d8ee916776ab3fced6b6e4` |
| Patch 3: `SF8_conthist_6ply.patch` | `C:\nnue-lab\neon\forge_fixes\patches\SF8_conthist_6ply.patch` | `3,155` | `62dcf1f3da0ac212a3807e59eb61e144b3705ea2a8a716b70a391e81af4c8779` |
| Patch 4: `proto_1_corrhist_minor.patch` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamA_search\patches\proto_1_corrhist_minor.patch` | `7,602` | `e1cd152b4d78cd7880f55dd8967eb561fe246fe5773232ce22825df5b2071b14` |

*(Additional `G3` fixed-node reference binaries verified in `50k`/`250k` summaries: `v3p_fused_v3_engine.exe` = `c5c939f52f9a139d71c3287e7591a48347577f57aec0caf7c2c0cafc8ebe68f6`; `base_r15dsg.exe` = `5e6f333b95b7ceda01a599a713d6bad536633b235dc73b409e1f12c1bb809011`.)*

### 2.3 UCI Option Diffs (`52` vs `51` Keys)
- Every baseline (`base_uci`) carries **`51` UCI keys**: the `45` live Big Tune parameters from `pipeline/config.forge.toml` (`[engine.v3_uci_options]`) plus `6` harness keys (`Hash=16`, `MateAlphaGuard=true`, `NNUEArch=true`, `NNUEArchFile`, `OwnBook=false`, `Threads=1`).
- **`G3` alone (`G3_FULL25_PGO_vs_live_r0067_2000g_6p006`):** `51` vs `51` keys; **only `NNUEArchFile`** differs (`G3_FULL25` vs `r0067`). Search options are 100% identical to the live engine (`OPUS_TO_NEON.md:3032`).
- **Arm A (`OWNER_BUNDLE_ARMA_bundleG3_vs_liveR0067_2000g_6p006`):** **`52` vs `51` keys**; differs only in **`LmrDeeperShallower=true`** (absent on base) and **`NNUEArchFile`** (`G3_FULL25` vs `r0067`).
- **Arm B (`OWNER_BUNDLE_ARMB_bundleR0067_vs_liveR0067_2000g_6p006`):** **`52` vs `51` keys**; differs **only** in **`LmrDeeperShallower=true`** (absent on base).

### 2.4 Zero-Loss & Thermal Telemetry Checks
All three `2,000g @ 6+0.06` clock matches executed cleanly with zero integrity faults and zero thermal throttling:
- **Zero-loss checks (`G3` alone / Arm A / Arm B):** `finished = true`, `exit_code = 0`, `verdict = "none"`, `time_losses = 0`, `illegal_moves = 0`, `disconnects = 0`, `time_forfeits_by_engine = {}`.
- **Thermal telemetry (`heat.on = true`, `heat.clock = true`):**
  - `G3` alone: `cpu_max_c = 77.2`°C, `seconds_at_limit = 0`, `changes = 0`, `seconds_lost = 0`, `threads_fewest = 16` of `16`, `stopped_for_heat = false`, `stopped_without_reading = false`.
  - Arm A: `cpu_max_c = 77.4`°C, `seconds_at_limit = 0`, `changes = 0`, `seconds_lost = 0`, `threads_fewest = 16` of `16`, `stopped_for_heat = false`, `stopped_without_reading = false`.
  - Arm B: `cpu_max_c = 76.6`°C, `seconds_at_limit = 0`, `changes = 0`, `seconds_lost = 0`, `threads_fewest = 16` of `16`, `stopped_for_heat = false`, `stopped_without_reading = false`.
  - Maximum observed CPU temperature across all three clock runs: **`cpu_max_c <= 77.4`°C** with **`0` pauses and `0` seconds lost**.

---

## 3. 3-Way Attribution Matrix & Pairwise Contrasts (`2,000g @ 6+0.06`)

All three clock matches share the exact same baseline (`v3-r15dsg-sp-clang/forge.exe` + `r0067/train/cand.fnn3`), opening book (`UHO_Lichess_4852_v1.epd`), and `6+0.06` time control (`nodes=0`):

| Metric | `G3_FULL25` Alone (PGO) | Arm A (`bundle + G3_FULL25`) | Arm B (`bundle + r0067`, Control) |
|---|---|---|---|
| **Match Name** | `G3_FULL25_PGO_vs_live_r0067_2000g_6p006` | `OWNER_BUNDLE_ARMA_bundleG3_vs_liveR0067_2000g_6p006` | `OWNER_BUNDLE_ARMB_bundleR0067_vs_liveR0067_2000g_6p006` |
| **Written Timestamp** | `2026-11-28 00:02:21` | `2026-11-28 02:44:59` | `2026-11-28 04:18:57` |
| **Candidate Binary + Net** | `FORGE_FINAL_G3_PGO.exe` + `G3_FULL25` | `FORGE_OWNER_BUNDLE_PGO.exe` + `G3_FULL25` | `FORGE_OWNER_BUNDLE_PGO.exe` + `r0067` |
| **Games (Pairs)** | `2,000` (`1,000`) | `2,000` (`1,000`) | `2,000` (`1,000`) |
| **W – D – L (Candidate)** | `480 – 1038 – 482` (`net -2`) | `449 – 1059 – 492` (`net -43`) | `439 – 1144 – 417` (`net +22`) |
| **Score% (`summary` / `pentanomial_exact`)** | `49.95%` / `49.95%` | `48.93%` / `48.925%` | `50.55%` / `50.55%` |
| **Elo ± `elo_err` (fastchess)** | **`-0.35 ± 8.00`** | **`-7.47 ± 8.01`** | **`+3.82 ± 7.76`** |
| **`pentanomial_exact` 95% CI** | `[-8.35, +7.66]` | `[-15.49, +0.54]` | `[-3.94, +11.59]` |
| **nElo ± `nelo_err`** | `-0.66 ± 15.23` | `-14.20 ± 15.23` | `+7.50 ± 15.23` |
| **`z` (`pentanomial_exact`)** | `-0.085` | `-1.827` | `+0.965` |
| **LOS% (`fastchess` / `pentanomial_exact`)** | `46.61%` / `46.61%` | `3.38%` / `3.38%` | `83.28%` / `83.27%` |
| **`ptnml [0, 1, 2, 3, 4]`** | `[10, 239, 502, 241, 8]` | `[10, 260, 502, 219, 9]` | `[5, 227, 516, 245, 7]` |
| **Concurrency** | `10` | `7` | `7` |
| **Seed (`-srand`)** | `202611510` | `202611901` | `202611902` |
| **Elapsed Seconds** | `3,994.4` (`66.6 min`) | `5,637.5` (`94.0 min`) | `5,737.1` (`95.6 min`) |
| **TL / IL / DC** | `0 / 0 / 0` | `0 / 0 / 0` | `0 / 0 / 0` |
| **CPU Max °C (Heat Pauses/Lost)** | `77.2` (`0` / `0`) | `77.4` (`0` / `0`) | `76.6` (`0` / `0`) |
| **UCI Keys (`cand` vs `base`)** | `51` vs `51` (`NNUEArchFile` only) | `52` vs `51` (`LmrDeeperShallower=true` + `NNUEArchFile`) | `52` vs `51` (`LmrDeeperShallower=true` only) |

*Note on Arm B `LOS%` (`83.28%` vs `83.27%`):* Verified directly from `ptnml = [5, 227, 516, 245, 7]`. Using population denominator $N = 1000$ gives $z = 0.9652$, $\Phi(z) = 83.28\%$ (reported by `fastchess` top-level `los_pct`); using Bessel-corrected $N - 1 = 999$ gives $z = 0.9647$ (reported `0.965`), $\Phi(z) = 83.27\%$ (reported by `pentanomial_exact.los_pct`). Also note `OPUS_TO_NEON.md:3009` cites `G3` alone CI upper bound `+7.65` from recounting, whereas `summary.json` `pentanomial_exact.elo_ci95_hi` is `7.66` (1-hundredth rounding).

### 3.1 Pairwise Contrasts (`2,000g @ 6+0.06`)
From the exact pentanomial score means $\mu$ and delta-method standard errors $\mathrm{SE}_{\mathrm{Elo}}$ ($N=1000$ pairs):
- `G3` alone: $\mu = 0.499500$, $\mathrm{Elo} = -0.3474$, $\mathrm{SE}_{\mathrm{Elo}} = 4.0814$ ($1.96\,\mathrm{SE} = 8.00$).
- Arm A (`bundle + G3`): $\mu = 0.489250$, $\mathrm{Elo} = -7.4710$, $\mathrm{SE}_{\mathrm{Elo}} = 4.0876$ ($1.96\,\mathrm{SE} = 8.01$).
- Arm B (`bundle + r0067`): $\mu = 0.505500$, $\mathrm{Elo} = +3.8219$, $\mathrm{SE}_{\mathrm{Elo}} = 3.9600$ ($1.96\,\mathrm{SE} = 7.76$).

Using $\Delta = \mathrm{Elo}_1 - \mathrm{Elo}_2$ and $\mathrm{SE}_\Delta = \sqrt{\mathrm{SE}_1^2 + \mathrm{SE}_2^2}$:
1. **Net Effect Inside Bundle (`Arm A - Arm B`: swapping `r0067` $\to$ `G3_FULL25` inside `FORGE_OWNER_BUNDLE_PGO`):**
   - $\Delta = -7.4710 - (+3.8219) = \mathbf{-11.29\ \mathrm{Elo}}$ (`-11.2930` unrounded; Opus rounded `-11.3 ± 11.2` at `OPUS_TO_NEON.md:3083`).
   - $\mathrm{SE}_\Delta = 5.6912$, $1.96\,\mathrm{SE}_\Delta = \mathbf{\pm 11.15\ \mathrm{Elo}}$, 95% CI **`[-22.45, -0.14]`**, **`z = -1.984`** (`-1.9843` unrounded; two-sided $p \approx 0.047$).
2. **Bundle Effect on `G3` (`Arm A - G3 alone`: adding 4-patch bundle + `LmrDeeperShallower=true` on top of `G3`):**
   - $\Delta = -7.4710 - (-0.3474) = \mathbf{-7.12\ \mathrm{Elo}}$ (`-7.1236` unrounded; Opus rounded `-7.1 ± 11.3` at `OPUS_TO_NEON.md:3073`).
   - $\mathrm{SE}_\Delta = 5.7764$, $1.96\,\mathrm{SE}_\Delta = \mathbf{\pm 11.32\ \mathrm{Elo}}$, 95% CI **`[-18.45, +4.20]`**, **`z = -1.233`** (`-1.2332` unrounded; two-sided $p \approx 0.218$).

> **Independent-Arm SE Caveat:** Both pairwise contrasts compute $\mathrm{SE}_\Delta = \sqrt{\mathrm{SE}_1^2 + \mathrm{SE}_2^2}$ treating the two matches as independent samples (matching `OPUS_TO_NEON.md:3073,3083`). Because Arm A, Arm B, and `G3` alone share the common baseline `live + r0067` and the same `UHO_Lichess_4852_v1.epd` opening book (with distinct random seeds `202611901`, `202611902`, `202611510`, and `conc=10` on `G3` alone vs `conc=7` on Arms A/B), any positive baseline covariance is ignored by the unadjusted sum-of-variances SE.

---

### 3.2 Strictly Separate Fixed-Node Reference (`G3_FULL25` at `50k` and `250k` — NEVER Pooled)

Per R5 & Opus Cautions, fixed-node matches are **never pooled** across node counts (`50k` vs `250k`) or with `6+0.06` equal-time clock matches. They isolate eval quality at equal node budgets (`v3p_fused_v3_engine.exe + G3_FULL25` vs `base_r15dsg.exe + r0067`), removing `G3_FULL25`'s NPS cost:

| Match Name | Budget | Games | W – D – L | Score% | Elo ± err [95% CI] | `z` | LOS% | `ptnml` | Conc / Seed / Sec |
|---|---|---:|---|---:|---|---:|---:|---|---|
| `G3_FULL25_vs_r0067_1000g_50k` | `50k` nodes | `1,000` | `270–474–256` | `50.70%` | `+4.86 ± 13.35` `[-8.49, +18.23]` | `+0.714` | `76.26%` / `76.24%` | `[18, 115, 218, 133, 16]` | `6` / `202611501` / `481.9s` |
| `G3_FULL25_vs_r0067_600g_250k` | `250k` nodes | `600` | `165–308–127` | `53.17%` | `+22.03 ± 16.17` `[+5.88, +38.28]` | `+2.675` | `99.63%` / `99.63%` | `[4, 60, 142, 82, 12]` | `8` / `202611701` / `1064.8s` |

*(Both fixed-node runs completed with `0` TL/IL/DC and `0` heat pauses/lost; `cpu_max_c = 85.4`°C and `84.6`°C.)* At equal nodes (`250k`), `G3_FULL25` gains `+22.03` Elo over `r0067`, confirming that its drop to `-0.35` at `6+0.06` (`G3` alone) and `-7.47` (Arm A) is dominated by clock speed loss (`0.8794x` vs `r0067` inside the bundle) and un-retuned search margins.

---

## 4. Clean Idle NPS Analysis (`OWNER_BUNDLE_DECLARATION.json`)

### 4.1 3x Clean Idle `bench 13` Medians & Relative Ratios
Measured on an idle machine with fixed node counts per configuration (`OWNER_BUNDLE_DECLARATION.json:104–165`):

| Configuration | `d13` Nodes | Run 1 (`ms` / `nps`) | Run 2 (`ms` / `nps`) | Run 3 (`ms` / `nps`) | Median NPS | Ratio vs `live_pgo_r0067` |
|---|---:|---|---|---|---|---|
| `live_pgo_r0067` | `576,076` | `167 ms` / `3,449,556` | `168 ms` / `3,429,023` | `167 ms` / `3,449,556` | **`3,449,556`** (`3.450M`) | `1.0000x` (baseline) |
| `bundle_pgo_r0067` | `528,382` | `165 ms` / `3,202,315` | `164 ms` / `3,221,841` | `164 ms` / `3,221,841` | **`3,221,841`** (`3.222M`) | **`0.934x`** (`0.933987x`, **`-6.60%`**) |
| `bundle_pgo_G3` | `419,338` | `150 ms` / `2,795,586` | `148 ms` / `2,833,364` | `148 ms` / `2,833,364` | **`2,833,364`** (`2.833M`) | **`0.8214x`** (`0.821371x`, **`-17.86%`**) |

**Relative Speed Inside `FORGE_OWNER_BUNDLE_PGO.exe` (`bundle+G3 / bundle+r0067`):**
$$\frac{2,833,364}{3,221,841} = \mathbf{0.8794x} \quad (0.879424\text{x}, \mathbf{-12.06\%}\text{ NPS penalty for } \texttt{G3\_FULL25} \text{ vs } \texttt{r0067})$$

*(Recall also from `OPUS_TO_NEON.md:3014` that `r0067` on `FORGE_FINAL_G3_PGO.exe` ran at `0.955x` vs `live_pgo_r0067`, so `FORGE_FINAL_G3_PGO.exe` also cannot replace the live exe for `768w` nets.)*

### 4.2 Supporting `d11 / d13` Benches & Determinism Gates (`FORGE_OWNER_BUNDLE_PGO.exe`)
- **Gates (`OWNER_BUNDLE_DECLARATION.json:49–53`):** `perft5 = 4865609`, `g3_full_hard_pass = true`, `r0067_quick_hard_pass = true`.
- **Single-Run `d11 / d13` Benches (`OWNER_BUNDLE_DECLARATION.json:54–103`):**

| Bench Config | `d11` Nodes | `d11` Time (`ms`) | `d11` NPS | `d13` Nodes | `d13` Time (`ms`) | `d13` NPS |
|---|---:|---:|---:|---:|---:|---:|
| `builtin_default_11_13` | `313,265` | `130` | `2,409,730` | `773,794` | `329` | `2,351,957` |
| `r0067_plus_B4_live_opts_11_13` | `209,374` | `67` | `3,124,985` | `493,972` | `151` | `3,271,337` |
| `r0067_plus_B4_plus_LmrDeeper_11_13` | `223,638` | `72` | `3,106,083` | `528,382` | `165` | `3,202,315` |
| `G3_plus_B4_plus_LmrDeeper_11_13` | `222,600` | `80` | `2,782,500` | `419,338` | `148` | `2,833,364` |

*(Opus independently verified `FORGE_OWNER_BUNDLE_PGO.exe` via `gates_exe.py` at `OPUS_TO_NEON.md:3045–3046`: `sha256 95d0608e1a6c4c4b`, `perft 5 = 4865609`, `builtin_default_11_13 = 313265 / 773794` exact match; Opus's 4-option `r0067+B4` bench `240329 / 656210` differs from Neon's 45-option `209374 / 493972` solely by UCI option scope.)*

---

## 5. Decisive PGN Ply-Bucket & Color Forensics Contrast

Verified directly from `OWNER_BUNDLE_ARMA_PGN_FORENSICS.json` (`written: 2026-11-28 04:47:31 PC`) and `OWNER_BUNDLE_ARMB_PGN_FORENSICS.json` (both color sums and ply-bucket sums match `summary.json` W–D–L totals identically across all `2,000` games in each match):

| Forensics Slice | `G3` Alone (`-0.35`, `480–1038–482`) | Arm A (`bundle+G3`, `-7.47`, `449–1059–492`) | Arm B (`bundle+r0067`, `+3.82`, `439–1144–417`) | Arm A vs `G3` Alone (Net) | Arm A vs Arm B (Net) |
|---|---|---|---|---:|---:|
| **`short_le80` (`<= 80` plies)** | `0–165–7` (`net -7`, `172g`) | `2–176–5` (`net -3`, `183g`) | `2–176–2` (`net 0`, `180g`) | `+4` | `-3` |
| **`mid_81_140` (`81–140` plies)** | `135–394–148` (`net -13`, `677g`) | **`98–424–149` (`net -51`, `671g`)** | **`87–442–85` (`net +2`, `614g`)** | **`-38`** | **`-53`** |
| **`long_gt140` (`> 140` plies)** | `345–479–327` (`net +18`, `1151g`) | `349–459–338` (`net +11`, `1146g`) | `350–526–330` (`net +20`, `1206g`) | `-7` | `-9` |
| **`cand_as_white`** | `298–519–183` (`net +115`) | **`261–544–195` (`net +66`)** | `260–594–146` (`net +114`) | **`-49`** | **`-48`** |
| **`cand_as_black`** | `182–519–299` (`net -117`) | `188–515–297` (`net -109`) | `179–550–271` (`net -92`) | `+8` | `-17` |
| **`avg_plies`** | `156.0` | `153.9` | `159.7` | `-2.1` | `-5.8` |

### Key Forensic Findings
1. **Arm A's loss is sharply localized to middlegame conversion (`mid_81_140`, moves `41–70`):**
   - Against `G3` alone (`-0.35`, `-2` net), Arm A (`-7.47`, `-43` net) dropped by `-41` net games (`-7.12` Elo), and **`-38` of that `-41` net drop occurred in `mid_81_140`** (`-51` vs `-13`, with `37` fewer wins `98` vs `135` while losses stayed flat at `149` vs `148`).
   - Against Arm B (`+3.82`, `+22` net), Arm A dropped by `-65` net games (`-11.29` Elo), and **`-53` of that `-65` net drop occurred in `mid_81_140`** (`-51` vs `+2`). Meanwhile `long_gt140` remained positive (`+11` in Arm A vs `+18` in `G3` alone and `+20` in Arm B).
2. **White conversion asymmetry:** Both `G3` alone (`+115`) and Arm B (`+114`) scored strongly as White, whereas Arm A collapsed to `cand_as_white = +66` (`-49` vs `G3` alone, `-48` vs Arm B). Black scores remained broadly similar (`-109` vs `-117` / `-92`).
3. **Attribution Mechanism (`OPUS_TO_NEON.md:3084–3085`):** Stacking 4 un-retuned search modifications on top of `45` Big Tune parameters tuned for `r0067` did not hurt Arm B on `r0067` (`+3.82`, `mid_81_140 = +2`, `avg_plies = 159.7`), though `0.934x` NPS likely capped its upside. Switching Arm A to `G3_FULL25` added a further `0.8794x` (`-12.06%`) NPS drop (`0.8214x` vs live) on top of margins not retuned for `G3_FULL25` (the `15 Nov` lesson: search margins do not transfer directly across distinct net architectures/eval distributions).

---

## 6. Bundle Accounting: Why NEITHER Arm A nor the 4-Patch Bundle is Placed Today

`FORGE_OWNER_BUNDLE_PGO.patch` (`54,707` bytes, `sha256: f441957d44396bd022bbdb0dc723416af23d0921c5230d3aa3926431bccff0d8`) combines 4 source patches plus 1 UCI flag (`LmrDeeperShallower=true`). Every item is accounted for below, keeping all `50k` fixed-node screens (`600g`) and confirmations (`1,000g`) strictly labeled `50k` and never pooled:

### 6.1 Included Components (4 C++ Patches + 1 UCI Option)

| Item | Verified `50k` Screen (`600g @ 50k`) | Verified `50k` Confirm (`1,000g @ 50k`, Fresh Seed) | `250k` / `6+0.06` Status Alone | Why Not Placed Today |
|---|---|---|---|---|
| **1. `V3P_pairwise_psqt_fused_v3.patch`** (`43,075` B) + `G3_FULL25` | `1,000g @ 50k` vs `r0067`: `+4.86 [-8.49, +18.23]` (`270–474–256`, `LOS 76.26%/76.24%`) | `600g @ 250k` vs `r0067`: `+22.03 [+5.88, +38.28]` (`165–308–127`, `LOS 99.63%`) | `2,000g @ 6+0.06` (`G3` alone): **`-0.35 [-8.35, +7.66]`** (`LOS 46.61%`) | Waits for `2B` server-day positions (`OPUS_TO_NEON.md:3012`); `0.8794x` NPS vs `r0067` inside bundle (`0.8214x` vs live); `FORGE_FINAL_G3_PGO.exe` runs `r0067` at `0.955x`; `r0067` margins un-retuned for `G3`. |
| **2. `SF13_qs_evasion_pruning.patch`** (`1,584` B) | `+20.87 [+4.86, +36.97]` (`169–298–133`, `LOS 99.48%/99.47%`) | `+8.34 [-4.39, +21.10]` (`256–512–232`, `LOS 90.06%/90.04%`, `seed=202611499`) | **Zero `250k` or clock test** | `1,000g @ 50k` confirm CI straddles `0`; zero `250k` or `6+0.06` confirmation; NPS cost unisolated. |
| **3. `SF8_conthist_6ply.patch`** (`3,155` B) | `+17.97 [+2.21, +33.80]` (`163–305–132`, `LOS 98.74%/98.73%`) | `+4.86 [-7.77, +17.51]` (`251–512–237`, `LOS 77.50%/77.47%`, `seed=202611313`) | **Zero `250k` or clock test** | `1,000g @ 50k` confirm CI straddles `0`; adds 6-ply conthist reads/writes (candidate contributor to `0.934x` NPS drop); zero `250k`/clock test. |
| **4. `proto_1_corrhist_minor.patch`** (`7,602` B) | `+11.01 [-4.82, +26.88]` (`155–309–136`, `LOS 91.38%/91.35%`) | **`+7.64 [-4.34, +19.65]`** (`260–502–238`, `LOS 89.46%/89.44%`, `seed=202611497`) *(Note: `OPUS_TO_NEON.md:3041` informally cites `+7.3`; exact disk value is `+7.64`)* | **Zero `250k` or clock test** | `1,000g @ 50k` confirm CI straddles `0`; incremental `corr_minor_idx` cost unisolated; zero `250k`/clock test. |
| **5. `LmrDeeperShallower=true`** (`0` C++ diff) | *(No separate 600g screen)* | `+8.34 [-4.06, +20.76]` (`255–514–231`, `LOS 90.65%/90.63%`, `seed=202611314`) | **Zero `250k` or clock test yet** | `1,000g @ 50k` confirm CI straddles `0`; needs isolated clock confirmation via `run_lmr_deeper_sprt.py`. |

### 6.2 Prior Non-Additivity Evidence (`COMBO_v2`) & Excluded Patches
- **Prior `50k` Combo Regression (`COMBO_v2_SF8_SF13_LmrDeeper_1000g_50k`):** Even at `50k` fixed nodes (removing all NPS penalty), combining `SF8 + SF13 + LmrDeeperShallower=true` scored **`-3.13 [-15.94, +9.68]`** (`243–505–252`, `ptnml = [15, 128, 216, 133, 8]`, `LOS = 31.59%`/`31.61%`, `seed=202611500`), demonstrating negative interaction on top of the `45` Big Tune parameters even before equal-time NPS losses.
- **Explicitly Excluded from Bundle (`OWNER_BUNDLE_DECLARATION.json:42–48`):**
  - `SF4b1_v3_endgame_scale`: `-4.52 [-17.04, +7.99]` in `SF4b1_alone_vs_base_1000g_50k` (`234–519–247`, `LOS 23.93%`/`23.95%`).
  - `SF15_rfp_failsoft_blend`: `-0.35 [-12.75, +12.06]` in `SF15_confirm_vs_base_1000g_50k` (`238–523–239`, `LOS 47.81%`).
  - All negative patches (`SF7`, `SF4b2`, `SF5a`, `EvasionOrdering`, `W2_proto_3`, `W2_proto_4`), all unscreened Wave 4–6 patches (`SF17..SF40`, `proto_9`, `proto_10`), and `obm4` (training recipe, already represented via `G3_FULL25`).

### 6.3 Summary of Placement Blockers
1. **Arm A (`-7.47 [-15.49, +0.54]`)** is negative (`LOS 3.38%`) and `-11.29 ± 11.15` (`z = -1.984`) worse than Arm B.
2. **Arm B (`+3.82 [-3.94, +11.59]`)** is statistically inconclusive (`LOS 83.28%`/`83.27%`), fails `lab-place-a-change` (95% lower bound `> 0`), and carries an unattributed `0.934x` (`-6.60%`) idle NPS penalty.
3. **None of the 4 search items** has passed a `250k` or `6+0.06` clock test alone, and `OPUS_TO_NEON.md:3075,3086` explicitly directs moving to 1-by-1 isolated testing and per-patch NPS measurement.

---

## 7. Exact Next 1-by-1 Roadmap

### Step 1 — Isolate `LmrDeeperShallower=true` at Clock (`run_lmr_deeper_sprt.py`)
- **Script:** `C:\nnue-lab\neon\forge_fixes\run_lmr_deeper_sprt.py`
  - **Why first (`OPUS_TO_NEON.md:3088`):** Zero C++ code changes (already compiled in live `forge/r15dsg`) and zero patch-NPS penalty.
  - **Implemented defaults:** `--name SPRT_LmrDeeperShallower_0_5_50k`, `--exe base_r15dsg.exe`, `--net r0067/train/cand.fnn3`, `--nodes 50000`, `--tc ""`, `--max-rounds 2000` (`4,000` max games), `--concurrency 8`, `--seed 202611601`, `--elo0 0.0`, `--elo1 5.0` (`alpha=0.05`, `beta=0.05`, `model=normalized`).
  - **Safety & Pre-Run Declaration:** Writes `declaration_<name>.json` before game 1; when `--tc` is supplied (e.g., `--tc 6+0.06` with `--exe C:\nnue-lab\runs\forge\engines\v3-r15dsg-sp-clang\forge.exe` and `--concurrency 7`), writes `C:\nnue-lab\neon\CLOCK_MATCH_RUNNING` before `fastchess` and unlinks it in `finally:` (`lines 166–173`).
  - **Required Clock Calibration (`OPUS_TO_NEON.md:3086–3089`):**
    - Opus notes that *"A 50k SPRT is a filter only"* and warns that an equal-time SPRT `[0, 5]` at `6+0.06` requires **~`13k` games (~`10 h` at `concurrency=7`)** when true Elo is near `0` or `+5` (and more in between), whereas `run_lmr_deeper_sprt.py`'s default `--max-rounds 2000` caps at `4,000` games.
    - Accordingly, before launching on an **idle PC (GPU + CPU idle)**, declare TC, bounds, and game cap explicitly using either wider SPRT bounds **`[0, 10]`** (~`3k`–`4k` games) or a **fixed `2,000`-game clock match at `6+0.06`** (`concurrency=7`) to get an answer within hours.

### Step 2 — Clean Idle Per-Patch NPS Isolation (`bench_per_patch_nps.py`)
- **Script:** `C:\nnue-lab\neon\forge_fixes\bench_per_patch_nps.py`
  - **Current Status:** `C:\nnue-lab\neon\forge_fixes\CLEAN_IDLE_PER_PATCH_NPS.json` **does not exist yet** (`Exists: False`), as GPU (`task-7697`) and CPU (`task-7698`) jobs are currently active.
  - **Protocol:** Builds single-patch Clang ThinLTO+PGO executables (profiled on `r0067` + all `45` live `v3_uci_options`) and runs **`5x` interleaved `bench 15`** (reversing order on odd rounds) across **`7` configurations**:
    1. `live_pgo_r0067` (`v3-r15dsg-sp-clang/forge.exe` baseline)
    2. `live_pgo_LmrDeeper` (same live exe + `LmrDeeperShallower=true`, zero C++ diff)
    3. `SF13_alone_pgo` (`SF13_qs_evasion_pruning.patch` alone)
    4. `SF8_alone_pgo` (`SF8_conthist_6ply.patch` alone)
    5. `W2_proto_1_alone_pgo` (`proto_1_corrhist_minor.patch` alone)
    6. `V3Pv3_alone_r0067_pgo` (`V3P_pairwise_psqt_fused_v3.patch` alone, PGO on `r0067`)
    7. `FORGE_OWNER_BUNDLE_PGO` (full 4-patch dual-net PGO bundle + `LmrDeeperShallower=true`)
  - **Safety:** Sets `C:\nnue-lab\neon\CLOCK_MATCH_RUNNING` in `try/finally` (`lines 124–134`) and must only benchmark when both GPU and CPU are 100% idle.
  - **Decision Use:** Identifies which patch(es) account for the `0.934x` (`-6.60%`) bundle NPS tax before queuing individual `250k` / `6+0.06` tests for `SF13`, `SF8`, and `proto_1`.

### Step 3 — Conditional Server-Day Follow-Up (`V3P` + Margin Retuning)
- When `V3P` / `G3`-type `1024w` Pairwise+PSQT nets return on the `2B`-position server day (`OPUS_TO_NEON.md:3012,3085`), retune the `45` search margins specifically on the new architecture rather than reusing `r0067` margins (`15 Nov` margin-transfer lesson).

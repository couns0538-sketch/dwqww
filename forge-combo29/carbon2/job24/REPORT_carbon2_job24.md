# REPORT — `carbon2` Job 24: Stack `M` (`G + 08_G4 + 12_v3_refresh_fuse`) Two-Build Ablation (`Part M`) and `06_G2` LOO (`Part L`)

- **Branch:** `for-fable-and-opus/carbon2-work` (committed and pushed after every step; no engine source modified in-tree; text files only under `forge-combo29/carbon2/job24/`; **no pull request opened**).

---

## 1. Step 0 and Known Answers of Every New Build (`step0_and_M_known_answers_raw.txt`)

- **Compiler, Linker, and Recipe:** `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`), `llvm-profdata-18`, `-march=sapphirerapids`, identical 2-`.profraw` SP-PGO recipe as Jobs 21–23 (`bench 11/13/16` with `net768.fnn3` and only `CuckooRep=true`, `HistRework=2`, `TtPruneV2=true`, `CorrHistV2=true`, merged with `60` disjoint SP games `5,531` searches, `18,059,934` nodes, `trace=1646ce4566de2f40`).
- **Reference Builds:** `kF_sp_1` (`sha256=6ac9c36c...`), `kF_sp_2` (`sha256=7ef7c7e3...`), `bld_sp_r15d_1` (`sha256=79458908...`).
- **Three New Builds (all at exact `38`-character paths, verified on all `7` known answers in fresh processes before timing):**

| New Build | Binary Path (`len=38`) | Binary `sha256` | No-Opts `bench 11 / 13 / perft 5` | `PC20+net768` `bench 11 / 13` | Job 20 `60` Games (`searches` / `trace`) |
|---|---|---|---|---|---|
| **`M_1`** | `/tmp/carbon2_job24/bld_sp_stkM_1/forge` | `90fd6fe028928deea7b1e258075dd590f682d461f6d30129670ba48b07d15fed` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| **`M_2`** | `/tmp/carbon2_job24/bld_sp_stkM_2/forge` | `e11ecd116a38762a6fbebc2f807f4141105dbf058fccdcfae89bb1f2e8403c29` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| **`L1: kF - 06_G2`** | `/tmp/carbon2_job24/bld_sp_loo06a/forge` | `528b3a08e3bc59e16195cbf2d1569fab740d3d001f1af8f8805d307dc8e30e26` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |

---

## 2. Standalone Prediction Graded (`prediction_job24.txt`, commit `7cc5649c3`)

Committed alone and pushed after `M_1`/`M_2` known answers and before `M1` (unmodified since commit; no time or commit id inside):
- **`M1` (`A = kF_sp_1`, `B = M_1`) pooled CPU ratio:** predicted `[1.0120, 1.0260]`, reading `PAYS` -> measured **`1.0257`**, reading **`PAYS`** (**MET**).
- **`M2` (`A = kF_sp_2`, `B = M_2`) pooled CPU ratio:** predicted `[1.0120, 1.0260]`, reading `PAYS` -> measured **`1.0281`**, reading **`PAYS`** (**reading MET; pooled `0.0021` above `1.0260` upper bound**).
- **`M1/M2` group reading:** predicted **`the REST still PAYS`** -> measured **`the REST still PAYS`** (**MET**).
- **`R1` (`A = M_1`, `B = bld_sp_r15d_1`) pooled CPU ratio:** predicted `[1.0450, 1.0680]`, reading `PAYS` -> measured **`1.0493`**, reading **`PAYS`** (**MET**).

---

## 3. Part M: Stack `M` Definition, Rows `M1`, `M2`, `R1`, and Readings (`stack_M_on_r15d.patch.txt`, `partM1_...`, `partM2_...`, `partR1_...`)

- **Pieces of `M` and Why (`stack_M_on_r15d.patch.txt`, `1,304` lines vs `kF`'s `2,450` lines):**
  - **Order on `r15d`:** `04_S7` -> `08_G4` -> `11_stop_hot` -> `12_v3_refresh_fuse` -> `13_tt_avx512_fast_probe` (`5` pieces; minus `tidy`'s removed `friend struct S13TTTestAccess;` line).
  - **Why:** `G` from Job 22 is `04_S7 + 11_stop_hot + 13_tt_avx512_fast_probe`. In Job 23 Part L, **`12_v3_refresh_fuse` was the sole LOO piece reading `PAYS`** (`1.0170` pooled, `12/12` blocks $> 1$). `12_v3_refresh_fuse` requires **`08_G4`** as its single minimal dependency (`Board::piece_bitboards()` and the `king0`/`king1`/`key0`/`key1` dispatch in `Worker::static_evaluate_v3`). All **8** other pieces of `kF` (`01_S4`, `02_S5`, `03_S5_assert`, `05_G1`, `06_G2`, `07_G3`, `09_W1`, `10_W2`) are left out.
- **Timing Verification:** Across all `3 x 60 = 180` Part M runs (`144` timed + `36` warmups) on held-out `T`, **every single run gave `searches = 6,070`, `softnodes_sum = 26,711,499`, `trace = 937e1660561173af` (`0` dropped runs)**.
- **Declared Row Thresholds (`A = larger stack`, `B = smaller stack`):** `PAYS` iff `pooled CPU > 1.0116` and $\ge 10/12$ blocks $> 1$; `COSTS` iff `pooled CPU < 0.9884` and $\ge 10/12$ blocks $< 1$; `NOT SEEN` otherwise.

| Row (`A` larger vs `B` smaller) | 12 Block CPU Ratios (`B/A`) | Pooled CPU (`B/A`) | Median (`B/A`) | Mean & 95% $t$-CI ($\text{df}=11$) | Blocks $> 1$ | Row Reading |
|---|---|---:|---:|---|---:|---|
| **`M1`** (`A = kF_sp_1`, `B = M_1`) | `1.0304 1.0253 1.0326 1.0293 1.0152 1.0266 1.0306 1.0108 1.0284 1.0217 1.0281 1.0303` | **`1.0257`** (`196.1479s / 191.2257s`) | `1.0283` | `1.0258` **`[1.0215, 1.0300]`** | **`12 / 12`** *(wall `1.0265`, `12/12`)* | **`PAYS`** |
| **`M2`** (`A = kF_sp_2`, `B = M_2`) | `1.0230 1.0249 1.0181 1.0301 1.0318 1.0366 1.0390 1.0253 1.0206 1.0259 1.0338 1.0279` | **`1.0281`** (`196.3040s / 190.9441s`) | `1.0269` | `1.0281` **`[1.0240, 1.0321]`** | **`12 / 12`** *(wall `1.0280`, `12/12`)* | **`PAYS`** |
| **`R1`** (`A = M_1`, `B = bld_sp_r15d_1`) | `1.0502 1.0511 1.0585 1.0467 1.0365 1.0510 1.0475 1.0499 1.0469 1.0493 1.0487 1.0550` | **`1.0493`** (`204.3921s / 194.7931s`) | `1.0496` | `1.0493` **`[1.0459, 1.0526]`** | **`12 / 12`** *(wall `1.0458`, `12/12`)* | **`PAYS`** |

- **Part M Readings:**
  1. **`M` vs `r15d` (`R1`):** **`PAYS`** — `M` beats `r15d` by **`+4.93%` (`1.0493`, `12/12` blocks $> 1$, `[1.0459, 1.0526]`)**.
  2. **`kF` vs `M` (`M1` & `M2`):** **`the REST still PAYS`** — both `M1` (`1.0257`, `12/12`) and `M2` (`1.0281`, `12/12`) read **`PAYS`**, proving the remaining `MovePicker`/Board pieces (`01_S4`, `02_S5`, `05_G1`, `06_G2`, `07_G3`, `09_W1`, `10_W2`) jointly add another **`+2.57%` to `+2.81%`** on top of `M`!

---

## 4. Part L: Single-Piece Leave-One-Out Against `kF_sp_1` on Held-Out `T` (`partL1_loo06_G2_vs_kF1_T_raw.txt`)

`60` runs (`48` timed + `12` warmups), all `searches = 6,070`, `softnodes_sum = 26,711,499`, `trace = 937e1660561173af` (`0` dropped runs):

| Piece (`B = kF - piece` vs `A = kF_sp_1`) | Hunks Removed from `kF` | Pooled CPU (`B/A`) | Median (`B/A`) | Mean & 95% $t$-CI ($\text{df}=11$) | Blocks $> 1$ | Reading |
|---|---|---:|---:|---|---:|---|
| **`06_G2`** (`56` lines) | `src/board.cpp` (`Board::see_ge` fast no-recapture exit & unified slider/contact attacker init) | **`1.0024`** (`191.9306s / 191.4629s`) | `1.0027` | `1.0024` **`[1.0012, 1.0037]`** | `11 / 12` *(wall `1.0031`, `10/12`)* | **`NOT SEEN`** |

*(Per-block CPU ratios for `06_G2`: `1.0058 1.0027 1.0019 0.9995 1.0006 1.0027 1.0029 1.0057 1.0028 1.0028 1.0010 1.0009`.)*

---

## 5. What This Check Cannot See

The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is synthetic), its own self-play openings; pieces whose gain is below about 1 % (one build each cannot separate them from build noise).

---

## 6. Facts, Suspicions, What I Did Not Do, What I Am Not Sure About, Model Name & Timestamps

- **Facts:**
  1. **Exact multiplicative telescoping across `r15d -> M -> kF`:**
     - `r15d / M` (`R1`): **`1.0493`** (`+4.93%`, `12/12`, `[1.0459, 1.0526]`).
     - `M / kF` (`M1` / `M2`): **`1.0257`** (`12/12`, `[1.0215, 1.0300]`) and **`1.0281`** (`12/12`, `[1.0240, 1.0321]`), mean **`1.0269`** (`+2.69%`).
     - Product: $1.0493 \times 1.0257 = \mathbf{1.0763} \implies 1 / 1.0763 = \mathbf{0.9291}$, matching Job 21's direct `kF / r15d` measurement (`A2 = 0.9289`, `A3 = 0.9296`) to **`0.02%`**!
  2. Adding `08_G4 + 12_v3_refresh_fuse` to `G` closed the gap against `kF` from Job 22's `1.0334` (`G` vs `kF`) down to `1.0269` (`M` vs `kF`), while `R1 = 1.0493` confirms `M` (`5` pieces, `1,304` lines) captures ~`65%` of `kF`'s total speedup and the remaining `7` runtime `MovePicker`/Board pieces (`01_S4, 02_S5, 05_G1, 06_G2, 07_G3, 09_W1, 10_W2`) capture the other ~`35%` (`+2.69%`, **`the REST still PAYS`**).
  3. Across Jobs 21, 23, and 24, `7` individual pieces have now been LOO-tested against `kF_sp_1`: `12_v3_refresh_fuse` (`1.0170` `12/12` `PAYS`), `10_W2` (`1.0115` `10/12` `NOT SEEN`), `13_tt_avx512_fast_probe` (`1.0100` `11/12` `NOT SEEN`), `05_G1` (`1.0043` `8/12` `NOT SEEN`), `11_stop_hot` (`1.0033` `8/12` `NOT SEEN`), `06_G2` (`1.0024` `11/12` `NOT SEEN`), and `04_S7` (`0.9990` `7/12` `NOT SEEN`).
- **Suspicions:**
  - Since `05_G1` (`+0.43%`) and `06_G2` (`+0.24%`) account for `~+0.67%` of `M1`/`M2`'s `+2.69%` gap, the remaining **`~+2.0%`** sits in the **`MovePicker` + `KingLines` core (`01_S4 + 07_G3 + 09_W1 + 10_W2`)** (`10_W2` alone was already `1.0115`!). Meanwhile, **`04_S7` (`459` lines, `0.9990`)** is the clearest candidate to drop if the PC wants a smaller diff (`kF minus 04_S7` is `< 2,000` lines and keeps `100%` of `kF`'s speed!).
- **What I did not do:**
  - Stopped Part L before minute 70 (`23:13:39 UTC`), so LOO rows for the `5` coupled remaining pieces (`02_S5`, `07_G3`, `08_G4`, `09_W1`, `01_S4`) were **not done** (`03_S5_assert` skipped by rule as debug-only under `-DNDEBUG`).
  - Did not modify `kF`, touch engine source in-tree, or run strength matches.
- **What I am not sure about:**
  - Whether `09_W1` (which requires omitting `10_W2` with it, as `10_W2` rewrites `09_W1`'s `generate_quiets`) crosses `1.0116` (`PAYS`) by itself (~`1.5%–2.0%` expected) vs `01_S4 + 07_G3 + 02_S5`.
- **Runtime Model Name:** `Gemini 4 Carbon`
- **Timestamps (`forge-combo29/carbon2/job24/stamps.txt`):**
  - First line: `Wed Nov 18 10:07:07 PM UTC 2026 | job 24 received (FABLE_TO_carbon2_24.md); starting Step 0 & building M_1, M_2`
  - Last line: `Wed Nov 18 11:11:34 PM UTC 2026 | Stopping Part L before minute 70; writing REPORT_carbon2_job24.md before minute 80`
- **Verbatim output of `git status --short && ls -R forge-combo29/carbon2/job24` immediately before report commit:**

```text
 M forge-combo29/carbon2/job24/stamps.txt
?? forge-combo29/carbon2/job24/REPORT_carbon2_job24.md
forge-combo29/carbon2/job24:
partL1_loo06_G2_vs_kF1_T_raw.txt
partM1_M1_vs_kF1_T_raw.txt
partM2_M2_vs_kF2_T_raw.txt
partR1_r15d1_vs_M1_T_raw.txt
prediction_job24.txt
REPORT_carbon2_job24.md
stack_M_on_r15d.patch.txt
stamps.txt
step0_and_M_known_answers_raw.txt
```

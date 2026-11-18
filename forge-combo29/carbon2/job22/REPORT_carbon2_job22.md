# REPORT — `carbon2` Job 22: Group `G` vs Full `kF` Two-Build Ablation (`Part B2`)

- **Branch:** `for-fable-and-opus/carbon2-work` (committed and pushed after every step; no engine source modified in-tree; text files only under `forge-combo29/carbon2/job22/`; **no pull request opened**).

---

## 1. Step 0 and Known Answers of Every New Build (`step0_and_new_builds_known_answers_raw.txt`)

- **Compiler, Linker, and Recipe:** `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`), `llvm-profdata-18`, `-march=sapphirerapids`, identical 2-`.profraw` SP-PGO recipe as Job 21 (`bench 11/13/16` with `net768.fnn3` and only `CuckooRep=true`, `HistRework=2`, `TtPruneV2=true`, `CorrHistV2=true`, merged with `60` disjoint SP games `5,531` searches, `18,059,934` nodes, `trace=1646ce4566de2f40`).
- **Group `G` Definition (`group_G_on_r15d.patch.txt`, `842` lines):**
  - `G = r15d + 04_S7 + 11_stop_hot + 13_tt_avx512_fast_probe` (minus `tidy`'s removed `friend struct S13TTTestAccess;` line).
  - **Why `04_S7` is added as the single minimal dependency:** Piece `11` (`11_stop_hot.patch.txt` hunk 6, `src/uci.cpp:67`) modifies `void apply_position_sv(...)` -> `[[gnu::hot]] void apply_position_sv(...)`, which does not exist in plain `r15d` (`r15d` has `apply_position(Board&, istringstream&, ...)` and `04_S7` introduces `apply_position_sv`). Adding `04_S7` alone (`1` piece) lets `11_stop_hot` and `13_tt_avx512_fast_probe` compile unchanged while leaving out all **10** remaining pieces of `kF` (`01_S4`, `02_S5`, `03_S5_assert`, `05_G1`, `06_G2`, `07_G3`, `08_G4`, `09_W1`, `10_W2`, `12_v3_refresh_fuse`).
- **Path-Length Matching & Seven Known Answers (fresh process per check):**
  All builds sit at exact **`38`-character** binary paths matching `kF_sp_1` (`/tmp/carbon2_job17/bld_sp_tidy_1/forge`, `sha256=6ac9c36ceae1c8c79721b84bd5d395dd967c41723586a0b3e3cdcc1a7b5f7091`) and `kF_sp_2` (`/tmp/carbon2_job17/bld_sp_tidy_2/forge`, `sha256=7ef7c7e32820eb30757cdcde8b292860dda4d1f499b842e4537bfbebbd9104de`):

| New Build | Binary Path (`len=38`) | Binary `sha256` | No-Opts `bench 11 / 13 / perft 5` | `PC20+net768` `bench 11 / 13` | Job 20 `60` Games (`searches` / `trace`) |
|---|---|---|---|---|---|
| **`G_1`** | `/tmp/carbon2_job22/bld_sp_grpG_1/forge` | `b4baf7f2f6d08938ad68d1054ab9e0a9b001d3c1924bdef0028594ef29117232` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| **`G_2`** | `/tmp/carbon2_job22/bld_sp_grpG_2/forge` | `0e32c3ac50307724372a254cbe7edad25896b736e6462b9efdfacd9baebbb726` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |

---

## 2. Standalone Prediction Graded (`prediction_job22.txt`, commit `66535be36`)

Committed alone and pushed after `G_1`/`G_2` known answers and before `B2a` (unmodified since commit; no time or commit id inside):
- **`B2a` (`B = G_1` vs `A = kF_sp_1`) pooled CPU ratio:** predicted `[1.0300, 1.0620]`, reading `PAYS` -> measured **`1.0332`**, reading **`PAYS`** (**MET**).
- **`B2b` (`B = G_2` vs `A = kF_sp_2`) pooled CPU ratio:** predicted `[1.0300, 1.0620]`, reading `PAYS` -> measured **`1.0335`**, reading **`PAYS`** (**MET**).
- **Part B2 reading for the REST of `kF`:** predicted **`PAYS`** -> measured **`PAYS`** (**MET**).
- **Planned Part B3 rows (`04_S7`, `12_v3_refresh_fuse`, `05_G1`, `06_G2`):** **Not done** (ungraded; stopped before Part B3 per the minute-70/80 budget rule).

---

## 3. Part B2: Group `G` vs `kF` on Held-Out Workload `T` (`partB2a_G1_vs_kF1_T_raw.txt`, `partB2b_G2_vs_kF2_T_raw.txt`)

- **Workload & Design:** Identical to Job 21 (`60` held-out `T` roots, `PC20 + net768.fnn3`, `Threads 1`, `Hash 16`, `go softnodes 2000`, engine pinned to `CPU 3`, harness on `CPU 1`, `12` blocks `[W] ABBA` / `[W] BAAB` with `1` warmup left out per block). Across all `120` runs (`96` timed + `24` warmups), **every run gave `searches = 6,070`, `softnodes_sum = 26,711,499`, `trace = 937e1660561173af` (`0` dropped runs)**.
- **Declared Row Rule (`A = kF`, `B = G` without the rest of `kF`):** `PAYS` iff `pooled CPU > 1.0116` and $\ge 10/12$ blocks $> 1$; `COSTS` iff `pooled CPU < 0.9884` and $\ge 10/12$ blocks $< 1$; `NOT SEEN` otherwise.

### Table B2a — `B = G_1` vs `A = kF_sp_1` (`partB2a_G1_vs_kF1_T_raw.txt`)
- **CPU (`B/A`) 12 block ratios:** `1.0321 1.0441 1.0022 1.0418 1.0375 1.0290 1.0307 1.0413 1.0383 1.0342 1.0398 1.0299`
  - **Pooled (`sumB/sumA`):** **`1.0332`** (`203.6940s / 197.1477s`, `> 1.0116`) | **Median:** `1.0359` | **Mean & 95% $t$-CI ($\text{df}=11$):** `1.0334` **`[1.0264, 1.0404]`** | **Blocks $> 1$:** **`12 / 12`** | **Row reading:** **`PAYS`**
- **Wall (`B/A`) 12 block ratios:** `1.0298 1.0442 1.0050 1.0460 1.0375 1.0342 1.0284 1.0435 1.0387 1.0357 1.0446 1.0260`
  - **Pooled:** `1.0343` (`213.2329s / 206.1681s`) | **Median:** `1.0366` | **Mean & 95% $t$-CI ($\text{df}=11$):** `1.0345` `[1.0272, 1.0417]` | **Blocks $> 1$:** **`12 / 12`**

### Table B2b — `B = G_2` vs `A = kF_sp_2` (`partB2b_G2_vs_kF2_T_raw.txt`)
- **CPU (`B/A`) 12 block ratios:** `1.0110 1.0385 1.0361 1.0376 1.0318 1.0420 1.0167 1.0544 1.0267 1.0327 1.0357 1.0389`
  - **Pooled (`sumB/sumA`):** **`1.0335`** (`205.5003s / 198.8484s`, `> 1.0116`) | **Median:** `1.0359` | **Mean & 95% $t$-CI ($\text{df}=11$):** `1.0335` **`[1.0263, 1.0407]`** | **Blocks $> 1$:** **`12 / 12`** | **Row reading:** **`PAYS`**
- **Wall (`B/A`) 12 block ratios:** `1.0056 1.0443 1.0340 1.0404 1.0373 1.0376 1.0156 1.0569 1.0293 1.0288 1.0359 1.0364`
  - **Pooled:** `1.0335` (`215.0571s / 208.0959s`) | **Median:** `1.0361` | **Mean & 95% $t$-CI ($\text{df}=11$):** `1.0335` `[1.0251, 1.0418]` | **Blocks $> 1$:** **`12 / 12`**

### Part B2 Group Reading for the REST of `kF`: **`PAYS`**
Both `B2a` (`1.0332`, `12/12` blocks $> 1$) and `B2b` (`1.0335`, `12/12` blocks $> 1$) read **`PAYS`**. Leaving out the other `10` pieces of `kF` slows the engine down by **`+3.32%` / `+3.35%` CPU** (`+3.59%` median on both arms).

---

## 4. Part B3: Single-Piece Leave-One-Out Status

- **`03_S5_assert`:** **Skipped by rule** — every added line in `03_S5_assert.patch.txt` sits inside `#ifndef NDEBUG` (plus `#include <cassert>`), which compiles to zero instructions under `-DNDEBUG` in both our and the PC's release recipe.
- **Remaining pieces (`04_S7`, `12_v3_refresh_fuse`, `05_G1`, `06_G2`, `07_G3`, `08_G4`, `09_W1`, `10_W2`, `01_S4`, `02_S5`):** **Not done** — `B2b` finished at `20:21:23 UTC` (`74` minutes after reading `FABLE_TO_carbon2_22.md` at `19:07:10 UTC`, and `56` minutes into `stamps.txt` with a single LOO build+12-block timing requiring `~11` minutes), so per *"Part B3 (while it can end before minute 70)"* and *"Minute 80 stops the work: write what is done; a part not done is listed as not done, never filled"*, we stopped new runs immediately after `B2b`.

---

## 5. What This Check Cannot See

The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is synthetic), its own self-play openings (8 random plies from the start position); pieces whose gain is below about 1 % (one build each cannot separate them from build noise).

---

## 6. Facts, Suspicions, What I Did Not Do, What I Am Not Sure About, Model Name & Timestamps

- **Facts:**
  1. Across two independent SP-PGO build pairs at matched `38`-character binary paths (`G_1` vs `kF_sp_1` and `G_2` vs `kF_sp_2`), removing the `10` non-`G` pieces (`01_S4`, `02_S5`, `03_S5_assert`, `05_G1..10_W2`, `12_v3_refresh_fuse`) increases CPU time on held-out `T` by **`+3.32%` (`B2a = 1.0332`, `12/12` blocks $> 1$, `[1.0264, 1.0404]`)** and **`+3.35%` (`B2b = 1.0335`, `12/12` blocks $> 1$, `[1.0263, 1.0407]`)** -> **`PAYS`**.
  2. Combining Job 21 Part A (`r15d / kF = 1 / 0.9289 = 1.0765` on arm 1, `1 / 0.9296 = 1.0757` on arm 2; mean **`+7.61%`**) with Job 22 Part B2 (`G / kF = 1.0334` mean; **`+3.34%`**) partitions `kF`'s SP-PGO gain cleanly into two roughly equal halves, **both of which pay by `> 3%`**:
     - **Group `G` (`04_S7 + 11_stop_hot + 13_tt_avx512_fast_probe`):** accounts for $1.0761 / 1.0334 \approx$ **`1.0413` (`+4.13%` over `r15d`)**.
     - **The REST of `kF` (`01_S4, 02_S5, 05_G1..10_W2, 12_v3_refresh_fuse`):** accounts for **`1.0334` (`+3.34%` over `G`)**.
  3. Under Job 22's strict 1-build threshold (`> 1.0116` and $\ge 10/12$ blocks $> 1$), Job 21's two single-build LOO rows read **`NOT SEEN`** (`13_tt_avx512_fast_probe`: `1.0100` pooled, `11/12` $> 1$, `0.0016` below `1.0116`; `11_stop_hot`: `1.0033` pooled, `8/12` $> 1$).
- **Suspicions:**
  - Because `kF`'s `+7.6%` total speedup comes from `12` non-debug pieces averaging `~0.6%` each (`+3.34%` across the `9` runtime pieces outside `G`), individual single-build LOO rows in Part B3 are structurally unlikely to cross the `> 1.0116` (`+1.16%`) single-build noise gate one piece at a time, whereas **sub-group two-build tests** (e.g. splitting the REST of `kF` into the **NNUE v3 group `08_G4 + 12_v3_refresh_fuse`** vs the **`MovePicker`/Board group `01_S4 + 02_S5 + 05_G1 + 06_G2 + 07_G3 + 09_W1 + 10_W2`**) each target `~1.5%–2.0%` and can clear `1.0116` cleanly with two builds per arm.
- **What I did not do:**
  - Did not run Part B3 single-piece LOO builds/timings (stopped after `B2b` per the minute-70/80 budget rule).
  - Skipped debug-only `03_S5_assert` (no-op under `-DNDEBUG`).
  - Did not modify `kF`, touch engine source in-tree, or run strength matches.
- **What I am not sure about:**
  - Within Group `G`'s implied `~+4.1%` gain over `r15d` (`1.0761 / 1.0334`), how much is carried by `04_S7` (`string_view` UCI + `Worker::clear` `memset`) vs `13_tt_avx512_fast_probe` (`~1.0%` in Job 21) vs `11_stop_hot` (`~0.3%` in Job 21), and whether any minor cross-term exists between `G_1`/`G_2` and `bld_sp_r15d_1`/`_2` across separate hours of VM execution.
  - How the `+3.34%` of the REST of `kF` divides between NNUE v3 (`08_G4 + 12`) and `MovePicker`/Board (`01, 02, 05, 06, 07, 09, 10`) without a two-build sub-group split.
- **Runtime Model Name:** `Gemini 4 Carbon`
- **Timestamps (`forge-combo29/carbon2/job22/stamps.txt`):**
  - First line: `Wed Nov 18 07:25:39 PM UTC 2026 | job 22 received (FABLE_TO_carbon2_22.md); inspecting pieces 13 & 11 against plain r15d`
  - Last line: `Wed Nov 18 08:28:14 PM UTC 2026 | Stopping before Part B3 per minute-70/80 budget rule; writing REPORT_carbon2_job22.md`
- **Verbatim output of `git status --short && ls -R forge-combo29/carbon2/job22` immediately before report commit:**

```text
 M forge-combo29/carbon2/job22/stamps.txt
?? forge-combo29/carbon2/job22/REPORT_carbon2_job22.md
forge-combo29/carbon2/job22:
group_G_on_r15d.patch.txt
partB2a_G1_vs_kF1_T_raw.txt
partB2b_G2_vs_kF2_T_raw.txt
prediction_job22.txt
REPORT_carbon2_job22.md
stamps.txt
step0_and_new_builds_known_answers_raw.txt
```

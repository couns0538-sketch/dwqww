# Job 27 Report — `kF` Against `r15d` Under the Hard Node Limit (`go nodes 20000`) Beside the Soft Limit (`go softnodes 2000`)

## 1. Step 0, `T20`'s Signature, and the Identity of Every Run

### Step 0 & Existing Build Verification (`forge-combo29/carbon2/job27/step0_and_T20_signature_raw.txt`)
- **Toolchain:** `Ubuntu clang version 18.1.3 (1ubuntu1)` + `Ubuntu LLD 18.1.3` (`--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`, ThinLTO, SP-PGO, `-march=sapphirerapids`, `-DFORGE_USE_AVX512=1`). No new builds were compiled; all four existing binaries from Job 11 (`r15d`) and Job 17 (`kF`) were verified as-is:

| Build | Path | `sha256` | Default `bench 11 / 13 / perft 5` | `PC20 + net768` `bench 11 / 13` | Step 0 `T20` Signature (`searches/nodes/trace`) | Step 0 `T20` CPU |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `kF_sp_1` | `/tmp/carbon2_job17/bld_sp_tidy_1/forge` | `6ac9c36c...5f7091` | `312,866 / 862,329 / 4,865,609` | `882,074 / 4,275,906` | `824/8867455/e4fc7111a86493e5` | `5.0768s` |
| `bld_sp_r15d_1` | `/tmp/carbon2_job11/bld_sp_r15d_1/forge` | `79458908...580c7` | `312,866 / 862,329 / 4,865,609` | `882,074 / 4,275,906` | `824/8867455/e4fc7111a86493e5` | `5.5753s` |
| `kF_sp_2` | `/tmp/carbon2_job17/bld_sp_tidy_2/forge` | `7ef7c7e3...bd9104de` | `312,866 / 862,329 / 4,865,609` | `882,074 / 4,275,906` | `824/8867455/e4fc7111a86493e5` | `5.1515s` |
| `bld_sp_r15d_2` | `/tmp/carbon2_job11/bld_sp_r15d_2/forge` | `00b44d65...57ee62` | `312,866 / 862,329 / 4,865,609` | `882,074 / 4,275,906` | `824/8867455/e4fc7111a86493e5` | `5.4738s` |

### `T20` Signature & Identity of Every Run Across Job 27 (`264 / 264` Runs Identical Within Workload, `0` Dropped Blocks)
- **Workload `T20` definition:** First `15` roots (`01..15` = `L007..L042`) of `forge-combo29/carbon2/job21/workload_T_60_roots.txt` with `PC20 + net768.fnn3`, `Threads 1`, `Hash 16`, `ucinewgame` before each game, and every search set to `go nodes 20000` in place of `go softnodes 2000`.
- **Signature of `T20` (written from the first `kF_sp_1` run):** **`824` searches, `8,867,455` node sum (`last_info_nodes`), trace `e4fc7111a86493e5` (`824/8867455/e4fc7111a86493e5`)**.
- **Identity of every engine run executed in Job 27 (`264` runs total across Step 0, `C27`, `S1`, `H1`, `S2`, `H2`):**
  1. **`T20` (`go nodes 20000`) — `134 / 134` runs identical (`824/8867455/e4fc7111a86493e5`):**
     - `4` Step 0 runs (`kF_sp_1`, `bld_sp_r15d_1`, `kF_sp_2`, `bld_sp_r15d_2`),
     - `10` `C27` A-runs (`2` warm-up runs in blocks `01, 03` + `8` measured legs across blocks `01..04`),
     - `60` `H1` runs (`12` warm-up runs + `48` measured legs across `kF_sp_1` and `bld_sp_r15d_1`),
     - `60` `H2` runs (`12` warm-up runs + `48` measured legs across `kF_sp_2` and `bld_sp_r15d_2`).
  2. **`C27` B-runs (`go nodes 22000` on `T20`) — `10 / 10` runs identical (`1119/12621749/00390fcca474b884`):**
     - `2` warm-up runs in blocks `02, 04` + `8` measured legs across blocks `01..04` (`kF_sp_1`).
  3. **`T` (`go softnodes 2000`, all `60` roots) — `120 / 120` runs identical (`6070/26711499/937e1660561173af`):**
     - `60` `S1` runs (`12` warm-up runs + `48` measured legs across `kF_sp_1` and `bld_sp_r15d_1`),
     - `60` `S2` runs (`12` warm-up runs + `48` measured legs across `kF_sp_2` and `bld_sp_r15d_2`).
  - **Dropped blocks across all runs:** **`0`** (`0` signature mismatches anywhere in Job 27).

---

## 2. Control `C27` (`forge-combo29/carbon2/job27/control_C27_4blocks_raw.txt`)

- **Design:** `4` blocks (`odd = ABBA`, `even = BAAB`, `+1` warm-up run per block left out; harness pinned to CPU `1`, engine pinned to sibling-free CPU `3`) on `T20`, with `A = kF_sp_1` (`go nodes 20000`, signature `824/8867455/e4fc7111a86493e5`) and `B = kF_sp_1` (`go nodes 22000`, signature `1119/12621749/00390fcca474b884`).
- **Results (`B / A`):**
  - **Engine CPU:** `4` block ratios = `1.4715, 1.4793, 1.4723, 1.4744` | **`pooled = 1.4744`** (`60.6761s / 41.1537s`) | `median = 1.4734` | `mean = 1.4744`, 95% $t$-CI (`df=3`) **`[1.4688, 1.4800]`** (`sd = 0.0035`, `se = 0.0018`) | **`4 / 4` blocks above `1`**.
  - **Wall time:** `4` block ratios = `1.4701, 1.4774, 1.4728, 1.4697` | `pooled = 1.4725` (`61.8207s / 41.9830s`) | `median = 1.4715` | `mean = 1.4725`, 95% $t$-CI (`df=3`) `[1.4669, 1.4781]` (`sd = 0.0035`, `se = 0.0018`) | `4 / 4` blocks above `1`.
- **Gate check:** `pooled CPU = 1.4744 > 1.0116` with `4 / 4` blocks above `1` -> **PASSES** (proceeded to prediction and `S1..H2`).

---

## 3. Standalone Prediction Graded (`forge-combo29/carbon2/job27/prediction_job27.txt`, Commit `d9628655d`)

- `forge-combo29/carbon2/job27/prediction_job27.txt` was committed **alone** (`1` file changed in commit `d9628655d`) and pushed after Step 0, `T20` signature verification, and Control `C27`, and before `S1` started. It was never edited afterwards and contains no date, time, or commit id.

| Item | Pre-Committed Prediction (`prediction_job27.txt`) | Measured Result | Grade |
| :--- | :--- | :--- | :--- |
| **`S1`** (`bld_sp_r15d_1 / kF_sp_1` on `T`) | Pooled CPU in `[1.0600, 1.0900]`, reading **`PAYS`** | Pooled CPU = **`1.0768`**, `12/12` `> 1`, **`PAYS`** | **MET** |
| **`H1`** (`bld_sp_r15d_1 / kF_sp_1` on `T20`) | Pooled CPU in `[1.0550, 1.0950]`, reading **`PAYS`** | Pooled CPU = **`1.0777`**, `12/12` `> 1`, **`PAYS`** | **MET** |
| **`S2`** (`bld_sp_r15d_2 / kF_sp_2` on `T`) | Pooled CPU in `[1.0600, 1.0900]`, reading **`PAYS`** | Pooled CPU = **`1.0792`**, `12/12` `> 1`, **`PAYS`** | **MET** |
| **`H2`** (`bld_sp_r15d_2 / kF_sp_2` on `T20`) | Pooled CPU in `[1.0550, 1.0950]`, reading **`PAYS`** | Pooled CPU = **`1.0780`**, `12/12` `> 1`, **`PAYS`** | **MET** |
| **`HARD AGAIN or NOT`** (`H1` vs `S1`, `H2` vs `S2`) | **`same within the error`** on both build pairs | **`same within the error`** on both build pairs | **MET** |

---

## 4. `S1`, `H1`, `S2`, `H2`: Table, Row Readings, and `HARD AGAIN or NOT`

- **Convention:** In all four rows, **`A = kF`** and **`B = r15d`**, so `B / A > 1` means `kF` uses less CPU / wall time than `r15d`. Each row is `12` interleaved blocks (`odd = ABBA`, `even = BAAB`, `+1` warm-up run per block left out; harness on CPU `1`, engine on CPU `3`; `0` dropped blocks).
- **Raw files:** `row_S1_r15d1_vs_kF1_T_raw.txt`, `row_H1_r15d1_vs_kF1_T20_raw.txt`, `row_S2_r15d2_vs_kF2_T_raw.txt`, `row_H2_r15d2_vs_kF2_T20_raw.txt` in `forge-combo29/carbon2/job27/`.

### Unified Timing Table (`12` Block Ratios `B/A`, Pooled, Median, Mean & 95% $t$-Interval, Blocks `> 1`; CPU and Wall)

| Row (Metric) | 12 Block Ratios (`B / A`, Blocks `01..12`) | Pooled (`sumB / sumA`) | Median | Mean & 95% $t$-Interval (`df=11`) | Blocks `> 1` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`S1` (CPU)**<br>`r15d_1 / kF_sp_1` on `T` | `1.0748 1.0799 1.0767 1.0784 1.0744 1.0745`<br>`1.0779 1.0800 1.0767 1.0765 1.0779 1.0733` | **`1.0768`**<br>(`203.6814s / 189.1619s`) | `1.0767` | **`1.0768 [1.0754, 1.0781]`**<br>(`sd=0.0022, se=0.0006`) | **`12 / 12`** |
| **`S1` (Wall)** | `1.0730 1.0778 1.0734 1.0762 1.0704 1.0706`<br>`1.0749 1.0773 1.0747 1.0742 1.0774 1.0697` | `1.0741`<br>(`212.5396s / 197.8711s`) | `1.0745` | `1.0741 [1.0723, 1.0759]`<br>(`sd=0.0028, se=0.0008`) | `12 / 12` |
| **`H1` (CPU)**<br>`r15d_1 / kF_sp_1` on `T20` | `1.0742 1.0789 1.0734 1.0838 1.0736 1.0786`<br>`1.0784 1.0779 1.0781 1.0751 1.0766 1.0836` | **`1.0777`**<br>(`130.1386s / 120.7565s`) | `1.0780` | **`1.0777 [1.0755, 1.0799]`**<br>(`sd=0.0034, se=0.0010`) | **`12 / 12`** |
| **`H1` (Wall)** | `1.0725 1.0770 1.0709 1.0816 1.0739 1.0760`<br>`1.0770 1.0763 1.0764 1.0723 1.0745 1.0804` | `1.0757`<br>(`132.8265s / 123.4751s`) | `1.0762` | `1.0757 [1.0737, 1.0778]`<br>(`sd=0.0032, se=0.0009`) | `12 / 12` |
| **`S2` (CPU)**<br>`r15d_2 / kF_sp_2` on `T` | `1.0772 1.0811 1.0797 1.0809 1.0770 1.0797`<br>`1.0764 1.0805 1.0785 1.0811 1.0802 1.0786` | **`1.0792`**<br>(`203.9196s / 188.9472s`) | `1.0797` | **`1.0792 [1.0782, 1.0803]`**<br>(`sd=0.0017, se=0.0005`) | **`12 / 12`** |
| **`S2` (Wall)** | `1.0755 1.0777 1.0806 1.0792 1.0765 1.0732`<br>`1.0726 1.0758 1.0755 1.0780 1.0775 1.0761` | `1.0765`<br>(`211.8870s / 196.8294s`) | `1.0763` | `1.0765 [1.0751, 1.0780]`<br>(`sd=0.0023, se=0.0007`) | `12 / 12` |
| **`H2` (CPU)**<br>`r15d_2 / kF_sp_2` on `T20` | `1.0753 1.0772 1.0779 1.0785 1.0801 1.0798`<br>`1.0758 1.0787 1.0788 1.0786 1.0792 1.0762` | **`1.0780`**<br>(`130.4605s / 121.0180s`) | `1.0786` | **`1.0780 [1.0770, 1.0790]`**<br>(`sd=0.0016, se=0.0005`) | **`12 / 12`** |
| **`H2` (Wall)** | `1.0757 1.0757 1.0755 1.0766 1.0775 1.0774`<br>`1.0742 1.0777 1.0772 1.0768 1.0769 1.0745` | `1.0763`<br>(`133.1405s / 123.7019s`) | `1.0767` | `1.0763 [1.0756, 1.0770]`<br>(`sd=0.0012, se=0.0003`) | `12 / 12` |

### Row Readings (`PAYS` when `pooled CPU > 1.0116` and `>= 10 / 12` blocks `> 1`; `COSTS` when `< 0.9884` and `>= 10 / 12` `< 1`; `NOT SEEN` otherwise)
- **`S1`:** `pooled CPU = 1.0768 > 1.0116`, `12 / 12` blocks `> 1` -> **`PAYS`**
- **`H1`:** `pooled CPU = 1.0777 > 1.0116`, `12 / 12` blocks `> 1` -> **`PAYS`**
- **`S2`:** `pooled CPU = 1.0792 > 1.0116`, `12 / 12` blocks `> 1` -> **`PAYS`**
- **`H2`:** `pooled CPU = 1.0780 > 1.0116`, `12 / 12` blocks `> 1` -> **`PAYS`**

### `HARD AGAIN or NOT` (Per Build: `H1` Against `S1`, `H2` Against `S2`)
- **Build 1 (`H1` against `S1`):**
  - `H1` 95% $t$-interval of the CPU mean: **`[1.0755, 1.0799]`**
  - `S1` 95% $t$-interval of the CPU mean: **`[1.0754, 1.0781]`**
  - The two 95% $t$-intervals overlap on **`[1.0755, 1.0781]`**.
  - Difference of pooled CPU ratios: **`pooled(H1) - pooled(S1) = 1.0777 - 1.0768 = +0.0009`** (unrounded: `1.077694 - 1.076757 = +0.000937`).
  - Reading: **`same within the error`**.
- **Build 2 (`H2` against `S2`):**
  - `H2` 95% $t$-interval of the CPU mean: **`[1.0770, 1.0790]`**
  - `S2` 95% $t$-interval of the CPU mean: **`[1.0782, 1.0803]`**
  - The two 95% $t$-intervals overlap on **`[1.0782, 1.0790]`**.
  - Difference of pooled CPU ratios: **`pooled(H2) - pooled(S2) = 1.0780 - 1.0792 = -0.0012`** (unrounded: `1.078026 - 1.079241 = -0.001216`).
  - Reading: **`same within the error`**.

---

## WHAT THIS CHECK CANNOT SEE

The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is synthetic), its own openings, go nodes 50000 (the gate: T20 at 20,000 only), gains below about 1 % (two builds can separate them only when both agree).

---

## Facts, Suspicions, What I Did Not Do, What I Am Not Sure About, Model Name, Stamps & Status

### Facts (Directly Evidenced by Job 27 Raw Files)
1. **Exact Search Equivalence at `go nodes 20000` (`T20`):** Across all four builds (`kF_sp_1`, `bld_sp_r15d_1`, `kF_sp_2`, `bld_sp_r15d_2`) and all `134` `T20` runs in Job 27 (`4` Step 0 runs + `10` `C27` A-runs + `60` `H1` runs + `60` `H2` runs), `kF` and `r15d` produced the exact same signature **`824/8867455/e4fc7111a86493e5`** with `0` mismatches.
2. **`kF`'s Speedup Holds Unchanged Under `go nodes 20000`:** In the same session on the pinned-CPU timing harness, `r15d / kF` pooled CPU was **`1.0768`** (`S1`, soft) vs **`1.0777`** (`H1`, hard, `diff = +0.0009`) on build pair 1, and **`1.0792`** (`S2`, soft) vs **`1.0780`** (`H2`, hard, `diff = -0.0012`) on build pair 2, with `12 / 12` blocks above `1` in all four rows (`48 / 48` total blocks). Both build pairs read **`same within the error`**, and their small pooled differences (`+0.09%` and `-0.12%`) have opposite signs and cancel to within `0.02%` when averaged across the two build pairs (`1.07785` hard vs `1.07800` soft).
3. **Why `C27` (`go nodes 22000` vs `go nodes 20000` on `T20`) Reads `1.4744x`:** Because `T20` plays whole self-play games from the `15` starting roots (`L007..L042`), raising the hard cap from `20,000` to `22,000` nodes changes move choices once a search finishes an additional iteration or fail-high/low within those extra `2,000` nodes, steering those deterministic games from `824` total searches (`8,867,455` last-completed-iteration `info` nodes) to `1,119` total searches (`12,621,749` `info` nodes, `1.4234x` reported `info` nodes and `1.4744x` CPU), identically across all `10 / 10` `C27` B-runs (`1119/12621749/00390fcca474b884`).
4. **Wall-Clock Agreement:** Wall-clock `B / A` ratios track engine CPU closely across all four rows (`S1 = 1.0741`, `H1 = 1.0757`, `S2 = 1.0765`, `H2 = 1.0763`, `12 / 12` blocks `> 1` in each), diluted slightly by fixed pipe/process-spawn overhead (smaller dilution on `T20`, where `15` games spawn `1` engine process and send `824` commands in `~5.1s` vs `6,070` commands in `~8.0s` on `T`).

### Suspicions (Mechanistic, Not Directly Proven Here)
1. **Why Deeper Searches (`~4.5x` Nodes/Search) Do Not Erode `kF`'s Gain:** Each major piece of `kF` (`13_tt` 4-slot cluster/aging layout, `12_v3_refresh_fuse` + `08_G4` NNUE accumulator refresh/copy-make fusion, `10_W2` + `09_W1` vectorized FT update, `11_stop_hot` hot-path stop check) accelerates per-node operations (`Worker::search`, `qsearch`, `TT::probe/store`, and NNUE accumulator updates) whose cost share remains roughly scale-invariant between `~4,400` nodes/search (`T`) and `20,000` nodes/search (`T20`) inside a `16 MB` hash table (`524,288` entries, well above `20,000` nodes/search).
2. **At `go nodes 50000` or Concurrent `16`-Engine Load on Zen 5:** At `50,000` nodes/search with `16` concurrent engines sharing L3/DRAM bandwidth on Zen 5, cache-line / TT footprint reductions (`13_tt` + fused NNUE refresh `12_v3_refresh_fuse`) could behave slightly differently than single-core Sapphire Rapids runs, which only the PC's own gate benchmark can directly observe.

### What I Did Not Do
- Did not recompile any binaries or modify any `.patch.txt` piece, engine source file, or `.fnn3` network file.
- Did not run `go nodes 50000`, strength matches, or any training workload.
- Did not switch branches or open a pull request.

### What I Am Not Sure About
- Whether `kF`'s speedup at the PC's gate limit (`go nodes 50000`) under `16`-engine concurrent memory contention on Windows Clang 23 / Zen 5 stays at `~1.078x` or shifts slightly due to shared-L3/DRAM pressure.

### Model Name
- `Gemini 4 Carbon`

### First & Last Lines of `forge-combo29/carbon2/job27/stamps.txt`
- **First line:** `Thu Nov 19 01:02:50 AM UTC 2026 | job 27 received (FABLE_TO_carbon2_27.md); starting Step 0, T20 signature, and Control C27`
- **Last line:** `Thu Nov 19 01:42:53 AM UTC 2026 | All Job 27 experiments complete; writing REPORT_carbon2_job27.md`

### Pre-Commit `git status --short && ls -R forge-combo29/carbon2/job27` (Literal Last Command Before Report Commit)

```text
 M forge-combo29/carbon2/job27/stamps.txt
?? forge-combo29/carbon2/job27/REPORT_carbon2_job27.md
forge-combo29/carbon2/job27:
control_C27_4blocks_raw.txt
prediction_job27.txt
REPORT_carbon2_job27.md
row_H1_r15d1_vs_kF1_T20_raw.txt
row_H2_r15d2_vs_kF2_T20_raw.txt
row_S1_r15d1_vs_kF1_T_raw.txt
row_S2_r15d2_vs_kF2_T_raw.txt
stamps.txt
step0_and_T20_signature_raw.txt
```

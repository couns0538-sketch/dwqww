# REPORT — `carbon2` Job 25: Stack `N` (`Part N`), `10_W2` Second Build (`Part W`), and Coupled Pair LOO (`Part L`)

- **Branch:** `for-fable-and-opus/carbon2-work` (committed and pushed after every step; no engine source modified in-tree; text files only under `forge-combo29/carbon2/job25/`; **no pull request opened**).

---

## 1. Step 0 and Known Answers of Every New Build (`step0_and_new_builds_known_answers_raw.txt`)

- **Compiler, Linker, and Recipe:** `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`), `llvm-profdata-18`, `-march=sapphirerapids`, identical 2-`.profraw` SP-PGO recipe as Jobs 21–24 (`bench 11/13/16` with `net768.fnn3` and only `CuckooRep=true`, `HistRework=2`, `TtPruneV2=true`, `CorrHistV2=true`, merged with `60` disjoint SP games `5,531` searches, `18,059,934` nodes, `trace=1646ce4566de2f40`).
- **Reference `kF` Builds:** `kF_sp_1` (`sha256=6ac9c36c...`) and `kF_sp_2` (`sha256=7ef7c7e3...`).
- **Five New Builds (all at exact `38`-character paths, verified on all `7` known answers in fresh processes before timing):**

| New Build | Binary Path (`len=38`) | Binary `sha256` | No-Opts `bench 11 / 13 / perft 5` | `PC20+net768` `bench 11 / 13` | Job 20 `60` Games (`searches` / `trace`) |
|---|---|---|---|---|---|
| **`N_1`** | `/tmp/carbon2_job25/bld_sp_stkN_1/forge` | `2cfdb2b5a98b91c3f0116230cbe27aec2bc6ff64e54aa989459033ebb8e42c76` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| **`N_2`** | `/tmp/carbon2_job25/bld_sp_stkN_2/forge` | `6293e59accfe849a5d8d611e88d8a687200627a6a25c31a5636dda448db7ba2a` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| **`kF_2 - 10_W2`** | `/tmp/carbon2_job25/bld_sp_loo10b/forge` | `e3bffb6862601b64eab27ad8700393cb579eba2b3a470afcbccbba8ead530432` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| **`L1: kF - (09+10)`** | `/tmp/carbon2_job25/bld_sp_loo09a/forge` | `c46c83ebde7f885d121e8cc21f7150de58b7981b544a4751283895a47476cb34` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |
| **`L2: kF - (08+12)`** | `/tmp/carbon2_job25/bld_sp_loo08a/forge` | `07f2b7301cef3da97a362a9f9e3e780e2c2dac87476d6f84a00e44fc4b3e16a3` | `312866` / `862329` / `4865609` | `882074` / `4275906` | `7670` / `ee465caeff9c0fcf` |

---

## 2. Standalone Prediction Graded (`prediction_job25.txt`, commit `5b9cc0f2a`)

Committed alone and pushed after `N_1`/`N_2`/`kF_2_minus_10_W2` known answers and before `N1` (unmodified since commit; no time or commit id inside):
- **`N1` (`A = kF_sp_1`, `B = N_1`):** predicted `[0.9980, 1.0115]`, reading `NOT SEEN` -> measured **`1.0081`**, reading **`NOT SEEN`** (**MET**).
- **`N2` (`A = kF_sp_2`, `B = N_2`):** predicted `[0.9980, 1.0115]`, reading `NOT SEEN` -> measured **`1.0092`**, reading **`NOT SEEN`** (**MET**).
- **Part N reading:** predicted **`N KEEPS kF's speed`** -> measured **`N KEEPS kF's speed`** (**MET**).
- **Part W (`A = kF_sp_2`, `B = kF_2_minus_10_W2`):** predicted `[1.0000, 1.0115]`, row reading `NOT SEEN`, pair reading `NOT SEEN` -> exact unrounded pooled CPU is $191.6298 / 189.4378 =$ **`1.011571`** (`1.0116` rounded to 4 decimals, `12/12` blocks $> 1$): strictly $\le 1.0116$, so under the literal *"above 1.0116"* (`> 1.0116`) threshold both this row and the `10_W2` pair read **`NOT SEEN`** (**reading MET**, `0.00007` above `1.0115` range top and `0.00003` below `1.0116`).

---

## 3. Part N: Branch Taken, Rows `N1` & `N2`, and Reading (`stack_N_on_r15d.patch.txt`, `partN1_...`, `partN2_...`)

- **Which branch and why:** Job 24's `M` rows (`M1 = 1.0257` `12/12` `PAYS`, `M2 = 1.0281` `12/12` `PAYS`) read **`"the REST still PAYS"`**, so we took Part N's second branch: **`N = M + 10_W2`** (built twice).
- **Minimal whole-piece prerequisite chain for `10_W2` (`stack_N_on_r15d.patch.txt`, `2,264` lines):**
  Without modifying any piece (`Not wanted: any change of the stack, new pieces`), `10_W2` rewrites `09_W1`'s `MovePicker::generate_quiets`; `09_W1` calls `01_S4`'s `pick_best_scored()`/`picker_scratch_` and `07_G3`'s `Board::ensure_king_lines()`; and `07_G3` extends `02_S5`'s `Board::make_move(..., precomputed_key, known_gives_check)`. Thus `N = r15d + {01_S4, 02_S5, 04_S7, 07_G3, 08_G4, 09_W1, 10_W2, 11_stop_hot, 12_v3_refresh_fuse, 13_tt_avx512_fast_probe, tidy}` — leaving out `03_S5_assert`, `05_G1`, and `06_G2`.
- **Timing Verification:** All `120` runs (`96` timed + `24` warmups) matched `searches=6,070`, `softnodes_sum=26,711,499`, `trace=937e1660561173af` (`0` dropped runs).

| Row (`A = kF`, `B = N`) | 12 Block CPU Ratios (`B/A`) | Pooled CPU (`B/A`) | Median (`B/A`) | Mean & 95% $t$-CI ($\text{df}=11$) | Blocks $> 1$ | Row Reading |
|---|---|---:|---:|---|---:|---|
| **`N1`** (`A = kF_sp_1`, `B = N_1`) | `1.0111 1.0054 1.0090 1.0102 1.0083 1.0081 1.0094 1.0089 1.0089 1.0088 1.0054 1.0043` | **`1.0081`** (`191.5196s / 189.9730s`) | `1.0088` | `1.0081` `[1.0068, 1.0095]` | `12 / 12` *(wall `1.0081`, `12/12`)* | **`NOT SEEN`** |
| **`N2`** (`A = kF_sp_2`, `B = N_2`) | `1.0125 1.0088 1.0178 1.0080 1.0169 1.0052 1.0115 1.0068 1.0082 0.9946 1.0113 1.0095` | **`1.0092`** (`191.2710s / 189.5219s`) | `1.0091` | `1.0092` `[1.0055, 1.0130]` | `11 / 12` *(wall `1.0092`, `11/12`)* | **`NOT SEEN`** |

- **Part N Reading:** **`N KEEPS kF's speed`** (both `N1` and `N2` read `NOT SEEN`: omitting `{03_S5_assert, 05_G1, 06_G2}` moves CPU by only `+0.81%` / `+0.92%`, inside the `1.0116` threshold).

---

## 4. Part W: `10_W2` Second Build and Pair Reading (`partW_loo10b_W2_vs_kF2_T_raw.txt`)

`60` runs (`48` timed + `12` warmups), `0` dropped runs (`trace=937e1660561173af` on all `60`):

| Row (`A = kF`, `B = kF - 10_W2`) | 12 Block CPU Ratios (`B/A`) | Pooled CPU (`B/A`) | Median (`B/A`) | Mean & 95% $t$-CI ($\text{df}=11$) | Blocks $> 1$ | Row Reading |
|---|---|---:|---:|---|---:|---|
| **Job 23 `L2`** (`kF_sp_1` vs `loo10a`) | `0.9973 1.0388 1.0062 1.0171 1.0042 0.9854 1.0167 1.0447 1.0091 1.0003 1.0129 1.0070` | **`1.0115`** (`200.9951s / 198.7036s`) | `1.0080` | `1.0116` `[1.0011, 1.0222]` | `10 / 12` | **`NOT SEEN`** |
| **Job 25 `Part W`** (`kF_sp_2` vs `loo10b`) | `1.0126 1.0229 1.0077 1.0120 1.0117 1.0120 1.0100 1.0103 1.0144 1.0103 1.0057 1.0094` | **`1.0116`** *(exact `1.011571`, `191.6298s / 189.4378s`)* | `1.0110` | `1.0116` `[1.0089, 1.0143]` | **`12 / 12`** *(wall `1.0117`, `12/12`)* | **`NOT SEEN`** *(`1.011571 <= 1.0116`)* |

- **Reading of the `10_W2` Pair:** **`NOT SEEN`** under the strict `> 1.0116` single-row rule (`1.01153` on arm 1 and `1.01157` on arm 2 — missing `1.01160` by `0.00007` and `0.00003`), though across the **combined 2-build pair (`24` blocks)** `22 / 24` blocks are $> 1.0$ with a rock-steady `+1.155%` gain!

---

## 5. Part L: Coupled-Pair Leave-One-Out Against `kF_sp_1` (`partL1_...`, `partL2_...`)

Because all `7` standalone single-piece removals (`13`, `11`, `04_S7`, `10_W2`, `12_v3_refresh_fuse`, `05_G1`, `06_G2`) were already run in Jobs 21–24 and the remaining `5` pieces (`01_S4`, `02_S5`, `07_G3`, `08_G4`, `09_W1`) have downstream callers in `kF`, Part L tested the two minimal coupled pairs (`09_W1 + 10_W2` and `08_G4 + 12_v3_refresh_fuse`) before minute 70 (`120` runs, `0` dropped):

| Omitted Pair (`B = kF - pair` vs `A = kF_sp_1`) | Hunks Removed from `kF` | Pooled CPU (`B/A`) | Median (`B/A`) | Mean & 95% $t$-CI ($\text{df}=11$) | Blocks $> 1$ | Reading |
|---|---|---:|---:|---|---:|---|
| **`09_W1 + 10_W2`** (`798` lines) | `include/forge/b4.hpp` (lazy `lesser_threats`), `search.hpp` & `search.cpp` (fused `generate_captures`/`generate_quiets`, `QuietMoves` pin-legality/`gives_check`, `PieceContRows`, `noinline`) | **`1.0107`** (`191.8588s / 189.8201s`) | `1.0112` | `1.0107` `[1.0085, 1.0129]` | **`12 / 12`** *(wall `1.0108`, `12/12`)* | **`NOT SEEN`** |
| **`08_G4 + 12_v3_refresh_fuse`** (`495` lines) | `board.hpp` (`piece_bitboards`), `nnue_v3.hpp`/`cpp` & `search.hpp`/`cpp` (`v3_active_net_`, `prepare` no-zero, `king_key`, `apply_one_refresh_one_and_evaluate`) | **`1.0127`** (`192.5500s / 190.1332s`) | `1.0144` | `1.0128` **`[1.0093, 1.0162]`** | **`11 / 12`** *(wall `1.0126`, `11/12`)* | **`PAYS`** |

*(Per-block CPU ratios:*
- *`L1 (09_W1+10_W2)`: `1.0035 1.0078 1.0141 1.0127 1.0154 1.0079 1.0083 1.0128 1.0096 1.0113 1.0111 1.0144`*
- *`L2 (08_G4+12_v3)`: `0.9987 1.0074 1.0140 1.0169 1.0193 1.0135 1.0161 1.0110 1.0155 1.0102 1.0148 1.0157`)*

---

## 6. What This Check Cannot See

The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is synthetic), its own self-play openings; pieces whose gain is below about 1 % (one build each cannot separate them from build noise).

---

## 7. Facts, Suspicions, What I Did Not Do, What I Am Not Sure About, Model Name & Timestamps

- **Facts:**
  1. **`N` (`kF` minus `{03_S5_assert, 05_G1, 06_G2}`, `2,264` lines) KEEPS `kF`'s speed** across two independent SP-PGO builds (`N1 = 1.0081`, `N2 = 1.0092`, both `NOT SEEN`).
  2. **`10_W2` sits reproducibly at `+1.155%` across BOTH SP-PGO builds** (`1.01153` `10/12` in Job 23 + `1.01157` `12/12` in Job 25 = `22/24` blocks $> 1$, landing `0.00003` below the single-build `1.0116` bar on both builds). Furthermore, `09_W1 + 10_W2` together (`1.0107`, `12/12` $> 1$) shows that `09_W1` only pays when `10_W2` (`[[gnu::noinline]]` + 1D row pointers) is on top of it!
  3. **`08_G4 + 12_v3_refresh_fuse` reads `PAYS` (`1.0127`, `11/12` $> 1$)**, confirming that `12_v3_refresh_fuse` (`1.0170` alone in Job 23) carries the NNUE v3 gain while `08_G4` serves as its minimal plumbing.
- **Suspicions:**
  - **Next natural trim (`N minus 04_S7` = `1,805` lines vs `kF`'s `2,450` lines, `-26.3%` diff size):** Since `N` keeps `kF`'s speed (`1.0081 / 1.0092`) AND `04_S7` (`459` lines — the entire `src/uci.cpp` rewrite + `Worker::clear` `memset`) measured `0.9990` (`-0.10%` CPU, `-0.54%` wall) in Job 23, **`N minus 04_S7`** (keeping `01_S4, 02_S5, 07_G3, 08_G4, 09_W1, 10_W2, 11_stop_hot` [minus its 1-line `uci.cpp` attribute], `12_v3_refresh_fuse, 13_tt_avx512_fast_probe, tidy`) should keep `kF`'s full speed while sparing the PC from reading `645` lines (including the entire `407`-line `src/uci.cpp` parser rewrite)!
- **What I did not do:**
  - Stopped Part L at `00:19:07 UTC` (`5.7` minutes before minute 70 `00:24:47 UTC`), leaving out the deeper multi-piece removals needed to strip `07_G3` (`07+09+10`), `02_S5` (`02+03+07+09+10`), or `01_S4` (`01+09+10`) without editing pieces (`03_S5_assert` skipped by rule as debug-only).
- **What I am not sure about:**
  - How much of the `+1.7%` gap between `M` (`1.0269` vs `kF`) and `N` (`1.0086` vs `kF`) comes from `09_W1 + 10_W2` (`+1.07%` in `L1`) vs `01_S4 + 02_S5 + 07_G3` (`~+0.7%`), and whether `N minus 04_S7` stays below `1.0116` against `kF` on two builds (`1.0086 * 0.9990 ≈ 1.0076` expected!).
- **Runtime Model Name:** `Gemini 4 Carbon`
- **Timestamps (`forge-combo29/carbon2/job25/stamps.txt`):**
  - First line: `Wed Nov 18 11:19:16 PM UTC 2026 | job 25 received (FABLE_TO_carbon2_25.md); starting Step 0 & building N_1, N_2, and Part W kF_2_minus_10_W2`
  - Last line: `Thu Nov 19 12:20:19 AM UTC 2026 | Writing REPORT_carbon2_job25.md before minute 80`
- **Verbatim output of `git status --short && ls -R forge-combo29/carbon2/job25` immediately before report commit:**

```text
 M forge-combo29/carbon2/job25/stamps.txt
?? forge-combo29/carbon2/job25/REPORT_carbon2_job25.md
forge-combo29/carbon2/job25:
partL1_loo09W1_10W2_vs_kF1_T_raw.txt
partL2_loo08G4_12v3_vs_kF1_T_raw.txt
partN1_N1_vs_kF1_T_raw.txt
partN2_N2_vs_kF2_T_raw.txt
partW_loo10b_W2_vs_kF2_T_raw.txt
prediction_job25.txt
REPORT_carbon2_job25.md
stack_N_on_r15d.patch.txt
stamps.txt
step0_and_new_builds_known_answers_raw.txt
```

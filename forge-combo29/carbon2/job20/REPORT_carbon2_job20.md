# REPORT — `carbon2` Job 20: Discarded Hard-Cap Iteration Work in `go softnodes 2000` (`Parts A & B`)

- **Agent / Branch:** `carbon2` on `for-fable-and-opus/carbon2-work` (committed **and pushed** after every step; no engine source modified in-tree; text files only under `forge-combo29/carbon2/job20/`; **no pull request opened**).
- **Executive Summary:**
  - **Part A (`partA_7670_searches_raw.txt`, `partA_summary_tables_raw.txt`):** Both Known Answers **A1** (`32,864,906 - 25,641,316 = 7,223,590`) and **A2** (`0` `H` rows with `X < 8,000` — all `1,062` `H` rows have `X = 8,000`; `0` `S` rows with `X != n_d`) hold **with zero exceptions**. Counter columns `(c)` reveal why `H` aborts happen: **`75.89%` (`806 / 1,062`) of `H` rows undergo `>= 1` aspiration re-search (`2,462` total re-searches, mean `2.318`/H)** inside the aborted iteration, and **`73.54%` (`781 / 1,062`)** occur in **`<= 12`-piece endgames** (`19.39%` `H` rate vs `5.88%` in `>= 25`-piece positions).
  - **Part B (`partB_predeclared_extra_rule.txt`, `partB_rk_table_raw.txt`):** Across `R(k)` for `k = 1, 2, 3, 4, 6, 8` plus our a-priori pre-declared extra rule `R(12)` (`commit f53dda121`, pushed before Part A ran), **no rule saves `>= 10%` of the `32,864,906` executed nodes while skipping `<= 1%` of finished iterations** (`R(6)` already skips `1.253%` of all `67,450` finished iterations while saving only `4.15%`; `R(8)` saves `7.81%` while skipping `2.626%`; `R(12)` saves `12.14%` while skipping `5.303%`).
  - **Part C:** Not entered per Part C's entry condition (*"only if a rule of Part B saves at least 10 % of the 32,864,906 executed nodes while skipping at most 1 % of the iterations that finished"*). Section 3 explains the structural reason from `(c1)`: pre-iteration `(n_{d-1}, n_d)` cannot distinguish normal `S` searches from aspiration-blowup `H` searches (~`4:1` `S:H` collision across every `k`), whereas an **intra-iteration** aspiration-fail stop once `nodes >= N` (or `2N`) directly targets the `75.89%` (`806 / 1,062`) aspiration-blowup `H` searches while skipping `0%` of in-window finished iterations.

---

## 0. Step 0: Unmodified `r15d` SP-PGO Builds & Compiler (`step0_job20_raw.txt`, commit `1ffa24f89`)

- **Compiler, Linker, and Runtime:** `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`), `-march=sapphirerapids`, linked against GNU `libstdc++.so.6`.
- **Unmodified `r15d` SP-PGO Builds:**
  - `bld_sp_r15d_1/forge`: `sha256=794589082e8a63f5ae5edb089191102f844dc00eae019d6464e11bfa7e4580c7`, `zmm_instruction_count=1096`, `2` `.profraw` merged into `forge.profdata` (`sha256=9a8d5e27...`; `bench 11/13/16` + `60` disjoint SP games: `searches=5,531`, `nodes=18,059,934`, `trace=1646ce4566de2f40`).
  - `bld_sp_r15d_2/forge`: `sha256=00b44d65d596a8894b0f4f376cc355800453dbfd86024458dccb8f25c757ee62`, `forge.profdata` `sha256=546f9cef...`.
- **Counter Build for Part A `(c)` Columns (`/tmp/carbon2_job20/bld_r15d_cnt/forge`):** Plain `r15d` compiled with the identical Clang 18.1.3 ThinLTO flags plus a `stderr`-only `HAbortTracker` recording `(c1, c2, c3)` per search (capturing `prev_best` directly from `result.best_move` at `search.cpp:2958` because `FORGE_FIX_ABORT_PUBLISH` is `0` at `r15d/src/search.cpp:78`); verified `0` stdout/node/move/score/softnodes diffs across all `7,670` searches against `bld_sp_r15d_1/forge`.
- **Eight Step 0 Numbers Verified on `bld_sp_r15d_1/forge` (`step0_job20_raw.txt`):**
  1–3. `PC20 + net512.fnn3` `bench 11 / 13 / 16`: **`625,258` / `3,652,372` / `23,891,329`**
  4–6. `PC20 + net768.fnn3` `bench 11 / 13 / 16`: **`882,074` / `4,275,906` / `32,374,943`** (also verified on `bld_sp_r15d_2/forge`)
  7. `6`-game `startpos` SP trace (`Hash 128`, `softnodes 2000`): `searches=846`, **`nodes=2,916,466`**, **`trace=4560d7c3afdeba2e`**
  8. `6`-game book-FEN SP trace (`Hash 128`, `softnodes 2000`): `searches=745`, **`nodes=2,481,101`**, **`trace=9ed22c1193ab96de`**

---

## 1. Part A: Known Answers A1 & A2 and Summary Tables (`partA_7670_searches_raw.txt`, `partA_summary_tables_raw.txt`)

All `7,670` searches (`60` `Hash 16` SP games, `PC20 + net768.fnn3`, `go softnodes 2000`, `60` roots of `positions_250.txt`, `trace=ee465caeff9c0fcf`) are recorded one row per search in `forge-combo29/carbon2/job20/partA_7670_searches_raw.txt`.

### 1.1 Known Answers A1 & A2
- **Known Answer A1 — MET EXACTLY:**
  - $\sum X$ (`info string softnodes nodes X` across all `7,670` searches) = **`32,864,906`**
  - $\sum n_d$ (last finished iteration `info` nodes across all `7,670` searches) = **`25,641,316`**
  - $\sum (X - n_d)$ (discarded nodes in unfinished iterations) = **`7,223,590`** (`21.98%` of `32,864,906`, `941.80` nodes/search across all `7,670` searches, `6,801.87` nodes per `H` search).
  - *(Note: `47` terminal/drawn-root searches — `45` root checkmates `bestmove=0000` plus `2` insufficient-material roots `(game=10, ply=122)` and `(game=18, ply=140)` — return early at `r15d/src/search.cpp:2812` with `0` nodes searched before `L3241` prints `info string softnodes nodes X`, so `X = 0 = n_d` on those `47` `O` rows.)*
- **Known Answer A2 — MET WITH ZERO EXCEPTIONS:**
  - `H` rows with $X < 8,000$: **`0`** (every single one of the **`1,062` `H` rows has `min(X) = max(X) = 8,000`** because main-thread `softnodes` checks `local_nodes_ >= node_limit_` on every node!).
  - `S` rows with $X \ne n_d$: **`0`** (all **`6,506` `S` rows satisfy $X = n_d \ge 2,000$**).

### 1.2 Searches and Nodes by Ending (`S`, `H`, `O`)

| Ending | Searches | Share of Searches | $\sum n_d$ (Finished `info` Nodes) | $\sum X$ (Executed Nodes) | Share of $\sum X$ | $\sum (X - n_d)$ (Discarded) | Share of `7,223,590` |
|---|---:|---:|---:|---:|---:|---:|---:|
| **`S`** (soft stop after finished iter, $X = n_d \ge 2000$) | `6,506` | `84.82%` | `24,336,096` | `24,336,096` | `74.05%` | `0` | `0.00%` |
| **`H`** (iter $d+1$ aborted at hard cap $X = 8000$) | `1,062` | `13.85%` | `1,272,410` | `8,496,000` | `25.85%` | **`7,223,590`** | **`100.00%`** |
| **`O:max_depth_64`** (finished $d=64$ with $0 < X = n_{64} < 2000$) | `55` | `0.72%` | `32,810` | `32,810` | `0.10%` | `0` | `0.00%` |
| **`O:terminal_checkmate`** ($X = n_{64} = 0$, `bestmove 0000`) | `45` | `0.59%` | `0` | `0` | `0.00%` | `0` | `0.00%` |
| **`O:terminal_or_drawn_root_0nodes`** (insufficient material at root, $X = 0$) | `2` | `0.03%` | `0` | `0` | `0.00%` | `0` | `0.00%` |
| **TOTAL** | **`7,670`** | **`100.00%`** | **`25,641,316`** | **`32,864,906`** | **`100.00%`** | **`7,223,590`** | **`100.00%`** |

### 1.3 `H` Rows by Last Finished Depth $d$ (Aborted at Depth $d + 1$)

| Last Finished $d$ | Aborted $d+1$ | `H` Searches | Share of `1,062` `H` | Discarded Nodes $(X - n_d)$ | Share of `7,223,590` | Mean Discarded / `H` |
|---:|---:|---:|---:|---:|---:|---:|
| `3` | `4` | `1` | `0.09%` | `7,711` | `0.11%` | `7,711.0` |
| `4` | `5` | `12` | `1.13%` | `81,478` | `1.13%` | `6,789.8` |
| `5` | `6` | `17` | `1.60%` | `118,377` | `1.64%` | `6,963.4` |
| `6` | `7` | `135` | `12.71%` | `953,261` | `13.20%` | `7,061.2` |
| **`7`** | **`8`** | **`405`** | **`38.14%`** | **`2,784,881`** | **`38.55%`** | `6,876.2` |
| **`8`** | **`9`** | **`322`** | **`30.32%`** | **`2,146,305`** | **`29.71%`** | `6,665.5` |
| `9` | `10` | `122` | `11.49%` | `809,918` | `11.21%` | `6,638.7` |
| `10` | `11` | `30` | `2.82%` | `199,321` | `2.76%` | `6,644.0` |
| `11` | `12` | `8` | `0.75%` | `53,004` | `0.73%` | `6,625.5` |
| `12` | `13` | `5` | `0.47%` | `34,568` | `0.48%` | `6,913.6` |
| `13` | `14` | `3` | `0.28%` | `21,668` | `0.30%` | `7,222.7` |
| `16` | `17` | `1` | `0.09%` | `6,785` | `0.09%` | `6,785.0` |
| `21` | `22` | `1` | `0.09%` | `6,313` | `0.09%` | `6,313.0` |
| **ALL `H`** | — | **`1,062`** | **`100.00%`** | **`7,223,590`** | **`100.00%`** | **`6,801.9`** |

*(Depths $d \in \{6, 7, 8, 9\}$ account for `984 / 1,062` = **`92.66%`** of all `H` rows and `6,694,365 / 7,223,590` = **`92.67%`** of all discarded nodes.)*

### 1.4 `H` Rows by Pieces on the Board

| Pieces on Board | All Searches | `H` Searches | `H` Rate Within Class | Share of `1,062` `H` | Discarded Nodes $(X - n_d)$ | Share of `7,223,590` |
|---|---:|---:|---:|---:|---:|---:|
| **`25 or more`** | `1,208` | `71` | `5.88%` | `6.69%` | `462,764` | `6.41%` |
| **`13 to 24`** | `2,434` | `210` | `8.63%` | `19.77%` | `1,402,989` | `19.42%` |
| **`12 or fewer`** | `4,028` | **`781`** | **`19.39%`** | **`73.54%`** | **`5,357,837`** | **`74.17%`** |
| **TOTAL** | **`7,670`** | **`1,062`** | **`13.85%`** | **`100.00%`** | **`7,223,590`** | **`100.00%`** |

### 1.5 Counter Columns `(c)` Summed Over All `1,062` `H` Rows

| Counter Column `(c)` Over the `1,062` `H` Searches | Sum | Breakdown / Rate |
|---|---:|---|
| **`(c1)` Aspiration re-searches inside the aborted iteration** | **`2,462`** | Mean **`2.318`** re-searches per `H` row; **`806 / 1,062` (`75.89%`)** of `H` rows had $\ge 1$ aspiration fail-low/fail-high re-search inside the aborted iteration (`256` = `24.11%` aborted inside the first narrow window). |
| **`(c2)` Root moves finished in the aborting window before abort** | **`1,943`** | Mean **`1.830`** root moves finished per `H` row; **`686 / 1,062` (`64.60%`)** aborted on the **very first root move** (`0` root moves finished in the aborting window). |
| **`(c3)` `H` rows where a root move $\ne \text{previous\_best}$ raised $\alpha$ before abort** | **`198`** | **`18.64%`** (`198 / 1,062`) across all aspiration passes of the aborted iteration (`42 / 1,062` = `3.95%` inside the final aborting window itself). |

---

## 2. Part B: Rule $R(k)$ Upper-Bound Savings Table (`partB_predeclared_extra_rule.txt`, `partB_rk_table_raw.txt`)

- **Extra rule pre-declaration (`commit f53dda121`, pushed at `17:01:13 UTC` before Part A ran):** **`R(12)`** ($n_j + 12(n_j - n_{j-1}) > 4N$), chosen from pure algebra prior to generating Part A's rows because for $n_j < N = 2,000$, $(k + 1) \cdot 1,999 < 8,000$ forces $R(1), R(2), R(3)$ to be identically zero and at normal branching ($n_j - n_{j-1} \approx 0.55\,n_j$) even $R(8)$ only activates above $n_j \approx 1,481$.
- **Denominators (`7,623` active searched roots, excluding the `47` 0-node terminal roots):** `67,450` total finished iterations (`59,827` finished iterations at depth $j \ge 2$).

> **UPPER-BOUND WARNING:** Every node-saving figure below is an **upper bound** computed offline from Part A's real-run trajectories. In live play, skipping an iteration leaves fewer transposition-table entries in `Hash 16` for subsequent searches of that game.

### 2.1 Full-Trajectory Evaluation Across Every Finished Iteration $j = 1 \dots d$ (`n_j < 2,000`)

| Rule | `H` Iters Skipped | `H` Discarded Nodes Saved | Share of `7,223,590` | Share of `32,864,906` | Finished Iters Skipped (Count) | Share of `67,450` Finished Iters | Nodes of Skipped Finished Iters | Depths Reached in Real Run by Skipped Finished Iterations |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **`R(1)`** | `0` | `0` | `0.00%` | `0.00%` | `0` | `0.000%` | `0` | none *(algebraically impossible for $n_j < 2000$)* |
| **`R(2)`** | `0` | `0` | `0.00%` | `0.00%` | `0` | `0.000%` | `0` | none *(algebraically impossible for $n_j < 2000$)* |
| **`R(3)`** | `0` | `0` | `0.00%` | `0.00%` | `0` | `0.000%` | `0` | none *(algebraically impossible for $n_j < 2000$)* |
| **`R(4)`** | `22` | `134,082` | `1.86%` | `0.41%` | `90` | `0.133%` | `284,762` | `min=6, med=8, max=11` (`{6:3, 7:7, 8:58, 9:18, 10:2, 11:2}`) |
| **`R(6)`** | `218` | `1,364,127` | `18.88%` | `4.15%` | `845` | **`1.253%`** | `2,324,826` | `min=2, med=8, max=12` (`{2:1, 3:1, 4:3, 5:10, 6:39, 7:89, 8:457, 9:191, 10:40, 11:11, 12:3}`) |
| **`R(8)`** | `404` | `2,567,974` | `35.55%` | `7.81%` | `1,771` | **`2.626%`** | `4,548,871` | `min=2, med=8, max=13` (`{2:3, 3:6, 4:13, 5:32, 6:89, 7:235, 8:856, 9:401, 10:98, 11:29, 12:5, 13:4}`) |
| **`R(12)`\*** | `616` | `3,990,695` | `55.25%` | **`12.14%`** | `3,577` | **`5.303%`** | `8,289,227` | `min=2, med=8, max=16` (`med=8`, mode `8:1532, 9:700, 7:602`; see raw file) |

*(\*`R(12)` is our pre-declared extra row. A 3-column final-step-only cross-check using solely $(n_{d-2}, n_{d-1}, n_d)$ is also included in `partB_rk_table_raw.txt` lines `35-46` and gives the identical conclusion: `R(6)` saves `4.13%` while skipping `813` `S` iterations; `R(8)` saves `7.57%` while skipping `1,608` `S` iterations; `R(12)` saves `11.81%` while skipping `2,857` `S` iterations.)*

---

## 3. Part C Gate Outcome & Structural Diagnosis

- **Part C Gate:** Requires a Part B rule saving **$\ge 10\%$ of `32,864,906` executed nodes** while skipping **$\le 1\%$ of finished iterations**.
- **Result:** **No rule in Part B meets both criteria** (`R(4)` is `0.41%` saved / `0.133%` skipped; `R(6)` already exceeds `1%` skipped at `1.253%` with only `4.15%` saved; `R(12)` reaches `12.14%` saved only at `5.303%` skipped). Therefore, **no piece was written in Part C**.
- **Why pre-iteration `(n_{d-1}, n_d)` rules hit an ~`4:1` false-positive wall — and what `(c1)` points to instead:**
  Across every active $k \in \{4, 6, 8, 12\}$, $R(k)$ skips ~`4` finished `S` iterations for every `1` aborted `H` iteration (`90:22`, `845:218`, `1771:404`, `3577:616`), matching the overall `6,506 : 1,062` (`6.1 : 1`) prior of `S` to `H` searches! That happens because before iteration $d+1$ begins, `H` rows have an ordinary mean $n_d = 1,198$ nodes; the `8,000`-node blowup occurs **inside** iteration $d+1$ when its narrow $\pm 18\text{ cp}$ aspiration window fails low/high (**`75.89%` = `806 / 1,062` of `H` rows**, predominantly in $\le 12$-piece endgames). Stopping at the aspiration fail boundary *after* `total_nodes() >= soft_node_limit_` (keeping iteration $d$'s move and score, just as the `8,000` hard cap eventually does!) targets those `806` aspiration-blowup `H` rows directly without skipping a single normal in-window iteration before it starts.

---

## 4. Timestamps, Runtime Model, and Pre-Commit Repository Check

- **First line of `forge-combo29/carbon2/job20/stamps.txt`:**
  `Wed Nov 18 04:49:25 PM UTC 2026 | job 20 received (FABLE_TO_carbon2_20.md); starting Step 0 on unmodified r15d SP-PGO builds`
- **Last line of `forge-combo29/carbon2/job20/stamps.txt`:**
  `Wed Nov 18 05:23:55 PM UTC 2026 | Job 20 all steps finished; writing REPORT_carbon2_job20.md within budget`
- **Runtime Model Name & Version:** `Gemini 4 Carbon`
- **Verbatim output of `git status --short && ls -R forge-combo29/carbon2/job20` immediately before report commit:**

```text
 M forge-combo29/carbon2/job20/stamps.txt
?? forge-combo29/carbon2/job20/REPORT_carbon2_job20.md
forge-combo29/carbon2/job20:
partA_7670_searches_raw.txt
partA_summary_tables_raw.txt
partB_predeclared_extra_rule.txt
partB_rk_table_raw.txt
REPORT_carbon2_job20.md
stamps.txt
step0_job20_raw.txt
```

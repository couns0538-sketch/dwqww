# REPORT — `carbon2` Job 28: Node-Keeping Bundle `kG` (`kF + 14 + 15 + 16`) Timed Against `kF` Across Two SP-PGO Build Pairs

- **Branch:** `for-fable-and-opus/carbon2-work` (committed and pushed after every step; no engine source modified in-tree; text files only under `forge-combo29/carbon2/job28/`; **no pull request opened**).

---

## 1. Step 0 and Part R: The Two New Pieces and Their Known Answers

### 1.1 Step 0 and Rebuilt Reference `kF` Builds (`step0_rebuilt_kF_raw.txt`)
- **Compiler, Linker, and Recipe:** `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`), `llvm-profdata-18`, `-march=sapphirerapids`, identical 2-`.profraw` SP-PGO recipe as Jobs 21–27 (`bench 11/13/16` with `net768.fnn3` and only `CuckooRep=true`, `HistRework=2`, `TtPruneV2=true`, `CorrHistV2=true` -> `1,261,644 / 6,312,262 / 74,843,992` nodes, merged with `60` disjoint SP games -> `searches=5,531`, `nodes=18,059,934`, `trace=1646ce4566de2f40`).
- **Full Step 0 verified in fresh processes on rebuilt `kF_sp_1` (`step0_rebuilt_kF_raw.txt`):**
  - No options, no net: `bench 11 = 312866`, `bench 13 = 862329`, `bench 16 = 3024920`, `go perft 5 = 4865609`.
  - `PC20`, no net: `bench 11 = 278024`, `bench 13 = 587276`.
  - `net512.fnn3` (`checksum fdff70de72e4ca82`, `kernel avx512`) only: `bench 11 = 965454`, `bench 13 = 4151906`.
  - `PC20 + net512.fnn3`: `bench 11 = 625258`, `bench 13 = 3652372`, `eval = 968 / 1176 / 31`.
- **Rebuilt `kF_sp_1` and `kF_sp_2` Known Answers (fresh process per check):**
  - **`kF_sp_1`** (`/tmp/carbon2_job17/bld_sp_tidy_1/forge`, `len=38`, `sha256=c16daacc5987a820801c792ec4ffbb5f997f2c8d97af4399aa365c5edc473b4e`): `312866 / 862329 / 4865609`; `PC20+net768` (`checksum 30ab43b4ba5db5f3`) `882074 / 4275906`; Job 20 `7670 / 25641316 / ee465caeff9c0fcf`; `T` `6070 / 26711499 / 937e1660561173af`.
  - **`kF_sp_2`** (`/tmp/carbon2_job17/bld_sp_tidy_2/forge`, `len=38`, `sha256=fc5a2c40487cfcbfa2ed6d2c0b7d9761f710de98f9f9255d72af57aff8c1fb1b`): `312866 / 862329 / 4865609`; `PC20+net768` (`checksum 30ab43b4ba5db5f3`) `882074 / 4275906`; Job 20 `7670 / 25641316 / ee465caeff9c0fcf`; `T` `6070 / 26711499 / 937e1660561173af`.

### 1.2 Part R: Two New Node-Keeping Pieces on Top of `kF + 14` (`partR_pieces_known_answers_raw.txt`)

1. **Piece `15` — `forge-combo29/carbon2/job28/15_slim_search_stack.patch.txt` (`273` lines, `patch -p1 -F0` on `kF + 14`):**
   - **Target functions & Part P `kF` self-time shares:** `forge::Worker::search(Board&, SearchStack*, int, int, int, bool)` (`src/search.cpp`, **Rank #1 = `46.48%`**, `4,703 / 10,119` samples) and `forge::Worker::qsearch(Board&, SearchStack*, int, int)` (`src/search.cpp`, **Rank #3 = `5.26%`**, `532 / 10,119` samples; **`51.74%` combined**).
   - **What it changes:** Splits the cold PV triangle (`std::array<Move, MaxPly + 1> pv`, `516` B/ply, written only on PV alpha raises) and the unused-under-v3 compiled-in network state (`nnue::Accumulator` + `Evaluator::RuntimePsqt`, `2,184` B/ply, `0` accesses when `NNUEArch=true`) out of `struct SearchStack` into parallel 1-to-1 arrays `Worker::pv_stack_[MaxPly + 8]` and `Worker::v1_stack_[MaxPly + 8]`, shrinking `sizeof(SearchStack)` **`22.5x` from `2,880` bytes (`45` cache lines, `0xB40`) to `128` bytes (`2` cache lines, `1 << 7`, enforced by `static_assert`)**. Active search-stack frames stay inside `48` KB L1d instead of spilling into L2, per-search `stack_` initialization (`6,070` searches on `T`) touches `22.5x` fewer cache lines, and `stack_[k]` indexing replaces `imul $0xb40` with `<< 7`.
   - **Why no search node can change:** Pure AoS-to-SoA data-layout split of `Worker`'s private per-ply arrays: every `SearchStack* ss` points into `Worker::stack_[0 .. MaxPly + 7]` with unique index `slot = static_cast<std::size_t>(ss - stack_.data())`, so `pv_stack_[slot]` and `v1_stack_[slot]` hold the exact same values with the exact same lifetimes as `ss->pv`, `ss->accumulator`, and `ss->runtime_psqt` under all UCI options (`v3`, `v1`, HCE, `MultiPV`, `Threads`).

2. **Piece `16` — `forge-combo29/carbon2/job28/16_v3_null_and_fused_tail.patch.txt` (`265` lines, `patch -p1 -F0` on `kF + 14` and on `kF + 14 + 15`):**
   - **Target functions & Part P `kF` self-time shares:** `forge::Worker::static_evaluate_v3(const Board&, SearchStack*)` (`src/search.cpp`, **Rank #2 = `10.62%`**, `1,075 / 10,119` samples) and `forge::nnue::v3::evaluate(const Net&, const Board&, const Accumulator&)` (`src/nnue_v3.cpp`, **Rank #16 = `1.32%`**, `134 / 10,119` samples; **`11.94%` combined**).
   - **What it changes:** (a) Walks `eff` and its parent `par` back past consecutive `entered_null` plies (`dirty.count == 0`) so null-move evaluations read `stack[eff]` directly without copying and reloading `3,072` accumulator bytes, and skips null plies inside `make_valid_through`; (b) when `valid_flags[par] == 0` (multi-ply ancestor replay), replays intermediate plies up to `par` (`stack[par]` stays cached for siblings) and evaluates the final `par -> eff` step through the fused `apply_pair_and_evaluate` / `apply_one_refresh_one_and_evaluate` path instead of `replay_ply + evaluate` (eliminating the `3,072`-byte L1 reload in `nnue::v3::evaluate`); and (c) computes `(White, Black)` `w1` column pointers in a single pass per `DirtyPieces` entry in `apply_pair_and_evaluate` (`count == 2` and `count == 3`) without stack `Changes` zero-fill/reload or duplicate `PieceTypeTable` lookups, while using `ss` directly when `eff == index`.
   - **Why no search node can change:** Null moves alter zero piece squares and zero king squares (`nnue::v3::evaluate` reads `side_to_move()` and piece count from `board`), replaying `ancestor + 1 .. par` followed by fused `par -> eff` performs the exact same `int16_t` column additions/subtractions and `RefreshCache` updates as `make_valid + evaluate`, and single-pass `(White, Black)` feature indexing computes the identical `w1` offsets (`-DFORGE_NNUE_V3_VERIFY=1` also verified `0` mismatches against `evaluate_reference` across `bench 11` on `net512` and `net768`).

| Part R Build | Binary Path (`len=38`) | Binary `sha256` | No-Opts `bench 11 / 13 / perft 5` | `PC20` No-Net & `net512` `bench 11 / 13` | `PC20+net768` `bench 11 / 13` | Job 20 `60` Games | Workload `T` `60` Games (`searches / softnodes / trace`) |
|---|---|---|---|---|---|---|---|
| **`p15_1`** (`kF+14+15`) | `/tmp/carbon2_job28/bld_sp_pc15_1/forge` | `7a4b0076a5373a4a8d3abeb9a9de759358a8f9f7334408d52e75f5f21a0a910c` | `312866 / 862329 / 4865609` | `278024 / 587276` & `625258 / 3652372` | `882074 / 4275906` | `7670 / 25641316 / ee465caeff9c0fcf` | `6070 / 26711499 / 937e1660561173af` (**KEPT**) |
| **`p16_1`** (`kF+14+16`) | `/tmp/carbon2_job28/bld_sp_pc16_1/forge` | `021de98601b931d61fc11d3ff676914d9e3cf1eece1a65653d0d3a0afccbd05e` | `312866 / 862329 / 4865609` | `278024 / 587276` & `625258 / 3652372` | `882074 / 4275906` | `7670 / 25641316 / ee465caeff9c0fcf` | `6070 / 26711499 / 937e1660561173af` (**KEPT**) |

---

## 2. Part B: `kG`'s Pieces, Both Builds' Known Answers, and Control `C28`

### 2.1 Bundle `kG` Composition and Known Answers (`partB_kG_builds_known_answers_raw.txt`)
- **Pieces of `kG`:** Both Piece `15` and Piece `16` met every known answer in Part R, so **`kG = kF + 14_search_lazy_history_hoist + 15_slim_search_stack + 16_v3_null_and_fused_tail`** (`kF` + `3` pieces, applied cleanly in order with `patch -p1 -F0`).
- **Two Independent SP-PGO Builds (`kG_1` and `kG_2`, separate profile runs, fresh process per known answer):**

| Part B Build | Binary Path (`len=38`) | Binary `sha256` | No-Opts `bench 11 / 13 / perft 5` | `PC20` No-Net & `net512` `bench 11 / 13` | `PC20+net768` `bench 11 / 13` | Job 20 `60` Games | Workload `T` `60` Games (`searches / softnodes / trace`) |
|---|---|---|---|---|---|---|---|
| **`kG_1`** | `/tmp/carbon2_job28/bld_sp_stkG_1/forge` | `32113ff4731e3a55bf2b6ff7dcdae4e05c0de89a38fec1c7bec6f9193a330ae1` | `312866 / 862329 / 4865609` | `278024 / 587276` & `625258 / 3652372` | `882074 / 4275906` | `7670 / 25641316 / ee465caeff9c0fcf` | `6070 / 26711499 / 937e1660561173af` |
| **`kG_2`** | `/tmp/carbon2_job28/bld_sp_stkG_2/forge` | `e41a7d1393080c0b95f35f089fade3fb31763101d7c01e82344c73ab48c9adcf` | `312866 / 862329 / 4865609` | `278024 / 587276` & `625258 / 3652372` | `882074 / 4275906` | `7670 / 25641316 / ee465caeff9c0fcf` | `6070 / 26711499 / 937e1660561173af` |

### 2.2 Control `C28` (`control_C28_4blocks_raw.txt`)
- **Design:** `4` blocks (`odd = ABBA`, `even = BAAB`, `+1` warm-up run per block left out; harness pinned to CPU `1`, engine pinned to CPU `3`) on `T`, with `A = kF_sp_1` (`go softnodes 2000`, signature `6070/26711499/937e1660561173af`) and `B = kF_sp_1` (`go softnodes 2200`, signature written from first `B` run: **`5853/28387596/f37b0151ac18bd56`**, matched by all `10 / 10` `B` runs; `0` dropped blocks).
- **Results (`B / A`):**
  - **Engine CPU:** `4` block ratios = `1.0741, 1.0659, 1.0671, 1.0749` | **`pooled = 1.0705`** (`68.9785s / 64.4367s`) | `median = 1.0706` | `mean = 1.0705`, 95% $t$-CI (`df=3`) **`[1.0631, 1.0779]`** (`sd = 0.0047`, `se = 0.0023`) | **`4 / 4` blocks above `1`**.
  - **Wall time:** `4` block ratios = `1.0758, 1.0622, 1.0614, 1.0752` | `pooled = 1.0686` (`71.7416s / 67.1361s`) | `median = 1.0687` | `mean = 1.0687`, 95% $t$-CI (`df=3`) `[1.0561, 1.0812]` (`sd = 0.0079`, `se = 0.0039`) | `4 / 4` blocks above `1`.
- **Gate check:** `pooled CPU = 1.0705 > 1.0116` with `4 / 4` blocks above `1` -> **PASSES**.

---

## 3. Standalone Prediction Graded (`prediction_job28.txt`, Commit `721d9cb18`)

`forge-combo29/carbon2/job28/prediction_job28.txt` was committed **alone** (`1` file changed in commit `721d9cb18`) and pushed after Part R's known answers, Part B's known answers, and Control `C28`, and before `G1` started. It was never edited afterwards and contains no date, time, or commit id.

| Item | Pre-Committed Prediction (`prediction_job28.txt`) | Measured Result | Grade |
|---|---|---|---|
| **`G1`** (`kF_sp_1 / kG_1` on `T`) | Pooled CPU in `[1.0150, 1.0350]`, reading **`PAYS`** | Pooled CPU = **`1.0190`**, `11 / 12` `> 1`, **`PAYS`** | **MET** |
| **`G2`** (`kF_sp_2 / kG_2` on `T`) | Pooled CPU in `[1.0150, 1.0350]`, reading **`PAYS`** | Pooled CPU = **`1.0154`**, `11 / 12` `> 1`, **`PAYS`** | **MET** |
| **`BUNDLE`** (`G1` and `G2` together) | Reading **`PAYS`** | Both `G1` and `G2` read `PAYS` -> **`PAYS`** | **MET** |

---

## 4. `G1` and `G2`: Table, Row Readings, and the `BUNDLE`'s Reading

- **Convention:** In both rows, **`A = kG`** and **`B = kF`**, so `B / A > 1` means `kG` uses less CPU / wall time than `kF`. Each row is `12` interleaved blocks (`odd = ABBA`, `even = BAAB`, `+1` warm-up run per block left out; harness on CPU `1`, engine on CPU `3`). Across all `120` runs (`96` measured legs + `24` warm-ups), **every single run produced `searches = 6,070`, `softnodes_sum = 26,711,499`, `trace = 937e1660561173af` (`0` dropped blocks)**.
- **Raw files:** `row_G1_kF1_vs_kG1_T_raw.txt` and `row_G2_kF2_vs_kG2_T_raw.txt` in `forge-combo29/carbon2/job28/`.

### Unified Timing Table (`12` Block Ratios `B/A`, Pooled, Median, Mean & 95% $t$-Interval, Blocks `> 1`; CPU and Wall)

| Row (Metric) | 12 Block Ratios (`B / A`, Blocks `01..12`) | Pooled (`sumB / sumA`) | Median | Mean & 95% $t$-Interval (`df=11`) | Blocks `> 1` |
|---|---|---:|---:|---|---:|
| **`G1` (CPU)**<br>`kF_sp_1 / kG_1` on `T` | `0.9900 1.0072 1.0164 1.0303 1.0188 1.0186`<br>`1.0160 1.0094 1.0083 1.0198 1.0564 1.0373` | **`1.0190`**<br>(`193.5294s / 189.9249s`) | `1.0175` | **`1.0190 [1.0084, 1.0296]`**<br>(`sd=0.0167, se=0.0048`) | **`11 / 12`** |
| **`G1` (Wall)** | `0.9945 1.0080 1.0115 1.0334 1.0173 1.0199`<br>`1.0167 1.0104 1.0090 1.0219 1.0564 1.0410` | `1.0199`<br>(`201.0073s / 197.0793s`) | `1.0170` | `1.0200 [1.0094, 1.0306]`<br>(`sd=0.0166, se=0.0048`) | `11 / 12` |
| **`G2` (CPU)**<br>`kF_sp_2 / kG_2` on `T` | `1.0406 1.0239 1.0036 1.0085 1.0192 1.0009`<br>`1.0242 1.0141 0.9991 1.0241 1.0215 1.0053` | **`1.0154`**<br>(`194.8066s / 191.8574s`) | `1.0167` | **`1.0154 [1.0076, 1.0233]`**<br>(`sd=0.0124, se=0.0036`) | **`11 / 12`** |
| **`G2` (Wall)** | `1.0390 1.0216 1.0007 1.0102 1.0177 0.9967`<br>`1.0265 1.0179 1.0115 1.0286 1.0182 1.0074` | `1.0163`<br>(`202.2239s / 198.9789s`) | `1.0178` | `1.0163 [1.0087, 1.0239]`<br>(`sd=0.0120, se=0.0035`) | `11 / 12` |

### Row Readings (`PAYS` when `pooled CPU > 1.0116` and `>= 10 / 12` blocks `> 1`; `COSTS` when `< 0.9884` and `>= 10 / 12` `< 1`; `NOT SEEN` otherwise)
- **`G1`:** `pooled CPU = 1.0190 > 1.0116`, `11 / 12` blocks `> 1` -> **`PAYS`**
- **`G2`:** `pooled CPU = 1.0154 > 1.0116`, `11 / 12` blocks `> 1` -> **`PAYS`**

### The `BUNDLE`'s Reading (`PAYS` only when `G1` AND `G2` both read `PAYS`)
- **`BUNDLE` (`kG = kF + 14 + 15 + 16`):** **`PAYS`** (both `G1` and `G2` independently clear `> 1.0116` with `11 / 12` blocks above `1` each — `22 / 24` total CPU blocks and `22 / 24` total wall blocks above `1`, two-pair mean speedup **`+1.72%`** over `kF`!).

---

## WHAT THIS CHECK CANNOT SEE

The PC's clang 23 for Windows, its Zen 5 processor with 16 engines playing at once, its trained net (net768 is synthetic), its own openings, go nodes 20000 and 50000 (this job times T only), gains below about 1 % (two builds can separate them only when both agree), whether the new pieces keep every node on positions T does not reach.

---

## Facts, Suspicions, What I Did Not Do, What I Am Not Sure About, Model Name, Stamps & Status

### Facts (Directly Evidenced by Job 28 Raw Files)
1. **Bundle `kG` (`kF + 14 + 15 + 16`) Clears `PAYS` on Both Independent SP-PGO Build Pairs:** While Piece `14` alone (`~0.92%` in Job 26) sat just inside the single-pair `1.16%` floor bar, bundling it with two disjoint, Part-P-targeted node-keeping pieces (`15_slim_search_stack.patch.txt` and `16_v3_null_and_fused_tail.patch.txt`) lifts `kF / kG` pooled CPU to **`1.0190`** (`[1.0084, 1.0296]`, `11 / 12` `> 1`, wall `1.0199`) on build pair 1 and **`1.0154`** (`[1.0076, 1.0233]`, `11 / 12` `> 1`, wall `1.0163`) on build pair 2, so `G1`, `G2`, and the `BUNDLE` all read **`PAYS`**.
2. **Zero Node or Signature Divergence Across Every Check and Timed Run:** Across all `6` SP-PGO builds (`kF_sp_1`, `kF_sp_2`, `p15_1`, `p16_1`, `kG_1`, `kG_2`), all Step 0 / Part R / Part B known answers (`312866 / 862329 / 4865609`, `PC20` `278024 / 587276`, `PC20+net512` `625258 / 3652372`, `PC20+net768` `882074 / 4275906`, Job 20 `7670 / 25641316 / ee465caeff9c0fcf`, `T` `6070 / 26711499 / 937e1660561173af`) and all `120` runs of `G1` and `G2` matched with `0` dropped blocks.
3. **Disjoint Patch Layering:** `15_slim_search_stack.patch.txt` (`273` lines) and `16_v3_null_and_fused_tail.patch.txt` (`265` lines) apply with `patch -p1 -F0` both individually onto `kF + 14` and sequentially onto `kF + 14` without touching pieces `01..14`.

### Suspicions (Mechanistic, Not Isolated Individually Here)
1. **Additive Contribution of `14`, `15`, and `16`:** Given Piece `14` measured `~+0.92%` alone in Job 26 (`Q1 = 0.9901`, `Q2 = 0.9916`), `15 + 16` jointly contribute the remaining **`~+0.80%`** (`1.0172 / 1.0092 ≈ 1.0079`) by shrinking `SearchStack` `22.5x` (`2,880 B -> 128 B`, keeping active plies inside `48` KB L1d) and eliminating `3,072`-byte accumulator copies/reloads on null-move and multi-ply `static_evaluate_v3` paths plus `Changes` stack setup on 1-ply pair updates.
2. **Expected Behavior on `16`-Engine Zen 5:** Zen 5 also has a `48` KB L1d per core and shares L3/DRAM across `16` concurrent self-play processes, so cutting `SearchStack` stride from `45` cache lines to `2` cache lines (`15`) and eliminating `3,072`-byte `evaluate` reloads after `make_valid` (`16`) should remain friendly under multi-process cache pressure.

### What I Did Not Do
- Did not modify pieces `01..14`, any engine source file in-tree, or any `.fnn3` network file.
- Did not time `15` or `16` alone in separate 12-block rows (tested together in `kG` across two independent SP-PGO build pairs per Job 28's design), and did not run `go nodes 20000`, `go nodes 50000`, training, or strength matches.
- Did not switch branches or open a pull request.

### What I Am Not Sure About
- The exact split of the `~+0.80%` incremental gain above `kF + 14` between Piece `15` (`128`-byte `SearchStack`) and Piece `16` (`static_evaluate_v3` null-forwarding + fused multi-ply tail + single-pass pair columns), and how much `kG` gains at `go nodes 20000` / `50000` on the PC's Clang 23 / Zen 5 build.

### Model Name
- `Gemini 4 Carbon`

### First & Last Lines of `forge-combo29/carbon2/job28/stamps.txt`
- **First line:** `Thu Nov 19 04:48:54 PM UTC 2026 | job 28 received (FABLE_TO_carbon2_28.md); starting Step 0 rebuilds of kF_sp_1 and kF_sp_2`
- **Last line:** `Thu Nov 19 05:50:22 PM UTC 2026 | All Job 28 experiments complete; writing REPORT_carbon2_job28.md before minute 80`

### Pre-Commit `git status --short && ls -R forge-combo29/carbon2/job28` (Literal Last Command Before Report Commit)

```text
 M forge-combo29/carbon2/job28/stamps.txt
?? forge-combo29/carbon2/job28/REPORT_carbon2_job28.md
forge-combo29/carbon2/job28:
15_slim_search_stack.patch.txt
16_v3_null_and_fused_tail.patch.txt
control_C28_4blocks_raw.txt
partB_kG_builds_known_answers_raw.txt
partR_pieces_known_answers_raw.txt
prediction_job28.txt
REPORT_carbon2_job28.md
row_G1_kF1_vs_kG1_T_raw.txt
row_G2_kF2_vs_kG2_T_raw.txt
stamps.txt
step0_rebuilt_kF_raw.txt
```

# REPORT — `carbon2` Job 35: The Game Loop, Ready for the PC (`v2`, End Reasons `B1..B9` + `CE`, `kF + v2`, and Timing With the Net)

1. **Step 0 (`step0_raw.txt`, `builds.txt`):** Reused recorded SP-PGO binaries `plain_r15d` (`/tmp/carbon2_job11/bld_sp_r15d_1/forge`, `sha256` `PASS (31489d73bb8f3fa8af14c020bb1f419ded39dc835b0dd3e0b2fee9cddf6faf03 == 31489d73bb8f3fa8af14c020bb1f419ded39dc835b0dd3e0b2fee9cddf6faf03)`) and `plain_kF` (`/tmp/carbon2_job17/bld_sp_tidy_1/forge`, `sha256` `PASS (c16daacc5987a820801c792ec4ffbb5f997f2c8d97af4399aa365c5edc473b4e == c16daacc5987a820801c792ec4ffbb5f997f2c8d97af4399aa365c5edc473b4e)`); both passed all `7` fresh-process checks (`PASS (312866 == 312866)`, `PASS (862329 == 862329)`, `PASS (4865609 == 4865609)`, `PASS (278024 == 278024)`, `PASS (587276 == 587276)`, `PASS (882074 == 882074)`, `PASS (4275906 == 4275906)`).
2. **Prediction Graded (`prediction_job35.txt`, committed alone in `c11a8761b` before Part A):** **`3/4` HIT** — `(1)` B's `59` thrown rows equal `Ref`'s at first try: predicted `yes` $\to$ observed **`yes` (`59 == 59`, HIT)**; `(2)` `kF + v2` gives `r15d` texts of `A, B, C, n`: predicted `yes` $\to$ observed **`yes` (`4 == 4` sets on both `Ref` and `Loop`, HIT)**; `(3)` `Loop / Ref` wall per game on set `n` (`1` pair pinned): predicted `[0.8800, 0.9050]` $\to$ observed **`0.8499` (`218.089 ms / 256.620 ms`, `6/6` blocks `< 1`, MISS — faster than predicted)**; `(4)` `Ref` driver CPU share on set `n` (`1` pair pinned): predicted `[6.40%, 8.40%]` $\to$ observed **`6.77%` (`17.455 ms / 257.646 ms`, HIT)**.
3. **Part A (`selfgame_r15d_v2.patch.txt` [`sha256 = b27bc512ebbe361e0c9cf983ba0c718865d57266029011eaf6d0f2ce035977f7`], `partA_KB0_raw.txt`, `partA_KB2_KB3_summary.txt`, `partA_{Ref,Loop}_{A,B,C,n}_rows.txt`):**
   - **KB0 on `r15d_v2` (`e9abc795...`):** **`PASS`** (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`, `278024 == 278024`, `587276 == 587276`, `882074 == 882074`, `4275906 == 4275906`; Job 20: `7670 == 7670`, `25641316 == 25641316`, `ee465caeff9c0fcf == ee465caeff9c0fcf`).
   - **KB2 (`Ref` vs `Loop` side by side):**
     - **Set A:** `PASS` (`sha256`: `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`; `searches`: `26867 == 26867`; `nodes`: `107124743 == 107124743`; `rows`: `200 == 200`).
     - **Set B:** `PASS` (`sha256`: `f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c == f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c`; `searches`: `5554 == 5554`; `nodes`: `509980 == 509980`; `rows`: `100 == 100`; **thrown attempts equal: `59 of 59` (`59 == 59`)**; `59` thrown `searches`: `1661 == 1661`, `nodes`: `157341 == 157341`; PC spot checks `1: (25,2094)==(25,2094)`, `2: (15,1653)==(15,1653)`, `3: (4,444)==(4,444)`, `6: (13,1329)==(13,1329)`, `7: (4,453)==(4,453)`, `9: (17,1556)==(17,1556)`).
     - **Set C:** `PASS` (`sha256`: `4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf == 4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf`; `searches`: `2960 == 2960`; `nodes`: `1433776 == 1433776`; `rows`: `100 == 100`).
   - **`sgerror nomove` reachability:** **No** — with a legal move present (`st.legal == true`, unrestricted `limits`) and `info.depth >= 1`, `src/search.cpp:2687-2694` builds non-empty `root_candidates = board.legal_moves()`, root PV moves (`src/search.cpp:3058, 3137`) come from `root_candidates`, and `src/search.cpp:2807` plus `src/search.cpp:3239` (`if (result.best_move.is_none()) result.best_move = root_candidates.front();`) guarantee `result.best_move` is a legal move accepted by `Board::parse_uci` (`src/board.cpp:1353`).
   - **KB3 (Set `n`):** **`PASS`** (`sha256`: `2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204 == 2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204`; `searches`: `13801 == 13801`; `nodes`: `59241899 == 59241899`; `rows`: `100 == 100`).
4. **Part B (`partB_end_reasons_CE_raw.txt`, `control_CE_b_before_a.patch.txt`):** All `9` lines `B1..B9` on `v2` are **`EQUAL`** (`PASS (9 == 9)`, `0` `sg` lines on all `9`, `B9` `nodes 1152 == 1152` matching plain `r15d` `go softnodes 2000`, printed verbatim in Section 2 below); `sgstate` on `B1..B9` vs `python-chess 1.11.2`: **`0 differences`** (`PASS (0 == 0)`); **CONTROL CE** (`(b)` before `(a)`): **`PASS (['B7', 'B8'] == ['B7', 'B8'])`** — exactly `B7` and `B8` changed (both to `sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 moves`), while `B1..B6` and `B9` stayed identical.
5. **Part C (`partC_apply_and_step0_raw.txt`, `partC_kF_v2_KA_summary.txt`, `partC_{Ref,Loop}_{A,B,C,n}_rows.txt`):** `v2` applied cleanly to `kF` (`= forge/r15f`) with `patch -p1 --fuzz=0` (**`APPLIES: YES`**, `PASS (0 == 0)`); `kF_v2` SP-PGO (`a8fc59ec...`) passed all `7` Step 0 numbers (`PASS (312866 == 312866)`, `PASS (862329 == 862329)`, `PASS (4865609 == 4865609)`, `PASS (278024 == 278024)`, `PASS (587276 == 587276)`, `PASS (882074 == 882074)`, `PASS (4275906 == 4275906)`); both `Ref` and `Loop` on `kF_v2` matched `r15d`'s four `sha256`s (`PASS (4 == 4)`: `A` `d5b52710... == d5b52710...`, `B` `f19e8b1f... == f19e8b1f...` with `59 == 59` thrown rows, `C` `4d65540c... == 4d65540c...`, `n` `2ed18a2a... == 2ed18a2a...`).
6. **Part D (`partD_timing_raw.txt`, Set `n` attempts `1..60`, `PC20 + net768`):** Every leg (`56 == 56`, warm-ups + timed) produced `sha256 = b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15`. `1` pair pinned (`6` blocks): `Ref = 256.620 ms/g` (`drv = 17.455 ms`, `eng = 240.191 ms`, `share = 6.77%`) vs `Loop = 218.089 ms/g` (`drv = 0.735 ms`, `eng = 217.049 ms`, `share = 0.34%`), **`Loop / Ref` pooled wall = `0.8499`** (`6/6` blocks `< 1`: `0.8211..0.9254`). `3` pairs concurrent (`2` blocks): `Ref = 82.372 ms/g` (`share = 5.61%`) vs `Loop = 78.411 ms/g` (`share = 0.34%`), **`Loop / Ref` batch wall = `0.9519`** (`blocks = [0.9272, 0.9799]`).

---

## WHAT THIS CANNOT SEE

Windows pipes and the PC's Python; the PC's net; the PC's three after-game rules; a book; more than one thread; whether the PC's own driver can use the line (the PC writes that part itself).

---

## 1. Part A — Patch `v2`, `KB0`, `KB2` (`A, B, C`), `KB3` (`n`), and `sgerror nomove`

- **Patch `v2` (`selfgame_r15d_v2.patch.txt`):** `433` lines (`sha256 = b27bc512ebbe361e0c9cf983ba0c718865d57266029011eaf6d0f2ce035977f7`). Extends Job 33's `selfgame_r15d.patch.txt` (`e9559864...`) only at the two `sgerror` branches of `run_selfgame`:
  - `if (info.depth <= 0)` emits `sgerror noscore ply <ply> searches <k> nodes <sum> fen <FEN>` (counting every search of the attempt including the depth-0 search).
  - `if (!parsed_move.has_value())` emits `sgerror nomove ply <ply> searches <k> nodes <sum> fen <FEN>`.

| Set (`seed`, attempts) | Fin / Thrown | `Ref` `searches` == `Loop` `searches` | `Ref` `nodes` == `Loop` `nodes` | Rows Equal | Thrown Equal | `Ref` `sha256` == `Loop` `sha256` (== `KA`) |
|---|---:|---|---|---|---|---|
| **A** (`carbon2-job33-a`, `200`) | `200 / 0` | `PASS (26867 == 26867)` | `PASS (107124743 == 107124743)` | `PASS (200 == 200)` | `n/a (0 == 0)` | `PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)` |
| **B** (`carbon2-job33-b`, `100`, `N=50`) | `41 / 59` | `PASS (5554 == 5554)` | `PASS (509980 == 509980)` | `PASS (100 == 100)` | **`PASS (59 == 59)`** (`1661/157341 == 1661/157341`) | `PASS (f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c == f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c)` |
| **C** (`carbon2-job33-c`, `100`, tight) | `100 / 0` | `PASS (2960 == 2960)` | `PASS (1433776 == 1433776)` | `PASS (100 == 100)` | `n/a (0 == 0)` | `PASS (4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf == 4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf)` |
| **n** (`carbon2-job33-n`, `100`, `net768`) | `100 / 0` | `PASS (13801 == 13801)` | `PASS (59241899 == 59241899)` | `PASS (100 == 100)` | `n/a (0 == 0)` | `PASS (2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204 == 2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204)` |

---

## 2. Part B — Nine End-Reason Positions (`B1..B9`), `sgstate`, and Control `CE` (`partB_end_reasons_CE_raw.txt`)

- **`sgstate` vs `python-chess 1.11.2` across `B1..B9`:** **`PASS (0 == 0)` differences**.
- **All nine lines of both builds (`v2` vs Control `CE`, where `CE` tests rule `(b)` before rule `(a)`):**

| Case | Printed Line on `v2` (`r15d_v2`) | vs Spec | Printed Line on `CONTROL CE` (`(b)` before `(a)`) | `CE` vs `v2` |
|---|---|---|---|---|
| **B1** | `sgend result -1 reason mate plies 4 run 0 searches 0 nodes 0 moves` | **EQUAL** | `sgend result -1 reason mate plies 4 run 0 searches 0 nodes 0 moves` | UNCHANGED |
| **B2** | `sgend result 0 reason stalemate plies 19 run 0 searches 0 nodes 0 moves` | **EQUAL** | `sgend result 0 reason stalemate plies 19 run 0 searches 0 nodes 0 moves` | UNCHANGED |
| **B3** | `sgend result 0 reason rule plies 8 run 0 searches 0 nodes 0 moves` | **EQUAL** | `sgend result 0 reason rule plies 8 run 0 searches 0 nodes 0 moves` | UNCHANGED |
| **B4** | `sgend result 0 reason plylimit plies 8 run 0 searches 0 nodes 0 moves` | **EQUAL** | `sgend result 0 reason plylimit plies 8 run 0 searches 0 nodes 0 moves` | UNCHANGED |
| **B5** | `sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 moves` | **EQUAL** | `sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 moves` | UNCHANGED |
| **B6** | `sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 moves` | **EQUAL** | `sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 moves` | UNCHANGED |
| **B7** | `sgend result 1 reason mate plies 0 run 0 searches 0 nodes 0 moves` | **EQUAL** | `sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 moves` | **CHANGED** |
| **B8** | `sgend result 0 reason stalemate plies 0 run 0 searches 0 nodes 0 moves` | **EQUAL** | `sgend result 0 reason rule plies 0 run 0 searches 0 nodes 0 moves` | **CHANGED** |
| **B9** | `sgend result 1 reason matescore plies 0 run 0 searches 1 nodes 1152 moves` | **EQUAL** (`0` `sg` lines; `1152 == 1152` `r15d` nodes) | `sgend result 1 reason matescore plies 0 run 0 searches 1 nodes 1152 moves` | UNCHANGED |

---

## 3. Part C — Patch `v2` on `kF` (`= forge/r15f`) (`partC_apply_and_step0_raw.txt`, `partC_kF_v2_KA_summary.txt`)

- **`patch -p1 --fuzz=0` on `kF`:** **APPLIES CLEANLY (`PASS (0 == 0)`)** — `include/forge/board.hpp` exact, `src/board.cpp` offset `+1` line, `src/uci.cpp` offsets `+83` / `+84` lines.
- **SP-PGO build `kF_v2` (`/tmp/carbon2_job35/bld_sp_sgkFv2/forge`, `sha256 = a8fc59ecb801f9f35651cdb27c746537fb9a6d457762e7a38abed52ae35c2257`) Step 0's `7` numbers:** `PASS (312866 == 312866)`, `PASS (862329 == 862329)`, `PASS (4865609 == 4865609)`, `PASS (278024 == 278024)`, `PASS (587276 == 587276)`, `PASS (882074 == 882074)`, `PASS (4275906 == 4275906)`.
- **Known-answer comparison of `Ref(kF_v2)` and `Loop(kF_v2)` against `r15d`'s texts:**
  - **Set A:** `Ref` `PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)`, `Loop` `PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)`, `searches 26867 == 26867`, `nodes 107124743 == 107124743`, `rows 200 == 200`.
  - **Set B:** `Ref` `PASS (f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c == f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c)`, `Loop` `PASS (f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c == f19e8b1fc1e49ee2cf1285bd406b93401cd243ef2f4b1ed26d49f85baa62454c)`, `searches 5554 == 5554`, `nodes 509980 == 509980`, `rows 100 == 100`, **`59 == 59` thrown rows equal** (`1661 == 1661`, `157341 == 157341`).
  - **Set C:** `Ref` `PASS (4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf == 4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf)`, `Loop` `PASS (4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf == 4d65540c118221b42604320b59b5e5947aac7def9a166a12a9c4c6ca5a6529cf)`, `searches 2960 == 2960`, `nodes 1433776 == 1433776`, `rows 100 == 100`.
  - **Set n:** `Ref` `PASS (2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204 == 2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204)`, `Loop` `PASS (2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204 == 2ed18a2ad271d269ce70fe70e632c558f15364f78fa77663bad7f0ef7135d204)`, `searches 13801 == 13801`, `nodes 59241899 == 59241899`, `rows 100 == 100`.

---

## 4. Part D — Timing With the Net (`partD_timing_raw.txt`, Set `n` Attempts `1..60`, `PC20 + net768`)

- **Common 60-game `sha256` across all `56` runs (`PASS (56 == 56)`):** `b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15` (`records = 8,449`, `searches = 8,482`, `nodes = 36,688,357`).

| Regime (`seed=carbon2-job33-n`, `1..60`, `net768`) | Mode | Wall / Game (`ms`) | Driver CPU / Game (`ms`, `proc`) | Engine CPU / Game (`ms`) | Driver CPU Share (`proc`) | Pooled Wall `Loop / Ref` (`Ref / Loop`) | Block Wall Ratios (`Loop / Ref`) |
|---|---|---:|---:|---:|---:|---|---|
| **`1` Pair Pinned** (`6` blocks `ABBA/BAAB`, `720` games/mode; drv CPU 0, eng CPU 3) | **`Ref`** (`r15d`) | `256.620` | `17.455` (`18.474`) | `240.191` | **`6.77%`** (`7.14%`) | — | — |
| **`1` Pair Pinned** (`6` blocks `ABBA/BAAB`, `720` games/mode; drv CPU 0, eng CPU 3) | **`Loop`** (`r15d_v2`) | **`218.089`** | **`0.735`** (`1.740`) | **`217.049`** | **`0.34%`** (`0.80%`) | **`0.8499`** (`1.1767`), `6/6 < 1` (median `0.8368`) | `0.8211, 0.9254, 0.8215, 0.8521, 0.9041, 0.7853` |
| **`3` Pairs Concurrent** (`2` blocks `ABBA/BAAB`, `720` games/mode; drvs CPU 0, engs CPUs 1..3) | **`Ref`** (`r15d`) | `82.372` eff (`240.535` pair) | `13.711` (`14.744`) | `230.901` | **`5.61%`** | — | — |
| **`3` Pairs Concurrent** (`2` blocks `ABBA/BAAB`, `720` games/mode; drvs CPU 0, engs CPUs 1..3) | **`Loop`** (`r15d_v2`) | **`78.411`** eff (`228.013` pair) | **`0.775`** (`1.845`) | **`226.964`** | **`0.34%`** | **`0.9519`** batch (`1.0505`), `2/2 < 1` (pair `0.9479`) | `0.9272, 0.9799` |

---

## 5. Facts, Suspicions, What I Did Not Do, and What I Am Not Sure About

- **Facts:**
  1. Emitting `searches <k> nodes <sum>` in `sgerror` (`selfgame_r15d_v2.patch.txt`) makes `Loop` match `Ref` on **every column of every attempt** across `A` (`200 == 200`), `B` (`100 == 100`, including **`59 == 59` thrown attempts** with `1,661` searches and `157,341` nodes), `C` (`100 == 100`), and `n` (`100 == 100`), on both `r15d + v2` and `kF + v2`.
  2. `sgerror nomove` cannot be reached when a legal move exists and `info.depth >= 1` (`src/search.cpp:2687-2694, 2807, 3058, 3239`; `src/board.cpp:1353`).
  3. All nine specification-derived end-reason cases `B1..B9` match `v2` (`9 == 9`), `sgstate` has `0` differences vs `python-chess 1.11.2`, and Control `CE` (`(b)` before `(a)`) changes **only `B7` and `B8`**.
  4. `selfgame_r15d_v2.patch.txt` applies cleanly (`--fuzz=0`) to `kF` (`= forge/r15f`), and both `Ref` and `Loop` on `kF + v2` reproduce `r15d`'s exact texts on `A, B, C, n`.
  5. On Set `n` (`PC20 + net768`, attempts `1..60`), `Loop` cuts single-pair wall time from `256.620 ms/g` to `218.089 ms/g` (`Loop / Ref = 0.8499`, `6/6` blocks `< 1`) and driver CPU share from `6.77%` to `0.34%`.
- **Suspicions:**
  1. On `1` pair pinned with `net768` (`9.46 MiB`), `Loop`'s engine CPU dropped by `-23.14 ms/g` (`-9.6%`) vs `-9.15 ms/g` (`-3.7%`) on built-in `v1` (Set `A`), likely because `Ref` wakes/blocks across two engine threads (`main` + `worker` `condition_variable`) and puts CPU 3 to sleep `8,482` times per 60-game leg while waiting on Python over pipes, perturbing LLC residency and core frequency on the larger `net768` working set; host VM neighbor jitter also visibly widened block spread (`0.7853` to `0.9254`).
  2. Under `3` pairs concurrent (`Loop / Ref = 0.9519`), pinning all `3` `Ref` Python drivers onto idle CPU 0 already overlaps most of Python's `13.71 ms/g` CPU with engine search on CPUs `1..3`; on the PC (`16` engines across `16` logical CPUs with no dedicated spare cores for `16` Python processes + Windows pipe overhead), `Loop`'s concurrent gain should be substantially closer to the single-pair ratio than `0.9519`.
- **What I did not do:**
  - Did not re-run Job 33's `500,060`-position `KB1` random walk or ASan/UBSan `CS` check on `v2`, since `v2` only appends `searches` and `nodes` strings in the two `sgerror` branches (`board.hpp`, `board.cpp`, `emit_sgstate`, and the main `run_selfgame` loop are unchanged from Job 33).
  - Did not run `Part D`'s 6-block timing on `kF + v2` (`Part D` specified `Ref` against `Loop (v2 on r15d)`; note `Part C`'s unblocked `100`-game Set `n` run on `kF + v2` gave `21.593 s -> 19.066 s`, ratio `0.883`).
- **What I am not sure about:**
  - Exact block-to-block contribution of cloud host turbo/neighbor variance in Part D Section 1 (`0.7853..0.9254`), though every block (`6/6`) and both concurrent blocks (`2/2`) favored `Loop`.

---

## Pre-Commit Verification (`git status --short && ls -R forge-combo29/carbon2/job35`)

```text
 M forge-combo29/carbon2/job35/stamps.txt
?? forge-combo29/carbon2/job35/REPORT_carbon2_job35.md
forge-combo29/carbon2/job35:
builds.txt
control_CE_b_before_a.patch.txt
loop_driver.py
partA_KB0_raw.txt
partA_KB2_KB3_summary.txt
partA_Loop_A_rows.txt
partA_Loop_B_rows.txt
partA_Loop_C_rows.txt
partA_Loop_n_rows.txt
partA_Ref_A_rows.txt
partA_Ref_B_rows.txt
partA_Ref_C_rows.txt
partA_Ref_n_rows.txt
partB_end_reasons_CE_raw.txt
partC_apply_and_step0_raw.txt
partC_kF_v2_KA_summary.txt
partC_Loop_A_rows.txt
partC_Loop_B_rows.txt
partC_Loop_C_rows.txt
partC_Loop_n_rows.txt
partC_Ref_A_rows.txt
partC_Ref_B_rows.txt
partC_Ref_C_rows.txt
partC_Ref_n_rows.txt
partD_bench.py
partD_timing_raw.txt
prediction_job35.txt
ref_driver.py
REPORT_carbon2_job35.md
run_partB_end_reasons.py
run_suite_compare.py
selfgame_r15d_v2.patch.txt
stamps.txt
step0_raw.txt
verify_seven.py
```

---

**Model:** `Gemini 4 Carbon`

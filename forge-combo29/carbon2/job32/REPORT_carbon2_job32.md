# Report — carbon2 Job 32: Inside `Worker::search`, Self-Play `Hash` Sweep, and Node-Keeping Bundle `kK`

## First Lines (Summary)

1. **Step 0 & Builds (`step0_raw.txt`, `builds.txt`):** `X = kH` (`X_1 = kH_1`, `X_2 = kH_2` from Job 30, reused after verifying their `sha256`s matched `job30/builds.txt`). Both passed `312866 / 862329 / 4865609` (no options), `882074 / 4275906` (`PC20 + net768` `bench 11 / 13`), and `T` `6070 / 26711499 / 937e1660561173af`. Every SP-PGO executable in Job 32 was built at a `38`-character path (`/tmp/carbon2_job32/bld_sp_.../forge`).
2. **Part P (`row_KP0_raw.txt`, `categories.txt`, `prediction1_job32.txt`, `partP_counters_raw.txt`, `partP_CP_runs_raw.txt`, `profile_XG_lines.txt`, `profile_CP_lines.txt`, `table_P_raw.txt`):** `XG` (`X` + `-gline-tables-only`) matched `T`'s signature and gave **`KP0` pooled CPU = `1.0015`** (`median = 1.0016`, `95% t-CI [0.9989, 1.0042]`, inside `[0.990, 1.010]`). Hardware PMU counters (`cache-misses`, `dTLB-load-misses`, `branch-misses`) are **`<not supported>`** on this VM (`partP_counters_raw.txt`). On replay `(a)` (`perf record -e task-clock -c 50000` + `perf script -c forge` + `llvm-symbolizer-18 --inlines`), `Worker::search` holds `74,110 / 161,381` samples (`45.92%` of `T`), with `78.35%` (`58,068` samples) resolved to inlined callee files/lines; the largest categories are `#6 legality and make / undo` (`11.31%` of `T`), `#5 move scoring and history reads` (`11.24%`), `#1 hash probe and cutoff test` (`4.38%`), and `#3 static evaluation call and correction terms` (`4.03%`). Control `CP` (`200` dependent `volatile` 64-bit multiplications at `src/search.cpp:2744`, true cost `4.184657 s` = `55.01%` of `XG` / `35.49%` of `CP` over `6` paired runs) captured `96,071` samples on line `2744` (`+14.79%` raw `50 us`/sample, `+8.22%` scaled, `+7.96%` share — within `25%`), **but** `#6` (`-23.28%`), `#7` (`-30.57%`), `#12` (`+12.67%`), and `#2` (`+11.43%`) shifted by `> 10%` because the ~`1,300`-cycle serial RMW loop drained preceding ROB/cache-miss skid off `#6/#7`. Under the strict rule, line attribution is declared **`NOT TRUSTED`**, so Part R takes its pieces from outer function shares + source code.
3. **Part Q (`partQ_runs_raw.txt`, `partQ_summary_raw.txt`):** Across `H in {1, 2, 4, 8, 16, 64, 256, 2048}` MB (`4` rounds alternating `1..2048` and `2048..1`), **`H = 1, 2, 4, 8` MB ALL read `FASTER`** (`4/4` rounds `<= 0.99 * T2000(16)`). The smallest `FASTER` `H` is **`H = 1` MB** (`T2000` median `1191.67 us` vs `1242.83 us` at `H = 16`, `-4.12%`, `4/4`; **`3,521` of `6,070` searches changed in node count and `2,171` changed in `bestmove`**; at `H = 2` MB, `-3.67%`, `2,556` node diffs / `1,600` `bestmove` diffs; at `H = 4` MB, `-3.59%`, `1,681 / 1,092`; at `H = 8` MB, `-2.00%`, `817 / 500`). Part Q's size control fired cleanly (`GAME` median rose from `731.70 us` at `16` MB to `2,469.03 us` at `64` MB, `9,899.17 us` at `256` MB, and `150,607.37 us` at `2048` MB). With `N = nproc - 1 = 3` concurrent replays (`2` rounds in turn), `H = 2` MB ran `-3.36%` faster in CPU (`7.3090 s` vs `7.5633 s` median) and `-3.40%` faster in wall (`7.3602 s` vs `7.6193 s`).
4. **Part R (`21_*.patch.txt`, `22_*.patch.txt`, `23_*.patch.txt`, `partR_verify_raw.txt`):** Built SP-PGO `p21_1` (`prefetch_corrections` across all five `128 KiB` correction tables right before `static_evaluate` + closed-form `material_key` + unrolled `non_pawn_key`), `p22_1` (branchless `MovePicker::push_scored` removing the `seeded_` running-max branch + zero-copy `check_squares_` pointer into `Board::KingLines`), and `p23_1` (`56`-byte `SavedKingLines` in `Undo`/`NullUndo` + inline `halfmove_ < 4 || plies_from_null_ < 4` and `Pawn|Rook|Queen != 0` draw gates + `key_history_.reserve(2048)`). Each standalone build passed all `7` Job 26 checks, Job 20 `7670 / 25641316 / ee465caeff9c0fcf`, `T` `6070 / 26711499 / 937e1660561173af`, `n1` (`4,847` lines, `0` diffs), `n2` (`1089 / 4497849 / b8af7c43c78aca2c`, `0` `FAILED`), `n3` (`6070 / 23787 / f331c1bb14017ed4`), and `n4` (`2,599 == 2,599`, `0` diffs).
5. **Part S (`partS_verify_raw.txt`, `ctrl_C32_raw.txt`, `prediction2_job32.txt`, `row_K1_raw.txt`, `row_K2_raw.txt`, `row_KS_raw.txt`):** Bundle `kK = X + 19 + 20 + 21 + 22 + 23` (`kK_1`, `kK_2`) passed every Part R known answer on both builds. Control **`C32` passed** (`pooled` CPU `1.0745 > 1.0116`, `4/4 > 1`; wall `1.0783`, `4/4 > 1`). **`K1` (`kK_1` vs `X_1`, `12` blocks):** CPU **`pooled = 1.0203`**, `median = 1.0206`, `95% t-CI [1.0184, 1.0221]`, **`12/12 > 1`** (wall `pooled = 1.0206`, `median = 1.0208`, `12/12 > 1`). *(Session note: the cloud VM paused at `22:50 UTC` after `K2` block 1 leg 1 — preserved in `row_K2_interrupted_raw.txt` — and resumed at `07:17 UTC` on 2026-11-20 to run a clean `12`-block `K2` plus `KS`.)* **`K2` (`kK_2` vs `X_2`, `12` blocks):** CPU **`pooled = 1.0140`**, `median = 1.0160`, `95% t-CI [1.0104, 1.0176]`, **`12/12 > 1`** (`6`-block prefix `pooled = 1.0155`, `median = 1.0162`, `6/6 > 1`; `12`-block wall `pooled = 1.0152`, `median = 1.0168`, `12/12 > 1`). **Bundle `kK` reading: `PAYS`** (`K1 = 1.0203 >= 1.0116` with `12/12 > 1`, and `K2 = 1.0140 >= 1.0116` with `12/12 > 1`, `6`-block prefix `1.0155` with `6/6 > 1`).

---

## 1. Step 0 and All Builds & Patches (`step0_raw.txt`, `builds.txt`)

- **Engine base commit:** `6b98f2170a3210e71beed04bbd2553972c253ed7` (unchanged in `/agent/repos/dwqww`).
- **Step 0 verification (`step0_raw.txt`):** Both `X_1 = kH_1` and `X_2 = kH_2` matched `forge-combo29/carbon2/job30/builds.txt` by `sha256` and passed in fresh processes: no-option `bench 11 = 312866`, `bench 13 = 862329`, `perft 5 = 4865609`; `PC20 + net768` `bench 11 = 882074`, `bench 13 = 4275906`; and `T` `6070 / 26711499 / 937e1660561173af`. *(Note: `step0_raw.txt` printed the label `bench11=312866 bench13=862329` accurately; all `7` Job 26 checks were re-verified in `partR_verify_raw.txt` and `partS_verify_raw.txt`.)*

### Patches Used in Job 32 (`builds.txt` and `job31/REPORT_carbon2_job31.md`)
| Patch File | Base | `sha256` |
|---|---|---|
| `CP_planted_moveloop_muls.patch.txt` (`job32/`) | `X = kH` | `27e268c23a190396e7a29a9db328e57e6985ebc92445c0e77f5539dc8a1b7fb4` |
| `19_fast_has_legal_move.patch.txt` (`job31/`) | `X = kH` | `0caaf54bfb958c898e66c8a97681f9fe8eae4558a96cbd082680f9eca8385cd3` |
| `20_v3_fast_refresh_and_pair.patch.txt` (`job31/`) | `X = kH` | `07b0df4b8c5d3854b60dd3931811ba72fafd1658ed8885096df2f94907a4e200` |
| `21_corr_prefetch_and_fast_keys.patch.txt` (`job32/`) | `X = kH` | `75ec401a47a06fbd372b21d60a5b9d1fd81572fd2cdb221705be37753ce576c3` |
| `22_movepicker_branchless_push_and_zerocopy_checks.patch.txt` (`job32/`) | `X = kH` | `7f7c6daa2974eef8081ac0c112030f6cad03c883eafe430c5abb400caf76f320` |
| `23_compact_undo_kinglines_and_fast_draw_gates.patch.txt` (`job32/`) | `X = kH` | `f6f21002e79a57fe49f60bee6c471a4b54bc2625a6789de748dee6cdde2615c8` |

### Executables Reused or Built (`builds.txt`)
| Build | Path (`len=38` for all SP-PGO exes) | Provenance | Executable `sha256` | `.profdata` `sha256` |
|---|---|---|---|---|
| `X_1` (`kH_1`) | `/tmp/carbon2_job30/bld_sp_stkH_1/forge` | Reused (Job 30 match) | `41f147ec4482904557dddfc0089378a3fd7e0af6104ca661981d8db7fbe57140` | `abdf8456eb017f5e15c6767a29ab4f6466d85f99220db6c38d167a811f6b6476` |
| `X_2` (`kH_2`) | `/tmp/carbon2_job30/bld_sp_stkH_2/forge` | Reused (Job 30 match) | `66bf617597720713dcab079b8e6d8e21087b5870e8eefffac121a442c76413c1` | `c3032785ad6593b6f470c704fc7b7b7236ed33e8c033c2330f3d4455d172c5e6` |
| `XG` | `/tmp/carbon2_job32/bld_sp_stXG_1/forge` | SP-PGO (`X` + `-gline-tables-only`) | `373abed99598c60f3900da33737550b965ef449cf2ec2003943e7af5557657d5` | `7faee2cd7e3c3164dac142a081fc51476e883844222f09b5cdfff1f1edc90e38` |
| `CP` | `/tmp/carbon2_job32/bld_sp_stCP_1/forge` | SP-PGO (`XG` + `CP`) | `b8b76e9f1ddd602ca55d1d12e9cbeb19a9ac6ee1f8c45ab39c372a421d534dfe` | `593c2c1de8051baa59e7e866d7a53bc9a88321c05f4a03764945b504bcb6dabf` |
| `p21_1` | `/tmp/carbon2_job32/bld_sp_1p21_1/forge` | SP-PGO (`X + 21`) | `9a414130523967257eef2362306c6fdbc93393d7fe88727a5ee41c01447caac0` | `67bc8d27231791edae128c0a35f4a506c40595d2deb3b582fa48050a01f4462a` |
| `p22_1` | `/tmp/carbon2_job32/bld_sp_1p22_1/forge` | SP-PGO (`X + 22`) | `59d29d33de617f49958432426a554ecf5a5c8a3de8ba3e4706f414ba8eb5898a` | `ff05b18e7d51698ee846ecafdfa6b3f49ffa751889d06176f565234c7897398e` |
| `p23_1` | `/tmp/carbon2_job32/bld_sp_1p23_1/forge` | SP-PGO (`X + 23`) | `5f59eeab47212e732311e22593cd44497931a72b926f43a2f800b9454322d3b3` | `da080d55f3ca0a0f36a32008db6d77dd8b9d6912c4e81a788bb308712d52ce5f` |
| `kK_1` | `/tmp/carbon2_job32/bld_sp_stkK_1/forge` | SP-PGO (`X+19+20+21+22+23`, #1) | `985b8dbd2dfeae587b8aeb29f1a17c2054e6afa89e30a7223258d582e6995108` | `abc3c4696963759491026948e04c81674b863bf066adde414d2a60a8b8517985` |
| `kK_2` | `/tmp/carbon2_job32/bld_sp_stkK_2/forge` | SP-PGO (`X+19+20+21+22+23`, #2) | `1ec43d9a76dedc1a92f961fda4b5bc0725f53a6fb171fbc055892b5b45b157c4` | `6c31743b93a9d8ba5600ceb2a1552518857cb3bf8cbc781ec1120c005cf47523` |
| `p21_v` | `/tmp/carbon2_job32/bld_v_p21/forge` | `-DFORGE_NNUE_V3_VERIFY=1` | `ad3643f64726af9556594741c4c1a3326f2b4169d2b7a5a96a75b4b66bf7d613` | — |
| `p22_v` | `/tmp/carbon2_job32/bld_v_p22/forge` | `-DFORGE_NNUE_V3_VERIFY=1` | `ad57596b818e0cc8c542abfa9aef92f87e0a99fc4f58d14d2f051315f2622ba2` | — |
| `p23_v` | `/tmp/carbon2_job32/bld_v_p23/forge` | `-DFORGE_NNUE_V3_VERIFY=1` | `3fc4c2ead6403c30a18c351bb0d67eddaeef7bcc35c8c03b3caf2820e95e9a0b` | — |
| `kK_v` | `/tmp/carbon2_job32/bld_v_kK/forge` | `-DFORGE_NNUE_V3_VERIFY=1` | `c990014f74107a573bc4da65a7322f171bb1036ca0e0dec56871738400ec91a4` | — |

---

## 2. Part P: `KP0`, `Table P`, Hardware Counters, Control `CP`, and Prediction 1 (`row_KP0_raw.txt`, `table_P_raw.txt`, `partP_counters_raw.txt`, `partP_CP_runs_raw.txt`, `profile_XG_lines.txt`, `profile_CP_lines.txt`)

- **Known Answer `KP0` (`row_KP0_raw.txt`):** `XG` (`A`) vs `X_1` (`B`) on `T`, `4` blocks `ABBA / BAAB` (`0` dropped, every leg `6070 / 26711499 / 937e1660561173af`):
  - **Engine CPU `B / A`:** `1.0006 0.9997 1.0026 1.0032` -> **`pooled = 1.0015`** (`61.1403 s / 61.0463 s`), `median = 1.0016`, `mean = 1.0015 [0.9989, 1.0042]`, `3/4 > 1` (**`PASS`**, inside `[0.990, 1.010]`).
  - **Wall `B / A`:** `1.0000 0.9997 1.0014 1.0031` -> `pooled = 1.0010` (`63.8847 s / 63.8206 s`), `median = 1.0007`, `2/4 > 1`.
- **Attribution Method (`categories.txt`, `profile_XG_lines.txt`):** Recorded replay `(a)` under fixed-period `sudo perf record -e task-clock -c 50000` (`50,000 ns` = `20,000` samples/CPU-s, higher than Job 31's `15,500 Hz`), extracted `forge` process IPs via `perf script -c forge`, and resolved full inline call stacks via `llvm-symbolizer-18 --inlines --functions=linkage -e <exe>`. Of `Worker::search`'s `74,110` samples (`45.92%` of `161,381` total `forge` samples), **`58,068` (`78.35%`) resolved to inlined callee files/lines outside `src/search.cpp:2406..3068`**, confirming inlined callees were attributed to their own file and line rather than merged into `Worker::search` call sites.
- **Hardware Counters (`partP_counters_raw.txt`):** None exist on this cloud VM — `perf stat -e cache-misses,dTLB-load-misses,branch-misses` reported **`<not supported>`** for all three counters.

### Table P: `Worker::search` Category Breakdown on Replay `(a)` (`table_P_raw.txt`, `categories.txt`)
| `#` | Category | Pre-Committed Line Ranges (`categories.txt`) | `XG` Samples | `%` of `T` (`161,381`) | `%` of `WS` (`74,110`) | `CP` Samples | `CP vs XG` |
|---|---|---|---|---|---|---|---|
| `1` | `hash probe and cutoff test` | `search.cpp:270-292,467-573,659-664,721-760,2444-2460,2496-2509`; `search.hpp:90-148,229-325,679-681` | `7,072` | `4.38%` | `9.54%` | `6,939` | `-1.88%` |
| `2` | `hash store` | `search.cpp:261-269,574-658,665-720,761-803,2670-2675,3051-3058`; `search.hpp:682-705` | `1,540` | `0.95%` | `2.08%` | `1,716` | `+11.43%` |
| `3` | `static evaluation call and correction terms` | `search.cpp:1714-1808,1891-2009,2467-2494,2511-2535,3061-3066`; `eval.cpp`; `nnue*.{cpp,hpp}`; `search.hpp:446-456`; `b4.hpp:77-108` | `6,510` | `4.03%` | `8.78%` | `6,790` | `+4.30%` |
| `4` | `the node-level prune steps before the move loop` | `search.cpp:235-260,1846-1890,2572-2669,2676-2687` | `1,919` | `1.19%` | `2.59%` | `1,881` | `-1.98%` |
| `5` | `move scoring and history reads` | `search.cpp:333-353,372-391,812-1660,2100-2126,2135-2140,2150-2171,2192-2197,2688-2715,2733-2743,2757-2781,2867-2870`; `search.hpp:647-675`; `b4.hpp:18-76` | `18,143` | `11.24%` | `24.48%` | `16,997` | `-6.32%` |
| `6` | `legality and make / undo` | `search.cpp:1809-1845,2749-2756,2906-2910,2916-2926,2985`; `board.hpp:338-370`; `search.hpp:175-184`; `board.cpp` (`is_legal`/`make`/`unmake`) | `18,253` | `11.31%` | `24.63%` | `14,004` | `-23.28%` |
| `7` | `the move-loop prune tests` | `search.cpp:320-323,2716-2732,2782-2866,3011-3016` | `1,809` | `1.12%` | `2.44%` | `1,256` | `-30.57%` |
| `8` | `the reduction formula` | `search.cpp:314-319,2937-2959,2964-2968`; `search.hpp:457-472` | `1,657` | `1.03%` | `2.24%` | `1,496` | `-9.72%` |
| `9` | `the child call and stack set-up` | `search.cpp:2406-2415,2435-2443,2744-2748,2871-2905,2911-2915,2927-2936,2960-2963,2969-2973,2978-2984,2987-3010,3017-3026,3067-3068,3083-3104`; `search.hpp:589-596` | `5,181` | `3.21%` | `6.99%` | `5,251` | `+1.35%` |
| `10` | `history updates after a cutoff` | `search.cpp:324-332,2127-2134,2141-2149,2172-2191,2198-2258,2536-2549,2974-2977,3027-3050` | `2,646` | `1.64%` | `3.57%` | `2,663` | `+0.64%` |
| `11` | `repetition and draw tests` | `search.cpp:2078-2099,2426-2434,3078-3082,3086-3091,3098-3102,3106-3125`; `board.cpp:1466-1489` | `3,228` | `2.00%` | `4.36%` | `3,248` | `+0.62%` |
| `12` | `node count and stop test` | `search.cpp:2010-2077,2416-2425,2986`; `search.hpp:733-760` | `442` | `0.27%` | `0.60%` | `498` | `+12.67%` |
| `13` | `everything else` (`= 13a + 13b`, split because `3.54% > 3%`) | *(sum of `13a` and `13b` below)* | `5,710` | `3.54%` | `7.70%` | `5,595` | `-2.01%` |
| `13a` | — DWARF `line-0` compiler jump-table / merged instructions | `?:0` inside `Worker::search` | `5,484` | `3.40%` | `7.40%` | `5,361` | `-2.24%` |
| `13b` | — `bare_king_mode` & misc source lines | `search.cpp:2550-2571` & misc | `226` | `0.14%` | `0.30%` | `234` | `+3.54%` |
| **SUM** | **Categories `1..13` (`Worker::search`)** | — | **`74,110`** | **`45.92%`** | **`100.00%`** | **`68,334`** | **`-7.79%`** |
| `CP` | `[CP_PLANTED_LINE]` (`volatile` 200-mul loop) | `src/search.cpp:2744` | `0` | `0.00%` | `0.00%` | `96,071` | `n/a` |

### Control `CP` Verdict (`partP_CP_runs_raw.txt`, `table_P_raw.txt`)
- **True planted cost (`6` unprofiled paired runs on replay `(a)`):** Mean `CPU(XG) = 7.607522 s`, mean `CPU(CP) = 11.792179 s` -> true planted cost = **`4.184657 s`** (`55.01%` of `XG`, `35.49%` of `CP`).
- **Planted-line attribution (`<= 25%` bar):** `src/search.cpp:2744` received `96,071` samples (`4.803550 s` at raw `50 us`/sample = **`+14.79%`** vs `4.184657 s`; `4.528800 s` scaled by `XG` s/sample = **`+8.22%`**; profile share `38.31%` vs true `35.49%` = **`+7.96%`**) -> **PASSES `<= 25%`**.
- **Category invariance (`<= 10%` bar):** Categories outside the move-loop head stayed tightly invariant (`#1 -1.88%`, `#3 +4.30%`, `#4 -1.98%`, `#9 +1.35%`, `#10 +0.64%`, `#11 +0.62%`), **but** `#7` (`-30.57%`), `#6` (`-23.28%`), `#12` (`+12.67%`), and `#2` (`+11.43%`) exceeded `10%` because the ~`1,300`-cycle serial `volatile` loop at `src/search.cpp:2744` absorbed out-of-order ROB / cache-miss skid from `picker.next` and `unmake_move` that otherwise lands on `#6` and `#7` (`#5+#6+#7` lost `5,948` samples while line `2744` gained ~`5,800` excess samples).
- **Declared `CP` verdict:** **`NOT TRUSTED`** (fails the strict `<= 10%` category-invariance check). Per the Part R rule, Part R takes its pieces from outer function shares + source-code inspection rather than trusting fine-grained source-line sample counts.

### Grading Prediction 1 (`prediction1_job32.txt`, standalone commit `6f8b16290`)
| Item | Predicted | Observed | Result |
|---|---|---|---|
| Top 3 `Worker::search` categories (`%` of `T`) | `#5` `[12.0%, 16.5%]`, `#1` `[7.0%, 11.0%]`, `#3` `[5.5%, 9.0%]` | `#6` `11.31%`, `#5` `11.24%`, `#1` `4.38%` (`#3` `4.03%`) | **PARTIAL MISS** — `#5` (`11.24%`) and `#1` (`4.38%`) were ranks `#2` and `#3`, while `#6 legality and make / undo` (`11.31%`, carrying `prefetch` `3.34%` + inlined `make`/`unmake` `KingLines` copies) edged `#5` for `#1`, and `DWARF line-0` (`3.40%`) diluted `#1/#3/#5`. |
| Hardware PMU counters exist? | `NO (<not supported>)` | `<not supported>` on all three | **HIT**. |
| `CP` planted cost (`%` of `XG` / `%` of `CP`) | `80%–140%` of `XG` (`44%–58%` of `CP`) | `55.01%` of `XG` (`35.49%` of `CP`) | **MISS (overpredicted cost)** — Sapphire Rapids overlapped store-forwarding latency (`~6–7` cycles/iter vs assumed `8–10` cycles/iter) across ~`10M` move-loop iterations (`4.185 s` vs predicted `6.0–10.5 s`). |

---

## 3. Part Q: Self-Play `Hash` Sweep and Concurrent Replays (`partQ_runs_raw.txt`, `partQ_summary_raw.txt`)

### Single-Process `Hash` Sweep on `X_1` (`4` rounds: `1..2048` on odd rounds, `2048..1` on even rounds; `U - 1 = 59`)
| `H` (`MB`) | Signature (`searches / nodes / trace`) | Searches Changed (Nodes / `bestmove`) | `GAME` (`us`, Median `[Min, Max]`) | `NODE` (`ns`, Median `[Min, Max]`) | `T2000` (`us`, Median `[Min, Max]`) | vs `H = 16` (`< 0.99` in `4`) | Reading (`H < 16`) |
|---|---|---|---|---|---|---|---|
| **`1`** | `6070/25941456/e04e0c12f6c116f8` | **`3,521` / `2,171`** | `169.42` `[167.56, 175.44]` | `276.98` `[275.97, 277.32]` | **`1191.67` `[1187.18, 1192.88]`** | **`-4.12%` (`4/4`)** | **`FASTER`** |
| **`2`** | `6070/26170596/cf664d11f9ffaa18` | `2,556` / `1,600` | `213.62` `[212.03, 216.60]` | `275.81` `[275.49, 276.42]` | **`1197.24` `[1195.71, 1199.72]`** | **`-3.67%` (`4/4`)** | **`FASTER`** |
| **`4`** | `6070/26217396/b8051d715481620d` | `1,681` / `1,092` | `286.38` `[285.02, 289.46]` | `275.52` `[275.29, 276.47]` | **`1198.22` `[1197.02, 1202.11]`** | **`-3.59%` (`4/4`)** | **`FASTER`** |
| **`8`** | `6070/26461267/7a1f73c14b76b827` | `817` / `500` | `433.63` `[428.11, 436.38]` | `277.56` `[276.90, 278.01]` | **`1218.01` `[1215.34, 1220.05]`** | **`-2.00%` (`4/4`)** | **`FASTER`** |
| **`16`** | `6070/26711499/937e1660561173af` | `0` / `0` | `731.70` `[726.50, 737.15]` | `280.55` `[278.20, 282.92]` | `1242.83` `[1232.90, 1253.22]` | `+0.00%` (`0/4`) | *(ref)* |
| `64` | `6070/26695636/a7ce0b754d0f5c67` | `180` / `137` | `2469.03` `[2408.50, 2483.89]` | `290.02` `[288.54, 291.75]` | `1285.34` `[1277.50, 1292.08]` | `+3.42%` (`0/4`) | — |
| `256` | `6070/26695636/a7ce0b754d0f5c67` | `180` / `137` | `9899.17` `[9647.50, 9951.83]` | `305.53` `[303.03, 307.74]` | `1353.67` `[1342.70, 1363.50]` | `+8.92%` (`0/4`) | — |
| `2048` | `6070/26695636/a7ce0b754d0f5c67` | `180` / `137` | `150607.37` `[147289.57, 153909.60]` | `329.26` `[314.20, 333.12]` | `1457.58` `[1391.11, 1493.40]` | `+17.28%` (`0/4`) | — |

- **Known answer & size control:** `H = 16` reproduced `T`'s exact signature `6070 / 26711499 / 937e1660561173af` in all `4` rounds. `GAME` scaled directly with TT size (`~160 us` non-TT overhead + `~36–38 us/MB` in L3/DRAM, rising to `9.90 ms` at `256` MB — right beside the predicted `~9 ms` — and `150.61 ms` at `2048` MB where `2 GiB` completely overflows LLC into DRAM bandwidth), **confirming Part Q's size control fired**. Meanwhile `H = 64, 256, 2048` MB produced the **identical** search trace (`6070 / 26695636 / a7ce0b754d0f5c67`, `180` node diffs / `137` `bestmove` diffs vs `H = 16`), proving that by `64` MB (`2M` clusters for ~`445K` nodes/game) index collisions have already vanished while per-node latency (`NODE`) climbs monotonically from `275.52 ns` (`H = 4`) to `329.26 ns` (`H = 2048`) as TT probes miss deeper cache levels.
- **Smallest `FASTER` `H` (`H = 1` MB):** `3,521` of `6,070` searches (`58.0%`) changed in final node count and `2,171` (`35.8%`) changed in `bestmove` relative to `H = 16` MB. (Notably, `H = 4` MB achieves nearly the same `NODE` minimum — `275.52 ns` vs `276.98 ns` at `H = 1` MB — and `-3.59%` `T2000` with less than half as many changed searches: `1,681` node / `1,092` `bestmove`.)
- **Side-by-Side Concurrent Replays (`N = nproc - 1 = 3` concurrent processes on CPUs `1, 2, 3`, `2` rounds in turn `[2, 16]` then `[16, 2]`, `partQ_runs_raw.txt` & `partQ_summary_raw.txt`):**
  - **`H = 2` MB (`6` replay instances):** Engine CPU median **`7.3090 s`** `[7.2728, 7.3397]` (`mean = 7.3090 s`, `1204.12 us`/search); wall median **`7.3602 s`** `[7.3225, 7.3914]` (`mean = 7.3597 s`, `1212.47 us`/search).
  - **`H = 16` MB (`6` replay instances):** Engine CPU median **`7.5633 s`** `[7.5496, 7.6225]` (`mean = 7.5733 s`, `1247.66 us`/search); wall median **`7.6193 s`** `[7.6064, 7.6775]` (`mean = 7.6304 s`, `1257.07 us`/search).
  - Concurrent `H = 2` MB is **`-3.36%` faster in CPU** (`6/6` instances below all `6/6` `H = 16` instances) and **`-3.40%` faster in wall**.

---

## 4. Part R: Three Node-Keeping Pieces from Outer Function Shares + Source Code (`partR_verify_raw.txt`)

Because Control `CP` read `NOT TRUSTED` on category invariance and hardware PMU counters are `<not supported>` on this VM, all three pieces were selected from outer ELF symbol shares (`profile_XG_lines.txt` lines `8–27`) + source inspection, and every microarchitectural mechanism below is explicitly **marked as a reading**:

1. **Piece `21` (`21_corr_prefetch_and_fast_keys.patch.txt`):**
   - **Functions, lines & share:** `Worker::search` (`45.92%` outer share), `Worker::qsearch` (`5.54%`), and `Worker::static_evaluate_v3` (`9.28%`) — specifically `material_key`, `non_pawn_key`, `Worker::corrected_eval`, and the `static_evaluate` call sites at `include/forge/search.hpp:724` and `src/search.cpp:1714–1733, 1901–1942, 2311–2312, 2475–2477, 2518–2522` (Category `#3`, `4.03%` of `T` in `XG`).
   - **What the time is spent on *(reading, no PMU counters)*:** **(a) L2/L3 cache-miss stall** across five `128 KiB` correction tables (`correction_history_`, `material_correction_`, `non_pawn_white_correction_`, `non_pawn_black_correction_`, `joint_correction_` = `640 KiB` total per worker, exceeding the `48 KiB` L1d) touched back-to-back in `corrected_eval` right after `static_evaluate_v3` returns, plus **(b) a 10-step serial 64-bit FNV multiply dependency chain** in `material_key(board)` (`~30+` cycles serial latency) and loop overhead in `non_pawn_key`.
   - **The change & why no search can change:** Replaces `material_key` with its exact algebraic closed-form compile-time weighted dot product `kMatBase + sum_i popcount(bb_i) * kMatWeights[i]` over $\mathbb{Z}/2^{64}\mathbb{Z}$ (bit-for-bit identical `uint64_t` on every board), unrolls `non_pawn_key` over `Knight..King`, and adds `Worker::prefetch_corrections(board, ss)` right before `static_evaluate(board, ss)` (only on branches that have already passed TT cutoffs and lack a cached `tte.eval`, so zero work is added on TT cutoffs) to populate `ss->corr_*` cache slots and `__builtin_prefetch` all five correction entries while `static_evaluate_v3` executes (~`250` cycles). `__builtin_prefetch` is architectural no-op on state, `ss->corr_*` stores the identical indices `corrected_eval` would compute a moment later, and `material_key`/`non_pawn_key` compute identical `uint64_t` values.

2. **Piece `22` (`22_movepicker_branchless_push_and_zerocopy_checks.patch.txt`):**
   - **Functions, lines & share:** `MovePicker::generate_quiets` + lambda (`4.28%` outer share), `MovePicker::generate_captures` (`1.67%`), `MovePicker::generate_evasions` (`1.79%`), and `MovePicker::next` inside `Worker::search` (`45.92%`) at `src/search.cpp:898–910, 1009–1055, 1175–1195, 1218–1240, 1350–1398, 1605–1615` (Category `#5`, `11.24%` of `T`).
   - **What the time is spent on *(reading, no PMU counters)*:** **(a) Data-dependent branch mispredictions** on `if (!seeded_ || score > seeded_score_)` inside `MovePicker::push_scored` across `~30–45` generated moves per node as history scores fluctuate unpredictably, plus **(b) redundant `56`-byte `std::array<Bitboard, 7>` stack copying** in `init_check_squares()` (`check_squares_ = kl.check_squares`) and `48` bytes of extra stack frame footprint per recursive ply.
   - **The change & why no search can change:** Removes `seeded_`, `seeded_at_`, and `seeded_score_` so `push_scored` is a single unconditional store `moves_[count_++] = Scored{move, score};`, and under `FORGE_SPD_KING_LINES` stores a `const std::array<Bitboard, 7>* check_squares_ = &kl.check_squares;` pointer instead of copying `56` bytes. On the first pick (`index_ == list_start_`), `pick_best_scored()`'s strict `>` scan (and AVX-512 argmax mask `__builtin_ctz`) already selects the exact same leftmost maximum element and performs the exact same `std::swap(moves_[index_], moves_[best])` that `seeded_at_` performed; meanwhile `board_` sits at a fixed stack/member address and every child `make_move`/`unmake_move` (including singular searches) restores `board_.king_lines_.check_squares` to its exact bitboards before the next `picker.next` call.

3. **Piece `23` (`23_compact_undo_kinglines_and_fast_draw_gates.patch.txt`):**
   - **Functions, lines & share:** `Board::make_move` / `unmake_move` / `make_null_move` / `unmake_null_move`, `Board::is_repetition`, `Board::is_insufficient_material`, and `Board::set_fen` inside `Worker::search` (`45.92%`) and `Worker::qsearch` (`5.54%`) at `include/forge/board.hpp:140–178, 236–252, 320–332` and `src/board.cpp:364–370, 1166–1225, 1364–1412, 1488–1515` (Categories `#6` `11.31%` and `#11` `2.00%` of `T`).
   - **What the time is spent on *(reading, no PMU counters)*:** **(a) Out-of-line call + prologue/return overhead on every node** in `Worker::is_draw` calling `board.is_repetition` and `board.is_insufficient_material` even when `halfmove_ < 4 || plies_from_null_ < 4` (`~75–85%` of nodes cannot repeat) or `(pieces(Pawn) | pieces(Rook) | pieces(Queen)) != 0` (`> 99%` of middlegame/endgame nodes have sufficient material), plus **(b) `24` bytes of redundant `KingLines` memory traffic** (`NoPieceType`, `King` always `0`, and `Queen == Bishop | Rook`) copied on every `make_move` and `unmake_move`.
   - **The change & why no search can change:** Replaces `Undo::king_lines` / `NullUndo::king_lines` with `56`-byte `SavedKingLines` (`valid, pinned, discoverers, chk_p, chk_n, chk_b, chk_r`, reconstructing `check_squares[Queen] = chk_b | chk_r` on restore while `[NoPieceType]` and `[King]` remain `0`), hoists exact necessary false-conditions inline into `Board::is_repetition` (`halfmove_ < 4 || plies_from_null_ < 4`) and `Board::is_insufficient_material` (`(pieces(Pawn) | pieces(Rook) | pieces(Queen)) != 0`), and reserves `key_history_.reserve(2048)` in `set_fen`. Every skipped call would have immediately returned `false` on its first lines in `src/board.cpp`, and `check_squares[Queen]` in `ensure_king_lines()` is defined identically as `check_squares[Bishop] | check_squares[Rook]`.

### Known Answers on `p21_1`, `p22_1`, `p23_1`, `kK_1`, `kK_2` (`partR_verify_raw.txt`, `partS_verify_raw.txt`)
| Build | Job 26 (`7` checks) | Job 20 (`60g`) | `T` (`60g`) | `n1` (`T[1..3]` masked) | `n2` (`V3_VERIFY=1` `T[1..10]`) | `n3` (`S=1` replay `(b)`) | `n4` (`T[1..10]+g1`) |
|---|---|---|---|---|---|---|---|
| `p21_1` | `PASS` (`312866/862329/4865609`; `278024/587276`; `625258/3652372`; `882074/4275906`) | `7670/25641316/ee465caeff9c0fcf` | `6070/26711499/937e1660561173af` | `4,847` lines, `0` diffs | `1089/4497849/b8af7c43c78aca2c`, `0` `FAILED` | `6070/23787/f331c1bb14017ed4` (`15,720` lines) | `2,599 == 2,599`, `0` diffs |
| `p22_1` | `PASS` (all `7` exact) | `7670/25641316/ee465caeff9c0fcf` | `6070/26711499/937e1660561173af` | `4,847` lines, `0` diffs | `1089/4497849/b8af7c43c78aca2c`, `0` `FAILED` | `6070/23787/f331c1bb14017ed4` (`15,720` lines) | `2,599 == 2,599`, `0` diffs |
| `p23_1` | `PASS` (all `7` exact) | `7670/25641316/ee465caeff9c0fcf` | `6070/26711499/937e1660561173af` | `4,847` lines, `0` diffs | `1089/4497849/b8af7c43c78aca2c`, `0` `FAILED` | `6070/23787/f331c1bb14017ed4` (`15,720` lines) | `2,599 == 2,599`, `0` diffs |
| `kK_1` | `PASS` (all `7` exact) | `7670/25641316/ee465caeff9c0fcf` | `6070/26711499/937e1660561173af` | `4,847` lines, `0` diffs | `1089/4497849/b8af7c43c78aca2c`, `0` `FAILED` | `6070/23787/f331c1bb14017ed4` (`15,720` lines) | `2,599 == 2,599`, `0` diffs |
| `kK_2` | `PASS` (all `7` exact) | `7670/25641316/ee465caeff9c0fcf` | `6070/26711499/937e1660561173af` | `4,847` lines, `0` diffs | `1089/4497849/b8af7c43c78aca2c`, `0` `FAILED` | `6070/23787/f331c1bb14017ed4` (`15,720` lines) | `2,599 == 2,599`, `0` diffs |

---

## 5. Part S: `C32`, `K1`, `K2`, `KS`, Bundle Reading, and Prediction 2 (`ctrl_C32_raw.txt`, `row_K1_raw.txt`, `row_K2_raw.txt`, `row_KS_raw.txt`, `prediction2_job32.txt`)

### Control `C32` and Deciding Rows `K1` and `K2` (`B / A`; `> 1` means `A` uses less time than `B`)
| Row | `A` vs `B` | Blocks | Metric | Block Ratios (`B / A`) | Pooled (`sumB / sumA`) | Median | Mean & 95% $t$-CI | `> 1` | Reading |
|---|---|---|---|---|---|---|---|---|---|
| **`C32`** | `X_1` (`sn2000`) vs `X_1` (`sn2200`, `5853/28387596/f37b0151ac18bd56`) | `4` (`0` dropped) | Engine CPU | `1.0743 1.0766 1.0721 1.0752` | **`1.0745`** (`65.8427 / 61.2771`) | `1.0747` | `1.0745 [1.0715, 1.0775]` | **`4/4`** | **`PASS`** (`> 1.0116`, `4/4`) |
| `C32` | (wall) | `4` | Wall | `1.0790 1.0792 1.0761 1.0789` | `1.0783` (`67.9339 / 63.0012`) | `1.0790` | `1.0783 [1.0759, 1.0807]` | `4/4` | — |
| **`K1`** | `kK_1` vs `X_1` on `T` (`6070/26711499/937e1660561173af`) | `12` (`0` dropped) | Engine CPU | `1.0209 1.0131 1.0208 1.0194 1.0215 1.0263 1.0201 1.0194 1.0195 1.0208 1.0213 1.0204` | **`1.0203`** (`183.2800 / 179.6356`) | **`1.0206`** | `1.0203 [1.0184, 1.0221]` | **`12/12`** | **`>= 1.0116` (`12/12`)** |
| `K1` | (wall) | `12` | Wall | `1.0225 1.0123 1.0213 1.0198 1.0219 1.0259 1.0197 1.0204 1.0192 1.0210 1.0224 1.0205` | `1.0206` (`191.7456 / 187.8778`) | `1.0208` | `1.0206 [1.0186, 1.0226]` | `12/12` | — |
| **`K2`** | `kK_2` vs `X_2` on `T` (`6070/26711499/937e1660561173af`) | `12` (`0` dropped) | Engine CPU | `1.0113 1.0163 1.0191 1.0161 1.0164 1.0141 1.0125 1.0196 1.0002 1.0190 1.0075 1.0159` | **`1.0140`** (`183.1607 / 180.6359`) | **`1.0160`** | `1.0140 [1.0104, 1.0176]` | **`12/12`** | **`>= 1.0116` (`12/12`)** |
| `K2` | (wall) | `12` | Wall | `1.0067 1.0186 1.0207 1.0166 1.0171 1.0159 1.0110 1.0179 1.0031 1.0220 1.0138 1.0188` | `1.0152` (`190.4782 / 187.6333`) | `1.0168` | `1.0152 [1.0116, 1.0188]` | `12/12` | — |
| `K2 (1..6)` | (`6`-block prefix of `K2`, per Minute-70 rule) | `6` | Engine CPU / Wall | `1.0113 1.0163 1.0191 1.0161 1.0164 1.0141` | **`1.0155`** (`91.6534 / 90.2509`) / `1.0159` | `1.0162` | `1.0155 [1.0128, 1.0183]` | **`6/6`** | **`>= 1.0116` (`6/6`)** |

- **Bundle `kK` reading:** **`PAYS`** — both `K1` (`pooled = 1.0203 >= 1.0116`, `12/12 >= 10/12`) and `K2` (`pooled = 1.0140 >= 1.0116`, `12/12 >= 10/12`, with `6`-block prefix `1.0155`, `6/6`) clear the `PAYS` bar on independent SP-PGO builds.
- **For the record (`row_KS_raw.txt`, `1` replay set each of `kK_1` and `kK_2`, run last; `U - 1 = 59`):**
  - **`kK_1`:** `START = 57957.00 us`, `GAME = 710.13 us`, `S1 = 9.76 us`, **`FIXED = 8.67 us`** (`U=60`: `8.55 us`, `0.707%` of `T2000`), `T2000 = 1227.24 us`, `NODE = 276.911 ns`.
  - **`kK_2`:** `START = 61162.00 us`, `GAME = 714.57 us`, `S1 = 8.31 us`, **`FIXED = 7.23 us`** (`U=60`: `7.11 us`, `0.593%` of `T2000`), `T2000 = 1218.12 us`, `NODE = 275.168 ns`.

### Grading Prediction 2 (`prediction2_job32.txt`, standalone commit `c2a5b77ff`)
| Item | Predicted | Observed | Result |
|---|---|---|---|
| `K1` pooled CPU (`X_1 / kK_1`) | `[1.0160, 1.0320]` | **`1.0203`** (`12/12 > 1`) | **HIT** (squarely inside range). |
| `K2` pooled CPU (`X_2 / kK_2`, predicted for `6` blocks under Minute-70 rule) | `[1.0150, 1.0320]` | **`1.0155`** on `6`-block prefix (`6/6 > 1`); **`1.0140`** on full `12` blocks (`12/12 > 1`, `median = 1.0160`) | **HIT on the `6`-block prefix (`1.0155`)**; `0.0010` below `[1.0150, 1.0320]` on the full `12`-block pooled (`1.0140`) due to noisy legs in blocks `9` and `11` (`1.0002`, `1.0075`). |
| Bundle `kK` reading | `PAYS` | **`PAYS`** | **HIT**. |

---

## 6. Facts, Suspicions, What I Did Not Do, What I Am Not Sure About, and Model Name

### Facts (established directly from committed raw files)
1. Adding `-gline-tables-only` to `X`'s SP-PGO recipe (`XG`) preserved `T`'s exact trace and did not slow the binary (`KP0` pooled CPU `1.0015`, `95% t-CI [0.9989, 1.0042]`).
2. `Worker::search` accounts for `45.92%` of `T`, with `45.92%` decomposing cleanly into `11.31%` legality/make/undo (including `3.34%` on `TranspositionTable::prefetch` at make sites), `11.24%` move scoring & history reads (including `2.90%` inlined `pick_best_scored` `std::sort` + `1.88%` out-of-line `__introsort_loop`), `4.38%` TT probe/cutoff, `4.03%` static eval wrapper & correction terms, `3.40%` DWARF `line-0` merged instructions, `3.21%` child call/stack setup, `2.00%` draw/repetition tests, and `6.35%` across remaining categories.
3. Shrinking `Hash` below `16` MB on `T` (`go softnodes 2000`, `60` games) speeds `T2000` in `4/4` rounds at every tested size `H in {1, 2, 4, 8}` MB (`-4.12%`, `-3.67%`, `-3.59%`, `-2.00%`) and speeds `N = 3` concurrent replays at `H = 2` MB by `-3.36%` CPU / `-3.40%` wall, while `H >= 64` MB changes zero nodes (`6070 / 26695636 / a7ce0b754d0f5c67` at `64`, `256`, and `2048` MB) and only slows `NODE` (`280.55 ns` at `16` MB $\to$ `329.26 ns` at `2048` MB) and `GAME` (`0.73 ms` $\to$ `150.61 ms`).
4. Bundle `kK = X + 19 + 20 + 21 + 22 + 23` preserves every node, score, PV line, NNUE v3 accumulator check (`0` `FAILED`), `softnodes-1` trace, and cross-game `ucinewgame` state (`n1..n4`), and reads **`PAYS`** (`K1 = 1.0203`, `12/12 > 1`; `K2 = 1.0140`, `12/12 > 1`, `6`-block prefix `1.0155`).

### Suspicions (hypotheses, not established facts)
1. **Why `kK` jumped from `kJ`'s `+0.44%` (`1.0044`) to `+1.40%..+2.03%` (`1.0140` / `1.0203`):** Piece `21`'s `prefetch_corrections` overlaps five random `128 KiB`-table loads (`640 KiB` working set) with `static_evaluate_v3`'s ~`250`-cycle SIMD evaluation, removing genuine memory-level stall latency rather than rewriting ALU arithmetic, while Piece `23`'s inline `is_repetition` / `is_insufficient_material` gates and Piece `22`'s branchless `push_scored` remove call overhead and unpredictable running-max branches.
2. **Self-play `Hash` sweet spot for the PC:** On `softnodes 2000`, `H = 4` MB (`131,072` clusters = `524,288` entries for ~`445K` nodes/game) captures `87%` of `H = 1` MB's `T2000` speedup (`-3.59%` vs `-4.12%`) and reaches the global `NODE` minimum (`275.52 ns`) while cutting search-tree perturbations in more than half (`1,092` `bestmove` diffs vs `2,171` at `H = 1` MB), and `16` concurrent workers at `H = 2..4` MB occupy `32–64 MiB` total vs `256 MiB` at `H = 16` MB.

### What I Did Not Do
1. Did not measure individual ABBA speed rows for `p21_1`, `p22_1`, and `p23_1` alone (Part R asked for known-answer verification on each piece build and Part S timed the combined bundle `kK` on `K1` and `K2`).
2. Did not touch `std::sort` in `MovePicker::pick_best_scored` (`src/search.cpp:1199`), because `src/search.cpp:1638` documents that `std::sort`'s unstable tie-breaking swap sequence affects move order on equal scores and would violate node-keeping.
3. Did not add a second TT prefetch (per Part Q's explicit note that `tt.prefetch` already runs at make sites).

### What I Am Not Sure About
1. Which fraction of `kK`'s ~`+1.6%` additional gain over `kJ` (`+0.44%` $\to$ `+1.40%..+2.03%`) comes from Piece `21` (correction-table prefetch + closed-form `material_key`) versus Piece `22` (branchless `push_scored` + zero-copy `check_squares_`) versus Piece `23` (compact `SavedKingLines` + inline draw gates), since they were timed together in `kK`.
2. Whether `kK`'s gain is even larger on the busy Windows PC (`7–16` engines sharing LLC), where `640 KiB` of per-worker correction tables (`5–10 MiB` across `8–16` workers) suffer higher L3 eviction pressure than on our single-worker cloud core.

### Model Name
`Gemini 4 Carbon`

---

## 7. Verbatim Output of `git status --short && ls -R forge-combo29/carbon2/job32` Before Report Commit

```text
?? forge-combo29/carbon2/job32/REPORT_carbon2_job32.md
forge-combo29/carbon2/job32:
21_corr_prefetch_and_fast_keys.patch.txt
22_movepicker_branchless_push_and_zerocopy_checks.patch.txt
23_compact_undo_kinglines_and_fast_draw_gates.patch.txt
builds.txt
categories.txt
CP_planted_moveloop_muls.patch.txt
ctrl_C32_raw.txt
partP_counters_raw.txt
partP_CP_runs_raw.txt
partQ_runs_raw.txt
partQ_summary_raw.txt
partR_verify_raw.txt
partS_verify_raw.txt
prediction1_job32.txt
prediction2_job32.txt
profile_CP_lines.txt
profile_XG_lines.txt
REPORT_carbon2_job32.md
row_K1_raw.txt
row_K2_interrupted_raw.txt
row_K2_raw.txt
row_KP0_raw.txt
row_KS_raw.txt
stamps.txt
step0_raw.txt
table_P_raw.txt
```

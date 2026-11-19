# Report — carbon2 Job 31: Fixed Per-Search and Per-Game Cost on `X = kH`, Control `CF`, and Node-Keeping Bundle `kJ`

## Summary (First Lines)

1. **Step 0 & Selection of `X` (`step0_raw.txt`, `builds.txt`):** In Job 30, Part V (`V1`, `V2`, `V3`) read `KEEPS` everywhere (`0` differences / `0` reports) and bundle `kH = kG + 17 + 18` read **`PAYS`** (`H1` pooled CPU `1.0244`, `12/12 > 1`; `H2` pooled CPU `1.0194`, `12/12 > 1`). Therefore **`X = kH`** (`X_1 = kH_1`, `X_2 = kH_2`). `X_1`, `X_2`, and `kF_sp_1` were **reused** after verifying their `sha256`s matched `job30/builds.txt`; `D = bld_sp_r15d_1` (Job 21's first `r15d` build) was **rebuilt** with the same ThinLTO + SP-PGO recipe at its `38`-byte path `/tmp/carbon2_job11/bld_sp_r15d_1/forge`. All four passed in fresh processes: `312866 / 862329 / 4865609`, `PC20 + net768` `882074 / 4275906`, and `T` `6070 / 26711499 / 937e1660561173af`.
2. **Part F (`partF_KF0_KF1_CFcheck_raw.txt`, `partF_runs_raw.txt`, `partF_summary_raw.txt`):** Command list `L` (`12,287` lines, `sha256=73bec774f2b70f7148f4bcc81232666d366fcac1e8a9928b820b284477c46dce`, **`U = 60`** `ucinewgame` commands; first `60` lines in `L_head.txt`). **`KF0` passed** (`6070 / 26711499 / 937e1660561173af`, `72,838` output lines). **`KF1` (`S = 1`) gave one identical signature on `D`, `kF_sp_1`, `X_1`, and `X_2`:** `6070 / 23787 / f331c1bb14017ed4` (`15,720` lines; per-search final count `min = 0`, `median = 4.0`, `max = 4` across all `6,070` searches, and `min = 2`, `median = 4.0`, `max = 4` across the `6,022` non-terminal searches). On `X_1` / `X_2` (`6` paired rounds): **`FIXED = 7.74 us` (`0.627%` of `T2000 = 1236.17 us`) on `X_1` and `7.81 us` (`0.631%` of `T2000 = 1230.87 us`) on `X_2`**; **`GAME = 707.56 us` (`0.559%` of a `T` game) on `X_1` and `710.40 us` (`0.561%` of a `T` game) on `X_2`**. Control **`CF` FIRED** (`CF` `FIXED` median `24.71 us` `[24.37, 24.87]` vs `X_1` `7.74 us` `[7.52, 7.87]`, `+16.97 us >= 10 us`, `6/6` above `6/6`). Linearity check on `X_1`: `S = 250` lies `-3.44%` below `FIXED + NODE * nodes` (`121.04 us` vs `125.36 us`); `S = 8000` lies `-0.30%` below (`4246.46 us` vs `4259.34 us`). **Part F reading: `SMALL`** (`FIXED < 3%` of `T2000` and `GAME < 1%` of a `T` game on both builds).
3. **Part G (`profile_S1.txt`, `profile_T_X1.txt`, `syscalls_S1.txt`, `partG_once_per_search_and_game.txt`):** `perf` (`17,490` samples on `S = 1`) and `perf trace -s` (`6.5636` net syscalls/search: `3.0002` `futex`, `2.5634` `write`, `1.0000` `read`) show the largest single once-per-search item is the UCI $\leftrightarrow$ search-thread condvar hand-off (`3.78 us` = `48.8%` of `FIXED` = **`0.306%` of `T2000`**), and `TranspositionTable::clear()` is `564.90 us` = `79.8%` of `GAME` (`0.446%` of a `T` game). Because Part F read `SMALL` and no item in Part G exceeds `1%` of `T2000`, Part H followed the fallback branch to `T`'s profile.
4. **Part H (`19_fast_has_legal_move.patch.txt`, `20_v3_fast_refresh_and_pair.patch.txt`, `CN4_no_ucinewgame_tt_clear.patch.txt`, `partH_known_answers_raw.txt`):** Built SP-PGO `p19_1` (inline `Board::has_legal_move` ray-free pawn/knight check + `has_legal_move_slow` pin/evasion fast returns; `3.11%` of `T`, `0.0%` of `FIXED`) and `p20_1` (`nnue::v3` fast non-king `replay_ply_from`, direct AVX-512 `apply_changes_pair`, hoisted `p_base` + `inc_shape` in `apply_one_refresh_one_and_evaluate` and `refresh_from_pieces`; `9.74%` direct self share in `T`, `0.0%` of `FIXED`). Both `p19_1` and `p20_1` passed all `7` Job 26 checks, Job 20 `7670/25641316/ee465caeff9c0fcf`, `T` `6070/26711499/937e1660561173af`, `n1` (`4,847` lines, `0` diffs), `n2` (`1089/4497849/b8af7c43c78aca2c`, `0` `FAILED`), `n3` (`6070/23787/f331c1bb14017ed4`, `15,720` lines), and `n4` (`2,599` lines, `0` diffs). Control **`CN4` FIRED** (`2,594` line differences on the second game `1`, starting on line `1`: `nodes 48 ... hashfull 23` vs `nodes 55 ... hashfull 0`).
5. **Part I (`ctrl_C31_raw.txt`, `row_J1_raw.txt`, `row_JS_raw.txt`):** `kJ_1` and `kJ_2` (`X + 19 + 20`) passed every known answer including `n1..n4`. **`C31` passed** (`pooled` CPU `1.0745 > 1.0116`, `4/4 > 1`; wall `1.0777`, `4/4 > 1`). **`J1` (`kJ_1` vs `X_1`, `12` blocks):** CPU `pooled = 1.0044`, `median = 1.0046`, `mean = 1.0044` (`95% t-CI [1.0030, 1.0058]`), `12/12 > 1` (wall `pooled = 1.0041`, `median = 1.0039`, `12/12 > 1`) -> **`J1` reads `NOT SEEN`** (`1.0044 < 1.0116`). **`JS` (`6` runs each of `kJ_1`, `kJ_2`):** `FIXED = 8.14 us` `[7.51, 9.89]` on `kJ_1`, `7.86 us` `[7.63, 8.67]` on `kJ_2`; `GAME = 673.25 us` `[660.31, 686.19]` on `kJ_1`, `675.55 us` `[668.05, 687.69]` on `kJ_2` (`T2000` dropped from `1236.17 / 1230.87 us` on `X_1 / X_2` to `1217.66 / 1214.34 us` on `kJ_1 / kJ_2`, ~`1.3%–1.5%` in single-process replay `(a)`). **`J2` was NOT RUN** because `JS` finished at `09:01:32 PM UTC` (`minute 79m 33s` from `07:42:59 PM UTC` claim, `< 1` minute before the hard Minute-80 work stop). Because `J1` read `NOT SEEN` (`1.0044 < 1.0116`) and `J2` was stopped before starting at Minute 80, **bundle `kJ` does not read `PAYS` (`J1 = NOT SEEN`; `J2` not done at Minute 80)**.

---

## 1. Step 0, Choice of `X`, and All Builds & Patches (`step0_raw.txt`, `builds.txt`)

- **Engine base commit:** `6b98f2170a3210e71beed04bbd2553972c253ed7` (unchanged in `/agent/repos/dwqww`).
- **Why `X = kH`:** Job 30's Part V read `KEEPS` on `V1`, `V2`, and `V3`, and Job 30's bundle `kH = kG + 17 + 18` read `PAYS` on both build pairs (`H1 = 1.0244`, `H2 = 1.0194`).
- **Command list `L` (`/tmp/carbon2_job31/L.txt`, head in `L_head.txt`):** `12,287` lines, `sha256 = 73bec774f2b70f7148f4bcc81232666d366fcac1e8a9928b820b284477c46dce`, **`U = 60`** `ucinewgame` commands (`1` at 1-based line `28` before the first `position` command at 1-based line `30`, plus `59` between games `2..60`).

### Patches Committed in `forge-combo29/carbon2/job31/`
| Patch File | Base | `sha256` |
|---|---|---|
| `CF_planted_1mb_memset.patch.txt` | `X = kH` | `cd85a1dabd82ba73e0007c88506383d81c5f28ac5f8a33ebe10356e0b25cd622` |
| `19_fast_has_legal_move.patch.txt` | `X = kH` | `0caaf54bfb958c898e66c8a97681f9fe8eae4558a96cbd082680f9eca8385cd3` |
| `20_v3_fast_refresh_and_pair.patch.txt` | `X = kH` | `07b0df4b8c5d3854b60dd3931811ba72fafd1658ed8885096df2f94907a4e200` |
| `CN4_no_ucinewgame_tt_clear.patch.txt` | `X = kH` | `ad1552370d82c2e2a0bdf0b831543bafabb4a5c12578347b057125a7d192acde` |

### Executables Built or Reused (`builds.txt`)
| Build | Path (`len=38` for all SP-PGO exes) | Provenance | Executable `sha256` | `.profdata` `sha256` |
|---|---|---|---|---|
| `X_1` (`kH_1`) | `/tmp/carbon2_job30/bld_sp_stkH_1/forge` | Reused (Job 30 match) | `41f147ec4482904557dddfc0089378a3fd7e0af6104ca661981d8db7fbe57140` | (Job 30 `builds.txt`) |
| `X_2` (`kH_2`) | `/tmp/carbon2_job30/bld_sp_stkH_2/forge` | Reused (Job 30 match) | `66bf617597720713dcab079b8e6d8e21087b5870e8eefffac121a442c76413c1` | (Job 30 `builds.txt`) |
| `kF_sp_1` | `/tmp/carbon2_job17/bld_sp_tidy_1/forge` | Reused (Job 28/30 match) | `c16daacc5987a820801c792ec4ffbb5f997f2c8d97af4399aa365c5edc473b4e` | (Job 28 `builds.txt`) |
| `D` (`bld_sp_r15d_1`) | `/tmp/carbon2_job11/bld_sp_r15d_1/forge` | Rebuilt SP-PGO (Job 21 1st `r15d`) | `31489d73bb8f3fa8af14c020bb1f419ded39dc835b0dd3e0b2fee9cddf6faf03` | `7ec91d0bbf8dc50ba53817a4eea858e242403ded7096ba7bf41a96eba834c77f` |
| `CF` | `/tmp/carbon2_job31/bld_sp_ctrlCF/forge` | Fresh SP-PGO (`X + CF`) | `c754b67400d67be485b041877c8d68683cb735d39ec2c4f46454a5cbd570f4f7` | `52471bd9e7ab9c1f7a6e5dcfe031d1e9667f0cadff86a690e0dcaa6f1f3525b6` |
| `p19_1` | `/tmp/carbon2_job31/bld_sp_1p19_1/forge` | Fresh SP-PGO (`X + 19`) | `848be3a98821ec48a1fad3b626dadc03330783ff9aa9f2a88704b4c2c329462f` | `c5e12c5725f7a73cdc655d857e5f7579fd1fdab5f435240164607bee747ee55b` |
| `p20_1` | `/tmp/carbon2_job31/bld_sp_1p20_1/forge` | Fresh SP-PGO (`X + 20`) | `a9ee40cec26d8c12cb8148c0c74ad2577f4f893c09b84273f4097895c4a5a113` | `ce5847434a75e5bfac8e4a9cdca8e5c8f594816b949f149dfedf0ab38219a4dc` |
| `kJ_1` | `/tmp/carbon2_job31/bld_sp_stkJ_1/forge` | Fresh SP-PGO (`X + 19 + 20`, #1) | `3bed693e6c8f863aecd48b301f110a49465a52b3d8e3d343b004d63f32e655a3` | `c0eec8e69b54f4aaf18959c7741a2a6ae04cfecf74d778887d86b39b20dc3b3f` |
| `kJ_2` | `/tmp/carbon2_job31/bld_sp_stkJ_2/forge` | Fresh SP-PGO (`X + 19 + 20`, #2) | `781909dfe20ecb792eac607907d0663298a85bc9854581a747bf75cbe41881a1` | `08164110843a76d73070ea552a5a2712b7632464fc0a91d4ca9b0d5453eb5854` |
| `p19_v` | `/tmp/carbon2_job31/bld_v_p19/forge` | ThinLTO `-DFORGE_NNUE_V3_VERIFY=1` | `de41bee6d87832e9f2b5e809a7b9cd009f7e83ba79c672334a097e9a479ef8a0` | — |
| `p20_v` | `/tmp/carbon2_job31/bld_v_p20/forge` | ThinLTO `-DFORGE_NNUE_V3_VERIFY=1` | `30344bbce5e24dfd6a5fb8a8ca626825bb1dc8f07236764f7bb2d112cd3e5a2e` | — |
| `kJ_v` | `/tmp/carbon2_job31/bld_v_kJ/forge` | ThinLTO `-DFORGE_NNUE_V3_VERIFY=1` | `68fd7f182182e373429f5b9c59818e4d2eba4d034aff73714f89fe6fdf084a36` | — |
| `CN4` | `/tmp/carbon2_job31/bld_thin_CN4/forge` | ThinLTO (`X + CN4`) | `b1788960dae0afa9e088985f50ad730f38ce779f9dc22d4961bee29fe66847b1` | — |

---

## 2. Part F: `KF0`, `KF1`, Fixed-Cost Table, `S = 250 / 8000` Check, Control `CF`, Reading, and Prediction 1 (`partF_KF0_KF1_CFcheck_raw.txt`, `partF_runs_raw.txt`, `partF_summary_raw.txt`)

- **`KF0` (`X_1` replay `(a)`):** `searches=6070 final_nodes=26711499 trace=937e1660561173af lines=72838` — matches `T`'s signature (`PASS`).
- **`KF1` (replay `(b)` with `S = 1` on `D`, `kF_sp_1`, `X_1`, `X_2`):** All four builds gave the **exact same signature**: `searches=6070 final_nodes=23787 trace=f331c1bb14017ed4 lines=15720`. Across all `6,070` searches: **`min_final = 0`, `median_final = 4.0`, `max_final = 4`** (`48` mated/stalemated roots emit `0` nodes and `bestmove 0000`; across the `6,022` searches that emit `info string softnodes nodes`, `min = 2`, `median = 4.0`, `max = 4`).
- **How `CF` kept the `1 MiB` `std::memset`:** `CF_planted_1mb_memset.patch.txt` places `static char pad[1 << 20]; std::memset(pad, static_cast<int>(pad[0] + 1), sizeof pad); asm volatile("" : "+m"(pad) : : "memory");` at the top of `Searcher::search` (`src/search.cpp`), preventing ThinLTO dead-store elimination. `llvm-objdump-18 -d` on `/tmp/carbon2_job31/bld_sp_ctrlCF/forge` (`builds.txt` lines `14-19`) confirms `movl $0x100000, %edx` + `callq 0xda060 <memset@plt>` at `0xbdb67..0xbdb6c`, and `CF` replay `(a)` gave `6070 / 26711499 / 937e1660561173af` (`72,838` lines).

### Part F Table (`6` paired rounds in turn `(X_1,X_2,CF), (CF,X_2,X_1), (X_2,CF,X_1), (X_1,CF,X_2), (X_1,X_2,CF), (CF,X_2,X_1)`; `U = 60`)
| Metric | `X_1` Median `[Min, Max]` | `X_2` Median `[Min, Max]` | `CF` Median `[Min, Max]` |
|---|---|---|---|
| `START` (`us`, replay `(c)`) | `55217.00` `[55034.00, 56750.00]` | `53734.50` `[53362.00, 54639.00]` | `55165.50` `[54947.00, 55423.00]` |
| `GAME` (`us`, `((d) - START)/600`) | `707.56` `[705.94, 712.23]` | `710.40` `[705.63, 712.52]` | `709.74` `[707.12, 715.15]` |
| `T2000` (`us`, `((a) - START - 60*GAME)/6070`) | `1236.17` `[1227.67, 1240.16]` | `1230.87` `[1226.80, 1237.92]` | `1290.21` `[1282.64, 1302.72]` |
| `S1` (`us`, `((b,S=1) - START - 60*GAME)/6070`) | `8.83` `[8.61, 8.96]` | `8.91` `[8.64, 9.51]` | `25.84` `[25.49, 25.99]` |
| `NODE` (`ns`, `((a) - (b,S=1))/(26711499 - 23787)`) | `279.164` `[277.234, 280.031]` | `277.842` `[277.042, 279.531]` | `287.598` `[285.820, 290.396]` |
| **`FIXED`** (`us`, `S1 - NODE*(23787/6070)`) | **`7.74` `[7.52, 7.87]`** | **`7.81` `[7.55, 8.43]`** | **`24.71` `[24.37, 24.87]`** |
| **`FIXED` in `%` of `T2000`** | **`0.627%` `[0.607%, 0.637%]`** | **`0.631%` `[0.615%, 0.685%]`** | **`1.903%` `[1.891%, 1.939%]`** |

*(Also from `partF_summary_raw.txt`: `GAME` as `%` of `CPU(a)/60` is `0.559%` `[0.557%, 0.562%]` on `X_1` and `0.561%` `[0.559%, 0.567%]` on `X_2`.)*

- **`S = 250` and `S = 8000` linearity check on `X_1` (`2` runs each after warm-up):**
  - `S = 250` (`6070 / 2557415 / d11ef24cb13f478f`, `45,824` lines, `421.320` nodes/search): measured CPU/search = **`121.04 us`** (`120.92`, `121.17`), line `FIXED + NODE * nodes = 125.36 us` -> difference **`-4.32 us` (`-3.44%` of line, `-3.57%` of measured)**.
  - `S = 8000` (`6070 / 92444625 / f2d3bf44418ba5de`, `90,039` lines, `15229.757` nodes/search): measured CPU/search = **`4246.46 us`** (`4240.77`, `4252.15`), line `FIXED + NODE * nodes = 4259.34 us` -> difference **`-12.88 us` (`-0.30%` of line, `-0.30%` of measured)**.
- **Control `CF` verdict:** **`FIRES (PASSES)`** — `CF` `FIXED` median minus `X_1` `FIXED` median = **`+16.97 us`** (`>= 10 us`; per-round differences `[+17.35, +17.16, +16.90, +16.51, +17.03, +16.53] us`), and `min(CF) = 24.37 us > max(X_1) = 7.87 us` (all `6/6` `CF` runs above all `6/6` `X_1` runs).
- **Part F declared reading:** **`SMALL`** (`FIXED / T2000` is `0.627%` and `0.631%` `< 3%`; `GAME / (CPU(a)/60)` is `0.559%` and `0.561%` `< 1%`).

### Grading Prediction 1 (`prediction1_job31.txt`, standalone commit `94226fb56`)
| Item | Predicted | Observed (`X_1` / `X_2`) | Result |
|---|---|---|---|
| `START` (`us`) | `[10000.0, 50000.0]` | `55217.00` / `53734.50` | **MISS (slightly high)** — `net768.fnn3` stream load + page faults took ~`54-55 ms`. |
| `GAME` (`us`) | `[250.0, 1100.0]` | `707.56` / `710.40` | **HIT** (both builds inside range). |
| `T2000` (`us`) | `[1190.0, 1290.0]` | `1236.17` / `1230.87` | **HIT** (both builds inside range). |
| `S1` (`us`) | `[12.0, 42.0]` | `8.83` / `8.91` | **MISS (lower/faster)** — `X = kH` already carries Piece 17 (`apply_position_sv`, single-pass `stack_` clear, `v3_state_->invalidate()`). |
| `FIXED` (`us`) | `[11.0, 41.0]` | `7.74` / `7.81` | **MISS (lower/faster)** — `7.7-7.8 us` per search (`3.3 us` below `11.0 us`). |
| `FIXED %` of `T2000` | `[0.90, 3.40]%` | `0.627%` / `0.631%` | **MISS (lower/faster)** — fixed per-search CPU is `< 0.65%` of `T2000`. |
| `CF - X_1` `FIXED` (`us`) | `[11.0, 55.0]` (`CF` fires) | `+16.97 us` (`6/6 > 6/6`) | **HIT**. |
| Top function in `profile_S1.txt` | `Worker::search(Board, ...)` | `TranspositionTable::clear()` (`25.12%`, `4,446` samples) | **MISS** — replay `(b)` runs `START` (`55 ms`) + `60` `ucinewgame`s (`42.5 ms`) alongside `6,070` `8.8 us` searches (`53.6 ms`), so `TT::clear()` (`79.8%` of `GAME`) tops raw `profile_S1.txt`. |

---

## 3. Part G: Once-Per-Search and Once-Per-Game Work (`profile_S1.txt`, `syscalls_S1.txt`, `partG_once_per_search_and_game.txt`)

`strace` is not installed on this VM; `sudo -n perf trace -s` worked and was recorded on replays `(b, S=1)`, `(c)`, and `(d)` in `syscalls_S1.txt`. Net of `(c)` and `59` post-setup `ucinewgame`s, each search executes **`6.5636` system calls**: `3.0002` `futex` (`1.0000` UCI wake + `2.0002` worker condvar waits/wake), `2.5634` `write` (flushed `info depth`, `info string softnodes nodes`, `bestmove`), and `1.0000` `read` (UCI command pipe).

### Once-Per-Search Work in Code-Path Order of `go` (`X_1`, `FIXED = 7.74 us` = `0.627%` of `T2000`)
| Step | Code-Path Stage (`uci.cpp` / `search.cpp`) | Syscalls / Search | Est. CPU (`us`) | Share of `FIXED` | Share of `T2000` |
|---|---|---|---|---|---|
| 1 | UCI stdin `read` & incremental `apply_position_sv` (`uci.cpp:517,843`) | `1.0000 read` | `0.37` | `4.8%` | `0.030%` |
| 2 | `go` parse (`parse_limits_sv`, `steady_clock::now`, `v3::problem`) & `pending_task` enqueue (`uci.cpp:846-921`) | `1.0000 futex` | `0.60` | `7.8%` | `0.049%` |
| 3 | UCI $\leftrightarrow$ search-thread condvar hand-off (`work_cv` / `done_cv`, `finish_task_switch`, `_raw_spin_*`, `uci.cpp:423-430,473-477`) | `2.0002 futex` | `3.78` | `48.8%` | `0.306%` |
| 4 | `Searcher::search` & `Worker::search` root set-up (`tt.new_search`, `ExclusiveLease`, `legal_moves`, `stack_[0..init_limit]`, `v3_state_->invalidate`, root eval, `search.cpp:3159-3493,3843-3900`) | `0.0000` | `0.51` | `6.6%` | `0.041%` |
| 5 | UCI `info depth`, `info string softnodes nodes`, and `bestmove` formatting + flushed `write`s (`search.cpp:3260,3791`, `uci.cpp:439-472`) | `2.5634 write` | `2.48` | `32.0%` | `0.201%` |
| **Total** | **All once-per-search non-node work (`FIXED`)** | **`6.5636`** | **`7.74`** | **`100.0%`** | **`0.627%`** |

### Once-Per-Game Work in Code-Path Order of `ucinewgame` + `isready` (`X_1`, `GAME = 707.56 us` = `0.559%` of `CPU(a)/60`)
| Step | Code-Path Stage (`uci.cpp` / `search.cpp`) | Syscalls / Game | Est. CPU (`us`) | Share of `GAME` | Share of `T` Game |
|---|---|---|---|---|---|
| 1 | `stop_search()` idle check (`uci.cpp:597`) | `0.0000` | `0.40` | `0.1%` | `<0.001%` |
| 2 | `TranspositionTable::clear()` across `16 MiB` (`524,288` clusters, `search.cpp:458`) | `0.0000` | `564.90` | `79.8%` | `0.446%` |
| 3 | `Evaluator::clear()` v1 pawn/refresh caches (`search.cpp:1689`) | `0.0000` | `66.09` | `9.3%` | `0.052%` |
| 4 | `Worker::clear()` history/stack ERMS `memset` (`0x1a1efa` `rep stosb` ~`2.3 MiB`, `search.cpp:1690-1709`) | `0.0000` | `67.77` | `9.6%` | `0.053%` |
| 5 | `board.set_fen(StartFen)`, `pos_cache` reset, and `isready` $\to$ `readyok` (`uci.cpp:595-603`) | `1 read + 1 write` | `8.40` | `1.2%` | `0.007%` |
| **Total** | **All once-per-`ucinewgame` work (`GAME`)** | **`2.0000`** | **`707.56`** | **`100.0%`** | **`0.559%`** |

---

## 4. Part H: Fallback to `T`'s Profile, Pieces `19` and `20`, Known Answers, and `CN4` (`partH_known_answers_raw.txt`)

Because Part F read `SMALL` and the largest Part G item is `0.306%` of `T2000` (`< 1%`), Part H took up to two node-keeping pieces from `T`'s profile (`profile_T_X1.txt`):

1. **Piece `19` (`19_fast_has_legal_move.patch.txt`):**
   - **Function & share:** `Board::has_legal_move() const` (`include/forge/board.hpp`, `src/board.cpp`), **`3.11%` self time in `T`** (`3,695 / 118,079` samples, rank `#5` in `profile_T_X1.txt`), **`0.0%` of `FIXED`** (`0` samples in top 50 of `profile_S1.txt`; pure per-node draw/terminal work).
   - **Change & why nothing can change:** Hoists the `checkers_ == 0` ray-free pawn and knight checks inline into `Board::has_legal_move()` and adds `pinned == 0 && ep_square_ < 0` / double-check king-evasion fast exits in `has_legal_move_slow()`; `has_legal_move()` is a pure `const` predicate that mutates no `Board` or `KingLines` state, every early `true` exhibits a strictly legal move off all king rays, and every early `false` runs only after exhausting every piece/king candidate when no pin or en-passant move can exist.
2. **Piece `20` (`20_v3_fast_refresh_and_pair.patch.txt`):**
   - **Functions & share:** `nnue::v3::apply_one_refresh_one_and_evaluate` (`6.52%`, rank `#3`), `nnue::v3::apply_changes_pair` (`2.17%`, rank `#8`), `nnue::v3::refresh_from_pieces` (`1.05%`, rank `#17`), and `nnue::v3::replay_ply_from` (inlined in `Worker::static_evaluate_v3`, `9.02%`, rank `#2`) — **`9.74%` direct self share in `T`**, **`0.0%` of `FIXED`** (per-evaluation accumulator work).
   - **Change & why nothing can change:** Adds a non-king fast path in `replay_ply_from`, direct inline AVX-512 `2`- and `3`-change kernels in `apply_changes_pair`, `prev_bb ^ curr_bb == 0` piece skips + hoisted per-piece `w1` base pointers in `refresh_from_pieces` and `apply_one_refresh_one_and_evaluate`, and hoisted `inc_shape` (`2`, `3`, `4`) outside the `h` loop in `apply_one_refresh_one_and_evaluate`; every `int16` column subtraction and addition is performed in the exact same order on the exact same feature indices, leaving every accumulator, cache entry, evaluation, output line, and subsequent search bit-for-bit identical.

### Known Answers on `p19_1`, `p20_1`, `kJ_1`, `kJ_2` and Control `CN4` (`partH_known_answers_raw.txt`)
| Build | Job 26 (`7` checks) | Job 20 (`60g`) | `T` (`60g`) | `n1` (`T[1..3]` masked) | `n2` (`V3_VERIFY=1` `T[1..10]`) | `n3` (`S=1` replay `(b)`) | `n4` (`T[1..10]+g1`) |
|---|---|---|---|---|---|---|---|
| `p19_1` | `PASS` (`312866/862329/4865609`; `278024/587276`; `625258/3652372`; `882074/4275906`) | `7670/25641316/ee465caeff9c0fcf` | `6070/26711499/937e1660561173af` | `4847` lines, `0` diffs | `1089/4497849/b8af7c43c78aca2c`, `0` `FAILED` | `6070/23787/f331c1bb14017ed4` (`15720` lines) | `2599 == 2599`, `0` diffs |
| `p20_1` | `PASS` (all `7` exact) | `7670/25641316/ee465caeff9c0fcf` | `6070/26711499/937e1660561173af` | `4847` lines, `0` diffs | `1089/4497849/b8af7c43c78aca2c`, `0` `FAILED` | `6070/23787/f331c1bb14017ed4` (`15720` lines) | `2599 == 2599`, `0` diffs |
| `kJ_1` | `PASS` (all `7` exact) | `7670/25641316/ee465caeff9c0fcf` | `6070/26711499/937e1660561173af` | `4847` lines, `0` diffs | `1089/4497849/b8af7c43c78aca2c`, `0` `FAILED` | `6070/23787/f331c1bb14017ed4` (`15720` lines) | `2599 == 2599`, `0` diffs |
| `kJ_2` | `PASS` (all `7` exact) | `7670/25641316/ee465caeff9c0fcf` | `6070/26711499/937e1660561173af` | `4847` lines, `0` diffs | `1089/4497849/b8af7c43c78aca2c`, `0` `FAILED` | `6070/23787/f331c1bb14017ed4` (`15720` lines) | `2599 == 2599`, `0` diffs |
| **`CN4`** | (`X` without `shared_.tt.clear()` in `Searcher::clear()`) | — | — | — | — | — | **`FAILS n4 (FIRES)`**: `len1=2599`, `len2=2289`, **`diffs=2594`** (line 1: `nodes 55 ... hashfull 0` vs `nodes 48 ... hashfull 23`) |

---

## 5. Part I: `C31`, `J1`, `J2`, `JS`, Bundle Reading, and Prediction 2 (`ctrl_C31_raw.txt`, `row_J1_raw.txt`, `row_JS_raw.txt`)

### Control `C31` and Row `J1` (`B / A`; `> 1` means `A` uses less time than `B`)
| Row | `A` vs `B` | Blocks | Metric | Block Ratios (`B / A`) | Pooled | Median | Mean & 95% $t$-CI | `> 1` | Reading |
|---|---|---|---|---|---|---|---|---|---|
| **`C31`** | `X_1` (`sn2000`) vs `X_1` (`sn2200`, `5853/28387596/f37b0151ac18bd56`) | `4` (`0` dropped) | Engine CPU | `1.0700 1.0734 1.0783 1.0764` | **`1.0745`** (`64.8356 / 60.3388`) | `1.0749` | `1.0745 [1.0687, 1.0803]` | **`4/4`** | **`PASS`** (`> 1.0116`, `4/4`) |
| `C31` | (wall) | `4` | Wall | `1.0712 1.0783 1.0834 1.0778` | `1.0777` (`67.1805 / 62.3398`) | `1.0780` | `1.0776 [1.0697, 1.0856]` | `4/4` | — |
| **`J1`** | `kJ_1` vs `X_1` on `T` (`6070/26711499/937e1660561173af`) | `12` (`0` dropped) | Engine CPU | `1.0037 1.0006 1.0027 1.0048 1.0051 1.0050 1.0027 1.0044 1.0058 1.0032 1.0094 1.0053` | **`1.0044`** (`180.3402 / 179.5498`) | **`1.0046`** | `1.0044 [1.0030, 1.0058]` | **`12/12`** | **`NOT SEEN`** (`< 1.0116`) |
| `J1` | (wall) | `12` | Wall | `1.0064 1.0010 1.0016 1.0053 1.0040 1.0053 1.0026 1.0037 1.0055 1.0019 1.0080 1.0033` | `1.0041` (`186.2408 / 185.4886`) | `1.0039` | `1.0041 [1.0027, 1.0054]` | `12/12` | — |
| **`J2`** | `kJ_2` vs `X_2` on `T` | **NOT DONE** | — | Stopped before starting due to Minute-80 stop rule (`JS` ended at `09:01:32 PM UTC`, `79m 33s` after `07:42:59 PM UTC` claim; `12` blocks need ~`7m 48s`). | — | — | — | — | **NOT DONE (Minute 80)** |

### Row `JS` (`6` runs each of `kJ_1` and `kJ_2` beside Part F's `X_1` and `X_2`, `U = 60`; for the record, no verdict)
| Build | `FIXED` (`us`, Median `[Min, Max]`) | `GAME` (`us`, Median `[Min, Max]`) | `T2000` (`us`, Median `[Min, Max]`) | `S1` (`us`, Median `[Min, Max]`) | `NODE` (`ns`, Median `[Min, Max]`) | `FIXED %` of `T2000` |
|---|---|---|---|---|---|---|
| `X_1` (Part F) | `7.74` `[7.52, 7.87]` | `707.56` `[705.94, 712.23]` | `1236.17` `[1227.67, 1240.16]` | `8.83` `[8.61, 8.96]` | `279.164` `[277.234, 280.031]` | `0.627%` `[0.607%, 0.637%]` |
| `X_2` (Part F) | `7.81` `[7.55, 8.43]` | `710.40` `[705.63, 712.52]` | `1230.87` `[1226.80, 1237.92]` | `8.91` `[8.64, 9.51]` | `277.842` `[277.042, 279.531]` | `0.631%` `[0.615%, 0.685%]` |
| **`kJ_1` (`JS`)** | **`8.14` `[7.51, 9.89]`** | **`673.25` `[660.31, 686.19]`** | `1217.66` `[1215.05, 1226.32]` | `9.22` `[8.58, 10.97]` | `274.829` `[273.863, 276.952]` | `0.669%` `[0.616%, 0.814%]` |
| **`kJ_2` (`JS`)** | **`7.86` `[7.63, 8.67]`** | **`675.55` `[668.05, 687.69]`** | `1214.34` `[1213.47, 1219.45]` | `8.94` `[8.71, 9.74]` | `274.154` `[273.791, 275.379]` | `0.648%` `[0.626%, 0.714%]` |

- **Bundle `kJ` reading:** **`NOT SEEN` (and `J2` incomplete at Minute 80)** — `J1` completed all `12` blocks cleanly (`0` dropped) with `12/12` blocks `> 1` and `95% t-CI [1.0030, 1.0058]`, proving a small consistent speedup (`+0.44%`), below Job 30's `1.0116` `PAYS` bar (`both rows >= 1.0116` required for `PAYS`).

### Grading Prediction 2 (`prediction2_job31.txt`, standalone commit `9bc1529dd`)
| Item | Predicted | Observed | Result |
|---|---|---|---|
| `J1` pooled CPU (`X_1 / kJ_1`) | `[1.0150, 1.0360]` | `1.0044` (`12/12 > 1`) | **MISS (overpredicted gain)** — `+0.44%` (`< 1.50%`). |
| `J2` pooled CPU (`X_2 / kJ_2`) | `[1.0140, 1.0360]` | Not run (stopped at Minute 80) | **NOT GRADED (not run)** (`JS` single-process `T2000` ratio `X_2 / kJ_2 = 1230.87 / 1214.34 = 1.0136`, though `X_2` and `kJ_2` were timed in separate windows). |
| Bundle `kJ` reading | `PAYS` | `NOT SEEN` on `J1` (`J2` not run at Minute 80) | **MISS**. |
| `kJ` `FIXED` minus `X` `FIXED` (`us`) | `[-0.60, +0.60] us` | `+0.225 us` (`8.00 - 7.775` midpoint of build medians; `kJ_1 - X_1 = +0.40 us`, `kJ_2 - X_2 = +0.05 us`) | **HIT** (all inside `[-0.60, +0.60] us`). |

---

## WHAT THIS CANNOT SEE

The PC's Windows pipes and its Python driver (a hand-off there costs other amounts), its clang 23 and Zen 5
processor, its trained nets, 16 engines side by side, more than one search thread, and games longer or shorter
than T's. FIXED is the engine's own CPU: time the engine spends waiting for a command is not in it.

---

## Facts, Suspicions, What I Did Not Do, What I Am Not Sure About

### Facts
1. On `X = kH` (`kF + 14 + 15 + 16 + 17 + 18`), non-node per-search engine CPU on `T` is **`7.74 us` (`0.627%` of `T2000`) on `X_1`** and **`7.81 us` (`0.631%` of `T2000`) on `X_2`**, while per-`ucinewgame` CPU is **`707.56 us` (`0.559%` of a `T` game) on `X_1`** and **`710.40 us` (`0.561%`) on `X_2`**.
2. Control `CF` (`+1 MiB` `memset` at the top of `Searcher::search`) raised `FIXED` by **`+16.97 us`** (`24.71 us` vs `7.74 us`, `6/6` above `6/6`), proving the replay instrument resolves fixed per-search costs cleanly.
3. Node-keeping holds down to `go softnodes 1`: `D` (`r15d`), `kF_sp_1`, `X_1`, `X_2`, `p19_1`, `p20_1`, `kJ_1`, and `kJ_2` all produce `6070 / 23787 / f331c1bb14017ed4` (`15,720` lines) on `KF1`/`n3`.
4. Removing `shared_.tt.clear()` from `Searcher::clear()` (`CN4`) immediately breaks `n4` on line `1` of the replayed game `1` (`hashfull 23`, `nodes 48` vs `hashfull 0`, `nodes 55`; `2,594` line differences), whereas `X_1`, `p19_1`, `p20_1`, `kJ_1`, and `kJ_2` have `0` differences across all `2,599` lines.
5. In `J1` (`12` ABBA/BAAB blocks), `kJ_1` beat `X_1` in `12/12` blocks (`pooled = 1.0044`, `95% t-CI [1.0030, 1.0058]`), which is statistically non-zero on this VM yet below the `1.0116` `PAYS` bar (`NOT SEEN`).

### Suspicions
1. Why `19 + 20` gave only `+0.44%` on `J1`: in `kH`, Clang 18 ThinLTO + SP-PGO was already partially inlining/devirtualizing hot paths of `apply_changes_pair` and `Board::has_legal_move`, and in `apply_one_refresh_one_and_evaluate` (`6.52%`) most of the self time sits in the `L2/L3`-resident `w1` column vector loads (`subs`/`adds`) rather than the `12`-piece bitboard header or `inc_cnt` branches.
2. Why `S = 250` (`121.04 us`) lies `3.44%` below the `S = 1` $\leftrightarrow$ `S = 2000` chord (`125.36 us`): shallow searches (`~421` nodes) experience higher `TT` and `RefreshCache` L1/L2 locality and fewer king-bucket refreshes per node than `S = 2000` (`~4,401` nodes/search).

### What I Did Not Do
1. **Row `J2` (`12` blocks of `kJ_2` vs `X_2` on `T`):** Not started because `JS` completed at `09:01:32 PM UTC` (`minute 79m 33s` after the `07:42:59 PM UTC` claim), and `FABLE_TO_carbon2_31.md` mandates stopping benchmark work at Minute 80 and listing any undone part as not done rather than running past Minute 80.
2. **Individual timing rows for `p19_1` and `p20_1`:** Not asked for by `FABLE_TO_carbon2_31.md` (Part I tests the bundle `kJ` directly).

### What I Am Not Sure About
1. In `L`, `1` of the `U = 60` `ucinewgame` commands occurs before the first `position` line (inside `(c) = START`), and `59` occur after. Both `partF_summary_raw.txt` and `row_JS_raw.txt` apply the literal specification formula `(CPU - START - U * GAME) / 6070` with `U = 60`; using `U - 1 = 59` instead adds `GAME / 6070 ≈ +0.117 us` to `T2000`, `S1`, and `FIXED` (`7.86 us` vs `7.74 us` on `X_1`, `0.636%` vs `0.627%`), changing no reading or control verdict.
2. Whether `kJ_2` vs `X_2` (`J2`) would also sit around `~1.004–1.008` (`NOT SEEN`) in paired ABBA blocks (`JS` showed `NODE = 274.154 ns` on `kJ_2` vs `274.829 ns` on `kJ_1`).

---

## Model Name, Timestamps, and Final Repository Check

- **Model:** `Gemini 4 Carbon`
- **First line of `stamps.txt`:** `Thu Nov 19 07:42:59 PM UTC 2026 | job 31 received (FABLE_TO_carbon2_31.md); claim committed`
- **Last line of `stamps.txt`:** `Thu Nov 19 09:02:59 PM UTC 2026 — Minute 80 stop reached; writing REPORT_carbon2_job31.md`

### Verbatim Output of `git status --short && ls -R forge-combo29/carbon2/job31` Before Report Commit
```text
 M forge-combo29/carbon2/job31/row_JS_raw.txt
 M forge-combo29/carbon2/job31/stamps.txt
?? forge-combo29/carbon2/job31/REPORT_carbon2_job31.md
forge-combo29/carbon2/job31:
19_fast_has_legal_move.patch.txt
20_v3_fast_refresh_and_pair.patch.txt
builds.txt
CF_planted_1mb_memset.patch.txt
CN4_no_ucinewgame_tt_clear.patch.txt
ctrl_C31_raw.txt
L_head.txt
partF_KF0_KF1_CFcheck_raw.txt
partF_runs_raw.txt
partF_summary_raw.txt
partG_once_per_search_and_game.txt
partH_known_answers_raw.txt
prediction1_job31.txt
prediction2_job31.txt
profile_S1.txt
profile_T_X1.txt
REPORT_carbon2_job31.md
row_J1_raw.txt
row_JS_raw.txt
stamps.txt
step0_raw.txt
syscalls_S1.txt
```

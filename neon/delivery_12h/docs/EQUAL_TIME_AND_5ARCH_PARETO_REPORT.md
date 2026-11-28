# Equal-Time Confirmation & 5-Architecture Hardware NPS Pareto Report (Stream A — Wave 7)

**Audience:** Three-Model Debate (Astra, Opus, Neon)  
**Scope:** Complete clean GPU+CPU-idle hardware speed verification (`CLEAN_IDLE_SPEED_2BUILDS.json`, `CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json`), Server-Day architecture diagnostic suite (`SERVERDAY_ARCH_SUITE_SUMMARY.json`), equal-time and fixed-node match verdicts (`G3_FULL25_PGO_vs_live_r0067_2000g_6p006`, `250k` & `50k` suites), the `concurrency=10` on 8-core caveat, and why `FORGENN3-P` (V3P) waits for Server Day `1.4B–2.0B` quiet-filtered positions rather than live-loop placement today.  
**Integrity Notice:** All numerical values below are quoted directly from verified JSON artifacts under `C:\nnue-lab\neon\forge_fixes\`. Loss, MSE, and Syzygy offline metrics in `SERVERDAY_ARCH_SUITE_SUMMARY.json` are strictly diagnostic and are never claimed as Elo.

---

## 1. Executive Summary

- **Equal-Time Confirmation (`G3_FULL25_PGO_vs_live_r0067_2000g_6p006`):** **`-0.35` Elo** (`95% CI [-8.35, +7.66]`, `elo_err=8.00`, `480–482–1038` W–L–D / `480-1038-482` W-D-L, `score_pct=49.95%`, `ptnml=[10, 239, 502, 241, 8]`, `z=-0.085`, `los_pct=46.61%`, `0` time losses, `0` illegal moves, `3994.4s` at `6+0.06`, `concurrency=10`). **Verdict: DEAD LEVEL** at equal time.
- **Why `-0.35` happened (`CLEAN_IDLE_SPEED_2BUILDS.json`):** On clean GPU+CPU-idle hardware, `FORGENN3-P` `1024w kb8` PGO (`v3_fused_PGO_A/B`) runs at **`3,020,708`–`3,041,832` NPS** (`0.8337x`–`0.8395x` vs `live_pgo_r0067` `3,623,176` NPS = **`-16.05%` to `-16.63%`** speed cost, vs the earlier loaded `0.9221x` reading). That `~16%` NPS gap (`~0.25` doublings, `~12–18` Elo at `50–70` Elo/doubling) offsets `G3_FULL25`'s per-node edge (`+22.03` vs `r0067` at `250k`, `+10.9 +/- 12.5` pooled, `-0.58` vs `r0202` at `250k`).
- **Key Server-Day 5-Arch Pareto Finding (`CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json`):**
  - **`1024p/kb16` (`2,940,975` / `2.941M` NPS, `0.8139x`)** costs only **`-0.61%` (`-0.6%`)** NPS vs `1024p/kb8` (`2,959,061` / `2.959M`, `0.8189x`), directly attacking opposite-side castling with near-zero speed penalty.
  - By contrast, **`1536p/kb8` (`2,664,542` / `2.665M` NPS, `0.7374x`)** pays **`-26.26%` (`-26.3%`)** NPS vs `live_pgo_r0067` (`3,613,642`) and **`-9.95%` (`-10.0%`)** NPS vs `1024p/kb8`.
- **Placement Decision:** **DO NOT place V3P (`FORGE_FINAL_G3_PGO.exe` + `G3_FULL25` `1024w` `keep_noisy=true`) into the live loop today.** Also do NOT replace `forge.exe` for `768w` nets (`v3p_pgo_r0067_768screlu` runs at `3,450,211` NPS = **`0.9548x`** vs live `3,613,642` NPS). V3P (`1024p/kb16` primary, `1536p/kb8` optional arm) waits for Server Day `1.4B–2.0B` quiet-filtered positions (`--skip-fqs-noisy`), while the 5-surface placement package (`teamwork_wave6\`) stays frozen and ready.

---

## 2. Clean Idle 2-Build Speed Proof (`CLEAN_IDLE_SPEED_2BUILDS.json`)

Measured strictly sequentially with GPU+CPU idle (`timestamp = "2026-11-28 00:02:21"`, `depth=15`, `rounds=5`). Every V3P build (`A` and `B` replicates across `v1_unfused`, `v3_fused`, and `v3_fused_PGO`) searched the exact same **`v3p_bit_exact_nodes = 869964`**, confirming bit-exact determinism:

| Build / Config | `nodes` | `median_ms` | `median_nps` | `ratio_vs_live_pgo_r0067` | `ratio_vs_v1_unfused` | `exe_sha256` (prefix) |
|---|---:|---:|---:|---:|---:|---|
| `live_pgo_r0067` (`768w` SCReLU) | `1,373,184` | `379` | **`3,623,176.0`** | `1.0` | `1.3202` | `cef2f21589102392...` |
| `v1_unfused_A` (`G3_FULL25` `1024w kb8`) | `869,964` | `317` | `2,744,365.0` | `0.7574` | `1.0` | `154bf2e777661444...` |
| `v1_unfused_B` (`G3_FULL25` `1024w kb8`) | `869,964` | `317` | `2,744,365.0` | `0.7574` | `1.0` | `c5a93f4d8c0d6633...` |
| `v3_fused_A` (`G3_FULL25` `1024w kb8`) | `869,964` | `310` | `2,806,335.0` | `0.7746` | `1.0226` | `7261cb8cc90c09bf...` |
| `v3_fused_B` (`G3_FULL25` `1024w kb8`) | `869,964` | `306` | `2,843,019.0` | `0.7847` | `1.0359` | `2a87dce476997585...` |
| **`v3_fused_PGO_A`** (`G3_FULL25` `1024w kb8`) | `869,964` | `288` | **`3,020,708.0`** | **`0.8337`** | `1.1007` | `f0576cd735ef7500...` |
| **`v3_fused_PGO_B`** (`G3_FULL25` `1024w kb8`) | `869,964` | `286` | **`3,041,832.0`** | **`0.8395`** | `1.1084` | `c128e2081b599305...` |

### Why Earlier `0.9221x` Misled & Why `869,964` vs `1,373,184` Is Not Strength
1. **Loaded vs. clean idle artifact:** Earlier in the quest (`SERVER_DAY_ARCH_SCALING_BRIEF.md` / `NEON_TO_OPUS.md:607`), `G2 1024w` on non-PGO `v3_fused` benchmarked at `2,405,811` vs `2,609,025` NPS = `0.9221x` (`-7.79%`) while GPU training and CPU matches were running concurrently. Contention suppressed the faster `768w` SCReLU build more heavily (`3.623M -> 2.609M`, `-28.0%`) than `1024w` (`2.843M -> 2.406M`, `-15.4%`), creating an optimistic `0.9221x` ratio. Under clean idle conditions, PGO `v3_fused` reaches `3.021M–3.042M` vs `3.623M` = **`0.8337x–0.8395x`** (`-16.05%` to `-16.63%`, `~12–18` Elo speed tax).
2. **Depth-15 node count (`869,964` vs `1,373,184`) is NOT a strength measure:** As noted in `OPUS_TO_NEON.md:2986`, different NNUE nets alter search tree shape and pruning rates, so searching fewer nodes to fixed `depth 15` does not measure Elo. Only head-to-head games decide.

---

## 3. Clean Idle 5-Architecture PGO NPS Pareto (`CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json`)

Measured strictly sequentially after the clock match (`timestamp = "2026-11-28 01:09:12"`, `depth=15`, `rounds=5`):

| Profile (`summary` key) | `nodes` | `median_nps` | `ratio_vs_live_pgo_r0067` | Delta vs `live_pgo_r0067` | Delta vs `1024p_kb8_G3` | Implied Speed Tax (`70*log2`, heuristic) |
|---|---:|---:|---:|---:|---:|---:|
| `live_pgo_r0067_768screlu` | `1,373,184` | **`3,613,642.0`** | `1.0` | `0.00%` | `+22.12%` | `+0.0` Elo |
| `v3p_pgo_r0067_768screlu` | `1,373,184` | **`3,450,211.0`** | **`0.9548`** | **`-4.52%`** | `+16.60%` | `-4.7` Elo |
| `v3p_pgo_768p_kb8` | `1,782,594` | `3,047,169.0` | `0.8432` | `-15.68%` | `+2.98%` | `-17.2` Elo |
| `v3p_pgo_1024p_kb8_G3` | `869,964` | **`2,959,061.0`** | `0.8189` | `-18.11%` | `0.00%` | `-20.2` Elo |
| **`v3p_pgo_1024p_kb16`** | `1,529,307` | **`2,940,975.0`** | **`0.8139`** | `-18.61%` | **`-0.61%` (`-0.6%`)** | `-20.8` Elo |
| **`v3p_pgo_1536p_kb8`** | `1,409,543` | **`2,664,542.0`** | **`0.7374`** | **`-26.26%` (`-26.3%`)** | **`-9.95%` (`-10.0%`)** | `-30.7` Elo |

### Pareto Analysis for Server Day `1.4B–2.0B`
1. **`1024p/kb16` is the clear Server-Day hardware Pareto sweet spot:** Doubling king buckets from `kb=8` to `kb=16` (`2,940,975` vs `2,959,061` NPS) costs only **`-0.61%`** (`2940975.0 / 2959061.0 = 0.993888`, `-0.6%` rounded) in NPS — essentially zero speed penalty — because L3 cache (`25.58 MB` net) still fits comfortably in Ryzen 9950X `64 MiB` L3 and only the king-bucket lookup index changes. It directly targets opposite-side castling with zero C++ changes.
2. **`1536p/kb8` pays a steep `-26.26%` (`-26.3%`) NPS wall:** At `2,664,542` NPS (`0.7374x` vs `live_pgo_r0067`, `-9.95%` vs `1024p/kb8`), `1536p/kb8` starts `~31` Elo behind `live_pgo_r0067` (and `~10.5` Elo behind `1024p/kb8`) on speed alone before playing a single move. On Server Day (`+€9` marginal H100 cost), `1536p/kb8` is worthwhile as an optional arm only if `1.4B–2.0B` quiet positions deliver enough fixed-node gain to clear its `-26.3%` speed barrier.
3. **`v3p_pgo_r0067_768screlu` (`0.9548x`) blocks exe-only replacement:** Running legacy `r0067` (`768w` SCReLU) on `FORGE_FINAL_G3_PGO.exe` yields `3,450,211` vs `3,613,642` NPS (`-4.52%`, likely because PGO was profiled on V3P Pairwise+PSQT paths). Therefore, `FORGE_FINAL_G3_PGO.exe` must **never** replace the live loop `forge.exe` for `768w` SCReLU nets (`OPUS_TO_NEON.md:3014`).

---

## 4. Server-Day Architecture Smoke Suite (`SERVERDAY_ARCH_SUITE_SUMMARY.json`)

All 3 Server-Day architecture variants trained on the 2M CC0 smoke setup passed `--quick` Master Gates (`master_gate_hard_pass = true`) and `0 cp` engine-vs-Python parity. *(Strictly diagnostic — never claimed as Elo.)*

| Arm | `hidden` | `king_buckets` | `net_bytes` | `train_seconds` | `final_train_loss` | `r0203_quiet_mix60` | `m4_wdl_mse` | `m4_corr` | `syz_draw_med_cp` | `syz_win_ok_pct` | `master_gate_hard_pass` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| `G5a_cc0_768p_kb8` | `768` | `8` | `9,647,848` | `31.8` | `0.001126` | `0.03504` | `0.02889` | `0.5163` | `38.0` | `99.4` | `true` |
| `G5b_cc0_1536p_kb8` | `1536` | `8` | `19,098,856` | `63.5` | `0.000559` | `0.033779` | `0.02915` | `0.5102` | `34.1` | `99.35` | `true` |
| `G5c_cc0_1024p_kb16` | `1024` | `16` | `25,577,704` | `53.5` | `0.000657` | `0.034658` | `0.02935` | `0.5064` | `54.3` | `99.3` | `true` |

---

## 5. Equal-Time & Fixed-Node Match Ledger (`G3_FULL25`, `r0202`, `r0067`)

All matches below recorded **`0` time losses, `0` disconnects, and `0` illegal moves** (`UHO_Lichess_4852_v1.epd`, `Threads=1`, `Hash=16`, identical 45 Big Tune UCI options on both engines):

| Match (`summary.json`) | TC / Nodes | `concurrency` | `games` (`W–L–D`) | `score_pct` | `elo` (`elo_err`) | `95% CI` | `ptnml` | `los_pct` | `seconds` |
|---|---|---:|---|---:|---|---|---|---:|---:|
| **`G3_FULL25_PGO_vs_live_r0067_2000g_6p006`** | **`6+0.06`** | `10` | `2000` (`480–482–1038`) | `49.95%` | **`-0.35`** (`8.00`) | `[-8.35, +7.66]` | `[10, 239, 502, 241, 8]` | `46.61%` | `3994.4` |
| `G3_FULL25_vs_r0067_600g_250k` | `250k` nodes | `8` | `600` (`165–127–308`) | `53.17%` | **`+22.03`** (`16.17`) | `[+5.88, +38.28]` | `[4, 60, 142, 82, 12]` | `99.63%` | `1064.8` |
| `G3_FULL25_vs_r0067_1000g_50k` | `50k` nodes | `6` | `1000` (`270–256–474`) | `50.7%` | **`+4.86`** (`13.35`) | `[-8.49, +18.23]` | `[18, 115, 218, 133, 16]` | `76.26%` | `481.9` |
| `G3_FULL25_vs_r0202_1000g_50k` | `50k` nodes | `6` | `1000` (`298–234–468`) | `53.2%` | **`+22.27`** (`13.64`) | `[+8.64, +35.96]` | `[16, 98, 217, 144, 25]` | `99.93%` | `485.2` |
| `G3_FULL25_vs_r0202_600g_250k` | `250k` nodes | `8` | `600` (`152–153–295`) | `49.92%` | **`-0.58`** (`15.70`) | `[-16.30, +15.14]` | `[4, 81, 130, 82, 3]` | `47.12%` | `999.1` |
| `OPUS_r0202_vs_r0067_1000g_250k` | `250k` nodes | `8` | `1000` (`230–244–526`) | `49.3%` | **`-4.86`** (`11.75`) | `[-16.64, +6.90]` | `[8, 126, 244, 116, 6]` | `20.85%` | `1657.9` |

### Opus's `250k` Heterogeneity & Pooled Estimate (`OPUS_TO_NEON.md:2957–2960`)
- Combining the three `250k` matches (`G3 vs r0067` `+22.03`, `G3 vs r0202` `-0.58`, `r0202 vs r0067` `-4.86`) via weighted least squares gives **`G3 - r0067 ~ +10.9 +/- 12.5`** (95%) and `r0202 - r0067 ~ +1.0 +/- 10.4`.
- **Heterogeneity caveat:** The three `250k` matches yield **`chi-square = 4.5`** on 1 degree of freedom (`p ~ 0.03`), indicating they fit a single transitive ranking poorly; hence `+22.03` is likely an overestimate, and the pooled `+10.9 +/- 12.5` per-node edge closely matches the observed equal-time landing at **`-0.35 [-8.35, +7.66]`** once the `-16%` clean NPS cost (`~12–18` Elo) is subtracted.

---

## 6. Critical Operational Caveats & Why V3P Waits for Server Day

1. **`concurrency=10` on 8 Physical Cores / 16 Threads (`G3_FULL25_PGO_vs_live_r0067_2000g_6p006`):**
   - `summary.json` (`declaration.concurrency = 10`) ran 10 simultaneous 1-thread engine processes on an 8-core / 16-thread CPU, forcing two engines to share a physical core on two pairs.
   - Opus hypothesized (`OPUS_TO_NEON.md:2973, 3013`) that core-sharing may penalize the wider `1024w` net slightly more, **but explicitly noted this stays a footnote** because it cannot turn `-0.35 [-8.35, +7.66]` into a placement case. All future equal-time clock matches (`OPUS_R1`, `run_clock_tm_screen.py`, owner bundle test) require **`concurrency <= 7`**.
2. **`FORGE_FINAL_G3_PGO.exe` Search Identity (`OPUS_TO_NEON.md:3028–3032`):**
   - Verified by Opus (`gates_exe.py`): `FORGE_FINAL_G3_PGO.exe` (`sha256=f8dcc4a2f42aead08d1174118b0f2d9d8f0d246ddfe96f068b32e74d5fbe3082`) gave `perft 5 = 4865609`, built-in `bench 11/13 = 312866 / 862329`, and `r0067+B4 bench 11/13 = 187930 / 632195` — identical to the live engine. Thus `G3_FULL25_PGO_vs_live_r0067_2000g_6p006` tested **only** the `G3_FULL25` net + V3P kernel speed, NOT the pending search-fix bundle (which requires its own declared 2-arm test at `concurrency <= 7`).
3. **Why V3P Waits for Server Day `1.4B–2.0B` Quiet-Filtered Positions:**
   - `G3_FULL25` was trained on `353M` rows with **`keep_noisy = true`** (`skip_fqs_noisy = false`, `OLS Q = 293.3`, `Q/P = 6.21`), whereas `FORGENN3-P` loses `+651.27` to `+699.72` Elo under `keep_noisy=true` on 2M CC0 rows.
   - At equal time on today's `353M` `keep_noisy=true` data, `G3_FULL25` scored `-0.35 [-8.35, +7.66]` vs `live r0067` (and `v3p_pgo_r0067` ran `0.9548x`).
   - **Decision:** Keep the 5-surface V3P loop placement package (`teamwork_wave6\`) frozen and verified, do NOT place V3P into the live loop today, and deploy V3P (`1024p/kb16` primary, `1536p/kb8` optional arm) on Server Day with **`1.4B–2.0B` quiet-filtered (`--skip-fqs-noisy`) positions**.

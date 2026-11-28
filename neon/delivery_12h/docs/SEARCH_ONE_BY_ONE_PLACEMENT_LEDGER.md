# Forge Search One-by-One Placement Ledger (Wave 11)

**Sources:** `CLEAN_IDLE_PER_PATCH_NPS.json`, `OWNER_BUNDLE_DECLARATION.json`, `OWNER_BUNDLE_RESULTS.json`, `OWNER_BUNDLE_ARMA_PGN_FORENSICS.json`, `OWNER_BUNDLE_ARMB_PGN_FORENSICS.json`, `ALL_MATCHES_SCOREBOARD.md`, `run_lmr_deeper_clock_sprt.py`, `matches/SP_SF13_alone_SPRT_0_10_250k/declaration_20261128_080634.json`.  
**Policy:** Screens (`600g @ 50k`) and independent confirmations (`1,000g @ 50k`, `250k` SPRT, `6+0.06` clock) are **never pooled**. Clean idle per-patch NPS (`depth 15`, `5x` interleaved, `r0067` + `45` live `v3_uci_options`, identical Clang 23.1.5 ThinLTO+PGO) isolates every patch's speed cost before any placement.

---

## 1. Single-Patch Search Placement Table

| Candidate | Patch / Option | Clean Idle `d15` Nodes | `med ms` | Clean Idle `d15` NPS (Ratio vs Live PGO) | `600g @ 50k` Screen | `1,000g @ 50k` Confirm (Unpooled) | Clock / `250k` Gate Status | Placement Decision |
|---|---|---:|---:|---:|---:|---:|---|---|
| **`live_pgo_r0067`** *(baseline)* | `v3-r15dsg-sp-clang/forge.exe` (`cef2f215...`) | `1,373,184` | `381` | **`3,604,157`** (`1.0000x`, `0.00%`) | — | — | Live baseline (`r0067` + `45` opts) | **LIVE BASELINE** |
| **`V3Pv3_alone_r0067_pgo`** | `V3P_pairwise_psqt_fused_v3.patch` (`6d5443e8...`) | **`1,373,184`** *(bit-exact)* | `384` | **`3,576,000`** (`0.9922x`, **`-0.78%`**) | — | — | Cold-PGO hypothesis confirmed (`FORGE_FINAL_G3_PGO.exe` was `0.9548x` on `r0067` due to V3P-only PGO). `G3_FULL25` (`keep_noisy=true`) scored `-0.35 [-8.35, +7.66]` at `2,000g @ 6+0.06` (`-16%` clean NPS). | **WAIT FOR SERVER DAY `2.0B` QUIET** (`V3P` 5-surface package frozen & verified) |
| **`LmrDeeperShallower=true`** | Zero C++ diff (`live_pgo` `cef2f215...`, UCI toggle) | `1,331,742` | **`381`** *(same wall ms!)* | **`3,495,385`** (`0.9698x`, `-3.02%`) | — | **`+8.34`** `[-4.06, +20.76]` (`255-514-231`, `LOS 90.6%`) | **`CLK_LmrDeeperShallower_SPRT_0_10_6p006`** queued (`6+0.06`, `conc=7`, `SPRT [0, 10]`, cap `4,000g`, `seed=202611971`) | **QUEUED 1ST FOR CLOCK SPRT** (eligible for 1-line `config.forge.toml:214` placement only on `H1`) |
| **`SF13_alone_pgo`** | `SF13_qs_evasion_pruning.patch` (`796ef50e...`) | `1,393,274` | `397` | **`3,509,506`** (`0.9737x`, **`-2.63%`**) | **`+20.87`** `[+4.86, +36.97]` (`169-298-133`, `LOS 99.5%`) | **`+8.34`** `[-4.39, +21.10]` (`256-512-232`, `LOS 90.0%`) | **`SP_SF13_alone_SPRT_0_10_250k`** **RUNNING** (`250k`, `conc=6`, `SPRT [0, 10]`, cap `3,000g`, `seed=202611981`) -> then `6+0.06` SPRT if `H1` | **TESTING ALONE (`250k` SPRT)** |
| **`W2_proto_1_alone_pgo`** | `proto_1_corrhist_minor.patch` (`56882b9b...`) | `1,412,411` | `403` | **`3,504,741`** (`0.9724x`, **`-2.76%`**) | **`+11.01`** `[-4.82, +26.88]` (`155-309-136`, `LOS 91.3%`) | **`+7.64`** `[-4.34, +19.65]` (`260-502-238`, `LOS 89.4%`) | Queued individually after `SF13` (`250k` `SPRT [0, 10]` -> `6+0.06` `SPRT [0, 10]`) | **QUEUED ALONE AFTER `SF13`** |
| **`SF8_alone_pgo`** | `SF8_conthist_6ply.patch` (`28e803a8...`) | `1,200,340` | `366` | **`3,279,617`** (`0.9100x`, **`-9.00%`**) | **`+17.97`** `[+2.21, +33.80]` (`163-305-132`, `LOS 98.7%`) | **`+4.86`** `[-7.77, +17.51]` (`251-512-237`, `LOS 77.5%`) | Primary NPS culprit (`6-ply` conthist cache misses); `-9.00%` NPS exceeds uncertain `+4.86` `50k` gain | **HELD OUT PER OPUS** (until speed-optimized `< 3%` or wins alone at `250k` AND `6+0.06`) |

---

## 2. Rejected, Negative, & Inconclusive Items (DO NOT PLACE)

| Item / Match | Games & TC | W–D–L | Elo `[95% CI]` | z / LOS | Key Forensics / Reason for Rejection |
|---|---|---|---|---|---|
| **`OWNER_BUNDLE` Arm A** (`FORGE_OWNER_BUNDLE_PGO` `95d0608e...` + `G3_FULL25` vs `live_pgo + r0067`) | `2,000g @ 6+0.06` (`conc=7`, `seed=202611901`) | `449–1059–492` | **`-7.47`** `[-15.49, +0.54]` | `-1.83 / 3.4%` | `0.8214x` clean `d13` NPS (`2,833,364` vs `3,449,556`). PGN forensics (`avg_plies=153.9`): `short_le80 -3`, **`mid_81_140 -51` (`98-424-149`) vs `G3` alone `-13` (`135-394-148`)** (`-38` of `-41` net-game drop in middlegames!), `long_gt140 +11`. **DO NOT PLACE.** |
| **`OWNER_BUNDLE` Arm B** (`FORGE_OWNER_BUNDLE_PGO` + `r0067` vs `live_pgo + r0067`) | `2,000g @ 6+0.06` (`conc=7`, `seed=202611902`) | `439–1144–417` | **`+3.82`** `[-3.94, +11.59]` | `+0.96 / 83.3%` | `0.9340x` clean `d13` NPS (`3,221,841`), `0.9293x` `d15` NPS (`3,349,276`, `-7.07%`). PGN forensics (`avg_plies=159.7`): `short_le80 0`, `mid_81_140 +2` (`87-442-85`), `long_gt140 +20` (`350-526-330`). **INCONCLUSIVE — DO NOT PLACE AS BUNDLE** (pursue 1-by-1). |
| **`SF4b1` alone** (`SF4b1_alone_vs_base_1000g_50k`) | `1,000g @ 50k` | `234–519–247` | **`-4.52`** `[-17.04, +7.99]` | `-0.71 / 23.9%` | Failed `1,000g` confirm (`600g` screen was `+15.06`); also **`-5.21`** (`V3P+SF6b+SF8+SF4b1`) and **`-15.99 [-29.09, -2.95]`** (`SF4b1+SF8`, `236-482-282`). **REJECTED.** |
| **`SF15` confirm** (`SF15_confirm_vs_base_1000g_50k`) | `1,000g @ 50k` | `238–523–239` | **`-0.35`** `[-12.75, +12.06]` | `-0.06 / 47.8%` | Flat in fresh-seed `1,000g` confirm (`600g` screen was `+7.53`). **REJECTED.** |
| **`UCI_EvasionOrdering`** (`UCI_EvasionOrdering_600g_50k`) | `600g @ 50k` | `135–303–162` | **`-15.65`** `[-30.99, -0.36]` | `-2.01 / 2.2%` | Statistically significant loss at `50k`. **REJECTED.** |
| **`COMBO_v2`** (`SF8 + SF13 + LmrDeeper`) | `1,000g @ 50k` | `243–505–252` | **`-3.13`** `[-15.94, +9.68]` | `-0.48 / 31.6%` | Negative interaction when blind-stacked; confirms 1-by-1 placement discipline. |
| **Other Rejected `50k` Screens** | `600g @ 50k` | — | `-4.05` to `-101.21` | `0.0%–31.4%` | `SF5a` (`-101.21`), `SF4b2` (`-19.71`), `SF7` (`-13.90`), `W2_proto_4` (`-7.53`), `W2_proto_3` (`-6.37`), `SF3` (`-6.37`), `UCI_AspFailHighReduce1` (`-4.05`), `SF2` (`-4.05`), `SF12` (`-4.05`), `COMBO_v1` (`-0.35`), `SF16` (`0.00`), `W2_proto_2` (`0.00`). |

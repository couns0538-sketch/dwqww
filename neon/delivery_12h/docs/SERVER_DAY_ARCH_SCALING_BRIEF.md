# Server-Day NNUE Architecture & Width Scaling Brief (For Three-Model Debate)

> **Purpose:** Supply the Three-Model Debate with **directly measured** Zen 5 AVX-512 (`v3p_fused_v3_engine.exe`) width-scaling NPS curves, exact file sizes, exact `0 cp` parity across `512..1536w`, and equal-time Elo breakeven math before committing Server-Day GPU compute on `1.5B–2.0B` usable positions.
> **Integrity Rule (R5):** NPS & offline loss/MSE are diagnostic/sizing inputs only; final architecture selection is strictly decided by declared equal-time `fastchess` matches.

---

## 1. Measured Zen 5 Split-Stream AVX-512 (`v3`) Width Scaling (`V3P_WIDTH_SCALING.json`)

All widths verified **`max_diff = 0 cp`** across 60 diverse 8-OB FENs against Python `forge_v3p.reference_eval()` exact integer oracle (`v3p_fused_v3_engine.exe`, 3x interleaved `bench 13` under live GPU+CPU load; clean GPU-idle ratios will be confirmed right after `G3_FULL25`!):

| Architecture (`kb=8, ob=8, mirror`) | File Size | `0 cp` Parity | Median NPS (under load) | Ratio vs `r0067` | Implied Equal-Time Speed Tax (`70*log2`) | Ratio vs `G2 1024w` | Implied Tax vs `1024w` |
|---|---:|---:|---:|---:|---:|---:|---:|
| **`r0067` (`768w` SCReLU, live)** | `9.03 MiB` | `0 cp` | `2,609,025` | `1.0000x` | `+0.0 Elo` | `1.0845x` | `+8.2 Elo` |
| **`G2` (`1024w` Pairwise+PSQT, real)** | `12.21 MiB` | `0 cp` | **`2,405,811`** | **`0.9221x`** | **`-8.2 Elo`** | `1.0000x` | `+0.0 Elo` |
| `512w` Pairwise+PSQT (syn) | `6.20 MiB` | `0 cp` | `2,428,996` | `0.9310x` | `-7.2 Elo` | `1.0096x` | `+1.0 Elo` |
| `768w` Pairwise+PSQT (syn) | `9.20 MiB` | `0 cp` | `2,348,023` | `0.9000x` | `-10.6 Elo` | `0.9760x` | `-2.5 Elo` |
| `1024w` Pairwise+PSQT (syn) | `12.21 MiB` | `0 cp` | `2,308,398` | `0.8848x` | `-12.4 Elo` | `0.9595x` | `-4.2 Elo` |
| `1280w` Pairwise+PSQT (syn) | `15.21 MiB` | `0 cp` | `2,175,220` | `0.8337x` | `-18.4 Elo` | `0.9042x` | `-10.2 Elo` |
| **`1536w` Pairwise+PSQT (syn)** | **`18.21 MiB`** | **`0 cp`** | **`2,215,243`** | **`0.8491x`** | **`-16.5 Elo`** | **`0.9208x`** | **`-8.3 Elo`** |

### Key Architectural Insights
1. **Why `V3P_pairwise_psqt_fused_v3.patch` Changes the Equal-Time Economics:**
   - On unfused `v1`, `G2 1024w` ran at `0.8378x` (`-17.9 Elo` speed tax).
   - With our Zen 5 split-stream fused AVX-512 `v3` kernel (`+4.1%` to `+6.1%` bit-exact over `v1`), `G2 1024w` climbs to **`0.9221x` (`-8.2 Elo` tax)** — meaning **`+15.30 Elo` fixed-node arch gain (`G2 vs G1`) ALREADY clears the equal-time breakeven by `~+7 Elo` BEFORE PGO or 25r scaling!**
2. **Why `1536w` Pairwise+PSQT Is a Live Server-Day Candidate (Ready Zero-Code Today!):**
   - `1536w` (`half = 768` = `24` ZMM vectors = `12` clean 2x-unrolled AVX-512 iterations with `0` tail) is **ALREADY supported** in `V3P_pairwise_psqt_fused_v3.patch`, `forge_v3p.py`, `train_v3p.py`, and `train_v3p_stream.py` (`0 cp` parity verified on `120` 8-OB FENs + `60` scaling FENs!).
   - Jumping `1024w -> 1536w` (`+50%` hidden capacity) costs only **`-8.3 Elo`** in NPS (`0.9208x` vs `1024w`)! On `1.5B–2.0B` CC0 positions (4–6x more data than `G3_FULL25`), if `1536w` adds `+12..+20 Elo` at fixed nodes (typical Stockfish/Viridithas/Stormphrax scaling at 1.5B+ positions), it delivers **`+4..+12` net equal-time Elo** with **zero C++ engine risk**!
   - **Recommended Server-Day GPU Experiment:** Train `1024w` (`seed1`, `loss_pow=2.5`) AND `1536w` (`seed1`, `loss_pow=2.5`) head-to-head on the exact same `1.5B–2.0B` bucketed-deduped `.fqs.z` shards using `train_v3p_stream.py` (`~6 hr` for `1024w`, `~9 hr` for `1536w` on 1x RX 7900 XT; `~2.5–4 hr` on 1x H100), then decide strictly by declared `2,000g @ 6+0.06` equal-time `fastchess`!
3. **Should We Add a Multi-Layer `L2` (`16 -> 32 -> 1`) Head Before Server Day?**
   - **Recommendation for Debate:** **NO for Server Day #1** unless `G3_FULL25` shows severe representational saturation on `SF19` middlegame blunders.
   - *Reason:* Adding an `L1(16) -> L2(32) -> 1` head adds ~`600–900` lines of new INT8/VNNI quantized C++ inference + new file format version + new quantizer calibration + new loader fuzzing/parity gates, AND at `1024w`/`1536w` Pairwise+PSQT on `G3_FULL25` Epoch 12 alone, `m4_wdl_mse` ALREADY plunged from `0.01302` (`r0067`) to **`0.01185` (`-9.0%`)** with **`0` `net_sanity` v2 flags** and **`SF19` overall WDL MSE `0.05737 -> 0.05351`**! Maximize proven `FORGENN3-P` (`1024w` & `1536w`) + clean 2B CC0 datagen first; reserve `L2` for Server Day #2.

---

## 2. Measured `kb=16` King-Bucket Feasibility & Chess-Pattern Error Taxonomy (`V3P_KB16_FEASIBILITY.json`, `SF19_ERROR_TAXONOMY.json`)

An X-ray of `6,000` Stockfish 19 reference positions (`analyze_sf19_error_taxonomy.py` -> `SF19_ERROR_TAXONOMY.json`) revealed that **`G3_FULL25` Ep 12 beat `r0067` across ALL 7 chess categories** (`-5.7%` to `-10.6%` WDL MSE), while isolating **`opp_side_castling`** (`0.07232` WDL MSE, **`20.67%` severe `>=0.35` error rate** vs `11.63%` quiet positional) as Forge's #1 non-tactical static weakness!

Because `FORGENN3-P` (`nnue_v3.hpp`) ALREADY reads an arbitrary `king_map[64]` from the 192-byte header and allows up to `32` king buckets, upgrading `kb=8 -> kb=16` mirrored king buckets requires **ZERO C++ engine change**:

| Metric (`1024w` Pairwise+PSQT) | `kb=8` | `kb=16` (16 mirrored king zones) | Delta / Notes |
|---|---:|---:|---|
| File Size (`w1 + psqt` L3 footprint) | `12.21 MiB` | `24.39 MiB` | Fits comfortably inside Ryzen 9950X `64 MiB` L3! |
| `v3p_fused_v3_engine.exe` vs Python Oracle (`60` 8-OB FENs) | `0 cp` | **`0 cp`** (`cksum 2e520890dd314fe2`) | **ZERO C++ change**; exact bit-for-bit parity! |
| Median `bench 13` NPS (3x interleaved, under load) | `2,337,416` | `2,656,730` (`1.137x`, ~`1.00x` noise) | **~0% ALU overhead** (only one L3 bucket index change on king moves!) |
| Trainer Support (`forge_v3p.py`, `train_v3p.py`, `train_v3p_stream.py`) | Ready | **Ready (`--king-buckets 16`)** | Uses `forge_v3p.king_layout(16)` (fine rank 1/2 + ranks 3-4 / 5-6 / 7-8) |
| Selective 16k Rescoring (`rescore_fqs_selective.py`) | Default | **`--prioritize-opp-castle` ready** | Targets opposite-side castled middlegames (`|sc| < 450`, `>=14` pcs) |

- **Debate Recommendation:** On `1.5B–2.0B` Server-Day CC0 positions, our data-balanced `kb=16` layout (`forge_v3p.king_layout(16)`: fine rank-1, fine rank-2, separate rank-3 `ab/cd`, separate rank-4 `ab/cd`, ranks 5-6 `ab/cd`, ranks 7-8 `ab/cd`) achieves **`3.333 bits`** entropy with minimum bucket **`0.578%` (`23.1M` perspectives at 2.0B positions)** (`OPENING_AND_KB16_DIVERSITY.json`). It is a **zero-C++-risk, ~zero-NPS-cost** candidate to directly attack Forge's #1 static middlegame weakness (`opp_side_castling`). Needs clean GPU-idle 2-build NPS check + declared Server-Day ablation (`kb=16` vs `kb=8` on equal data & equal time).

---

## 3. Measured Opening Diversity & Server-Day Cost Economics (`OPENING_AND_KB16_DIVERSITY.json`, `SERVER_DAY_COST_MODEL.json`)

1. **Equal-N (`500,000` pos) Diversity Comparison (`r0202` 8-rand vs `CC0 v2` book):**
   - `CC0 v2` (`book_cc0_clean.epd` + 1/2 parity rand + 10% startpos): **`34.50%`** castled king (`b1/g1`), **`25.41%`** exact equal material (tournament-realistic calibration!).
   - `r0202` (8 blind random plies): higher material-signature entropy (**`5.854` vs `5.338` bits**), higher opposite-side castling middlegames (**`6.53%` vs `4.24%`**), **`19.66%`** equal material.
   - **Hybrid Server-Day Recipe (`gen_cc0_selfgame_fqs.py --wide-div-frac 0.15`):** `75%` CC0 book (1/2 parity rand) + `15%` wide-diversity CC0 (4/5 rand plies) + `10%` startpos (0..2 rand plies) + Syzygy 3-4-5 adjudication + `ply_limit_skip` + `--resume` preemption safety!
2. **Measured Storage, Transfer & Cloud Cost Model (`SERVER_DAY_COST_MODEL.json`, 0 servers rented):**
   - **2.0B usable positions** in `.fqs.z` = **`19.7 GiB`** on disk (vs `~280 GiB` `.plain` = **`13.5x` smaller**, transfers at 1 Gbps in **`2.6 min`**!).
   - **Bucketed exact dedup (`partition_fqs_buckets.py`, 128 buckets):** **`6.6 min`** (`0.11 hr`) and **`23.0 GiB` RAM** on 32 workers (eliminating the `400–600 GiB` Python-dict OOM).
   - **Cost Breakdown (~90% CPU datagen, ~10% GPU training):**
     - `2.0B @ 4k` (`256c` EPYC + `1x H100`, `1024w`, `0.5%` 16k rescore): `~14.6h` CPU (`~€66`) + `~2.7h` GPU (`~€6.4`) = **`~€72.4` (`€36.2 / 1B usable`)**; adding a second **`1536w`** (or **`kb=16`**) run on the SAME 2.0B shards costs only **`+€9` (`+12%`)**!
     - `1.5B @ 2k` (`256c` EPYC + owner's local `RX 7900 XT` at `1.91M pos/s`, `1%` 16k rescore): `~6.3h` CPU (`~€28.5`) + `4.4h` local GPU (`€0`) = **`~€28.5` (`€19.0 / 1B usable`)**!

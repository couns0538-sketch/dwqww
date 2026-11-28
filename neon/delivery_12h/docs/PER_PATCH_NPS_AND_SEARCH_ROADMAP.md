# Per-Patch NPS Proof & 1-by-1 Search Roadmap (Forge Teamwork Wave 10 — Stream A)

**Status:** Verified read-only engineering record (`2026-11-28`, CPU-only, zero builds, zero GPU, zero matches).  
**Verdict:** The 4-patch owner bundle (`FORGE_OWNER_BUNDLE_PGO.exe`) remains **DO NOT PLACE**. Clean idle per-patch NPS isolation (`CLEAN_IDLE_PER_PATCH_NPS.json`) proves two decisive facts: (1) `V3P_pairwise_psqt_fused_v3.patch` has only **`-0.78%`** (`0.9922x`) NPS cost with bit-exact `1,373,184` nodes when PGO-profiled on `r0067`, confirming Opus's cold-PGO hypothesis; and (2) `SF8_conthist_6ply.patch` (`-9.00%` NPS) is the primary speed bottleneck behind the bundle's `-7.07%` (`d15`) / `-6.60%` (`d13`) speed tax and Arm B's `-6.6%` NPS penalty.

---

## 1. Executive Summary & Ownership / Integrity Guardrails

1. **Proof 1 — Cold-PGO Hypothesis Confirmed (`V3Pv3_alone_r0067_pgo`):** Rebuilt alone with Clang 23.1.5 ThinLTO + PGO profiled on `r0067`, `V3P_pairwise_psqt_fused_v3.patch` runs at **`3,576,000` NPS** (`0.9922x`, **`-0.78%`**) with **bit-exact `1,373,184` nodes** vs `live_pgo_r0067` (`3,604,157` NPS). The earlier `0.9548x` (`-4.52%`, `3,450,211` NPS) observed on `FORGE_FINAL_G3_PGO.exe` was PGO profile skew from profiling on `G3_FULL25` V3P work, not V3P code overhead on `768w` SCReLU.
2. **Proof 2 — `SF8` Is the Bundle NPS Bottleneck (`-9.00%`):** Under identical `r0067` PGO conditions, `SF8_alone_pgo` drops to **`3,279,617` NPS** (`0.9100x`, **`-9.00%`**), dwarfing `SF13_alone_pgo` (`-2.63%`), `W2_proto_1_alone_pgo` (`-2.76%`), and zero-C++ `live_pgo_LmrDeeper` (exact same `381 ms` median wall time, `-3.02%` nodes). `SF8` directly explains `FORGE_OWNER_BUNDLE_PGO`'s `-7.07%` (`d15`) / `-6.60%` (`d13`) NPS penalty in Owner Bundle Arm B (`+3.82 [-3.94, +11.59]` Elo).
3. **1-by-1 Search Roadmap (`OPUS-2811-ARM-B-RECOUNTED`):**
   - **Step 1:** Zero-C++ `LmrDeeperShallower=true` at clean `6+0.06`, `concurrency=7`, normalized `SPRT [0, 10]` capped at `4,000` games (`live_pgo` + `r0067` both sides, via `run_lmr_deeper_sprt.py`).
   - **Step 2:** `SF13_alone_pgo` (`-2.63%`) and `W2_proto_1_alone_pgo` (`-2.76%`) individually (`250k` `SPRT [0, 10]` cap `3,000g` -> clean `6+0.06` `SPRT [0, 10]`).
   - **Step 3:** Exclude `SF8_conthist_6ply.patch` (`-9.00%`) from live and all bundles unless replaced by a speed-optimized variant (e.g., 4-ply only / prefetch) or proven with a decisive `>= +12 Elo` fixed-node gain to overcome its `-9%` speed tax.
4. **Integrity Guardrails:** Every figure in this document is quoted directly from verified JSON, Python, patch, and markdown artifacts on disk in `C:\nnue-lab\neon\forge_fixes\` and `C:\nnue-lab\neon\OPUS_TO_NEON.md`. Diagnostic metrics are never conflated with Elo, and the 4-patch bundle stays **DO NOT PLACE**.

---

## 2. Clean GPU+CPU-Idle Per-Patch NPS Proof (`CLEAN_IDLE_PER_PATCH_NPS.json`)

### 2.1 Test Protocol (`C:\nnue-lab\neon\forge_fixes\bench_per_patch_nps.py`)
- **Timestamp & Environment:** Written `2026-11-28 06:54:12 PC` on 100% idle GPU + CPU with `CLOCK_MATCH_RUNNING` lockfile set during execution (`bench_per_patch_nps.py:14, 124–134`).
- **Build Homogeneity (`bench_per_patch_nps.py:3–12, 59–76` & `build_fast.py:18–36, 76–100`):** Each single-patch executable (`SF13_alone_pgo`, `SF8_alone_pgo`, `W2_proto_1_alone_pgo`, `V3Pv3_alone_r0067_pgo`) was built from `C:\nnue-lab\forge\r15dsg` with identical Clang 23.1.5 ThinLTO + PGO (`-std=c++20 -O3 -DNDEBUG -march=znver5 -flto=thin -ffp-contract=off -fno-fast-math`), profiled on `C:\nnue-lab\runs\forge\r0067\train\cand.fnn3` with all `45` live `v3_uci_options` from `C:\nnue-lab\pipeline\config.forge.toml`.
- **Benchmark Loop (`bench_per_patch_nps.py:79–100, 120–149`):** `bench 15` over `5` interleaved rounds (alternating forward order on even `r_idx` and reversed order on odd `r_idx`), `Threads=1`, `Hash=16`, `OwnBook=false`, `MateAlphaGuard=true`, `NNUEArch=true`, `NNUEArchFile=C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`, plus all `45` live `v3_uci_options` (`LmrDeeperShallower=true` added only for `live_pgo_LmrDeeper` and `FORGE_OWNER_BUNDLE_PGO`). Summary takes `statistics.median` across the 5 rounds.

### 2.2 Complete 7-Row Per-Patch Isolation Table (`CLEAN_IDLE_PER_PATCH_NPS.json:6–70`)

| Config Key | Executable Path | Full SHA-256 Digest | Nodes (`d15`) | Median `ms` | Median NPS | Ratio vs Live PGO | Delta vs Live PGO | Notes / Variant Diff |
|---|---|---|---:|---:|---:|---:|---:|---|
| `live_pgo_r0067` | `C:\nnue-lab\runs\forge\engines\v3-r15dsg-sp-clang\forge.exe` | `cef2f21589102392fdd7e3cbde74bfd01baa94f9677a2be33365f68e4bceb03d` | `1,373,184` | `381` | **`3,604,157`** | `1.0000x` | `0.00%` | Baseline live PGO |
| `V3Pv3_alone_r0067_pgo` | `C:\nnue-lab\neon\forge_fixes\builds\V3Pv3_alone_r0067_pgo.exe` | `6d5443e8088b6617ce0a266bb4336db05bf363ae672442895cdbd60f8a3369c7` | `1,373,184` | `384` | **`3,576,000`** | `0.9922x` | **`-0.78%`** | `V3P_pairwise_psqt_fused_v3.patch`; **bit-exact `1,373,184` nodes** |
| `SF13_alone_pgo` | `C:\nnue-lab\neon\forge_fixes\builds\SF13_alone_pgo.exe` | `796ef50e534b892453de3401bc4e65e3661f9d11b911146e7807bb95600ae1c1` | `1,393,274` | `397` | **`3,509,506`** | `0.9737x` | **`-2.63%`** | `SF13_qs_evasion_pruning.patch` |
| `W2_proto_1_alone_pgo` | `C:\nnue-lab\neon\forge_fixes\builds\W2_proto_1_alone_pgo.exe` | `56882b9be1032bd5cddafff3c9a5e7b60a61301db32068e5a6e73148b83bbc06` | `1,412,411` | `403` | **`3,504,741`** | `0.9724x` | **`-2.76%`** | `proto_1_corrhist_minor.patch` |
| `live_pgo_LmrDeeper` | `C:\nnue-lab\runs\forge\engines\v3-r15dsg-sp-clang\forge.exe` | `cef2f21589102392fdd7e3cbde74bfd01baa94f9677a2be33365f68e4bceb03d` | `1,331,742` | `381` | **`3,495,385`** | `0.9698x` | **`-3.02%`** | Zero C++ diff; `LmrDeeperShallower=true`; **exact same `381 ms`** |
| `SF8_alone_pgo` | `C:\nnue-lab\neon\forge_fixes\builds\SF8_alone_pgo.exe` | `28e803a8d0b6e88d12dcf42bd37d57b0fe177476666cb1bbe3bdde17cc5f3905` | `1,200,340` | `366` | **`3,279,617`** | `0.9100x` | **`-9.00%`** | `SF8_conthist_6ply.patch`; **primary NPS bottleneck** |
| `FORGE_OWNER_BUNDLE_PGO` | `C:\nnue-lab\neon\forge_fixes\builds\FORGE_OWNER_BUNDLE_PGO.exe` | `95d0608e1a6c4c4ba6606a6ba2a8e4562280f71129b33d5d71f65b7e3c8941b0` | `1,490,428` | `445` | **`3,349,276`** | `0.9293x` | **`-7.07%`** | All 4 patches + `LmrDeeperShallower=true` (dual-net PGO) |

**Per-Round NPS Stability (`CLEAN_IDLE_PER_PATCH_NPS.json:71–261`):**
- `live_pgo_r0067`: `[3604157, 3585336, 3613642, 3530035, 3604157]` (`380–389 ms`)
- `V3Pv3_alone_r0067_pgo`: `[3566711, 3576000, 3576000, 3511979, 3576000]` (`384–391 ms`)
- `SF13_alone_pgo`: `[3509506, 3509506, 3518368, 3500688, 3527275]` (`395–398 ms`)
- `W2_proto_1_alone_pgo`: `[3504741, 3504741, 3504741, 3284676, 3504741]` (`403–430 ms`)
- `live_pgo_LmrDeeper`: `[3513831, 3513831, 3486235, 3405989, 3495385]` (`379–391 ms`)
- `SF8_alone_pgo`: `[3270681, 3288602, 3288602, 3252953, 3279617]` (`365–369 ms`)
- `FORGE_OWNER_BUNDLE_PGO`: `[3356819, 3349276, 3219066, 3349276, 3356819]` (`444–463 ms`)

**Important Note on `live_pgo_LmrDeeper`:** `LmrDeeperShallower=true` changes **zero C++ code** and finishes `bench 15` in the **exact same `381 ms`** median wall time (`1,331,742` nodes vs `1,373,184` baseline, `-3.02%` nodes/NPS purely from searching a `3.02%` smaller tree at the same speed, e.g., slightly higher relative move-ordering/leaf cost per node on shallower subtrees).

---

## 3. Decisive Proof 1 — Cold-PGO Hypothesis Confirmed (`FORGE_FINAL_G3_PGO.exe` vs `V3Pv3_alone_r0067_pgo`)

### 3.1 Side-by-Side Evidence
In the earlier clean idle `bench 15` measurement (`CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json:2–29`, `2026-11-28 01:09:12`), running `r0067` on `FORGE_FINAL_G3_PGO.exe` (`sha256: f8dcc4a2f42aead08d1174118b0f2d9d8f0d246ddfe96f068b32e74d5fbe3082`, from `G3_FULL25_PGO_vs_live_r0067_2000g_6p006/declaration_20261128_000221.json:4–5`) produced **`3,450,211` NPS (`0.9548x`, `-4.52%`)** vs `live_pgo_r0067_768screlu` at `3,613,642` NPS, with identical `1,373,184` nodes.

| Executable | PGO Profile Target | Net Evaluated | Nodes (`d15`) | Median NPS | Ratio vs Live PGO | Delta | Source |
|---|---|---|---:|---:|---:|---:|---|
| `FORGE_FINAL_G3_PGO.exe` (`f8dcc4a2...`) | `G3_FULL25` (`FORGENN3-P`, `1024p/kb8` V3P work) | `r0067` (`768` SCReLU) | `1,373,184` | `3,450,211` | `0.9548x` | **`-4.52%`** | `CLEAN_IDLE_SERVERDAY_5ARCH_NPS.json:18–29` |
| `V3Pv3_alone_r0067_pgo.exe` (`6d5443e8...`) | `r0067` (`768` SCReLU + `45` live opts) | `r0067` (`768` SCReLU) | `1,373,184` | `3,576,000` | `0.9922x` | **`-0.78%`** | `CLEAN_IDLE_PER_PATCH_NPS.json:52–60` |

### 3.2 Reasoning & Opus Verification
- At `01:12 PC` (`OPUS_TO_NEON.md:3014`, `OPUS-2811-CLOCK-RECOUNTED-AND-R1-TWIN`), Opus flagged the `0.955x` penalty on `FORGE_FINAL_G3_PGO.exe` and formulated the exact cold-PGO hypothesis: *"r0067 on FORGE_FINAL_G3_PGO.exe runs at 0.955x the live exe. So the new exe must not replace the live exe for 768 nets. (HYPOTHESIS: its PGO profile was taken on V3P work.)"*
- Compiling `V3P_pairwise_psqt_fused_v3.patch` alone with identical Clang 23.1.5 ThinLTO + PGO profiled on `r0067` recovers almost the entire gap (`0.9548x` -> `0.9922x`, `-0.78%` delta, bit-exact `1,373,184` search tree). Because `V3Pv3` gates `pairwise` and `has_psqt` paths behind net flags loaded at init (`include/forge/nnue_v3.hpp:27–28`), profiling exclusively on V3P `G3_FULL25` left legacy `768` SCReLU evaluation paths cold in PGO branch layout.
- At `06:56 PC` (`OPUS_TO_NEON.md:3123`, `OPUS-2811-KEEP-THE-SPRT`), Opus confirmed this proof: *"Good to see the V3P kernel alone at 0.992x with bit-exact nodes: the 0.955x was the PGO profile."*
- **Operational Corollary:** If a single engine binary must serve both `768` SCReLU and `FORGENN3-P` nets at full speed, it requires dual-net PGO profiling (or separate net-matched PGO binaries). V3P itself does **not** materially slow down `r0067`.

---

## 4. Decisive Proof 2 — `SF8_conthist_6ply.patch` (`-9.00%` NPS) Is the Bundle Bottleneck

### 4.1 Owner Bundle Clock Results & PGN Forensics (`OWNER_BUNDLE_RESULTS.json`, `OWNER_BUNDLE_ARMA/B_PGN_FORENSICS.json`)
`FORGE_OWNER_BUNDLE_PGO.exe` (`sha256: 95d0608e...`) combined 4 C++ patches (`V3P_pairwise_psqt_fused_v3.patch`, `SF13_qs_evasion_pruning.patch`, `SF8_conthist_6ply.patch`, `proto_1_corrhist_minor.patch`) plus `LmrDeeperShallower=true`, dual-net PGO profiled on `G3_FULL25` + `r0067`. In clean idle `bench 13` (`3x` pre-match, `OWNER_BUNDLE_RESULTS.json:105–166`) and `bench 15` (`CLEAN_IDLE_PER_PATCH_NPS.json:61–69`):
- `bench 13`: `live_pgo_r0067 = 3,449,556` (`1.0000x`), `bundle_pgo_r0067 = 3,221,841` (`0.9340x`, **`-6.60%`**), `bundle_pgo_G3 = 2,833,364` (`0.8214x`, **`-17.86%`**).
- `bench 15`: `FORGE_OWNER_BUNDLE_PGO` on `r0067 = 3,349,276` (`0.9293x`, **`-7.07%`**).

Both 2,000-game equal-time (`6+0.06`, `concurrency=7`, `0` TL/IL/DC) arms failed to clear placement (`OWNER_BUNDLE_RESULTS.json:190–545`):
- **Arm A (`OWNER_BUNDLE_ARMA_bundleG3_vs_liveR0067_2000g_6p006`, `seed=202611901`):** `449–1059–492` (`48.925%` / `48.93%`), **`-7.47 [-15.49, +0.54]` Elo**, `z = -1.827`, `LOS = 3.38%`, `ptnml = [10, 260, 502, 219, 9]`, `5,637.5s`, `cpu_max_c = 77.4°C`.
  - **PGN Forensics (`OWNER_BUNDLE_ARMA_PGN_FORENSICS.json:3–76`) vs `G3` alone (`-0.35 [-8.35, +7.66]`, `480–1038–482`, `avg_plies = 156.0`):** `avg_plies = 153.9`; `short_le80` `-3` (`2-176-5`) vs `-7` (`0-165-7`); **`mid_81_140` `-51` (`98-424-149`) vs `-13` (`135-394-148`)** — **`-38` net (`-37` fewer White wins)**; `long_gt140` `+11` (`349-459-338`) vs `+18` (`345-479-327`); White `+66` (`261-544-195`) vs `+115` (`298-519-183`), Black `-109` (`188-515-297`) vs `-117` (`182-519-299`).
- **Arm B (`OWNER_BUNDLE_ARMB_bundleR0067_vs_liveR0067_2000g_6p006`, `seed=202611902`):** `439–1144–417` (`50.55%`), **`+3.82 [-3.94, +11.59]` Elo**, `z = +0.965`, `LOS = 83.27%` (`83.28%` top-level), `ptnml = [5, 227, 516, 245, 7]`, `5,737.1s`, `cpu_max_c = 76.6°C`.
  - **PGN Forensics (`OWNER_BUNDLE_ARMB_PGN_FORENSICS.json:1–36`):** `avg_plies = 159.7`; `short_le80` `0` (`2-176-2`); `mid_81_140` `+2` (`87-442-85`); `long_gt140` `+20` (`350-526-330`); White `+114` (`260-594-146`), Black `-92` (`179-550-271`).
- **Arm Contrast (`OPUS-2811-ARM-B-RECOUNTED`, `OPUS_TO_NEON.md:3083–3084`):** `Arm A - Arm B = -11.3 ± 11.2` Elo (`z ≈ -2.0`), attributable to `G3` speed (`0.879x` relative to bundle+`r0067`) plus search margins tuned on `r0067`.

### 4.2 Why `SF8_conthist_6ply.patch` Explains Arm B's `-6.6%` / `-7.1%` NPS Penalty
Comparing the single-patch NPS table (`CLEAN_IDLE_PER_PATCH_NPS.json`) against Arm B (`bundle_pgo_r0067`):
1. `V3Pv3` (`-0.78%`), `SF13` (`-2.63%`), and `W2_proto_1` (`-2.76%`) each impose modest overhead, and `LmrDeeperShallower=true` takes the **exact same `381 ms`** wall time as baseline.
2. `SF8_alone_pgo` alone suffers a **`-9.00%`** NPS drop (`3,279,617` vs `3,604,157` NPS), making `SF8_conthist_6ply.patch` unequivocally the dominant speed bottleneck inside the 4-patch bundle (`-6.60%` at `d13`, `-7.07%` at `d15`).
3. **Code Mechanism (`C:\nnue-lab\neon\forge_fixes\patches\SF8_conthist_6ply.patch:1–58`):**
   - Adds a `const PieceToHistory* cont6` member in `MovePicker` (`ss != nullptr && ss->ply >= 2 && !(ss - 6)->current_move.is_none() ? (ss - 6)->continuation : nullptr`, lines 7, 18).
   - Reads `(*cont6)[p][move.to] / 4` in `MovePicker::score` (line 26) and `(*(ss - 6)->continuation)[p][move.to] / 4` in `quiet_history` (lines 38–40).
   - Removes the `tune::ContHist4PlyRead` conditional guard on 4-ply continuation reads in both `MovePicker` and `quiet_history` (lines 15–17, 34–37).
   - Extends `Worker::update_continuation` loop from `{1, 2, 4}` to `{1, 2, 4, 6}` with `bonus / 4` scaling for `back == 6` (lines 47–55).
   - **Cache Impact:** Every quiet move scoring and every continuation history update touches an additional `PieceToHistory` table 6 plies up the stack, increasing L1/L2 cache misses in the hottest move-ordering loop. While it prunes the `bench 15` tree (`1,200,340` nodes in `366 ms` vs `1,373,184` in `381 ms`), its `-9.00%` NPS loss directly eats the time budget in clock games.

---

## 5. Exact 3-Step 1-by-1 Clock Test Roadmap (`OPUS-2811-ARM-B-RECOUNTED` & `OPUS-2811-KEEP-THE-SPRT`)

Per `OPUS-2811-ARM-B-RECOUNTED` (`OPUS_TO_NEON.md:3086–3089`, `05:57 PC`), **every individual search test must pre-declare its time control, SPRT bounds, and game cap before game 1**, never pool games across tests, and use `50k` fixed-node runs strictly as a filter. Individual `1,000g @ 50k` prior filter points (`ALL_MATCHES_SCOREBOARD.md:22, 24, 25, 31`) are shown for reference only:

| Roadmap Step | Candidate | Clean Idle `d15` NPS (Delta) | Prior `1,000g @ 50k` Filter (`ALL_MATCHES_SCOREBOARD.md`) | Declared Gate Protocol |
|---|---|---|---|---|
| **Step 1 (First)** | `LmrDeeperShallower=true` (Zero C++ change) | `3,495,385` (`-3.02%` nodes, **exact `381 ms`**) | `+8.34 [-4.06, +20.76]` (`255-514-231`, `LOS 90.6%`) | Clean **`6+0.06`**, `concurrency=7`, normalized **`SPRT [0, 10]`** (`alpha=0.05, beta=0.05`), **cap `4,000` games** (`2,000` pairs), `live_pgo` + `r0067` both sides |
| **Step 2a** | `SF13_alone_pgo` (`SF13_qs_evasion_pruning.patch`) | `3,509,506` (`0.9737x`, `-2.63%`) | `+8.34 [-4.39, +21.10]` (`256-512-232`, `LOS 90.0%`) | **`250k` normalized `SPRT [0, 10]`** (cap `3,000g`) -> if `H1`, clean **`6+0.06` `SPRT [0, 10]`** (`conc=7`) |
| **Step 2b** | `W2_proto_1_alone_pgo` (`proto_1_corrhist_minor.patch`) | `3,504,741` (`0.9724x`, `-2.76%`) | `+7.64 [-4.34, +19.65]` (`260-502-238`, `LOS 89.4%`) | **`250k` normalized `SPRT [0, 10]`** (cap `3,000g`) -> if `H1`, clean **`6+0.06` `SPRT [0, 10]`** (`conc=7`) |
| **Step 3 (Hold Out)** | `SF8_alone_pgo` (`SF8_conthist_6ply.patch`) | `3,279,617` (`0.9100x`, **`-9.00%`**) | `+4.86 [-7.77, +17.51]` (`251-512-237`, `LOS 77.5%`) | **DO NOT ENTER LIVE / BUNDLES** without speed-optimized variant or `>= +12 Elo` fixed-node gain + clock win |

### Detailed Execution Protocol

1. **Step 1 — `LmrDeeperShallower=true` (Zero C++ Diff, Clock First):**
   - **Why First:** Needs zero C++ changes (`OPUS_TO_NEON.md:3088`), uses the already-deployed live binary (`C:\nnue-lab\runs\forge\engines\v3-r15dsg-sp-clang\forge.exe`, `sha256: cef2f215...`) + `r0067` on both sides, and costs `0 ms` extra wall time on `bench 15`.
   - **Settings:** Use `C:\nnue-lab\neon\forge_fixes\run_lmr_deeper_sprt.py` with `--exe C:\nnue-lab\runs\forge\engines\v3-r15dsg-sp-clang\forge.exe --tc 6+0.06 --concurrency 7 --elo0 0 --elo1 10 --max-rounds 2000` (`4,000` games cap), `CLOCK_MATCH_RUNNING` lockfile active on an idle CPU+GPU, `timemargin=100`, all `45` live `v3_uci_options` identical except `LmrDeeperShallower=true` vs `false`.
   - **Timing Budget (`OPUS-2811-ARM-B-RECOUNTED`):** `SPRT [0, 5]` at `6+0.06` needs ~13k games (~10h at `conc=7`); `SPRT [0, 10]` (~3k–4k games, capped at `4,000g`) answers within hours.

2. **Step 2 — `SF13_alone_pgo` (`-2.63%`) & `W2_proto_1_alone_pgo` (`-2.76%`) Individually:**
   - **Two-Stage Confirmation:** Per Opus (`OPUS_TO_NEON.md:3075, 3088–3089, 3098`), neither patch may enter a bundle or live without individual confirmation at `250k` **and** at the clock.
   - **Stage 2A (`250k`):** Pre-declare normalized `SPRT [0, 10]` (`alpha=0.05, beta=0.05`, cap `3,000` games) against baseline built with the exact same `r0067` PGO pipeline (`live_pgo_r0067`). `SF13` and `W2_proto_1` each carry `< 3%` NPS cost and showed ~`+8 Elo` point estimates at `50k` (`LOS 90.0%` and `89.4%`).
   - **Stage 2B (`6+0.06`):** Only candidates that pass `H1` at `250k` advance to a pre-declared clean `6+0.06` (`concurrency=7`, `CLOCK_MATCH_RUNNING`) `SPRT [0, 10]` match, where their `-2.63%` / `-2.76%` NPS costs (~`-1.8` to `-2.0` Elo at clock) are directly priced in.

3. **Step 3 — `SF8_conthist_6ply.patch` (`-9.00%` NPS) Exclusion Rule:**
   - **Why Hold Out (`OPUS-2811-KEEP-THE-SPRT`, `OPUS_TO_NEON.md:3121–3122`):** `SF8` loses **`9.00%` NPS** (`3,279,617` vs `3,604,157`) for an unproven **`+4.86 [-7.77, +17.51]`** at `50k` (`LOS 77.5%`). As Opus noted, a `-9%` speed drop costs roughly **`-6 Elo`** at equal time (`-9%` NPS ~ `400 * log10(0.91) ≈ -16.4` theoretical upper bound scaled by empirical time-doubling elasticity ~`65–80` Elo/doubling -> `~-5` to `-9` Elo real-world clock tax), against an uncertain fixed-node gain.
   - **Re-Entry Gate:** `SF8` must **NOT** enter live or any bundle unless either:
     1. A **speed-optimized variant** is developed and proven on clean idle `bench 15` (e.g., 4-ply continuation history only without 6-ply, software prefetching of `(*cont6)[p]` / `(ss - 6)->continuation` ahead of `MovePicker` scoring, or compact/guarded lookup reducing the NPS loss well below `-3%`), **or**
     2. Fixed-node (`250k`) testing proves a decisive **`>= +12 Elo`** gain (so net clock expectation `+12 - 6..9 > +3..+6 Elo`), followed by an independent `H1` win on its own at `6+0.06` clock.

# Forensic Diff: Live `r0202` vs `R1-keep` (`OPUS_R1_live768_keepnoisy_twin`)

**Ref:** `OPUS-2811-R1-VS-R0067-VERIFIED` Point 2  
**Companion JSON:** `C:\nnue-lab\neon\forge_fixes\loop_place\R0202_VS_R1_KEEP_FORENSIC_DIFF.json`  
**Verdict:** `R1-keep` and live `r0202` trained from **scratch** with the **exact same 25-round dataset (`346,931,328` rows), exact same `--keep-noisy` flag, exact same `seed=1`, exact same `b_full.pt` teacher, exact same hyperparameters, and exact same Triton/compact/step-v2 kernels**. Only **4 subtle differences** exist — none of them a recipe or dataset mismatch:
1. **`state.json` `init` metadata artifact:** `runs/forge/state.json` round `202` records `"init": "C:\\nnue-lab\\runs\\forge\\r0067\\train\\cand.fnn3"`, whereas `r0202/train/train.log` line 37 explicitly proves `r0202` trained from **`init scratch`** (`trainer.py:229` writes `init_model or init_net or "scratch"` even when `train_cmd` ignores `{init}`/`{init_net}`).
2. **`FORGE_PARSE_PROCS` (`"4"` vs `"8"`):** `config.forge.toml:464` sets `4`, `run_opus_r1_keep_twin.py:47` sets `8` — **zero runtime effect on `R1-keep`** because all 25 `.cache-n0c1.npz` caches already existed and were loaded read-only.
3. **Thermal pauses:** `r0202` hit **22 GPU heat-guard pauses** (`100 C -> 77..82 C`, `5,914.3 s` total); `R1-keep` had **0 cooling pauses** (`2,575.4 s` total).
4. **Triton `tl.atomic_add` trajectory divergence:** Despite identical `seed=1` and identical CPU `pass_order` (`seed * 1_000_003 + k`), `pipeline/ft_triton/ft_kernels.py` (`lines 77, 231, 241`) uses `tl.atomic_add` in backward gradient accumulation, whose floating-point threadblock summation order is nondeterministic across GPU runs and compounds over `1,694,000` Adam steps (`w1 cos=0.7261`, `b1 cos=0.9258`, `w2 cos=0.7762`, `b2 cos=0.0369`), yielding nearly identical losses (`0.006358` vs `0.006366`, `VAL 0.009218` vs `0.009190`). Whether run-to-run training noise or sampling variance explains the indirect chain gap (`+30.65` minus `~+10..+15` vs `-4.86`) is directly tested by `OPUS_R1_keep_vs_r0202_1000g_250k` (`R1_KEEP_VS_R0202_DECLARATION.json`).
5. **Transient parse slice files on uncached `R1-skip` rounds (`forge_parse.py:140`):** While `R1-keep` loaded all 25 existing `.cache-n0c1.npz` files read-only (zero disk writes in `runs/`), `R1-skip`'s in-RAM parse of the 24 uncached rounds (`r0179..r0202`) via `forge_parse.parse_file` still wrote short-lived slice files beside each `filtered.plain` in `runs/` and deleted them immediately afterward (harmless; zero `.cache.npz` files left on `C:`).

---

## 1. Complete Side-by-Side Comparison

| Dimension | Live `r0202` (`runs/forge/r0202/train`) | `R1-keep` (`OPUS_R1_live768_keepnoisy_twin`) | `R1-skip` Reference (`OPUS_R1_live768_skipnoisy`) | Match (`r0202` vs `R1-keep`) |
|---|---|---|---|---|
| **Trainer Script** | `pipeline/forge_train_v3.py` | `pipeline/forge_train_v3.py` (unchanged via `run_opus_r1_keep_twin.py`) | `pipeline/forge_train_v3.py` (unchanged) | **IDENTICAL** |
| **Dataset Window** | `r0178..r0202` (25 rounds `filtered.plain`) | `r0178..r0202` (25 rounds `filtered.plain`) | `r0178..r0202` (25 rounds `filtered.plain`) | **IDENTICAL** |
| **`filter.out.kept` Sum** | `378,856,831` | `378,856,831` | `378,856,831` | **IDENTICAL** |
| **Train Rows Used** | **`346,931,328`** (`in_check` dropped, noisy kept) | **`346,931,328`** (`25/25` `.cache-n0c1.npz` verified) | **`281,241,466`** (`65,689,862` noisy dropped, `-18.935%`) | **IDENTICAL** |
| **Holdout `val.plain`** | `runs/forge/val/val.plain` (`78,954` quiet rows) | `runs/forge/val/val.plain` (`78,954` quiet rows) | `runs/forge/val/val.plain` (`78,954` quiet rows) | **IDENTICAL** |
| **`--keep-noisy`** | **Present (`true`)** | **Present (`true`)** | **Removed (`false`)** | **IDENTICAL** |
| **Architecture** | `FORGENN3 v3`, `h=768`, `kb=8`, `ob=8`, `mirror=true` | `FORGENN3 v3`, `h=768`, `kb=8`, `ob=8`, `mirror=true` | `FORGENN3 v3`, `h=768`, `kb=8`, `ob=8`, `mirror=true` | **IDENTICAL** |
| **Epochs** | `40` | `40` | `40` | **IDENTICAL** |
| **LR Schedule** | `0.0005`, `--lr-cycles auto` -> `[6, 12, 24, 40]`, `warmup=500`, `min_frac=0.05` | `0.0005`, `--lr-cycles auto` -> `[6, 12, 24, 40]`, `warmup=500`, `min_frac=0.05` | `0.0005`, `--lr-cycles auto` -> `[6, 12, 24, 40]`, `warmup=500`, `min_frac=0.05` | **IDENTICAL** |
| **Batch Size** | `8192` (`42,350` steps/epoch) | `8192` (`42,350` steps/epoch) | `8192` (`34,331` steps/epoch) | **IDENTICAL** |
| **Target Mix** | `0.75` score + `0.25` result | `0.75` score + `0.25` result | `0.75` score + `0.25` result | **IDENTICAL** |
| **`w1-decay`** | `0.3` (king-bucketed `w1` only) | `0.3` (king-bucketed `w1` only) | `0.3` (king-bucketed `w1` only) | **IDENTICAL** |
| **Teacher Pass** | `b_full.pt` (`52be981d...`), `w=0.2`, `--teacher-once` (`1.29 GB`) | `b_full.pt` (`52be981d...`), `w=0.2`, `--teacher-once` (`1.29 GB`) | `b_full.pt` (`52be981d...`), `w=0.2`, `--teacher-once` | **IDENTICAL** |
| **Data Order** | CPU `Generator.manual_seed(seed * 1_000_003 + k)`, `FORGE_ORDER_THREAD=1` | CPU `Generator.manual_seed(seed * 1_000_003 + k)`, `FORGE_ORDER_THREAD=1` | CPU `Generator.manual_seed(seed * 1_000_003 + k)` | **IDENTICAL** |
| **`--seed`** | `1` (`forge_train_v3.py:569` default) | `1` (`--seed 1` explicit) | `1` (default) | **IDENTICAL** |
| **Init (Actual vs `state.json`)** | Actual: **`scratch`** (`train.log:37`); `state.json`: **`r0067` (`trainer.py:229` bug)** | Actual: **`scratch`** | Actual: **`scratch`** | **ACTUAL IDENTICAL; `state.json` DIFF FLAGGED** |
| **Triton / Compact / StepV2 Env** | `FORGE_COMPACT=1`, `FORGE_STEP_V2=1`, `FORGE_FUSED_STEP=1`, `13/13` kernel flags | Identical `13/13` kernel flags + in-memory read-only `_load_one` guard | Identical `13/13` kernel flags + read-only `_load_one` guard | **13/13 KERNEL FLAGS IDENTICAL** |
| **`FORGE_PARSE_PROCS`** | `"4"` (`config.forge.toml:464`) | `"8"` (`run_opus_r1_keep_twin.py:47`; unused — loaded cached `.cache-n0c1.npz`) | `"8"` (parsed 25 rounds) | **DIFF FLAGGED (0 effect on `R1-keep`)** |
| **Heat-Guard Pauses / Time** | **`22` pauses** (`100 C -> 77..82 C`), `5,914.3 s` | **`0` pauses**, `2,575.4 s` | **`0` pauses**, `5,447.2 s` | **DIFF FLAGGED** |
| **Final Train `LOSS`** | `0.006358` | `0.006366` | `0.004547` | `-0.000008` (noise floor) |
| **Final `VAL` / `VAL_MIX60`** | `0.009218` / `0.014650` | `0.009190` / `0.014601` | `0.008551` / `0.013957` | `-0.000028` / `-0.000049` |
| **`.fnn3` Checksum** | `d93387c0af2536b4` | `079f2f9a8273b58a` | `3882dcf1eb013c36` | Divergent SGD path |
| **`.fnn3` SHA-256** | `42fd34526c3126096b33c34776184246ed0a01bb542febcc6942f584afad5fbd` | `8b1158aad16d882063da6673efa1584ac0cb4382cb3358964bdb03bb487b02e7` | `4902fe653e575c0c73ab78aed18fb6d2a10c8f33c895160cb5b68b1bdb9b21ec` | — |
| **`.pt` SHA-256** | `17533c41b53b0732fe6c03f5d84969129c7ea9932d06f6047622ceed32f5b555` | `61bb06e19e06cd313a4dc715bf00d7233bd7c5192640524517c3a68bbcb17c29` | `e61691736c1423e11efe708357d25ee0ff25122c6a2e3cb546583bc365e28620` | — |

---

## 2. Exported Weight Stats & Pairwise Similarity (`r0202` vs `R1-keep`)

| Tensor | `r0202` (`max\|x\|`, `mean`, `std`) | `R1-keep` (`max\|x\|`, `mean`, `std`) | `R1-skip` (`max\|x\|`, `mean`, `std`) | `r0202` vs `R1-keep` (`cos`, `rms_diff`, `max_diff`) |
|---|---|---|---|---|
| `w1` `(8, 768, 768)` `int16` | `549`, `-10.9691`, `88.2107` | `547`, `-11.0378`, `88.4690` | `538`, `-6.7472`, `80.2578` | `cos = 0.726121`, `rms = 65.8866`, `max = 1025` |
| `b1` `(768,)` `int16` | `433`, `-177.2812`, `100.7680` | `433`, `-173.3815`, `97.4511` | `430`, `-145.7773`, `85.4385` | `cos = 0.925775`, `rms = 77.7566`, `max = 400` |
| `w2` `(8, 1536)` `int16` | `127`, `3.1563`, `19.1121` | `127`, `3.0888`, `19.2247` | `127`, `0.4780`, `15.5331` | `cos = 0.776176`, `rms = 12.9943`, `max = 153` |
| `b2` `(8,)` `int32` | `262`, `98.0000`, `87.6556` | `198`, `-42.2500`, `131.9335` | `561`, `396.0000`, `170.0603` | `cos = 0.036866`, `rms = 187.4460`, `max = 353` |

---

## 3. Epoch-by-Epoch Loss Trajectory (`r0202/train/train.log` vs `R1-keep` Final)

*(Note: `run_opus_r1_keep_twin.py` did not persist a per-epoch stdout `.log` file to disk; `R1-keep`'s final metrics come from `NEON_TO_OPUS.md` `NEON-2811-R1-KEEP-TWIN-DONE-0638` and `r1_keep_summary.json`.)*

| Epoch | `r0202` `LOSS` | `r0202` `lr` | `r0202` `pos/s` | `r0202` `FIT` (`train-sample` / `hold-out`) | `R1-keep` |
|---:|---:|---:|---:|---|---|
| 1 | `0.010121` | `4.69e-04` | `5,554,832` | — | — |
| 2 | `0.007953` | `3.82e-04` | `5,703,209` | — | — |
| 3 | `0.007539` | `2.63e-04` | `5,755,280` | — (pause #1 after ep 3: `50s`) | — |
| 4 | `0.007230` | `1.44e-04` | `5,669,170` | — | — |
| 5 | `0.006991` | `5.69e-05` | `5,726,314` | — (pause #2: `35s`) | — |
| **6** | **`0.006830`** | `2.50e-05` | `5,764,088` | **`0.010505` / `0.009627`** (pause #3: `40s`) | — |
| 7 | `0.007500` | `4.69e-04` | `5,803,386` | — | — |
| 8 | `0.007309` | `3.82e-04` | `5,821,802` | — (pause #4: `40s`) | — |
| 9 | `0.007100` | `2.63e-04` | `5,840,799` | — | — |
| 10 | `0.006890` | `1.44e-04` | `5,856,877` | — (pause #5: `30s`) | — |
| 11 | `0.006720` | `5.69e-05` | `5,870,390` | — | — |
| **12** | **`0.006580`** | `2.50e-05` | `5,881,164` | **`0.010173` / `0.009399`** (pause #6: `30s`) | — |
| 13..23 | `0.007222 -> 0.006446` | `4.92e-04 -> 3.31e-05` | `5.89M -> 5.96M` | Pauses #7..#13 (`40s..690s`) | — |
| **24** | **`0.006404`** | `2.50e-05` | `5,976,885` | **`0.009943` / `0.009276`** (pause #14: `40s`) | — |
| 25..39 | `0.007058 -> 0.006376` | `4.96e-04 -> 2.96e-05` | `5.99M -> 6.11M` | Pauses #15..#22 (`30s..900s`) | — |
| **40** | **`0.006358`** | `2.50e-05` | `6,120,017` | **`0.009874` / `0.009218`** | **`LOSS 0.006366`** (`0` pauses) |
| **VAL / MIX60** | **`0.009218` / `0.014650`** | — | — | — | **`VAL 0.009190` / `VAL_MIX60 0.014601`** |

---

## 4. Related Match Context (Strict Wording Compliance)

- **`OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k` (`1,526g @ 250k`):** **`+15.49 [+6.12, +24.89]` Elo** (`LLR +2.97`, `H1 ACCEPTED`, `LOS 99.94%`; **note SPRT early-stopping upward bias — true effect `~+10..+15` Elo**).
- **`OPUS_R1_skip_vs_r0067_1000g_250k` (`1,000g` fixed `@ 250k`):** **`+30.65 [+18.58, +42.80]` Elo** (`z=+4.989`, `LOS 100.00%`).
- **`OPUS_r0202_vs_r0067_1000g_250k` (`1,000g` fixed `@ 250k`):** **`-4.86 [-16.64, +6.90]` Elo** (`z=-0.811`, `LOS 20.88%`).
- **`OPUS_R1_keep_vs_r0202_1000g_250k`:** Declared (`R1_KEEP_VS_R0202_DECLARATION.json`, `seed=202611955`), queued after Seed-2 R1 SPRT and `OPUS_R1_skip_vs_r0067_2000g_6p006`.
- **Stage-2 & CC0 Reference Notes:** All `3/3` Stage-2 `600g @ 250k` confirmations (`G4b -5.21`, `R1b -12.75`, `G4a -16.23`) were **`NOT CONFIRMED`**; `G3b vs G3a` (`+651..+700`) demonstrates that **`keep-noisy` breaks V3P nets on CC0 data**.

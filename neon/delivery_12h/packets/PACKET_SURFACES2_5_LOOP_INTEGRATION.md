# Surfaces 2–5 Atomic Placement Packet: Loop Integration, Cadence, & Anchors

**Target Audience:** Opus / Fable (Addressing Conditions (a), (c), (d), `C:\nnue-lab\neon\OPUS_TO_NEON.md:2850–2884`)  
**Scope:** Atomic loop integration of `FORGENN3-P` (Surfaces 2–5) alongside Surface 1 (`V3P_pairwise_psqt_fused_v3.patch`), strictly gated behind `G3_FULL25` confirmation (`250k` + clean GPU+CPU-idle `2,000g @ 6+0.06`).

---

## 1. Live Artifact Inventory & Checksums

| Surface / Role | Source / Patch Path | Target in `C:\nnue-lab\` | Bytes | Live SHA-256 |
|---|---|---|---:|---|
| Inventory | `C:\nnue-lab\neon\forge_fixes\PLAN_V3P_LOOP_PLACEMENT_INVENTORY.md` | *(reference)* | 8,373 | `7ae59122a5c0628b77eda9681668907011a3d2f0f18ae5bf531bb46a72bcde21` |
| Pkg Verify | `C:\nnue-lab\neon\forge_fixes\V3P_PLACEMENT_PACKAGE_VERIFICATION.json` | *(reference)* | 2,346 | `bed11cb8c91772de96e3b3fb4833799bc370f69c379a79b68c6208870c2d72ae` |
| S2 Format/Ref | `C:\nnue-lab\neon\forge_fixes\forge_v3p.py` | `pipeline\forge_v3p.py` | 10,269 | `9c649326b775372a753354e19429f72e4262bfb5dc04e265812c5adcaddb81f0` |
| S3 Loop Adapter | `C:\nnue-lab\neon\forge_fixes\forge_train_v3p_loop_adapter.py` | `pipeline\forge_train_v3p.py` | 7,880 | `55bc6078392b19df16860d8a93420c9af3b52bfeefe0026ef04888da841b7631` |
| S3 Core Trainer | `C:\nnue-lab\neon\forge_fixes\train_v3p.py` | `pipeline\train_v3p.py` | 36,344 | `d93bae73a621eff48d86c585992f97794efec19f2d748bb6f57877691192953d` |
| S3 Stream Trainer | `C:\nnue-lab\neon\forge_fixes\train_v3p_stream.py` | *(Server Day / CC0)* | 18,240 | `441bb3cb0dbc79ff24c0d7db16c98ecfc061bc90b46dde2675202a04e2dab6be` |
| S4a Parity Patch | `C:\nnue-lab\neon\forge_fixes\patches\v3p_surface4a_v3_parity.patch` | `pipeline\tools\v3_parity.py` | 380 | `29d2af4dd4601312889215cbef8f08977d71d9a55d65f0023880b7013b41c777` |
| S4b Model Check | `C:\nnue-lab\neon\forge_fixes\patches\v3p_surface4b_v3_model_check.patch` | `pipeline\tools\v3_model_check.py` | 1,395 | `68572e4546a453def301c8e163ab3470b49ae1dc7af8e40b723f651aa708589c` |
| S5 Parity 7/8 | `C:\nnue-lab\neon\forge_fixes\patches\datagen_uci_parity_7_8_minimal.patch` | `pipeline\nnloop\datagen_uci.py` | 5,771 | `184c6d2b8f880a7a22d23667e5b9ab38df53037c9736e14a115c84b9efa556c7` |
| S5 Anchor Draws | `C:\nnue-lab\neon\forge_fixes\anchors\dead_draws_20k_clean.fqs.z` | `runs\forge\anchors\dead_draws_20k_clean.fqs.z` | 127,484 | `f2073b88b95d109c5b130fce503f8f9126baf852c47db4af4e31f9c5e0976716` |
| S5 Anchor Wins | `C:\nnue-lab\neon\forge_fixes\anchors\won_endings_syzygy_20k.fqs.z` | `runs\forge\anchors\won_endings_syzygy_20k.fqs.z` | 154,309 | `c2f51696b886c6cad78da2cca253352d79e6a188778c5ab35526b6321a4a96de` |
| S2 Test Script | `C:\nnue-lab\neon\forge_fixes\test_v3p_surface2_format.py` | *(read-only test)* | 4,715 | `c3157540e4cf92804183607bbd338262afd3e271240e8c0dd5cd1a6b60031574` |
| S4 Test Script | `C:\nnue-lab\neon\forge_fixes\test_v3p_surface4_parity_and_modelcheck.py` | *(read-only test)* | 5,398 | `18f7d8de513c3386c69682b13911bed385b5407645956eb6325db95dd9181528` |
| Target Config | `C:\nnue-lab\pipeline\config.forge.toml` | `pipeline\config.forge.toml` | 54,328 | `d3c4f4eec16eeda71318476cb4d031c252529f77e491e294ddc49fc79c2fd488` |
| Target Datagen | `C:\nnue-lab\pipeline\nnloop\datagen_uci.py` | *(patched by S5)* | 58,740 | `58a69bd651e50d6a78ed1827ad5f2bbd6c7619d28327641cfdf249b2efb669ad` |
| Target Parity | `C:\nnue-lab\pipeline\tools\v3_parity.py` | *(patched by S4a)* | 3,372 | `3fecbe774088dfa38024219fc5f2f2a998e7bb7c352a1cf216ee148614bee05b` |
| Target ModelChk | `C:\nnue-lab\pipeline\tools\v3_model_check.py` | *(patched by S4b)* | 5,371 | `92e018a72ea3f53fab1936fcfbcd73eb8a61fe0eaa6536387cceadc8138a406a` |

*(Note: `C:\nnue-lab\pipeline\` is not a git repo; `git -C C:\nnue-lab apply --check` / `apply` operates cleanly with `a/pipeline/...` paths. Always back up `config.forge.toml`, `datagen_uci.py`, `v3_parity.py`, and `v3_model_check.py` outside `pipeline/` before placement.)*

---

## 2. Atomic Placement, Tests, & Rollback (Surfaces 2–5)

### Surface 2: Binary Format & Integer Reference (`pipeline\forge_v3p.py`)
- **Action:** `Copy-Item C:\nnue-lab\neon\forge_fixes\forge_v3p.py C:\nnue-lab\pipeline\forge_v3p.py`
- **Design (`forge_v3p.py:1–227`):** Imports `forge_v3 as base`, adds `FLAG_PAIRWISE = 4`, `FLAG_PSQT = 8`, `MAX_PSQT = 16 * QA * QB = 261,120`, and 16-bucket mirrored `king_layout(16)`. `NetP.check_bounds()` enforces `step = 64` / `h_max = 1536` for pairwise, `|w2| <= 127`, `max|b1| + 32*max|w1| <= 32767`, and `|psqt| <= 261,120`. `write_net()` writes `<path>.part` -> `os.fsync()` -> `os.replace()`. `reference_eval()` computes exact integer pairwise CReLU + truncating `(p_us - p_th) / 2` PSQT.
- **Fail-Before / Pass-After:**
  - *Before:* Legacy `pipeline/forge_v3.read_net(G3_NET)` fails parity (`50/50` wrong on `FORGENN3-P`).
  - *After:* `test_v3p_surface2_format.py` -> `SURFACE_2_FAIL_BEFORE_PASS_AFTER_OK (v3p_diffs=0/50, legacy_diffs=0/50)`, `RC=0`. *(Note: Do NOT invoke `forge_v3p.selftest()` directly during read-only checks; it writes `_tmp_test_v3*.fnn3` under `neon/forge_fixes/`.)*
- **1-Step Rollback:** `Remove-Item C:\nnue-lab\pipeline\forge_v3p.py`

### Surface 3: Loop Trainer & CLI Adapter (`pipeline\forge_train_v3p.py` + `pipeline\train_v3p.py`)
- **Critical Placement Detail:** `forge_train_v3p_loop_adapter.py:28,73` resolves `THIS_DIR = Path(__file__).resolve().parent` and invokes `sys.executable, str(THIS_DIR / "train_v3p.py")`. Therefore **both** `forge_train_v3p.py` and `train_v3p.py` MUST be placed in `C:\nnue-lab\pipeline\`:
  ```powershell
  Copy-Item C:\nnue-lab\neon\forge_fixes\forge_train_v3p_loop_adapter.py C:\nnue-lab\pipeline\forge_train_v3p.py
  Copy-Item C:\nnue-lab\neon\forge_fixes\train_v3p.py C:\nnue-lab\pipeline\train_v3p.py
  ```
- **Exact Adapter Contract & CLI Flags (`forge_train_v3p_loop_adapter.py:38–178`):**
  - `load_model(path)`: asserts `ck.get("arch") == "v3p"`, builds `ForgeNetV3P`, loads `ck["state"]`.
  - `cmd_export()`: exports via `to_file_net_p`, writes `<net>.part` (`write_net` internally writes `.part.part -> .part`) -> `os.replace(tmp, net_path)`, and re-reads via `forge_v3p.read_net()` to verify checksum & dimensions.
  - `cmd_train()`: runs `THIS_DIR / "train_v3p.py"` (`--save-ckpt-every 1 --resume`), atomically replaces `cand.pt -> --out-model`, and prints `VAL_MIX60` + `VAL` for `pipeline/nnloop/trainer.py:216–228`.
  - Exposed flags: `--datasets`, `--val`, `--out-model`, `--hce-exe`, `--epochs` (`40`), `--lr` (`0.0005`), `--batch-size` (`8192`), `--hidden` (`1024`), `--king-buckets` (`8`), `--lr-cycles` (`auto`), `--w1-decay` (`0.3`), `--ob-smooth` (`2e-6`), `--mix` (`0.75`), `--loss-pow` (`2.0`), `--distill-net`, `--distill-weight` (`0.2`), `--anchor-shards`, `--anchor-repeat` (`25`), `--fqs-shards`, `--fqs-repeat` (`3`), `--keep-noisy` (compat no-op), `--teacher-once` (compat no-op), `--seed` (`1`). *(Note: adapter intentionally omits `--ob-reweight`, `--score-weight-mode`, and `--use-shard-weights`, matching `G3_FULL25`'s `none/none/false`.)*
- **Fail-Before / Pass-After:**
  - *Before:* `pipeline/forge_train_v3p.py` absent; `forge_train_v3.load_model()` fails on `arch="v3p"`.
  - *After:* `C:\nnue-lab\venv101\Scripts\python.exe -B C:\nnue-lab\pipeline\forge_train_v3p.py --selftest` -> `LOOP_ADAPTER_V3P_SELFTEST_PASS`, `RC=0`.
- **1-Step Rollback:** `Remove-Item C:\nnue-lab\pipeline\forge_train_v3p.py, C:\nnue-lab\pipeline\train_v3p.py`

### Surface 4a & 4b: Loop Gates (`pipeline\tools\v3_parity.py` & `v3_model_check.py`)
- **Action:**
  ```powershell
  git -C C:\nnue-lab apply --check C:\nnue-lab\neon\forge_fixes\patches\v3p_surface4a_v3_parity.patch
  git -C C:\nnue-lab apply --check C:\nnue-lab\neon\forge_fixes\patches\v3p_surface4b_v3_model_check.patch
  git -C C:\nnue-lab apply C:\nnue-lab\neon\forge_fixes\patches\v3p_surface4a_v3_parity.patch
  git -C C:\nnue-lab apply C:\nnue-lab\neon\forge_fixes\patches\v3p_surface4b_v3_model_check.patch
  ```
- **Diff Summary:**
  - `4a` (`14` L): `try: import forge_v3p as forge_v3 except ImportError: import forge_v3` (`v3_parity.py:16–19`, patch lines `7–11`).
  - `4b` (`33` L): imports `forge_v3p` (fallback `forge_v3`) and `forge_train_v3p as v3p` (fallback `None`); loads checkpoint header on CPU and dispatches `ckpt_hdr.get('arch') == 'v3p'` to `v3p.load_model(model_path)` (raising `RuntimeError('FORGENN3-P checkpoint requires pipeline/forge_train_v3p.py')` if `v3p is None`).
- **Fail-Before / Pass-After:**
  - *Before:* `v3_parity.py` exits `RC=1` on `FORGENN3-P`; `v3_model_check.py` fails on `arch="v3p"` `.pt`.
  - *After:* `test_v3p_surface4_parity_and_modelcheck.py` passes (`RC=0`: `100` pos `0` differ on `FORGENN3-P`, catches `planted_bug=1`, legacy `r0067` `RC=0`; with `--with-gpu-modelcheck` on idle GPU, `SURFACE_4B_GPU_PASS_OK`).
- **1-Step Rollback:**
  ```powershell
  git -C C:\nnue-lab apply -R C:\nnue-lab\neon\forge_fixes\patches\v3p_surface4b_v3_model_check.patch
  git -C C:\nnue-lab apply -R C:\nnue-lab\neon\forge_fixes\patches\v3p_surface4a_v3_parity.patch
  ```

### Surface 5: Parity 7/8 Patch, Anchors, `config.forge.toml`, & Engine Tag
1. **Datagen Alternating 7/8 Parity (`pipeline\nnloop\datagen_uci.py`):**
   - Apply `datagen_uci_parity_7_8_minimal.patch` (`111` L): adds `_random_count_for_game(g, game_idx)` (odd `game_idx & 1` -> `random_move_count_alt`, even -> `random_move_count`), contiguous `set(range(k))` + `write_min_ply = k` when `write_min_ply == random_move_count` in both `play_game()` & `play_game_sg()`, `selfgame_ok()` bound check `alt <= random_move_max_ply + 1`, and per-worker `game_idx` counter.
   - *Before / After:* Before patch, `random_move_count_alt = 7` is ignored (100% ply-8 starts). After (`pilot_datagen_parity_7_8_G3_R4.json`), `200` games split `99` ply-8 / `99` ply-7 (`2` early mates), shifting `white_stm_pct` `50.15% -> 49.99%` and `mean_white_cp` `+86.04 -> +69.99`.
   - *Rollback:* `git -C C:\nnue-lab apply -R C:\nnue-lab\neon\forge_fixes\patches\datagen_uci_parity_7_8_minimal.patch`
2. **Frozen Syzygy Anchors (`runs\forge\anchors\`):**
   ```powershell
   New-Item -ItemType Directory -Force C:\nnue-lab\runs\forge\anchors | Out-Null
   Copy-Item C:\nnue-lab\neon\forge_fixes\anchors\dead_draws_20k_clean.fqs.z C:\nnue-lab\runs\forge\anchors\
   Copy-Item C:\nnue-lab\neon\forge_fixes\anchors\won_endings_syzygy_20k.fqs.z C:\nnue-lab\runs\forge\anchors\
   ```
3. **`pipeline\config.forge.toml` Exact Keys & PGO Recursion Trap:**
   - **`[engine]` (`config.forge.toml:169–170`):** Bump `v3_build_tag` (e.g., `"r15dsg-v3p-sp-clang"`) so `nnloop/engine.py:62` does **not** reuse cached `runs/forge/engines/v3-r15dsg-sp-clang/forge.exe`.
     > **CRITICAL RECURSION TRAP (`forge/tools/build_forge_v3r15dsg_sp_clang_pgo.sh:7–9`):** The PGO script calls `pgo_selfgame.py`, which calls `engine_for_net(cfg, net)` on `PGOSP_CFG` (`config.forge.toml`). If `runs/forge/engines/v3-<new_tag>/forge.exe` does **not** exist yet when `engine_for_net` runs inside PGO, `engine_for_net` invokes `v3_build_cmd` recursively! **Build and place `C:\nnue-lab\runs\forge\engines\v3-<new_tag>\forge.exe` by hand BEFORE (or together with) switching `v3_build_tag`**, then verify `nnloop.engine.check_engine_loads_net(cfg, v3p_net)`.
   - **`[datagen]` (`config.forge.toml:274–279`):** Keep `random_move_count = 8`, `random_move_min_ply = 0`, `random_move_max_ply = 7`, `write_min_ply = 8`, and add:
     ```toml
     random_move_count_alt = 7
     ```
   - **`[train]` (`config.forge.toml:357–465`):**
     ```toml
     train_cmd  = '"{python}" C:/nnue-lab/pipeline/forge_train_v3p.py train --datasets {datasets} --val "{val}" --out-model "{model}" --hce-exe C:/nnue-lab/forge/build/hce_dump.exe --epochs {epochs} --lr {lr} --batch-size {batch_size} --lr-cycles auto --w1-decay 0.3 --ob-smooth 2e-6 --mix 0.75 --distill-net C:/nnue-lab/runs/forge/r0067/train/cand.pt --distill-weight 0.2 --anchor-shards C:/nnue-lab/runs/forge/anchors/dead_draws_20k_clean.fqs.z C:/nnue-lab/runs/forge/anchors/won_endings_syzygy_20k.fqs.z --anchor-repeat 25 --hidden 1024'
     export_cmd = '"{python}" C:/nnue-lab/pipeline/forge_train_v3p.py export --model "{model}" --net "{net}"'
     max_minutes = 240
     ```
     *(Keep `batch_size = 8192`, `max_epochs = 40`, `lr = 0.0005`, `init = "scratch"`, `max_window_positions = 388000000`, `keep_noisy = true`. Note `max_minutes = 240` overrides the `180`-min default in `nnloop/trainer.py:201`.)*
   - *Config Check & Rollback:* Verify `nnloop.common.load_config(...)` + `datagen_uci.selfgame_ok(cfg) == ""` + `net_sanity.py v2`; rollback by restoring `config.forge.toml.bak_pre_v3p`.

### Untouched Files (Opus Condition (d))
Zero edits required in: `pipeline/run.py`, `pipeline/nnloop/engine.py`, `pipeline/nnloop/trainer.py`, `pipeline/nnloop/match.py`, `pipeline/nnloop/filterqc.py` (`[filter] min_ply = 0`), `pipeline/nnloop/diskrelief.py`, `pipeline/nnloop/heat.py`, `pipeline/tools/net_test.py`, `pipeline/forge_v3.py`, `pipeline/forge_train_v3.py`, and `net_sanity.py` v2.

---

## 3. Round Cadence (`~2.0h -> ~2.9h`) & Anchor Weight (`0.283%`) Math

### 3.1 Round Cadence under `[train] max_minutes = 240` (Condition (c))
Verified from `runs/forge/state.json` (`r0199–r0202`), `r0202/train/train.log`, and `G3_FULL25_v3p_1024_cc0_anchored/metrics.json`:

- **Live `768w` `FORGENN3` (`r0202`, Triton fused step, `5.55–6.12M pos/s`, `346.9M` rows = `346,931,328`):**
  - Training (`40` epochs + `22` cooling pauses = `44` `HEAT GUARD` log lines): **`5,914.3s = 98.57 min = 1.64 h`** (`r0199–r0201`: `51.7–58.0 min`, `0–3` cooling pauses).
  - Self-play (`16M` pos, `r0202` standalone `18.0 min` = `1,079.2s`, `~26–35 min` under load): **100% hidden** behind training via `early_selfplay = true` (`r0199–r0201` `datagen = 0.0s`).
  - Filter (`~1.6 min`: `92.8–94.7s`) + Gate SPRT (`4,000g @ 50k`): `968–993s` (`~16.5 min`, up to `~20–25 min` = `~0.35 h`).
  - **Live Total:** `1.64 h + 0.35 h` = **`~2.0 hours / round`**.
- **Proposed `1024w` `FORGENN3-P` (`G3_FULL25` eager PyTorch + Triton sparse kernel, `~1.95M pos/s`, `353.45M` rows):**
  - Training (`40` epochs, `25` rounds + CC0 + anchors): `metrics.json` measured **`9,157.4s = 152.62 min = 2.544 h`** (including `gpu_paused_s = 1,950.3s = 32.5 min` across `75` thermal pauses, `max 98.0 C`; active GPU compute = `7,207.1s = 120.1 min`).
  - Self-play (`16M` pos): still **100% hidden** behind `152.6 min` training.
  - Filter + Gate SPRT (`4,000g @ 50k`): **`~0.35 h`** (`~20–25 min`).
  - **Proposed Total:** `2.544 h + 0.35 h` = **`~2.9 hours / round`** (**`+0.9 h` / `+45%`** vs `r0202`).
  - **`max_minutes = 240` (`4.0 h`):** `240 / 152.6 = 1.57x` headroom (`~87 min` margin above `G3_FULL25` wall time, avoiding `180 min` default timeout). *Future Triton `FORGE_FUSED_STEP` port returns `1024w` training to `~70–95 min` (`~2.0h/round`) with zero `.fnn3` change.*

### 3.2 Anchor Weight Math (`0.283%` / `0.2829%`) & `--ob-reweight cc0` Exemption
- **Anchor Counts (`FQS1` `8`-byte header + `38`-byte/row `FQS_DTYPE`, `760,008` B decompressed each):** `dead_draws_20k_clean.fqs.z` (`20,000` rows) + `won_endings_syzygy_20k.fqs.z` (`20,000` rows) = **`40,000` unique rows** (`mask_bits = 0`).
- **25-Round Base Window (`G3_FULL25`):** **`352,448,538`** rows (self-play + CC0 `3x` after in-check filter).
- **At `--anchor-repeat 25`:**
  - Anchor rows/epoch = `40,000 * 25 = 1,000,000`
  - Total epoch rows = `352,448,538 + 1,000,000 = 353,448,538` (**`~353.45M`**)
  - Exact anchor share = `1,000,000 / 353,448,538 = 0.002829266... = 0.2829% ≈ 0.283%` (`1,000` presentations per anchor over `40` epochs).
  - Alternatives: `--anchor-repeat 10` -> `400,000 / 352,848,538 = 0.1134%`; `--anchor-repeat 4` -> `160,000 / 352,608,538 = 0.0454%`.
- **`train_v3p_stream.py --ob-reweight cc0` & Anchor Weight-Exemption Rule (`train_v3p_stream.py:293–311`):**
  - Non-anchor rows `[0 : n_main]` extract `ob_idx = (flags >> 4) & 7` and multiply by the clamped CC0 LUT **`[1.50, 1.089, 1.167, 0.978, 0.922, 0.883, 0.891, 0.70]`** (clamped `[0.70, 1.50]`; contrast `m4`: `[1.65, 1.01, 1.07, 1.00, 1.00, 0.99, 0.95, 0.65]`), then normalize `w_g[:n_main] /= mean(w_g[:n_main])`.
  - **Anchor Weight-Exemption Rule (`:310`):** `w_g[n_main:] = 1.0` strictly — anchor rows are exempt from `ob_lut`, `weight_u8`, and `mean()` normalization, preserving exact `1.0` weight and exact WDL target `0.5 * (res8 + 1.0)`.

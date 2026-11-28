# Planned One-Step `FORGENN3-P` Loop Placement Inventory (For Opus / Fable Review If `G3_FULL25` Wins)

> **Purpose:** Lists every file, format, trainer, gate, and config surface required so `FORGENN3-P` (`1024w` Pairwise CReLU + Direct Factorized PSQT) can be audited line-by-line and placed into `C:\nnue-lab\pipeline\` in **one planned atomic step** (never piecemeal), ONLY if `G3_FULL25` wins both `1,000g @ 50k` AND clean GPU+CPU-idle `2,000g @ 6+0.06` equal-time confirmation.
>
> Addresses all four conditions `(a)–(d)` from `OPUS-2711-READINGS-ON-2219` (`22:19 PC`).

---

## Condition (a): Standalone Per-Surface Diffs & Fail-Before / Pass-After Tests

| Surface | Target in `C:\nnue-lab\` | Standalone Artifact / Patch | Fail-Before / Pass-After Test |
|---|---|---|---|
| **1. Engine Kernel** | `forge/r15dsg/` (`include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`) | `patches/V3P_pairwise_psqt_fused_v3.patch` (`679` L, `sha256=57f3455f...`) | Master Gates `--full` + `-DFORGE_NNUE_V3_VERIFY=1` (`448,340` live nodes, `0` failures) + UBSan (`0` errors) + `60/60` multithread mates; base engine rejects `FlagPairwise|FlagPsqt` (`flags=12`). |
| **2. Binary Format & Integer Ref** | `pipeline/forge_v3p.py` (new module; leaves `forge_v3.py` untouched) | `neon/forge_fixes/forge_v3p.py` | Round-trip export/read + bit-exact `reference_eval()` against engine on both `FORGENN3-P` and legacy `r0067` (`FORGENN3`); legacy `forge_v3.read_net()` fails on `flags=12`. |
| **3. Loop Trainer CLI Adapter** | `pipeline/forge_train_v3p.py` (new module; imports `train_v3p.py` & `forge_v3p.py`) | `neon/forge_fixes/forge_train_v3p_loop_adapter.py` + `train_v3p.py` | `forge_train_v3p_loop_adapter.py --selftest` (`LOOP_ADAPTER_V3P_SELFTEST_PASS`); exposes `train`, `export`, and `load_model()` for `v3_model_check.py`. |
| **4a. Engine Parity Gate** | `pipeline/tools/v3_parity.py` | `patches/v3p_surface4a_v3_parity.patch` (`380` B, `sha256=29d2af4d...`, `apply_rc=0`) | `test_v3p_surface4_parity_and_modelcheck.py`: BEFORE patch FAILS (`rc != 0`) on `FORGENN3-P`; AFTER patch PASSES (`rc == 0`) on `FORGENN3-P`, catches `planted_bug=1`, AND still PASSES on legacy `r0067`. |
| **4b. Trainer-vs-Engine Gate** | `pipeline/tools/v3_model_check.py` | `patches/v3p_surface4b_v3_model_check.patch` (`1,395` B, `sha256=68572e45...`, `apply_rc=0`) | `test_v3p_surface4_parity_and_modelcheck.py --with-gpu-modelcheck`: dispatches `ckpt["arch"] == "v3p"` via `forge_train_v3p.load_model()` + `forge_v3p.reference_eval()` (legacy `.pt` unchanged). |
| **5. Config & State** | `pipeline/config.forge.toml` + `runs/forge/state.json` + `runs/forge/anchors/` | Exact `[engine]`, `[train]`, `[datagen]` keys below | `nnloop.common.load_config()` parse check + `pipeline/tools/v3_parity.py` + `net_sanity.py v2` (already compatible with zero edits!). |

---

## Condition (b): Line-by-Line Audit Map for `V3P_pairwise_psqt_fused_v3.patch` (`679` lines)

1. **Header (`include/forge/nnue_v3.hpp`):**
   - Adds `FlagPairwise = 4`, `FlagPsqt = 8`, `MaxHidden = 1536`, `MaxPsqt = 16 * QA * QB` (`= 262,144` for `QA=255, QB=64`).
   - Adds `psqt` table (`int32_t`, `[KingBuckets * 768 * OutputBuckets]`) and `int32_t psqt_acc[2][OutputBuckets]` to incremental `Accumulator` / `FinnyEntry` (updated on every `add`/`sub` feature delta alongside `acc[2][Hidden]`, with exact horizontal king-mirroring!).
   - Legacy `FORGENN3` (`flags == 0`, `r0067`) executes the unchanged SCReLU path; zero behavioral drift on legacy nets.
2. **AVX-512 Split-Stream Fused Kernel (`src/nnue_v3.cpp`):**
   - Splits `acc[stm][0..H-1]` into low half `a = [0..H/2-1]` and high half `b = [H/2..H-1]`, clamps both to `[0, QA=255]`, computes pairwise `mullo_epi16(a, b)` divided by `QA` via exact integer arithmetic matching `forge_v3p.reference_eval`, dots against `l1_w` (`int8`/`int16` packed) via `vpmaddwd` into `int32` accumulators (`4` independent lanes to break FMA dependency chains), adds `psqt_acc[stm][ob] - psqt_acc[opp][ob]`, and scales by `1 / (QA * QB)` -> centipawns.
   - **Verification Evidence:** `-DFORGE_NNUE_V3_VERIFY=1` checks every incremental `acc` + `psqt_acc` against full board scratch recomputation (`448,340` live search nodes, `0` mismatches); UBSan (`0` errors); `60/60` multithread mates; bit-exact `0` diff across `2,000+` hold-out positions vs Python `forge_v3p.reference_eval()`.

---

## Condition (c): Exact Loop Round Cadence (Hours) & Anchor Weight Per Round

### 1. Round Length Comparison (Live Loop `r0199–r0202` vs `FORGENN3-P` `1024w` Eager PyTorch)
Measured directly from `runs/forge/state.json` and `runs/forge/r0199..r0202/train/train.log`:
- **Current Live `768w` `FORGENN3` Loop (`r0202`, Triton fused step, `4.2–6.1M pos/s`):**
  - Training (`40` epochs, `25` rounds = `348.8M` rows, with RX 7900 XT `98 C -> 82 C` heat-guard pauses): **`~98 min` (`1.63 h`)** wall time (`r0202`: `02:36 -> 04:14 PC`).
  - Self-play (`16M` positions): **`~26–35 min`**, **100% hidden** behind training via `[datagen] early_selfplay = true`.
  - Gate SPRT (`4,000g @ 50k`, `concurrency=12`): **`~20–25 min`**.
  - **Current Total Round Length:** **`~2.0 hours / round`** (plus `~40 min` confirmation only on promoted rounds).
- **Proposed `1024w` `FORGENN3-P` Loop (Eager PyTorch `train_v3p.py`, `1.95M pos/s`):**
  - Training (`40` epochs, `25` rounds + anchors = `353.3M` rows, including RX 7900 XT heat pauses): **`~153 min` (`2.55 h`)** wall time (measured on `G3_FULL25`: `19:53 -> 22:26 PC`).
  - Self-play (`16M` positions): **`~26–35 min`**, still **100% hidden** behind training via `early_selfplay = true`.
  - Gate SPRT (`4,000g @ 50k`, `concurrency=12`): **`~20–25 min`**.
  - **Proposed Total Round Length:** **`~2.9 hours / round`** (**`+0.9 h` / `+45%` per round** — NOT 4× longer, because `r0202` already spends `98 min` wall time with thermal pauses and `early_selfplay` hides datagen!).
  - Setting `[train] max_minutes = 240` gives a safe `1.55x` safety margin above `153 min` (absorbs extra summer/ambient thermal pauses without falsely aborting epoch 38–40).
  - **Future Speedup Path (Zero Format Change):** Porting `FORGE_FUSED_STEP` Triton kernels to Pairwise+PSQT drops `1024w` training back from `~153 min` to `~70–95 min` (`~2.0h/round`, identical to live `768w`).

### 2. Anchor Weight Per Round (Exact Counts Verified from `G3_FULL25` Run Log)
The 2 frozen Syzygy anchor shards used in `G3_FULL25` (`anchors/dead_draws_20k_clean.fqs.z` `20,000` + `anchors/won_endings_syzygy_20k.fqs.z` `20,000` = **`40,000` unique positions**, strictly disjoint from `heldout_syzygy_4k`) against the 25-round window (`352,448,538` self-play + CC0 rows):

| `--anchor-repeat` | Effective Anchor Rows / Epoch | Share of `353.45M` Window | Presentations / Unique Anchor (`40` ep) | Notes / Recommendation |
|---:|---:|---:|---:|---|
| **`25x`** (used in `G3_FULL25`) | `1,000,000` | **`0.283%`** | `1,000` | **Exact proven `G3_FULL25` recipe** — tiny `0.283%` of window (adds `< 0.3%` epoch time!), zero dilution of self-play, cuts `heldout_syzygy_4k` draw median to `~10.7 cp` with `99.65%` win sign ok. |
| **`10x`** | `400,000` | **`0.113%`** | `400` | Lighter repetition alternative if owner prefers lower per-position repeat count. |
| **`4x`** | `160,000` | **`0.045%`** | `160` | Minimal floor (`< 0.05%`); may under-anchor `OB0` against `352M` self-play rows. |

> **Recommendation for Owner/Opus:** Keep `--anchor-repeat 25` (`0.283%` of the `353.45M` window — exact proven `G3_FULL25` recipe, zero unmeasured drift, negligible compute cost). Also note `G3_FULL25` measured exact wall time = **`9,157.4s` (`152.6 min` = `2.54 h`, including `75` thermal pauses totaling `32.5 min`, `max 98.0 C`)**.

---

## Condition (d): Files Requiring ZERO Changes & Monday Second-Reader Readiness
- **Zero changes required in:** `pipeline/run.py`, `pipeline/nnloop/engine.py`, `pipeline/nnloop/trainer.py`, `pipeline/nnloop/match.py`, `pipeline/nnloop/filterqc.py` (`[filter] min_ply = 0`), `pipeline/nnloop/diskrelief.py`, `pipeline/nnloop/heat.py`, `pipeline/tools/net_test.py`, `tmp/opus_scratch/netcheck/net_sanity.py` v2.
- All 5 surfaces, standalone diffs, fail-before/pass-after tests, and checksums are self-contained inside `C:\nnue-lab\neon\forge_fixes\` so either Opus (now) or Fable (Monday `30 Nov`) can audit and place cleanly in one atomic step.

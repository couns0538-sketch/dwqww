# Wave 8 Final `teamwork\` Delivery Manifest (Curated Text-Only Staging Bundle)

> **CRITICAL SAFETY RULE:** **DO NOT RUN `--live` OR COPY ANYTHING INTO `C:\nnue-lab\teamwork\` DURING WAVE 8.**
> Staging into `C:\nnue-lab\teamwork\neon_12h_quest_delivery\` is permitted **ONLY AFTER FULL QUEST FREEZE**, when:
> 1. All `[PENDING`, `[IN PROGRESS`, `[QUEUED`, `[TESTING`, and `[TRAINING` markers in `C:\nnue-lab\neon\filter_quest\HANDOFF_12H_DATA_QUALITY.md` are resolved/cleared, **AND**
> 2. `C:\nnue-lab\neon\forge_fixes\OWNER_BUNDLE_RESULTS.json` exists on disk and parses as a valid non-empty JSON object.

---

## 1. Stager Architecture & Dual-Lock Safety Contract

- **Stager Script:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave8\streamC_delivery_stager_w8\stage_teamwork_delivery_w8.py` (`33,503` B)
- **External Manifest:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave8\streamC_delivery_stager_w8\DELIVERY_MANIFEST_W8.json` (`161,252` B, schema `w8.1`, `377` entries)
- **Default Execution Mode:** `--dry-run` (mutually exclusive `--dry-run` / `--verify-manifest` / `--check-freeze` / `--live`; read-only, `C:\nnue-lab\teamwork\` untouched).
- **No Escape Hatch:** Zero `--allow-unfrozen` option exists.
- **Dual-Lock `--live` Gate (`RC=2` Refusal Without Touching Disk):** `--live` unconditionally refuses (`RC=2`, creating zero directories and copying zero files) unless **ALL** of the following pass:
  1. `--confirm-quest-complete YES_COPY_TO_TEAMWORK` is passed verbatim,
  2. `--check-freeze` passes (`0` open bracket markers in `HANDOFF_12H_DATA_QUALITY.md` and `OWNER_BUNDLE_RESULTS.json` exists as a valid non-empty JSON dict), and
  3. `schema_errors == 0`, `dup_dest_rel == 0`, `dup_source == 0`, `missing == 0`, `pending_sibling == 0`, `pending_freeze == 0`, `immutable_mismatch == 0`, `forbidden_ext == 0`, `forbidden_path == 0`, `forbidden_words == 0`, `json_invalid == 0`, and `total_staged_bytes <= 3,145,728` (`3.0 MiB` cap including `MANIFEST_SHA256.json`).
- **Text-Only Enforcement:** Blocks `.binpack`, `.dll`, `.epd`, `.exe`, `.fnn3`, `.fqs`, `.lib`, `.log`, `.npz`, `.o`, `.obj`, `.out`, `.part`, `.pgn`, `.plain`, `.pt`, `.pyc`, `.z` on all path suffixes (`src` and `dest_rel`), plus `__pycache__`, `.pytest_cache`, `_tmp_cache`, and `_work_*` directory components.

---

## 2. Bundle Size & Category Breakdown (`377` Manifest Entries <= `3.0 MiB`)

- **Total Manifest Entries:** **`377`** (`370` existing W6/W7/post-W6 + `6` W8 deliverables + `1` `pending_until_freeze` target `OWNER_BUNDLE_RESULTS.json`)
- **Pre-W8 Verified Footprint (`370` files):** `2,563,024` B (`2.444 MiB`: `217` W6 `1,819,088` B + `7` W7 `164,097` B + `146` post-W6 `579,839` B)
- **Wave 8 Deliverables (`6` files):** `294,414` B (`0.281 MiB`, well within the `5 MiB` `teamwork_wave8\` limit)
- **Generated `MANIFEST_SHA256.json` (`--live`):** `71,431` B compact JSON (`separators=(",",":")`)
- **Total Verified Footprint vs Cap:** `2,926,506` B / `3,145,728` B (`2.791 MiB` / `3.000 MiB`), leaving **`219,222` B (`214.08 KiB`) headroom** for `OWNER_BUNDLE_RESULTS.json` and living index updates.

| Category | Manifest Entries | Present on Disk | Present Bytes | Notes |
|---|---:|---:|---:|---|
| `audits\` | 201 | 200 | 924,912 | Includes `DELIVERY_MANIFEST_W8.json` & pending `OWNER_BUNDLE_RESULTS.json` |
| `docs\` | 32 | 32 | 508,717 | Includes Stream A dossier, Stream B science report, & this manifest |
| `packets\` | 31 | 31 | 311,771 | W1–W6 architecture/search packets |
| `patches\` | 51 | 51 | 332,863 | `49` W6 + `FORGE_OWNER_BUNDLE_PGO.patch` + `FORGE_FINAL_G3_PGO.patch` |
| `scripts\` | 41 | 41 | 527,786 | `20` W6 + `1` W7 + `19` post-W6 (incl. `serverday_v3/*.sh`) + `1` W8 stager |
| `tests\` | 21 | 21 | 249,026 | `6` W6 + `1` W7 + `13` parity/gate pytests + `1` W8 pytest |
| **Manifest Subtotal** | **377** | **376** | **2,855,075** | Only `OWNER_BUNDLE_RESULTS.json` (`pending_until_freeze`) absent |
| `MANIFEST_SHA256.json` | 1 | — | 71,431 | Compact hash registry generated on `--live` |
| **Verified Total / Cap** | **378** | **376** | **2,926,506 / 3,145,728** | **`3.0 MiB` hard cap** (upgraded from W6 `1.8 MiB`) |

---

## 3. Wave 8 Deliverables (`wave8_sibling: true`, `freeze_mutable: true`, `sha256: null`)

| Staged Path (`neon_12h_quest_delivery\`) | Source Path (`C:\nnue-lab\neon\forge_fixes\teamwork_wave8\...`) | Stream |
|---|---|---|
| `docs\OWNER_BUNDLE_TECHNICAL_DOSSIER.md` | `streamA_owner_bundle_and_search\OWNER_BUNDLE_TECHNICAL_DOSSIER.md` | Stream A |
| `tests\test_owner_bundle_and_r1_scripts_w8.py` | `streamA_owner_bundle_and_search\tests\test_owner_bundle_and_r1_scripts_w8.py` | Stream A |
| `docs\FILTER_QUEST_STAGE2_INTERIM_SCIENCE.md` | `streamB_filter_science\FILTER_QUEST_STAGE2_INTERIM_SCIENCE.md` | Stream B |
| `scripts\stage_teamwork_delivery_w8.py` | `streamC_delivery_stager_w8\stage_teamwork_delivery_w8.py` | Stream C |
| `audits\DELIVERY_MANIFEST_W8.json` | `streamC_delivery_stager_w8\DELIVERY_MANIFEST_W8.json` | Stream C |
| `docs\DELIVERY_MANIFEST_W8.md` | `streamC_delivery_stager_w8\DELIVERY_MANIFEST_W8.md` | Stream C |

---

## 4. Expansion Summary Since Wave 6 (`217` -> `377` Entries)

- **Wave 6 Baseline (`217` files):** Preserved in full. Historical static files (`207`, including now-pinned `DELIVERY_MANIFEST_W6.md` and `stage_teamwork_delivery_w6.py`) are locked with `freeze_mutable: false`; `10` living quest docs/audits remain `freeze_mutable: true`.
- **Wave 7 Deliverables (`7` files, `164,097` B):** `EQUAL_TIME_AND_5ARCH_PARETO_REPORT.md`, `KEEP_NOISY_ROOT_CAUSE_REPORT.md`, `SERVER_DAY_2B_FINAL_EXECUTION_SPEC.md`, `THREE_MODEL_DEBATE_EXECUTIVE_BRIEF.md`, `test_serverday_skipnoisy_and_scripts_w7.py`, `check_freeze_readiness_w7.py` (`freeze_mutable: false`), plus living `freeze_readiness_w7.json` (`freeze_mutable: true`).
- **Post-W6 Curated Core & Verified Sets (`146` files, `579,839` B):**
  - `31` core docs/patches/scripts/audits (`OLS_SCALEFREE_COMPARISON.md/.json`, `G3_SCALING_TRAJECTORY.md`, living `CHECKPOINT_LATEST.md`, `FORGE_OWNER_BUNDLE_PGO.patch`, `FORGE_FINAL_G3_PGO.patch`, `serverday_v3/run_dedup_buckets_v3.sh`, `serverday_v3/run_train_stream_gpu_v3.sh`, `17` runners/audit scripts, `6` PGO/forensic/declare JSONs incl. living `OWNER_BUNDLE_DECLARATION.json` and `STAGE2_QUIET_GPU_SUMMARY.json`).
  - `18` match `summary.json` + `declaration_*.json` across `9` post-W6 completed matches (including `G3_FULL25_PGO_vs_live_r0067_2000g_6p006`, `OPUS_r0202_vs_r0067_1000g_250k`, `G3b_skipnoisy_vs_G3a_*`, `S2Q_G4a_*`, `S2Q_G4b_*`, `S2Q_EXP_F1_*`, and `S2Q_EXP_F2_first_vs_G3b_1000g_50k`).
  - `13` non-W6 `test_*.py` parity/gate/filter tests (`63,747` B).
  - `12` `G5a/G5b/G5c` server-day JSONs (`35,521` B) + `1` `OPUS_R1_live768_skipnoisy/declaration.json` (`982` B).
  - `27` `filter_quest/stage2_runs_quiet/` JSONs (`39,545` B) + `5` `forge_fixes/builds/` PGO gate/manifest JSONs (`34,768` B) + `39` `G3a/G3b/G4a/G4b` GPU run JSON/TXTs (`92,407` B).
  - *(Intentionally omitted to stay cleanly under `3.0 MiB`: `98` pre-W6 match files `314,352` B already summarized in `ALL_MATCHES_SCOREBOARD.json`, and `196,559` B `heldout_perpos_cand.tsv`.)*

---

## 5. Immutable vs Living & `pending_until_freeze` Summary

- **Immutable Frozen (`356` entries, `freeze_mutable: false`):** Exact 64-hex SHA-256 verified on every run (`207` W6 + `6` W7 + `143` post-W6). Any byte drift fails immediately.
- **Living Quest Files (`14` existing entries, `freeze_mutable: true`):**
  - W6 (`10`): `HANDOFF_12H_DATA_QUALITY.md`, `PHASE_B_METHODS_AND_DESIGN.md`, `ALL_MATCHES_SCOREBOARD.md`, `ALL_MATCHES_SCOREBOARD.json`, `STAGE2_FILTER_QUEST_SUMMARY.md`, `STAGE2_FILTER_QUEST_SUMMARY.json`, `WDL_CALIBRATION_AUDIT.json`, `G3_SCALING_TRAJECTORY.json`, `G3_RESIDUAL_BLUNDER_DIAGNOSIS.json`, `G3_QUIET_BLUNDER_DEPTH_PROBE.json`.
  - W7 & Post-W6 (`4`): `freeze_readiness_w7.json`, `CHECKPOINT_LATEST.md`, `OWNER_BUNDLE_DECLARATION.json`, `STAGE2_QUIET_GPU_SUMMARY.json`.
- **Wave 8 Siblings (`6` entries, `wave8_sibling: true`, `freeze_mutable: true`, `sha256: null`):** Checked for existence (`--require-siblings`), zero forbidden terms, and JSON validity (for `DELIVERY_MANIFEST_W8.json`); final hashes are captured in `MANIFEST_SHA256.json` on `--live`.
- **Freeze-Pending (`1` entry, `pending_until_freeze: true`, `freeze_mutable: true`, `sha256: null`):** `C:\nnue-lab\neon\forge_fixes\OWNER_BUNDLE_RESULTS.json` (`audits\OWNER_BUNDLE_RESULTS.json`). Absent during `--dry-run` (`RC=0`), required as a valid non-empty JSON object for `--check-freeze` (`RC=0`) and `--live` (`RC=0`).

---

## 6. Exact Final Freeze & Live-Copy Commands (Main Agent Only)

```powershell
$env:CUDA_VISIBLE_DEVICES = ""
$env:HIP_VISIBLE_DEVICES = ""
$env:ROCR_VISIBLE_DEVICES = ""
$env:PYTHONDONTWRITEBYTECODE = "1"
$py = "C:\nnue-lab\venv101\Scripts\python.exe"
$sc = "C:\nnue-lab\neon\forge_fixes\teamwork_wave8\streamC_delivery_stager_w8\stage_teamwork_delivery_w8.py"

# 1. Pre-freeze dry-run & manifest verification (requires all 6 W8 siblings present; safe read-only)
& $py -B $sc --dry-run --require-siblings
& $py -B $sc --verify-manifest --require-siblings

# 2. Freeze readiness check (returns RC=0 ONLY when all open markers are cleared & OWNER_BUNDLE_RESULTS.json exists)
& $py -B $sc --check-freeze

# 3. Final live staging into C:\nnue-lab\teamwork\neon_12h_quest_delivery (ONLY after --check-freeze returns RC=0)
& $py -B $sc --live --confirm-quest-complete YES_COPY_TO_TEAMWORK
```

# Wave 10 Final `teamwork\` Delivery Manifest (Curated Text-Only Staging Bundle)

> **CRITICAL SAFETY RULE:** **DO NOT RUN `--live` OR COPY ANYTHING INTO `C:\nnue-lab\teamwork\` DURING WAVE 10.**
> Staging into `C:\nnue-lab\teamwork\neon_12h_quest_delivery\` is permitted **ONLY AFTER FULL QUEST FREEZE**, when:
> 1. All `[PENDING`, `[IN PROGRESS`, `[QUEUED`, `[TESTING`, and `[TRAINING` markers in `C:\nnue-lab\neon\filter_quest\HANDOFF_12H_DATA_QUALITY.md` are resolved/cleared, **AND**
> 2. Every `pending_freeze` (`pending_until_freeze: true`) target — specifically `C:\nnue-lab\neon\forge_fixes\matches\OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k\summary.json` — exists on disk and parses as a valid non-empty JSON object.

---

## 1. Stager Architecture & Dual-Lock Safety Contract

- **Stager Script:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave10\streamC_delivery_stager_w10\stage_teamwork_delivery_w10.py`
- **External Manifest:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave10\streamC_delivery_stager_w10\DELIVERY_MANIFEST_W10.json` (schema `w10.1`, `wave: 10`, `415` entries)
- **Default Execution Mode:** `--dry-run` (mutually exclusive `--dry-run` / `--verify-manifest` / `--check-freeze` / `--live`; read-only, `C:\nnue-lab\teamwork\` untouched).
- **No Escape Hatch:** Zero `--allow-unfrozen` option exists.
- **Dual-Lock `--live` Gate (`RC=2` Refusal Without Touching Disk):** `--live` unconditionally refuses (`RC=2`, creating zero directories and copying zero files) unless **ALL** of the following pass:
  1. `--confirm-quest-complete YES_COPY_TO_TEAMWORK` is passed verbatim,
  2. `--check-freeze` passes (`0` open bracket markers in `HANDOFF_12H_DATA_QUALITY.md` and every `pending_freeze` JSON exists as a valid non-empty JSON dict), and
  3. `schema_errors == 0`, `dup_dest_rel == 0`, `dup_source == 0`, `missing == 0`, `pending_sibling == 0`, `pending_freeze == 0`, `immutable_mismatch == 0`, `forbidden_ext == 0`, `forbidden_path == 0`, `forbidden_words == 0`, `json_invalid == 0`, and `total_staged_bytes <= 4,194,304` (`4.0 MiB` cap including `MANIFEST_SHA256.json`).
- **Explicit Status & Invariant Schema (`w10.1`):** Every entry explicitly declares `"status"` (`"frozen"` | `"living"` | `"pending_freeze"`) and `"wave10_sibling"` alongside `freeze_mutable`, `pending_until_freeze`, and `sha256`, strictly enforcing:
  - `status == "pending_freeze"` <=> `pending_until_freeze is True` and `freeze_mutable is True` and `sha256 is None`
  - `status == "living"` <=> `freeze_mutable is True` and `pending_until_freeze is False`
  - `status == "frozen"` <=> `freeze_mutable is False` and `pending_until_freeze is False` and `wave10_sibling is False` and valid 64-hex `sha256`
- **Text-Only Enforcement:** Blocks `.binpack`, `.dll`, `.epd`, `.exe`, `.fnn3`, `.fqs`, `.lib`, `.log`, `.npz`, `.o`, `.obj`, `.out`, `.part`, `.pgn`, `.plain`, `.pt`, `.pyc`, `.z` on all path suffixes (`src` and `dest_rel`), plus `__pycache__`, `.pytest_cache`, `_tmp_cache`, and `_work_*` directory components.

---

## 2. Bundle Size & Category Breakdown (`415` Manifest Entries <= `4.0 MiB`)

- **Total Manifest Entries:** **`415`** (`377` W8 baseline entries + `3` W9 deliverables + `28` new post-W8 verified text/JSON artifacts + `1` `pending_freeze` active match summary + `6` W10 deliverables)
- **Status Partition (`415`):** `387` `frozen` + `27` `living` + `1` `pending_freeze`

| Category | Manifest Entries | Present on Disk | Present Bytes | Notes |
|---|---:|---:|---:|---|
| `audits\` | 227 | 226 | 1,229,439 | Includes `DELIVERY_MANIFEST_W10.json`, post-W8 JSONs, & `pending_freeze` `OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k_summary.json` |
| `docs\` | 38 | 38 | 644,236 | Includes Stream A, Stream B, `PACKET_IMMEDIATE_LOOP_AND_SERVERDAY_DELTAS.md`, W9 docs, & this manifest |
| `packets\` | 31 | 31 | 311,771 | W1–W6 architecture/search packets |
| `patches\` | 51 | 51 | 332,863 | `49` W6 + `FORGE_OWNER_BUNDLE_PGO.patch` + `FORGE_FINAL_G3_PGO.patch` |
| `scripts\` | 45 | 45 | 585,094 | Includes `bench_per_patch_nps.py`, `audit_owner_bundle_arma_pgn.py`, `run_serverday_arch_suite_quiet.py`, `serverday_v3/*.sh`, & `stage_teamwork_delivery_w10.py` |
| `tests\` | 23 | 23 | 305,124 | Includes W6/W7/W8/W9 pytests + `test_wave10_stager_and_artifacts.py` |
| **Manifest Subtotal** | **415** | **414** | **3,408,527** | Only `OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k\summary.json` (`pending_freeze`) absent |
| `MANIFEST_SHA256.json` | 1 | — | 86,477 | Compact hash registry generated on `--live` |
| **Verified Total / Cap** | **416** | **414** | **3,495,004 / 4,194,304** | **`4.0 MiB` hard cap** (upgraded from W8 `3.0 MiB`) |

---

## 3. Wave 10 Deliverables (`wave10_sibling: true`, `status: "living"`, `freeze_mutable: true`, `sha256: null`)

| Staged Path (`neon_12h_quest_delivery\`) | Source Path (`C:\nnue-lab\neon\forge_fixes\teamwork_wave10\...`) | Stream |
|---|---|---|
| `docs\PER_PATCH_NPS_AND_SEARCH_ROADMAP.md` | `streamA_per_patch_nps_and_search\PER_PATCH_NPS_AND_SEARCH_ROADMAP.md` | Stream A |
| `docs\STAGE2_250K_VERIFICATION_AND_SERVERDAY_FINAL_LOCK.md` | `streamB_stage2_250k_postmortem\STAGE2_250K_VERIFICATION_AND_SERVERDAY_FINAL_LOCK.md` | Stream B |
| `scripts\stage_teamwork_delivery_w10.py` | `streamC_delivery_stager_w10\stage_teamwork_delivery_w10.py` | Stream C |
| `audits\DELIVERY_MANIFEST_W10.json` | `streamC_delivery_stager_w10\DELIVERY_MANIFEST_W10.json` | Stream C |
| `docs\DELIVERY_MANIFEST_W10.md` | `streamC_delivery_stager_w10\DELIVERY_MANIFEST_W10.md` | Stream C |
| `tests\test_wave10_stager_and_artifacts.py` | `streamC_delivery_stager_w10\tests\test_wave10_stager_and_artifacts.py` | Stream C |

---

## 4. Expansion & Status Transitions Since Wave 8 (`377` -> `415` Entries)

- **Wave 8 Deliverables Promoted to `frozen` (`6` files, exact SHA-256s):** `OWNER_BUNDLE_TECHNICAL_DOSSIER.md`, `test_owner_bundle_and_r1_scripts_w8.py`, `FILTER_QUEST_STAGE2_INTERIM_SCIENCE.md`, `stage_teamwork_delivery_w8.py`, `DELIVERY_MANIFEST_W8.json`, `DELIVERY_MANIFEST_W8.md`.
- **`OWNER_BUNDLE_RESULTS.json` Promoted to `frozen` (`18,893` B):** Completed post-W8 (`sha256: 855a255f...`), promoted from W8 `pending_until_freeze`.
- **Reclassified as `living` (`6` W8 entries + `1` post-W8 entry):** `OLS_SCALEFREE_COMPARISON.md/.json`, `serverday_v3/run_train_stream_gpu_v3.sh`, `serverday_v3/run_dedup_buckets_v3.sh`, `run_post_bundle_250k_queue.py`, `audit_ols_ratios_and_netunits.py`, and `R1_TWIN_DECLARATION.json` (alongside the `14` existing W6/W7/post-W6 living files and `6` W10 siblings = `27` total `living`).
- **Wave 9 Deliverables Added (`3` files, `frozen`, `105,110` B):** `OWNER_BUNDLE_FINAL_ATTRIBUTION_REPORT.md`, `STAGE2_FILTER_QUEST_10OF10_FINAL_ANALYSIS.md`, `test_wave9_declarations_and_packets.py`.
- **Post-W8 Verified Text/JSON Artifacts Added (`28` files, `27` `frozen` + `1` `living`):**
  - Core post-W8 (`15` new): `CLEAN_IDLE_PER_PATCH_NPS.json`, `SERVERDAY_ARCH_SUITE_QUIET_SUMMARY.json`, `R1_TWIN_DECLARATION.json` (`living`), `STAGE2_250K_CONFIRMATIONS_DECLARATION.json`, `PACKET_IMMEDIATE_LOOP_AND_SERVERDAY_DELTAS.md`, `OWNER_BUNDLE_ARMA_PGN_FORENSICS.json`, `OWNER_BUNDLE_ARMB_PGN_FORENSICS.json`, `bench_per_patch_nps.py`, `audit_owner_bundle_arma_pgn.py`, `run_serverday_arch_suite_quiet.py`, `OPUS_R1_live768_skipnoisy/r1_summary.json`, `OPUS_R1_live768_keepnoisy_twin/r1_keep_summary.json`, and all `3` `S2Q_*_600g_250k_CONFIRM/summary.json` files.
  - Supporting completed post-W8 JSONs (`13` files): `OPUS_R1_live768_skipnoisy/{eval_full,master_gate_quick}.json`, `OPUS_R1_live768_keepnoisy_twin/{declaration,eval_full,master_gate_quick}.json`, `OWNER_BUNDLE_ARMA_*/{declaration_20261128_024459,summary}.json`, `OWNER_BUNDLE_ARMB_*/{declaration_20261128_041857,summary}.json`, the `3` `S2Q_*_600g_250k_CONFIRM/declaration_*.json` files, and `OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k/declaration_20261128_065512.json`.
- **Active `pending_freeze` (`1` entry):** `C:\nnue-lab\neon\forge_fixes\matches\OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k\summary.json` (`audits\OPUS_R1_skip_vs_R1_keep_SPRT_0_10_250k_summary.json`).

---

## 5. Exact Pre-Freeze Verification & Final Live-Copy Commands (Main Agent Only)

```powershell
$env:CUDA_VISIBLE_DEVICES = ""
$env:HIP_VISIBLE_DEVICES = ""
$env:ROCR_VISIBLE_DEVICES = ""
$env:PYTHONDONTWRITEBYTECODE = "1"
$py = "C:\nnue-lab\venv101\Scripts\python.exe"
$sc = "C:\nnue-lab\neon\forge_fixes\teamwork_wave10\streamC_delivery_stager_w10\stage_teamwork_delivery_w10.py"

# 1. Pre-freeze dry-run & manifest verification (requires all 6 W10 siblings present; safe read-only)
& $py -B $sc --dry-run --require-siblings
& $py -B $sc --verify-manifest --require-siblings

# 2. Freeze readiness check (returns RC=0 ONLY when all open markers are cleared & pending_freeze targets exist)
& $py -B $sc --check-freeze

# 3. Wave 10 pytest suite (< 3s, CPU-only, zero cache)
& $py -B -m pytest -p no:cacheprovider "C:\nnue-lab\neon\forge_fixes\teamwork_wave10\streamC_delivery_stager_w10\tests\test_wave10_stager_and_artifacts.py"

# 4. Final live staging into C:\nnue-lab\teamwork\neon_12h_quest_delivery (ONLY after --check-freeze returns RC=0)
& $py -B $sc --live --confirm-quest-complete YES_COPY_TO_TEAMWORK
```

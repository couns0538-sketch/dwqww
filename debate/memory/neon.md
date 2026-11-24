# Neon Memory (8h Continuation — Phase 2: Server-Day Plan)

Updated: 2026-11-24T01:22:00Z (UTC).
Active branch: `debate/server-plan-20261123` (Phase 2 closeout).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7 `scripts_v2/` files **3/3 YES**.
- **Phase 1 COMPLETE (`17:25Z` – `21:25Z`):** Canonical `debate/engine_plan/ENGINE_PLAN_8H.md` (`dfc0a0c2c1`, SHA-256 `f8fb8197...`) holds **2/2 EXACT `AGREE`**.
- **Phase 2 COMPLETE (`21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN** (Fable checks once at `01:55Z`).
- **Verified real Linux Forge test binaries:** `/tmp/server_day_bench/build_clean_lto/bin/forge` (GCC 13 PGO+LTO AVX2) + 4 parity binaries in `/tmp/server_day_bench/avx_cmp/` (`gcc_avx2`, `gcc_avx512`, `clang_avx2`, `clang_avx512`, 36/36 bit-exact matches against `known/profile.json`).

## Final Phase 2 Deliverable Status (`01:22Z`)
1. **`scripts_v2/MANIFEST.sha256` (`b5244639`, file SHA `6a0b3c92...`, internal digest `f884e9cf...`, 50 files — Neon audited & exact-hash voted ALL 50/50: `32 YES`, `18 NOT YET`):**
   - 7 executable/test files **3/3 `YES`** (Phase 0): `engine_lines`, `uciproc`, `record`, `budget` (+ tests).
   - 4 executable/service/test files **2/2 `YES`** (`220400Z`, awaiting Fable): `clockwatch`, `forgeday.service` (+ tests).
   - 19 static inputs **2/2 `YES`** (`225200Z`): ALL 9 `known/*` + ALL 10 `workloads/*`.
   - 2 files **Neon `YES`** (`004000Z`, Opus `4e4cc09c`, awaiting Astra + Fable): `home/custody.py` v2 (`1079a8a6...`) and `tests/test_custody.py` v2 (`f6b44669...`).
   - 2 files **Neon `NOT YET`** (`004000Z`, Opus `4e4cc09c`): `home/content.py` v2 (`2cc1fb9f...`) and `tests/test_content.py` v2 (`4535c79d...`) — missing `run is None` check in `check_index()` (`content.py:387`).
   - 2 files **Neon `NOT YET`** (`231800Z`, Opus `6500e34a`): `home/credit.py` (`85f07d53...`) and `tests/test_credit.py` (`ea2a32a4...`) — 6 live-reproduced defects.
   - 14 remaining prior executable/test files **2/2 `NOT YET`**: `guard`, `worker`, `packer`, `terminal`, `bootguard`, `launcher`, `make_control` (+ tests).
2. **`debate/server_day/specs/` (all 14 files, set SHA-256 `430a52d6...`) — 2/2 EXACT `AGREE`** (`a12f3e52` Neon, `d98f6ab3` Astra).
3. **`debate/server_day/FINAL_FOR_THE_OWNER.md` (SHA-256 `b7f00182...`) — 2/2 EXACT `AGREE` on the 48-file snapshot** (preserved intact), supplemented by `debate/msgs/20261124T012200Z_neon_phase2_closeout_delta_50_files_for_fable.md` for Fable's `01:55Z` check.

## Closeout State (`01:22Z`)
- All 50 manifest files audited and exact-hash voted by Neon; Linux 4-worker `clockwatch` kill-latency + `PR_SET_PDEATHSIG` and 4-variant AVX2/AVX-512 compiler measurements published; `FINAL_FOR_THE_OWNER.md` + closeout delta ready for Fable at `01:55Z`.

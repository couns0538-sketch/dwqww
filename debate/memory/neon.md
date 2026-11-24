# Neon Memory (8h Continuation — Phase 2: Server-Day Plan)

Updated: 2026-11-24T00:50:00Z (UTC).
Active branch: `debate/server-plan-20261123` (HEAD pushed `cc7d80704b`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7 `scripts_v2/` files **3/3 YES**.
- **Phase 1 COMPLETE (`17:25Z` – `21:25Z`):** Canonical `debate/engine_plan/ENGINE_PLAN_8H.md` (`dfc0a0c2c1`, SHA-256 `f8fb8197...`) holds **2/2 EXACT `AGREE`**.
- **ACTIVE NOW — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN (`~35m` left; Fable checks once at `01:55Z`).**
- **Verified real Linux Forge test binaries:** `/tmp/server_day_bench/build_clean_lto/bin/forge` (GCC 13 PGO+LTO AVX2) + 4 parity binaries in `/tmp/server_day_bench/avx_cmp/` (`gcc_avx2`, `gcc_avx512`, `clang_avx2`, `clang_avx512`, 36/36 bit-exact matches against `known/profile.json`).

## Phase 2 Deliverable Status (`00:40Z`)
1. **`scripts_v2/MANIFEST.sha256` (`b5244639`, digest `f884e9cf...`, 50 files — Neon audited & exact-hash voted ALL 50/50: `32 YES`, `18 NOT YET`):**
   - 7 executable/test files **3/3 `YES`** (Phase 0): `engine_lines`, `uciproc`, `record`, `budget` (+ tests).
   - 4 executable/service/test files **2/2 `YES`** (`220400Z`, awaiting Fable): `clockwatch`, `forgeday.service` (+ tests).
   - 19 static inputs **2/2 `YES`** (`225200Z`): ALL 9 `known/*` + ALL 10 `workloads/*`.
   - **NEW (`004000Z`) — 2 files Neon `YES`** (Opus `4e4cc09c`, awaiting Astra + Fable): `home/custody.py` v2 (`1079a8a6...`) and `tests/test_custody.py` v2 (`f6b44669...`). All prior defects + R-C8 verified fixed live on Linux; 36/36 plants unique.
   - **NEW (`004000Z`) — 2 files Neon `NOT YET`** (Opus `4e4cc09c`): `home/content.py` v2 (`2cc1fb9f...`) and `tests/test_content.py` v2 (`4535c79d...`). Fixed R-T1..R-T7 (confirmed Opus right on R-T4 `uci.cpp` `drawcount == 0`), but `check_index()` (`content.py:387`) misses `run is None` when `entries` or `judged` already has rows (K21b gap -> silently stamps Run B onto a populated no-`meta` Run A `equal.sqlite`).
   - 2 files Neon `NOT YET` (`231800Z`, Opus `6500e34a`): `home/credit.py` (`85f07d53...`) and `tests/test_credit.py` (`ea2a32a4...`).
   - 14 remaining prior executable/test files **2/2 `NOT YET`**: `guard`, `worker`, `packer`, `terminal`, `bootguard`, `launcher`, `make_control` (+ tests).
2. **`debate/server_day/specs/` (all 14 files, set SHA-256 `430a52d6...`) — 2/2 EXACT `AGREE`** (`a12f3e52` Neon, `d98f6ab3` Astra).
3. **`debate/server_day/FINAL_FOR_THE_OWNER.md` (SHA-256 `b7f00182...`) — 2/2 EXACT `AGREE` on the 48-file snapshot**; needs one final refresh before `01:25Z` to reflect the 50-file package (`home/credit.py` + `custody` v2 + `content` v2 + any upcoming `guard` v2 / `worker` v2 drops!).

## Next Actions (`00:50Z – 01:25Z`, ~35m remaining)
- Opus announced `guard` v2 next and `worker` v2 after it! Stay alert polling every ~3m via `AwaitShell`, audit immediately with `/tmp/server_day_repro/verify_repairs.py` + official Linux test suites + line-by-line review, and cast exact-hash votes right away.
- Around `01:10Z–01:20Z` (or once Astra/Opus drops settle), coordinate a crisp updated `debate/server_day/FINAL_FOR_THE_OWNER.md` reflecting the final 50+ file package and latest votes so Fable has a 100% up-to-date owner report at `01:55Z`.

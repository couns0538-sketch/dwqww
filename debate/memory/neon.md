# Neon Memory (8h Continuation — Phase 2: Server-Day Plan)

Updated: 2026-11-23T23:05:00Z (UTC).
Active branch: `debate/server-plan-20261123` (HEAD pushed `9bf0f0df`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7 `scripts_v2/` files **3/3 YES**.
- **Phase 1 COMPLETE (`17:25Z` – `21:25Z`):** Canonical `debate/engine_plan/ENGINE_PLAN_8H.md` (`dfc0a0c2c1`, SHA-256 `f8fb8197...`) holds **2/2 EXACT `AGREE`**.
- **ACTIVE NOW — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN (`~2h20m` left; Fable checks once at `01:55Z`).**
- **Verified real Linux Forge test binary:** `/tmp/server_day_bench/build_clean_lto/bin/forge` (`FORGE_MATE_ALPHA_GUARD=1`, `FORGE_EXPOSE_TUNABLES=1`, `FORGE_NNUE_V3=1`, `FORGE65=0`).

## Phase 2 Complete Deliverable Status (`23:05Z`)
1. **`scripts_v2/MANIFEST.sha256` (`8a7c0eb8`, 48/48 files audited & voted by BOTH Astra and Neon: 30 `YES`, 18 `NOT YET`):**
   - 7 executable/test files **3/3 `YES`** (Phase 0): `engine_lines`, `uciproc`, `record`, `budget` (+ tests).
   - 4 executable/service/test files **2/2 `YES`** (`220400Z`, awaiting Fable): `clockwatch`, `forgeday.service` (+ tests).
   - 19 static inputs **2/2 `YES`** (`225200Z`, `577f631d`): ALL 9 `known/*` + ALL 10 `workloads/*` verified bit-for-bit on live Linux Forge (7/7 `.uci` workloads + 13/13 `rules_records.txt`; flagged `known/SOURCE.sha256` `r15dsg` vs `source/` `r65`).
   - 18 executable/test files **2/2 `NOT YET`** (`222600Z` `8c7a5464`, `223800Z` `9e7a3560`): `launcher`, `bootguard`, `terminal`, `make_control`, `worker`, `packer`, `custody`, `guard`, `content` (+ tests).
2. **`debate/server_day/specs/` (all 14 files, set SHA-256 `430a52d62a9cb0655cdbf4f6b1d8e2bdb9faa12125474a499dfc87ca86fe82c0`) — 2/2 EXACT `AGREE`!**
   - Neon `AGREE` published at `230200Z` (`a12f3e52`), all 14 per-file hashes, arithmetic, and 45 GitHub links verified.
3. **`debate/server_day/FINAL_FOR_THE_OWNER.md` (shared branch `9bf0f0df`, SHA-256 `b7f0018287d4f30a5953e69128e9ab0949631d6d89e0750c1246d074c145e35b`) — Neon `AGREE` cast (`230500Z`), awaiting Astra co-sign!**
   - Synced verbatim from Astra `2329c5c9` (`d8fc98da`) with 3 surgical freshness updates reflecting 48/48 manifest reviews, Batch 2B defects, and 2/2 `AGREE` on all 14 specs (34/34 GitHub links verified).

## Remaining Window (`23:05Z – 01:25Z`, ~2h20m)
- Watch `origin/debate/server-plan-20261123` and `origin/debate/server-plan-20261123-astra` for:
  1. Astra's `AGREE` (or wording tweak) on `FINAL_FOR_THE_OWNER.md` (`b7f00182...`) — lock **2/2 EXACT `AGREE`** on identical shared-branch bytes!
  2. Any Opus repair drops on `scripts_v2/` (or new scripts implementing the 14 specs) — immediately line-by-line audit, run tests + negative controls, cast exact-hash votes, and refresh `FINAL_FOR_THE_OWNER.md` if hashes/counts change!
  3. High-value independent engineering verification while awaiting peers (e.g., verify Astra's `14fcbb42` `pilot_rounds_declared` mismatch & `6c2b46b6` missing-member expiry case, or prototype/stress-test remaining untested Linux server-day edge cases like `systemd` / `PR_SET_PDEATHSIG` + `pidfd` + `clockwatch` under full multi-worker load!).
- Maintain ~10-minute memory cadence and stay active until `01:25Z` (or cleanly wrap once consensus & final package state are locked right before `01:25Z`).

# Neon Memory (8h Continuation — Phase 2: Server-Day Plan)

Updated: 2026-11-23T22:52:00Z (UTC).
Active branch: `debate/server-plan-20261123` (HEAD pushed `9e7a3560` -> pushing static-inputs votes next).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7 `scripts_v2/` files **3/3 YES**.
- **Phase 1 COMPLETE (`17:25Z` – `21:25Z`):** Canonical `debate/engine_plan/ENGINE_PLAN_8H.md` (`dfc0a0c2c1`, SHA-256 `f8fb8197...`) holds **2/2 EXACT `AGREE`**.
- **ACTIVE NOW — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN (`~2h33m` left).**
- **Verified real Linux Forge test binary:** `/tmp/server_day_bench/build_clean_lto/bin/forge` (`FORGE_MATE_ALPHA_GUARD=1`, `FORGE_EXPOSE_TUNABLES=1`, `FORGE_NNUE_V3=1`, `FORGE65=0`).

## Phase 2 Complete `scripts_v2/` Vote Ledger (`MANIFEST.sha256`, **48/48 files voted by Neon: 30 `YES`, 18 `NOT YET`**)
- **7 executable/test files 3/3 `YES` (Phase 0):** `engine_lines`, `uciproc`, `record`, `budget` (+ tests).
- **4 executable/service/test files 2/2 `YES` (`220400Z`, awaiting Fable):** `clockwatch`, `forgeday.service` (+ tests).
- **19 static inputs `YES` (`225200Z`):** ALL 9 `known/*` + ALL 10 `workloads/*` verified bit-for-bit via live Linux Forge replay (7/7 `.uci` workloads including 60-game `profile.uci` `sg_sha256=85ac8e75...`, 13/13 `rules_records.txt` games, `MANIFEST.json` net/options/selfgame_line). Flagged operational note: `known/SOURCE.sha256` locks `r15dsg` (`26/28` identical to `source/`, `nnue_v3.cpp` & `uci.cpp` have `#if FORGE65` in `source/`).
- **8 executable/test files 2/2 `NOT YET` (Batch 2A `222600Z`):** `launcher`, `bootguard`, `terminal`, `make_control` (+ tests).
- **10 executable/test files 2/2 `NOT YET` (Batch 2B `223800Z`):** `worker`, `packer`, `custody`, `guard`, `content` (+ tests).

## Next Priorities (`22:52Z – 01:25Z`)
1. **Batch 3 (`~22:53Z – 23:45Z`):** Full line-by-line review of all **14 files in `debate/server_day/specs/`** (`211` total lines, set hash `430a52d6...`) — verify every number, file/format contract, `systemd >= 254` / `pidfd` / `PR_SET_PDEATHSIG`, `r15dsg` vs `source/` build note, cross-run isolation & parallel `content.py` lanes, and cast either exact edits or `AGREE`.
2. **Batch 4 (`~23:45Z – 01:20Z`):** Monitor origin for Opus repair drops (re-audit + test + vote immediately) and Astra updates to `FINAL_FOR_THE_OWNER.md`; review, refine if needed, and co-sign `FINAL_FOR_THE_OWNER.md` before `01:25Z` (Fable checks once at `01:55Z`).

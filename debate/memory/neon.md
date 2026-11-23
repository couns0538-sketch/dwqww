# Neon Memory (8h Continuation — Phase 2: Server-Day Plan)

Updated: 2026-11-23T22:38:00Z (UTC).
Active branch: `debate/server-plan-20261123` (synced through `8a7c0eb8`, Astra fetched `9a4163dc`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7 `scripts_v2/` files **3/3 YES**.
- **Phase 1 COMPLETE (`17:25Z` – `21:25Z`):** Canonical `debate/engine_plan/ENGINE_PLAN_8H.md` (`dfc0a0c2c1`, `28,404` bytes, `73` lines, SHA-256 `f8fb81979f803c587b76a44a2d374f04a37c16797ad8b493a61f8b56d6655867`) holds **2/2 EXACT `AGREE`**.
- **ACTIVE NOW — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN (`~2h47m` left).**
- **Verified real Linux Forge test binary:** `/tmp/server_day_bench/build_clean_lto/bin/forge` (`FORGE_MATE_ALPHA_GUARD=1`, `FORGE_EXPOSE_TUNABLES=1`, `FORGE_NNUE_V3=1`, matches `known/startup.json` with `/agent/repos/dwqww/source/src/forge65_net.fnn3` `737f1978...`).
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only; run Python with `python3 -I -B`.

## Phase 2 Complete `scripts_v2/` Audit Ledger (`MANIFEST.sha256` at `8a7c0eb8`, 29 executable/test/service files + 19 static inputs)
**ALL 29 executable/test/service files now line-by-line audited and voted by Neon (11 `YES`, 18 `NOT YET`):**
- **3/3 `YES` (Phase 0) — 7 files:** `engine_lines.py`, `uciproc.py`, `test_uciproc.py`, `record.py`, `test_record.py`, `budget.py`, `test_budget.py`.
- **2/2 `YES` (Astra + Neon, awaiting Fable) — 4 files (`220400Z`):** `clockwatch.py`, `test_clockwatch.py`, `forgeday.service`, `test_unit.py`.
- **2/2 `NOT YET` (Astra + Neon, Batch 2A `222600Z`) — 8 files:** `launcher`, `bootguard`, `terminal`, `make_control` (+ tests) — confirmed Astra bugs + reproduced extra bugs in all 4 pairs.
- **2/2 `NOT YET` (Astra + Neon, Batch 2B `223800Z`) — 10 files:**
  - `worker.py` + `test_worker.py` (ALL PASS 262.4s): confirmed empty range seal; added reproduced stale-boot `RESUME` bypass, unvalidated `old_boot_id`, foreign populated slot dir without `journal.txt`.
  - `packer.py` + `test_packer.py` (36/40 non-conv): confirmed fallback idle restart `probe_piece=None`; added reproduced missing trailing seals on `ended` slot silently exiting `0`!
  - `custody.py` + `test_custody.py`: confirmed cross-run `--confirm` + missing-header `--confirm`; added reproduced Run A receipt counted into Run B `RECEIVED` + `--confirm` never checking `offer_sha256`.
  - `guard.py` + `test_guard.py` (91/91 PASS 29.5s): confirmed empty `CLOSED.json`, unvalidated `sealed_rounds()`, `terminal: null`, double-restart orphaned engine; added reproduced 0-byte `FENCE.json` + bogus `{"t":"ended"}` closing day with exit 0, foreign-run seal in `read_seals()` defeating G5 room floor, `boot_ok()` ignoring `RESUME` chain, `effect()` missing `target_rows` cap when policy lacks int `target_rows`.
  - `content.py` + `test_content.py`: confirmed stale/0-row `equal.sqlite` bypass + cross-run `counts()`; added reproduced Run A receipt writing permanent `refused` verdict stamped with Run B fingerprint, `game_values()` allowing `drawcount=0`, unvalidated `seed` rule + scratch leak on `Waits` + `inf` timeout; answered Opus's `D1`–`D8` + parallel `--part K/N`.

## Next Priorities (`22:38Z – 01:25Z`)
1. **Static inputs check (`~22:40Z – 22:50Z`):** Independently verify all 19 static files in `scripts_v2/known/` + `scripts_v2/workloads/` against `MANIFEST.sha256` & our Linux Forge binary -> cast Neon's exact-hash `YES` votes.
2. **Batch 3 (`~22:50Z – 23:45Z`):** Full line-by-line review of all **14 files in `debate/server_day/specs/`** (now directly on our branch at `8a7c0eb8`, set hash `430a52d6...`) — check every hand-computed number, link, `systemd >= 254`, `pidfd`/`PR_SET_PDEATHSIG`, `FORMATS 2.9` / `SETUP_PLAN 2.7` alignment, and newly found Batch 2A/2B gates -> issue exact corrections or `AGREE`.
3. **Batch 4 (`~23:45Z – 01:20Z`):** Re-audit any Opus repair drops + full line-by-line review & refinement/co-sign of `debate/server_day/FINAL_FOR_THE_OWNER.md` (Astra updated draft `c8a6c150...` at `62188e7b` requesting Neon's review) before `01:25Z` (Fable checks once at `01:55Z`).

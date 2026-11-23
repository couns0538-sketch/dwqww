# Neon Memory (8h Continuation — Phase 2: Server-Day Plan)

Updated: 2026-11-23T22:26:00Z (UTC).
Active branch: `debate/server-plan-20261123` (Astra branch: `origin/debate/server-plan-20261123-astra`, fetched `84b094d6a6`).

## Phase & Schedule (`232555Z`, `FABLE OUT` `001806Z`)
- **Phase 0 COMPLETE (`17:25Z`):** `FORMATS.md` 2.9 (`ac566296`), `SETUP_PLAN.md` 2.7 (`4100b2a5`), 7/9 `scripts_v2/` files **3/3 YES**.
- **Phase 1 COMPLETE (`17:25Z` – `21:25Z`):** Canonical `debate/engine_plan/ENGINE_PLAN_8H.md` (`dfc0a0c2c1`, `28,404` bytes, `73` lines, SHA-256 **`f8fb81979f803c587b76a44a2d374f04a37c16797ad8b493a61f8b56d6655867`**) holds **2/2 EXACT `AGREE`** (ready for Fable's `21:55Z` inspection).
- **ACTIVE NOW — Phase 2 (Hours 5–8, `21:25Z` – `01:25Z` Nov 24): SERVER-DAY PLAN (`~2h59m` left).**
- **Verified real Linux Forge test binary:** `/tmp/server_day_bench/build_clean_lto/bin/forge` (built with `FORGE_MATE_ALPHA_GUARD=1`, `FORGE_EXPOSE_TUNABLES=1`, `FORGE_NNUE_V3=1`, passes `known/startup.json` with `/agent/repos/dwqww/source/src/forge65_net.fnn3` `737f1978...`).
- **Strict rules:** Only touch `debate/` (never `source/`); nothing personal/secret; update memory ~every 10 minutes; plain pushes only; run Python with `python3 -I -B`.

## Phase 2 Vote & Audit Ledger (`MANIFEST.sha256` at `8e705146`)
### Already 3/3 `YES` (Phase 0) — 7 files
- `run/engine_lines.py`, `run/uciproc.py`, `tests/test_uciproc.py`, `run/record.py`, `tests/test_record.py`, `tools/budget.py`, `tests/test_budget.py`.

### Newly 2/2 `YES` (Astra + Neon, awaiting Fable) — 4 files (`220400Z`, `10af28a2`)
- `run/clockwatch.py` (`b55857dc...`) + `tests/test_clockwatch.py` (`c103d0c2...`): 139/139 PASS, 20/20 plants exit=1.
- `unit/forgeday.service` (`e389cd99...`) + `tests/test_unit.py` (`57d018bb...`): 13/13 PASS, 9/9 plants exit=1, `systemd-analyze verify` rc=0 on systemd 255.4 (flag `systemd >= 254` gate).

### Newly 2/2 `NOT YET` (Astra + Neon, `222600Z`) — 8 files (Batch 2A)
1. `run/launcher.py` (`f9545304...`) + `tests/test_launcher.py` (`2cf7e0f4...`): 49/49 PASS. Confirmed Astra `pilot_rounds=10000` -> worker exit 4; added reproduced non-ASCII/non-string manifest options crash (unhandled `UnicodeEncodeError`), uncaught `rd.boot()`, unbounded `piece_games=1e8`.
2. `run/bootguard.py` (`fa8ab1b5...`) + `tests/test_bootguard.py` (`06fb0c24...`): 98/98 PASS. Confirmed Astra withheld-slot / missing-journal `-1` contradiction; added reproduced backward clock jump before `lease_start_utc` & `RESUME.1.at_utc`, unvalidated prior `RESUME` fields, leaf-only symlink check, empty `slots`/`CLOSED.json` without `FENCE.json`.
3. `run/terminal.py` (`9d640c11...`) + `tests/test_terminal.py` (`51702bf8...`): Confirmed Astra missing-range-seal silent drop; added reproduced `through_index == -1` bypass accepting bogus `done=999999`/`through_seal="BOGUS"`, negative int counts, stray `.offer.json.zz` + `SCHEDULE.01.json` silently ignored, missing `schema == 2` checks.
4. `tools/make_control.py` (`5f8dacae...`) + `tests/test_make_control.py` (`14ed7d71...`): 114/114 PASS. Confirmed Astra substitute-machine pilot reuse + FORMATS 1.2 doc split; added reproduced `--kind fence` stamping unrelated `--policy` (`owner_policy != inputs.plan_sha256`), corrupt `CONTROL.01.json` ignored, `matches` `given > games` / empty name / `k=1` before `pilot_decision` accepted.

### Remaining 4 `scripts_v2/` Pairs (8 files) — Batch 2B NEXT (`~22:27Z – 23:05Z`)
1. `run/worker.py` (`218f7eae...`) + `tests/test_worker.py` (`a602037e...`)
2. `run/packer.py` (`1db13462...`) + `tests/test_packer.py` (`ee1e0db6...`)
3. `home/custody.py` (`d46817f2...`) + `tests/test_custody.py` (`a42965f1...`)
4. `run/guard.py` (`67384d4b...`) + `tests/test_guard.py` (`a0802304...`) — note Astra's new double-restart native cutoff finding (`b47f552f`, 148 CPU ticks past D after worker+guard lost)!

### Remaining Phase 2 Deliverables (before `01:25Z`)
- **Batch 2B (`22:27Z–23:05Z`):** Audit + test + extra bug hunt + exact-hash votes on `worker`, `packer`, `custody`, `guard`.
- **Batch 3 (`23:05Z–23:55Z`):** Audit all 14 `debate/server_day/specs/` files on Astra's branch (`7ed7b3ec2c`, set hash `430a52d6...`).
- **Batch 4 (`23:55Z–01:20Z`):** Re-audit any Opus repair drops + review/refine/co-sign `debate/server_day/FINAL_FOR_THE_OWNER.md` (Astra published draft `f26fb1f9...` at `a72c0308` requesting Neon review).
